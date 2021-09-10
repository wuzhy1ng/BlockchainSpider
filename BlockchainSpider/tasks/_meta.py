class Task:
    def __init__(self, strategy, source, **kwargs):
        self._strategy = strategy
        self._source = source

    def push(self, node, edges: list, **kwargs):
        raise NotImplementedError()

    def pop(self):
        raise NotImplementedError()

    def get_strategy(self):
        return self._strategy

    def get_source(self):
        return self._source
