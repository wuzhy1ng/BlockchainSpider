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
        self.request_parent = dict()  # request -> request | semaphore (int)
        self.sync_keys = dict()  # request -> sync_key
        self.sync_sem = dict()  # sync_key -> semaphore (int)
        self.sync_items = dict()  # sync_key -> items
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
                if self.sync_items.get(key) is None:
                    yield item
                    continue
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
            # note that we use the locked semaphore as the sync signal
            # so the semaphore is released when creating new task
            if request.cb_kwargs.get(self.SYNC_KEYWORD) is not None:
                req_fingerprint = fingerprint(request)
                await self._lock.acquire()
                sem = self.sync_sem.get(sync_key)
                if sem is None:
                    self.sync_sem[sync_key] = asyncio.Semaphore(value=0)
                    self.sync_items[sync_key] = dict()
                self.sync_sem[sync_key].release()
                self.request_parent[req_fingerprint] = self.sync_sem[sync_key]
                self.sync_keys[req_fingerprint] = sync_key
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
                self.request_parent[grandpa_fingerprint].release()
            else:
                self.request_parent[req_fingerprint] = parent_fingerprint
                self.request_parent[parent_fingerprint].release()
            self._lock.release()

        # release!
        await self._lock.acquire()
        yield await self._release_sync_item(response.request)
        self._lock.release()

    def make_errback(self, old_errback) -> Callable:
        async def new_errback(failure):
            # reload context data and log out
            request = failure.request
            self.log(
                message='Get error when fetching {}'.format(request.body),
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
                parent_fingerprint = fingerprint(request)
                for item in old_results:
                    if not isinstance(item, scrapy.Request):
                        yield item
                        continue

                    # generate the wrapped request
                    sync_key = request.cb_kwargs[self.SYNC_KEYWORD]
                    yield request.replace(
                        errback=self.make_errback(request.errback),
                        cb_kwargs={
                            self.SYNC_KEYWORD: sync_key,
                            **item.cb_kwargs
                        },
                    )

                    # update the trace map
                    await self._lock.acquire()
                    grandpa_fingerprint = self.request_parent.get(parent_fingerprint)
                    if not grandpa_fingerprint:
                        self._lock.release()
                        continue
                    req_fingerprint = fingerprint(item)
                    if isinstance(grandpa_fingerprint, bytes):
                        self.request_parent[req_fingerprint] = grandpa_fingerprint
                        self.request_parent[grandpa_fingerprint].release()
                    else:
                        self.request_parent[req_fingerprint] = parent_fingerprint
                        self.request_parent[parent_fingerprint].release()
                    self._lock.release()

            # generate sync item (when the response fails)
            await self._lock.acquire()
            yield await self._release_sync_item(request)
            self._lock.release()

        return new_errback

    async def _release_sync_item(self, finished_request: scrapy.Request) -> Union[SyncItem, None]:
        # calc fingerprint
        parent_fingerprint = fingerprint(finished_request)
        grandpa_fingerprint = self.request_parent.get(parent_fingerprint)
        if grandpa_fingerprint is None:
            return

        # release sync data when response
        sync_key = None
        if not isinstance(grandpa_fingerprint, bytes):
            await self.request_parent[parent_fingerprint].acquire()
            if self.request_parent[parent_fingerprint].locked():
                del self.request_parent[parent_fingerprint]
                sync_key = self.sync_keys.pop(parent_fingerprint)
        else:
            await self.request_parent[grandpa_fingerprint].acquire()
            if self.request_parent[grandpa_fingerprint].locked():
                del self.request_parent[grandpa_fingerprint]
                sync_key = self.sync_keys.pop(grandpa_fingerprint)
            del self.request_parent[parent_fingerprint]

        if sync_key is None:
            return
        self.log(
            message="Synchronized: {}".format(sync_key),
            level=logging.INFO,
        )
        items = self.sync_items[sync_key]
        del self.sync_sem[sync_key]
        del self.sync_items[sync_key]
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
