import csv
import json
import logging
import urllib.parse

import scrapy

from BlockchainSpider.items import TxItem
from BlockchainSpider.spiders.txs.eth._meta import TxsETHSpider
from BlockchainSpider.strategies import Poison
from BlockchainSpider.tasks import AsyncTask


class TxsETHPoisonSpider(TxsETHSpider):
    name = 'txs.eth.poison'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # task map
        self.task_map = dict()
        self.strategy = Poison
        self.depth = int(kwargs.get('depth', 2))

    def start_requests(self):
        # load source nodes
        source_nodes = set()
        if self.filename is not None:
            with open(self.filename, 'r') as f:
                for row in csv.reader(f):
                    source_nodes.add(row[0])
                    self.task_map[row[0]] = AsyncTask(
                        strategy_cls=self.strategy,
                        source=row[0],
                        depth=self.depth,
                    )
        elif self.source is not None:
            source_nodes.add(self.source)
            self.task_map[self.source] = AsyncTask(
                strategy_cls=self.strategy,
                source=self.source,
                depth=self.depth,
            )

        # generate requests
        for node in source_nodes:
            yield from self.gen_txs_requests(node, **{
                'source': node,
                'depth': 1,
            })

    def _parse_txs(self, response, **kwargs):
        # parse data from response
        data = json.loads(response.text)
        if data['status'] == 0:
            logging.warning("On parse: Get error status from:%s" % response.url)
            return
        logging.info(
            'On parse: Extend {} from seed of {}, depth {}'.format(
                kwargs['address'], kwargs['source'], kwargs['depth']
            )
        )

        if isinstance(data['result'], list):
            # save tx
            for row in data['result']:
                yield TxItem(source=kwargs['source'], tx=row)

            # push data to task
            self.task_map[kwargs['source']].push(
                node=kwargs['address'],
                edges=data['result'],
                cur_depth=kwargs['depth'],
            )

            # next address request
            if data['result'] is None or len(data['result']) < 10000:
                task = self.task_map[kwargs['source']]
                for item in task.pop():
                    yield from self.gen_txs_requests(
                        source=kwargs['source'],
                        address=item['node'],
                        depth=item['depth']
                    )
            # next page request
            else:
                _url = response.url
                _url = urllib.parse.urlparse(_url)
                query_args = {k: v[0] if len(v) > 0 else None for k, v in urllib.parse.parse_qs(_url.query).items()}
                query_args['startblock'] = self.get_max_blk(data['result'])
                _url = '?'.join([
                    '%s://%s%s' % (_url.scheme, _url.netloc, _url.path),
                    urllib.parse.urlencode(query_args)
                ])
                yield scrapy.Request(
                    url=_url,
                    method='GET',
                    dont_filter=True,
                    cb_kwargs={
                        'source': kwargs['source'],
                        'address': kwargs['address'],
                        'depth': kwargs['depth'],
                    },
                    callback=self._parse_txs
                )

    def parse_external_txs(self, response, **kwargs):
        yield from self._parse_txs(response, **kwargs)

    def parse_internal_txs(self, response, **kwargs):
        yield from self._parse_txs(response, **kwargs)

    def parse_erc20_txs(self, response, **kwargs):
        yield from self._parse_txs(response, **kwargs)

    def parse_erc721_txs(self, response, **kwargs):
        yield from self._parse_txs(response, **kwargs)
