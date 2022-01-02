from BlockchainSpider.spiders.txs.eth.poison import TxsETHPoisonSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsPolygonPoisonSpider(TxsETHPoisonSpider):
    name = 'txs.polygon.poison'
    TXS_API_URL = 'https://api.polygonscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('polygon')
