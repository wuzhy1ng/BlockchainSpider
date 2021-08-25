import logging
import re
from urllib.parse import urlsplit, urljoin, urlencode

import scrapy
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from ..items import LabelItem


class LabelsSpider(scrapy.Spider):
    name = 'labels'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver_options = webdriver.ChromeOptions()
        self.driver_options.binary_location = '/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev'

        self.url_label_cloud = 'https://cn.etherscan.com/labelcloud'
        self.page_size = 1000

    def start_requests(self):
        driver = webdriver.Chrome(options=self.driver_options)
        driver.get('https://cn.etherscan.com/login')
        WebDriverWait(
            driver=driver,
            timeout=300,
        ).until(lambda d: d.current_url.find('myaccount') > 0)
        raw_cookies = driver.get_cookies()
        driver.quit()

        print(raw_cookies)
        session_cookie = dict()
        for c in raw_cookies:
            if c.get('name') == 'ASP.NET_SessionId':
                session_cookie['ASP.NET_SessionId'] = c['value']
                break
        yield scrapy.Request(
            url=self.url_label_cloud,
            method='GET',
            cookies=session_cookie,
            callback=self.parse_label_cloud,
        )

    def parse_label_cloud(self, response, **kwargs):
        for a in response.xpath('//div[contains(@class,"dropdown-menu")]//a'):
            href = a.xpath('@href').get()
            size = a.xpath('text()').get()
            size = re.sub('<.*?>', '', size)
            size = re.search(r'\d+', size).group() if re.search(r'\d+', size) else self.page_size

            root_url = '%s://%s' % (urlsplit(response.url).scheme, urlsplit(response.url).netloc)
            yield scrapy.Request(
                url=urljoin(root_url, href),
                method='GET',
                cookies=response.request.cookies,
                callback=self.parse_label_navigation,
                cb_kwargs=dict(size=size)
            )

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
                size = total if total < self.page_size else self.page_size
                start = 0
                subcatid = tab.attrib.get('val', 0)

                while start < total:
                    _url = '?'.join([
                        base_url,
                        urlencode({
                            'subcatid': subcatid,
                            'size': size,
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
                    start += size
        else:
            total = int(kwargs.get('size', self.page_size))
            size = total if total < self.page_size else self.page_size
            start = 0

            while start < total:
                _url = '?'.join([
                    base_url,
                    urlencode({
                        'size': size,
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
                start += size

    def parse_labels(self, response, **kwargs):
        label = kwargs.get('label')

        info_headers = response.xpath('//thead/tr/th/text()').getall()
        info_headers = [re.sub(r'\s*', '', header) for header in info_headers]
        for row in response.xpath('//tbody/tr'):
            info = dict(url=response.url)
            for i, td in enumerate(row.xpath('./td').extract()):
                info[info_headers[i]] = re.sub('<.*?>', '', td)
            yield LabelItem(
                net='eth',
                label=label,
                info=info,
            )
