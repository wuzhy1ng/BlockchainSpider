import csv
import os

from pybloom import ScalableBloomFilter

from BlockchainSpider.items.sync import SyncDataItem
from BlockchainSpider.items.trans import BlockItem, TransactionItem, EventLogItem, TraceItem, ContractItem, \
    Token721TransferItem, Token20TransferItem, Token1155TransferItem, TokenApprovalItem, TokenApprovalAllItem, \
    TokenPropertyItem, NFTMetadataItem, TransactionReceiptItem, DCFGItem, DCFGBlockItem, DCFGEdgeItem


class TransBloomFilterPipeline:
    def __init__(self):
        self._bloom4contract = ScalableBloomFilter(
            initial_capacity=1024,
            error_rate=1e-4,
            mode=ScalableBloomFilter.SMALL_SET_GROWTH,
        )
        self._bloom4token_property = ScalableBloomFilter(
            initial_capacity=1024,
            error_rate=1e-4,
            mode=ScalableBloomFilter.SMALL_SET_GROWTH,
        )

    def process_item(self, item, spider):
        if isinstance(item, ContractItem):
            if item['address'] in self._bloom4contract:
                return
            self._bloom4contract.add(item['address'])
            return item
        if isinstance(item, TokenPropertyItem):
            if item['contract_address'] in self._bloom4token_property:
                return
            self._bloom4token_property.add(item['contract_address'])
            return item
        return item


class Trans2csvPipeline:
    def __init__(self):
        self.filename2file = dict()
        self.filename2writer = dict()
        self.filename2headers = dict()
        self.accepted_item_cls = {
            cls.__name__: True for cls in [
                BlockItem, TransactionItem, TransactionReceiptItem,
                EventLogItem, TraceItem, ContractItem,
                Token721TransferItem, Token20TransferItem, Token1155TransferItem,
                TokenApprovalItem, TokenApprovalAllItem,
                TokenPropertyItem, NFTMetadataItem,
                SyncDataItem,
            ]
        }
        # self.executor = ProcessPoolExecutor(os.cpu_count())

    async def process_item(self, item, spider):
        if getattr(spider, 'out_dir') is None:
            return item
        if self.accepted_item_cls.get(item.__class__.__name__) is None:
            return item

        # create output path
        if not os.path.exists(spider.out_dir):
            os.makedirs(spider.out_dir)

        # init output file
        fn = os.path.join(spider.out_dir, '%s.csv' % item.__class__.__name__)
        if not self.filename2file.get(fn):
            file = open(fn, 'w', encoding='utf-8', newline='\n')
            self.filename2file[fn] = file

            # init headers
            headers = sorted(item.keys())
            self.filename2headers[fn] = headers

            # init writer
            writer = csv.writer(file)
            writer.writerow(headers)
            self.filename2writer[fn] = writer

        # save to file
        self.filename2writer[fn].writerow([
            item[k] for k in self.filename2headers[fn]
        ])
        return item

    def close_spider(self, spider):
        for file in self.filename2file.values():
            file.close()


class TransDCFG2csvPipeline(Trans2csvPipeline):
    def __init__(self):
        super().__init__()
        self._bloom4blocks = ScalableBloomFilter(
            initial_capacity=1024,
            error_rate=1e-4,
            mode=ScalableBloomFilter.SMALL_SET_GROWTH,
        )
        self._is_inited = False

    def init_csv_file(self, out_dir: str):
        self._is_inited = True
        for cls in [DCFGBlockItem, DCFGEdgeItem]:
            fn = os.path.join(out_dir, '%s.csv' % cls.__name__)
            file = open(fn, 'w', encoding='utf-8', newline='\n')
            self.filename2file[fn] = file

            # init headers
            headers = sorted(cls.fields.keys())
            self.filename2headers[fn] = headers

            # init writer
            writer = csv.writer(file)
            writer.writerow(headers)
            self.filename2writer[fn] = writer

    def process_item(self, item, spider):
        if getattr(spider, 'out_dir') is None:
            return item
        if not isinstance(item, DCFGItem):
            return item

        # create output path
        if not os.path.exists(spider.out_dir):
            os.makedirs(spider.out_dir)

        # init file objs
        if not self._is_inited:
            self.init_csv_file(spider.out_dir)

        # filter deduplicated blocks and save to files
        for block in item['blocks']:
            block_id = '{}#{}'.format(
                block['contract_address'],
                block['start_pc']
            )
            if block_id in self._bloom4blocks:
                continue
            self._bloom4blocks.add(block_id)
            fn = os.path.join(spider.out_dir, '%s.csv' % block.__class__.__name__)
            self.filename2writer[fn].writerow([
                block[k] for k in self.filename2headers[fn]
            ])

        # save edges
        for edge in item['edges']:
            fn = os.path.join(spider.out_dir, '%s.csv' % edge.__class__.__name__)
            self.filename2writer[fn].writerow([
                edge[k] for k in self.filename2headers[fn]
            ])

        return item
