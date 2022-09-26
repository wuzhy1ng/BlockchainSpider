from urllib.parse import urlparse

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import LabelItem
from BlockchainSpider.spiders.labels.web import LabelsWebSpider


class LabelsTorSpider(LabelsWebSpider):
    name = 'labels.tor'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.TorMiddleware': 900,
            **getattr(settings, 'DOWNLOADER_MIDDLEWARES', dict())
        },
        'TOR_HOST': '127.0.0.1',
        'TOR_PORT': 9150,
        **LabelsWebSpider.custom_settings,
    }

    def parse(self, response, **kwargs):
        for item in super(LabelsTorSpider, self).parse(response, **kwargs):
            if isinstance(item, scrapy.Request) and \
                    not self._is_onion_url(item.url):
                continue
            if isinstance(item, LabelItem):
                item['label'] = 'dark web'
            yield item

    def _is_onion_url(self, url: str):
        netloc = urlparse(url).netloc
        return netloc.endswith('onion')
