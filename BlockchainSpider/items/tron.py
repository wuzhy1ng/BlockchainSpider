import scrapy

from BlockchainSpider.items.defs import ContextualItem


class TronTransactionItem(ContextualItem):
    transaction_hash = scrapy.Field()  # str
    transaction_index = scrapy.Field()  # int
    block_hash = scrapy.Field()  # str
    block_number = scrapy.Field()  # int
    block_version = scrapy.Field()  # int
    timestamp = scrapy.Field()  # int
    raw_data = scrapy.Field()  # dict
