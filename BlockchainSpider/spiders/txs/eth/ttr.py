import csv
import logging
import time

from BlockchainSpider import strategies
from BlockchainSpider.items import TxItem, PPRItem
from BlockchainSpider.spiders.txs.eth._meta import TxsETHSpider
from BlockchainSpider.tasks import SyncTask


class TxsETHTTRSpider(TxsETHSpider):
    name = 'txs.eth.ttr'
    allow_strategies = {'TTRBase', 'TTRWeight', 'TTRTime', 'TTRAggregate'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # task map
        self.task_map = dict()
        self.alpha = float(kwargs.get('alpha', 0.15))
        self.beta = float(kwargs.get('beta', 0.7))
        self.epsilon = float(kwargs.get('epsilon', 1e-3))

        self.strategy_cls = kwargs.get('strategy', 'TTRAggregate')
        assert self.strategy_cls in TxsETHTTRSpider.allow_strategies
        self.strategy_cls = getattr(strategies, self.strategy_cls)

    def start_requests(self):
        # load source nodes
        source_nodes = set()
        if self.filename is not None:
            with open(self.filename, 'r') as f:
                for row in csv.reader(f):
                    source_nodes.add(row[0])
                    self.task_map[row[0]] = SyncTask(
                        strategy=self.strategy_cls(
                            source=row[0],
                            alpha=self.alpha,
                            beta=self.beta,
                            epsilon=self.epsilon
                        ),
                        source=row[0],
                    )
        elif self.source is not None:
            source_nodes.add(self.source)
            self.task_map[self.source] = SyncTask(
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
            for txs_type in self.txs_types:
                now = time.time()
                self.task_map[node].wait(now)
                yield self.txs_req_getter[txs_type](
                    address=node,
                    **{
                        'source': node,
                        'residual': 1.0,
                        'wait_key': now,
                    }
                )

    # def _load_txs_from_response(self, response):
    #     data = json.loads(response.text)
    #     txs = None
    #     if isinstance(data.get('result'), list):
    #         txs = list()
    #         for tx in data['result']:
    #             if tx['from'] == '' or tx['to'] == '':
    #                 continue
    #             tx['value'] = int(tx['value'])
    #             tx['timeStamp'] = float(tx['timeStamp'])
    #
    #             if self.symbols and tx.get('tokenSymbol', 'ETH') not in self.symbols:
    #                 continue
    #             tx['symbol'] = '{}_{}'.format(tx.get('tokenSymbol', 'ETH'), tx.get('contractAddress'))
    #             txs.append(tx)
    #     return txs

    def parse_external_txs(self, response, **kwargs):
        # parse data from response
        txs = self.load_txs_from_response(response)
        if txs is None:
            self.log(
                message="On parse: Get error status from: %s" % response.url,
                level=logging.WARNING,
            )
            return
        self.log(
            message='On parse: Extend {} from seed of {}, residual {}'.format(
                kwargs['address'], kwargs['source'], kwargs['residual']
            ),
            level=logging.INFO
        )

        # push data to task and save tx
        for tx in self.task_map[kwargs['source']].push(
                node=kwargs['address'],
                edges=txs,
                wait_key=kwargs['wait_key']
        ):
            yield TxItem(source=kwargs['source'], tx=tx)

        if len(txs) < 10000 or self.auto_page is False:
            task = self.task_map[kwargs['source']]
            if task.is_locked():
                return

            # generate ppr item and finished
            item = task.pop()
            if item is None:
                yield PPRItem(source=kwargs['source'], ppr=task.strategy.p)
                return

            # next address request
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
        txs = self.load_txs_from_response(response)
        if txs is None:
            self.log(
                message="On parse: Get error status from: %s" % response.url,
                level=logging.WARNING,
            )
            return
        self.log(
            message='On parse: Extend {} from seed of {}, residual {}'.format(
                kwargs['address'], kwargs['source'], kwargs['residual']
            ),
            level=logging.INFO
        )

        # push data to task and save tx
        yield from self.task_map[kwargs['source']].push(
            node=kwargs['address'],
            edges=txs,
            wait_key=kwargs['wait_key']
        )

        if len(txs) < 10000 or self.auto_page is False:
            task = self.task_map[kwargs['source']]
            if task.is_locked():
                return

            # generate ppr item and finished
            item = task.pop()
            if item is None:
                yield PPRItem(source=kwargs['source'], ppr=task.strategy.p)
                return

            # next address request
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
        # parse data from response
        txs = self.load_txs_from_response(response)
        if txs is None:
            self.log(
                message="On parse: Get error status from: %s" % response.url,
                level=logging.WARNING,
            )
            return
        self.log(
            message='On parse: Extend {} from seed of {}, residual {}'.format(
                kwargs['address'], kwargs['source'], kwargs['residual']
            ),
            level=logging.INFO
        )

        # push data to task and save tx
        yield from self.task_map[kwargs['source']].push(
            node=kwargs['address'],
            edges=txs,
            wait_key=kwargs['wait_key']
        )

        if len(txs) < 10000 or self.auto_page is False:
            task = self.task_map[kwargs['source']]
            if task.is_locked():
                return

            # generate ppr item and finished
            item = task.pop()
            if item is None:
                yield PPRItem(source=kwargs['source'], ppr=task.strategy.p)
                return

            # next address request
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
            yield self.get_erc20_txs_request(
                address=kwargs['address'],
                **{
                    'source': kwargs['source'],
                    'residual': kwargs['residual'],
                    'wait_key': now
                }
            )

    def parse_erc721_txs(self, response, **kwargs):
        # TODO
        pass
