import scrapy
import json
from BlockchainSpider import settings
from BlockchainSpider.items import LabelReportItem


class SolScanSpider(scrapy.Spider):
    name = 'labels.solscan'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.HTTPProxyMiddleware': 749,
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
        # yield request of label
        for addr in self.addresses:
            url = 'https://api-v2.solscan.io/v2/account?address='
            yield scrapy.Request(
                url=url + addr,
                method='GET',
                headers={'Origin': 'https://solscan.io'},
                callback=self.parse_label,
                cb_kwargs={'address': addr, 'url': url},
            )

    def parse_label(self, response, **kwargs):
        # parse label data
        # (optional) generate IDL request
        result = json.loads(response.text)
        address = kwargs.get('address')
        if not result['data'].get('notifications'):
            return
        item = LabelReportItem(
            labels=result['data']['notifications']['label'],
            urls=[response.url],
            addresses=[dict(
                net='solana',
                address=address,
            )],
            transactions=None,
            reporter='solscan.io',
        )
        if not result['data']['executable']:
            yield item
            return
        url = 'https://api-v2.solscan.io/v2/account/anchor_idl?address='
        yield scrapy.Request(
            url=url + address,
            method='GET',
            headers={'Origin': 'https://solscan.io'},
            callback=self.parse_idl,
            cb_kwargs={'item': item},
        )

    def parse_idl(self, response, **kwargs):
        # parse IDL data and attach to description
        result = json.loads(response.text)
        item = kwargs.get('item')
        item['description'] = {'idl': result['data']}
        yield item
