import json
import logging

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import SolanaBlockItem, SolanaTransactionItem
from BlockchainSpider.items.solana import SolanaLogItem, SolanaInstructionItem,SolanaBalanceChangesItem,SPLTokenActionItem,ValidateVotingItem,SystemItem,SPLmemoItem,SolanaInnerInstructionItem
from BlockchainSpider.spiders.trans.evm import EVMBlockTransactionSpider


class SolanaBlockTransactionSpider(EVMBlockTransactionSpider):
    name = 'trans.block.solana'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.SolanaTrans2csvPipeline': 299,
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
                    cb_kwargs={self.sync_item_key: {'block_height': blk}},
                )
        else:
            self.log(
                message="Result field is None on getBlockHeight" +
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
        if result is None:
            self.log(
                message="Result field is None on getBlock" +
                        "please ensure that whether the provider is available.",
                level=logging.ERROR
            )
            return

        #block_height = kwargs[self.sync_item_key]['block_height']
        block_time = result.get('blockTime', -1)
        yield SolanaBlockItem(
            block_height=result.get('blockheight', -1),
            block_time=block_time,
            block_hash=result.get('blockhash', ''),
            parent_slot=result.get('parentSlot', -1),
            previous_blockhash=result.get('previousBlockhash', ''),
        )
        for item in result['transactions']:
            trans_meta = item.get('meta')
            signature = item['transaction']['signatures'][0]
            err = list(trans_meta['err'].keys())[0] \
                if isinstance(trans_meta, dict) and isinstance(trans_meta.get('err'), dict) else ''
            yield SolanaTransactionItem(
                signature=signature,
                block_time=block_time,
                version=item.get('version', 'legacy'),
                fee=trans_meta['fee'] if trans_meta is not None else -1,
                compute_consumed=trans_meta['computeUnitsConsumed'] if trans_meta is not None and 'computeUnitsConsumed' in trans_meta.keys() else -1, #有些区块的meta无computeUnitsConsumed关键字
                err=err,
                recent_blockhash=item['transaction']['message']['recentBlockhash'],
            )
            #TODO: parse balance changes

            accounts = [ak['pubkey'] for ak in item['transaction']['message']['accountKeys']]

            if isinstance(trans_meta, dict) \
                    and isinstance(trans_meta.get('preTokenBalances'), list) \
                    and isinstance(trans_meta.get('postTokenBalances'), list):
                pre_balances = [None for _ in range(len(accounts))]
                for balance in trans_meta['preTokenBalances']:
                    idx = balance.get('accountIndex')
                    if idx is None: continue
                    pre_balances[idx] = balance
                post_balances = [None for _ in range(len(accounts))]
                for balance in trans_meta['postTokenBalances']:
                    idx = balance.get('accountIndex')
                    if idx is None: continue
                    post_balances[idx] = balance
                for i, account in enumerate(accounts):
                    pre_balance, post_balance = pre_balances[i], post_balances[i]
                    if pre_balance is None or post_balance is None:
                        continue
                    yield SolanaBalanceChangesItem(
                        signature=signature,
                        account=account,
                        mint=pre_balance.get('mint', ''),
                        owner=pre_balance.get('owner', ''),
                        program_id=pre_balance.get('programId', ''),
                        pre_amount=pre_balance['uiTokenAmount']['amount'],
                        post_amount=post_balance['uiTokenAmount']['amount'],
                        decimals=post_balance['uiTokenAmount']['decimals'],
                    )

            #parse logs
            if isinstance(trans_meta, dict) and trans_meta.get('logMessages'):
                for index, log in enumerate(item['meta']['logMessages']):
                    yield SolanaLogItem(

                        signature=signature,
                        index=index,
                        log=log,
                    )
            if item:
                trace_ids, instructions = list(), list()
                for index, instruction in enumerate(item['transaction']['message']['instructions']):
                    trace_ids.append(str(index))
                    instructions.append(instruction)
                    program_id = instruction['programId']
                    if not instruction.get('parsed'):
                        yield SolanaInstructionItem(
                            signature=signature,
                            trace_id=index,
                            data=instruction.get('data', ''),
                            program_id=program_id
                        )
                        continue
                    parsed_instruction = instruction['parsed']
                    program = instruction['program']
                    if program == 'spl-token':
                        yield SPLTokenActionItem(
                            signature=signature,
                            trace_id=index,
                            program_id=program_id,
                            dtype=parsed_instruction['type'],
                            info=parsed_instruction['info'],
                            program=program
                        )
                    elif program == 'vote':
                        yield ValidateVotingItem(
                            signature=signature,
                            trace_id=index,
                            program_id=program_id,
                            dtype=parsed_instruction['type'],
                            info=parsed_instruction['info'],
                            program=program
                        )
                    elif program == 'system':
                        yield SystemItem(
                            signature=signature,
                            trace_id=index,
                            program_id=program_id,
                            dtype=parsed_instruction['type'],
                            info=parsed_instruction['info'],
                            program=program
                        )
                    elif program == 'spl-memo':
                        yield SPLmemoItem(
                            signature = signature,
                            trace_id = index,
                            program=program,
                            program_id=program_id
                        )

            if isinstance(trans_meta, dict) and trans_meta.get('innerInstructions'):
                    for inner_instruction in trans_meta['innerInstructions']:
                        index = inner_instruction['index']+1
                        stack_height_array=list()
                        idx_array=[]
                        for instruction in inner_instruction['instructions']:
                            stack_height_array.append(instruction['stackHeight'])

                        idx_array=generate_multilevel_sequence(stack_height_array,index)

                        for idx,instruction in enumerate(inner_instruction['instructions']):
                            program_id=instruction['programId']
                            if not instruction.get('parsed'):
                                yield SolanaInnerInstructionItem(
                                    signature=signature,
                                    trace_id=idx_array[idx],
                                    program_id=program_id,
                                    data=instruction.get('data', '')
                                )
                                continue
                            parsed_instruction = instruction['parsed']
                            program = instruction['program']
                            if program == 'spl-token':
                                yield SPLTokenActionItem(
                                    signature=signature,
                                    trace_id=idx_array[idx],
                                    program_id=program_id,
                                    dtype=parsed_instruction['type'],
                                    info=parsed_instruction['info'],
                                    program=program
                                )
                            elif program == 'vote':
                                yield ValidateVotingItem(
                                    signature=signature,
                                    trace_id=idx_array[idx],
                                    program_id=program_id,
                                    dtype=parsed_instruction['type'],
                                    info=parsed_instruction['info'],
                                    program=program
                                )
                            elif program == 'spl-memo':
                                yield SPLmemoItem(
                                    signature=signature,
                                    trace_id=idx_array[idx],
                                    program_id=program_id,
                                    program=program
                                )
                            elif program == 'system':
                                yield SystemItem(
                                    signature=signature,
                                    trace_id=idx_array[idx],
                                    program_id=program_id,
                                    dtype=parsed_instruction['type'],
                                    info=parsed_instruction['info'],
                                    program=program
                                )

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


def generate_multilevel_sequence(levels, start):

    stack = [start - 1]
    result = []
    def add_sequence(level):
        if level > len(stack):
            stack.append(1)
        else:
            stack[level - 1] += 1
            for i in range(level, len(stack)):
                stack[i] = 0

        result.append(".".join(str(num) for num in stack[:level]))

    for num in levels:
        add_sequence(num)

    return result



