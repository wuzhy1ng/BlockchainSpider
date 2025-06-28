import hashlib
import json

import scrapy

from BlockchainSpider.items import AccountTransferItem
from BlockchainSpider.middlewares.txs.tronscan import TRXTRC10TransferMiddleware
from BlockchainSpider.utils.url import QueryURLBuilder


class TRC20TRC721TransferMiddleware(TRXTRC10TransferMiddleware):
    async def get_request_transfers(
            self, address: str,
            start_timestamp: int,
            end_timestamp: int,
            **kwargs
    ):
        request = await super().get_request_transfers(
            address=address,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            **kwargs
        )
        query_params = {
            'relatedAddress': address,
            'sort': 'timestamp',
            'count': True,
            'limit': self.max_page_size,
            'start': kwargs.get('start', 0),
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp,
        }
        if kwargs.get('retry') is not None:
            query_params['retry'] = kwargs['retry']
        url = '%s/api/token_trc20/transfers' % self.endpoint
        url = QueryURLBuilder(url).get(query_params)
        return request.replace(url=url)

    async def parse_transfers(self, response: scrapy.http.Response, **kwargs):
        # check the response data and retry
        data = json.loads(response.text)
        if not isinstance(data.get('token_transfers'), list):
            yield await self.get_retry_request_transfers(response.request)
            return

        # parsing
        for tx in data['token_transfers']:
            tx['id'] = '_'.join([
                tx['from_address'], tx['to_address'],
                tx.get('quant', 1), tx['transaction_id'],
                tx['contract_address'],
            ])
            tx['id'] = hashlib.sha1(tx['id'].encode('utf-8')).hexdigest()
            item = AccountTransferItem(
                id=tx['id'], hash=tx['transaction_id'],
                address_from=tx['from_address'],
                address_to=tx['to_address'],
                value=int(tx.get('quant', 1)),
                token_id='',
                timestamp=int(tx['block_ts']),
                block_number=int(tx['block']),
                contract_address=tx['contract_address'],
                symbol=tx['tokenInfo'].get('tokenAbbr', ''),
                decimals=int(tx['tokenInfo'].get('tokenDecimal', -1)),
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
        start_timestamp = kwargs.get('start_timestamp', self.start_timestamp)
        end_timestamp = kwargs.get('end_timestamp', self.end_timestamp)
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
            if pages > 19:
                break
