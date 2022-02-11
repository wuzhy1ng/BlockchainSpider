from BlockchainSpider.spiders.txs.eth.bfs import TxsETHBFSSpider


class TxsHecoBFSSpider(TxsETHBFSSpider):
    name = 'txs.heco.bfs'
    TXS_API_URL = 'https://api.hecoinfo.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = type(self.apikey_bucket)(net='heco', kps=5)

