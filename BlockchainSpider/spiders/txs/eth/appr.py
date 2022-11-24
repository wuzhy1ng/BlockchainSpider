import logging

from BlockchainSpider.items import SubgraphTxItem, ImportanceItem
from BlockchainSpider.spiders.txs.eth._meta import TxsETHSpider
from BlockchainSpider.strategies import APPR
from BlockchainSpider.tasks import SyncSubgraphTask


class TxsETHAPPRSpider(TxsETHSpider):
    name = 'txs.eth.appr'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # task map
        self.task_map = dict()
        self.alpha = float(kwargs.get('alpha', 0.15))
        self.epsilon = float(kwargs.get('epsilon', 1e-3))

    def start_requests(self):
        # load source nodes
        if self.filename is not None:
            infos = self.load_task_info_from_json(self.filename)
            for i, info in enumerate(infos):
                self.task_map[i] = SyncSubgraphTask(
                    strategy=APPR(
                        source=info['source'],
                        alpha=float(info.get('alpha', 0.15)),
                        epsilon=float(info.get('epsilon', 1e-3)),
                    ),
                    **info
                )
        elif self.source is not None:
            self.task_map[0] = SyncSubgraphTask(
                strategy=APPR(
                    source=self.source,
                    alpha=self.alpha,
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

    def _process_response(self, response, func_txs_type_request, **kwargs):
        # reload task id
        tid = kwargs['task_id']
        task = self.task_map[tid]

        # parse data from response
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

        # save ppr
        yield ImportanceItem(
            source=task.info['source'],
            importance=task.strategy.p,
            task_info=task.info
        )

        # push data to task and save tx
        for tx in task.push(
                node=kwargs['address'],
                edges=txs,
        ):
            yield SubgraphTxItem(source=task.info['source'], tx=tx, task_info=task.info)

        # next address request
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
        yield from self._process_response(response, self.get_external_txs_request, **kwargs)

    def parse_internal_txs(self, response, **kwargs):
        yield from self._process_response(response, self.get_internal_txs_request, **kwargs)

    def parse_erc20_txs(self, response, **kwargs):
        yield from self._process_response(response, self.get_erc20_txs_request, **kwargs)

    def parse_erc721_txs(self, response, **kwargs):
        yield from self._process_response(response, self.get_erc721_txs_request, **kwargs)
