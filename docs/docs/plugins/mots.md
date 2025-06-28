# MoTS

MoTS is an EVM transaction embedding tool that represent transactions as vectors,
which in turn can be used in user machine learning, deep learning tasks.
The MoTS pipeline is able to run on both the `trans.block.evm` and `trans.evm` spiders.

To enable this pipeline, you should **first** install the dependencies:
```shell
pip install -r plugins/mots/requirements.txt
```

And add the configuration in `BlockchainSpider/settings.py`:
```python
ITEM_PIPELINES = {
    'plugins.mots.pipelines.MoTSPipeline': 666,
}
```

**Finally**, launch the EVM transaction spider.
Here is a example:
```shell
scrapy crawl trans.block.evm
-a out=/path/to/output/data \
-a start_blk=19000000
-a end_blk=19001000 \
-a providers=https://your.providers \
-a enable=BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware,BlockchainSpider.middlewares.trans.TraceMiddleware,BlockchainSpider.middlewares.trans.TokenTransferMiddleware
```