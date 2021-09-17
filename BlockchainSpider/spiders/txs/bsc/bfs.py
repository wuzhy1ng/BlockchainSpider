from BlockchainSpider.spiders.txs.eth.bfs import TxsETHBFSSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsBSCBFSSpider(TxsETHBFSSpider):
    name = 'txs.bsc.bfs'
    TXS_API_URL = 'https://api.bscscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('bsc')
