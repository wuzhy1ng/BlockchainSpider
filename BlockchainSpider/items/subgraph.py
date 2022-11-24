import scrapy


class SubgraphTxItem(scrapy.Item):
    source = scrapy.Field()
    tx = scrapy.Field()
    task_info = scrapy.Field()


class ImportanceItem(scrapy.Item):
    source = scrapy.Field()
    importance = scrapy.Field()
    task_info = scrapy.Field()
