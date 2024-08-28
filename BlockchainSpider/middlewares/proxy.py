import logging

from BlockchainSpider.middlewares.defs import LogMiddleware


class HTTPProxyMiddleware(LogMiddleware):
    def process_request(self, request, spider):
        proxy = spider.__dict__.get('http_proxy')
        if proxy is not None:
            request.meta['proxy'] = proxy
            self.log(
                message='proxy request from %s to %s' % (proxy, request.url),
                level=logging.INFO,
            )
