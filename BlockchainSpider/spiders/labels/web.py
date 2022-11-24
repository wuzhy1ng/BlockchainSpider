import re
import urllib.parse
from collections.abc import Generator

import scrapy
from bitcoin import is_address as is_btc_address
from summa.keywords import keywords
from summa.summarizer import summarize
from web3 import Web3

from BlockchainSpider import settings
from BlockchainSpider.items import LabelReportItem, LabelAddressItem, LabelTransactionItem


class LabelsWebSpider(scrapy.Spider):
    name = 'labels.web'
    custom_settings = {
        'DEPTH_PRIORITY': 1,
        'SCHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleFifoDiskQueue',
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.FifoMemoryQueue',
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.LabelsPipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = kwargs.get('source')
        assert self.source is not None, 'source url must not be None.'

        self.domain = kwargs.get('domain', None)
        if self.domain is not None:
            self.__class__.allowed_domains = self.domain.split(',')

        self.keywords = int(kwargs.get('keywords', 16))
        self.summary = kwargs.get('summary', 256)
        self.out_dir = kwargs.get('out')

    def start_requests(self):
        yield scrapy.Request(
            url=self.source,
            method='GET',
        )

    def parse(self, response: scrapy.http.Response, **kwargs):
        # remove style tag and script tag
        content = re.sub(r'<style[\s\S]*?</style>', ' ', response.text)
        content = re.sub(r'<script[\s\S]*?</script>', ' ', content)
        content = re.sub('<(.*?)>', ' ', content)

        # generate address label items from raw text
        yield from self.generate_address_item(
            extract_text=content,
            summary_text=content if not kwargs.get('summary_text') else kwargs['summary_text'],
            url=response.url,
        )

        # generate address label items from script
        for script in response.xpath('//script[@type="text/javascript"]/text()').getall():
            yield from self.generate_address_item(
                extract_text=script,
                summary_text=content if not kwargs.get('summary_text') else kwargs['summary_text'],
                url=response.url,
            )

        # generate address label items from link
        for href in response.xpath('//a/@href').getall():
            yield from self.generate_address_item(
                extract_text=href,
                summary_text=content if not kwargs.get('summary_text') else kwargs['summary_text'],
                url=response.url,
            )

        # fetching related link
        for href in response.xpath('//a/@href').getall():
            url = urllib.parse.urljoin(response.url, href)
            if not urllib.parse.urlparse(url).scheme.startswith('http'):
                continue
            yield scrapy.Request(
                url=url,
                method='GET',
            )

        # fetching related script
        for src in response.xpath('//script/@src').getall():
            url = urllib.parse.urljoin(response.url, src)
            yield scrapy.Request(
                url=url,
                method='GET',
                cb_kwargs={'summary_text': content}
            )

    def _generate_btc_address(self, text: str) -> Generator:
        pattern = re.compile(r'\W([13][a-km-zA-HJ-NP-Z1-9]{25,34})')
        for addr in pattern.findall(text):
            if is_btc_address(addr):
                yield addr

    def _generate_btc_transaction(self, text: str) -> Generator:
        pattern = re.compile(r"\W([0-9a-f]{64})", re.IGNORECASE | re.ASCII)
        for addr in pattern.findall(text):
            yield addr

    def _generate_eth_address(self, text: str) -> Generator:
        pattern = re.compile(r"\W(0x[0-9a-f]{40})", re.IGNORECASE | re.ASCII)
        for addr in pattern.findall(text):
            if Web3.isAddress(addr):
                yield addr

    def _generate_eth_transaction(self, text: str) -> Generator:
        pattern = re.compile(r"\W(0x[0-9a-f]{64})", re.IGNORECASE | re.ASCII)
        for addr in pattern.findall(text):
            yield addr

    def generate_address_item(
            self,
            extract_text: str,
            summary_text: str,
            url: str
    ) -> Generator:
        # generate btc label item
        for addr in self._generate_btc_address(extract_text):
            yield LabelReportItem(
                labels=keywords(summary_text, split=True, words=self.keywords),
                urls=list(),
                addresses=[{**LabelAddressItem(
                    net='BTC-Like',
                    address=addr,
                )}],
                transactions=list(),
                description=summarize(summary_text, words=self.summary),
                reporter=url,
            )

        # generate eth label item
        for addr in self._generate_eth_address(extract_text):
            yield LabelReportItem(
                labels=keywords(summary_text, split=True, words=self.keywords),
                urls=list(),
                addresses=[{**LabelAddressItem(
                    net='ETH-Like',
                    address=addr,
                )}],
                transactions=list(),
                description=summarize(summary_text, words=self.summary),
                reporter=url,
            )

        # generate BTC transaction label item
        for txhash in self._generate_btc_transaction(extract_text):
            yield LabelReportItem(
                labels=keywords(summary_text, split=True, words=self.keywords),
                urls=list(),
                addresses=list(),
                transactions=[{**LabelTransactionItem(
                    net='BTC-Like',
                    transaction_hash=txhash,
                )}],
                description=summarize(summary_text, words=self.summary),
                reporter=url,
            )

        # generate ETH transaction label item
        for txhash in self._generate_eth_transaction(extract_text):
            yield LabelReportItem(
                labels=keywords(summary_text, split=True, words=self.keywords),
                urls=list(),
                addresses=list(),
                transactions=[{**LabelTransactionItem(
                    net='ETH-Like',
                    transaction_hash=txhash,
                )}],
                description=summarize(summary_text, words=self.summary),
                reporter=url,
            )