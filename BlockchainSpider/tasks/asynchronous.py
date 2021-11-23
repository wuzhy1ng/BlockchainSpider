from ._meta import Task


class AsyncTask(Task):
    def push(self, node, edges: list, **kwargs):
        self._strategy.push(node, edges, **kwargs)

    def pop(self):
        while True:
            item = self._strategy.pop()
            if item is None:
                break
            yield item
