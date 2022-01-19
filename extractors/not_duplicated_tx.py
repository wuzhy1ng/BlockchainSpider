import csv
import os

from extractors._meta import Extractor


class NotDuplicatedTxExtractor(Extractor):
    def __init__(self):
        super().__init__()
        self._vis = set()

    def extract(self, tx, **kwargs):
        if tx.get('hash') in self._vis:
            return

        self._vis.add(tx.get('hash'))
        return tx

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        assert self._args.get('fn') is not None
        assert self._args.get('in_dir') is not None
        assert self._args.get('out_dir') is not None

        out_file = open(os.path.join(self._args['out_dir'], self._args['fn']), 'w', newline='')
        out_writer = csv.writer(out_file)
        with open(os.path.join(self._args['in_dir'], self._args['fn']), 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            out_writer.writerow(header)
            for row in reader:
                tx = {header[i]: row[i] for i in range(len(header))}
                if self.extract(tx) is not None:
                    out_writer.writerow(row)
        out_file.close()


class NotDuplicatedBTCTxExtractor(Extractor):
    def __init__(self):
        super().__init__()
        self._vis = set()

    def extract(self, tx, **kwargs):
        if tx.get('hash') in self._vis:
            return

        self._vis.add(tx.get('hash'))
        return tx

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        assert self._args.get('fn') is not None
        assert self._args.get('in_dir') is not None
        assert self._args.get('out_dir') is not None

        out_file = open(os.path.join(self._args['out_dir'], self._args['fn']), 'w', newline='')
        out_writer = csv.writer(out_file)
        with open(os.path.join(self._args['in_dir'], self._args['fn']), 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            out_writer.writerow(header)
            for row in reader:
                tx = {header[i]: row[i] for i in range(len(header))}
                row[0] = tx['hash'] = '{}_{}'.format(
                    tx['hash'],
                    tx['age'],
                )
                if self.extract(tx) is not None:
                    out_writer.writerow(row)
        out_file.close()
