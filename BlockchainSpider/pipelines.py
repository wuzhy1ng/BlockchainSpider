# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import csv
import json
import os

from BlockchainSpider.items import LabelItem


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
