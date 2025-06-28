from BlockchainSpider.middlewares.txs.blockscan.external import ExternalTransferMiddleware
from BlockchainSpider.utils.url import QueryURLBuilder


class Token20TransferMiddleware(ExternalTransferMiddleware):
    async def get_request_transfers(
            self, address: str,
            start_blk: int, end_blk: int,
            **kwargs
    ):
        request = await super().get_request_transfers(
            address=address,
            start_blk=start_blk,
            end_blk=end_blk,
            **kwargs,
        )
        query_params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'sort': 'asc',
            'offset': self.max_page_size,
            'startblock': start_blk,
            'endblock': end_blk,
            'apikey': await self.apikey_bucket.get()
        }
        if kwargs.get('retry') is not None:
            query_params['retry'] = kwargs['retry']
        return request.replace(url=QueryURLBuilder(self.endpoint).get(query_params))
