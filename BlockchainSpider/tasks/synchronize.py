from collections import Iterator

from ._meta import Task


class SyncTask(Task):
    def __init__(self, strategy, **kwargs):
        super().__init__(strategy, **kwargs)
        self._cache = list()
        self._mux = 0

    def wait(self):
        self._mux -= 1

    def push(self, node, edges: list, **kwargs):
        self._mux += 1
        self._cache.extend(edges)

        if not self.is_locked():
            self._cache = list()

            rlt = self.strategy.push(node, edges, **kwargs)
            if isinstance(rlt, Iterator):
                yield from rlt

    def pop(self):
        if self.is_locked():
            return None
        item = self.strategy.pop()
        return item

    def is_locked(self):
        if self._mux < 0:
            return True
