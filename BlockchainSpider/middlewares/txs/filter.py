from BlockchainSpider.items import AccountTransferItem
from BlockchainSpider.items.subgraph import PopItem, UTXOTransferItem
from BlockchainSpider.middlewares.defs import LogMiddleware


class TokenFilterMiddleware(LogMiddleware):
    def __init__(self):
        self.allow_all_tokens = True
        self.allowed_tokens = dict()  # str -> True

    async def process_spider_output(self, response, result, spider):
        async for item in result:
            if isinstance(item, PopItem):
                kwargs = item.get_context_kwargs()
                self.allow_all_tokens = kwargs.get('allow_all_tokens', self.allow_all_tokens)
                allowed_tokens = kwargs.get('allowed_tokens')
                if allowed_tokens is not None:
                    self.allowed_tokens = {token: True for token in allowed_tokens}
                    self.allow_all_tokens = False
            if isinstance(item, AccountTransferItem) and not self.allow_all_tokens:
                token_identity = item['contract_address']
                if item['token_id'] != '':
                    token_identity = '{}_{}'.format(
                        token_identity,
                        item['token_id'],
                    )
                if token_identity in self.allowed_tokens:
                    yield item
                continue
            yield item


class DeduplicateFilterMiddleware(LogMiddleware):
    def __init__(self):
        self.vis = set()

    async def process_spider_output(self, response, result, spider):
        async for item in result:
            if any([
                isinstance(item, AccountTransferItem),
                isinstance(item, UTXOTransferItem),
            ]):
                if item['id'] in self.vis:
                    continue
                self.vis.add(item['id'])
            yield item
