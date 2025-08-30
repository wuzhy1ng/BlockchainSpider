# EVM-compatible chains

BlockchainSpider provides a spider to collect transaction data from EVM-compatible chains, such as Ethereum, BNBChain, Polygon, etc.
You can find all EVM-compatible chains in [chainlist.org](https://chainlist.org/).

## Collect by block number

To collect blockchain data by block number, use the following command:

```shell
scrapy crawl trans.block.evm \
-a providers=https://eth.llamarpc.com \
-a start_blk=19000000 \
-a end_blk=19000100 \
-a out=/path/to/your/data \
-a enable=BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware,BlockchainSpider.middlewares.trans.TokenTransferMiddleware
```

Another example to listen the latest transactions in Ethereum:
```shell
scrapy crawl trans.block.evm \
-a providers=https://eth.llamarpc.com \
-a out=/path/to/your/data \
-a enable=BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware,BlockchainSpider.middlewares.trans.TokenTransferMiddleware
```

**Parameters**:

- `providers`: The RPC providers URL for accessing the EVM-compatible blockchain. If you have multiple providers, join them with commas.
It is recommended that you build your own blockchain nodes,
or get providers from blockchain data services, e.g., [alchemy](https://www.alchemy.com/), [chainnodes](https://chainnodes.org/), etc.
- `start_blk`: (**optional**) The starting block number for data collection. If not specified, it will start from the latest block.
- `end_blk`: (**optional**) The ending block number for data collection, if not specified, it will continuously listen and parse the latest block data.
- `out`: (**optional**) The output directory for storing the collected data. The default is `./data`.
- `enable`: (**optional**) Specifies middlewares to activate during the spider run. 
Note that different middlewares may product different items, e.g., receipts, logs, and traces.
If you enable multiple middlewares, join them with commas.
Please refer to the [available middlewares](#available_middlewares) for more details.

## Collect by transaction hash

To collect blockchain data by transaction hash, use the following command:

```shell
scrapy crawl trans.evm \
-a providers=https://eth.llamarpc.com \
-a hash=0xyour...txhash \ 
-a out=/path/to/your/data \
-a enable=BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware,BlockchainSpider.middlewares.trans.TokenTransferMiddleware
```

**Parameters**:

- `providers`: The RPC providers URL for accessing the EVM-compatible blockchain. If you have multiple providers, join them with commas.
It is recommended that you build your own blockchain nodes,
or get providers from blockchain data services, e.g., [alchemy](https://www.alchemy.com/), [chainnodes](https://chainnodes.org/), etc.
- `hash`: The transaction hash for data collection. If you have multiple hashes, join them with commas.
- `out`: (**optional**) The output directory for storing the collected data. The default is `./data`.
- `enable`: (**optional**) Specifies middlewares to activate during the spider run. 
Note that different middlewares may product different items, e.g., receipts, logs, and traces.
If you enable multiple middlewares, join them with commas.
Please refer to the [available middlewares](#available_middlewares) for more details.

<span id="available_middlewares"></span>
## Available middlewares
BlockchainSpider provides several middlewares to collect different types of data:

- **BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware**:
collect transaction receipts when transaction spiders running.
- **BlockchainSpider.middlewares.trans.TokenTransferMiddleware**:
parse (ERC20, ERC721, and ERC1155) token transfer when transaction 
spiders running. Note that this middleware is available if `BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware`
is enabled at the same time. Enabling this middleware alone will not any effect.
- **BlockchainSpider.middlewares.trans.TokenPropertyMiddleware**:
parse the token name, decimals, and other ERC token properties when transaction 
spiders running. Note that this middleware is available if
`BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware` and 
`BlockchainSpider.middlewares.trans.TokenTransferMiddleware`
are enabled at the same time. Enabling this middleware alone will not any effect.
- **BlockchainSpider.middlewares.trans.MetadataMiddleware**:
Collects NFT metadata during the spider run.
- **BlockchainSpider.middlewares.trans.TraceMiddleware**:
Collects transaction call traces during the spider run.
- **BlockchainSpider.middlewares.trans.ContractMiddleware**:
Extract the contract bytecode if the collected block contains a contract creation transaction.
Note that this middleware requires `BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware` to be enabled simultaneously.
- **BlockchainSpider.middlewares.trans.DCFGMiddleware**:
Collects dynamic control flow graph (DCFG) data during the spider run.
If you are not familiar with DCFG, please refer to the Appendix in this [paper](https://dl.acm.org/doi/pdf/10.1145/3696410.3714928) for more details.

💡 All of collected data are defined in [BlockchainSpider/items/evm.py](https://github.com/wuzhy1ng/BlockchainSpider/blob/master/BlockchainSpider/items/evm.py), 
and you can find the corresponding data structure there.