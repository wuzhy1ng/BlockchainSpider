import json
import time
import traceback
from typing import Union, List

import scrapy
from web3 import Web3

from BlockchainSpider import settings
from BlockchainSpider.items import EventLogItem, Token1155TransferItem, TokenApprovalAllItem, TokenPropertyItem
from BlockchainSpider.items import Token721TransferItem, Token20TransferItem, TokenApprovalItem
from BlockchainSpider.middlewares.defs import LogMiddleware
from BlockchainSpider.utils.cache import LRUCache
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.token import ERC20_TRANSFER_TOPIC, ERC721_TRANSFER_TOPIC, \
    ERC1155_SINGLE_TRANSFER_TOPIC, ERC1155_BATCH_TRANSFER_TOPIC, TOKEN_APPROVE_TOPIC, \
    TOKEN_APPROVE_ALL_TOPIC
from BlockchainSpider.utils.web3 import split_to_words, word_to_address, hex_to_dec, parse_bytes_data


class TokenTransferMiddleware(LogMiddleware):
    def __init__(self):
        self.provider_bucket = None
        self._cache_is_token721 = LRUCache(getattr(settings, 'MIDDLE_CACHE_SIZE', 2 ** 16))
        self._waiting_ctx = dict()  # addr -> logs

    def _init_by_spider(self, spider):
        if self.provider_bucket is not None:
            return
        if getattr(spider, 'middleware_providers') and \
                spider.middleware_providers.get(self.__class__.__name__):
            self.provider_bucket = spider.middleware_providers[self.__class__.__name__]
        else:
            self.provider_bucket = spider.provider_bucket

    async def process_spider_output(self, response, result, spider):
        self._init_by_spider(spider)

        # filter and process the result flow
        async for item in result:
            yield item
            if not isinstance(item, EventLogItem):
                continue
            if not isinstance(item['topics'], list) or len(item['topics']) < 1:
                continue

            # extract token action
            log = item
            if not isinstance(log['topics'], list) or len(log['topics']) == 0:
                continue

            # extract the erc20 and erc721 token transfers
            if log['topics'][0] == ERC20_TRANSFER_TOPIC:
                cached_is_token721 = self._cache_is_token721.get(log['address'])
                if cached_is_token721 is not None:
                    yield self.parse_token721_transfer_item(log=log) \
                        if cached_is_token721 is True \
                        else self.parse_token20_transfer_item(log=log)
                    continue
                logs = self._waiting_ctx.get(log['address'])
                if isinstance(logs, list):
                    logs.append(log)
                    continue
                self._waiting_ctx[log['address']] = [log]
                yield await self.get_request_is_token721(
                    contract_address=log['address'],
                    priority=response.request.priority,
                    cb_kwargs={'contract_address': log['address']},
                )
                continue

            # extract the erc1155 token transfers
            if log['topics'][0] == ERC1155_SINGLE_TRANSFER_TOPIC or \
                    log['topics'][0] == ERC1155_BATCH_TRANSFER_TOPIC:
                yield self.parse_token1155_transfer_item(log=log)
                continue

            # extract the token approve
            if log['topics'][0] == TOKEN_APPROVE_TOPIC:
                yield self.parse_token_approve_item(log=log)
                continue

            # extract the token approve all
            if log['topics'][0] == TOKEN_APPROVE_ALL_TOPIC:
                yield self.parse_token_approve_all_item(log=log)
                continue

    def parse_token721_transfer_item(self, log: EventLogItem) -> Union[Token721TransferItem, None]:
        # load log topics
        topics = log.get('topics')
        if any([
            topics is None,
            len(topics) < 1,
            topics[0] != ERC721_TRANSFER_TOPIC
        ]):
            return

        # load log data
        data = log.get('data')
        topics_with_data = topics + split_to_words(data)
        if len(topics_with_data) != 4:
            return

        # return item
        return Token721TransferItem(
            transaction_hash=log['transaction_hash'],
            log_index=log['log_index'],
            block_number=log['block_number'],
            timestamp=log['timestamp'],
            contract_address=log['address'],
            address_from=word_to_address(topics_with_data[1]),
            address_to=word_to_address(topics_with_data[2]),
            token_id=hex_to_dec(topics_with_data[3]),
        )

    def parse_token20_transfer_item(self, log: EventLogItem) -> Union[Token20TransferItem, None]:
        # load log topics
        topics = log.get('topics')
        if any([
            topics is None,
            len(topics) < 1,
            topics[0] != ERC721_TRANSFER_TOPIC
        ]):
            return

        # load log data
        data = log.get('data')
        topics_with_data = topics + split_to_words(data)
        if len(topics_with_data) != 4:
            return

        # return item
        return Token20TransferItem(
            transaction_hash=log['transaction_hash'],
            log_index=log['log_index'],
            block_number=log['block_number'],
            timestamp=log['timestamp'],
            contract_address=log['address'],
            address_from=word_to_address(topics_with_data[1]),
            address_to=word_to_address(topics_with_data[2]),
            value=hex_to_dec(topics_with_data[3]),
        )

    def parse_token1155_transfer_item(self, log: EventLogItem) -> Union[Token1155TransferItem, None]:
        # load logs data
        topics = log.get('topics')
        data = log.get('data')
        topics_with_data = topics + split_to_words(data)

        # generate erc1155 token single transfers
        if topics[0] == ERC1155_SINGLE_TRANSFER_TOPIC:
            if len(topics_with_data) < 5 + 1:
                return
            return Token1155TransferItem(
                transaction_hash=log.get('transaction_hash', ''),
                log_index=log.get('log_index'),
                block_number=log.get('block_number'),
                timestamp=log['timestamp'],
                contract_address=log['address'],
                address_operator=word_to_address(topics_with_data[1]),
                address_from=word_to_address(topics_with_data[2]),
                address_to=word_to_address(topics_with_data[3]),
                token_ids=[hex_to_dec(topics_with_data[4])],
                values=[hex_to_dec(topics_with_data[5])],
            )

        # generate erc1155 token batch transfers
        if topics[0] == ERC1155_BATCH_TRANSFER_TOPIC:
            # About 1 + 3 + 3
            # 1: skip the token transfer topics
            # 3: skip the operator, from, and to address
            # 3: skip the array-length pointer and the array length
            words_list = [hex_to_dec(word) for word in topics_with_data[1 + 3 + 3:]]
            if len(topics_with_data) < 5 + 1 or len(words_list) % 2 != 1:
                return
            mid_idx = len(words_list) >> 1
            return Token1155TransferItem(
                transaction_hash=log.get('transaction_hash', ''),
                log_index=log.get('log_index'),
                block_number=log.get('block_number'),
                timestamp=log['timestamp'],
                contract_address=log['address'],
                address_operator=word_to_address(topics_with_data[1]),
                address_from=word_to_address(topics_with_data[2]),
                address_to=word_to_address(topics_with_data[3]),
                token_ids=words_list[:mid_idx],
                values=words_list[mid_idx + 1:],
            )

    def parse_token_approve_item(self, log: EventLogItem):
        # load log topics
        topics = log.get('topics')
        if any([
            topics is None,
            len(topics) < 1,
            topics[0] != TOKEN_APPROVE_TOPIC
        ]):
            return

        # load log data
        data = log.get('data')
        topics_with_data = topics + split_to_words(data)
        if len(topics_with_data) != 4:
            return

        return TokenApprovalItem(
            transaction_hash=log['transaction_hash'],
            log_index=log['log_index'],
            block_number=log['block_number'],
            timestamp=log['timestamp'],
            contract_address=log['address'],
            address_from=word_to_address(topics_with_data[1]),
            address_to=word_to_address(topics_with_data[2]),
            value=hex_to_dec(topics_with_data[3]),
        )

    def parse_token_approve_all_item(self, log):
        # load log topics
        topics = log.get('topics')
        if any([
            topics is None,
            len(topics) < 1,
            topics[0] != TOKEN_APPROVE_ALL_TOPIC
        ]):
            return

        # load log data
        data = log.get('data')
        topics_with_data = topics + split_to_words(data)
        if len(topics_with_data) != 4:
            return

        return TokenApprovalAllItem(
            transaction_hash=log['transaction_hash'],
            log_index=log['log_index'],
            block_number=log['block_number'],
            timestamp=log['timestamp'],
            contract_address=log['address'],
            address_from=word_to_address(topics_with_data[1]),
            address_to=word_to_address(topics_with_data[2]),
            approved=bool(hex_to_dec(topics_with_data[3])),
        )

    @log_debug_tracing
    def parse_is_token721(self, response: scrapy.http.Response, **kwargs):
        is_token721 = False
        try:
            data = json.loads(response.text)
            if data.get('result') is not None:
                result = parse_bytes_data(data['result'], ['bool', ])
                if result is not None and len(result) > 0 and result[0] is True:
                    is_token721 = True

            # set the cache
            self._cache_is_token721.set(kwargs['contract_address'], is_token721)

            # process waiting items
            logs = self._waiting_ctx.pop(kwargs['contract_address'])
            for log in logs:
                yield self.parse_token721_transfer_item(log=log) \
                    if is_token721 is True \
                    else self.parse_token20_transfer_item(log=log)
        except:
            traceback.print_exc()

    @log_debug_tracing
    def errback_parse_is_token721(self, failure):
        kwargs = failure.request.cb_kwargs

        # process waiting items
        logs = self._waiting_ctx.pop(kwargs['contract_address'])
        for log in logs:
            yield self.parse_token20_transfer_item(log=log)

    async def get_request_is_token721(
            self, contract_address: str, priority: int, cb_kwargs: dict
    ) -> Union[scrapy.Request, None]:
        # detect ERC721, return if contract is ERC721
        # see https://ethereum.stackexchange.com/questions/44880/erc-165-query-on-erc-721-implementation
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{
                    'to': contract_address,
                    "data": "0x01ffc9a780ac58cd00000000000000000000000000000000000000000000000000000000",
                }, 'latest'
                ],
                "id": int(time.time() * 1000000),  # ensure not be filtered with the same fingerprint
            }),
            priority=priority,
            callback=self.parse_is_token721,
            errback=self.errback_parse_is_token721,
            cb_kwargs=cb_kwargs,
        )


