import json
import os
import csv
from collections import OrderedDict
from BlockchainSpider.items.signature import SignatureItem,TransactionsItem


class SignaturePipeline:
    def __init__(self):
        self.file = None
        self.csv_writer = None
        self.headers_written = False  # 标记是否已经写入了表头

    def process_item(self, item, spider):
        if spider.out_dir is None:
            return item
        if not isinstance(item, SignatureItem):
            return item

        # 初始化 CSV 文件
        if self.file is None:
            fn = os.path.join(spider.out_dir, "signature.csv")  # 修改为 CSV 文件
            if not os.path.exists(spider.out_dir):
                os.makedirs(spider.out_dir)
            self.file = open(fn, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.file)

        # 获取字段名（表头）
        item_dict = OrderedDict(item)  # 以确定字段顺序
        if not self.headers_written:
            self.csv_writer.writerow(item_dict.keys())  # 写入表头
            self.headers_written = True

        # 写入 item 数据
        self.csv_writer.writerow(item_dict.values())

        return item

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()

class TransactionsPipeline:
    def __init__(self):
        self.file = None
        self.csv_writer = None
        self.headers_written = False  # 标记是否已经写入了表头

    def process_item(self, item, spider):
        if spider.out_dir is None:
            return item
        if not isinstance(item, TransactionsItem):
            return item

        # 初始化 CSV 文件
        if self.file is None:
            fn = os.path.join(spider.out_dir, "Transactions.csv")  # 修改为 CSV 文件
            if not os.path.exists(spider.out_dir):
                os.makedirs(spider.out_dir)
            self.file = open(fn, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.file)

        # 获取字段名（表头）
        item_dict = OrderedDict(item)  # 以确定字段顺序
        if not self.headers_written:
            self.csv_writer.writerow(item_dict.keys())  # 写入表头
            self.headers_written = True

        # 写入 item 数据
        self.csv_writer.writerow(item_dict.values())

        return item

    def close_spider(self, spider):
        if self.file is not None:
            self.file.close()