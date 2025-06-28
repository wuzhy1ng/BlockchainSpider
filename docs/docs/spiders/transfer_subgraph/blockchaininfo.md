# BlockchainInfo

The `txs.blockchaininfo` is designed to fetch transfer subgraph from the `Bitcoin` blockchain explorer, i.e.,
`blockchain.info`.
Specifically, `txs.blockchaininfo` aims at searching for the source and destination of funds from a given **transaction**.

## Usage

Run the spider using the following command:

```shell
scrapy crawl txs.blockchaininfo \
-a source=YourSourceTxhash \
-a strategy=BlockchainSpider.strategies.txs.BFS \
-a out=/path/to/your/data
```

**Parameters**

- **`source`**: The starting transaction hash for collecting transaction data. This parameter is required.
- **`strategy`**: (**optional**) The traversal strategy for collecting transactions.
  Default is `BlockchainSpider.strategies.txs.BFS` (Breadth-First Search).
  BlockchainSpider implements other advanced strategies, e.g., Poison, APPR, and TTR.
  For more details, please refer to [Transaction tracing](/advance/transaction_tracing/) section.
- **`out`**: (**optional**) The output directory for storing the collected data. Default is `./data`.

