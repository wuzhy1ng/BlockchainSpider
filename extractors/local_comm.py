import csv
import os

import networkx as nx

from extractors._meta import Extractor


class LocalCommunityExtractor(Extractor):
    def __init__(self, phi: float = 1e-4):
        super().__init__()
        self.phi = phi

    def extract(self, txs: list, source, p, **kwargs) -> list:
        g = nx.MultiDiGraph()
        for tx in txs:
            g.add_edge(tx['from'], tx['to'], hash=tx['hash'])

        def _calc_conductance_incr(inter_sum, outer_sum, new_node, g, inter_nodes, outer_nodes, p):
            inter_nodes.add(new_node)
            inter_sum += p[new_node]

            if new_node in outer_nodes:
                outer_sum -= p.get(new_node, 0)

            for e in g.in_edges(new_node):
                if e[0] not in inter_nodes and e[0] not in outer_nodes:
                    outer_nodes.add(e[0])
                    outer_sum += p.get(e[0], 0)
            for e in g.out_edges(new_node):
                if e[1] not in inter_nodes and e[1] not in outer_nodes:
                    outer_nodes.add(e[1])
                    outer_sum += p.get(e[1], 0)
            return inter_sum, outer_sum, inter_nodes, outer_nodes

        inter_nodes = {source}
        outer_nodes = set()
        inter_sum, outer_sum = 0, 0

        p_items = list()
        for k, v in p.items():
            if k != source:
                p_items.append((k, v))
        p_items.sort(key=lambda x: x[1])

        inter_sum, outer_sum, inter_nodes, outer_nodes = _calc_conductance_incr(
            inter_sum, outer_sum, source, g, inter_nodes, outer_nodes, p
        )
        while outer_sum >= self.phi * (inter_sum + outer_sum) and len(p_items) > 0:
            new_node, weight = p_items.pop()
            inter_sum, outer_sum, inter_nodes, outer_nodes = _calc_conductance_incr(
                inter_sum, outer_sum, new_node, g, inter_nodes, outer_nodes, p
            )

        _txs = list()
        _txs_hash = set([attr['hash'] for _, _, attr in g.subgraph(inter_nodes).edges(data=True)])
        for tx in txs:
            if tx['hash'] in _txs_hash:
                _txs.append(tx)
        return _txs

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        assert self._args.get('source') is not None
        assert self._args.get('in_dir') is not None
        assert self._args.get('out_dir') is not None

        out_file = open(os.path.join(self._args['out_dir'], self._args['fn']), 'w', newline='')
        out_writer = csv.writer(out_file)

        # load txs
        txs = list()
        with open(os.path.join(self._args['in_dir'], '%s.csv' % self._args['source']), 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            out_writer.writerow(header)

            for row in reader:
                tx = {header[i]: row[i] for i in range(len(header))}
                txs.append(tx)

        # load ppr
        p = dict()
        with open(os.path.join(self._args['in_dir'], 'ppr', '%s.csv' % self._args['source']), 'r') as f:
            reader = csv.reader(f)
            _ = next(reader)
            for row in reader:
                p[row[0]] = float(row[1])

        # write tx for output
        for tx in self.extract(txs, self._args['source'], p):
            out_writer.writerow([tx[h] for h in header])
        out_file.close()
