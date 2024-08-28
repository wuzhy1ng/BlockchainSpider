import scrapy


class LabelReportItem(scrapy.Item):
    labels = scrapy.Field()  # [str]
    urls = scrapy.Field()  # [str]
    addresses = scrapy.Field()  # [dict]
    transactions = scrapy.Field()  # [dict]
    description = scrapy.Field()  # str | dict
    reporter = scrapy.Field()  # str
