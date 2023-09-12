import scrapy


class SyncSignalItem(scrapy.Item):
    signal = scrapy.Field()  # dict
