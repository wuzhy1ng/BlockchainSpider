import scrapy


class MotifTransactionRepresentationItem(scrapy.Item):
    transaction_hash = scrapy.Field()  # str
    vector = scrapy.Field()  # List[float]
