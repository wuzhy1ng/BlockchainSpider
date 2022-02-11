import json
import os
from urllib.parse import urlparse

import scrapy

from BlockchainSpider.items import LabelItem


class LabelsTokenSnifferSpider(scrapy.Spider):
    name = 'labels.tokensniffer'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.domain_url = 'https://tokensniffer.com'

        self.out_dir = kwargs.get('out', './data')

    def start_requests(self):
        request_paths = [
            '/tokens/top',
            '/tokens/trending',
            '/tokens/new',
            '/tokens/scam'
        ]
        for path in request_paths:
            yield scrapy.Request(
                url=self.domain_url + path,
                method='GET'
            )

    def parse(self, response, **kwargs):
        data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        data = json.loads(data)
        data = data['props']['pageProps']
        tokens = data.get('tokens')
        if tokens is None:
            return

        if isinstance(tokens, dict):
            for token_list in tokens.values():
                for token in token_list:
                    yield LabelItem(
                        net=token.get('network'),
                        label=urlparse(response.url).path.replace('/tokens/', ''),
                        info=token
                    )
        else:
            for token in tokens:
                yield LabelItem(
                    net=token.get('network'),
                    label=urlparse(response.url).path.replace('/tokens/', ''),
                    info=token
                )
