import scrapy
import json
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
                cb_kwargs={'address': addr,'url':url},
            )

    def parse_label(self, response, **kwargs):
        # TODO: parse label data
        # TODO: (optional) generate IDL request
        result = json.loads(response.text)
        address = kwargs.get('address')
        url = kwargs.get('address')

        item = LabelReportItem(
            labels=result['data']['notifications']['label'],
            urls=url+address,
            addresses=address,
            transactions=None,
            reporter=None,
        )
        if result['data']['executable']:
            url = 'https://api-v2.solscan.io/v2/account/anchor_idl?address='
            yield scrapy.Request(
                url=url + address,
                method='GET',
                headers={'Origin': 'https://solscan.io'},
                callback=self.parse_idl,
                cb_kwargs={'item': item},
            )
        else:
            yield LabelReportItem(
                labels=result['data']['notifications']['label'],
                urls=url + address,
                addresses=address,
                transactions=None,
                description=None,
                reporter=None,
            )

    def parse_idl(self, response, **kwargs):
        # TODO: parse IDL data and attach to description
        result = json.loads(response.text)
        item = kwargs.get('item')
        item['description'] = result['data']
        yield item
