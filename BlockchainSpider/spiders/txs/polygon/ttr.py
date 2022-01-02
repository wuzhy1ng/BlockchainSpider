from BlockchainSpider.spiders.txs.eth.ttr import TxsETHTTRSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsPolygonTTRSpider(TxsETHTTRSpider):
    name = 'txs.polygon.ttr'
    TXS_API_URL = 'https://api.polygonscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('polygon')
