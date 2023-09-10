import csv
import os

from BlockchainSpider.items.trans import TransactionItem, EventLogItem, TraceItem, ContractItem, \
    Token721TransferItem, Token20TransferItem, Token1155TransferItem, TokenApprovalItem, TokenApprovalAllItem, \
    TokenMetadataItem, NFTMetadataItem, TransactionReceiptItem


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
            TokenMetadataItem, NFTMetadataItem,
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
        self.filename2writer[fn].writerow(
            [item[k] for k in self.filename2headers[fn]]
        )
        return item

    def close_spider(self, spider):
        for file in self.filename2file.values():
            file.close()
