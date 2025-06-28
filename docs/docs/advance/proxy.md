# Proxy

In some cases, your web request may not be completed, because you are in an area where the network is restricted.
In this case, you can use a proxy to access the resource.
BlockchainSpider supports using proxies for requests.

**First**, you need to enable the proxy middleware in `BlockchainSpider/settings.py`:
```python
DOWNLOADER_MIDDLEWARES = {
    'BlockchainSpider.middlewares.HTTPProxyMiddleware': 901,
}
```

**Next**, when starting the spider, you need to append an additional parameter `http_proxy`.
This parameter specifies the url of your http proxy.
Suppose the following is your startup command for a spider:
```shell
scrapy crawl txs.blockscan \ 
-a source=0xYourSourceAddress \
-a apikeys=YourApiKey1,YourApiKey2
```
The command after adding `http_proxy` should be:
```shell
scrapy crawl txs.blockscan \ 
-a source=0xYourSourceAddress \
-a apikeys=YourApiKey1,YourApiKey2 \
-a http_proxy=http://your.proxy.server:port
```