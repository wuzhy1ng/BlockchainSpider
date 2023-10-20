import http
import json
import logging

import scrapy

from BlockchainSpider import settings
from BlockchainSpider.items import SourceCodeItem
from BlockchainSpider.utils.bucket import AsyncItemBucket
from BlockchainSpider.utils.url import QueryURLBuilder


class SourceCodeSpider(scrapy.Spider):
    name = 'contracts.source.web3'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.SourceCodePipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = kwargs.get('out', './data')

        # set api domain
        self.api_domain = kwargs.get('domain', 'api.etherscan.io')
        self.api_domain = 'https://%s/api' % self.api_domain

        # load apikey bucket class
        self.apikeys = kwargs.get('apikeys')
        assert self.apikeys is not None
        self.apikeys = self.apikeys.split(',')
        self.apikey_bucket = AsyncItemBucket(self.apikeys, 2)

        # set addresses for query source code
        self.addresses = kwargs.get('addresses')
        assert self.addresses is not None
        self.addresses = self.addresses.split(',')

    def start_requests(self):
        yield scrapy.Request(
            url=self.api_domain,
            callback=self._start_requests,
        )

    async def _start_requests(self, response: scrapy.http.Response, **kwargs):
        if response.status != http.HTTPStatus.OK:
            self.log(
                message='Failed on api endpoint of `{}`'.format(self.api_domain),
                level=logging.ERROR,
            )
            return

        # generate request for each contract addresses
        self.log(
            message='Detected api endpoint of `{}`'.format(self.api_domain),
            level=logging.INFO,
        )
        for addr in self.addresses:
            yield scrapy.Request(
                url=QueryURLBuilder(self.api_domain).get({
                    'module': 'contract',
                    'action': 'getsourcecode',
                    'address': addr,
                    'apikey': await self.apikey_bucket.get()
                }),
                callback=self.parse_source,
            )

    def parse_source(self, response: scrapy.http.Response, **kwargs):
        try:
            data = json.loads(response.text)
        except:
            self.log(
                message='Failed to parse the response contract as JSON',
                level=logging.WARNING,
            )

        rlt = data['result'][0]
        yield SourceCodeItem(
            compiler_version=rlt.get('CompilerVersion', ''),
            evm_version=rlt.get('EVMVersion', ''),
            contract_name=rlt.get('ContractName', ''),
            library=rlt.get('Library', ''),
            proxy=rlt.get('Proxy', ''),
            optimization=rlt.get('OptimizationUsed', ''),
            runs=rlt.get('Runs', ''),
            source_code=rlt.get('SourceCode', ''),
            constructor_arguments=rlt.get('ConstructorArguments', ''),
            license=rlt.get('LicenseType', ''),
        )
