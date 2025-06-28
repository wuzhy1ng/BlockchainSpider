import hashlib
import json
import logging

import scrapy

from BlockchainSpider.items.subgraph import PopItem, AccountTransferItem
from BlockchainSpider.middlewares import SyncMiddleware
from BlockchainSpider.middlewares.defs import LogMiddleware
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.url import QueryURLBuilder


class ExternalTransferMiddleware(LogMiddleware):
    def __init__(self):
        self.endpoint = None
        self.apikey_bucket = None
        self.start_blk = 0
        self.end_blk = 99999999
        self.max_retry = 2
        self.max_pages = 1
        self.max_page_size = 10000

    def _init_by_spider(self, spider):
        if self.endpoint is not None:
            return
        self.endpoint = spider.endpoint
        self.apikey_bucket = spider.apikey_bucket
        self.start_blk = int(spider.__dict__.get('start_blk', self.start_blk))
        self.end_blk = int(spider.__dict__.get('end_blk', self.end_blk))
        self.max_retry = int(spider.__dict__.get('max_retry', self.max_retry))
        self.max_pages = int(spider.__dict__.get('max_pages', self.max_pages))
        self.max_page_size = int(spider.__dict__.get('max_page_size', self.max_page_size))

    async def process_spider_output(self, response, result, spider):
        self._init_by_spider(spider)
        async for item in result:
            yield item
            if not isinstance(item, PopItem):
                continue
            pop_context = item.get_context_kwargs()
            request = await self.get_request_transfers(
                address=item['node'],
                start_blk=pop_context.get('start_blk', self.start_blk),
                end_blk=pop_context.get('end_blk', self.end_blk),
                **{SyncMiddleware.SYNC_KEYWORD: item['node']}
            )
            yield request

    async def get_request_transfers(
            self, address: str,
            start_blk: int, end_blk: int,
            **kwargs
    ):
        query_params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'sort': 'asc',
            'offset': self.max_page_size,
            'startblock': start_blk,
            'endblock': end_blk,
            'apikey': await self.apikey_bucket.get()
        }
        if kwargs.get('retry') is not None:
            query_params['retry'] = kwargs['retry']
        url = QueryURLBuilder(self.endpoint).get(query_params)
        return scrapy.Request(
            url=url, method='GET',
            dont_filter=True,
            cb_kwargs={
                'address': address,
                'start_blk': start_blk,
                'end_blk': end_blk,
                'num_page': kwargs.get('num_page', 1),
                **kwargs
            },
            callback=self.parse_transfers,
            errback=self.errback_parse_transfers,
        )

    async def get_retry_request_transfers(
            self, failed_request: scrapy.Request,
    ):
        kwargs = failed_request.cb_kwargs
        retry = kwargs.get('retry', 0)
        if retry >= self.max_retry:
            self.log(
                message='Failed to fetch data from: %s, '
                        'please check your apikey is available now. '
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
        address = kwargs.pop('address')
        start_blk, end_blk = kwargs.pop('start_blk'), kwargs.pop('end_blk')
        return await self.get_request_transfers(
            address=address,
            start_blk=start_blk,
            end_blk=end_blk,
            **kwargs,
        )

    @log_debug_tracing
    async def parse_transfers(self, response: scrapy.http.Response, **kwargs):
        # check the response data and retry
        # because the API may return a non-list result
        data = json.loads(response.text)
        if not isinstance(data.get('result'), list):
            yield await self.get_retry_request_transfers(response.request)
            return

        # parsing
        for tx in data['result']:
            if tx['from'] == '' or tx['to'] == '':
                continue
            tx['id'] = '_'.join([
                tx['from'], tx['to'],
                str(tx.get('value', tx.get('tokenValue', 1))),
                tx.get('hash', ''), tx.get('traceId', ''),
                tx.get('tokenSymbol', 'native'),
                tx.get('contractAddress', ''), tx.get('tokenID', ''),
            ])
            tx['id'] = hashlib.sha1(tx['id'].encode('utf-8')).hexdigest()
            contract_address = tx.get('contractAddress', '')
            contract_address = '0x' + '0' * 40 if contract_address == '' else contract_address
            item = AccountTransferItem(
                id=tx['id'], hash=tx['hash'],
                address_from=tx['from'], address_to=tx['to'],
                value=int(tx.get('value', tx.get('tokenValue', 1))),
                token_id=tx.get('tokenID', ''),
                timestamp=int(tx['timeStamp']),
                block_number=int(tx['blockNumber']),
                contract_address=contract_address,
                symbol=tx.get('tokenSymbol', 'native'),
                decimals=int(tx.get('tokenDecimal', 18)),
                gas=tx.get('gas', ''),
                gas_price=tx.get('gasPrice', ''),
            )
            item.set_context_kwargs(raw=tx)
            yield item

        # next page request
        if len(data['result']) == 0 or kwargs['num_page'] >= self.max_pages:
            return
        cur_max_blk = int(data['result'][-1]['blockNumber'])
        if kwargs['start_blk'] < cur_max_blk <= kwargs['end_blk']:
            request = await self.get_request_transfers(
                address=kwargs['address'],
                start_blk=cur_max_blk,
                end_blk=kwargs['end_blk'],
            )
            yield request

    @log_debug_tracing
    async def errback_parse_transfers(self, failure):
        yield await self.get_retry_request_transfers(failure.request)
