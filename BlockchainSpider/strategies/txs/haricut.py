from typing import Dict, Tuple, Any

from BlockchainSpider.strategies.txs import PushPopModel


class Haircut(PushPopModel):
    def __init__(self, source, min_weight=1e-3, **kwargs):
        super().__init__(source)
        self.min_weight = float(min_weight)
        assert 0 < self.min_weight < 1
        self.weight_map = {self.source: 1}
        self._vis = {self.source}

    def push(self, node, edges: list, **kwargs):
        out_sum = 0
        out_edges = list()
        for e in edges:
            if e.get('from') == node:
                out_sum += float(e.get('value', 0))
                out_edges.append(e)

        if out_sum == 0:
            return

        node_weight = self.weight_map.get(node, 0)
        self.weight_map[node] = 0
        for oe in out_edges:
            out_neibor = oe.get('to')
            edge_value = float(oe.get('value'))
            self.weight_map[out_neibor] = self.weight_map.get(out_neibor, 0) + \
                                          node_weight * (edge_value / out_sum)

    def pop(self) -> Tuple[Any, Dict]:
        node, weight = None, 0
        for _node, _weight in self.weight_map.items():
            if _weight < self.min_weight:
                continue
            if _node not in self._vis and _weight > weight:
                node, weight = _node, _weight
        self._vis.add(node)
        if node is None:
            return None, {}
        return node, {'weight': weight}

    def get_context_snapshot(self) -> Dict:
        return {
            'source': self.source,
            'min_weight': self.min_weight,
            'weight_map': self.weight_map,
            'vis': list(self._vis),
        }

    def get_node_rank(self) -> Dict:
        return self.weight_map
