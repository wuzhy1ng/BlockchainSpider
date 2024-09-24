import scrapy
import json
from BlockchainSpider import settings
from BlockchainSpider.items.signature import SignatureItem, TransactionsItem
from BlockchainSpider.utils.bucket import AsyncItemBucket


class SolScanSpider(scrapy.Spider):
    name = 'solana.signature'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.signature.SignaturePipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }



    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.addresses = kwargs.get('addresses', '').split(',')
        self.out_dir = kwargs.get('out', './data')

        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
        )

    def start_requests(self):
        for addr in self.addresses:
            yield scrapy.Request(
                url=self.provider_bucket.items[0],
                method='POST',
                headers={'Content-Type': 'application/json'},
                body=json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignaturesForAddress",
                    "params": [
                        addr,
                        {
                            "limit": 1000
                        }
                    ]
                }),
                callback=self.parse_signature,
                cb_kwargs={'address': addr},
            )

    def parse_signature(self, response, **kwargs):
        result = json.loads(response.text)
        address = kwargs.get('address')
        for i in range(len(result['result'])):
            yield SignatureItem(
                address=address,
                signature=result['result'][i]['signature'],
            )

