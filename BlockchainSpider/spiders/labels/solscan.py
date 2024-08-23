import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import LabelReportItem, LabelAddressItem


class SolScanSpider(scrapy.Spider):
    name = 'labels.solscan'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 666,
        },
        'ITEM_PIPELINES': {  # May be need proxies here
            'BlockchainSpider.pipelines.LabelReportPipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.addresses = kwargs.get('addresses', '').split(',')
        self.out_dir = kwargs.get('out', './data')

    def start_requests(self):
        # TODO: yield request of label
        for addr in self.addresses:
            url = 'https://api-v2.solscan.io/v2/account?address='
            yield scrapy.Request(
                url=url + addr,
                method='GET',
                headers={'Origin': 'https://solscan.io'},
                callback=self.parse_label,
                cb_kwargs={'address': addr},
            )

    def parse_label(self, response, **kwargs):
        # TODO: parse label data
        # TODO: (optional) generate IDL request
        address = kwargs.get('address')
        item = LabelReportItem(
            labels=...,
            ...
        )
        url = 'https://api-v2.solscan.io/v2/account/anchor_idl?address='
        yield scrapy.Request(
            url=url + address,
            method='GET',
            headers={'Origin': 'https://solscan.io'},
            callback=self.parse_idl,
            cb_kwargs={'item': item},
        )

    def parse_idl(self, response, **kwargs):
        # TODO: parse IDL data and attach to description
        item = kwargs.get('item')
        item['description'] = idl
        yield item
