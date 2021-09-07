class Task:
    def __init__(self, strategy_cls, source, **kwargs):
        self._strategy = strategy_cls(source, **kwargs)
        self.source = source

    def push(self, node, edges: list, **kwargs):
        raise NotImplementedError()

    def pop(self):
        raise NotImplementedError()
