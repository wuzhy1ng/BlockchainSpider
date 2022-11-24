from ._meta import SubgraphTask


class AsyncSubgraphTask(SubgraphTask):
    def push(self, node, edges: list, **kwargs):
        if self.is_closed:
            return

        self.strategy.push(node, edges, **kwargs)

    def pop(self):
        if self.is_closed:
            return

        while True:
            item = self.strategy.pop()
            if item is None:
                break
            yield item
