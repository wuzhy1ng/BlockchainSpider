import scrapy
from scrapy.http import Response

from BlockchainSpider import settings
from BlockchainSpider.items import LabelReportItem


class BlockscanSpider(scrapy.Spider):
    name = 'labels.blockscan'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.LabelReportPipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.addresses = kwargs.get('addresses', '').split(',')
        self.domain = kwargs.get('domain', 'etherscan.io')
        self.out_dir = kwargs.get('out', './data')

    def start_requests(self):
        # yield request of label
        for addr in self.addresses:
            url = 'https://%s/address/%s' % (self.domain, addr)
            yield scrapy.Request(
                url=url,
                method='GET',
                cb_kwargs={'address': addr},
                callback=self.parse,
                # errback=self.error_back
            )

    def parse(self, response: Response, **kwargs):
        labels = response.xpath('//div[@id="ContentPlaceHolder1_divLabels"]//span/text()').getall()
        labels.extend(response.xpath('//span[@class="hash-tag text-truncate lh-sm my-n1"]/text()').getall())
        if len(labels) == 0:
            return
        yield LabelReportItem(
            labels=labels,
            urls=[response.url],
            addresses=[{
                'address': kwargs['address'],
                'net': 'eth',
            }],
            transactions=[],
            description='',
            reporter='etherscan.io',
        )

    def error_back(self, failure):
        self.logger.error(repr(failure))
