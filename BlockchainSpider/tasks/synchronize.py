from collections import Iterator

from ._meta import Task


class SyncTask(Task):
    def __init__(self, strategy, **kwargs):
        super().__init__(strategy, **kwargs)
        self._cache = list()
        self._mux = 0

    def wait(self):
        if self.is_closed:
            return

        self._mux -= 1

    def push(self, node, edges: list, **kwargs):
        if self.is_closed:
            return

        self._mux += 1
        self._cache.extend(edges)

        if not self.is_locked():
            rlt = self.strategy.push(node, self._cache, **kwargs)
            if isinstance(rlt, Iterator):
                yield from rlt
            self._cache = list()

    def pop(self):
        if self.is_closed:
            return

        if self.is_locked():
            return None
        item = self.strategy.pop()
        return item

    def is_locked(self):
        if self.is_closed:
            return

        if self._mux < 0:
            return True

    def fuse(self, node, **kwargs):
        if self.is_closed:
            return

        self._mux = 0
        self._cache = list()

        rlt = self.strategy.push(node, list(), **kwargs)
        if isinstance(rlt, Iterator):
            for _ in rlt:
                pass

        item = self.strategy.pop()
        return item
