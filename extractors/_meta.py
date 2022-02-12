class BaseExtractor:
    def __init__(self):
        self.args = None

    def extract(self, *args, **kwargs):
        raise NotImplementedError()
