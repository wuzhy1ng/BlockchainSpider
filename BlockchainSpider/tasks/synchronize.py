from collections.abc import Iterator

from ._meta import SubgraphTask, MotifCounterTask


class SyncSubgraphTask(SubgraphTask):
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
        return self._mux < 0

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


class SyncMotifCounterTask(MotifCounterTask):
    def __init__(self, strategy):
        super().__init__(strategy)
        self._cache = list()
        self._mux = 0

    def count(self, edges: list, **kwargs):
        self._mux += 1
        self._cache.extend(edges)

        if self.is_locked():
            return
        rlt = self.strategy.count(self._cache)
        self._cache = list()
        return rlt

    def wait(self):
        self._mux -= 1

    def is_locked(self):
        return self._mux < 0
