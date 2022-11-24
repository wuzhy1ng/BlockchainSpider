import csv
import os

from BlockchainSpider.items import ImportanceItem, SubgraphTxItem


class SubgraphTxsPipeline:
    def __init__(self):
        self.file_map = dict()

    def process_item(self, item, spider):
        if spider.out_dir is None or not isinstance(item, SubgraphTxItem):
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
            self.file_map[key] = open(fn, 'w', newline='\n', encoding='utf-8')
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
    def process_item(self, item, spider):
        if spider.out_dir is None or not isinstance(item, ImportanceItem):
            return item

        # load task info
        info = item['task_info']
        out_dir = os.path.join(info['out_dir'], 'importance')

        # create output dir
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # write item
        fn = os.path.join(out_dir, '%s.csv' % item['source'])
        with open(fn, 'w', newline='\n') as f:
            writer = csv.writer(f)
            writer.writerow(['node', 'importance'])
            for k, v in item['importance'].items():
                writer.writerow([k, v])

        return item
