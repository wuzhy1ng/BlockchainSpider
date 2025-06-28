import logging
import time
from typing import Union
from urllib.parse import urlparse, parse_qs, urlencode

from BlockchainSpider.middlewares.defs import LogMiddleware
from BlockchainSpider.utils.cache import LRUCache


class APIMemoryCacheMiddleware(LogMiddleware):
    def __init__(self):
        super().__init__()
        self.max_cache_size = 2 ** 10
        self.cache = None
        self._last_report_time = time.time()
        self._hit_count = 0
        self._no_hit_count = 0

    def _init_by_spider(self, spider):
        if self.cache is not None:
            return
        self.max_cache_size = spider.__dict__.get('max_cache_size', self.max_cache_size)
        self.max_cache_size = int(self.max_cache_size)
        self.cache = LRUCache(self.max_cache_size)

    def process_request(self, request, spider):
        self._init_by_spider(spider)
        cache_key = self.get_cache_key(request)
        cached_response = self.cache.get(cache_key)

        # report the cache hit info
        self._hit_count = self._hit_count + int(cached_response is not None)
        self._no_hit_count = self._no_hit_count + int(cached_response is None)
        timestamp = time.time()
        if timestamp - self._last_report_time > 30:
            self._last_report_time = timestamp
            hit_rate = self._hit_count + self._no_hit_count
            hit_rate = (self._hit_count / hit_rate) if hit_rate > 0 else 0
            hit_rate = round(hit_rate, 3) * 100
            usage_rate = len(self.cache) / self.max_cache_size
            usage_rate = round(usage_rate, 3) * 100
            self.log(
                message='Hit cache {}/{} ({}%), '
                        'cache usage {}/{} ({}%)'.format(
                    self._hit_count,
                    self._hit_count + self._no_hit_count,
                    hit_rate, len(self.cache),
                    self.max_cache_size,
                    usage_rate,
                ),
                level=logging.INFO,
            )

        # return the cache data
        if cached_response is not None:
            return cached_response.replace(
                url=request.url,
                request=request,
            )

    def process_response(self, request, response, spider):
        cache_key = self.get_cache_key(request)
        if cache_key is None:
            return response
        self.cache.set(cache_key, response.copy())
        return response

    @staticmethod
    def get_cache_key(request) -> Union[str, None]:
        url = urlparse(request.url)
        query_args = parse_qs(url.query)
        apikey = query_args.get('apikey', list())
        if len(apikey) == 0:
            return None
        del query_args['apikey']
        cache_url = '?'.join([
            '%s://%s%s' % (url.scheme, url.netloc, url.path),
            urlencode({
                k: v[0] if len(v) > 0 else ''
                for k, v in query_args.items()
            }),
        ])
        return cache_url
