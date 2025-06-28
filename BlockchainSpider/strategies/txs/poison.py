from queue import Queue
from typing import Dict, Tuple, Any

from BlockchainSpider.strategies.txs import PushPopModel


class Poison(PushPopModel):
    def __init__(self, source, depth=2, **kwargs):
        super().__init__(source)
        self.depth = int(depth)
        self._vis = {self.source}
        self._queue = Queue()

    def push(self, node, edges: list, **kwargs):
        cur_depth = kwargs.get('depth', 0)
        assert cur_depth >= 0

        if cur_depth + 1 > self.depth:
            return

        for e in edges:
            if e.get('from') == node:
                self._queue.put((e.get('to'), cur_depth + 1))

    def pop(self) -> Tuple[Any, Dict]:
        while not self._queue.empty():
            node, depth = self._queue.get()
            if node not in self._vis:
                self._vis.add(node)
                return node, {'depth': depth}
        return None, {}

    def get_context_snapshot(self) -> Dict:
        return {
            'source': self.source,
            'depth': self.depth,
            'vis': list(self._vis),
        }

    def get_node_rank(self) -> Dict:
        return {}
