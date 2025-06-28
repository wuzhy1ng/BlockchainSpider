# Speedup

In some cases, you may need to make the spider run faster.

Here are two suggestions that may help you accelerate BlockchainSpider.

## Use multiple APIKeys/providers
Transaction Subgraph (`txs`) spider and Transaction (`trans`) spider allow adding multiple data sources, i.e., APIKeys or providers.
BlockchainSpider load balancing across multiple data sources.
In general, the more data sources there are, the faster the spider will be.
For example, if you are using `trans.block.solana` to crawl solana transactions,
then you'd better go to the blockchain data provider website and apply for a few more providers.
Next, you can join multiple providers with commas and start the spider:
```shell
scrapy crawl trans.block.solana \
-a start_slot=270000000 \
-a providers=https://solana-mainnet.g.alchemy.com/v2/UOD8HE4CVqEiDY5E_9XbKDFqYZzJE3XP,https://solana-mainnet.g.alchemy.com/v2/AgKT8OzbNsYnul856tenwnsnL3Pm7WRB,https://solana-mainnet.g.alchemy.com/v2/gwlaWGMm1YWliQTvWtEHcjjfNXQ3W0lK
```


## Increase the concurrency
If you hold a professional apikey or provider, they perform well. 
And you might also consider speeding up BlockchainSpider by adding concurrency.
For example, if you are using `trans.block.solana` to crawl solana transactions.
You can increase the concurrency parameter `CONCURRENT_REQUESTS` in the settings file to achieve the acceleration.
Firstly, please edit the setting file `BlockchainSpider/settings.py`:
```python
# The default concurrency is 2
CONCURRENT_REQUESTS = 16
```
Next, you can go ahead and start the same command when not set `CONCURRENT_REQUESTS`:
```shell
scrapy crawl trans.block.solana \
-a start_slot=270000000 \
-a providers=<your-high-performance-provider>
```