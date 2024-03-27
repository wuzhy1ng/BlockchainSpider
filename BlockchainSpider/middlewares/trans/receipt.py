import json
import logging

import scrapy

from BlockchainSpider.items import EventLogItem, TransactionReceiptItem, BlockItem, TransactionItem
from BlockchainSpider.middlewares.defs import LogMiddleware
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.web3 import hex_to_dec, web3_json_rpc


class TransactionReceiptMiddleware(LogMiddleware):
    def __init__(self):
        self.provider_bucket = None
        self.block_receipt_method = None
        self._is_checked = False

    async def _init_by_spider(self, spider):
        if self.provider_bucket is not None:
            return
        if getattr(spider, 'middleware_providers') and \
                spider.middleware_providers.get(self.__class__.__name__):
            self.provider_bucket = spider.middleware_providers[self.__class__.__name__]
        else:
            self.provider_bucket = spider.provider_bucket

        block_receipt_method = getattr(spider, 'block_receipt_method', '')
        if block_receipt_method == '':
            self._is_checked = True
            self.block_receipt_method = None
            return

        # test rpc interface
        rpc_rsp = await web3_json_rpc(
            tx_obj={
                "jsonrpc": "2.0",
                "method": block_receipt_method,
                "params": ["0x0"],
                "id": 1,
            },
            provider=await self.provider_bucket.get(),
            timeout=5,
        )
        self._is_checked = True
        if rpc_rsp is None:
            self.log(
                message="`%s` is not available, " % block_receipt_method +
                        "using `eth_getTransactionReceipt` instead.",
                level=logging.INFO,
            )
            self.block_receipt_method = None
        else:
            self.log(
                message="Using `%s` for speeding up." % block_receipt_method,
                level=logging.INFO,
            )
            self.block_receipt_method = block_receipt_method

    async def process_spider_output(self, response, result, spider):
        await self._init_by_spider(spider)
        async for item in result:
            yield item
            if isinstance(item, BlockItem) and self.block_receipt_method is not None:
                ctx_kwargs = item.get_context_kwargs()
                yield await self.get_request_eth_block_receipt(
                    block_number=item['block_number'],
                    priority=response.request.priority,
                    cb_kwargs={'@transactions': ctx_kwargs['@transactions']},
                )
                continue

            if isinstance(item, TransactionItem) and self.block_receipt_method is None:
                yield await self.get_request_eth_transaction_receipt(
                    transaction_hash=item['transaction_hash'],
                    priority=response.request.priority,
                    cb_kwargs={'@transaction': item},
                )

    @log_debug_tracing
    async def parse_eth_block_receipt(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')
        txhash2transaction = {
            item['transaction_hash']: item
            for item in kwargs['@transactions']
        }

        # generate items
        for item in result:
            txhash = item.get('transactionHash', '')
            transaction = txhash2transaction.get(txhash)
            if transaction is None:
                continue
            for log in item['logs']:
                yield EventLogItem(
                    transaction_hash=log.get('transactionHash', ''),
                    log_index=hex_to_dec(log.get('logIndex')),
                    block_number=hex_to_dec(log.get('blockNumber')),
                    timestamp=transaction['timestamp'],
                    address=log.get('address', '').lower(),
                    topics=log.get('topics', list()),
                    data=log.get('data', ''),
                    removed=log.get('removed', False),
                )
            yield TransactionReceiptItem(
                transaction_hash=txhash,
                transaction_index=hex_to_dec(item.get('transactionIndex')),
                transaction_type=hex_to_dec(item.get('type')),
                block_hash=item.get('blockHash', ''),
                block_number=hex_to_dec(item.get('blockNumber')),
                gas_used=hex_to_dec(item.get('gasUsed')),
                effective_gas_price=hex_to_dec(item.get('effectiveGasPrice')),
                created_contract=item['contractAddress'] if item.get('contractAddress') else '',
                is_error=item.get('status') != '0x1',
                cb_kwargs={'@transaction': transaction}
            )

    @log_debug_tracing
    async def parse_eth_get_transaction_receipt(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')
        transaction: TransactionItem = kwargs['@transaction']

        for log in result['logs']:
            yield EventLogItem(
                transaction_hash=log.get('transactionHash', ''),
                log_index=hex_to_dec(log.get('logIndex')),
                block_number=hex_to_dec(log.get('blockNumber')),
                timestamp=transaction['timestamp'],
                address=log.get('address', '').lower(),
                topics=log.get('topics', list()),
                data=log.get('data', ''),
                removed=log.get('removed', False),
            )
        yield TransactionReceiptItem(
            transaction_hash=result.get('transactionHash', ''),
            transaction_index=hex_to_dec(result.get('transactionIndex')),
            transaction_type=hex_to_dec(result.get('type')),
            block_hash=result.get('blockHash', ''),
            block_number=hex_to_dec(result.get('blockNumber')),
            gas_used=hex_to_dec(result.get('gasUsed')),
            effective_gas_price=hex_to_dec(result.get('effectiveGasPrice')),
            created_contract=result['contractAddress'] if result.get('contractAddress') else '',
            is_error=result.get('status') != '0x1',
            cb_kwargs={'@transaction': transaction},
        )

    async def get_request_eth_block_receipt(
            self, block_number: int, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": self.block_receipt_method,
                "params": [
                    hex(block_number) if isinstance(block_number, int) else block_number,
                ],
                "id": 1
            }),
            callback=self.parse_eth_block_receipt,
            priority=priority,
            cb_kwargs=cb_kwargs,
        )

    async def get_request_eth_transaction_receipt(
            self, transaction_hash: int, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "eth_getTransactionReceipt",
                "params": [transaction_hash],
                "id": 1
            }),
            callback=self.parse_eth_get_transaction_receipt,
            priority=priority,
            cb_kwargs=cb_kwargs,
        )
