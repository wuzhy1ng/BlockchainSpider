# Tronscan

The `txs.tronscan` is designed to fetch transfer subgraph from the `Tron` blockchain explorer, i.e., `tronscan.org`.
Specifically, `txs.tronscan` aims at searching for the source and destination of funds from a given **address**.

## Usage

Run the spider using the following command:

```shell
scrapy crawl txs.tronscan \
-a source=YourSourceAddress \
-a apikeys=YourApiKey1,YourApiKey2 \
-a strategy=BlockchainSpider.strategies.txs.BFS \
-a allowed_tokens=TokenAddress1,TokenAddress2 \
-a out=/path/to/your/data \
-a out_fields=hash,address_from,address_to,value,token_id,timestamp,block_number,contract_address,symbol,decimals \
-a enable=BlockchainSpider.middlewares.txs.tronscan.TRXTRC10TransferMiddleware \
-a start_timestamp=1750000000 \
-a end_timestamp=1751000000 \
-a max_pages=20 \
-a max_page_size=50
```

**Parameters**

- **`source`**: The starting address for collecting transaction data. This parameter is required.
- **`apikeys`**: A comma-separated list of API keys for accessing the blockchain explorer.
  At least one API key is required.
  You can apply your API key from [tronscan.org](https://tronscan.org).
- **`strategy`**: (**optional**) The traversal strategy for collecting transactions.
  Default is `BlockchainSpider.strategies.txs.BFS` (Breadth-First Search).
  BlockchainSpider implements other advanced strategies, e.g., Poison, APPR, and TTR.
  For more details, please refer to [Transaction tracing](/advance/transaction_tracing/) section.
- **`allowed_tokens`**: (**optional**) A comma-separated list of token contract addresses to filter transactions. If not
  provided, all
  tokens are included.
- **`out`**: (**optional**) The output directory for storing the collected data. Default is `./data`.
- **`out_fields`**: (**optional**) A comma-separated list of fields to include in the output.
  the default is
  `address_from,address_to,block_number,contract_address,decimals,gas,gas_price,hash,id,symbol,timestamp,token_id,value`.
- **`enable`**: (**optional**) A comma-separated list of middlewares to enable during the spider run. Add different
  middlewares to
  trace specific types of assets. The default is `BlockchainSpider.middlewares.txs.tronscan.TRXTRC10TransferMiddleware`.
- **`start_timestamp`**: (**optional**) The starting timestamp for data searching.
  If not specified, the spider will start from the timestamp of the first block.
- **`end_timestamp`**: (**optional**) The ending timestamp for data searching.
  If not specified, the spider will search the data until now.
- **`max_pages`**: (**optional**) Maximum number of money transfer pages per middleware request for an address. Default
  is `20`.
- **`max_page_size`**: (**optional**) Maximum number of money transfers per page (<=50). Default is `50`.

## Available middlewares

The spider uses several middlewares to handle different types of token transfers. Below are the available middlewares
and their functionalities:

- **`BlockchainSpider.middlewares.txs.tronscan.TRXTRC10TransferMiddleware`**: Traces native token (i.e., TRX) transfers
  and TRC10 token transfers from transaction data.
- **`BlockchainSpider.middlewares.txs.tronscan.TRC20TRC721TransferMiddleware`**: Traces TRC-20 and TRC-721 token
  transfers.
