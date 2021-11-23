from BlockchainSpider.spiders.txs.eth.poison import TxsETHPoisonSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsPolyganPoisonSpider(TxsETHPoisonSpider):
    name = 'txs.polygan.poison'
    TXS_API_URL = 'https://api.polyganscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('polygan')
