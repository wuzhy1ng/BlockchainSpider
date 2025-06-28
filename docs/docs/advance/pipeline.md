from Demos.RegCreateKeyTransacted import trans

# Pipeline
Pipeline is used to process output items.
In BlockchainSpider, the default pipeline is to save all output data to a file, e.g., CSV, JSON, etc.
The default storage path is `. /data`.
All built-in pipelines are defined under `BlockchainSpider/pipelines`.

Of course, you can also define **your own pipeline**.
Here is an example.
We start a `trans.block.evm` spider that extracts data from the block.
If there are more than 1000 Ether transactions in the extracted data, we print the transaction hash in the custom pipeline.

**First**, we define a file `mypipe.py` in the project root directory:
```python
from BlockchainSpider.items import SyncItem, TransactionItem

class MyPipeline:
    def process_item(self, item, spider):
        # `trans.block.evm` spider output the SyncItem that should be unpacked.
        # you can find the definition of SyncItem in `BlockchainSpider/items/sync.py`
        if not isinstance(item, SyncItem):
            return item
        transfers = item.get(TransactionItem.__name__)
        for transfer in transfers:
            value = transfer.get('value', 0)
            amount = value / 10**18  # Convert Wei to Ether
            if amount > 1000:
                print(f"Transaction hash: {transfer.get('transaction_hash')}")
        return item
```

**Next**, you need to enable your pipeline in `BlockchainSpider/settings.py`:
```python
ITEM_PIPELINES = {
    'mypipe.MyPipeline': 888,
}
```

**Finally**, start the `trans.block.evm` spider:
```shell
scrapy crawl trans.block.evm \
-a providers=https://eth.llamarpc.com \
-a start_blk=19000000 \
-a end_blk=19100000
```