import scrapy


class SourceCodeItem(scrapy.Item):
    compiler_version = scrapy.Field()
    evm_version = scrapy.Field()
    contract_name = scrapy.Field()
    library = scrapy.Field()
    proxy = scrapy.Field()
    optimization = scrapy.Field()
    runs = scrapy.Field()
    source_code = scrapy.Field()
    constructor_arguments = scrapy.Field()
    license = scrapy.Field()
