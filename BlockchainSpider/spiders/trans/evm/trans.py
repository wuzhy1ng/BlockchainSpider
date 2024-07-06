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


class EVMTransactionSpider(scrapy.Spider):
    name = 'trans.evm'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.EVMTrans2csvPipeline': 299,
            'BlockchainSpider.pipelines.EVMTransDCFG2csvPipeline': 298,
            'BlockchainSpider.pipelines.EVMTransBloomFilterPipeline': 297,
        } if len(getattr(settings, 'ITEM_PIPELINES', dict())) == 0
        else getattr(settings, 'ITEM_PIPELINES', dict()),
        'SPIDER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.SyncMiddleware': 535,
            **getattr(settings, 'SPIDER_MIDDLEWARES', dict())
        },
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        available_middlewares = {
            'BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware': 542,
            'BlockchainSpider.middlewares.trans.TokenTransferMiddleware': 541,
            'BlockchainSpider.middlewares.trans.TokenPropertyMiddleware': 540,
            'BlockchainSpider.middlewares.trans.MetadataMiddleware': 539,
            'BlockchainSpider.middlewares.trans.TraceMiddleware': 538,
            'BlockchainSpider.middlewares.trans.ContractMiddleware': 537,
            'BlockchainSpider.middlewares.trans.DCFGMiddleware': 536,
        }
        middlewares = kwargs.get('enable')
        if middlewares is not None:
            spider_middlewares = spider.settings.getdict('SPIDER_MIDDLEWARES')
            for middleware in middlewares.split(','):
                assert middleware in available_middlewares
                spider_middlewares[middleware] = available_middlewares[middleware]
            spider.settings.set(
                name='SPIDER_MIDDLEWARES',
                value=spider_middlewares,
                priority=spider.settings.attributes['SPIDER_MIDDLEWARES'].priority,
            )
        return spider

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
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
        )

        # provider settings for specific data
        self.middleware_providers = {
            'TransactionReceiptMiddleware': AsyncItemBucket(
                items=kwargs['providers4receipt'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4receipt') else None,
            'TraceMiddleware': AsyncItemBucket(
                items=kwargs['providers4trace'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4trace') else None,
            'TokenTransferMiddleware': AsyncItemBucket(
                items=kwargs['providers4token_transfer'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4token_transfer') else None,
            'TokenPropertyMiddleware': AsyncItemBucket(
                items=kwargs['providers4token_property'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4token_property') else None,
            'MetadataMiddleware': AsyncItemBucket(
                items=kwargs['providers4metadata'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4metadata') else None,
            'ContractMiddleware': AsyncItemBucket(
                items=kwargs['providers4contract'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4contract') else None,
            'DCFGMiddleware': AsyncItemBucket(
                items=kwargs['providers4dcfg'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4dcfg') else None,
        }

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
                cb_kwargs={
                    'txhash': txhash,
                    self.sync_item_key: {'transaction_hash': txhash}
                },
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
