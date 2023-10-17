import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import SignItem


class Sign4btyesSpider(scrapy.Spider):
    name = 'signs.web3'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.SignsPipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = kwargs.get('out', './data')
        self.url4func_sign = 'https://www.4byte.directory/api/v1/signatures/?'
        self.url4event_sign = 'https://www.4byte.directory/api/v1/event-signatures/?'

    def start_requests(self):
        yield scrapy.Request(
            url='https://www.4byte.directory/api/v1/signatures/?format=json',
            method='GET',
            headers={'Content-Type': 'application/json'},
        )
        yield scrapy.Request(
            url='https://www.4byte.directory/api/v1/event-signatures/?format=json',
            method='GET',
            headers={'Content-Type': 'application/json'},
        )

    def parse(self, response: scrapy.http.TextResponse, **kwargs):
        # parse data
        data = response.json()

        # generate requests
        if data.get('next'):
            yield scrapy.Request(
                url=data['next'],
                method='GET',
                headers={'Content-Type': 'application/json'},
            )

        # generate items
        if not data.get('results'):
            return
        sign_type = 'Event' if response.url.startswith(
            'https://www.4byte.directory/api/v1/event-signatures') else 'Function'
        for item in data['results']:
            yield SignItem(
                text=item['text_signature'],
                sign=item['hex_signature'],
                type=sign_type,
            )
