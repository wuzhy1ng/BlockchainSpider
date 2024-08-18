import scrapy


class SyncItem(scrapy.Item):
    key = scrapy.Field()  # Any
    data = scrapy.Field()  # dict
