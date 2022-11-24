import asyncio
import traceback

import aiohttp
import scrapy
from aiohttp_socks import ProxyConnector, ProxyType
from multidict import CIMultiDict
from scrapy.exceptions import IgnoreRequest

from BlockchainSpider import settings


class TorMiddleware(object):
    def __init__(self):
        self.current_requests = getattr(settings, 'CONCURRENT_REQUESTS', 16)
        self.timeout = getattr(settings, 'DOWNLOAD_TIMEOUT', 120)
        self.lock_request = asyncio.Semaphore(self.current_requests)

    async def process_request(self, request: scrapy.Request, spider):
        # get tor host and port
        tor_host = getattr(spider, 'tor_host', '127.0.0.1')
        tor_port = getattr(spider, 'tor_port', 9150)

        # get signal and requesting
        await self.lock_request.acquire()

        # start a socket5 proxy
        connector = ProxyConnector(
            proxy_type=ProxyType.SOCKS5,
            host=tor_host,
            port=tor_port,
        )

        # start a client
        client = aiohttp.ClientSession(
            connector=connector,
            loop=asyncio.get_event_loop(),
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        try:
            # fetch response
            rsp = await client.request(
                method=request.method,
                url=request.url,
                headers=CIMultiDict(**{
                    k.decode(): v[0].decode()
                    for k, v in request.headers.items()
                }),
                data=request.body,
            )

            # get data and return response
            data = await rsp.read()
            return scrapy.http.TextResponse(
                url=request.url,
                status=rsp.status,
                headers={
                    k.encode(): [v.encode() for v in rsp.headers.getall(k)]
                    for k in rsp.headers.keys() if k.lower() not in {
                        'content-encoding'
                    }
                },
                body=data,
                request=request,
            )
        except:
            traceback.print_exc()
            raise IgnoreRequest()
        finally:
            await client.close()
            await connector.close()
            self.lock_request.release()
