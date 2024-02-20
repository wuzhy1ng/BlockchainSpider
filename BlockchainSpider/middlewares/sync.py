import asyncio
import logging
from typing import Callable, Generator, AsyncGenerator, Union

import scrapy
from scrapy.utils.request import fingerprint

from BlockchainSpider.items.sync import SyncDataItem
from BlockchainSpider.middlewares.defs import LogMiddleware


class SyncMiddleware(LogMiddleware):
    def __init__(self):
        self.request_parent = dict()
        self.sync_items = dict()
        self._lock = asyncio.Lock()

    async def process_spider_output(self, response, result, spider):
        key = getattr(spider, 'sync_item_key')
        if key is None:
            async for item in result:
                yield item
            return

        # listen each request for tracing sync process
        parent_fingerprint = fingerprint(response.request)
        async for item in result:
            if not isinstance(item, scrapy.Request):
                yield item
                continue

            # handle error
            yield item.replace(
                errback=self.make_errback(item.errback),
            )

            # start new task
            value = item.cb_kwargs.get(key)
            if value is not None:
                assert isinstance(value, dict)
                req_fingerprint = fingerprint(item)
                await self._lock.acquire()
                self.request_parent[req_fingerprint] = 1
                self.sync_items[req_fingerprint] = value
                self._lock.release()
                continue

            # trace extra generated requests
            await self._lock.acquire()
            if not self.request_parent.get(parent_fingerprint):
                self._lock.release()
                continue
            req_fingerprint = fingerprint(item)
            grandpa_fingerprint = self.request_parent[parent_fingerprint]
            if isinstance(grandpa_fingerprint, bytes):
                self.request_parent[req_fingerprint] = grandpa_fingerprint
                self.request_parent[grandpa_fingerprint] += 1
            else:
                self.request_parent[req_fingerprint] = parent_fingerprint
                self.request_parent[parent_fingerprint] += 1
            self._lock.release()

        # release!
        await self._lock.acquire()
        yield await self._release_sync_item(response.request)
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
                message='Get error when fetching {} with {}, callback args {}'.format(
                    request.url, request.body, str(request.cb_kwargs)
                ),
                level=logging.WARNING
            )

            # generate sync item (when the response fails)
            yield await self._release_sync_item(request)

        return new_errback

    async def _release_sync_item(self, finished_request: scrapy.Request) -> Union[SyncDataItem, None]:
        parent_fingerprint = fingerprint(finished_request)
        grandpa_fingerprint = self.request_parent.get(parent_fingerprint)
        if grandpa_fingerprint is None:
            return

        # release signal when response
        value = None
        if not isinstance(grandpa_fingerprint, bytes):
            self.request_parent[parent_fingerprint] -= 1
            if self.request_parent[parent_fingerprint] == 0:
                del self.request_parent[parent_fingerprint]
                value = self.sync_items.pop(parent_fingerprint)
        else:
            self.request_parent[grandpa_fingerprint] -= 1
            del self.request_parent[parent_fingerprint]
            if self.request_parent[grandpa_fingerprint] == 0:
                del self.request_parent[grandpa_fingerprint]
                value = self.sync_items.pop(grandpa_fingerprint)

        if value is None:
            return
        self.log(
            message="Synchronized: {}".format(value),
            level=logging.INFO,
        )
        return SyncDataItem(data=value)
