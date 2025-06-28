import hashlib
import json
import logging
from urllib.parse import urlparse

import scrapy

from BlockchainSpider.items.subgraph import PopItem, UTXOTransferItem
from BlockchainSpider.middlewares import SyncMiddleware
from BlockchainSpider.middlewares.defs import LogMiddleware
from BlockchainSpider.utils.decorator import log_debug_tracing


class TransactionMiddleware(LogMiddleware):
    def __init__(self):
        self.max_retry = 2
        self.endpoint = None

    async def process_spider_output(self, response, result, spider):
        if self.endpoint is None:
            self.endpoint = spider.endpoint
        async for item in result:
            yield item
            if not isinstance(item, PopItem):
                continue
            yield self.get_request_transaction(
                txid=item['node'],
                **{SyncMiddleware.SYNC_KEYWORD: item['node']}
            )

    def get_request_transaction(self, txid: str, **kwargs):
        url = '%s/transaction/%s' % (self.endpoint, txid)
        return scrapy.Request(
            url=url, method='GET',
            dont_filter=True,
            cb_kwargs={
                'txid': txid,
                **kwargs
            },
            callback=self.parse_transaction,
            errback=self.errback_parse_transaction,
        )

    def get_retry_request_transaction(self, failed_request: scrapy.Request):
        kwargs = failed_request.cb_kwargs
        retry = kwargs.get('retry', 0)
        if retry >= self.max_retry:
            self.log(
                message='Failed to fetch data from: %s, '
                        'please check your network is available now. '
                        'Otherwise, you can try to slow down the currency.' % failed_request.url,
                level=logging.ERROR,
            )
            return
        kwargs['retry'] = retry + 1
        self.log(
            message="Retrying ({}/{}), find a failure of: {}".format(
                kwargs['retry'], self.max_retry, failed_request.url,
            ),
            level=logging.WARNING,
        )
        txid = kwargs.pop('txid')
        return self.get_request_transaction(
            txid=txid,
            **kwargs,
        )

    @log_debug_tracing
    def parse_transaction(self, response: scrapy.http.Response, **kwargs):
        # check the response data
        data = json.loads(response.text)
        if not isinstance(data, dict):
            return
        txid = kwargs['txid']

        # parsing input
        for i, in_utxo in enumerate(data['inputs']):
            tx_from = in_utxo['txid']
            identity = '{}_{}_{}'.format(tx_from, txid, i)
            identity = hashlib.sha1(identity.encode('utf-8')).hexdigest()
            yield UTXOTransferItem(
                id=identity,
                tx_from=tx_from,
                tx_to=txid,
                address=in_utxo.get('address', ''),
                value=in_utxo.get('value', -1),
                is_spent=True,
                is_coinbase=data.get('coinbase', False),
                timestamp=data['time'],
                block_number=data['block']['height'],
                fee=data['fee'],
            )

        # parsing output
        for i, out_utxo in enumerate(data['outputs']):
            tx_to = ''
            if out_utxo.get('spent', False):
                tx_to = out_utxo['spender']['txid']
            identity = '{}_{}_{}'.format(txid, tx_to, i)
            identity = hashlib.sha1(identity.encode('utf-8')).hexdigest()
            yield UTXOTransferItem(
                id=identity,
                tx_from=txid,
                tx_to=tx_to,
                address=out_utxo.get('address', ''),
                value=out_utxo.get('value', -1),
                is_spent=data.get('spent', False),
                is_coinbase=False,
                timestamp=data['time'],
                block_number=data['block']['height'],
                fee=data['fee'],
            )

    @log_debug_tracing
    async def errback_parse_transaction(self, failure):
        yield self.get_retry_request_transaction(failure.request)
