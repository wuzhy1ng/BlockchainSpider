import argparse
import csv
import os
import shutil

import networkx as nx

from extractors._meta import BaseExtractor


class LocalCommunityExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()

        parser = argparse.ArgumentParser()
        parser.description = 'Deduplication for transaction data'
        parser.add_argument('-i', '--input', help='input raw data folder', dest='in_dir', type=str, default=None)
        parser.add_argument('-o', '--output', help='output data folder', dest='out_dir', type=str, default=None)
        parser.add_argument('-p', '--phi', help='epsilon for local communication discovery', dest='phi',
                            type=float, default=1e-3)

        self.args = parser.parse_args()

        assert self.args.in_dir and self.args.out_dir, 'input and output folder needed!'
        assert 0 < self.args.phi < 1.0, 'phi must be less than 1.0 and greater then 0'

    def extract(self, *args, **kwargs):
        if not os.path.exists(self.args.out_dir):
            os.makedirs(self.args.out_dir)

        for fn in os.listdir(self.args.in_dir):
            in_txs_fn = os.path.join(self.args.in_dir, fn)
            out_txs_fn = os.path.join(self.args.out_dir, fn)
            print('processing %s >> %s' % (in_txs_fn, out_txs_fn))

            if os.path.isdir(in_txs_fn):
                shutil.copytree(in_txs_fn, out_txs_fn)
                continue

            # load graph
            g = nx.Graph()
            with open(in_txs_fn, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                for row in reader:
                    tx = {header[i]: row[i] for i in range(len(header))}
                    g.add_edge(tx.get('from'), tx.get('to'))

            # load importance
            p = dict()
            in_importance_fn = os.path.join(self.args.in_dir, 'importance', fn)
            with open(in_importance_fn, 'r') as f:
                reader = csv.reader(f)
                _ = next(reader)
                for row in reader:
                    p[row[0]] = float(row[1])

            # get local community nodes
            source = fn.split('.')[0]
            local_comm_nodes = self._local_comm(source, g, p)

            # write tx for output
            out_file = open(out_txs_fn, 'w', newline='', encoding='utf-8')
            out_writer = csv.writer(out_file)
            with open(in_txs_fn, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                out_writer.writerow(header)

                for row in reader:
                    tx = {header[i]: row[i] for i in range(len(header))}
                    if tx.get('from') in local_comm_nodes and tx.get('to') in local_comm_nodes:
                        out_writer.writerow(row)
            out_file.close()

    def _local_comm(self, source, g: nx.Graph, p: dict) -> set:
        inter_nodes = {source}
        outer_nodes = set()
        inter_sum, outer_sum = 0, 0

        p_items = list()
        p_sum = 0
        for k, v in p.items():
            p_sum += v
            if k != source:
                p_items.append((k, v))
        p_items = [(item[0], item[1] / p_sum) for item in p_items]
        p_items.sort(key=lambda x: x[1])

        def _calc_conductance_incr(inter_sum, outer_sum, new_node, g, inter_nodes, outer_nodes, p):
            inter_nodes.add(new_node)
            inter_sum += p[new_node]

            if new_node in outer_nodes:
                outer_sum -= p.get(new_node, 0)

            for neibor in g.neighbors(new_node):
                if neibor not in inter_nodes and neibor not in outer_nodes:
                    outer_nodes.add(neibor)
                    outer_sum += p.get(neibor, 0)

            return inter_sum, outer_sum, inter_nodes, outer_nodes

        inter_sum, outer_sum, inter_nodes, outer_nodes = _calc_conductance_incr(
            inter_sum, outer_sum, source, g, inter_nodes, outer_nodes, p
        )
        while outer_sum >= self.args.phi * inter_sum and len(p_items) > 0:
            new_node, weight = p_items.pop()
            if not g.has_node(new_node):
                continue
            inter_sum, outer_sum, inter_nodes, outer_nodes = _calc_conductance_incr(
                inter_sum, outer_sum, new_node, g, inter_nodes, outer_nodes, p
            )
        return inter_nodes
