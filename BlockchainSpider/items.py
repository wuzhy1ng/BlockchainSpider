# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class LabelItem(scrapy.Item):
    net = scrapy.Field()
    label = scrapy.Field()
    info = scrapy.Field()


class TxItem(scrapy.Item):
    source = scrapy.Field()
    tx = scrapy.Field()
