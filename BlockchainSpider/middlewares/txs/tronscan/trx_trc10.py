import hashlib
import json
import logging

import scrapy

from BlockchainSpider.items.subgraph import PopItem, AccountTransferItem
from BlockchainSpider.middlewares import SyncMiddleware
from BlockchainSpider.middlewares.defs import LogMiddleware
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.url import QueryURLBuilder


class TRXTRC10TransferMiddleware(LogMiddleware):
    def __init__(self):
        self.endpoint = None
        self.apikey_bucket = None
        self.start_timestamp = 0
        self.end_timestamp = 9999999999999
        self.max_retry = 2
        self.max_pages = 20
        self.max_page_size = 50

    def _init_by_spider(self, spider):
        if self.endpoint is not None:
            return
        self.endpoint = spider.endpoint
        self.apikey_bucket = spider.apikey_bucket
        self.start_timestamp = int(spider.__dict__.get('start_timestamp', self.start_timestamp))
        self.end_timestamp = int(spider.__dict__.get('end_timestamp', self.end_timestamp))
        self.max_pages = int(spider.__dict__.get('max_pages', self.max_pages))
        self.max_page_size = int(spider.__dict__.get('max_page_size', self.max_page_size))
        self.max_retry = int(spider.__dict__.get('max_retry', self.max_retry))

    async def process_spider_output(self, response, result, spider):
        self._init_by_spider(spider)
        async for item in result:
            yield item
            if not isinstance(item, PopItem):
                continue
            pop_context = item.get_context_kwargs()
            request = await self.get_request_transfers(
                address=item['node'],
                start_timestamp=pop_context.get('start_timestamp', self.start_timestamp),
                end_timestamp=pop_context.get('end_timestamp', self.end_timestamp),
                **{
                    'is_first': True,
                    SyncMiddleware.SYNC_KEYWORD: item['node'],
                }
            )
            yield request

    async def get_request_transfers(
            self, address: str,
            start_timestamp: int,
            end_timestamp: int,
            **kwargs
    ):
        query_params = {
            'address': address,
            'sort': 'timestamp',
            'count': True,
            'limit': self.max_page_size,
            'start': kwargs.get('start', 0),
        }
        if kwargs.get('retry') is not None:
            query_params['retry'] = kwargs['retry']
        url = '%s/api/new/transfer' % self.endpoint
        return scrapy.Request(
            url=QueryURLBuilder(url).get(query_params),
            method='GET',
            headers={'TRON-PRO-API-KEY': await self.apikey_bucket.get()},
            dont_filter=True,
            cb_kwargs={
                'address': address,
                'start_timestamp': start_timestamp,
                'end_timestamp': end_timestamp,
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
        start_timestamp, end_timestamp = kwargs.pop('start_timestamp'), kwargs.pop('end_timestamp')
        return await self.get_request_transfers(
            address=address,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            **kwargs,
        )

    @log_debug_tracing
    async def parse_transfers(self, response: scrapy.http.Response, **kwargs):
        # check the response data and retry
        data = json.loads(response.text)
        if not isinstance(data.get('data'), list):
            yield await self.get_retry_request_transfers(response.request)
            return

        # parsing
        start_timestamp = kwargs.get('start_timestamp', self.start_timestamp)
        end_timestamp = kwargs.get('end_timestamp', self.end_timestamp)
        for tx in data['data']:
            tx['id'] = '_'.join([
                tx['transferFromAddress'], tx['transferToAddress'],
                str(tx['amount']), tx['transactionHash'],
                tx['tokenInfo']['tokenAbbr'],
                tx['tokenInfo']['tokenId'],
            ])
            tx['id'] = hashlib.sha1(tx['id'].encode('utf-8')).hexdigest()
            timestamp = int(tx['timestamp'])
            if timestamp < start_timestamp or timestamp > end_timestamp:
                continue
            item = AccountTransferItem(
                id=tx['id'], hash=tx['transactionHash'],
                address_from=tx['transferFromAddress'],
                address_to=tx['transferToAddress'],
                value=int(tx['amount']),
                token_id=tx['tokenInfo']['tokenId'],
                timestamp=timestamp,
                block_number=int(tx['block']),
                contract_address='T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb',  # black hole
                symbol=tx['tokenInfo']['tokenAbbr'],
                decimals=int(tx['tokenInfo']['tokenDecimal']),
                gas=tx.get('gas', -1),
                gas_price=tx.get('gasPrice', -1),
            )
            item.set_context_kwargs(raw=tx)
            yield item

        # next page requests
        if not kwargs['is_first'] or data['total'] <= self.max_page_size:
            return
        pages = 1
        left_count = data['total'] - self.max_page_size
        while left_count > 0 and pages < self.max_pages:
            yield await self.get_request_transfers(
                address=kwargs['address'],
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                **{
                    'is_first': False,
                    'start': pages * self.max_page_size,
                    'num_page': pages + 1,
                }
            )
            left_count -= self.max_page_size
            pages += 1

    @log_debug_tracing
    async def errback_parse_transfers(self, failure):
        yield await self.get_retry_request_transfers(failure.request)
