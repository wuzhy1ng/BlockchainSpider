import scrapy

from BlockchainSpider.settings import SCAN_APIKEYS
from BlockchainSpider.utils.apikey import StaticAPIKeyBucket
from BlockchainSpider.utils.url import URLBuilder


class TxsETHSpider(scrapy.Spider):
    # Target original url configure
    TXS_ETH_ORIGINAL_URL = 'http://api-cn.etherscan.com/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # input source nodes
        self.source = kwargs.get('source', None)
        self.filename = kwargs.get('file', None)
        assert self.source or self.filename, "`source` or `file` arguments are needed"

        # output dir
        self.out_dir = kwargs.get('out', './data')

        # apikey bucket
        self.apikey_bucket = StaticAPIKeyBucket(SCAN_APIKEYS)

        # tx types
        self.txs_types = kwargs.get('types', 'external').split(',')
        self.txs_req_getter = {
            'external': self.parse_external_txs,
            'internal': self.parse_internal_txs,
            'erc20': self.parse_erc20_txs,
            'erc721': self.parse_erc721_txs,
        }
        for txs_type in self.txs_types:
            assert txs_type in set(self.txs_req_getter.keys())

    def get_max_blk(self, txs: list):
        rlt = 0
        for tx in txs:
            blk_num = int(tx.get('blockNumber', 0))
            if blk_num > rlt:
                rlt = blk_num
        return rlt

    def get_external_txs_request(self, address: str, **kwargs):
        return scrapy.Request(
            url=URLBuilder(TxsETHSpider.TXS_ETH_ORIGINAL_URL).get({
                'module': 'account',
                'action': 'txlist',
                'address': address,
                'sort': 'asc',
                'startblock': kwargs.get('startblock', 0),
                'apikey': self.apikey_bucket.get()
            }),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'source': kwargs['source'],
                'address': address,
                **kwargs
            },
            callback=self.parse_external_txs,
        )

    def get_internal_txs_request(self, address: str, **kwargs):
        return scrapy.Request(
            url=URLBuilder(TxsETHSpider.TXS_ETH_ORIGINAL_URL).get({
                'module': 'account',
                'action': 'txlistinternal',
                'address': address,
                'sort': 'asc',
                'startblock': kwargs.get('startblock', 0),
                'apikey': self.apikey_bucket.get()
            }),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'source': kwargs['source'],
                'address': address,
                **kwargs
            },
            callback=self.parse_internal_txs,
        )

    def get_erc20_txs_request(self, address: str, **kwargs):
        return scrapy.Request(
            url=URLBuilder(TxsETHSpider.TXS_ETH_ORIGINAL_URL).get({
                'module': 'account',
                'action': 'tokentx',
                'address': address,
                'sort': 'asc',
                'startblock': kwargs.get('startblock', 0),
                'apikey': self.apikey_bucket.get()
            }),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'source': kwargs['source'],
                'address': address,
                **kwargs
            },
            callback=self.parse_erc20_txs,
        )

    def get_erc721_txs_request(self, address: str, **kwargs):
        return scrapy.Request(
            url=URLBuilder(TxsETHSpider.TXS_ETH_ORIGINAL_URL).get({
                'module': 'account',
                'action': 'tokennfttx',
                'address': address,
                'sort': 'asc',
                'startblock': kwargs.get('startblock', 0),
                'apikey': self.apikey_bucket.get()
            }),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'source': kwargs['source'],
                'address': address,
                **kwargs
            },
            callback=self.parse_erc721_txs,
        )

    def gen_txs_requests(self, address: str, **kwargs):
        for txs_type in self.txs_types:
            self.txs_req_getter[txs_type](address, **kwargs)

    def parse_external_txs(self, response, **kwargs):
        raise NotImplementedError()

    def parse_internal_txs(self, response, **kwargs):
        raise NotImplementedError()

    def parse_erc20_txs(self, response, **kwargs):
        raise NotImplementedError()

    def parse_erc721_txs(self, response, **kwargs):
        raise NotImplementedError()
