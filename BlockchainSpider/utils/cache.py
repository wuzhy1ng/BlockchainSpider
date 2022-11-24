class LRUCache:
    def __init__(self, max_size: int = 128):
        self.max_size = max_size
        self._cache = dict()
        self._key_list = list()

    def get(self, key):
        value = self._cache.get(key)
        if value is not None:
            self._key_list.remove(key)
            self._key_list.insert(0, key)
        return value

    def set(self, key, value):
        # replace cache item if full
        if len(self._cache) >= self.max_size:
            _key = self._key_list.pop()
            self._cache.pop(_key)

        # set cache
        self._cache[key] = value
        self._key_list.insert(0, key)
