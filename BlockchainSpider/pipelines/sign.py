import csv
import os

from BlockchainSpider.items import SignItem


class SignsPipeline:
    def __init__(self):
        self.file = None
        self.writer = None

    def process_item(self, item, spider):
        if spider.out_dir is None or not isinstance(item, SignItem):
            return item

        # init file from filename
        if self.file is None:
            fn = os.path.join(spider.out_dir, spider.name, '.csv')
            if not os.path.exists(spider.out_dir):
                os.makedirs(spider.out_dir)
            self.file = open(fn, 'w', newline='\n', encoding='utf-8')
            self.writer = csv.DictWriter(self.file, item.keys())

        # write item
        self.writer.writerow(item)
        return item

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()
