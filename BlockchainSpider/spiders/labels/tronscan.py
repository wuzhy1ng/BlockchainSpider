import scrapy
import json
from BlockchainSpider import settings
from BlockchainSpider.items import LabelReportItem


class TronScanSpider(scrapy.Spider):
    name = 'labels.tronscan'
    custom_settings = {
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
            url = 'https://apilist.tronscanapi.com/api/accountv2?address='
            yield scrapy.Request(
                url=url + addr,
                method='GET',
                callback=self.parse_label,
                cb_kwargs={'address': addr, 'url': url},
            )

    def parse_label(self, response, **kwargs):
        result = json.loads(response.text)
        address = kwargs.get('address')
        tag = result.get('publicTag')
        if tag is None:
            return
        yield LabelReportItem(
            labels=[tag],
            urls=[response.url],
            addresses=[dict(
                net='tron',
                address=address,
            )],
            transactions=None,
            reporter='tronscan.org',
        )
