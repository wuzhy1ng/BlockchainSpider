import asyncio
import json
import logging
import time

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import BlockItem, TransactionItem
from BlockchainSpider.utils.bucket import AsyncItemBucket
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.enum import ETHDataTypes
from BlockchainSpider.utils.web3 import hex_to_dec


class Web3BlockTransactionSpider(scrapy.Spider):
    name = 'trans.block.web3'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.TransPipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        },
        'SPIDER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.trans.InterceptMiddleware': 542,
            'BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware': 541,
            'BlockchainSpider.middlewares.trans.TraceMiddleware': 540,
            'BlockchainSpider.middlewares.trans.TokenMiddleware': 539,
            'BlockchainSpider.middlewares.trans.MetadataMiddleware': 538,
            'BlockchainSpider.middlewares.trans.ContractMiddleware': 537,
            'BlockchainSpider.middlewares.SyncMiddleware': 536,
            **getattr(settings, 'SPIDER_MIDDLEWARES', dict())
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # output dir and block range
        self.out_dir = kwargs.get('out', './data')
        self.start_block = int(kwargs.get('start_blk', '0'))
        self.end_block = int(kwargs['end_blk']) if kwargs.get('end_blk') else None
        self._block_cursor = self.start_block
        self.blocks = [
            int(blk) for blk in kwargs['blocks'].split(',')
        ] if kwargs.get('blocks') else None

        # extract data types
        self.data_types = kwargs.get('types', 'meta,transaction').split(',')
        for data_type in self.data_types:
            assert ETHDataTypes.has(data_type)

        # block receipt method
        self.block_receipt_method = kwargs.get('block_receipt_method', 'eth_getBlockReceipts')

        # sync signal key
        self.sync_item_key = 'sync_item'

        # provider settings
        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 1),
        )

    def start_requests(self):
        request = self.get_request_web3_client_version()
        time.sleep(1 / self.provider_bucket.qps)
        yield request

    async def _start_requests(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')

        # start requests
        self.log(
            message="Detected client version: {}, {} is starting.".format(
                result, getattr(settings, 'BOT_NAME'),
            ),
            level=logging.INFO,
        )

        # generate the requests for discrete blocks
        if self.blocks is not None:
            for i, blk in enumerate(self.blocks):
                yield await self.get_request_eth_block_by_number(
                    block_number=blk,
                    priority=len(self.blocks) - i,
                    cb_kwargs={'sync_item': {'block_number': blk}},
                )
            return

        # generate the requests for continuous blocks
        if self.end_block is None:
            yield await self.get_request_eth_block_number()
            return
        end_block = self.end_block + 1
        for blk in range(self.start_block, end_block):
            yield await self.get_request_eth_block_by_number(
                block_number=blk,
                priority=end_block - blk,
                cb_kwargs={'sync_item': {'block_number': blk}},
            )

    @log_debug_tracing
    async def parse_eth_block_number(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')

        # generate more requests
        if result is not None:
            end_block = int(result, 16) + 1
            start_block, self._block_cursor = self._block_cursor, end_block
            for blk in range(start_block, end_block):
                yield await self.get_request_eth_block_by_number(
                    block_number=blk,
                    priority=end_block - blk,
                    cb_kwargs={'block_number': blk},
                )
        else:
            self.log(
                message="Result field is None on eth_getBlockNumber" +
                        "please ensure that whether the provider is available.",
                level=logging.ERROR
            )

        # next query of block number
        if self.end_block is not None:
            return
        self.log(
            message="Query the latest block number after 5 seconds...",
            level=logging.INFO
        )
        await asyncio.sleep(5)
        yield await self.get_request_eth_block_number()

    @log_debug_tracing
    async def parse_eth_get_block_by_number(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')

        yield BlockItem(
            block_hash=result.get('hash', ''),
            block_number=hex_to_dec(result.get('number')),
            parent_hash=result.get('parentHash', ''),
            difficulty=hex_to_dec(result.get('difficulty')),
            total_difficulty=hex_to_dec(result.get('totalDifficulty')),
            size=hex_to_dec(result.get('size')),
            transaction_hashes=list() if not result.get('transactions') else [
                item.get('hash', '') for item in result['transactions']
            ],
            gas_limit=hex_to_dec(result.get('gasLimit')),
            gas_used=hex_to_dec(result.get('gasUsed')),
            miner=result.get('miner', ''),
            receipts_root=result.get('receiptsRoot', ''),
            timestamp=hex_to_dec(result.get('timestamp')),
            logs_bloom=result.get('logsBloom', ''),
            nonce=hex_to_dec(result.get('nonce')),
        )

        # fetch receipt for each transaction if block receipt api unavailable
        timestamp = hex_to_dec(result.get('timestamp'))
        for item in result.get('transactions', list()):
            yield TransactionItem(
                transaction_hash=item.get('hash', ''),
                transaction_index=hex_to_dec(item.get('transactionIndex')),
                block_hash=item.get('blockHash', ''),
                block_number=hex_to_dec(item.get('blockNumber')),
                timestamp=timestamp,
                address_from=item['from'] if item.get('from') else '',
                address_to=item['to'] if item.get('to') else '',
                value=hex_to_dec(item.get('value')),
                gas=hex_to_dec(item.get('gas')),
                gas_price=hex_to_dec(item.get('gasPrice')),
                nonce=hex_to_dec(item.get('nonce')),
                input=item.get('input', ''),
            )

    def get_request_web3_client_version(self):
        return scrapy.Request(
            url=self.provider_bucket.items[0],
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "web3_clientVersion",
                "id": 1
            }),
            callback=self._start_requests,
        )

    async def get_request_eth_block_number(self) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "method": "eth_blockNumber",
                "params": [],
                "id": 1,
                "jsonrpc": "2.0"
            }),
            callback=self.parse_eth_block_number,
        )

    async def get_request_eth_block_by_number(
            self, block_number: int, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "eth_getBlockByNumber",
                "params": [
                    hex(block_number) if isinstance(block_number, int) else block_number,
                    True
                ],
                "id": 1
            }),
            callback=self.parse_eth_get_block_by_number,
            priority=priority,
            cb_kwargs=cb_kwargs,
        )