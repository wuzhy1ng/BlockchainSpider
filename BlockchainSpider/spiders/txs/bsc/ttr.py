from BlockchainSpider.spiders.txs.eth.ttr import TxsETHTTRSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsBSCTTRSpider(TxsETHTTRSpider):
    name = 'txs.bsc.ttr'
    TXS_API_URL = 'https://api.bscscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('bsc')
