from ._meta import Task


class AsyncTask(Task):
    def push(self, node, edges: list, **kwargs):
        self.strategy.push(node, edges, **kwargs)

    def pop(self):
        while True:
            item = self.strategy.pop()
            if item is None:
                break
            yield item
