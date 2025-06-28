# Solana

BlockchainSpider provides a spider to collect transaction data from the Solana blockchain.

## Collect by Slot Number

To collect Solana blockchain data by slot number, use the following command:

```shell
scrapy crawl trans.block.solana \
-a providers=https://your.provider.solana \
-a start_slot=349485000 \
-a end_slot=349486000 \
-a out=/path/to/your/data
```

### Parameters:

- **`providers`**: The RPC provider URL for accessing the Solana.
If you have multiple providers, separate them with commas.
It is recommended that you get providers from blockchain data services, e.g., [alchemy](https://www.alchemy.com/).
- **`start_slot`**: The starting slot number for data collection.
- **`end_slot`**: (**optional**) The ending slot number for data collection.
If not specified, the spider will continuously listen and parse the latest slot data.
- **`out`**: (**optional**) The output directory for storing the collected data. The default is `./data`.

💡 All collected data structures are defined in [BlockchainSpider/items/solana.py](https://github.com/wuzhy1ng/BlockchainSpider/blob/master/BlockchainSpider/items/solana.py).
Refer to the corresponding code for detailed data structures.
