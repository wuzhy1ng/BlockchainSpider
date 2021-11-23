from ._meta import Task


class SyncTask(Task):
    def __init__(self, strategy, source, **kwargs):
        super().__init__(strategy, source, **kwargs)
        self._cache = dict()

    def wait(self, key):
        self._cache[key] = None

    def push(self, node, edges: list, **kwargs):
        key = kwargs.get('wait_key', None)
        assert key is not None
        del kwargs['wait_key']

        self._cache[key] = edges
        if not self.is_locked():
            edges = list()
            for cache in self._cache.values():
                edges.extend(cache)
            self._cache = dict()
            return self._strategy.push(node, edges, **kwargs)

    def pop(self):
        if self.is_locked():
            return None
        item = self._strategy.pop()
        return item

    def is_locked(self):
        for k in self._cache.keys():
            if self._cache[k] is None:
                return True
        return False
