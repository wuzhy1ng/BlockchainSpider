# Scrapy settings for BlockchainSpider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'BlockchainSpider'

SPIDER_MODULES = ['BlockchainSpider.spiders']
NEWSPIDER_MODULE = 'BlockchainSpider.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'BlockchainSpider (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 8

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 5
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.8 Safari/537.36',
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'BlockchainSpider.middlewares.BlockchainspiderSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   'BlockchainSpider.middlewares.TxsCacheMiddleware': 901,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'BlockchainSpider.pipelines.LabelsPipeline': 300,
    'BlockchainSpider.pipelines.TxsPipeline': 301,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = './cache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
HTTPCACHE_GZIP = True

# Log configure
LOG_LEVEL = 'INFO'

SCAN_APIKEYS = [
    # 'SQK66V2BNCHM85JJDGBP7EV4VHVTW7ZKDJ',
    # '4UX2YETIKG27YIP81XDI4SEII8DW538QU3',
    'XFFYAR7DBFMZB29VTQ6GR51XF2DB887X58',

    # 'J9996KUX8WNA5I86WY67ZMZK72SST1BIW8',
    # 'YEZRSSP7JJW93WNZ8AIM4CFEIQ1XDI8CDW',
    'PFPRS98QBSNWCWFG1QSBSNTDWSWD8TYT6Y',

    # '4VCZMM3P2GD73WYEBC434YNTQC5R2K1EP5',
    # '8Y7KSGX5BP6DMQT8ITJPFY6DCHQIUHST24',
    '9V1P5HYR53Q41CK6DAJTAU2UJ7IB8F8WWE',

    # 'JKE66VUUEHBF3A182C11PGMYSH44QC89IN',
    'NN8E4G2ECEIZDFHWU3IN28MIQ7SUMEYPTF',

    'YB9Y2UZKHM2V9PKIGBXYRNBATZ36T5GS8T',
]
