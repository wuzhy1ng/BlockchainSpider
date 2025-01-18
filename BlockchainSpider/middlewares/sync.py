import asyncio
import logging
from typing import Callable, Generator, AsyncGenerator, Union

import scrapy
from scrapy.utils.request import fingerprint

from BlockchainSpider.items.sync import SyncItem
from BlockchainSpider.middlewares.defs import LogMiddleware


class SyncMiddleware(LogMiddleware):
    SYNC_KEYWORD = '$sync'

    def __init__(self):
        self.request_parent = dict()  # request -> request | int
        self.sync_keys = dict()  # request -> sync_key
        self.sync_items = dict()  # sync_key -> items
        self._lock = asyncio.Lock()

    async def process_spider_output(self, response: scrapy.http.Response, result, spider):
        # listen each request for tracing sync process
        key = response.cb_kwargs.get(self.SYNC_KEYWORD)
        parent_fingerprint = fingerprint(response.request)
        async for item in result:
            # add item to the sync cache
            if not isinstance(item, scrapy.Request) and key is not None:
                cls_name = item.__class__.__name__
                if not self.sync_items[key].get(cls_name):
                    self.sync_items[key][cls_name] = list()
                self.sync_items[key][cls_name].append(item)
                continue

            # handle error in the new request
            # and append sync_key to the cb_kwargs
            request = item
            sync_key = request.cb_kwargs.get(self.SYNC_KEYWORD)
            sync_key = sync_key if sync_key is not None else key
            yield request.replace(
                errback=self.make_errback(request.errback),
                cb_kwargs={self.SYNC_KEYWORD: sync_key, **request.cb_kwargs},
            )

            # trace requests with a new task
            if request.cb_kwargs.get(self.SYNC_KEYWORD) is not None:
                req_fingerprint = fingerprint(request)
                await self._lock.acquire()
                self.request_parent[req_fingerprint] = 1
                self.sync_keys[req_fingerprint] = sync_key
                self.sync_items[sync_key] = dict()
                self._lock.release()
                continue

            # trace extra generated requests
            await self._lock.acquire()
            grandpa_fingerprint = self.request_parent.get(parent_fingerprint)
            if not grandpa_fingerprint:
                self._lock.release()
                continue
            req_fingerprint = fingerprint(request)
            if isinstance(grandpa_fingerprint, bytes):
                self.request_parent[req_fingerprint] = grandpa_fingerprint
                self.request_parent[grandpa_fingerprint] += 1
            else:
                self.request_parent[req_fingerprint] = parent_fingerprint
                self.request_parent[parent_fingerprint] += 1
            self._lock.release()

        # release!
        await self._lock.acquire()
        yield self._release_sync_item(response.request)
        self._lock.release()

    def make_errback(self, old_errback) -> Callable:
        async def new_errback(failure):
            # wrap the old error callback
            old_results = old_errback(failure) if old_errback else None
            if isinstance(old_results, Generator):
                for rlt in old_results:
                    yield rlt
            if isinstance(old_results, AsyncGenerator):
                async for rlt in old_results:
                    yield rlt

            # reload context data and log out
            request = failure.request
            self.log(
                message='Get error when fetching {} with {}'.format(
                    request.url, request.body
                ),
                level=logging.WARNING
            )

            # generate sync item (when the response fails)
            yield self._release_sync_item(request)

        return new_errback

    def _release_sync_item(self, finished_request: scrapy.Request) -> Union[SyncItem, None]:
        # calc fingerprint
        parent_fingerprint = fingerprint(finished_request)
        grandpa_fingerprint = self.request_parent.get(parent_fingerprint)
        if grandpa_fingerprint is None:
            return

        # release sync data when response
        sync_key = None
        if not isinstance(grandpa_fingerprint, bytes):
            self.request_parent[parent_fingerprint] -= 1
            if self.request_parent[parent_fingerprint] == 0:
                del self.request_parent[parent_fingerprint]
                sync_key = self.sync_keys.pop(parent_fingerprint)
        else:
            self.request_parent[grandpa_fingerprint] -= 1
            if self.request_parent[grandpa_fingerprint] == 0:
                del self.request_parent[grandpa_fingerprint]
                sync_key = self.sync_keys.pop(grandpa_fingerprint)
            del self.request_parent[parent_fingerprint]

        if sync_key is None:
            return
        self.log(
            message="Synchronized: {}".format(sync_key),
            level=logging.INFO,
        )
        items = self.sync_items.pop(sync_key)
        return SyncItem(key=sync_key, data=items)


class SyncIgnoreMiddleware(LogMiddleware):
    async def process_spider_output(self, response: scrapy.http.Response, result, spider):
        sync_ignore = spider.__dict__.get('sync_ignore')
        async for item in result:
            if not isinstance(item, scrapy.Request) or not sync_ignore:
                yield item
                continue
            sync_key = item.cb_kwargs.get(SyncMiddleware.SYNC_KEYWORD)
            if sync_key is None:
                yield item
                continue
            ignore_exp = sync_ignore.replace(SyncMiddleware.SYNC_KEYWORD, str(sync_key))
            if eval(ignore_exp):
                yield item
