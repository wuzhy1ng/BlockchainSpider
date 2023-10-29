from typing import Union

from BlockchainSpider import settings
from BlockchainSpider.items import EventLogItem, Token1155TransferItem, TokenApprovalAllItem
from BlockchainSpider.items import Token721TransferItem, Token20TransferItem, TokenApprovalItem
from BlockchainSpider.middlewares._meta import LogMiddleware
from BlockchainSpider.utils.token import ERC20_TRANSFER_TOPIC, is_token721_contract, ERC721_TRANSFER_TOPIC, \
    ERC1155_SINGLE_TRANSFER_TOPIC, ERC1155_BATCH_TRANSFER_TOPIC, TOKEN_APPROVE_TOPIC, \
    TOKEN_APPROVE_ALL_TOPIC
from BlockchainSpider.utils.web3 import split_to_words, word_to_address, hex_to_dec


class TokenMiddleware(LogMiddleware):
    def __init__(self):
        self.provider_bucket = None
        self.timeout = getattr(settings, 'DOWNLOAD_TIMEOUT', 120)

    async def process_spider_output(self, response, result, spider):
        if getattr(spider, 'middleware_providers') and \
                spider.middleware_providers.get(self.__class__.__name__):
            self.provider_bucket = spider.middleware_providers[self.__class__.__name__]
        else:
            self.provider_bucket = spider.provider_bucket

        # filter and process the result flow
        async for item in result:
            yield item
            if not isinstance(item, EventLogItem):
                continue

            # extract the erc20 and erc721 token transfers
            if item['topics'][0] == ERC20_TRANSFER_TOPIC:
                if await is_token721_contract(
                        address=item['address'],
                        provider_bucket=self.provider_bucket,
                        timeout=self.timeout,
                ):
                    yield self.parse_token721_transfer_item(log=item)
                    continue
                yield self.parse_token20_transfer_item(log=item)

            # extract the erc1155 token transfers
            if item['topics'][0] == ERC1155_SINGLE_TRANSFER_TOPIC or \
                    item['topics'][0] == ERC1155_BATCH_TRANSFER_TOPIC:
                yield self.parse_token1155_transfer_item(log=item)

            # extract the token approve
            if item['topics'][0] == TOKEN_APPROVE_TOPIC:
                yield self.parse_token_approve_item(log=item)

            # extract the token approve all
            if item['topics'][0] == TOKEN_APPROVE_ALL_TOPIC:
                yield self.parse_token_approve_all_item(log=item)

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
