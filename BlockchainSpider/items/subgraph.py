import scrapy

from BlockchainSpider.items.defs import ContextualItem


class PopItem(ContextualItem):
    node = scrapy.Field()


class StrategySnapshotItem(ContextualItem):
    data = scrapy.Field()  # Dict


class RankItem(ContextualItem):
    data = scrapy.Field()  # Dict


class AccountTransferItem(ContextualItem):
    id = scrapy.Field()  # str
    hash = scrapy.Field()  # str
    address_from = scrapy.Field()  # str
    address_to = scrapy.Field()  # str
    value = scrapy.Field()  # str
    token_id = scrapy.Field()  # str
    timestamp = scrapy.Field()  # int
    block_number = scrapy.Field()  # int
    contract_address = scrapy.Field()  # str
    symbol = scrapy.Field()  # str
    decimals = scrapy.Field()  # int
    gas = scrapy.Field()  # str
    gas_price = scrapy.Field()  # str


class UTXOTransferItem(ContextualItem):
    id = scrapy.Field()  # str
    tx_from = scrapy.Field()  # str
    tx_to = scrapy.Field()  # str
    address = scrapy.Field()  # str
    value = scrapy.Field()  # str
    is_spent = scrapy.Field()  # bool
    is_coinbase = scrapy.Field()  # bool
    timestamp = scrapy.Field()  # int
    block_number = scrapy.Field()  # int
    fee = scrapy.Field()  # int
