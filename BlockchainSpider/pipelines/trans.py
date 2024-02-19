import csv
import os

from pybloom import ScalableBloomFilter

from BlockchainSpider.items.trans import TransactionItem, EventLogItem, TraceItem, ContractItem, \
    Token721TransferItem, Token20TransferItem, Token1155TransferItem, TokenApprovalItem, TokenApprovalAllItem, \
    TokenPropertyItem, NFTMetadataItem, TransactionReceiptItem, DCFGBlockItem, DCFGEdgeItem
from BlockchainSpider.items.sync import SyncDataItem


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
        self._bloom4DCFGBlock = ScalableBloomFilter(
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
        if isinstance(item, DCFGBlockItem):
            block_id = '{}#{}'.format(
                item['contract_address'],
                item['start_pc']
            )
            if block_id in self._bloom4DCFGBlock:
                return
            self._bloom4DCFGBlock.add(block_id)
            return item
        return item


class TransPipeline:
    def __init__(self):
        self.filename2file = dict()
        self.filename2writer = dict()
        self.filename2headers = dict()

    def process_item(self, item, spider):
        if getattr(spider, 'out_dir') is None:
            return item
        if not any([isinstance(item, t) for t in [
            TransactionItem, TransactionReceiptItem,
            EventLogItem, TraceItem, ContractItem,
            Token721TransferItem, Token20TransferItem, Token1155TransferItem,
            TokenApprovalItem, TokenApprovalAllItem,
            TokenPropertyItem, NFTMetadataItem,
            DCFGBlockItem, DCFGEdgeItem, SyncDataItem,
        ]]):
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
