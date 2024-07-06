import json
import logging
from typing import Iterator

import scrapy

from BlockchainSpider.items import BlockItem, TraceItem, TransactionItem
from BlockchainSpider.middlewares.defs import LogMiddleware
from BlockchainSpider.spiders.trans.evm.trans import EVMTransactionSpider
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.web3 import hex_to_dec


class TraceMiddleware(LogMiddleware):
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
        async for item in result:
            yield item
            if isinstance(item, BlockItem):
                context_kwargs = item.get_context_kwargs()
                transaction_hashes = [
                    trans['transaction_hash']
                    for trans in context_kwargs['@transactions']
                ]
                yield await self.get_request_debug_trace_block(
                    block_number=item['block_number'],
                    priority=response.request.priority,
                    cb_kwargs={
                        'transaction_hashes': transaction_hashes,
                        'block_number': item['block_number'],
                        'timestamp': item['timestamp'],
                    }
                )
                continue

            if isinstance(spider, EVMTransactionSpider) and isinstance(item, TransactionItem):
                if item.get('gas', 0) <= 21000:
                    continue
                yield await self.get_request_debug_transaction(
                    txhash=item['transaction_hash'],
                    priority=response.request.priority,
                    cb_kwargs={
                        'transaction_hash': item['transaction_hash'],
                        'block_number': item['block_number'],
                        'timestamp': item['timestamp'],
                    }
                )
                continue

    @log_debug_tracing
    async def parse_debug_trace_block(self, response: scrapy.http.Response, **kwargs):
        data = json.loads(response.text)
        data = data.get('result')
        if data is None:
            self.log(
                message='On parse_debug_trace_block, `result` is None, '
                        'please check if your providers are fully available at debug_traceBlockByNumber.',
                level=logging.WARNING,
            )
            return

        # parse trance item (skip the first call)
        transaction_hashes = kwargs['transaction_hashes']
        for idx, trace in enumerate(data):
            trace = trace['result']
            for item, depth, order in self._retrieve_mapping_tree('calls', trace):
                if depth <= 0 and order <= 0:
                    continue
                yield TraceItem(
                    transaction_hash=transaction_hashes[idx],
                    trace_type=item.get('type', ''),
                    trace_id='%d_%d' % (depth, order),
                    block_number=kwargs['block_number'],
                    timestamp=kwargs['timestamp'],
                    address_from=item.get('from', ''),
                    address_to=item.get('to', ''),
                    value=hex_to_dec(item.get('value')),
                    gas=hex_to_dec(item.get('gas')),
                    gas_used=hex_to_dec(item.get('gasUsed')),
                    input=item.get('input', ''),
                    output=item.get('output', ''),
                )

    @log_debug_tracing
    def parse_debug_transaction(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')
        if result is None:
            self.log(
                message='On parse_debug_transaction, `result` is None, '
                        'please check if your providers are fully available at debug_traceBlockByNumber.',
                level=logging.WARNING,
            )
            return

        # parse trance item (skip the first call)
        for item, depth, order in self._retrieve_mapping_tree('calls', result):
            if depth <= 0 and order <= 0:
                continue
            yield TraceItem(
                transaction_hash=kwargs['transaction_hash'],
                trace_type=item.get('type', ''),
                trace_id='%d_%d' % (depth, order),
                block_number=kwargs['block_number'],
                timestamp=kwargs['timestamp'],
                address_from=item.get('from', ''),
                address_to=item.get('to', ''),
                value=hex_to_dec(item.get('value')),
                gas=hex_to_dec(item.get('gas')),
                gas_used=hex_to_dec(item.get('gasUsed')),
                input=item.get('input', ''),
                output=item.get('output', ''),
            )

    async def get_request_debug_trace_block(
            self, block_number: int, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "debug_traceBlockByNumber",
                "params": [hex(block_number), {"tracer": "callTracer"}],
                "id": 1
            }),
            priority=priority,
            callback=self.parse_debug_trace_block,
            cb_kwargs=cb_kwargs if cb_kwargs else dict(),
        )

    async def get_request_debug_transaction(
            self, txhash: str, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "debug_traceTransaction",
                "params": [txhash, {"tracer": "callTracer"}],
                "id": 1
            }),
            priority=priority,
            callback=self.parse_debug_transaction,
            cb_kwargs=cb_kwargs if cb_kwargs else dict(),
        )

    def _retrieve_mapping_tree(self, key: str, item: dict, depth: int = 0, order: int = 0) -> Iterator:
        if item is None:
            yield None, -1, -1
            return

        yield item, depth, order
        if not item.get(key):
            return
        for idx, child in enumerate(item[key]):
            yield from self._retrieve_mapping_tree(key, child, depth + 1, idx)
