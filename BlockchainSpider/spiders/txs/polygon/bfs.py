from BlockchainSpider.spiders.txs.eth.bfs import TxsETHBFSSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class TxsPolygonBFSSpider(TxsETHBFSSpider):
    name = 'txs.polygon.bfs'
    TXS_API_URL = 'https://api.polygonscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = JsonAPIKeyBucket('polygon')
