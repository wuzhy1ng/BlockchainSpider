import logging
import time

from BlockchainSpider.items import TxItem
from BlockchainSpider.spiders.txs.eth._meta import TxsETHSpider
from BlockchainSpider.strategies import BFS
from BlockchainSpider.tasks import AsyncTask


class TxsETHBFSSpider(TxsETHSpider):
    name = 'txs.eth.bfs'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # task map
        self.task_map = dict()
        self.depth = int(kwargs.get('depth', 2))

    def start_requests(self):
        # load source nodes
        if self.filename is not None:
            infos = self.load_task_info_from_csv(self.filename)
            for i, info in enumerate(infos):
                self.task_map[i] = AsyncTask(
                    strategy=BFS(
                        source=info['source'],
                        depth=info.get('depth', 2),
                    ),
                    **info
                )
        elif self.source is not None:
            self.task_map[0] = AsyncTask(
                strategy=BFS(
                    source=self.source,
                    depth=self.depth,
                ),
                **self.info
            )

        # generate requests
        for tid in self.task_map.keys():
            task = self.task_map[tid]
            for txs_type in task.info['txs_types']:
                now = time.time()
                task.wait(now)
                yield self.txs_req_getter[txs_type](
                    address=task.info['source'],
                    **{
                        'depth': 1,
                        'startblock': task.info['start_blk'],
                        'endblock': task.info['end_blk'],
                        'task_id': tid
                    }
                )
        # generate requests
        # for node in source_nodes:
        #     yield from self.gen_txs_requests(node, **{
        #         'source': node,
        #         'depth': 1,
        #     })

    def _parse_txs(self, response, func_next_page_request, **kwargs):
        # reload task id
        tid = kwargs['task_id']
        task = self.task_map[tid]

        # parse data from response
        txs = self.load_txs_from_response(response)
        if txs is None:
            self.log(
                message="On parse: Get error status from:%s" % response.url,
                level=logging.WARNING
            )
            return
        self.log(
            message='On parse: Extend {} from seed of {}, depth {}'.format(
                kwargs['address'], task.info['source'], kwargs['depth']
            ),
            level=logging.INFO
        )

        # save tx
        for tx in txs:
            yield TxItem(source=task.info['source'], tx=tx)

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
            now = time.time()
            task.wait(now)
            yield func_next_page_request(
                address=kwargs['address'],
                **{
                    'startblock': self.get_max_blk(txs),
                    'endblock': task.info['end_blk'],
                    'depth': kwargs['depth'],
                    'task_id': kwargs['task_id']
                }
            )

            # _url = response.url
            # _url = urllib.parse.urlparse(_url)
            # query_args = {k: v[0] if len(v) > 0 else None for k, v in urllib.parse.parse_qs(_url.query).items()}
            # query_args['startblock'] = self.get_max_blk(txs)
            # _url = '?'.join([
            #     '%s://%s%s' % (_url.scheme, _url.netloc, _url.path),
            #     urllib.parse.urlencode(query_args)
            # ])
            # yield scrapy.Request(
            #     url=_url,
            #     method='GET',
            #     dont_filter=True,
            #     cb_kwargs={
            #         'source': kwargs['source'],
            #         'address': kwargs['address'],
            #         'depth': kwargs['depth'],
            #     },
            #     callback=self._parse_txs
            # )

    def parse_external_txs(self, response, **kwargs):
        yield from self._parse_txs(response, self.get_external_txs_request, **kwargs)

    def parse_internal_txs(self, response, **kwargs):
        yield from self._parse_txs(response, self.get_internal_txs_request, **kwargs)

    def parse_erc20_txs(self, response, **kwargs):
        yield from self._parse_txs(response, self.get_erc20_txs_request, **kwargs)

    def parse_erc721_txs(self, response, **kwargs):
        yield from self._parse_txs(response, self.get_erc721_txs_request, **kwargs)
