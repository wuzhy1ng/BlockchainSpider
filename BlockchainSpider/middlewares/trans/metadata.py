import asyncio
import json
import re
from typing import Union

import scrapy.http
from pybloom import ScalableBloomFilter
from scrapy import Request

from BlockchainSpider import settings
from BlockchainSpider.items import EventLogItem
from BlockchainSpider.items import TokenMetadataItem, Token20TransferItem, Token721TransferItem, \
    Token1155TransferItem, NFTMetadataItem
from BlockchainSpider.middlewares._meta import LogMiddleware
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.token import get_token_name, get_token_symbol, get_token_decimals, \
    get_token_total_supply
from BlockchainSpider.utils.web3 import web3_json_rpc, parse_bytes_data


class MetadataMiddleware(LogMiddleware):
    def __init__(self):
        self.provider_bucket = None
        self.timeout = getattr(settings, 'DOWNLOAD_TIMEOUT', 120)
        self.bloom4metadata = ScalableBloomFilter(
            initial_capacity=1024,
            error_rate=1e-4,
            mode=ScalableBloomFilter.SMALL_SET_GROWTH,
        )

    async def process_spider_output(self, response, result, spider):
        if self.provider_bucket is None:
            self.provider_bucket = spider.provider_bucket

        # filter and process the result flow
        async for item in result:
            yield item

            # extract the token metadata
            if any([
                isinstance(item, Token20TransferItem),
                isinstance(item, Token721TransferItem),
                isinstance(item, Token1155TransferItem),
            ]) and item['contract_address'] not in self.bloom4metadata:
                self.bloom4metadata.add(item['contract_address'])
                yield await self.parse_token_metadata_item(item=item)

            # extract the erc721 nft metadata
            if isinstance(item, Token721TransferItem):
                key = '{}_{}'.format(item['contract_address'], item['token_id'])
                if key in self.bloom4metadata:
                    continue
                self.bloom4metadata.add(key)
                yield await self.get_request_nft721_metadata(
                    contract_address=item['contract_address'],
                    token_id=item['token_id'],
                    cb_kwargs={'item_token721_transfer': item},
                )

            # extract the erc1155 nft metadata
            if isinstance(item, Token1155TransferItem):
                for i in range(len(item['token_ids'])):
                    if item['values'][i] > 1:
                        continue
                    key = '{}_{}'.format(item['contract_address'], item['token_ids'][i])
                    if key in self.bloom4metadata:
                        continue
                    self.bloom4metadata.add(key)
                    yield await self.get_request_nft1155_metadata(
                        contract_address=item['contract_address'],
                        token_id=item['token_ids'][i],
                        cb_kwargs={'item_token1155_transfer': item, 'index': i},
                    )

    async def parse_token_metadata_item(self, item: EventLogItem) -> TokenMetadataItem:
        tasks = list()
        tasks.append(asyncio.create_task(get_token_name(
            address=item['contract_address'],
            provider_bucket=self.provider_bucket,
            timeout=self.timeout,
        )))
        tasks.append(asyncio.create_task(get_token_symbol(
            address=item['contract_address'],
            provider_bucket=self.provider_bucket,
            timeout=self.timeout,
        )))
        tasks.append(asyncio.create_task(get_token_decimals(
            address=item['contract_address'],
            provider_bucket=self.provider_bucket,
            timeout=self.timeout,
        )))
        tasks.append(asyncio.create_task(get_token_total_supply(
            address=item['contract_address'],
            provider_bucket=self.provider_bucket,
            timeout=self.timeout,
        )))
        data = await asyncio.gather(*tasks)
        return TokenMetadataItem(
            address=item['contract_address'],
            name=data[0],
            token_symbol=data[1],
            decimals=data[2],
            total_supply=data[3],
        )

    @log_debug_tracing
    def parse_nft721_metadata_item(self, response: scrapy.http.Response, **kwargs):
        try:
            data = json.loads(response.text)
        except:
            return

        # recover the cached item and raw uri
        item = kwargs['item_token721_transfer']
        uri = kwargs['uri']

        # generate metadata item
        yield NFTMetadataItem(
            transaction_hash=item['transaction_hash'],
            log_index=item['log_index'],
            block_number=item['block_number'],
            timestamp=item['timestamp'],
            contract_address=item['contract_address'],
            token_id=item['token_id'],
            uri=uri,
            data=json.dumps(data),
        )

    @log_debug_tracing
    def parse_nft1155_metadata_item(self, response: scrapy.http.Response, **kwargs):
        try:
            data = json.loads(response.text)
        except:
            return

        # recover the cached item and raw uri
        item = kwargs['item_token1155_transfer']
        index = kwargs['index']
        uri = kwargs['uri']

        # generate metadata item
        yield NFTMetadataItem(
            transaction_hash=item['transaction_hash'],
            log_index=item['log_index'],
            block_number=item['block_number'],
            timestamp=item['timestamp'],
            contract_address=item['contract_address'],
            token_id=item['token_ids'][index],
            uri=uri,
            data=json.dumps(data),
        )

    async def get_request_nft721_metadata(
            self, contract_address: str, token_id: int, cb_kwargs: dict,
    ) -> Union[Request, None]:
        # fetch uri
        # see https://github.com/ethereum/EIPs/blob/master/EIPS/eip-721.md
        data = await web3_json_rpc(
            tx_obj={
                "id": 1,
                "jsonrpc": "2.0",
                "params": [{
                    "to": contract_address,
                    "data": '0xc87b56dd' + str.zfill(hex(token_id)[2:], 64)
                }, "latest"],
                "method": "eth_call"
            },
            provider=await self.provider_bucket.get(),
            timeout=self.timeout,
        )
        if data is None:
            return
        result = parse_bytes_data(data, ["string"])
        if result is None or len(result) < 1:
            return

        # generate metadata request
        uri: str = result[0]
        url = uri if not uri.startswith('ipfs://ipfs/') else uri.replace('ipfs://ipfs/', 'https://ipfs.io/ipfs/')
        url = uri if not uri.startswith('ipfs://') else uri.replace('ipfs://', 'https://ipfs.io/ipfs/')
        url = url if not url.startswith('//') else 'http:{}'.format(url)
        if re.search(
                r'[http|https|ipfs]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                url
        ) is None:
            return
        return Request(
            url=url,
            method='GET',
            callback=self.parse_nft721_metadata_item,
            cb_kwargs={**cb_kwargs, 'uri': uri},
        )

    async def get_request_nft1155_metadata(
            self, contract_address: str, token_id: int, cb_kwargs: dict,
    ) -> Union[Request, None]:
        # fetch uri
        # see https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1155.md
        data = await web3_json_rpc(
            tx_obj={
                "id": 1,
                "jsonrpc": "2.0",
                "params": [{
                    "to": contract_address,
                    "data": '0x0e89341c' + str.zfill(hex(token_id)[2:], 64)
                }, "latest"],
                "method": "eth_call"
            },
            provider=await self.provider_bucket.get(),
            timeout=self.timeout,
        )
        if data is None:
            return
        result = parse_bytes_data(data, ["string"])
        if result is None or len(result) < 1:
            return

        # generate metadata request
        uri: str = result[0]
        url = uri if not uri.startswith('ipfs://ipfs/') else uri.replace('ipfs://ipfs/', 'https://ipfs.io/ipfs/')
        url = uri if not uri.startswith('ipfs://') else uri.replace('ipfs://', 'https://ipfs.io/ipfs/')
        url = url if not url.startswith('//') else 'http:{}'.format(url)
        if re.search(
                r'[http|https|ipfs]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                url
        ) is None:
            return
        return Request(
            url=url,
            method='GET',
            callback=self.parse_nft1155_metadata_item,
            cb_kwargs={**cb_kwargs, 'uri': uri},
        )
