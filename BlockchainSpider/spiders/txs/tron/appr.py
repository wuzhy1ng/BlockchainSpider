import json

import scrapy

from BlockchainSpider.spiders.txs.eth.appr import TxsETHAPPRSpider
from BlockchainSpider.utils.url import QueryURLBuilder


class TxsTRONAPPRSpider(TxsETHAPPRSpider):
    name = 'txs.tron.appr'
    TXS_API_URL = 'https://apilist.tronscan.org/api'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apikey_bucket = type(self.apikey_bucket)(net='eth', kps=5)

    def get_external_txs_request(self, address: str, **kwargs):
        query_params = {
            'address': address,
            'sort': '-timestamp',
            'limit': 10000,
            # 'start_timestamp': max(kwargs.get('startblock', self.start_blk), self.start_blk),
            # 'end_timestamp': min(kwargs.get('endblock', self.end_blk), self.end_blk),
        }
        _ = self.apikey_bucket.get()
        return scrapy.Request(
            url=QueryURLBuilder(self.TXS_API_URL + '/transaction').get(query_params),
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
            'address': address,
            'sort': '-timestamp',
            'limit': 10000,
            # 'start_timestamp': max(kwargs.get('startblock', self.start_blk), self.start_blk),
            # 'end_timestamp': min(kwargs.get('endblock', self.end_blk), self.end_blk),
        }
        _ = self.apikey_bucket.get()
        return scrapy.Request(
            url=QueryURLBuilder(self.TXS_API_URL + '/internal-transaction').get(query_params),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'address': address,
                **kwargs
            },
            callback=self.parse_external_txs,
        )

    def get_erc20_txs_request(self, address: str, **kwargs):
        query_params = {
            'address': address,
            'sort': '-timestamp',
            'limit': 10000,
            # 'start_timestamp': max(kwargs.get('startblock', self.start_blk), self.start_blk),
            # 'end_timestamp': min(kwargs.get('endblock', self.end_blk), self.end_blk),
        }
        _ = self.apikey_bucket.get()
        if kwargs.get('retry') is not None:
            query_params['retry'] = kwargs['retry']
        return scrapy.Request(
            url=QueryURLBuilder(self.TXS_API_URL + '/contract/events').get(query_params),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'address': address,
                **kwargs
            },
            callback=self.parse_erc20_txs,
        )

    def get_erc721_txs_request(self, address: str, **kwargs):
        return None

    def load_txs_from_response(self, response):
        data = json.loads(response.text)
        txs = None
        data = data.get('data', data.get('token_transfers', None))
        if isinstance(data, list):
            txs = list()
            for tx in data:
                if tx.get('ownerAddress') and tx.get('toAddress'):
                    tx['from'], tx['to'] = tx['ownerAddress'], tx['toAddress']
                if tx.get('transferFromAddress') and tx.get('transferToAddress'):
                    tx['from'], tx['to'] = tx['transferFromAddress'], tx['transferToAddress']
                tx['value'] = int(tx.get('amount', 1))
                tx['timeStamp'] = int(tx.get('timestamp', 1))

                symbol = tx.get('tokenName', 'native')
                if self.symbols and symbol not in self.symbols:
                    continue
                tx['symbol'] = symbol
                tx['id'] = '{}_{}_{}'.format(tx.get('hash'), tx.get('traceId'), tx['symbol'])
                txs.append(tx)
        return txs

