import argparse
import csv
import os
from typing import List

from extractors._meta import BaseExtractor


class MergeExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()

        parser = argparse.ArgumentParser()
        parser.description = 'Merge transaction data'
        parser.add_argument('-i', '--input', help='input raw data folder', dest='in_dir', type=str, default=None)
        parser.add_argument('-o', '--output', help='output data folder', dest='out_dir', type=str, default=None)

        self.args = parser.parse_args()
        assert self.args.in_dir and self.args.out_dir, 'input and output folder needed!'
        if not os.path.exists(self.args.out_dir):
            os.makedirs(self.args.out_dir)

    def extract(self, *args, **kwargs):
        txs_fns = list()
        for fn in os.listdir(self.args.in_dir):
            fn = os.path.join(self.args.in_dir, fn)
            if not os.path.isdir(fn):
                txs_fns.append(fn)
        self.merge_txs(txs_fns, os.path.join(self.args.out_dir, 'merged_txs.csv'))

        imp_fns = list()
        for fn in os.listdir(os.path.join(self.args.in_dir, 'importance')):
            fn = os.path.join(self.args.in_dir, 'importance', fn)
            imp_fns.append(fn)
        self.merge_importance(imp_fns, os.path.join(self.args.out_dir, 'merged_importance.csv'))

    def merge_txs(self, file_list: List[str], output_file: str):
        with open(output_file, 'w', encoding='utf-8', newline='\n') as out_file:
            writer = csv.writer(out_file)
            header_written = False

            for file_name in file_list:
                with open(file_name, 'r', encoding='utf-8', newline='\n') as in_file:
                    reader = csv.reader(in_file)
                    header = next(reader)
                    if not header_written:
                        writer.writerow(header)
                        header_written = True
                    for row in reader:
                        writer.writerow(row)

    def merge_importance(self, file_list: List[str], output_file: str):
        node2item = {}
        headers = None
        for file_name in file_list:
            with open(file_name, 'r') as in_file:
                reader = csv.reader(in_file)
                headers = next(reader)
                for row in reader:
                    row = {h: row[i] for i, h in enumerate(headers)}
                    node = row.pop('node')
                    if not node2item.get(node):
                        node2item[node] = row
                        node2item[node]['importance'] = float(node2item[node]['importance'])
                        continue
                    node2item[node]['importance'] += float(row.get('importance'))

        with open(output_file, 'w', encoding='utf-8', newline='\n') as out_file:
            writer = csv.writer(out_file)
            writer.writerow(headers)
            for node, item in node2item.items():
                writer.writerow([item.get(h, node) for h in headers])
