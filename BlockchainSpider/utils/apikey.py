import json
import time

from twisted.internet.defer import DeferredLock

from BlockchainSpider import settings


class APIKeyBucket:
    def __init__(self, apikeys: list, kps: int):
        self.apikeys = apikeys
        self.kps = kps

        self._last_get_time = 0
        self._get_interval = 1 / (len(self.apikeys) * kps)
        self._lock = DeferredLock()

    def get(self) -> str:
        # get lock
        self._lock.acquire()

        # get apikey
        now = time.time()
        duration = now - self._last_get_time
        if duration < self._get_interval:
            time.sleep(self._get_interval - duration)
        self._last_get_time = time.time()
        key = self.get_apikey()

        # release lock and return key
        self._lock.release()
        return key

    def get_apikey(self) -> str:
        raise NotImplementedError()


class StaticAPIKeyBucket(APIKeyBucket):
    def __init__(self, net: str, kps: int = 5):
        apikeys = getattr(settings, 'APIKEYS', None)
        assert isinstance(apikeys, dict)

        apikeys = apikeys.get(net, list())
        assert len(apikeys) > 0
        super().__init__(apikeys, kps)

        self._index = 0

    def get_apikey(self) -> str:
        key = self.apikeys[self._index]
        self._index = (self._index + 1) % len(self.apikeys)
        return key


class JsonAPIKeyBucket(APIKeyBucket):
    def __init__(self, net: str, kps: int = 5):
        self.json_fn = getattr(settings, 'APIKEYS_JSON_FILENAME', None)
        self.net = net
        assert self.json_fn is not None and self.net is not None

        with open(self.json_fn, 'r') as f:
            data = json.load(f)
            assert isinstance(data, dict)
            apikeys = data.get(self.net)

        assert len(apikeys) > 0
        super().__init__(apikeys, kps)

        self._index = 0

    def get_apikey(self) -> str:
        key = self.apikeys[self._index]
        self._index = (self._index + 1) % len(self.apikeys)
        return key
