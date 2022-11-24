import datetime

import scrapy

from BlockchainSpider.items import SubgraphTxItem
from BlockchainSpider.utils.bucket import JsonAPIKeyBucket
from BlockchainSpider.utils.url import RouterURLBuiler, QueryURLBuilder


class TxsBTCSpider(scrapy.Spider):
    # Target original url configure
    TXS_API_URL = 'https://api.blockcypher.com'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # input source nodes
        self.source = kwargs.get('source', None)
        self.filename = kwargs.get('file', None)
        assert self.source or self.filename, "`source` or `file` arguments are needed"

        # output dir
        self.out_dir = kwargs.get('out', './data')
        self.out_fields = kwargs.get('fields', 'id,hash,from,to,value,timeStamp,blockNumber,age').split(',')

        # apikey bucket
        self.apikey_bucket = JsonAPIKeyBucket('btc', kps=3)

    def get_tx_request(self, txhash: str, **kwargs):
        return scrapy.Request(
            url=QueryURLBuilder(
                original_url=RouterURLBuiler(self.TXS_API_URL).get(['v1', 'btc', 'main', 'txs', txhash])
            ).get(args={'token': self.apikey_bucket.get(), 'limit': 99999}),
            method='GET',
            dont_filter=True,
            cb_kwargs={
                'source': kwargs['source'],
                'hash': txhash,
                **kwargs
            },
            callback=self.parse_tx,
        )

    def parse_tx(self, response, **kwargs):
        raise NotImplementedError()

    def parse_input_txs(self, data: dict, **kwargs) -> list:
        txs = list()
        for tx in data['inputs']:
            txs.append(SubgraphTxItem(
                source=kwargs['source'],
                tx={
                    'id': '{}_{}'.format(data['hash'], tx.get('age', 0)),
                    'hash': data['hash'],
                    'from': tx['prev_hash'],
                    'to': data['hash'],
                    'value': tx['output_value'],
                    'address': tx['addresses'][0] if len(tx['addresses']) > 0 else '',
                    'timeStamp': int(datetime.datetime.strptime(data['confirmed'], '%Y-%m-%dT%H:%M:%S%z').timestamp()),
                    'spent': True,
                    'blockNumber': data['block_height'],
                    'script': tx.get('script', ''),
                    'age': tx.get('age', 0)
                }
            ))
        return txs

    def parse_output_txs(self, data: dict, **kwargs) -> list:
        txs = list()
        for tx in data['outputs']:
            spent_by = tx.get('spent_by')
            txs.append(SubgraphTxItem(
                source=kwargs['source'],
                tx={
                    'id': '{}_{}'.format(data['hash'], tx.get('age', 0)),
                    'hash': data['hash'],
                    'from': data['hash'],
                    'to': spent_by if spent_by else '',
                    'value': tx['value'],
                    'address': tx.get('addresses')[0] if tx.get('addresses') and len(tx['addresses']) > 0 else '',
                    'timeStamp': int(datetime.datetime.strptime(data['confirmed'], '%Y-%m-%dT%H:%M:%S%z').timestamp()),
                    'spent': True if spent_by else False,
                    'blockNumber': data['block_height'],
                    'script': tx.get('script', ''),
                    'age': tx.get('age', 0)
                }
            ))
        return txs
