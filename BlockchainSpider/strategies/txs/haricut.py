from BlockchainSpider.strategies import PushPopModel


class Haircut(PushPopModel):
    def __init__(self, source, min_weight: float = 1e-3):
        super().__init__(source)
        assert 0 < min_weight < 1
        self.min_weight = min_weight
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

    def pop(self):
        node, weight = None, 0
        for _node, _weight in self.weight_map.items():
            if _weight < self.min_weight:
                continue
            if _node not in self._vis and _weight > weight:
                node, weight = _node, _weight
        self._vis.add(node)
        return dict(node=node, weight=weight) if node else None


class OPICHaircut(Haircut):
    def __init__(self, source, min_weight: float = 1e-3, tendency: float = 0.7):
        super().__init__(source, min_weight)
        self.tendency = tendency

    def push(self, node, edges: list, **kwargs):
        in_sum, out_sum = 0, 0
        in_edges, out_edges = list(), list()
        for e in edges:
            if e.get('from') == node:
                out_sum += float(e.get('value', 0))
                out_edges.append(e)
            elif e.get('to') == node:
                in_sum += float(e.get('value', 0))
                in_edges.append(e)

        if out_sum == 0 or in_sum / out_sum <= 0:
            return

        R = in_sum / out_sum
        R = 1 if R > 1 else R
        node_weight = self.weight_map.get(node, 0)
        self.weight_map[node] = 0
        for oe in out_edges:
            out_neibor = oe.get('to')
            edge_value = float(oe.get('value'))
            self.weight_map[out_neibor] = self.weight_map.get(out_neibor, 0) + \
                                          node_weight * (edge_value / out_sum) * \
                                          self.tendency * R
        for ie in in_edges:
            in_neibor = ie.get('from')
            edge_value = float(ie.get('value'))
            self.weight_map[in_neibor] = self.weight_map.get(in_neibor, 0) + \
                                         node_weight * (edge_value / in_sum) * \
                                         (1 - self.tendency) * R
