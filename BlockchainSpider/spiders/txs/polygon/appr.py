from BlockchainSpider.spiders.txs.eth.appr import TxsETHAPPRSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsPolygonAPPRSpider(TxsETHAPPRSpider):
    name = 'txs.polygon.appr'
    TXS_API_URL = 'https://api.polygonscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('polygon')
