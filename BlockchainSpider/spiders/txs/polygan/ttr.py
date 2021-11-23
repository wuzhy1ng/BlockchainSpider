from BlockchainSpider.spiders.txs.eth.ttr import TxsETHTTRSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsPolyganTTRSpider(TxsETHTTRSpider):
    name = 'txs.polygan.ttr'
    TXS_API_URL = 'https://api.polyganscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('bsc')
