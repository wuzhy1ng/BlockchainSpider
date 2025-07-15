import csv
import os

from BlockchainSpider.items import AccountTransferItem
from BlockchainSpider.items.subgraph import RankItem, UTXOTransferItem
from BlockchainSpider.pipelines.sync import unpacked_sync_item


class TransferDeduplicatePipeline:
    def __init__(self):
        self.vis = set()

    @unpacked_sync_item
    def process_item(self, item, spider):
        # deduplicate account transfers
        if isinstance(item, AccountTransferItem):
            if item['id'] in self.vis:
                return None
            self.vis.add(item['id'])

        # deduplicate UTXO transfers
        elif isinstance(item, UTXOTransferItem):
            if item['id'] in self.vis:
                return None
            self.vis.add(item['id'])

        return item


class AccountTransfer2csvPipeline:
    def __init__(self):
        self.out_dir = './data'
        self.file = None
        self.file_mode = 'w'
        self.writer = None
        self.item_type = AccountTransferItem
        self.fields = list(AccountTransferItem.fields.keys())
        if 'id' in self.fields:
            self.fields.remove('id')

    def open_spider(self, spider):
        self.out_dir = spider.__dict__.get('out', self.out_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.file_mode = spider.__dict__.get('out_mode', self.file_mode)
        fn = '%s.csv' % self.item_type.__name__
        path = os.path.join(self.out_dir, fn)

        # process output fields
        fields = spider.__dict__.get('out_fields', None)
        if fields is not None:
            fields = fields.split(',')
            self.fields = fields
        self.fields.sort()

        # init the output file
        has_old_file = os.path.exists(path)
        self.file = open(path, self.file_mode, encoding='utf-8', newline='\n')
        self.writer = csv.writer(self.file)
        if self.file_mode == 'a' and has_old_file:
            return
        self.writer.writerow(self.fields)

    @unpacked_sync_item
    def process_item(self, item, spider):
        if self.out_dir is None or not isinstance(item, self.item_type):
            return item
        row_data = list()
        for field in self.fields:
            value = item.get(field)
            if value is not None:
                row_data.append(value)
                continue
            kwargs = item.get_context_kwargs()
            value = kwargs.get(field, '')
            row_data.append(value)
        self.writer.writerow(row_data)
        return item

    def close_spider(self, spider):
        self.file.close()


class UTXOTransfer2csvPipeline(AccountTransfer2csvPipeline):
    def __init__(self):
        super().__init__()
        self.item_type = UTXOTransferItem
        self.fields = list(UTXOTransferItem.fields.keys())
        if 'id' in self.fields:
            self.fields.remove('id')


class Rank2csvPipeline:
    def __init__(self):
        self.out_dir = './data'
        self.latest_item = None

    def open_spider(self, spider):
        self.out_dir = spider.__dict__.get('out', self.out_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)

    @unpacked_sync_item
    def process_item(self, item, spider):
        if self.out_dir is None or not isinstance(item, RankItem):
            return item
        data = item['data']
        ranks = list(data.items())
        ranks.sort(key=lambda x: x[1], reverse=True)
        path = os.path.join(
            self.out_dir,
            '%s.csv' % RankItem.__name__,
        )
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            w = csv.writer(f)
            w.writerow(['address', 'rank'])
            for addr, val in ranks:
                w.writerow([addr, val])
        return item
