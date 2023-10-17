import scrapy


class SignItem(scrapy.Item):
    text = scrapy.Field()  # str
    sign = scrapy.Field()  # str
    type = scrapy.Field()  # str
