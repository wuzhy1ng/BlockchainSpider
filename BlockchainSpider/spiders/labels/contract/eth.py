import csv
import json

import scrapy
from scrapy.utils.misc import load_object

from BlockchainSpider import settings
from BlockchainSpider.items import LabelItem


class LabelsContractETHSpider(scrapy.Spider):
    name = 'labels.contract.eth'
    net = 'eth'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # self.out_filename = kwargs.get('out', os.path.join('./data', self.name))
        self.out_dir = kwargs.get('out', './data')
        self.start_block = kwargs.get('start_blk', '0')
        self.end_block = kwargs.get('end_blk', None)
        self.contracts_file = kwargs.get('file', None)

        # load apikey bucket class
        apikey_bucket = getattr(settings, 'APIKEYS_BUCKET', None)
        assert apikey_bucket is not None
        self.apikey_bucket = load_object(apikey_bucket)(net='eth', kps=5)

        self.base_ui_url = 'https://cn.etherscan.com'
        self.base_api_url = 'https://api-cn.etherscan.com/api'

    def start_requests(self):
        if self.contracts_file is not None:
            with open(self.contracts_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    yield self.get_contract_request(row[0])
            return

        if self.end_block is None:
            url = self.base_api_url + '?module=proxy&action=eth_blockNumber&apikey=%s' % self.apikey_bucket.get()
            yield scrapy.Request(
                url=url,
                method='GET',
                callback=self.parse_block_number,
            )
            return

        self.start_block = int(self.start_block)
        self.end_block = int(self.end_block)
        for i in range(self.start_block, self.end_block + 1):
            url = self.base_api_url + '?module=proxy&action=eth_getBlockByNumber&tag=%s&boolean=true&apikey=%s' % (
                hex(i), self.apikey_bucket.get()
            )
            yield scrapy.Request(
                url=url,
                method='GET',
                callback=self.parse_block,
            )

    def parse_block_number(self, response, **kwargs):
        data = json.loads(response.text)
        self.end_block = int(data['result'], 16)

        self.start_block = int(self.start_block)
        self.end_block = int(self.end_block)
        for i in range(self.start_block, self.end_block + 1):
            url = self.base_api_url + '?module=proxy&action=eth_getBlockByNumber&tag=%s&boolean=true&apikey=%s' % (
                hex(i), self.apikey_bucket.get()
            )
            yield scrapy.Request(
                url=url,
                method='GET',
                callback=self.parse_block,
            )

    def parse_block(self, response, **kwargs):
        data = json.loads(response.text)
        txs = data.get('result')
        if not isinstance(txs, dict):
            yield response.request.replace(dont_filter=True)
            return

        txs = txs.get('transactions')
        if txs is None or len(txs) == 0:
            return

        create_tx_hash = list()
        for tx in txs:
            if tx.get('to') is None:
                create_tx_hash.append(tx['hash'])

        # self.log(create_tx_hash)
        for tx_hash in create_tx_hash:
            yield self.get_tx_receipt_request(tx_hash)

    def parse_tx_receipt(self, response, **kwargs):
        data = json.loads(response.text)
        contract_address = data['result'].get('contractAddress')
        if contract_address is not None:
            yield self.get_contract_request(contract_address)

    def parse_contract(self, response, **kwargs):
        address = kwargs['address']
        tags = response.xpath('//main[@id="content"]//div[@class="mt-1"]/a/text()').getall()
        site_name = response.xpath(
            '//div[@id="ContentPlaceHolder1_divSummary"]//div[@class="col-md-6 mb-3 mb-md-0"]/div[@class="card h-100"]/div[contains(@class,"card-header")]/div/span/span/text()'
        ).get()
        site = response.xpath(
            '//div[@id="ContentPlaceHolder1_divSummary"]//div[@class="col-md-6 mb-3 mb-md-0"]/div[@class="card h-100"]/div[contains(@class,"card-header")]/div//a/@href'
        ).get()
        creator = response.xpath(
            '//div[@id="ContentPlaceHolder1_trContract"]/div[contains(@class,"row")]/div[@class="col-md-8"]/a/text()'
        ).get()

        url = self.base_ui_url + '/address/%s' % creator
        yield scrapy.Request(
            url=url,
            method='GET',
            callback=self.parse_creator,
            cb_kwargs=dict(
                address=address,
                tags=tags,
                site_name=site_name,
                site=site,
                creator=creator,
            ),
            priority=response.request.priority * 2,
        )

    def parse_creator(self, response, **kwargs):
        tags = response.xpath('//main[@id="content"]//div[@class="mt-1"]/a/text()').getall()
        site_name = response.xpath(
            '//div[@id="ContentPlaceHolder1_divSummary"]//div[@class="col-md-6 mb-3 mb-md-0"]/div[@class="card h-100"]/div[contains(@class,"card-header")]/div/span/span/text()'
        ).get()
        site = response.xpath(
            '//div[@id="ContentPlaceHolder1_divSummary"]//div[@class="col-md-6 mb-3 mb-md-0"]/div[@class="card h-100"]/div[contains(@class,"card-header")]/div//a/@href'
        ).get()
        creator = kwargs['creator']
        kwargs['creator'] = dict(
            address=creator,
            tags=tags,
            site_name=site_name,
            site=site,
        )
        yield LabelItem(
            net=self.net,
            label=','.join(kwargs.get('tags', [])),
            info=kwargs
        )

    def get_block_request(self, block_number: int):
        url = self.base_api_url + "?module=proxy&action=eth_getBlockByNumber&" \
                                  "tag=%s&boolean=true&apikey=%s" % (hex(block_number), self.apikey_bucket.get())
        return scrapy.Request(
            url=url,
            method='GET',
            callback=self.parse_block
        )

    def get_tx_receipt_request(self, tx_hash: str, priority: int = 100):
        url = self.base_api_url + '?module=proxy&action=eth_getTransactionReceipt&txhash=%s&apikey=%s' % (
            tx_hash, self.apikey_bucket.get()
        )
        return scrapy.Request(
            url=url,
            method='GET',
            callback=self.parse_tx_receipt,
            priority=priority
        )

    def get_contract_request(self, contract_address: str, priority: int = 200):
        url = (self.base_ui_url + '/address/%s') % contract_address
        return scrapy.Request(
            url=url,
            method='GET',
            callback=self.parse_contract,
            cb_kwargs={'address': contract_address},
            priority=priority,
        )
