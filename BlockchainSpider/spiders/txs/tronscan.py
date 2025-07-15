import json
import logging
import time
from typing import Iterable

import scrapy
from scrapy import Request

from BlockchainSpider import settings
from BlockchainSpider.items.subgraph import PopItem
from BlockchainSpider.spiders.txs.blockscan import BlockscanTxsSpider
from BlockchainSpider.utils.url import QueryURLBuilder


class TronscanTxsSpider(BlockscanTxsSpider):
    name = 'txs.tronscan'
    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.txs.TokenFilterMiddleware': 537,
            'BlockchainSpider.middlewares.SyncMiddleware': 536,
            'BlockchainSpider.middlewares.txs.PushAdapterMiddleware': 535,
            **getattr(settings, 'SPIDER_MIDDLEWARES', dict())
        },
        'DOWNLOADER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.txs.PushDownloadMiddleware': 898,
            'BlockchainSpider.middlewares.txs.tronscan.APIMemoryCacheMiddleware': 899,
            **getattr(settings, 'DOWNLOADER_MIDDLEWARES', dict())
        },
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.TransferDeduplicatePipeline': 297,
            'BlockchainSpider.pipelines.AccountTransfer2csvPipeline': 298,
            'BlockchainSpider.pipelines.Rank2csvPipeline': 299,
        } if len(getattr(settings, 'ITEM_PIPELINES', dict())) == 0
        else getattr(settings, 'ITEM_PIPELINES', dict())
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BlockscanTxsSpider, cls).from_crawler(crawler, *args, **kwargs)

        # mount the middleware chain
        available_middlewares = {
            'BlockchainSpider.middlewares.txs.tronscan.TRXTRC10TransferMiddleware': 539,
            'BlockchainSpider.middlewares.txs.tronscan.TRC20TRC721TransferMiddleware': 538,
        }
        middlewares = kwargs.get('enable')
        spider_middlewares = spider.settings.getdict('SPIDER_MIDDLEWARES')
        if middlewares is not None:
            for middleware in middlewares.split(','):
                assert middleware in available_middlewares
                spider_middlewares[middleware] = available_middlewares[middleware]
        else:
            default_middleware = 'BlockchainSpider.middlewares.txs.tronscan.TRXTRC10TransferMiddleware'
            spider_middlewares[default_middleware] = 538
        spider.settings.set(
            name='SPIDER_MIDDLEWARES',
            value=spider_middlewares,
            priority=spider.settings.attributes['SPIDER_MIDDLEWARES'].priority,
        )
        return spider

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.endpoint = 'https://apilist.tronscanapi.com'

    def start_requests(self) -> Iterable[Request]:
        query_params = {
            'limit': 10,
            'address': 'T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb',
        }
        url = '%s/api/new/transfer' % self.endpoint
        url = QueryURLBuilder(url).get(query_params)
        apikey = self.apikey_bucket.items[0]
        yield scrapy.Request(
            url=url, method='GET',
            headers={'TRON-PRO-API-KEY': apikey},
            dont_filter=True,
            callback=self._verify_apikey,
            errback=self._errback_verify_apikey,
        )

    def _verify_apikey(self, response: scrapy.http.Response, **kwargs):
        data = json.loads(response.text)
        try:
            assert isinstance(data['data'], list)
            self.log(
                message="Your ApiKeys are verified, the spider is starting...",
                level=logging.INFO,
            )
            time.sleep(1.0)
            item = PopItem(node=self.source)
            item.set_context_kwargs(**self.__dict__)
            yield item
        except Exception as _:
            self.log(
                message="Failed on loading APIs of: %s, "
                        "please check your apikey or network..." % self.endpoint,
                level=logging.ERROR,
            )
