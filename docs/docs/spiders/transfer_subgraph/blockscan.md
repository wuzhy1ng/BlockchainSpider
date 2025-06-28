# Blockscan

The `txs.blockscan` spider is designed to collect transaction data from blockscan explorers like
Etherscan. 
Specifically, `txs.blockscan` aims at searching for the source and destination of funds from a given **address**.

## Usage

To run the spider, use the following command:

```shell
scrapy crawl txs.blockscan \
-a source=0xYourSourceAddress \
-a apikeys=YourApiKey1,YourApiKey2 \
-a endpoint=https://api.etherscan.io/api \
-a strategy=BlockchainSpider.strategies.txs.BFS \
-a allowed_tokens=0xTokenAddress1,0xTokenAddress2 \
-a out=/path/to/your/data \
-a out_fields=hash,address_from,address_to,value,token_id,timestamp,block_number,contract_address,symbol,decimals \
-a enable=BlockchainSpider.middlewares.txs.blockscan.ExternalTransferMiddleware,BlockchainSpider.middlewares.txs.blockscan.Token20TransferMiddleware \
-a start_blk=1000000 \
-a end_blk=1500000 \
-a max_pages=1 \
-a max_page_size=10000
```

**Parameters**

- **`source`**: The source address to start collecting transactions. This parameter is required.
- **`apikeys`**: A comma-separated list of API keys for accessing the blockchain explorer. At least one API key is
  required.
