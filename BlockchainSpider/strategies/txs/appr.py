from typing import Dict, Tuple, Any

from BlockchainSpider.strategies.txs import PushPopModel
from BlockchainSpider.utils.cache import LRUCache


class APPR(PushPopModel):
    def __init__(
            self, source,
            alpha=0.15,
            epsilon=1e-5,
            **kwargs,
    ):
        super().__init__(source)

        self.alpha = float(alpha)
        assert 0 <= self.alpha <= 1

        self.epsilon = float(epsilon)
        assert 0 < self.epsilon < 1

        self.r = {self.source: 1}
        self.p = dict()

        self.cache = LRUCache()

    def push(self, node, edges: list, **kwargs):
        r_node = self.r.get(node, 0)
        if r_node == 0:
            return
        self.r[node] = 0
        # self.r[node] = (1 - self.alpha) * r_node / 2
        self.p[node] = self.p.get(node, 0) + r_node * self.alpha

        cache_dist = self.cache.get(node)
        if cache_dist is not None:
            for v, d in cache_dist.items():
                self.r[v] = self.r.get(v, 0) + d * r_node
            return

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
        self.cache.set(node, {neighbour: (1 - self.alpha) / neighbours_cnt for neighbour in neighbours})

    def pop(self) -> Tuple[Any, Dict]:
        while True:
            node, r_node = None, None
            for _node, _r_node in self.r.items():
                if _r_node <= self.epsilon or not self.cache.get(_node):
                    continue
                node, r_node = _node, _r_node
                break

            if not node:
                break
            self.r[node] = 0
            self.p[node] = self.p.get(node, 0) + r_node * self.alpha
            for v, d in self.cache.get(node).items():
                self.r[v] = self.r.get(v, 0) + d * r_node

        node, r = None, self.epsilon
        for _node, _r in self.r.items():
            if _r > r:
                node, r = _node, _r

        if node is None:
            return None, {}
        return node, {'residual': r}

    def get_context_snapshot(self) -> Dict:
        return {
            'source': self.source,
            'alpha': self.alpha,
            'epsilon': self.epsilon,
            'r': self.r,
            'p': self.p,
        }

    def get_node_rank(self) -> Dict:
        return self.p
