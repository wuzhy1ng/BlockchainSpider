class Extractor:
    def __init__(self):
        self._args = None

    def extract(self, *args, **kwargs):
        raise NotImplementedError()

    def __call__(self, *args, **kwargs):
        self._args = kwargs


class BaseExtractor:
    def __init__(self):
        self.args = None

    def extract(self, *args, **kwargs):
        raise NotImplementedError()
