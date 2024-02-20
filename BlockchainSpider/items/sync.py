import scrapy


class SyncDataItem(scrapy.Item):
    data = scrapy.Field()  # dict
