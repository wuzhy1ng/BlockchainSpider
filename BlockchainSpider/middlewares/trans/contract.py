import json
import traceback
from typing import Union

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import TransactionReceiptItem
from BlockchainSpider.items.trans import ContractItem
from BlockchainSpider.middlewares.defs import LogMiddleware
from BlockchainSpider.utils.cache import LRUCache
from BlockchainSpider.utils.decorator import log_debug_tracing


class ContractMiddleware(LogMiddleware):
    def __init__(self):
        self.provider_bucket = None
        self.timeout = getattr(settings, 'DOWNLOAD_TIMEOUT', 120)
        self._cache = LRUCache(getattr(settings, 'MIDDLE_CACHE_SIZE', 2 ** 16))
        self._waiting_ctx = dict()  # addr -> str

    def _init_by_spider(self, spider):
        if self.provider_bucket is not None:
            return
        if getattr(spider, 'middleware_providers') and \
                spider.middleware_providers.get(self.__class__.__name__):
            self.provider_bucket = spider.middleware_providers[self.__class__.__name__]
        else:
            self.provider_bucket = spider.provider_bucket

    async def process_spider_output(self, response, result, spider):
        self._init_by_spider(spider)

        # filter and process the result flow
        async for item in result:
            yield item
            if isinstance(item, TransactionReceiptItem) and item['created_contract'] != '':
                yield await self.get_contract_item(
                    contract_address=item['created_contract'],
                    transaction_hash=item['transaction_hash'],
                    block_number=item['block_number'],
                    priority=response.request.priority,
                )

    async def get_contract_item(
            self, contract_address: str,
            transaction_hash: str,
            block_number: int,
            **kwargs,
    ) -> Union[scrapy.Request, ContractItem, None]:
        cached_item = self._cache.get(contract_address)
        if cached_item is not None:
            return ContractItem(
                address=contract_address,
                code=cached_item,
                cb_kwargs={
                    'transaction_hash': transaction_hash,
                    'block_number': block_number,
                }
            )

        # add waiting list
        if isinstance(self._waiting_ctx.get(contract_address), list):
            self._waiting_ctx[contract_address].append({
                'transaction_hash': transaction_hash,
                'block_number': block_number,
            })
            return
        self._waiting_ctx[contract_address] = [{
            'transaction_hash': transaction_hash,
            'block_number': block_number,
        }]

        # generate a new request for the contract item
        return await self.get_request_contract(
            address=contract_address,
            block_tag=hex(block_number),
            priority=kwargs['priority'],
            cb_kwargs={
                'address': contract_address,
                'block_number': block_number,
            },
        )

    @log_debug_tracing
    async def parse_contract_item(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')
        if result is None or result == '0x':
            return

        # add cache and generate result
        self._cache.set(kwargs['address'], result)
        try:
            ctx_list = self._waiting_ctx.pop(kwargs['address'])
            for ctx in ctx_list:
                yield ContractItem(
                    address=kwargs['address'],
                    code=result,
                    cb_kwargs={
                        'transaction_hash': ctx['transaction_hash'],
                        'block_number': ctx['block_number'],
                    }
                )
        except:
            traceback.print_exc()

    async def get_request_contract(
            self, address: str, block_tag: str,
            priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "eth_getCode",
                "params": [address, block_tag],
                "id": 1
            }),
            priority=priority,
            callback=self.parse_contract_item,
            cb_kwargs=cb_kwargs if cb_kwargs else dict(),
        )
