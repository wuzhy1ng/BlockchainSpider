import scrapy
import json
from BlockchainSpider import settings
from BlockchainSpider.items.signature import TransactionsItem
from BlockchainSpider.utils.bucket import AsyncItemBucket
import pandas as pd


class SolScanSpider(scrapy.Spider):
    name = 'solana.transactions'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.signature.TransactionsPipeline': 399,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = kwargs.get('out', './data')

        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
        )

    def start_requests(self):
        df = pd.read_csv('D:\Blockchainspider\BlockchainSpider\data\signature.csv')#先爬取自己想要账户的交易签名
        signatures = df['signature']
        for signature in signatures:
            print(signature)
            yield scrapy.Request(
                url=self.provider_bucket.items[0],
                method='POST',
                headers={'Content-Type': 'application/json'},
                body=json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [
                        signature,
                        {
                            "encoding": "jsonParsed",
                            "maxSupportedTransactionVersion": 1
                        }
                    ]
                }),
                callback=self.parse_Transaction,
                cb_kwargs={'signature': signature}
            )

    def parse_Transaction(self, response, **kwargs):
        result = json.loads(response.text)
        signature = kwargs.get('signature')
        if result.get('result'):
            yield TransactionsItem(
                signature=signature,
                data=result['result']
            )
