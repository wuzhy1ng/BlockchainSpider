class Task:
    def __init__(self, strategy, **kwargs):
        self.strategy = strategy
        self.info = kwargs

    def push(self, node, edges: list, **kwargs):
        raise NotImplementedError()

    def pop(self):
        raise NotImplementedError()
