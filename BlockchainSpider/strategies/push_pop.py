class PushPopModel:
    def __init__(self, source):
        self.source = source

    def push(self, node, edges: list, **kwargs):
        """
        push a node with related edges
        :param node:
        :param edges:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def pop(self):
        """
        pop a series of nodes
        :return:
        """
        raise NotImplementedError()
