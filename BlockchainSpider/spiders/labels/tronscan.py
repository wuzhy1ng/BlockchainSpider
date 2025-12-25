import scrapy
from BlockchainSpider import settings
from BlockchainSpider.items import LabelReportItem


class TronScanSpider(scrapy.Spider):
    name = 'labels.tronscan'
    custom_settings = {
        'ITEM_PIPELINES': {  # May be need proxies here
            'BlockchainSpider.pipelines.LabelReportPipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        },
        'DOWNLOADER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.SeleniumMiddleware': 900,
            **getattr(settings, 'DOWNLOADER_MIDDLEWARES', dict())
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.addresses = kwargs.get('addresses', '').split(',')
        self.out_dir = kwargs.get('out', './data')

    def start_requests(self):
        # yield request of label
        for addr in self.addresses:
            url = 'https://tronscan.org/#/address/'
            yield scrapy.Request(
                url=url + addr,
                method='GET',
                callback=self.parse_label,
                cb_kwargs={'address': addr, 'url': url},
            )

    def parse_label(self, response, **kwargs):
        result = response.xpath('//*[@id="address-tag-id"]//div[contains(@class, "tag-item")]/text()')
        result = result.getall()
        if len(result) == 0:
            return
        yield LabelReportItem(
            labels=[result[0]],
            urls=[response.url],
            addresses=[dict(
                net='tron',
                address=kwargs['address'],
            )],
            transactions=None,
            reporter='tronscan.org',
        )
