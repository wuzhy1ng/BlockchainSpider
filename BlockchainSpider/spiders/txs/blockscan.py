import json
import logging
import time
from typing import Iterable

import scrapy
from scrapy import Request
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.misc import load_object

from BlockchainSpider import settings
from BlockchainSpider.items.subgraph import PopItem, StrategySnapshotItem, RankItem
from BlockchainSpider.utils.bucket import AsyncItemBucket
from BlockchainSpider.utils.url import QueryURLBuilder


class BlockscanTxsSpider(scrapy.Spider):
    name = 'txs.blockscan'
    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.txs.blockscan.ExternalTransferMiddleware': 541,
            'BlockchainSpider.middlewares.txs.TokenFilterMiddleware': 537,
            'BlockchainSpider.middlewares.txs.DeduplicateFilterMiddleware': 536,
            'BlockchainSpider.middlewares.SyncMiddleware': 535,
            'BlockchainSpider.middlewares.txs.PushAdapterMiddleware': 534,
            **getattr(settings, 'SPIDER_MIDDLEWARES', dict())
        },
        'DOWNLOADER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.txs.PushDownloadMiddleware': 898,
            'BlockchainSpider.middlewares.txs.blockscan.APIMemoryCacheMiddleware': 899,
            **getattr(settings, 'DOWNLOADER_MIDDLEWARES', dict())
        },
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.AccountTransfer2csvPipeline': 298,
            'BlockchainSpider.pipelines.Rank2csvPipeline': 299,
        } if len(getattr(settings, 'ITEM_PIPELINES', dict())) == 0
        else getattr(settings, 'ITEM_PIPELINES', dict())
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)

        # mount the middleware chain
        available_middlewares = {
            'BlockchainSpider.middlewares.txs.blockscan.ExternalTransferMiddleware': 541,
            'BlockchainSpider.middlewares.txs.blockscan.InternalTransferMiddleware': 540,
            'BlockchainSpider.middlewares.txs.blockscan.Token20TransferMiddleware': 539,
            'BlockchainSpider.middlewares.txs.blockscan.Token721TransferMiddleware': 538,
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
        # input source nodes
        self.source = kwargs.get('source', '').lower()
        assert self.source != '', "`source` argument is needed"

        # load apikey and api endpoint
        self.endpoint = kwargs.get('endpoint', 'https://api.etherscan.io/api')
        self.apikey_bucket = AsyncItemBucket(
            items=kwargs['apikeys'].split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
        )

        # load strategy
        strategy_cls = kwargs.get('strategy', 'BlockchainSpider.strategies.txs.BFS')
        strategy_cls = load_object(strategy_cls)
        self.strategy = strategy_cls(**kwargs)

        # load pop item cache
        self.context_pop_items = dict()  # node -> PopItem

    def start_requests(self) -> Iterable[Request]:
        query_params = {
            'module': 'proxy',
            'action': 'eth_blockNumber',
            'apikey': self.apikey_bucket.items[0],
        }
        yield scrapy.Request(
            url=QueryURLBuilder(self.endpoint).get(query_params),
            method='GET',
            dont_filter=True,
            callback=self._verify_apikey,
        )

    def _verify_apikey(self, response: scrapy.http.Response, **kwargs):
        data = json.loads(response.text)
        try:
            int(data['result'], 16)
            self.log(
                message="Your ApiKeys are verified, the spider is starting...",
                level=logging.INFO,
            )
            time.sleep(1.0)
            item = PopItem(node=self.source)
            if self.__dict__.get('allowed_tokens') is not None:
                allow_tokens = self.__dict__.get('allowed_tokens').split(',')
                item.set_context_kwargs(allow_tokens=allow_tokens)
            yield item
        except Exception as _:
            import traceback
            traceback.print_exc()
            self.log(
                message="Failed on loading APIs of: %s, "
                        "please check your apikey or network..." % self.endpoint,
                level=logging.ERROR,
            )

    def _errback_verify_apikey(self, failure):
        self.log(
            message="Failed on loading APIs of: %s, "
                    "please check your apikey or network is available now." % self.endpoint,
            level=logging.ERROR,
        )
        if failure.check(HttpError):
            response = failure.value.response
            data = {
                'status': response.status,
                'body': response.body,
            }
            self.log(
                message="Failed response info: {}".format(data),
                level=logging.ERROR,
            )

    def push_pop(self, response, **kwargs):
        node, edges, context_kwargs = kwargs['node'], kwargs['edges'], kwargs['context']
        self.log(
            message='Pushing: {}, with {} transfers'.format(
                node, len(edges)
            ),
            level=logging.INFO
        )
        self.strategy.push(node, edges, **context_kwargs)

        # generate a strategy context item
        snapshot_data = self.strategy.get_context_snapshot()
        yield StrategySnapshotItem(data=snapshot_data)

        # generate the node ranks
        ranks = self.strategy.get_node_rank()
        yield RankItem(data=ranks)

        # pop account from the strategy
        node, context_kwargs = self.strategy.pop()
        if node is None:
            return
        self.log(
            message='Popping: {}, with args {}'.format(
                node, context_kwargs
            ),
            level=logging.INFO
        )
        pop_item = PopItem(node=node)
        pop_item.set_context_kwargs(**context_kwargs)
        yield pop_item
