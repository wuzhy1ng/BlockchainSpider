![](http://120.78.210.226:8000/logo.jpg)

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
pip install scrapy
pip install selenium
pip install networkx
```

For more information, please refer to the document in `./docs/html/index.html`.



### 🔍Crawl a transaction subgraph

We will demonstrate how to crawl a transaction subgraph of [KuCoin hacker](https://etherscan.io/address/0xeb31973e0febf3e3d7058234a5ebbae1ab4b8c23) on Ethereum and trace the illegal fund of the hacker!

Run on this command as follow:

```shell
scrapy crawl txs.eth.ttr -a source=0xeb31973e0febf3e3d7058234a5ebbae1ab4b8c23
```

You can find the transaction data on `./data/0xeb3...c23.csv` on finished. 

Try to import the transaction data and the importance of the addresses in the subgraph `./data/importance/0xeb3...c23.csv` to [Gephi](https://gephi.org/).

![](http://120.78.210.226:8000/readme_kucoin.png)

The hacker is related to Tornado Cash, a mixing server, it shows that the hacker took part in money laundering! 



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

### 🧱Collect block data

In this section, we will demonstrate how to collect block data in [Ethereum](https://ethereum.org/)!

Run this command as follow:
```shell
scrapy crawl blocks.eth
```

You can find the label data on `./data`, in which:
- `blocks.eth.meta` saves the metadata for blocks, such as minter, timestamp and so on.
- `blocks.eth.external` saves the external transactions of blocks.

Each row of those files is a JSON object just like this:
```json
{
    "difficulty":"0x400000000",
    "extraData":"0x11bbe8db4e347b4e8c937c1c8370e4b5ed33adb3db69cbdb7a38e1e50b1b82fa",
    "gasLimit":"0x1388",
    "gasUsed":"0x0",
    "hash":"0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3",
    "logsBloom":"0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "miner":"0x0000000000000000000000000000000000000000",
    "mixHash":"0x0000000000000000000000000000000000000000000000000000000000000000",
    "nonce":"0x0000000000000042",
    "number":"0x0",
    "parentHash":"0x0000000000000000000000000000000000000000000000000000000000000000",
    "receiptsRoot":"0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
    "sha3Uncles":"0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
    "size":"0x21c",
    "stateRoot":"0xd7f8974fb5ac78d9ac099b9ad5018bedc2ce0a72dad1827a1709da30580f0544",
    "timestamp":"0x0",
    "totalDifficulty":"0x400000000",
    "transactionsRoot":"0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
    "uncles":[
    ]
}
```

## ❗Important tips
If you want to get the best performance of Blockchainspider, 
please read the settings of [APIKeys](https://870167019.gitbook.io/blockchainspider/settings/apikeys) and [Cache](https://870167019.gitbook.io/blockchainspider/settings/cache).

## 🔬About TRacer

Please cite our [paper](https://arxiv.org/abs/2201.05757) (and the respective papers of the methods used) if you use this code in your own work:

```latex
@misc{wu2022tracer,
      title={TRacer: Scalable Graph-based Transaction Tracing for Account-based Blockchain Trading Systems}, 
      author={Zhiying Wu and Jieli Liu and Jiajing Wu and Zibin Zheng},
      year={2022},
      eprint={2201.05757},
      archivePrefix={arXiv},
      primaryClass={cs.CR}
}
```

Please execute the code in `./test` to reproduce the experimental results in the paper.

- `parameters.py`: Parameter sensitivity experiment.
- `compare.py`: Comparative experiment.
- `metrics.py`: Export evaluation metrics.

For more information, please refer to `./test/README.md`
