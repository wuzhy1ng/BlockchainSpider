import csv
import json
import logging

import scrapy

from BlockchainSpider.items import TxItem
from BlockchainSpider.settings import TXS_ETH_ORIGINAL_URL, SCAN_APIKEYS
from BlockchainSpider.strategies import BFS
from BlockchainSpider.utils.apikey import StaticAPIKeyBucket
from BlockchainSpider.utils.url import URLBuilder


class TxsETHBFSSpider(scrapy.Spider):
    name = 'txs.eth.bfs'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # input source nodes
        self.source = kwargs.get('source', None)
        self.filename = kwargs.get('file', None)
        assert self.source or self.filename, "`source` or `file` arguments are needed"

        # output dir
        self.out_dir = kwargs.get('out', './data')

        # task map
        self.task_map = dict()
        self.strategy = BFS
        self.depth = int(kwargs.get('depth', 2))

        # apikey bucket
        self.apikey_bucket = StaticAPIKeyBucket(SCAN_APIKEYS)

    def start_requests(self):
        # load source nodes
        source_nodes = set()
        if self.filename is not None:
            with open(self.filename, 'r') as f:
                for row in csv.reader(f):
                    source_nodes.add(row[0])
                    self.task_map[row[0]] = {
                        'strategy': self.strategy(
                            source=row[0],
                            depth=self.depth,
                        )
                    }
        elif self.source is not None:
            source_nodes.add(self.source)
            self.task_map[self.source] = {
                'strategy': self.strategy(
                    source=self.source,
                    depth=self.depth,
                )
            }

        # generate requests
        for node in source_nodes:
            yield scrapy.Request(
                url=URLBuilder(TXS_ETH_ORIGINAL_URL).get({
                    'module': 'account',
                    'action': 'txlist',
                    'address': node,
                    'offset': 10000,
                    'page': 1,
                    'apikey': self.apikey_bucket.get()
                }),
                method='GET',
                dont_filter=True,
                cb_kwargs={
                    'source': node,
                    'address': node,
                    'page': 1,
                    'depth': 1,
                }
            )

    def parse(self, response, **kwargs):
        # parse data from response
        data = json.loads(response.text)
        if data['status'] == 0:
            logging.warning("On parse: Get error status from:%s" % response.url)
            return
        logging.info(
            'On parse: Extend {} from seed of {}, page {}, depth {}'.format(
                kwargs['address'], kwargs['source'], kwargs['page'], kwargs['depth']
            )
        )

        if isinstance(data['result'], list):
            # save tx
            for row in data['result']:
                yield TxItem(source=kwargs['source'], tx=row)

            # push data to strategy
            self.task_map[kwargs['source']]['strategy'].push(
                node=kwargs['address'],
                edges=data['result'],
                cur_depth=kwargs['depth'],
            )

            # next address request
            if data['result'] is None or len(data['result']) < 10000:
                strategy = self.task_map[kwargs['source']]['strategy']
                while True:
                    node, depth = strategy.pop()
                    if node is None:
                        break
                    yield scrapy.Request(
                        url=URLBuilder(TXS_ETH_ORIGINAL_URL).get({
                            'module': 'account',
                            'action': 'txlist',
                            'address': node,
                            'offset': 10000,
                            'page': 1,
                            'apikey': self.apikey_bucket.get()
                        }),
                        method='GET',
                        dont_filter=True,
                        cb_kwargs={
                            'source': kwargs['source'],
                            'address': node,
                            'page': kwargs['page'] + 1,
                            'depth': depth,
                        }
                    )
            # next page request
            else:
                yield scrapy.Request(
                    url=URLBuilder(TXS_ETH_ORIGINAL_URL).get({
                        'module': 'account',
                        'action': 'txlist',
                        'address': kwargs['address'],
                        'offset': 10000,
                        'page': kwargs['page'] + 1,
                        'apikey': self.apikey_bucket.get()
                    }),
                    method='GET',
                    dont_filter=True,
                    cb_kwargs={
                        'source': kwargs['source'],
                        'address': kwargs['address'],
                        'page': kwargs['page'] + 1,
                        'depth': kwargs['depth'],
                    }
                )
