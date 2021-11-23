from BlockchainSpider.spiders.txs.eth.appr import TxsETHAPPRSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsHecoAPPRSpider(TxsETHAPPRSpider):
    name = 'txs.heco.appr'
    TXS_API_URL = 'https://api.hecoinfo.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('heco')
