import csv
import json
import logging
import time

from BlockchainSpider.items import TxItem
from BlockchainSpider.spiders.txs.eth._meta import TxsETHSpider
from BlockchainSpider.strategies import TTR
from BlockchainSpider.tasks import SyncTask


class TxsETHTTRSpider(TxsETHSpider):
    name = 'txs.eth.ttr'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # task map
        self.task_map = dict()
        self.alpha = float(kwargs.get('alpha', 0.1))
        self.beta = float(kwargs.get('beta', 0.6))
        self.epsilon = float(kwargs.get('epsilon', 5e-5))
        self.phi = float(kwargs.get('phi', 5e-5))

    def start_requests(self):
        # load source nodes
        source_nodes = set()
        if self.filename is not None:
            with open(self.filename, 'r') as f:
                for row in csv.reader(f):
                    source_nodes.add(row[0])
                    self.task_map[row[0]] = SyncTask(
                        strategy=TTR(source=row[0], alpha=self.alpha, beta=self.beta, epsilon=self.epsilon),
                        source=row[0],
                    )
        elif self.source is not None:
            source_nodes.add(self.source)
            self.task_map[self.source] = SyncTask(
                strategy=TTR(source=self.source, alpha=self.alpha, beta=self.beta, epsilon=self.epsilon),
                source=self.source,
            )

        # generate requests
        for node in source_nodes:
            for txs_type in self.txs_types:
                now = time.time()
                self.task_map[node].wait(now)
                yield self.txs_req_getter[txs_type](
                    address=node,
                    **{
                        'source': node,
                        'residual': 1.0,
                        'wait_key': now
                    }
                )

    def _load_txs_from_response(self, response):
        data = json.loads(response.text)
        txs = None
        if isinstance(data.get('result'), list):
            txs = data['result']
            for i in range(len(txs)):
                txs[i]['value'] = float(txs[i]['value'])
                txs[i]['timeStamp'] = int(txs[i]['timeStamp'])
        return txs

    def parse_external_txs(self, response, **kwargs):
        # parse data from response
        txs = self._load_txs_from_response(response)
        if txs is None:
            logging.warning("On parse: Get error status from: %s" % response.url)
            return
        logging.info(
            'On parse: Extend {} from seed of {}, residual {}'.format(
                kwargs['address'], kwargs['source'], kwargs['residual']
            )
        )

        # push data to task and save tx
        for tx in self.task_map[kwargs['source']].push(
                node=kwargs['address'],
                edges=txs,
                wait_key=kwargs['wait_key']
        ):
            yield TxItem(source=kwargs['source'], tx=tx)

        # next address request
        if len(txs) < 10000:
            task = self.task_map[kwargs['source']]
            item = task.pop()
            if item is None:
                return
            for txs_type in self.txs_types:
                now = time.time()
                self.task_map[kwargs['source']].wait(now)
                yield self.txs_req_getter[txs_type](
                    address=item['node'],
                    **{
                        'source': kwargs['source'],
                        'residual': item['residual'],
                        'wait_key': now
                    }
                )
        # next page request
        else:
            now = time.time()
            self.task_map[kwargs['source']].wait(now)
            yield self.get_external_txs_request(
                address=kwargs['address'],
                **{
                    'source': kwargs['source'],
                    'startblock': self.get_max_blk(txs),
                    'residual': kwargs['residual'],
                    'wait_key': now
                }
            )

    def parse_internal_txs(self, response, **kwargs):
        # parse data from response
        txs = self._load_txs_from_response(response)
        if txs is None:
            logging.warning("On parse: Get error status from: %s" % response.url)
            return
        logging.info(
            'On parse: Extend {} from seed of {}, residual {}'.format(
                kwargs['address'], kwargs['source'], kwargs['residual']
            )
        )

        # push data to task and save tx
        yield from self.task_map[kwargs['source']].push(
            node=kwargs['address'],
            edges=txs,
            wait_key=kwargs['wait_key']
        )

        # next address request
        if len(txs) < 10000:
            task = self.task_map[kwargs['source']]
            item = task.pop()
            if item is None:
                return
            for txs_type in self.txs_types:
                now = time.time()
                self.task_map[kwargs['source']].wait(now)
                yield self.txs_req_getter[txs_type](
                    address=item['node'],
                    **{
                        'source': kwargs['source'],
                        'residual': item['residual'],
                        'wait_key': now
                    }
                )
        # next page request
        else:
            now = time.time()
            self.task_map[kwargs['source']].wait(now)
            yield self.get_internal_txs_request(
                address=kwargs['address'],
                **{
                    'source': kwargs['source'],
                    'residual': kwargs['residual'],
                    'wait_key': now
                }
            )

    def parse_erc20_txs(self, response, **kwargs):
        # TODO
        pass

    def parse_erc721_txs(self, response, **kwargs):
        # TODO
        pass