- **`endpoint`**: (**optional**) The API endpoint of the blockchain explorer.
  Default is `https://api.etherscan.io/api`.
  See the [support chains](#support-chains) section for more endpoints.
- **`strategy`**: (**optional**) The traversal strategy for collecting transactions.
  Default is `BlockchainSpider.strategies.txs.BFS` (Breadth-First Search).
  BlockchainSpider implements other advanced strategies, e.g., Poison, APPR, and TTR.
  For more details, please refer to [Transaction tracing](/advance/transaction_tracing/) section.
- **`allowed_tokens`**: (**optional**) A comma-separated list of token contract addresses to filter token transfers.
  If not provided, all tokens are included.
  It should be noted that some strategies (especially TTR methods) may automatically analyze token types and collect
  token transfer records that are different from the given type.
- **`out`**: (**optional**) The output directory for storing the collected data. The default is `./data`.
- **`out_fields`**: (**optional**) A comma-separated list of fields to include in the output.
  the default is
  `address_from,address_to,block_number,contract_address,decimals,gas,gas_price,hash,id,symbol,timestamp,token_id,value`,
  and other fields include `isError`, `input`, and `nonce`.
- **`enable`**: (**optional**) A comma-separated list of middlewares to enable during the spider run.
  Add different middlewares to trace different types of assets.
  See the [available middleware](#available-middlewares) section for details.
  The default is `BlockchainSpider.middlewares.txs.blockscan.ExternalTransferMiddleware`.
- **`start_blk`**: (**optional**) The starting block number for data searching.
  If not specified, the spider will start from the first block.
- **`end_blk`**: (**optional**) The ending block number for data searching.
  If not specified, the spider will search the data until the latest block.
- **`max_pages`**: (**optional**) Maximum number of money transfer pages per middleware request for an address. Default is `1`.
- **`max_page_size`**: (**optional**) Maximum number of money transfers per page (<=10000). Default is `10000`.

<span id="available_middlewares"></span>

## Available middlewares

The spider uses several middlewares to handle different types of token transfers.
Below are the available middlewares and their functionalities:

- **`BlockchainSpider.middlewares.txs.blockscan.ExternalTransferMiddleware`**: Trace external transfers (e.g., ETH
  transfers) from the transaction data.
- **`BlockchainSpider.middlewares.txs.blockscan.InternalTransferMiddleware`**: Trace internal transfers (e.g.,
  contract-to-contract calls) from the transaction data.
- **`BlockchainSpider.middlewares.txs.blockscan.Token20TransferMiddleware`**: Trace ERC-20 token transfers from the
  transaction data.
- **`BlockchainSpider.middlewares.txs.blockscan.Token721TransferMiddleware`**: Trace ERC-721 (NFT) token transfers from
  the transaction data.

<span id="support_chains"></span>

## Support chains

| Chain         | Apply for your apikeys                                     | API Endpoint                                                                       |
|---------------|------------------------------------------------------------|------------------------------------------------------------------------------------|
| Ethereum      | [etherscan.io](https://etherscan.io)                       | [https://api.etherscan.io/api](https://api.etherscan.io/api)                       |
| Ape           | [apescan.io](https://apescan.io)                           | [https://api.apescan.io/api](https://api.apescan.io/api)                           |
| Arbitrum One  | [arbiscan.io](https://arbiscan.io)                         | [https://api.arbiscan.io/api](https://api.arbiscan.io/api)                         |
| Arbitrum Nova | [nova.arbiscan.io](https://nova.arbiscan.io)               | [https://api-nova.arbiscan.io/api](https://api-nova.arbiscan.io/api)               |
| Base          | [basescan.org](https://basescan.org)                       | [https://api.basescan.org/api](https://api.basescan.org/api)                       |
| Bera          | [berascan.com](https://berascan.com)                       | [https://api.berascan.com/api](https://api.berascan.com/api)                       |
| Blast Chain   | [blastscan.io](https://blastscan.io)                       | [https://api.blastscan.io/api](https://api.blastscan.io/api)                       |
| BNB Chain     | [bscscan.com](https://bscscan.com)                         | [https://api.bscscan.com/api](https://api.bscscan.com/api)                         |
| BTTC          | [bttcscan.com](https://bttcscan.com)                       | [https://api.bttcscan.com/api](https://api.bttcscan.com/api)                       |
| Celo          | [celoscan.io](https://celoscan.io)                         | [https://api.celoscan.io/api](https://api.celoscan.io/api)                         |
| Cronos        | [cronoscan.com](https://cronoscan.com)                     | [https://api.cronoscan.com/api](https://api.cronoscan.com/api)                     |
| Frax Chain    | [fraxscan.com](https://fraxscan.com)                       | [https://api.fraxscan.com/api](https://api.fraxscan.com/api)                       |
| Gnosis        | [gnosisscan.io](https://gnosisscan.io)                     | [https://api.gnosisscan.io/api](https://api.gnosisscan.io/api)                     |
| Linea         | [lineascan.build](https://lineascan.build)                 | [https://api.lineascan.build/api](https://api.lineascan.build/api)                 |
| Mantle        | [mantlescan.xyz](https://mantlescan.xyz)                   | [https://api.mantlescan.xyz/api](https://api.mantlescan.xyz/api)                   |
| MemeCore      | [memecorescan.io](https://memecorescan.io)                 | [https://api.memecorescan.io/api](https://api.memecorescan.io/api)                 |
| Moonbeam      | [moonbeam.moonscan.io](https://moonbeam.moonscan.io)       | [https://api-moonbeam.moonscan.io/api](https://api-moonbeam.moonscan.io/api)       |
| Moonriver     | [moonriver.moonscan.io](https://moonriver.moonscan.io)     | [https://api-moonriver.moonscan.io/api](https://api-moonriver.moonscan.io/api)     |
| opBNB         | [opbnb.bscscan.com](https://opbnb.bscscan.com/)            | [https://api-opbnb.bscscan.com/api](https://api-opbnb.bscscan.com/api)             |
| Optimism      | [optimistic.etherscan.io](https://optimistic.etherscan.io) | [https://api-optimistic.etherscan.io/api](https://api-optimistic.etherscan.io/api) |
| Polygon zkEVM | [zkevm.polygonscan.com](https://zkevm.polygonscan.com)     | [https://api-zkevm.polygonscan.com/api](https://api-zkevm.polygonscan.com/api)     |
| Polygon       | [polygonscan.com](https://polygonscan.com)                 | [https://api.polygonscan.com/api](https://api.polygonscan.com/api)                 |
| Scroll        | [scrollscan.com](https://scrollscan.com)                   | [https://api.scrollscan.com/api](https://api.scrollscan.com/api)                   |
| Avax C-Chain  | [snowtrace.io](https://snowtrace.io)                       | [https://api.snowtrace.io/api](https://api.snowtrace.io/api)                       |
| Sonic         | [sonicscan.org](https://sonicscan.org)                     | [https://api.sonicscan.org/api](https://api.sonicscan.org/api)                     |
| Sophon        | [sophscan.xyz](https://sophscan.xyz)                       | [https://api.sophscan.xyz/api](https://api.sophscan.xyz/api)                       |
| Swell Chain   | [swellchainscan.io](https://swellchainscan.io)             | [https://api.swellchainscan.io/api](https://api.swellchainscan.io/api)             |
| Taiko         | [taikoscan.io](https://taikoscan.io)                       | [https://api.taikoscan.io/api](https://api.taikoscan.io/api)                       |
| unichain      | [uniscan.xyz](https://uniscan.xyz)                         | [https://api.uniscan.xyz/api](https://api.uniscan.xyz/api)                         |
| Wemix         | [wemixscan.com](https://wemixscan.com)                     | [https://api.wemixscan.com/api](https://api.wemixscan.com/api)                     |
| World         | [worldscan.org](https://worldscan.org)                     | [https://api.worldscan.org/api](https://api.worldscan.org/api)                     |
| Xai           | [xaiscan.io](https://xaiscan.io)                           | [https://api.xaiscan.io/api](https://api.xaiscan.io/api)                           |
| Xdc           | [xdcscan.io](https://xdcscan.io)                           | [https://api.xdcscan.io/api](https://api.xdcscan.io/api)                           |
| zkSync Era    | [era.zksync.network](https://era.zksync.network)           | [https://api-era.zksync.network/api](https://api-era.zksync.network/api)           |