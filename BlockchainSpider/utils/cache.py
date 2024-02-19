import asyncio
from collections import OrderedDict


class LRUCache:
    def __init__(self, max_size: int = 128):
        self.max_size = max_size
        self._cache = OrderedDict()

    def get(self, key):
        value = self._cache.pop(key, None)
        if value is not None:
            self._cache[key] = value
        return value

    def set(self, key, value):
        ret = self._cache.pop(key, None)
        if ret is not None and len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        self._cache[key] = value
