import scrapy
import json
import logging
import time
import asyncio
from BlockchainSpider import settings
from BlockchainSpider.items import SolanaBlockItem,SolanaTransactionItem
from BlockchainSpider.utils.bucket import AsyncItemBucket
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.web3 import hex_to_dec

class SolanaSpider(scrapy.Spider):
    name = 'trans.block.solana'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.Trans2csvPipeline': 299,
            'BlockchainSpider.pipelines.TransDCFG2csvPipeline': 298,
            'BlockchainSpider.pipelines.TransBloomFilterPipeline': 297,
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
            'BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware': 542,
            'BlockchainSpider.middlewares.trans.TokenTransferMiddleware': 541,
            'BlockchainSpider.middlewares.trans.TokenPropertyMiddleware': 540,
            'BlockchainSpider.middlewares.trans.MetadataMiddleware': 539,
            'BlockchainSpider.middlewares.trans.TraceMiddleware': 538,
            'BlockchainSpider.middlewares.trans.ContractMiddleware': 537,
            'BlockchainSpider.middlewares.trans.DCFGMiddleware': 536,
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # output dir and block range
        self.out_dir = kwargs.get('out', './data')
        self.start_block = int(kwargs.get('start_blk', '0'))
        self.end_block = int(kwargs['end_blk']) if kwargs.get('end_blk') else None
        self._block_cursor = self.start_block
        self.blocks = [
            int(blk) for blk in kwargs['blocks'].split(',')
        ] if kwargs.get('blocks') else None

        # block receipt method
        self.block_receipt_method = kwargs.get('block_receipt_method', 'eth_getBlockReceipts')

        # sync signal key
        self.sync_item_key = 'sync_item'

        # provider settings
        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
        )

        # provider settings for specific data
        self.middleware_providers = {
            'TransactionReceiptMiddleware': AsyncItemBucket(
                items=kwargs['providers4receipt'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4receipt') else None,
            'TraceMiddleware': AsyncItemBucket(
                items=kwargs['providers4trace'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4trace') else None,
            'TokenTransferMiddleware': AsyncItemBucket(
                items=kwargs['providers4token_transfer'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4token_transfer') else None,
            'TokenPropertyMiddleware': AsyncItemBucket(
                items=kwargs['providers4token_property'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4token_property') else None,
            'MetadataMiddleware': AsyncItemBucket(
                items=kwargs['providers4metadata'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4metadata') else None,
            'ContractMiddleware': AsyncItemBucket(
                items=kwargs['providers4contract'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4contract') else None,
            'DCFGMiddleware': AsyncItemBucket(
                items=kwargs['providers4dcfg'].split(','),
                qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
            ) if kwargs.get('providers4dcfg') else None,
        }
    def start_requests(self):
        for slot_number in range(self.start_block, self.end_block + 1):
            request = self.get_request_solana_block(slot_number)
            time.sleep(1 / self.provider_bucket.qps)
            yield request

    async def parse_solana_block(self, response: scrapy.http.Response, **kwargs):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON response")
            return

        result = data.get('result')
        if result is None:
            self.logger.error("Received None result")
            return

        yield SolanaBlockItem(
            blockheight=result.get('blockHeight', ''),
            blocktime=result.get('blockTime', ''),
            blockhash=result.get('blockhash', ''),
            parentslot=result.get('parentSlot', ''),
            previousblockhash=result.get('previousBlockhash', ''),
        )

        result = result.get('transactions')
        if result is None:
            self.logger.error("No transactions found in the result")
            return

        transaction = list()
        for item in result:
            instructions = item['transaction']['message']['instructions']
            instruction_data = [instruction['data'] for instruction in instructions]  # 提取所有指令的 data 字段
            item = SolanaTransactionItem(
                fee=item['meta']['fee'],
                innerinstructions=item['meta']['innerInstructions'],
                postbalances=item['meta']['postBalances'],
                posttokenbalances=item['meta']['postTokenBalances'],
                prebalances=item['meta']['preBalances'],
                pretokenbalances=item['meta']['preTokenBalances'],
                accountkeys=item['transaction']['message']['accountKeys'],
                instructions=item['transaction']['message']['instructions'],
                data= instruction_data,
                recentblockhash=item['transaction']['message']['recentBlockhash'],
                signatures=item['transaction']['signatures']
            )
            transaction.append(item)
            yield item



    def get_request_solana_block(self, slot_number: int) -> scrapy.Request:
        return scrapy.Request(
            url='https://api.devnet.solana.com',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlock",
                "params": [
                    slot_number,
                    {
                        "commitment": "finalized",
                        "encoding": "json",
                        "maxSupportedTransactionVersion": 0,
                        "transactionDetails": "full",
                        "rewards": False
                    }
                ]
            }),
            callback=self.parse_solana_block,
            priority=0,
            dont_filter=True,
        )