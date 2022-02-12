from BlockchainSpider.strategies import PushPopModel


class APPR(PushPopModel):
    def __init__(self, source, alpha: float = 0.15, epsilon: float = 1e-5):
        super().__init__(source)

        assert 0 <= alpha <= 1
        self.alpha = alpha

        assert 0 < epsilon < 1
        self.epsilon = epsilon

        self.r = {self.source: 1}
        self.p = dict()

        self._vis = set()

    def push(self, node, edges: list, **kwargs):
        r_node = self.r.get(node, 0)
        if r_node == 0:
            return
        self.r[node] = 0

        self.p[node] = self.p.get(node, 0) + r_node * self.alpha
        # self.r[node] = (1 - self.alpha) * r_node / 2

        neighbours = set()
        for e in edges:
            neighbours.add(e.get('from'))
            neighbours.add(e.get('to'))
        if node in neighbours:
            neighbours.remove(node)

        neighbours_cnt = len(neighbours)
        inc = (1 - self.alpha) * r_node / neighbours_cnt if neighbours_cnt > 0 else 0
        for neighbour in neighbours:
            self.r[neighbour] = self.r.get(neighbour, 0) + inc

        # yield edges
        if node not in self._vis:
            self._vis.add(node)
            yield from edges

    def pop(self):
        node, r = None, self.epsilon
        for _node, _r in self.r.items():
            if _r > r:
                node, r = _node, _r

        return dict(node=node, residual=r) if node is not None else None
