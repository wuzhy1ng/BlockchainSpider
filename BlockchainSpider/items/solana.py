import scrapy

from BlockchainSpider.items.defs import ContextualItem


class SolanaBlockItem(ContextualItem):
    block_hash = scrapy.Field()  # str
    block_height = scrapy.Field()  # int
    block_time = scrapy.Field()  # int
    parent_slot = scrapy.Field()  # str
    previous_blockhash = scrapy.Field()  # str


class SolanaTransactionItem(ContextualItem):
    signature = scrapy.Field()  # str
    block_time = scrapy.Field()  # int
    version = scrapy.Field()  # Union[int, str]
    fee = scrapy.Field()  # int
    compute_consumed = scrapy.Field()  # int
    err = scrapy.Field()  # Union[None, str]
    recent_blockhash = scrapy.Field()  # str


class SolanaBalanceChangesItem(ContextualItem):
    signature = scrapy.Field()  # str
    account = scrapy.Field()  # str
    mint = scrapy.Field()  # Union[None, str]
    owner = scrapy.Field()  # str
    programId = scrapy.Field()  # Union[None, str]
    pre_amount = scrapy.Field()  # str
    post_amount = scrapy.Field()  # str
    decimals = scrapy.Field()  # int


class SolanaLogItem(ContextualItem):
    signature = scrapy.Field()  # str
    index = scrapy.Field()  # str
    log = scrapy.Field()  # str


class SolanaInstructionItem(ContextualItem):
    signature = scrapy.Field()  # str
    trace_id = scrapy.Field()  # str
    data = scrapy.Field()  # Union[None, str], None if parsed
    program_id = scrapy.Field()  # str


# SPL definition, please see:
# https://github.com/solana-labs/solana-program-library/blob/master/token/program/src/instruction.rs
class SPLTokenActionItem(SolanaInstructionItem):
    dtype = scrapy.Field()  # str
    info = scrapy.Field()  # dict


# class SPLInitializeMintItem(SolanaInstructionItem):
#     decimals = scrapy.Field()  # int
#     mint_authority = scrapy.Field()  # str
#     freeze_authority = scrapy.Field()  # str
#
#
# class SPLInitializeAccountItem(SolanaInstructionItem):
#     account = scrapy.Field()  # str
#     pass  # TODO
#
#
# class SPLInitializeMultisigItem(SolanaInstructionItem):
#     account = scrapy.Field()  # str
#     pass  # TODO
#
#
# class SPLTransferItem(SolanaInstructionItem):
#     source = scrapy.Field()  # str
#     destination = scrapy.Field()  # str
#     signer = scrapy.Field()  # str
#     amount = scrapy.Field()  # str
#
#
# class SPLApproveItem(SolanaInstructionItem):
#     source = scrapy.Field()  # str
#     destination = scrapy.Field()  # str
#     signer = scrapy.Field()  # str
#
#
# class SPLRevokeItem(SolanaInstructionItem):
#     source = scrapy.Field()  # str
#     signer = scrapy.Field()  # str
#
#
# class SPLSetAuthorityItem(SolanaInstructionItem):
#     authority = scrapy.Field()  # str
#     signer = scrapy.Field()  # str
#     authority_type = scrapy.Field()  # str
#     new_authority = scrapy.Field()  # str
#
#
# class SPLMintToItem(SolanaInstructionItem):
#     mint = scrapy.Field()  # str
#     account = scrapy.Field()  # str
#     amount = scrapy.Field()  # str
#     mint_authority = scrapy.Field()  # str


class ValidateVotingItem(ContextualItem):
    dtype = scrapy.Field()  # str
    info = scrapy.Field()  # dict
