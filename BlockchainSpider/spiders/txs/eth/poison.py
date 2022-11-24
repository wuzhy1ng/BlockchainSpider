import logging

from BlockchainSpider.items import SubgraphTxItem
from BlockchainSpider.spiders.txs.eth._meta import TxsETHSpider
from BlockchainSpider.strategies import Poison
from BlockchainSpider.tasks import AsyncSubgraphTask


class TxsETHPoisonSpider(TxsETHSpider):
    name = 'txs.eth.poison'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # task map
        self.task_map = dict()
        self.depth = int(kwargs.get('depth', 2))

    def start_requests(self):
        # load source nodes
        if self.filename is not None:
            infos = self.load_task_info_from_json(self.filename)
            for i, info in enumerate(infos):
                self.task_map[i] = AsyncSubgraphTask(
                    strategy=Poison(
                        source=info['source'],
                        depth=int(info.get('depth', 2)),
                    ),
                    **info
                )
        elif self.source is not None:
            self.task_map[0] = AsyncSubgraphTask(
                strategy=Poison(
                    source=self.source,
                    depth=self.depth,
                ),
                **self.info
            )

        # generate requests
        for tid in self.task_map.keys():
            task = self.task_map[tid]
            for txs_type in task.info['txs_types']:
                yield self.txs_req_getter[txs_type](
                    address=task.info['source'],
                    **{
                        'depth': 1,
                        'startblock': task.info['start_blk'],
                        'endblock': task.info['end_blk'],
                        'task_id': tid
                    }
                )

    def _parse_txs(self, response, func_next_page_request, **kwargs):
        # reload task id
        tid = kwargs['task_id']
        task = self.task_map[tid]

        # parse data from response
        txs = self.load_txs_from_response(response)
        if txs is None:
            kwargs['retry'] = kwargs.get('retry', 0) + 1
            if kwargs['retry'] > self.max_retry:
                self.log(
                    message="On parse: failed on %s" % response.url,
                    level=logging.ERROR,
                )
                return
            self.log(
                message="On parse: Get error status from %s, retrying %d" % (response.url, kwargs['retry']),
                level=logging.WARNING,
            )
            yield func_next_page_request(
                address=kwargs['address'],
                **{k: v for k, v in kwargs.items() if k != 'address'}
            )
            return

        # tip for parse data successfully
        self.log(
            message='On parse: Extend {} from seed of {}, depth {}'.format(
                kwargs['address'], task.info['source'], kwargs['depth']
            ),
            level=logging.INFO
        )

        # save tx
        for tx in txs:
            yield SubgraphTxItem(source=task.info['source'], tx=tx, task_info=task.info)

        # push data to task
        task.push(
            node=kwargs['address'],
            edges=txs,
            cur_depth=kwargs['depth'],
        )

        # next address request
        if txs is None or len(txs) < 10000 or task.info['auto_page'] is False:
            for item in task.pop():
                yield from self.gen_txs_requests(
                    address=item['node'],
                    depth=item['depth'],
                    startblock=task.info['start_blk'],
                    endblock=task.info['end_blk'],
                    task_id=tid,
                )
        # next page request
        else:
            yield func_next_page_request(
                address=kwargs['address'],
                **{
                    'startblock': self.get_max_blk(txs),
                    'endblock': task.info['end_blk'],
                    'depth': kwargs['depth'],
                    'task_id': kwargs['task_id']
                }
            )

    def parse_external_txs(self, response, **kwargs):
        yield from self._parse_txs(response, self.get_external_txs_request, **kwargs)

    def parse_internal_txs(self, response, **kwargs):
        yield from self._parse_txs(response, self.get_internal_txs_request, **kwargs)

    def parse_erc20_txs(self, response, **kwargs):
        yield from self._parse_txs(response, self.get_erc20_txs_request, **kwargs)

    def parse_erc721_txs(self, response, **kwargs):
        yield from self._parse_txs(response, self.get_erc721_txs_request, **kwargs)
