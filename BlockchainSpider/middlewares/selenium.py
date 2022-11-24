import asyncio
import traceback

import scrapy
from scrapy.exceptions import IgnoreRequest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from BlockchainSpider import settings


class SeleniumMiddleware(object):
    def __init__(self):
        self.driver = None
        self.timeout = getattr(settings, 'DOWNLOAD_TIMEOUT', 60)
        self.delay = getattr(settings, 'DOWNLOAD_DELAY', 2)
        self.lock = asyncio.Lock()

    async def process_request(self, request: scrapy.Request, spider):
        await self.lock.acquire()
        if self.driver is None:
            spider_driver = getattr(spider, 'driver')
            self.driver = spider_driver if spider_driver else webdriver.Chrome(
                options=webdriver.ChromeOptions()
            )

        try:
            self.driver.get(request.url)
            await asyncio.sleep(self.delay)
            WebDriverWait(self.driver, self.timeout, 0.5).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            body = self.driver.page_source.encode()
            return scrapy.http.TextResponse(
                url=request.url,
                status=200,
                body=body,
                request=request,
            )
        except:
            traceback.print_exc()
            raise IgnoreRequest()
        finally:
            self.lock.release()
