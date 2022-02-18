# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import csv
import json
import os

from BlockchainSpider.items import LabelItem, SubgraphTxItem, ImportanceItem, BlockMetaItem, BlockTxItem, CloseItem


class LabelsPipeline:
    def __init__(self):
        self.file = None

    def process_item(self, item, spider):
        if not isinstance(item, LabelItem):
            return item

        # init file from filename
        if self.file is None:
            fn = os.path.join(spider.out_dir, spider.name)
            if not os.path.exists(spider.out_dir):
                os.makedirs(spider.out_dir)
            self.file = open(fn, 'w')

        # write item
        json.dump({**item}, self.file)
        self.file.write('\n')
        return item

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()


class SubgraphTxsPipeline:
    def __init__(self):
        self.file_map = dict()
        self.out_dir = None

    def process_item(self, item, spider):
        if isinstance(item, CloseItem):
            info = item['task_info']
            key = '{}_{}'.format(item['source'], info['out_dir'])
            file = self.file_map.get(key)
            if file is not None:
                file.close()
            return item

        if not isinstance(item, SubgraphTxItem):
            return item

        # load task info
        info = item['task_info']
        out_dir = info['out_dir']
        fields = info['out_fields']

        # create output dir
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # init file
        key = '{}_{}'.format(item['source'], out_dir)
        if self.file_map.get(key) is None:
            fn = os.path.join(out_dir, '%s.csv' % item['source'])
            self.file_map[key] = open(fn, 'w', newline='', encoding='utf-8')
            csv.writer(self.file_map[key]).writerow(fields)

        # write item
        row = [item['tx'].get(field, '') for field in fields]
        csv.writer(self.file_map[key]).writerow(row)

        return item

    def close_spider(self, spider):
        # close all file
        for f in self.file_map.values():
            f.close()


class ImportancePipeline:
    def __init__(self):
        self.out_dir = None

    def process_item(self, item, spider):
        if not isinstance(item, ImportanceItem):
            return item

        # load task info
        info = item['task_info']
        out_dir = os.path.join(info['out_dir'], 'importance')

        # create output dir
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # write item
        fn = os.path.join(out_dir, '%s.csv' % item['source'])
        with open(fn, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['node', 'importance'])
            for k, v in item['importance'].items():
                writer.writerow([k, v])

        return item


class BlockPipeline:
    def __init__(self):
        self.files = dict()

    def process_item(self, item, spider):
        if not isinstance(item, BlockMetaItem) and not isinstance(item, BlockTxItem):
            return item

        # init file
        suffix = 'meta' if isinstance(item, BlockMetaItem) else item.get('tx_type')
        if self.files.get(suffix) is None:
            fn = os.path.join(spider.out_dir, '%s.%s' % (spider.name, suffix))
            if not os.path.exists(spider.out_dir):
                os.makedirs(spider.out_dir)
            self.files[suffix] = open(fn, 'w')

        # write item
        file = self.files[suffix]
        json.dump(item['info'], file)
        file.write('\n')
        return item
