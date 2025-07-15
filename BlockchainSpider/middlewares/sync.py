import asyncio
import logging
from typing import Callable, Generator, AsyncGenerator, Union, List

import scrapy
from scrapy.utils.request import fingerprint

from BlockchainSpider.items.sync import SyncItem
from BlockchainSpider.middlewares.defs import LogMiddleware


class SyncMiddleware(LogMiddleware):
    SYNC_KEYWORD = '$sync'

    def __init__(self):
        self.request2key = dict()  # request -> sync_key
        self.key2sem = dict()  # sync_key -> semaphore (int)
        self.key2items = dict()  # sync_key -> items
        self._lock = asyncio.Lock()

    async def process_spider_output(self, response: scrapy.http.Response, result, spider):
        # listen each request for tracing sync process
        key = response.cb_kwargs.get(self.SYNC_KEYWORD)
        parent_fingerprint = fingerprint(response.request)

        # access all items in blocking mode
        # It ensures that there will be no premature unlocking cache
        results = list()
        async for item in result:
            results.append(item)

        # process all items
        for item in results:
            # add item to the sync cache
            if not isinstance(item, scrapy.Request):
                if self.key2items.get(key) is None:
                    yield item
                    continue
                cls_name = item.__class__.__name__
                if not self.key2items[key].get(cls_name):
                    self.key2items[key][cls_name] = list()
                self.key2items[key][cls_name].append(item)
                continue

            # handle new request
            request = await self._handle_new_request(
                request=item,
                parent_key=key,
                parent_fingerprint=parent_fingerprint,
            )
            yield request

        # release!
        await self._lock.acquire()
        yield await self._release_sync_item(parent_fingerprint)
        self._lock.release()

    def make_errback(self, old_errback) -> Callable:
        async def new_errback(failure):
            # reload context data and log out
            parent_request = failure.request
            parent_fingerprint = fingerprint(parent_request)
            self.log(
                message='Get error when fetching {}'.format(parent_request.url),
                level=logging.WARNING,
            )

            # wrap the old error callback
            old_results = old_errback(failure) if old_errback else None
            if isinstance(old_results, Generator):
                old_results = [rlt for rlt in old_results]
            if isinstance(old_results, AsyncGenerator):
                _old_results = list()
                async for rlt in old_results:
                    _old_results.append(rlt)
                old_results = _old_results

            # trace requests in the error callback
            # note that the item in the error callback will be skipped
            if isinstance(old_results, List):
                parent_key = self.request2key.get(parent_fingerprint)
                for item in old_results:
                    if not isinstance(item, scrapy.Request):
                        yield item
                        continue
                    request = await self._handle_new_request(
                        request=item,
                        parent_key=parent_key,
                        parent_fingerprint=parent_fingerprint,
                    )
                    yield request

            # generate sync item (when the response fails)
            await self._lock.acquire()
            yield await self._release_sync_item(parent_fingerprint)
            self._lock.release()

        return new_errback

    async def _handle_new_request(
            self, request: scrapy.Request,
            parent_key, parent_fingerprint,
    ) -> scrapy.Request:
        # handle error in the new request
        # and append sync_key to the cb_kwargs
        sync_key = request.cb_kwargs.get(self.SYNC_KEYWORD)
        if sync_key is None:
            sync_key = parent_key
        cb_kwargs = request.cb_kwargs.copy()
        if sync_key is not None:
            cb_kwargs[self.SYNC_KEYWORD] = sync_key
        errback_request = request.replace(
            errback=self.make_errback(request.errback),
            cb_kwargs=cb_kwargs,
        )

        # trace requests with a new task
        # note that we use the locked semaphore as the sync signal
        # so the semaphore is released when creating new task
        if request.cb_kwargs.get(self.SYNC_KEYWORD) is not None:
            req_fingerprint = fingerprint(request)
            await self._lock.acquire()
            sem = self.key2sem.get(sync_key)
            if sem is None:
                self.key2sem[sync_key] = asyncio.Semaphore(value=0)
                self.key2items[sync_key] = dict()
            self.key2sem[sync_key].release()
            self.request2key[req_fingerprint] = sync_key
            self._lock.release()
            return errback_request

        # trace extra generated requests
        await self._lock.acquire()
        parent_key = self.request2key.get(parent_fingerprint)
        if parent_key is None:
            self._lock.release()
            return errback_request
        req_fingerprint = fingerprint(request)
        self.request2key[req_fingerprint] = parent_key
        self.key2sem[parent_key].release()
        self._lock.release()
        return errback_request

    async def _release_sync_item(self, parent_fingerprint) -> Union[SyncItem, None]:
        sync_key = self.request2key.get(parent_fingerprint)
        if sync_key is None:
            return

        # update the semaphore
        await self.key2sem[sync_key].acquire()
        del self.request2key[parent_fingerprint]
        if not self.key2sem[sync_key].locked():
            return

        # clean up the cache if synced
        self.log(
            message="Synchronized: {}".format(sync_key),
            level=logging.INFO,
        )
        del self.key2sem[sync_key]
        items = self.key2items.pop(sync_key)
        return SyncItem(key=sync_key, data=items)
