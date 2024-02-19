import scrapy


class SyncDataItem(scrapy.Item):
    data = scrapy.Field()  # dict


class SyncSignalItem(scrapy.Item):
    is_add_lock = scrapy.Field()  # bool