class TokenPropertyMiddleware(LogMiddleware):
    def __init__(self):
        self.provider_bucket = None
        self._cache_property = LRUCache(getattr(settings, 'MIDDLE_CACHE_SIZE', 2 ** 16))
        self._waiting_ctx = dict()  # addr -> token transfers

    def _init_by_spider(self, spider):
        if self.provider_bucket is not None:
            return
        if getattr(spider, 'middleware_providers') and \
                spider.middleware_providers.get(self.__class__.__name__):
            self.provider_bucket = spider.middleware_providers[self.__class__.__name__]
        else:
            self.provider_bucket = spider.provider_bucket

    async def process_spider_output(self, response, result, spider):
        self._init_by_spider(spider)

        # filter and process the result flow
        async for item in result:
            yield item
            if not any([
                isinstance(item, Token20TransferItem),
                isinstance(item, Token721TransferItem),
                isinstance(item, Token1155TransferItem),
                isinstance(item, TokenApprovalItem),
                isinstance(item, TokenApprovalAllItem)
            ]):
                continue

            # generate item if cached
            contract_address = item['contract_address']
            cached_property = self._cache_property.get(contract_address)
            if cached_property is not None:
                yield TokenPropertyItem(
                    contract_address=contract_address,
                    name=cached_property.get('name', ''),
                    token_symbol=cached_property.get('token_symbol', ''),
                    decimals=cached_property.get('decimals', -1),
                    total_supply=cached_property.get('total_supply', -1),
                    cb_kwargs={'@token_action': item},
                )
                continue

            # add items waiting for processing
            if isinstance(self._waiting_ctx.get(contract_address), list):
                self._waiting_ctx[contract_address].append(item)
                continue
            self._waiting_ctx[contract_address] = [item]

            # generate requests for fetching property
            request_kwargs = [
                {'property_key': 'name', 'func': 'name()', 'return_type': ["string", ]},
                {'property_key': 'token_symbol', 'func': 'symbol()', 'return_type': ["string", ]},
                {'property_key': 'token_symbol', 'func': 'symbol()', 'return_type': ["bytes32", ]},
                {'property_key': 'token_symbol', 'func': 'SYMBOL()', 'return_type': ["string", ]},
                {'property_key': 'token_symbol', 'func': 'SYMBOL()', 'return_type': ["bytes32", ]},
                {'property_key': 'decimals', 'func': 'decimals()', 'return_type': ["uint8", ]},
                {'property_key': 'decimals', 'func': 'DECIMALS()', 'return_type': ["uint8", ]},
                {'property_key': 'total_supply', 'func': 'totalSupply()', 'return_type': ["uint256", ]},
            ]
            token_property = {'semaphore': -len(request_kwargs)}
            for kwargs in request_kwargs:
                yield await self.get_request_token_property(
                    contract_address=contract_address,
                    priority=response.request.priority,
                    cb_kwargs={
                        'contract_address': contract_address,
                        'token_property': token_property,
                        '@token_action': item,
                    },
                    **kwargs
                )

    @log_debug_tracing
    async def parse_token_property(self, response: scrapy.http.Response, **kwargs):
        return_type = kwargs['return_type']
        try:
            result = json.loads(response.text)
            result = result.get('result')
            result = parse_bytes_data(result, return_type)
            if result is not None:
                result = result[0] if not isinstance(result[0], bytes) else result[0].decode()
                result = result.replace('\0', '') if isinstance(result, str) else result
                property_key = kwargs['property_key']
                property_value = kwargs['token_property'].get(property_key)
                if property_value is None or result > property_value:
                    kwargs['token_property'][property_key] = result

            # check the property is available or not
            kwargs['token_property']['semaphore'] += 1
            if kwargs['token_property']['semaphore'] < 0:
                return
            self._cache_property.set(kwargs['contract_address'], kwargs['token_property'])

            # generate items
            token_action_items = self._waiting_ctx.pop(kwargs['contract_address'])
            token_property = kwargs['token_property']
            for item in token_action_items:
                yield TokenPropertyItem(
                    contract_address=kwargs['contract_address'],
                    name=token_property.get('name', ''),
                    token_symbol=token_property.get('token_symbol', ''),
                    decimals=token_property.get('decimals', -1),
                    total_supply=token_property.get('total_supply', -1),
                    cb_kwargs={'@token_action': item},
                )
        except:
            traceback.print_exc()

    @log_debug_tracing
    def errback_parse_token_property(self, failure):
        kwargs = failure.request.cb_kwargs
        try:
            kwargs['token_property']['semaphore'] += 1
            if kwargs['token_property']['semaphore'] < 0:
                return
            self._cache_property.set(kwargs['contract_address'], kwargs['token_property'])

            # generate items
            token_action_items = self._waiting_ctx.pop(kwargs['contract_address'])
            token_property = kwargs['token_property']
            for item in token_action_items:
                yield TokenPropertyItem(
                    contract_address=kwargs['contract_address'],
                    name=token_property.get('name', ''),
                    token_symbol=token_property.get('token_symbol', ''),
                    decimals=token_property.get('decimals', -1),
                    total_supply=token_property.get('total_supply', -1),
                    cb_kwargs={'@token_action': item},
                )
        except:
            pass

    async def get_request_token_property(
            self, contract_address: str, priority: int,
            property_key: str, func: str, return_type: List, cb_kwargs: dict,
    ) -> Union[scrapy.Request, None]:
        # generate request
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [
                    {'to': contract_address, "data": Web3.keccak(text=func).hex()[:2 + 8]},
                    'latest'
                ],
                "id": int(time.time() * 1000000),  # ensure not be filtered with the same fingerprint
            }),
            priority=priority,
            callback=self.parse_token_property,
            errback=self.errback_parse_token_property,
            cb_kwargs={
                'property_key': property_key,
                'return_type': return_type,
                **cb_kwargs,
            },
        )
