import csv
import json
import logging

from BlockchainSpider.spiders.txs.btc._meta import TxsBTCSpider
from BlockchainSpider.strategies import Poison
from BlockchainSpider.tasks import AsyncSubgraphTask


class TxsBTCBFSSpider(TxsBTCSpider):
    name = 'txs.btc.poison'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # task map
        self.task_map = dict()
        self.depth = int(kwargs.get('depth', 2))

    def start_requests(self):
        # load source nodes
        source_nodes = set()
        if self.filename is not None:
            with open(self.filename, 'r') as f:
                for row in csv.reader(f):
                    source_nodes.add(row[0])
                    self.task_map[row[0]] = AsyncSubgraphTask(
                        strategy=Poison(source=row[0], depth=self.depth),
                        source=row[0],
                    )
        elif self.source is not None:
            source_nodes.add(self.source)
            self.task_map[self.source] = AsyncSubgraphTask(
                strategy=Poison(source=self.source, depth=self.depth),
                source=self.source,
            )

        # generate requests
        for node in source_nodes:
            yield self.get_tx_request(node, **{
                'source': node,
                'depth': 1,
            })

    def parse_tx(self, response, **kwargs):
        # parse data from response
        if response.status != 200:
            logging.warning("On parse: Get error status from:%s" % response.url)
            return
        data = json.loads(response.text)
        logging.info(
            'On parse: Extend {} from seed of {}, depth {}'.format(
                kwargs['hash'], kwargs['source'], kwargs['depth']
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
            cur_depth=kwargs['depth'],
        )

        # next requests
        for item in task.pop():
            yield self.get_tx_request(item['node'], **{
                'source': kwargs['source'],
                'depth': item['depth'],
            })
