# BlockchainSpider

Blockchain spiders aim to collect data of public chains, including:

- **Transaction subgraph**: the subgraph with a center of specific address
- **Label data**: the labels of address or transaction
- **Block data**: the blocks on chains
- ...

For more info in detail, see our [documentation](https://870167019.gitbook.io/blockchainspider/).


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

We will demonstrate how to crawl a transaction subgraph of [KuCoin hacker](https://etherscan.io/address/0xeb31973e0febf3e3d7058234a5ebbae1ab4b8c23) on Ethereum and trace the illegal fund of the hacker!

Run on this command as follow:

```shell
scrapy crawl txs.eth.ttr -a source=0xeb31973e0febf3e3d7058234a5ebbae1ab4b8c23
```

You can find the transaction data on `./data/0xeb3...c23.csv` on finished. 

Try to import the transaction data and the importance of the addresses in the subgraph `./data/importance/0xeb3...c23.csv` to [Gephi](https://gephi.org/).



### 💡Collect label data

In this section, we will demonstrate how to collect labeled addresses in [OFAC sanctions list](https://home.treasury.gov/policy-issues/financial-sanctions/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists)!

Run this command as follow:

```shell	
scrapy crawl labels.ofac
```

You can find the label data on `./data/labels.ofac`, each row of this file is a json object just like this:

```json
{
    "net":"ETH",
    "label":"Entity",
    "info":{
        "uid":"30518",
        "address":"0x72a5843cc08275C8171E582972Aa4fDa8C397B2A",
        "first_name":null,
        "last_name":"SECONDEYE SOLUTION",
        "identities":[
            {
                "id_type":"Email Address",
                "id_number":"support@secondeyesolution.com"
            },
            {
                "id_type":"Email Address",
                "id_number":"info@forwarderz.com"
            }
        ]
    }
}
```

**Note**: Please indicate the source when using crawling labels.

### ✨Collect transaction data

In this section, we will demonstrate how to collect transaction data in [Ethereum](https://ethereum.org/)!

The following command will continuously collect transactions from block number `19000000` to the latest block:
```shell
scrapy crawl trans.block.evm -a start_blk=19000000 -a providers=https://freerpc.merkle.io
```

You can find the label data on `./data`, in which:
- `BlockItem.csv` saves the metadata for blocks, such as minter, timestamp and so on.
- `TransactionItem.csv` saves the external transactions of blocks.

> BlockchainSpider also supports collecting transaction receipts, logs, token transfers, etc. 
> Moreover, collecting block data from EVM-compatible chains (e.g., BNBChain, Polygon, etc.) is also available; 
> see our [documentation](https://870167019.gitbook.io/blockchainspider/transaction-spiders/overview).

(Solana support, alpha) The following command will continuously collect transaction data from block height `270000000` to the latest block:
```shell
scrapy crawl trans.block.solana -a start_blk=270000000 -a providers=<your http provider>
```

## 🏷️Citation
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
    address = {New York, NY, USA},
    doi = {10.1145/3543507.3583537},
    pages = {1918–1927},
    numpages = {10},
    series = {WWW '23}
}
```

## 🔬About TRacer
Please execute the code in `./test` to reproduce the experimental results in the paper.

- `parameters.py`: Parameter sensitivity experiment.
- `compare.py`: Comparative experiment.
- `metrics.py`: Export evaluation metrics.

For more information, please refer to `./test/README.md`
