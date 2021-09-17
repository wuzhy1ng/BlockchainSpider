from BlockchainSpider.spiders.txs.eth.bfs import TxsETHBFSSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsPolyganBFSSpider(TxsETHBFSSpider):
    name = 'txs.polygan.bfs'
    TXS_API_URL = 'https://api.polyganscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('polygan')
