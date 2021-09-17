import json
import random
from BlockchainSpider import settings


class APIKeyBucket:
    def get(self) -> str:
        raise NotImplementedError()


class StaticAPIKeyBucket(APIKeyBucket):
    def __init__(self, apikeys: list):
        self.apikeys = apikeys
        self._idx = 0
        self._cnt = len(self.apikeys)

    def get(self) -> str:
        return random.choice(self.apikeys)


class JsonAPIKeyBucket(APIKeyBucket):
    def __init__(self, chain: str):
        self.json_fn = getattr(settings, 'APIKEYS_JSON_FILENAME', None)
        self.chain = chain
        assert self.json_fn is not None and self.chain is not None

        self.apikeys = list()
        with open(self.json_fn, 'r') as f:
            data = json.load(f)
            assert isinstance(data, dict)
            self.apikeys = data.get(self.chain)

    def get(self) -> str:
        assert len(self.apikeys) > 0
        return random.choice(self.apikeys)
