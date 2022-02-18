# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class LabelItem(scrapy.Item):
    net = scrapy.Field()
    label = scrapy.Field()
    info = scrapy.Field()


class SubgraphTxItem(scrapy.Item):
    source = scrapy.Field()
    tx = scrapy.Field()
    task_info = scrapy.Field()


class ImportanceItem(scrapy.Item):
    source = scrapy.Field()
    importance = scrapy.Field()
    task_info = scrapy.Field()


class BlockMetaItem(scrapy.Item):
    info = scrapy.Field()


class BlockTxItem(scrapy.Item):
    info = scrapy.Field()
    tx_type = scrapy.Field()


class CloseItem(scrapy.Item):
    task_info = scrapy.Field()
