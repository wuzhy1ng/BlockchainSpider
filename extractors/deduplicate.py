import argparse
import csv
import os
import shutil

from extractors._meta import BaseExtractor


class DeduplicateExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()

        parser = argparse.ArgumentParser()
        parser.description = 'Deduplication for transaction data'
        parser.add_argument('-i', '--input', help='input raw data folder', dest='in_dir', type=str, default=None)
        parser.add_argument('-o', '--output', help='output data folder', dest='out_dir', type=str, default=None)
        self.args = parser.parse_args()

        assert self.args.in_dir and self.args.out_dir, 'input and output folder needed!'

    def extract(self, *args, **kwargs):
        if not os.path.exists(self.args.out_dir):
            os.makedirs(self.args.out_dir)

        for fn in os.listdir(self.args.in_dir):
            in_fn = os.path.join(self.args.in_dir, fn)
            out_fn = os.path.join(self.args.out_dir, fn)
            print('processing %s >> %s' % (in_fn, out_fn))

            if os.path.isdir(in_fn):
                shutil.copytree(in_fn, out_fn)
                continue

            out_f = open(out_fn, 'w', newline='', encoding='utf-8')
            out_writer = csv.writer(out_f)
            with open(in_fn, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                fields = next(reader)
                out_writer.writerow(fields)

                key_idx = fields.index('id')
                keys = set()
                for row in reader:
                    key = row[key_idx]
                    if key in keys:
                        continue
                    keys.add(key)
                    out_writer.writerow(row)
            out_f.close()
