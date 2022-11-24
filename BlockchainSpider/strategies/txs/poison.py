from queue import Queue

from BlockchainSpider.strategies import PushPopModel


class Poison(PushPopModel):
    def __init__(self, source, depth: int = 2):
        super().__init__(source)
        self.depth = depth
        self._vis = {self.source}
        self._queue = Queue()

    def push(self, node, edges: list, cur_depth: int = -1):
        assert cur_depth >= 0

        if cur_depth + 1 > self.depth:
            return

        for e in edges:
            if e.get('from') == node:
                self._queue.put((e.get('to'), cur_depth + 1))

    def pop(self):
        while not self._queue.empty():
            node, depth = self._queue.get()
            if node not in self._vis:
                self._vis.add(node)
                return dict(node=node, depth=depth)
        return None
