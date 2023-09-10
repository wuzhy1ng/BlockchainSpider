import json
import logging
import re
import time

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import TransactionItem
from BlockchainSpider.utils.bucket import AsyncItemBucket
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.web3 import hex_to_dec


class Web3TransactionSpider(scrapy.Spider):
    name = 'trans.web3'
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

        # output dir and transaction hash
        self.out_dir = kwargs.get('out')
        self.txhashs = [
            item for item in kwargs.get('hash', '').split(',')
            if re.search(r"(0x[0-9a-f]{64})", item, re.IGNORECASE | re.ASCII)
        ]

        # provider settings
        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 3),
        )

        # set sync key
        self.sync_item_key = 'sync_item'

    def start_requests(self):
        request = self.get_request_web3_client_version()
        time.sleep(1 / self.provider_bucket.qps)
        yield request

    @log_debug_tracing
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
        for i, txhash in enumerate(self.txhashs):
            yield await self.get_request_eth_transaction(
                txhash=txhash,
                priority=len(self.txhashs) - i,
                cb_kwargs={'txhash': txhash, 'sync_item': {'txhash': txhash}},
            )

    @log_debug_tracing
    async def parse_transaction(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')

        # parse external transaction
        yield TransactionItem(
            transaction_hash=result.get('hash', ''),
            transaction_index=hex_to_dec(result.get('transactionIndex')),
            block_hash=result.get('blockHash', ''),
            block_number=hex_to_dec(result.get('blockNumber')),
            timestamp=hex_to_dec(result.get('timestamp')),
            address_from=result['from'] if result.get('from') else '',
            address_to=result['to'] if result.get('to') else '',
            value=hex_to_dec(result.get('value')),
            gas=hex_to_dec(result.get('gas')),
            gas_price=hex_to_dec(result.get('gasPrice')),
            nonce=hex_to_dec(result.get('nonce')),
            input=result.get('input', ''),
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

    async def get_request_eth_transaction(
            self, txhash: str, priority: int, cb_kwargs: dict = None
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "eth_getTransactionByHash",
                "params": [txhash],
                "id": 1
            }),
            priority=priority,
            callback=self.parse_transaction,
            cb_kwargs=cb_kwargs if cb_kwargs else dict(),
        )
