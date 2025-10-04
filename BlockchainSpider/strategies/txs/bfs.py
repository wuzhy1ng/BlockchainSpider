from queue import Queue
from typing import Dict, Tuple, Any

from BlockchainSpider.strategies.txs import PushPopModel


class BFS(PushPopModel):
    def __init__(self, source, depth=2, **kwargs):
        super().__init__(source)
        self.max_depth = int(depth)
        self._vis = {self.source}
        self._queue = Queue()

    def push(self, node, edges: list, **kwargs):
        """
        push a node with related edges, and the edges requires `from` and `to`
        :param node:
        :param edges:
        :return:
        """
        cur_depth = kwargs.get('depth', 0)
        assert cur_depth >= 0

        if cur_depth + 1 > self.max_depth:
            return

        for e in edges:
            self._queue.put((e.get('from'), cur_depth + 1))
            self._queue.put((e.get('to'), cur_depth + 1))

    def pop(self) -> Tuple[Any, Dict]:
        while not self._queue.empty():
            node, depth = self._queue.get()
            if node not in self._vis and depth <= self.max_depth:
                self._vis.add(node)
                return node, {'depth': depth}
        return None, {}

    def get_context_snapshot(self) -> Dict:
        return {
            'source': self.source,
            'max_depth': self.max_depth,
            'vis': list(self._vis),
        }

    def get_node_rank(self) -> Dict:
        return {}
