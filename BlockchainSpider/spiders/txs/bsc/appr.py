from BlockchainSpider.spiders.txs.eth.appr import TxsETHAPPRSpider


class TxsBSCAPPRSpider(TxsETHAPPRSpider):
    name = 'txs.bsc.appr'
    TXS_API_URL = 'https://api.bscscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = type(self.apikey_bucket)(net='bsc', kps=5)
