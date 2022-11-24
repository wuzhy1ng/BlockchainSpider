import json
import logging

import scrapy
from web3 import Web3

from BlockchainSpider import settings
from BlockchainSpider.items import LabelReportItem, LabelAddressItem


class LabelsCryptoScamDBSpider(scrapy.Spider):
    name = 'labels.cryptoscamdb'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.LabelsPipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.url_api_addressses = 'https://api.cryptoscamdb.org/v1/addresses'

        self.out_dir = kwargs.get('out', './data')

    def start_requests(self):
        yield scrapy.Request(
            url=self.url_api_addressses,
            method='GET',
        )

    def parse(self, response, **kwargs):
        data = json.loads(response.text)
        if not data.get('success', True):
            self.log(
                message="Failed to crawl api of %s" % self.url_api_addressses,
                level=logging.ERROR
            )
            return

        for items in data['result'].values():
            for item in items:
                labels = list()
                if item.get('category'): labels.append(item.get('category'))
                if item.get('subcategory'): labels.append(item.get('subcategory'))
                if item.get('type'): labels.append(item.get('type'))
                yield LabelReportItem(
                    labels=labels,
                    urls=[item['url']] if item.get('url') else list(),
                    addresses=[{**LabelAddressItem(
                        net='ETH' if Web3.isAddress(item.get('address')) else '',
                        address=item.get('address').lower(),
                    )}],
                    transactions=list(),
                    description=item,
                    reporter=item.get('reporter'),
                )
