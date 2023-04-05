import json

import scrapy
from scrapy.utils.misc import load_object

from BlockchainSpider import settings
from BlockchainSpider.utils.url import QueryURLBuilder


class TxsETHSpider(scrapy.Spider):
    # Target original url configure
    TXS_API_URL = 'https://api-cn.etherscan.com/api'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.SubgraphTxsPipeline': 298,
            'BlockchainSpider.pipelines.ImportancePipeline': 299,
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.info = dict()

        # input source nodes
        self.source = kwargs.get('source', None)
        self.filename = kwargs.get('file', None)
        assert self.source or self.filename, "`source` or `file` arguments are needed"
        self.info['source'] = self.source

        # output dir
        self.out_dir = kwargs.get('out', './data')
        self.info['out_dir'] = self.out_dir

        # output fields
        self.out_fields = kwargs.get(
            'fields',
            'id,hash,from,to,value,timeStamp,blockNumber,symbol,contractAddress'
        ).split(',')
        self.info['out_fields'] = self.out_fields

        # load apikey bucket class
        apikey_bucket = getattr(settings, 'APIKEYS_BUCKET', None)
        assert apikey_bucket is not None
        self.apikey_bucket = load_object(apikey_bucket)(net='eth', kps=5)

        # tx types
        self.txs_types = kwargs.get('types', 'external').split(',')
        self.txs_req_getter = {
            'external': self.get_external_txs_request,
            'internal': self.get_internal_txs_request,
            'erc20': self.get_erc20_txs_request,
            'erc721': self.get_erc721_txs_request,
        }
        for txs_type in self.txs_types:
            assert txs_type in set(self.txs_req_getter.keys())
        self.info['txs_types'] = self.txs_types

        # tx block range
        self.start_blk = int(kwargs.get('start_blk', 0))
        self.end_blk = int(kwargs.get('end_blk', 99999999))
        self.info['start_blk'] = self.start_blk
        self.info['end_blk'] = self.end_blk

        # auto turn page, for the etherscan api offer 10k txs per request
        self.auto_page = kwargs.get('auto_page', False)
        self.auto_page = True if self.auto_page == 'True' else False
        self.info['auto_page'] = self.auto_page

        # restrict token symbol
        self.symbols = kwargs.get('symbols', None)
        self.symbols = set(self.symbols.split(',')) if self.symbols else self.symbols
        self.info['symbols'] = self.symbols

        self.max_retry = 2

    def load_task_info_from_json(self, fn: str):
        infos = list()
        with open(fn, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert isinstance(data, list)
            for item in data:
                item['out_dir'] = item.get('out', './data')
                item['out_fields'] = item.get(
                    'fields',
                    'id,hash,from,to,value,timeStamp,blockNumber,symbol,contractAddress'
                ).split(',')
                item['txs_types'] = item.get('types', 'external').split(',')
                item['start_blk'] = int(item.get('start_blk', 0))
                item['end_blk'] = int(item.get('end_blk', 99999999))
                item['auto_page'] = item.get('auto_page', False)
                item['symbols'] = item.get('symbols').split(',') if item.get('symbols') else None

                infos.append(item)
        return infos

    def get_max_blk(self, txs: list):
        rlt = 0
        for tx in txs:
            blk_num = int(tx.get('blockNumber', 0))
            if blk_num > rlt:
                rlt = blk_num
        return rlt

    def get_external_txs_request(self, address: str, **kwargs):
        query_params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'sort': 'asc',
            'startblock': max(kwargs.get('startblock', self.start_blk), self.start_blk),
            'endblock': min(kwargs.get('endblock', self.end_blk), self.end_blk),
            'apikey': self.apikey_bucket.get()
        }
        if kwargs.get('retry') is not None:
            query_params['retry'] = kwargs['retry']
        return scrapy.Request(
            url=QueryURLBuilder(self.TXS_API_URL).get(query_params),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'address': address,
                **kwargs
            },
            callback=self.parse_external_txs,
        )

    def get_internal_txs_request(self, address: str, **kwargs):
        query_params = {
            'module': 'account',
            'action': 'txlistinternal',
            'address': address,
            'sort': 'asc',
            'startblock': max(kwargs.get('startblock', self.start_blk), self.start_blk),
            'endblock': min(kwargs.get('endblock', self.end_blk), self.end_blk),
            'apikey': self.apikey_bucket.get()
        }
        if kwargs.get('retry') is not None:
            query_params['retry'] = kwargs['retry']
        return scrapy.Request(
            url=QueryURLBuilder(self.TXS_API_URL).get(query_params),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'address': address,
                **kwargs
            },
            callback=self.parse_internal_txs,
        )

    def get_erc20_txs_request(self, address: str, **kwargs):
        query_params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'sort': 'asc',
            'startblock': max(kwargs.get('startblock', self.start_blk), self.start_blk),
            'endblock': min(kwargs.get('endblock', self.end_blk), self.end_blk),
            'apikey': self.apikey_bucket.get()
        }
        if kwargs.get('retry') is not None:
            query_params['retry'] = kwargs['retry']
        return scrapy.Request(
            url=QueryURLBuilder(self.TXS_API_URL).get(query_params),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'address': address,
                **kwargs
            },
            callback=self.parse_erc20_txs,
        )

    def get_erc721_txs_request(self, address: str, **kwargs):
        query_params = {
            'module': 'account',
            'action': 'tokennfttx',
            'address': address,
            'sort': 'asc',
            'startblock': max(kwargs.get('startblock', self.start_blk), self.start_blk),
            'endblock': min(kwargs.get('endblock', self.end_blk), self.end_blk),
            'apikey': self.apikey_bucket.get()
        }
        if kwargs.get('retry') is not None:
            query_params['retry'] = kwargs['retry']
        return scrapy.Request(
            url=QueryURLBuilder(self.TXS_API_URL).get(query_params),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'address': address,
                **kwargs
            },
            callback=self.parse_erc721_txs,
        )

    def gen_txs_requests(self, address: str, **kwargs):
        for txs_type in self.txs_types:
            yield self.txs_req_getter[txs_type](address, **kwargs)

    def load_txs_from_response(self, response):
        data = json.loads(response.text)
        txs = None
        if isinstance(data.get('result'), list):
            txs = list()
            for tx in data['result']:
                if tx['from'] == '' or tx['to'] == '':
                    continue
                tx['value'] = int(tx.get('value', 1))
                tx['timeStamp'] = int(tx['timeStamp'])

                if self.symbols and tx.get('tokenSymbol', 'native') not in self.symbols:
                    continue
                tx['symbol'] = '{}_{}'.format(tx.get('tokenSymbol', 'native'), tx.get('contractAddress'))
                if tx.get('tokenID') is not None:
                    tx['symbol'] = '{}_{}'.format(tx['symbol'], tx['tokenID'])

                tx['id'] = '{}_{}_{}'.format(tx.get('hash'), tx.get('traceId'), tx['symbol'])
                txs.append(tx)
        return txs

    def parse_external_txs(self, response, **kwargs):
        raise NotImplementedError()

    def parse_internal_txs(self, response, **kwargs):
        raise NotImplementedError()

    def parse_erc20_txs(self, response, **kwargs):
        raise NotImplementedError()

    def parse_erc721_txs(self, response, **kwargs):
        raise NotImplementedError()
