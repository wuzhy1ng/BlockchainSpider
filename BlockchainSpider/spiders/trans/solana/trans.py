import json
import logging
import time

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items.solana import SPLMemoItem, ValidateVotingItem, SystemItem, SolanaInstructionItem, \
    SPLTokenActionItem, SolanaTransactionItem, SolanaBalanceChangesItem, SolanaLogItem
from BlockchainSpider.middlewares import SyncMiddleware
from BlockchainSpider.spiders.trans.solana import SolanaBlockTransactionSpider
from BlockchainSpider.utils.bucket import AsyncItemBucket
from BlockchainSpider.utils.decorator import log_debug_tracing


class SolanaTransactionSpider(scrapy.Spider):
    name = 'trans.solana'
    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.SyncMiddleware': 535,
            **getattr(settings, 'SPIDER_MIDDLEWARES', dict())
        },
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.SolanaTrans2csvPipeline': 299,
        } if len(getattr(settings, 'ITEM_PIPELINES', dict())) == 0
        else getattr(settings, 'ITEM_PIPELINES', dict()),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # output dir and transaction hash
        self.out_dir = kwargs.get('out', './data')
        self.txhashs = kwargs.get('hash', '').split(',')

        # provider settings
        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
        )

    def start_requests(self):
        request = self.get_request_web3_client_version()
        time.sleep(1 / self.provider_bucket.qps)
        yield request

    @log_debug_tracing
    async def _start_requests(self, response: scrapy.http.Response, **kwargs):
        try:
            result = json.loads(response.text)
            result = result.get('result')
            self.log(
                message="Detected client version: {}, {} is starting.".format(
                    result, getattr(settings, 'BOT_NAME'),
                ),
                level=logging.INFO,
            )
        except:
            pass

        for i, txhash in enumerate(self.txhashs):
            yield await self.get_request_eth_transaction(
                txhash=txhash,
                priority=len(self.txhashs) - i,
                cb_kwargs={
                    'txhash': txhash,
                    SyncMiddleware.SYNC_KEYWORD: txhash,
                },
            )

    @log_debug_tracing
    async def parse_transaction(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        item = result.get('result')

        block_time = item.get('blockTime', -1)
        block_height = item.get('slot', -1)
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
            compute_consumed=trans_meta['computeUnitsConsumed'] \
                if trans_meta is not None and trans_meta.get('computeUnitsConsumed') else -1,
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

                idx_array = SolanaBlockTransactionSpider._generate_multilevel_sequence(stack_height_array, index)
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

    async def get_request_eth_transaction(
            self, txhash: str, priority: int, cb_kwargs: dict = None
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    txhash,
                    {
                        "commitment": "confirmed",
                        "maxSupportedTransactionVersion": 0,
                        "encoding": "jsonParsed"
                    }
                ]
            }),
            priority=priority,
            cb_kwargs=cb_kwargs if cb_kwargs else dict(),
            callback=self.parse_transaction,
        )
