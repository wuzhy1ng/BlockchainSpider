import csv
import os

from contrib.mots.items import MotifTransactionRepresentationItem


class MoTSPipeline:
    def __init__(self):
        self.file = None
        self.writer = None
        self.headers = ['transaction_hash', *['M%i' % i for i in range(1, 16 + 1)]]

    def process_item(self, item, spider):
        if getattr(spider, 'out_dir') is None:
            return item
        if not isinstance(item, MotifTransactionRepresentationItem):
            return item

        # create output path
        if not os.path.exists(spider.out_dir):
            os.makedirs(spider.out_dir)

        # init output file
        fn = os.path.join(spider.out_dir, '%s.csv' % item.__class__.__name__)
        if not self.file:
            file = open(fn, 'w', encoding='utf-8', newline='\n')
            self.file = file

            # init writer
            writer = csv.writer(file)
            writer.writerow(self.headers)
            self.writer = writer

        # save to file
        self.writer.writerow([item[k] for k in self.headers])

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()
