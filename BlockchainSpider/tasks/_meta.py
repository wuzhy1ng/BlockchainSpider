class Task:
    def __init__(self, strategy, source, **kwargs):
        self._strategy = strategy
        self.source = source

    def push(self, node, edges: list, **kwargs):
        raise NotImplementedError()

    def pop(self):
        raise NotImplementedError()
