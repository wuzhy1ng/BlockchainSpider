from BlockchainSpider.spiders.txs.eth.bfs import TxsETHBFSSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsHecoBFSSpider(TxsETHBFSSpider):
    name = 'txs.heco.bfs'
    TXS_API_URL = 'https://api.hecoinfo.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('heco')
