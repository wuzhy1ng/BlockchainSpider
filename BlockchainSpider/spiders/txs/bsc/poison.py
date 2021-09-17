from BlockchainSpider.spiders.txs.eth.poison import TxsETHPoisonSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsBSCPoisonSpider(TxsETHPoisonSpider):
    name = 'txs.bsc.poison'
    TXS_API_URL = 'https://api.bscscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('bsc')
