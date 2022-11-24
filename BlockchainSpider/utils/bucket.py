import json
import sys
import time

from twisted.internet.defer import DeferredLock

from BlockchainSpider import settings


class APIKeyBucket:
    def __init__(self, apikeys: [str], kps: int):
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


class ProvidersBucket:
    def __init__(self, providers: [str], qps: int):
        self.providers = providers
        self.qps = qps

        self._last_get_time = [0 for _ in range(len(self.providers))]
        self._get_interval = 1 / (len(self.providers) * qps)
        self._lock = DeferredLock()

    def get(self) -> str:
        # get lock
        self._lock.acquire()

        # choose a provider
        idx, last_get_time = 0, sys.maxsize
        for _idx, _last_get_time in enumerate(self._last_get_time):
            if _last_get_time < last_get_time:
                last_get_time = _last_get_time
                idx = _idx

        # get provider
        now = time.time()
        duration = now - last_get_time
        if duration < self._get_interval:
            time.sleep(self._get_interval - duration)
        self._last_get_time[idx] = time.time()
        provider = self.providers[idx]

        # release lock and return provider
        self._lock.release()
        return provider


class StaticProvidersBucket(ProvidersBucket):
    def __init__(self, net: str, kps: int = 5):
        providers = getattr(settings, 'PROVIDERS', None)
        assert isinstance(providers, dict)

        providers = providers.get(net, list())
        assert len(providers) > 0
        super().__init__(providers, kps)
