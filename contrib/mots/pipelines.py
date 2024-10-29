import asyncio
import csv
import functools
import os
from concurrent.futures import ProcessPoolExecutor

from BlockchainSpider.items import SyncItem, TransactionItem, TraceItem, Token721TransferItem, Token20TransferItem, \
    Token1155TransferItem
from contrib.mots.highorder import HighOrderMotifCounter


class MoTSPipeline:
    def __init__(self):
        self.file = None
        self.writer = None
        self.executor = ProcessPoolExecutor(max_workers=max(1, min(os.cpu_count() - 1, 61)))

    def open_spider(self, spider):
        out_dir = getattr(spider, 'out_dir')
        if out_dir is None:
            return
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        path = os.path.join(out_dir, 'MoTS.csv')
        self.file = open(path, 'w', encoding='utf-8', newline='\n')
        self.writer = csv.writer(self.file)
        headers = ['transaction_hash', *['M%i' % i for i in range(1, 16 + 1)]]
        self.writer.writerow(headers)

    async def process_item(self, item, spider):
        if self.file is None:
            return item
        if not isinstance(item, SyncItem):
            return item

        # collect money transfer items
        txhash2edges = dict()
        transfer_type_names = [
            cls.__name__ for cls in [
                TransactionItem, TraceItem,
                Token721TransferItem, Token20TransferItem, Token1155TransferItem,
            ]
        ]
        for name in transfer_type_names:
            if not item['data'].get(name):
                continue
            for transfer_item in item['data'][name]:
                txhash = transfer_item['transaction_hash']
                if not txhash2edges.get(txhash):
                    txhash2edges[txhash] = list()
                txhash2edges[txhash].append({
                    'address_from': transfer_item['address_from'],
                    'address_to': transfer_item['address_to'],
                })

        # create calc vec task
        txhashes, tasks = list(), list()
        for txhash, edges in txhash2edges.items():
            txhashes.append(txhash)
            func = functools.partial(HighOrderMotifCounter(motif_size=4).count, edges)
            task = asyncio.get_running_loop().run_in_executor(
                executor=self.executor,
                func=func,
            )
            tasks.append(task)

        # start the tasks
        vecs = await asyncio.gather(*tasks)
        for txhash, vec in zip(txhashes, vecs):
            vec_list = [vec[i] for i in range(1, 16 + 1)]
            self.writer.writerow([txhash, *vec_list])

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()
