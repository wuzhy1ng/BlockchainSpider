# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import csv
import json
import os

from BlockchainSpider.items import LabelItem, TxItem, PPRItem


class LabelsPipeline:
    def __init__(self):
        self.file = None

    def process_item(self, item, spider):
        if not isinstance(item, LabelItem):
            return item

        # init file from filename
        if self.file is None:
            self.file = open(spider.out_filename, 'a')

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

        # create output dir
        if self.out_dir is None:
            if not os.path.exists(spider.out_dir):
                os.makedirs(spider.out_dir)
            self.out_dir = spider.out_dir

        # init file
        if self.file_map.get(item['source']) is None:
            fn = os.path.join(self.out_dir, '%s.csv' % item['source'])
            self.file_map[item['source']] = open(fn, 'w', newline='')
            csv.writer(self.file_map[item['source']]).writerow(spider.out_fields)

        # write item
        row = [item['tx'].get(field, '') for field in spider.out_fields]
        csv.writer(self.file_map[item['source']]).writerow(row)

        return item

    def close_spider(self, spider):
        # close all file
        for f in self.file_map.values():
            f.close()


class PPRPipeline:
    def __init__(self):
        self.out_dir = None

    def process_item(self, item, spider):
        if not isinstance(item, PPRItem):
            return item

        # create output dir
        if self.out_dir is None:
            self.out_dir = os.path.join(spider.out_dir, 'ppr')
            if not os.path.exists(self.out_dir):
                os.makedirs(self.out_dir)

        # write item
        fn = os.path.join(self.out_dir, '%s.csv' % item['source'])
        with open(fn, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['node', 'p'])
            for k, v in item['ppr'].items():
                writer.writerow([k, v])

        return item
