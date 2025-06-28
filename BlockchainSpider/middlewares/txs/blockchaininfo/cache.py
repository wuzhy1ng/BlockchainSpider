from typing import Union
from urllib.parse import urlparse

from BlockchainSpider.middlewares.txs.blockscan import APIMemoryCacheMiddleware as BlockscanAPIMemoryCacheMiddleware


class APIMemoryCacheMiddleware(BlockscanAPIMemoryCacheMiddleware):
    @staticmethod
    def get_cache_key(request) -> Union[str, None]:
        url = urlparse(request.url)
        cache_url = '%s://%s%s' % (url.scheme, url.netloc, url.path)
        return cache_url
