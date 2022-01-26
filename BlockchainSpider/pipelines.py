# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import csv
import json
import os

from BlockchainSpider.items import LabelItem, TxItem, ImportanceItem


class LabelsPipeline:
    def __init__(self):
        self.file = None

    def process_item(self, item, spider):
        if not isinstance(item, LabelItem):
            return item

        # init file from filename
        if self.file is None:
            self.file = open(spider.out_filename, 'w')

        # write item
        json.dump({**item}, self.file)
        self.file.write('\n')
        return item

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()


class TxsPipeline:
    def __init__(self):
        self.file_map = dict()
        self.out_dir = None

    def process_item(self, item, spider):
        if not isinstance(item, TxItem):
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
