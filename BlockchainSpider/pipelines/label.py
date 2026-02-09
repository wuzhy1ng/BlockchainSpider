import json
import os

from BlockchainSpider.items.label import LabelReportItem


class LabelReportPipeline:
    def __init__(self):
        self.file = None
        self.out_dir = './data'

    def open_spider(self, spider):
        if getattr(spider, 'out_dir'):
            self.out_dir = spider.out_dir
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)

    def process_item(self, item, spider):
        if not isinstance(item, LabelReportItem):
            return item

        # init file from filename
        if self.file is None:
            fn = os.path.join(self.out_dir, LabelReportItem.__name__)
            self.file = open(fn, 'a')

        # write item
        json.dump({**item}, self.file)
        self.file.write('\n')
        return item

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()
