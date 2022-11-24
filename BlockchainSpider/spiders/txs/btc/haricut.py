import csv
import json
import logging
import time

from BlockchainSpider.spiders.txs.btc._meta import TxsBTCSpider
from BlockchainSpider.strategies import Haircut
from BlockchainSpider.tasks import SyncSubgraphTask


class TxsBTCHaircutSpider(TxsBTCSpider):
    name = 'txs.btc.haircut'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # task map
        self.task_map = dict()
        self.min_weight = float(kwargs.get('min_weight', 1e-3))

    def start_requests(self):
        # load source nodes
        source_nodes = set()
        if self.filename is not None:
            with open(self.filename, 'r') as f:
                for row in csv.reader(f):
                    source_nodes.add(row[0])
                    self.task_map[row[0]] = SyncSubgraphTask(
                        strategy=Haircut(source=row[0], min_weight=self.min_weight),
                        source=row[0],
                    )
        elif self.source is not None:
            source_nodes.add(self.source)
            self.task_map[self.source] = SyncSubgraphTask(
                strategy=Haircut(source=self.source, min_weight=self.min_weight),
                source=self.source,
            )

        # generate requests
        for node in source_nodes:
            now = time.time()
            self.task_map[node].wait(now)
            yield self.get_tx_request(node, **{
                'source': node,
                'weight': 1.0,
                'wait_key': now,
            })

    def parse_tx(self, response, **kwargs):
        # parse data from response
        if response.status != 200:
            logging.warning("On parse: Get error status from:%s" % response.url)
            return
        data = json.loads(response.text)
        logging.info(
            'On parse: Extend {} from seed of {}, weight {}'.format(
                kwargs['hash'], kwargs['source'], kwargs['weight']
            )
        )

        # save input txs
        in_txs = self.parse_input_txs(data, **kwargs)
        yield from in_txs

        # save output txs
        out_txs = self.parse_output_txs(data, **kwargs)
        yield from out_txs

        # push data to task
        task = self.task_map[kwargs['source']]
        task.push(
            node=kwargs['hash'],
            edges=[item['tx'] for item in out_txs if item['tx']['to'] != ''],
            wait_key=kwargs['wait_key']
        )

        # next requests
        item = task.pop()
        if item is not None:
            now = time.time()
            task.wait(now)
            yield self.get_tx_request(item['node'], **{
                'source': kwargs['source'],
                'weight': item['weight'],
                'wait_key': now
            })
