import json

import scrapy

from BlockchainSpider.items import TransactionReceiptItem
from BlockchainSpider.items.evm import ContractItem
from BlockchainSpider.middlewares.defs import LogMiddleware
from BlockchainSpider.utils.decorator import log_debug_tracing


class ContractMiddleware(LogMiddleware):
    def __init__(self):
        self.provider_bucket = None

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
                yield await self.get_request_contract(
                    address=item['created_contract'],
                    block_tag=hex(item['block_number']),
                    priority=response.request.priority,
                    cb_kwargs={'@receipt': item},
                )

    @log_debug_tracing
    async def parse_contract_item(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')
        if result is None or result == '0x':
            return

        receipt: TransactionReceiptItem = kwargs['@receipt']
        yield ContractItem(
            address=receipt['created_contract'],
            code=result,
            cb_kwargs={'@receipt': receipt}
        )

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
