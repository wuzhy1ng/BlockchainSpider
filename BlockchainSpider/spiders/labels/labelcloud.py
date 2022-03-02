import logging
import re
from urllib.parse import urlsplit, urljoin, urlencode

import scrapy
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from BlockchainSpider.items import LabelItem


class LabelsCloudSpider(scrapy.Spider):
    name = 'labels.labelcloud'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver_options = webdriver.ChromeOptions()
        # self.driver_options.binary_location = '/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev'

        self.site = kwargs.get('site', 'etherscan')
        self._allow_site = {
            'etherscan': 'https://cn.etherscan.com',
            'bscscan': 'https://bscscan.com',
            'polygonscan': 'https://polygonscan.com',
            'hecoinfo': 'https://hecoinfo.com'
        }
        assert self.site in self._allow_site.keys()

        self.url_site = self._allow_site[self.site]
        self.url_label_cloud = self.url_site + '/labelcloud'
        self.page_size = 100

        self.out_dir = kwargs.get('out', './data')

        self.label_names = kwargs.get('labels', None)
        if self.label_names is not None:
            self.label_names = self.label_names.split(',')

    def start_requests(self):
        # open selenium to login in
        driver = webdriver.Chrome(options=self.driver_options)
        driver.get(self.url_site + '/login')
        WebDriverWait(
            driver=driver,
            timeout=300,
        ).until(lambda d: d.current_url.find('myaccount') > 0)
        raw_cookies = driver.get_cookies()
        driver.quit()

        # get cookies
        session_cookie = dict()
        for c in raw_cookies:
            if c.get('name') == 'ASP.NET_SessionId':
                session_cookie['ASP.NET_SessionId'] = c['value']
                break

        # generate request for label cloud
        yield scrapy.Request(
            url=self.url_label_cloud,
            method='GET',
            cookies=session_cookie,
            callback=self.parse_label_cloud,
        )

    def parse_label_cloud(self, response, **kwargs):
        root_url = '%s://%s' % (urlsplit(response.url).scheme, urlsplit(response.url).netloc)

        for a in response.xpath('//div[contains(@class,"dropdown-menu")]//a'):
            href = a.xpath('@href').get()
            size = a.xpath('text()').get()
            size = re.sub('<.*?>', '', size)
            size = re.search(r'\d+', size).group() if re.search(r'\d+', size) else self.page_size

            request = scrapy.Request(
                url=urljoin(root_url, href),
                method='GET',
                cookies=response.request.cookies,
                callback=self.parse_label_navigation,
                cb_kwargs=dict(size=size)
            )
            if self.label_names is None:
                yield request
            else:
                for label_name in self.label_names:
                    if href.find(label_name) >= 0:
                        yield request

    def parse_label_navigation(self, response, **kwargs):
        label = ','.join([
            response.xpath('//h1/text()').get(),
            response.xpath('//h1/span/text()').get()
        ])

        base_url = urljoin(
            base='%s://%s' % (urlsplit(response.url).scheme, urlsplit(response.url).netloc),
            url=urlsplit(response.url).path,
        )

        tab_anchors = response.xpath('//div[contains(@class,"card-header")]/ul/li/a')
        if len(tab_anchors) > 0:
            for tab in tab_anchors:
                total = tab.xpath('text()').get()
                total = int(re.search(r'\d+', total).group()) if re.search(r'\d+', total) else self.page_size
                start = 0
                subcatid = tab.attrib.get('val', 0)

                while start < total:
                    _url = '?'.join([
                        base_url,
                        urlencode({
                            'subcatid': subcatid,
                            'size': self.page_size,
                            'start': start,
                        })
                    ])
                    yield scrapy.Request(
                        url=_url,
                        method='GET',
                        cookies=response.request.cookies,
                        callback=self.parse_labels,
                        dont_filter=True,
                        cb_kwargs={'label': label}
                    )
                    start += self.page_size
        else:
            total = int(kwargs.get('size', self.page_size))
            start = 0

            while start < total:
                _url = '?'.join([
                    base_url,
                    urlencode({
                        'size': self.page_size,
                        'start': start,
                    })
                ])
                yield scrapy.Request(
                    url=_url,
                    method='GET',
                    cookies=response.request.cookies,
                    callback=self.parse_labels,
                    dont_filter=True,
                    cb_kwargs={'label': label}
                )
                start += self.page_size

    def parse_labels(self, response, **kwargs):
        self.log(
            message='Extracting items from: ' + response.url,
            level=logging.INFO
        )
        label = kwargs.get('label')

        info_headers = list()
        for header in response.xpath('//thead/tr/th').extract():
            header = re.sub('<.*?>', '', header)
            header = re.sub(r'\s*', '', header)
            info_headers.append(header)

        for row in response.xpath('//tbody/tr'):
            info = dict(url=response.url)
            for i, td in enumerate(row.xpath('./td').extract()):
                info[info_headers[i]] = re.sub('<.*?>', '', td)
            yield LabelItem(
                net='eth',
                label=label,
                info=info,
            )
