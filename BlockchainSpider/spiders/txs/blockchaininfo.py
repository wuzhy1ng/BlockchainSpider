import datetime
import json
import logging

import scrapy
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.misc import load_object

from BlockchainSpider import settings
from BlockchainSpider.items.subgraph import PopItem, StrategySnapshotItem, RankItem


class BlockchainInfoTxsSpider(scrapy.Spider):
    name = 'txs.blockchaininfo'
    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.txs.blockchaininfo.TransactionMiddleware': 536,
            'BlockchainSpider.middlewares.SyncMiddleware': 535,
            'BlockchainSpider.middlewares.txs.PushAdapterMiddleware': 534,
            **getattr(settings, 'SPIDER_MIDDLEWARES', dict())
        },
        'DOWNLOADER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.txs.PushDownloadMiddleware': 898,
            'BlockchainSpider.middlewares.txs.blockchaininfo.APIMemoryCacheMiddleware': 899,
            **getattr(settings, 'DOWNLOADER_MIDDLEWARES', dict())
        },
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.UTXOTransfer2csvPipeline': 298,
            'BlockchainSpider.pipelines.Rank2csvPipeline': 299,
        } if len(getattr(settings, 'ITEM_PIPELINES', dict())) == 0
        else getattr(settings, 'ITEM_PIPELINES', dict())
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.endpoint = kwargs.get('endpoint', 'https://api.blockchain.info/haskoin-store/btc')

        # input source nodes
        self.source = kwargs.get('source', '').lower()
        assert self.source != '', "`source` argument is needed"

        # load strategy
        strategy_cls = kwargs.get('strategy', 'BlockchainSpider.strategies.txs.BFS')
        strategy_cls = load_object(strategy_cls)
        self.strategy = strategy_cls(**kwargs)

        # load pop item cache
        self.context_pop_items = dict()  # node -> PopItem

    def start_requests(self):
        url = '/transaction/4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b'
        url = self.endpoint + url
        yield scrapy.Request(
            url=url, method='GET',
            dont_filter=True,
            callback=self._verify_endpoint,
            errback=self._errback_verify_endpoint,
        )

    def _verify_endpoint(self, response: scrapy.http.Response, **kwargs):
        data = json.loads(response.text)
        try:
            timestamp = data['time']
            timestamp = datetime.datetime.fromtimestamp(timestamp)
            timestamp = str(timestamp)
            self.log(
                message='Your endpoint is valid. Genesis tx is created in %s' % timestamp,
                level=logging.INFO
            )
            item = PopItem(node=self.source)
            item.set_context_kwargs(**self.__dict__)
            yield item
        except Exception as _:
            import traceback
            traceback.print_exc()
            self.log(
                message="Failed on connecting %s, "
                        "please check your network is available or not." % self.endpoint,
                level=logging.ERROR,
            )

    def _errback_verify_endpoint(self, failure):
        self.log(
            message="Failed on connecting %s, "
                    "please check your network is available or not." % self.endpoint,
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