from BlockchainSpider.spiders.txs.eth.appr import TxsETHAPPRSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsPolyganAPPRSpider(TxsETHAPPRSpider):
    name = 'txs.polygan.haircut'
    TXS_API_URL = 'https://api.polyganscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('polygan')
