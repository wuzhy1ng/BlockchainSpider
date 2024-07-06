import json
import logging

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import SolanaBlockItem, SolanaTransactionItem
from BlockchainSpider.items.solana import SolanaLogItem, SolanaInstructionItem
from BlockchainSpider.spiders.trans.evm import EVMBlockTransactionSpider


class SolanaBlockTransactionSpider(EVMBlockTransactionSpider):
    name = 'trans.block.solana'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.Solana2csvPipeline': 299,
        } if len(getattr(settings, 'ITEM_PIPELINES', dict())) == 0
        else getattr(settings, 'ITEM_PIPELINES', dict()),
        'SPIDER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.SyncMiddleware': 535,
            **getattr(settings, 'SPIDER_MIDDLEWARES', dict())
        },
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        available_middlewares = {
            'BlockchainSpider.middlewares.trans.SPLTokenTransferMiddleware': 541,
        }
        middlewares = kwargs.get('enable')
        if middlewares is not None:
            spider_middlewares = spider.settings.getdict('SPIDER_MIDDLEWARES')
            for middleware in middlewares.split(','):
                assert middleware in available_middlewares
                spider_middlewares[middleware] = available_middlewares[middleware]
            spider.settings.set(
                name='SPIDER_MIDDLEWARES',
                value=spider_middlewares,
                priority=spider.settings.attributes['SPIDER_MIDDLEWARES'].priority,
            )
        return spider

    async def parse_eth_block_number(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')

        # generate more requests
        if result is not None:
            end_block = result
            start_block, self._block_cursor = self._block_cursor, end_block
            if end_block - start_block > 0:
                self.log(
                    message='Try to fetch the new block to: #%d' % end_block,
                    level=logging.INFO,
                )
            for blk in range(start_block, end_block):
                yield await self.get_request_eth_block_by_number(
                    block_number=blk,
                    priority=2 ** 32 - blk,
                    cb_kwargs={self.sync_item_key: {'block_number': blk}},
                )
        else:
            self.log(
                message="Result field is None on eth_getBlockNumber" +
                        "please ensure that whether the provider is available.",
                level=logging.ERROR
            )

        # next query of block number
        if self.end_block is not None:
            return
        yield await self.get_request_eth_block_number()

    async def parse_eth_get_block_by_number(self, response: scrapy.http.Response, **kwargs):
        data = json.loads(response.text)
        result = data.get('result')

        block_time = result.get('blockTime', '')
        yield SolanaBlockItem(
            block_height=result.get('blockHeight', ''),
            block_time=block_time,
            block_hash=result.get('blockhash', ''),
            parent_slot=result.get('parentSlot', ''),
            previous_blockhash=result.get('previousBlockhash', ''),
        )
        for item in result['transactions']:
            signature = item['transaction']['signatures'][0]
            yield SolanaTransactionItem(
                signature=signature,
                block_time=block_time,
                version=item['version'],
                fee=item['meta']['fee'],
                compute_consumed=item['meta']['computeUnitsConsumed'],
                err=None if item['meta']['err'] is None else item['meta']['err'].keys()[0],
                recent_blockhash=item['transaction']['message']['recentBlockhash'],
            )

            # TODO: parse balance changes
            accounts = [ak['pubkey'] for ak in item['transaction']['message']['accountKeys']]

            # parse logs
            for index, log in enumerate(item['meta']['logMessages']):
                yield SolanaLogItem(
                    signature=signature,
                    index=index,
                    log=log,
                )

            # TODO: parse instructions
            trace_ids, instructions = list(), list()
            for index, instruction in enumerate(item['transaction']['message']['instructions']):
                trace_ids.append(str(index))
                instructions.append(instruction)
            for inner_instruction in item['meta'].get('innerInstructions', []):
                index = inner_instruction['index']
                for inst in inner_instruction['instructions']:
                    pass

    def get_request_web3_client_version(self) -> scrapy.Request:
        return scrapy.Request(
            url=self.provider_bucket.items[0],
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "getVersion",
                "id": 1
            }),
            callback=self._start_requests,
        )

    async def get_request_eth_block_number(self) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlockHeight",
            }),
            callback=self.parse_eth_block_number,
            errback=self.errback_parse_eth_block_number,
            priority=0,
            dont_filter=True,
        )

    async def get_request_eth_block_by_number(
            self, block_number: int, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlock",
                "params": [
                    block_number,
                    {
                        "encoding": "jsonParsed",
                        "maxSupportedTransactionVersion": 0,
                        "transactionDetails": "full",
                        "rewards": False
                    }
                ]
            }),
            callback=self.parse_eth_get_block_by_number,
            priority=priority,
            cb_kwargs=cb_kwargs,
        )
