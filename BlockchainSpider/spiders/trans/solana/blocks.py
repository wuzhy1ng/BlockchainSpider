import json
import logging
from typing import List

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import SolanaBlockItem, SolanaTransactionItem
from BlockchainSpider.items.solana import SolanaLogItem, SolanaInstructionItem, SolanaBalanceChangesItem, \
    SPLTokenActionItem, ValidateVotingItem, SystemItem, SPLMemoItem
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
                    cb_kwargs={'$sync': blk},
                )
        else:
            self.log(
                message="Result field is None on getBlockHeight," +
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
        block_height = kwargs['$sync']
        if result is None:
            self.log(
                message="Result field is None on getBlock method, " +
                        "please ensure that whether the provider is available. " +
                        "(blockHeight: {})".format(block_height),
                level=logging.ERROR
            )
            return

        block_time = result.get('blockTime', -1)
        yield SolanaBlockItem(
            block_height=block_height,
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
                signer=item['transaction']['message']['accountKeys'][0]['pubkey'],
                block_time=block_time,
                block_height=block_height,
                version=item.get('version', 'legacy'),
                fee=trans_meta['fee'] if trans_meta is not None else -1,
                compute_consumed=trans_meta['computeUnitsConsumed'] if trans_meta.get('computeUnitsConsumed') else -1,
                err=err,
                recent_blockhash=item['transaction']['message']['recentBlockhash'],
            )

            # parse balance changes
            accounts = [ak['pubkey'] for ak in item['transaction']['message']['accountKeys']]
            if isinstance(trans_meta, dict) \
                    and isinstance(trans_meta.get('preTokenBalances'), list) \
                    and isinstance(trans_meta.get('postTokenBalances'), list):
                token_account2pre_balance = {
                    accounts[pre_balance['accountIndex']]: pre_balance
                    for pre_balance in trans_meta['preTokenBalances']
                }
                token_account2post_balance = {
                    accounts[post_balance['accountIndex']]: post_balance
                    for post_balance in trans_meta['postTokenBalances']
                }
                token_accounts = set(token_account2pre_balance.keys())
                token_accounts = token_accounts.union(set(token_account2post_balance.keys()))
                for token_account in token_accounts:
                    pre_balance = token_account2pre_balance.get(token_account)
                    post_balance = token_account2post_balance.get(token_account)
                    pre_amount = pre_balance['uiTokenAmount']['amount'] if pre_balance is not None else 0
                    post_amount = post_balance['uiTokenAmount']['amount'] if post_balance is not None else 0
                    if pre_amount == post_amount:
                        continue
                    balance_info = pre_balance if pre_balance is not None else post_balance
                    yield SolanaBalanceChangesItem(
                        signature=signature,
                        account=token_account,
                        mint=balance_info.get('mint', ''),
                        owner=balance_info.get('owner', ''),
                        program_id=balance_info.get('programId', ''),
                        pre_amount=pre_amount,
                        post_amount=post_amount,
                        decimals=balance_info['uiTokenAmount']['decimals'],
                    )
            if isinstance(trans_meta, dict) \
                    and isinstance(trans_meta.get('preBalances'), list) \
                    and isinstance(trans_meta.get('postBalances'), list):
                pre_balances = trans_meta['preBalances']
                post_balances = trans_meta['postBalances']
                for i, account in enumerate(accounts):
                    pre_balance, post_balance = pre_balances[i], post_balances[i]
                    if post_balance == pre_balance:
                        continue
                    yield SolanaBalanceChangesItem(
                        signature=signature,
                        account=account,
                        mint='',
                        owner=account,
                        program_id='11111111111111111111111111111111',
                        pre_amount=pre_balance,
                        post_amount=post_balance,
                        decimals=9,
                    )

            # parse logs
            if isinstance(trans_meta, dict) and trans_meta.get('logMessages'):
                for index, log in enumerate(item['meta']['logMessages']):
                    yield SolanaLogItem(
                        signature=signature,
                        index=index,
                        log=log,
                    )

            # parse instructions
            for index, instruction in enumerate(item['transaction']['message']['instructions']):
                program_id = instruction['programId']
                if not instruction.get('parsed'):
                    yield SolanaInstructionItem(
                        signature=signature,
                        trace_id=index,
                        data=instruction.get('data', ''),
                        program_id=program_id,
                        accounts=instruction.get('accounts', []),
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
                    yield SPLMemoItem(
                        signature=signature,
                        trace_id=index,
                        program_id=program_id,
                        memo=parsed_instruction,
                        program=program,
                    )

            # parse inner instructions
            if isinstance(trans_meta, dict) and trans_meta.get('innerInstructions'):
                for inner_instruction in trans_meta['innerInstructions']:
                    index = inner_instruction['index'] + 1
                    stack_height_array = list()
                    for instruction in inner_instruction['instructions']:
                        stack_height_array.append(instruction['stackHeight'])

                    idx_array = self._generate_multilevel_sequence(stack_height_array, index)
                    for idx, instruction in enumerate(inner_instruction['instructions']):
                        program_id = instruction['programId']
                        if not instruction.get('parsed'):
                            yield SolanaInstructionItem(
                                signature=signature,
                                trace_id=idx_array[idx],
                                program_id=program_id,
                                data=instruction.get('data', ''),
                                accounts=instruction.get('accounts', []),
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
                            yield SPLMemoItem(
                                signature=signature,
                                trace_id=idx_array[idx],
                                program_id=program_id,
                                memo=parsed_instruction,
                                program=program,
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
                "method": "getSlot",
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

    @staticmethod
    def _generate_multilevel_sequence(levels: List[int], start: int) -> List[str]:
        stack = [start - 1]
        result = []

        def _add_sequence(level):
            if level > len(stack):
                stack.append(1)
            else:
                stack[level - 1] += 1
                for i in range(level, len(stack)):
                    stack[i] = 0

            result.append(".".join(str(num) for num in stack[:level]))

        for num in levels:
            _add_sequence(num)
        return result
