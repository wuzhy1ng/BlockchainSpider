import scrapy


class LabelReportItem(scrapy.Item):
    labels = scrapy.Field()  # [str]
    urls = scrapy.Field()  # [str]
    addresses = scrapy.Field()  # [LabelAddressItem]
    transactions = scrapy.Field()  # [LabelTransactionItem]
    description = scrapy.Field()  # str | dict
    reporter = scrapy.Field()  # str


class LabelAddressItem(scrapy.Item):
    net = scrapy.Field()  # str
    address = scrapy.Field()  # str


class LabelTransactionItem(scrapy.Item):
    net = scrapy.Field()  # str
    transaction_hash = scrapy.Field()  # str
