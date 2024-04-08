import scrapy


class SubgraphTxItem(scrapy.Item):
    source = scrapy.Field()  # str
    tx = scrapy.Field()  # Dict
    task_info = scrapy.Field()


class ImportanceItem(scrapy.Item):
    source = scrapy.Field()  # str
    importance = scrapy.Field()  # Dict[str, float]
    task_info = scrapy.Field()
