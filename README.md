# BlockchainSpider
![](https://img.shields.io/badge/Python-3.8~3.10-blue
)
![](https://img.shields.io/badge/license-MIT-green
)

Blockchain spiders aim to collect on-chain data, including:

- **Transfer subgraph**: the money flow with a center of specific address/transaction.
- **Transaction**: the transaction data on chains, e.g., receipts, logs, trace, etc.
- **Label data**: the labels of address/transaction.
- ...

For more info in detail, see our [documentation](https://wuzhy1ng.github.io/blockchainspider).


## 🚀Getting Started

### 🔧Install

Let's start with the following command:
```shell
git clone https://github.com/wuzhy1ng/BlockchainSpider.git
```
And then install the dependencies:

```shell
pip install -r requirements.txt
```


### 🔍Crawl a transaction subgraph

We demonstrate how to crawl a transaction subgraph of [KuCoin hacker](https://etherscan.io/address/0xeb31973e0febf3e3d7058234a5ebbae1ab4b8c23) on Ethereum and trace the illegal fund of the hacker!

Run on this command as follow:

```shell
scrapy crawl txs.blockscan -a source=0xeb31973e0febf3e3d7058234a5ebbae1ab4b8c23 -a apikeys=7MM6JYY49WZBXSYFDPYQ3V7V3EMZWE4KJK -a endpoint=https://api.etherscan.io/v2/api?chainid=1
```

You can find the money transfer data on `./data/AccountTransferItem.csv`. 

### ✨Collect transaction data

In this section, we will demonstrate how to collect transaction data.

The following command will continuously collect transactions in [Ethereum](https://ethereum.org/) from block number `19000000` to `19000100`:
```shell
scrapy crawl trans.block.evm -a start_blk=19000000 -a end_blk=19000100 -a providers=https://eth.llamarpc.com
```

Another example to listen the latest transactions in Ethereum:
```shell
scrapy crawl trans.block.evm -a providers=https://eth.llamarpc.com
```

You can find the label data on `./data`, in which:
- `BlockItem.csv` saves the metadata for blocks, such as minter, timestamp and so on.
- `TransactionItem.csv` saves the external transactions of blocks.

> BlockchainSpider also supports collecting transaction receipts, logs, token transfers, etc. 
> Moreover, collecting block data from EVM-compatible chains (e.g., BNBChain, Polygon, etc.) is also available; 
> see our [documentation](https://wuzhy1ng.github.io/blockchainspider/spiders/transaction/evm/).

The following command will continuously collect transaction data in [Solana](https://solana.com) from block height `270000000` to `270001000`:
```shell
scrapy crawl trans.block.solana -a start_slot=270000000 -a end_slot=270001000 -a providers=https://solana-mainnet.g.alchemy.com/v2/UOD8HE4CVqEiDY5E_9XbKDFqYZzJE3XP
```

Another example to listen the latest transactions in Solana:
```shell
scrapy crawl trans.block.solana -a providers=https://solana-mainnet.g.alchemy.com/v2/UOD8HE4CVqEiDY5E_9XbKDFqYZzJE3XP
```

### 💡Collect label data

In this section, we demonstrate how to collect labeled addresses in darknet!

Run this command as follow:

```shell
scrapy crawl labels.tor -a source=http://6nhmgdpnyoljh5uzr5kwlatx2u3diou4ldeommfxjz3wkhalzgjqxzqd.onion
```

You can find the label data on `./data/LabelReportItem`, each row of this file is a json object.


## Reference
The following paper supports `BlockchainSpider`. Here are the bib references:

```latex
@article{tracer23wu,
    author={Wu, Zhiying and Liu, Jieli and Wu, Jiajing and Zheng, Zibin and Chen, Ting},
    journal={IEEE Transactions on Information Forensics and Security}, 
    title={TRacer: Scalable Graph-Based Transaction Tracing for Account-Based Blockchain Trading Systems}, 
    year={2023},
    volume={18},
    number={},
    pages={2609-2621}
}
@inproceedings{mots23wu,
    author = {Wu, Zhiying and Liu, Jieli and Wu, Jiajing and Zheng, Zibin and Luo, Xiapu and Chen, Ting},
    title = {Know Your Transactions: Real-time and Generic Transaction Semantic Representation on Blockchain \& Web3 Ecosystem},
    year = {2023},
    publisher = {Association for Computing Machinery},
    address = {Austin, TX, USA},
    doi = {10.1145/3543507.3583537},
    pages = {1918–1927},
    numpages = {10},
    series = {WWW '23}
}
```

## 🔬About TRacer
Please refer to the [old version](https://github.com/wuzhy1ng/BlockchainSpider/blob/16d833d7237b2a55ec9c2569eee8ead13de16dfa/test/README.md) of this project.
