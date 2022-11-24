from urllib.parse import urlparse

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import LabelReportItem
from BlockchainSpider.spiders.labels.web import LabelsWebSpider


class LabelsTorSpider(LabelsWebSpider):
    name = 'labels.tor'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'BlockchainSpider.middlewares.TorMiddleware': 900,
            **getattr(settings, 'DOWNLOADER_MIDDLEWARES', dict())
        },
        **LabelsWebSpider.custom_settings,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tor_host = kwargs.get('tor_host', '127.0.0.1')
        self.tor_port = kwargs.get('tor_port', 9150)

    def parse(self, response, **kwargs):
        for item in super(LabelsTorSpider, self).parse(response, **kwargs):
            if isinstance(item, scrapy.Request) and \
                    not self._is_onion_url(item.url):
                continue
            if isinstance(item, LabelReportItem):
                item['labels'].insert(0, 'dark web')
                item['reporter'] = 'TOR'
            yield item

    def _is_onion_url(self, url: str):
        netloc = urlparse(url).netloc
        return netloc.endswith('onion')
