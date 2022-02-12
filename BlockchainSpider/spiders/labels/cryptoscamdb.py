import json
import logging

import scrapy

from BlockchainSpider.items import LabelItem


class LabelsCryptoScamDBSpider(scrapy.Spider):
    name = 'labels.cryptoscamdb'

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
                yield LabelItem(
                    net='',
                    label=item.get('type', ''),
                    info=item,
                )
