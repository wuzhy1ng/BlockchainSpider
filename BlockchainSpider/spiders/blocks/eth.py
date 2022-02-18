import json
import logging

import scrapy
from scrapy.utils.misc import load_object

from BlockchainSpider import settings
from BlockchainSpider.items import BlockTxItem, BlockMetaItem
from BlockchainSpider.utils.url import QueryURLBuilder


class BlocksETHSpider(scrapy.Spider):
    name = 'blocks.eth'
    net = 'eth'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # output dir and block range
        self.out_dir = kwargs.get('out', './data')
        self.start_block = kwargs.get('start_blk', '0')
        self.end_block = kwargs.get('end_blk', None)

        # tx types
        self.txs_types = kwargs.get('types', 'external').split(',')
        self.txs_req_getter = {
            'external': self.get_external_block_request,
            'internal': self.get_internal_block_request,
            'erc20': self.get_erc20_block_request,
            'erc721': self.get_erc721_block_request,
        }
        for txs_type in self.txs_types:
            assert txs_type in set(self.txs_req_getter.keys())

        # load token contract addresses
        self.contracts = kwargs.get('contracts', None)
        if 'erc20' in self.txs_types or 'erc721' in self.txs_types:
            assert self.contracts is not None
            self.contracts = self.contracts.split(',')

        # load apikey bucket class
        apikey_bucket = getattr(settings, 'APIKEYS_BUCKET', None)
        assert apikey_bucket is not None
        self.apikey_bucket = load_object(apikey_bucket)(net='eth', kps=5)

        # api url
        self.base_api_url = 'https://api-cn.etherscan.com/api'

    def start_requests(self):
        if self.end_block is None:
            url = self.base_api_url + '?module=proxy&action=eth_blockNumber&apikey=%s' % self.apikey_bucket.get()
            yield scrapy.Request(
                url=url,
                method='GET',
                callback=self.parse_block_number,
            )
            return

        yield from self.gen_requests(self.start_block, self.end_block)

    def parse_block_number(self, response, **kwargs):
        data = json.loads(response.text)
        self.end_block = int(data['result'], 16)
        yield from self.gen_requests(self.start_block, self.end_block)

    def parse_external_block(self, response, **kwargs):
        data = json.loads(response.text)
        data = data.get('result')
        if not isinstance(data, dict):
            self.log(
                message="Error on parsing external block: %s" % str(data),
                level=logging.ERROR
            )
            return

        txs = data.get('transactions')
        if isinstance(txs, list):
            for tx in txs:
                yield BlockTxItem(info=tx, tx_type='external')

        if txs is not None:
            del data['transactions']
        yield BlockMetaItem(info=data)

    def parse_internal_block(self, response, **kwargs):
        data = json.loads(response.text)
        data = data.get('result')
        if not isinstance(data, list):
            self.log(
                message="Error on parsing external block: %s" % str(data),
                level=logging.ERROR
            )
            return

        for tx in data:
            yield BlockTxItem(info=tx, tx_type='internal')

    def parse_erc20_block(self, response, **kwargs):
        data = json.loads(response.text)
        data = data.get('result')
        if not isinstance(data, list):
            self.log(
                message="Error on parsing external block: %s" % str(data),
                level=logging.ERROR
            )
            return

        for tx in data:
            yield BlockTxItem(info=tx, tx_type='erc20')

    def parse_erc721_block(self, response, **kwargs):
        data = json.loads(response.text)
        data = data.get('result')
        if not isinstance(data, list):
            self.log(
                message="Error on parsing external block: %s" % str(data),
                level=logging.ERROR
            )
            return

        for tx in data:
            yield BlockTxItem(info=tx, tx_type='erc721')

    def gen_requests(self, start_blk, end_blk):
        start_blk = int(start_blk)
        end_blk = int(end_blk)
        for i in range(start_blk, end_blk + 1):
            for txs_type in self.txs_types:
                if txs_type not in {'erc20', 'erc721'}:
                    yield self.txs_req_getter[txs_type](block=i)
                    continue
                for contract_address in self.contracts:
                    yield self.txs_req_getter[txs_type](block=i, contract_address=contract_address)

    def get_external_block_request(self, block: int) -> scrapy.Request:
        url = QueryURLBuilder(self.base_api_url).get({
            'module': 'proxy',
            'action': 'eth_getBlockByNumber',
            'tag': hex(block),
            'boolean': True,
            'apikey': self.apikey_bucket.get()
        })
        return scrapy.Request(
            url=url,
            method='GET',
            callback=self.parse_external_block,
        )

    def get_internal_block_request(self, block: int) -> scrapy.Request:
        url = QueryURLBuilder(self.base_api_url).get({
            'module': 'account',
            'action': 'txlistinternal',
            'startblock': block,
            'endblock': block,
            'apikey': self.apikey_bucket.get()
        })
        return scrapy.Request(
            url=url,
            method='GET',
            callback=self.parse_internal_block,
        )

    def get_erc20_block_request(self, block: int, **kwargs) -> scrapy.Request:
        url = QueryURLBuilder(self.base_api_url).get({
            'module': 'account',
            'action': 'tokentx',
            'contractaddress': kwargs.get('contract_address'),
            'startblock': block,
            'endblock': block,
            'apikey': self.apikey_bucket.get()
        })
        return scrapy.Request(
            url=url,
            method='GET',
            callback=self.parse_erc20_block,
        )

    def get_erc721_block_request(self, block: int, **kwargs) -> scrapy.Request:
        url = QueryURLBuilder(self.base_api_url).get({
            'module': 'account',
            'action': 'tokennfttx',
            'contractaddress': kwargs.get('contract_address'),
            'startblock': block,
            'endblock': block,
            'apikey': self.apikey_bucket.get()
        })
        return scrapy.Request(
            url=url,
            method='GET',
            callback=self.parse_erc721_block,
        )
