from typing import Iterator

from BlockchainSpider.middlewares._meta import LogMiddleware


class InterceptMiddleware(LogMiddleware):
    async def process_spider_output(self, response, result, spider):
        if isinstance(result, Iterator):
            for item in result:
                yield item
        else:
            async for item in result:
                yield item
