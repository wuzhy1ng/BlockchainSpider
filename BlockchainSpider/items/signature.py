import scrapy


class SignatureItem(scrapy.Item):
    address = scrapy.Field()  # [str]
    signature = scrapy.Field()  # [str]

class TransactionsItem(scrapy.Item):
    signature=scrapy.Field()  # str
    data = scrapy.Field()  # list