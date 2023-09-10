import json

import scrapy
from pybloom import ScalableBloomFilter

from BlockchainSpider import settings
from BlockchainSpider.items import TransactionItem, TraceItem
from BlockchainSpider.items.trans import ContractItem
from BlockchainSpider.middlewares._meta import LogMiddleware
from BlockchainSpider.utils.decorator import log_debug_tracing


class ContractMiddleware(LogMiddleware):
    def __init__(self):
        self.provider_bucket = None
        self.timeout = getattr(settings, 'DOWNLOAD_TIMEOUT', 120)
        self.bloom4contract = ScalableBloomFilter(
            initial_capacity=1024,
            error_rate=1e-4,
            mode=ScalableBloomFilter.SMALL_SET_GROWTH,
        )

    async def process_spider_output(self, response, result, spider):
        if self.provider_bucket is None:
            self.provider_bucket = spider.provider_bucket

        # filter and process the result flow
        async for item in result:
            yield item

            if isinstance(item, TransactionItem):
                if item['address_to'] in self.bloom4contract:
                    continue
                self.bloom4contract.add(item['address_to'])
                yield await self.get_request_contract(
                    address=item['address_to'],
                    block_tag=hex(item['block_number']),
                    cb_kwargs={'address': item['address_to']},
                )

            if isinstance(item, TraceItem) and item['trace_id'] != '0_0':
                if item['address_from'] not in self.bloom4contract:
                    self.bloom4contract.add(item['address_from'])
                    yield await self.get_request_contract(
                        address=item['address_from'],
                        block_tag=hex(item['block_number']),
                        cb_kwargs={'address': item['address_from']},
                    )
                if item['address_to'] not in self.bloom4contract:
                    self.bloom4contract.add(item['address_to'])
                    yield await self.get_request_contract(
                        address=item['address_to'],
                        block_tag=hex(item['block_number']),
                        cb_kwargs={'address': item['address_to']},
                    )

    @log_debug_tracing
    def parse_contract_item(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')
        if result is None or result == '0x':
            return

        # recover cached address
        address = kwargs['address']

        # generate contract item
        yield ContractItem(
            address=address,
            code=result,
        )

    async def get_request_contract(self, address: str, block_tag: str, cb_kwargs: dict) -> scrapy.Request:
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
            callback=self.parse_contract_item,
            cb_kwargs=cb_kwargs if cb_kwargs else dict(),
        )
