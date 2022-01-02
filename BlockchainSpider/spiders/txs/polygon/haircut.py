from BlockchainSpider.spiders.txs.eth.haircut import TxsETHHaircutSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsPolygonHaircutSpider(TxsETHHaircutSpider):
    name = 'txs.polygon.haircut'
    TXS_API_URL = 'https://api.polygonscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('polygon')
