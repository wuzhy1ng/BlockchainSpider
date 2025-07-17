import json
import sys

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import EventLogItem
from BlockchainSpider.items.tron import TronTransactionItem
from BlockchainSpider.middlewares import SyncMiddleware
from BlockchainSpider.spiders.trans.evm import EVMBlockTransactionSpider
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.web3 import hex_to_dec


class TronBlockTransactionSpider(EVMBlockTransactionSpider):
    name = 'trans.block.tron'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.TronTrans2csvPipeline': 299,
        } if len(getattr(settings, 'ITEM_PIPELINES', dict())) == 0
        else getattr(settings, 'ITEM_PIPELINES', dict()),
        'SPIDER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.trans.TokenTransferMiddleware': 542,
            'BlockchainSpider.middlewares.SyncMiddleware': 535,
            **getattr(settings, 'SPIDER_MIDDLEWARES', dict())
        },
    }

    async def get_request_eth_block_by_number(
            self, block_number: int, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        url = await self.provider_bucket.get()
        url = url.replace('/jsonrpc', '')
        url = url + '/wallet/getblock'
        return scrapy.Request(
            url=url,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "id_or_num": str(block_number),
                "detail": True
            }),
            callback=self.parse_eth_get_block_by_number,
            priority=priority,
            cb_kwargs=cb_kwargs,
        )

    @log_debug_tracing
    async def parse_eth_get_block_by_number(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        block_hash = result.get('blockID', '')
        block_number = kwargs.get(SyncMiddleware.SYNC_KEYWORD)
        if block_hash is None:
            return
        block_header = result.get('block_header', {})
        block_raw_data = block_header.get('raw_data', {})
        block_version = block_raw_data.get('version', -1)
        timestamp = block_raw_data.get('timestamp', -1)

        # yield request for events
        yield await self.get_request_eth_get_logs(
            block_number=block_number,
            priority=sys.maxsize - block_number,
            cb_kwargs={'timestamp': timestamp}
        )

        # Parse transactions
        for i, transaction in enumerate(result.get('transactions', [])):
            yield TronTransactionItem(
                transaction_hash=transaction.get('txID', ''),
                transaction_index=i,
                block_hash=block_hash,
                block_number=block_number,
                block_version=block_version,
                timestamp=timestamp,
                raw_data=transaction.get('raw_data', {}),
            )

    async def get_request_eth_get_logs(
            self, block_number: int, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        url = await self.provider_bucket.get()
        url = url + '/wallet/getblockbyid'
        return scrapy.Request(
            url=url,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "eth_getLogs",
                "params": [{
                    "fromBlock": hex(block_number),
                    "toBlock": hex(block_number)
                }],
                "id": 1,
            }),
            callback=self.parse_eth_get_logs,
            priority=priority,
            cb_kwargs=cb_kwargs,
        )

    @log_debug_tracing
    async def parse_eth_get_logs(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        logs = result.get('result')
        for log in logs:
            yield EventLogItem(
                transaction_hash=log.get('transactionHash', ''),
                log_index=hex_to_dec(log.get('logIndex')),
                block_number=hex_to_dec(log.get('blockNumber')),
                timestamp=kwargs['timestamp'],
                address=log.get('address', '').lower(),
                topics=log.get('topics', list()),
                data=log.get('data', ''),
                removed=log.get('removed', False),
            )
