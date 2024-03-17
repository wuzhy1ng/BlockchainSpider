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
            cls_name = item.__class__.__name__
            fn = os.path.join(spider.out_dir, '{}.csv'.format(cls_name))
            if not os.path.exists(spider.out_dir):
                os.makedirs(fn)
            self.file = open(fn, 'w', newline='\n', encoding='utf-8')
            self.writer = csv.DictWriter(self.file, item.keys())
            self.writer.writeheader()

        # write item
        self.writer.writerow(item)
        return item

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()
