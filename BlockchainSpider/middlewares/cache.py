# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import logging
from email.utils import formatdate
from functools import wraps
from urllib.parse import urlparse, parse_qs, urlencode

from scrapy.downloadermiddlewares.httpcache import HttpCacheMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.http import Request, Response
from scrapy.spiders import Spider


def _decorator_ignore_request_apikey(func):
    @wraps(func)
    def wrapper(self, request, spider):
        url = urlparse(request.url)
        query_args = parse_qs(url.query)
        apikey = query_args.get('apikey', list())
        if len(apikey) != 0:
            del query_args['apikey']
        token = query_args.get('token', list())
        if len(token) != 0:
            del query_args['token']

        _url = '?'.join([
            '%s://%s%s' % (url.scheme, url.netloc, url.path),
            urlencode({k: v[0] if len(v) > 0 else '' for k, v in query_args.items()}),
        ])
        _request = request.replace(url=_url)

        rlt = func(self, _request, spider)
        return rlt

    return wrapper


def _decorator_ignore_response_apikey(func):
    @wraps(func)
    def wrapper(self, request: Request, response: Response, spider: Spider):
        # process url of request
        url = urlparse(request.url)
        query_args = parse_qs(url.query)
        apikey = query_args.get('apikey', list())
        if len(apikey) != 0:
            del query_args['apikey']
        token = query_args.get('token', list())
        if len(token) != 0:
            del query_args['token']

        _url = '?'.join([
            '%s://%s%s' % (url.scheme, url.netloc, url.path),
            urlencode({k: v[0] if len(v) > 0 else '' for k, v in query_args.items()}),
        ])
        _request = request.replace(url=_url)

        # process url of response
        url = urlparse(response.url)
        query_args = parse_qs(url.query)
        apikey = query_args.get('apikey', list())
        if len(apikey) != 0:
            del query_args['apikey']
        token = query_args.get('token', list())
        if len(token) != 0:
            del query_args['token']

        _url = '?'.join([
            '%s://%s%s' % (url.scheme, url.netloc, url.path),
            urlencode({k: v[0] if len(v) > 0 else '' for k, v in query_args.items()}),
        ])
        _response = response.replace(url=_url)

        return func(self, _request, _response, spider)

    return wrapper


def _decorator_ignore_error_status_response(func):
    @wraps(func)
    def wrapper(self, request: Request, response: Response, spider: Spider):
        if response.status != 200:
            request.meta['dont_cache'] = True

        return func(self, request, response, spider)

    return wrapper


class RequestCacheMiddleware(HttpCacheMiddleware):
    @_decorator_ignore_request_apikey
    def process_request(self, request, spider):
        if request.meta.get('dont_cache', False):
            return None

        # Skip uncacheable requests
        if not self.policy.should_cache_request(request):
            request.meta['_dont_cache'] = True  # flag as uncacheable
            return None

        # Look for cached response and check if expired
        cachedresponse = self.storage.retrieve_response(spider, request)
        if cachedresponse is None:
            self.stats.inc_value('httpcache/miss', spider=spider)
            if self.ignore_missing:
                self.stats.inc_value('httpcache/ignore', spider=spider)
                raise IgnoreRequest("Ignored request not in cache: %s" % request)
            return None  # first time request

        # Return cached response only if not expired
        cachedresponse.flags.append('cached')
        if self.policy.is_cached_response_fresh(cachedresponse, request):
            self.stats.inc_value('httpcache/hit', spider=spider)
            logging.info('load cache of: %s' % request.url)
            return cachedresponse

        # Keep a reference to cached response to avoid a second cache lookup on
        # process_response hook
        request.meta['cached_response'] = cachedresponse

        return None

    @_decorator_ignore_response_apikey
    @_decorator_ignore_error_status_response
    def process_response(self, request: Request, response: Response, spider: Spider) -> Response:
        if request.meta.get('dont_cache', False):
            return response

        # Skip cached responses and uncacheable requests
        if 'cached' in response.flags or '_dont_cache' in request.meta:
            request.meta.pop('_dont_cache', None)
            return response

        # RFC2616 requires origin server to set Date header,
        # https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.18
        if 'Date' not in response.headers:
            response.headers['Date'] = formatdate(usegmt=True)

        # Do not validate first-hand responses
        cachedresponse = request.meta.pop('cached_response', None)
        if cachedresponse is None:
            self.stats.inc_value('httpcache/firsthand', spider=spider)
            self._cache_response(spider, response, request, cachedresponse)
            return response

        if self.policy.is_cached_response_valid(cachedresponse, response, request):
            self.stats.inc_value('httpcache/revalidate', spider=spider)
            return cachedresponse

        self.stats.inc_value('httpcache/invalidate', spider=spider)
        self._cache_response(spider, response, request, cachedresponse)
        return response
