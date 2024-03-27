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


class SignItem(scrapy.Item):
    text = scrapy.Field()  # str
    sign = scrapy.Field()  # str
    type = scrapy.Field()  # str, 'Function' or 'Event'


class ABIItem(scrapy.Item):
    contract_address = scrapy.Field()  # str
    abi = scrapy.Field()  # dict
