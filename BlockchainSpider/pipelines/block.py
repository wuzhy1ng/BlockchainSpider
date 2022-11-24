import csv
import os

from BlockchainSpider.items import BlockNumberItem, BlockMetaItem
from BlockchainSpider.items import ERCTokenItem, ExternalTransactionItem, InternalTransactionItem, \
    ERC20TokenTransferItem, ERC721TokenTransferItem, ERC1155TokenTransferItem, LogItem, TransactionMotifItem


class BlockPipeline:
    def __init__(self):
        self.files = dict()
        self.writers = dict()

    def process_item(self, item, spider):
        if spider.out_dir is None or not any([
            isinstance(item, BlockMetaItem),
            isinstance(item, ExternalTransactionItem),
            isinstance(item, InternalTransactionItem),
            isinstance(item, ERC20TokenTransferItem),
            isinstance(item, ERC721TokenTransferItem),
            isinstance(item, ERC1155TokenTransferItem),
            isinstance(item, LogItem),
            isinstance(item, ERCTokenItem),
        ]):
            return item

        # create output path
        if not os.path.exists(spider.out_dir):
            os.makedirs(spider.out_dir)

        # save item
        fn = os.path.join(spider.out_dir, type(item).__name__ + '.csv')
        if self.files.get(fn) is None:
            if not os.path.exists(fn):
                file = open(fn, 'w', newline='\n', encoding='utf-8')
                writer = csv.writer(file)
                writer.writerow(sorted(item.keys()))
            else:
                file = open(fn, 'a', newline='\n', encoding='utf-8')
                writer = csv.writer(file)
            self.files[fn] = file
            self.writers[fn] = writer

        self.writers[fn].writerow(
            [item[k] for k in sorted(item.keys())]
        )
        return item

    def close_spider(self, spider):
        for file in self.files.values():
            file.close()


class BlockNumberPipeline:
    def process_item(self, item, spider):
        if spider.out_dir is None or not isinstance(item, BlockNumberItem):
            return item

        # create output path
        if not os.path.exists(spider.out_dir):
            os.makedirs(spider.out_dir)

        # save last synced block number
        fn = os.path.join(spider.out_dir, 'last_synced_block.txt')
        with open(fn, 'w') as f:
            f.write(str(item['block_number']))
        return item


class BlockSemanticPipeline:
    def __init__(self):
        self.files = dict()
        self.writers = dict()

    def process_item(self, item, spider):
        if spider.out_dir is None or not isinstance(item, TransactionMotifItem):
            return item

        # create output path
        if not os.path.exists(spider.out_dir):
            os.makedirs(spider.out_dir)

        # save item
        fn = os.path.join(spider.out_dir, type(item).__name__ + '.csv')
        if self.files.get(fn) is None:
            if not os.path.exists(fn):
                file = open(fn, 'w', newline='\n', encoding='utf-8')
                writer = csv.writer(file)
                writer.writerow([
                    'transaction_hash',
                    *['M{}'.format(i) for i in sorted(item['frequency'].keys())]
                ])
            else:
                file = open(fn, 'a', newline='\n', encoding='utf-8')
                writer = csv.writer(file)
            self.files[fn] = file
            self.writers[fn] = writer

        self.writers[fn].writerow([
            item['transaction_hash'],
            *[item['frequency'][i] for i in sorted(item['frequency'].keys())]
        ])
        return item

    def close_spider(self, spider):
        for file in self.files.values():
            file.close()
