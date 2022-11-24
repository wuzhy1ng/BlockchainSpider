import csv
import json
import logging
import time

from BlockchainSpider.items import SubgraphTxItem, ImportanceItem
from BlockchainSpider.spiders.txs.btc._meta import TxsBTCSpider
from BlockchainSpider import strategies
from BlockchainSpider.tasks import SyncSubgraphTask


class TxsBTCTTRSpider(TxsBTCSpider):
    name = 'txs.btc.ttr'
    allow_strategies = {'TTRBase', 'TTRWeight'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # task map
        self.task_map = dict()
        self.alpha = float(kwargs.get('alpha', 0.15))
        self.beta = float(kwargs.get('beta', 0.7))
        self.epsilon = float(kwargs.get('epsilon', 1e-4))

        self.strategy_cls = kwargs.get('strategy', 'TTRWeight')
        assert self.strategy_cls in TxsBTCTTRSpider.allow_strategies
        self.strategy_cls = getattr(strategies, self.strategy_cls)

    def start_requests(self):
        # load source nodes
        source_nodes = set()
        if self.filename is not None:
            with open(self.filename, 'r') as f:
                for row in csv.reader(f):
                    source_nodes.add(row[0])
                    self.task_map[row[0]] = SyncSubgraphTask(
                        strategy=self.strategy_cls(
                            source=self.source,
                            alpha=self.alpha,
                            beta=self.beta,
                            epsilon=self.epsilon
                        ),
                        source=row[0],
                    )
        elif self.source is not None:
            source_nodes.add(self.source)
            self.task_map[self.source] = SyncSubgraphTask(
                strategy=self.strategy_cls(
                    source=self.source,
                    alpha=self.alpha,
                    beta=self.beta,
                    epsilon=self.epsilon
                ),
                source=self.source,
            )

        # generate requests
        for node in source_nodes:
            now = time.time()
            self.task_map[node].wait(now)
            yield self.get_tx_request(node, **{
                'source': node,
                'residual': 1.0,
                'wait_key': now,
            })

    def parse_tx(self, response, **kwargs):
        # parse data from response
        if response.status != 200:
            logging.warning("On parse: Get error status from:%s" % response.url)
            return
        data = json.loads(response.text)
        logging.info(
            'On parse: Extend {} from seed of {}, residual {}'.format(
                kwargs['hash'], kwargs['source'], kwargs['residual']
            )
        )

        # get input txs
        in_txs = self.parse_input_txs(data, **kwargs)

        # get output txs
        out_txs = self.parse_output_txs(data, **kwargs)

        # push data to task and save txs
        task = self.task_map[kwargs['source']]
        for tx in task.push(
                node=kwargs['hash'],
                edges=[item['tx'] for item in in_txs + out_txs if item['tx']['to'] != ''],
                wait_key=kwargs['wait_key']
        ):
            yield SubgraphTxItem(source=kwargs['source'], tx=tx)

        # next requests
        item = task.pop()
        if item is not None:
            now = time.time()
            task.wait(now)
            yield self.get_tx_request(item['node'], **{
                'source': kwargs['source'],
                'residual': item['residual'],
                'wait_key': now
            })
        else:
            # generate ppr item and finished
            yield ImportanceItem(source=kwargs['source'], importance=task.strategy.p)
