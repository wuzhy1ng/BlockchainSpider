from BlockchainSpider.spiders.txs.eth.appr import TxsETHAPPRSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsBSCAPPRSpider(TxsETHAPPRSpider):
    name = 'txs.bsc.haircut'
    TXS_API_URL = 'https://api.bscscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('bsc')
