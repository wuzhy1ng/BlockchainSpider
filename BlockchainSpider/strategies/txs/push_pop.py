from BlockchainSpider.utils.cache import LRUCache


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


class CachedPushPopModel:
    def __init__(self, instance: PushPopModel, max_cache_size: int = 1024):
        self.instance = instance
        self._cache = LRUCache(max_size=max_cache_size)

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
