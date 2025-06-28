from typing import Union
from urllib.parse import urlparse, parse_qs, urlencode

from BlockchainSpider.middlewares.txs.blockscan import APIMemoryCacheMiddleware as BlockscanAPIMemoryCacheMiddleware


class APIMemoryCacheMiddleware(BlockscanAPIMemoryCacheMiddleware):
    @staticmethod
    def get_cache_key(request) -> Union[str, None]:
        url = urlparse(request.url)
        query_args = parse_qs(url.query)
        cache_url = '?'.join([
            '%s://%s%s' % (url.scheme, url.netloc, url.path),
            urlencode({
                k: v[0] if len(v) > 0 else ''
                for k, v in query_args.items()
            }),
        ])
        return cache_url
