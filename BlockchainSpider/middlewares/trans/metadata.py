import json
import re
from typing import Union

import scrapy.http
from pybloom import ScalableBloomFilter
from scrapy import Request

from BlockchainSpider import settings
from BlockchainSpider.items import Token721TransferItem, \
    Token1155TransferItem, NFTMetadataItem
from BlockchainSpider.middlewares.defs import LogMiddleware
from BlockchainSpider.utils.decorator import log_debug_tracing
from BlockchainSpider.utils.web3 import parse_bytes_data


class MetadataMiddleware(LogMiddleware):
    def __init__(self):
        self.provider_bucket = None
        self.timeout = getattr(settings, 'DOWNLOAD_TIMEOUT', 120)
        self.bloom4metadata = ScalableBloomFilter(
            initial_capacity=1024,
            error_rate=1e-4,
            mode=ScalableBloomFilter.SMALL_SET_GROWTH,
        )

    def _init_by_spider(self, spider):
        if self.provider_bucket is not None:
            return
        if getattr(spider, 'middleware_providers') and \
                spider.middleware_providers.get(self.__class__.__name__):
            self.provider_bucket = spider.middleware_providers[self.__class__.__name__]
        else:
            self.provider_bucket = spider.provider_bucket

    async def process_spider_output(self, response, result, spider):
        self._init_by_spider(spider)

        # filter and process the result flow
        async for item in result:
            yield item

            # extract the erc721 nft metadata
            if isinstance(item, Token721TransferItem):
                key = '{}_{}'.format(item['contract_address'], item['token_id'])
                if key in self.bloom4metadata:
                    continue
                self.bloom4metadata.add(key)
                yield await self.get_request_metadata_uri(
                    contract_address=item['contract_address'],
                    token_id=item['token_id'],
                    metadata_func_sign='0xc87b56dd',
                    priority=response.request.priority,
                    cb_kwargs={'@nft_transfer': item},
                )
                continue

            # extract the erc1155 nft metadata
            if isinstance(item, Token1155TransferItem):
                for i in range(len(item['token_ids'])):
                    if item['values'][i] > 1:
                        continue
                    key = '{}_{}'.format(item['contract_address'], item['token_ids'][i])
                    if key in self.bloom4metadata:
                        continue
                    self.bloom4metadata.add(key)
                    yield await self.get_request_metadata_uri(
                        contract_address=item['contract_address'],
                        token_id=item['token_ids'][i],
                        metadata_func_sign='0x0e89341c',
                        priority=response.request.priority,
                        cb_kwargs={'token_transfer_item': item},
                    )
                continue

    @log_debug_tracing
    def parse_metadata_uri(self, response: scrapy.http.Response, **kwargs):
        try:
            data = json.loads(response.text)
            result = parse_bytes_data(data.get('result'), ["string"])
        except:
            return
        if result is None or len(result) < 1:
            return

        # generate metadata request
        uri: str = result[0]
        url = uri if not uri.startswith('ipfs://ipfs/') else uri.replace('ipfs://ipfs/', 'https://ipfs.io/ipfs/')
        url = uri if not uri.startswith('ipfs://') else uri.replace('ipfs://', 'https://ipfs.io/ipfs/')
        url = url if not url.startswith('//') else 'http:{}'.format(url)
        pattern = r'[http|https|ipfs]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        if re.search(pattern, url) is None:
            return
        yield self.get_request_metadata(
            url=url,
            priority=response.request.priority,
            cb_kwargs={'uri': uri, **kwargs},
        )

    @log_debug_tracing
    def parse_metadata_item(self, response: scrapy.http.Response, **kwargs):
        try:
            data = response.text
            json.loads(data)
        except:
            return

        # generate metadata item
        nft_transfer: Union[Token721TransferItem, Token1155TransferItem] = kwargs['@nft_transfer']
        yield NFTMetadataItem(
            contract_address=nft_transfer['contract_address'],
            token_id=kwargs['token_id'],
            uri=kwargs['uri'],
            data=data,
            cb_kwargs={'@nft_transfer': kwargs['@nft_transfer']}
        )

    async def get_request_metadata_uri(
            self, contract_address: str, token_id: int,
            metadata_func_sign: str,
            priority: int, cb_kwargs: dict,
    ) -> Request:
        return Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "id": 1,
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{
                    "to": contract_address,
                    "data": metadata_func_sign + str.zfill(hex(token_id)[2:], 64)
                }, "latest"],
            }),
            callback=self.parse_metadata_uri,
            priority=priority,
            cb_kwargs={
                'contract_address': contract_address,
                'token_id': token_id,
                'metadata_func_sign': metadata_func_sign,
                **cb_kwargs
            },
        )

    def get_request_metadata(
            self, url: str,
            priority: int, cb_kwargs: dict,
    ) -> Request:
        return Request(
            url=url,
            method='GET',
            priority=priority,
            callback=self.parse_metadata_item,
            cb_kwargs=cb_kwargs,
        )
