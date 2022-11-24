import logging

from BlockchainSpider import strategies
from BlockchainSpider.items import SubgraphTxItem, ImportanceItem
from BlockchainSpider.spiders.txs.eth._meta import TxsETHSpider
from BlockchainSpider.tasks import SyncSubgraphTask


class TxsETHTTRSpider(TxsETHSpider):
    name = 'txs.eth.ttr'
    allow_strategies = {'TTRBase', 'TTRWeight', 'TTRTime', 'TTRRedirect'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # task map
        self.task_map = dict()
        self.alpha = float(kwargs.get('alpha', 0.15))
        self.beta = float(kwargs.get('beta', 0.7))
        self.epsilon = float(kwargs.get('epsilon', 1e-3))

        self.strategy_cls = kwargs.get('strategy', 'TTRRedirect')
        assert self.strategy_cls in TxsETHTTRSpider.allow_strategies
        self.strategy_cls = getattr(strategies, self.strategy_cls)

    def start_requests(self):
        # load source infos
        if self.filename is not None:
            infos = self.load_task_info_from_json(self.filename)
            for i, info in enumerate(infos):
                strategy = info.get('strategy', 'TTRRedirect')
                assert strategy in TxsETHTTRSpider.allow_strategies
                strategy = getattr(strategies, strategy)

                self.task_map[i] = SyncSubgraphTask(
                    strategy=strategy(
                        source=info['source'],
                        alpha=float(info.get('alpha', 0.15)),
                        beta=float(info.get('beta', 0.7)),
                        epsilon=float(info.get('epsilon', 1e-3)),
                    ),
                    **{k: v for k, v in info.items() if k != 'strategy'}
                )
        elif self.source is not None:
            self.task_map[0] = SyncSubgraphTask(
                strategy=self.strategy_cls(
                    source=self.source,
                    alpha=self.alpha,
                    beta=self.beta,
                    epsilon=self.epsilon
                ),
                **self.info
            )

        # generate requests
        for tid in self.task_map.keys():
            task = self.task_map[tid]
            for txs_type in task.info['txs_types']:
                task.wait()
                yield self.txs_req_getter[txs_type](
                    address=task.info['source'],
                    **{
                        'residual': 1.0,
                        'startblock': task.info['start_blk'],
                        'endblock': task.info['end_blk'],
                        'task_id': tid
                    }
                )

    def _proess_response(self, response, func_txs_type_request, **kwargs):
        # reload task id
        tid = kwargs['task_id']
        task = self.task_map[tid]

        # parse data from response and handle error
        txs = self.load_txs_from_response(response)
        if txs is None:
            kwargs['retry'] = kwargs.get('retry', 0) + 1

            # retry if less than max retry count
            if kwargs['retry'] < self.max_retry:
                self.log(
                    message="On parse: Get error status from %s, retrying" % response.url,
                    level=logging.WARNING,
                )
                yield func_txs_type_request(
                    address=kwargs['address'],
                    **{k: v for k, v in kwargs.items() if k != 'address'}
                )
                return

            # fuse this address and generate next address request
            self.log(
                message="On parse: failed on %s" % response.url,
                level=logging.ERROR,
            )
            item = task.fuse(kwargs['address'])
            if item is not None:
                for txs_type in task.info['txs_types']:
                    task.wait()
                    yield self.txs_req_getter[txs_type](
                        address=item['node'],
                        **{
                            'startblock': task.info['start_blk'],
                            'endblock': task.info['end_blk'],
                            'residual': item['residual'],
                            'task_id': kwargs['task_id']
                        }
                    )
            return

        # tip for parse data successfully
        self.log(
            message='On parse: Extend {} from seed of {}, residual {}'.format(
                kwargs['address'], task.info['source'], kwargs['residual']
            ),
            level=logging.INFO
        )

        # push data to task and save tx
        for tx in task.push(
                node=kwargs['address'],
                edges=txs,
        ):
            yield SubgraphTxItem(source=task.info['source'], tx=tx, task_info=task.info)

        # save ttr
        yield ImportanceItem(
            source=task.info['source'],
            importance=task.strategy.p,
            task_info=task.info
        )

        if len(txs) < 10000 or task.info['auto_page'] is False:
            if task.is_locked():
                return

            # generate next address or finish
            item = task.pop()
            if item is None:
                return

            # next address request
            for txs_type in task.info['txs_types']:
                task.wait()
                yield self.txs_req_getter[txs_type](
                    address=item['node'],
                    **{
                        'startblock': task.info['start_blk'],
                        'endblock': task.info['end_blk'],
                        'residual': item['residual'],
                        'task_id': kwargs['task_id']
                    }
                )
        # next page request
        else:
            yield func_txs_type_request(
                address=kwargs['address'],
                **{
                    'startblock': self.get_max_blk(txs),
                    'endblock': task.info['end_blk'],
                    'residual': kwargs['residual'],
                    'task_id': kwargs['task_id']
                }
            )

    def parse_external_txs(self, response, **kwargs):
        yield from self._proess_response(response, self.get_external_txs_request, **kwargs)

    def parse_internal_txs(self, response, **kwargs):
        yield from self._proess_response(response, self.get_internal_txs_request, **kwargs)

    def parse_erc20_txs(self, response, **kwargs):
        yield from self._proess_response(response, self.get_erc20_txs_request, **kwargs)

    def parse_erc721_txs(self, response, **kwargs):
        yield from self._proess_response(response, self.get_erc721_txs_request, **kwargs)
