import csv
import os

from BlockchainSpider.items import SourceCodeItem


class SourceCodePipeline:
    def __init__(self):
        self.file = None
        self.writer = None

    def process_item(self, item, spider):
        if spider.out_dir is None or not isinstance(item, SourceCodeItem):
            return item

        # init file from filename
        if self.file is None:
            fn = os.path.join(spider.out_dir, item.__class__.__name__ + '.csv')
            if not os.path.exists(spider.out_dir):
                os.makedirs(spider.out_dir)
            self.file = open(fn, 'w', newline='\n', encoding='utf-8')
            self.writer = csv.DictWriter(self.file, item.keys())
            self.writer.writeheader()

        # write item
        self.writer.writerow(item)
        return item

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()
