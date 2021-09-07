from ._meta import Task


class SyncTask(Task):
    def __init__(self, strategy_cls, source, **kwargs):
        super().__init__(strategy_cls, source, **kwargs)
        self._cache = dict()

    def wait(self, key):
        self._cache[key] = None

    def push(self, node, edges: list, **kwargs):
        key = kwargs.get('wait_key', None)
        assert key is not None
        del kwargs['wait_key']

        self._cache[key] = edges
        if not self._is_locked():
            self._strategy.push(node, edges, **kwargs)
            self._cache = dict()

    def pop(self):
        if self._is_locked():
            return None
        item = self._strategy.pop()
        return item

    def _is_locked(self):
        for k in self._cache.keys():
            if self._cache[k] is None:
                return True
        return False
