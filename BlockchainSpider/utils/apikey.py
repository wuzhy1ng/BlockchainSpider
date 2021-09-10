import random


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
