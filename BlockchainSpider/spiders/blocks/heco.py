from BlockchainSpider.spiders.blocks.eth import BlocksETHSpider


class BlocksPolygonSpider(BlocksETHSpider):
    name = 'blocks.heco'
    net = 'heco'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # load apikey bucket class
        self.apikey_bucket = type(self.apikey_bucket)(net='heco', kps=5)

        # api url
        self.base_api_url = 'https://api.hecoinfo.com/api'
