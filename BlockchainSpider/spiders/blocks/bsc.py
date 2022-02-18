from BlockchainSpider.spiders.blocks.eth import BlocksETHSpider


class BlocksBSCSpider(BlocksETHSpider):
    name = 'blocks.bsc'
    net = 'bsc'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # load apikey bucket class
        self.apikey_bucket = type(self.apikey_bucket)(net='bsc', kps=5)

        # api url
        self.base_api_url = 'https://api.bscscan.com/api'
