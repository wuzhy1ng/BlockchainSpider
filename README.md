![](http://120.78.210.226:8000/logo.jpg)

# BlockchainSpider

Blockchain spiders aim to collect data of public chains, including:

- **Transaction subgraph**: the subgraph with a center of specific address
- **Label data**: the labels of address or transaction
- **Block data**: the blocks on chains (TODO)
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

In this section, we will demonstrate how to collect labeled addresses in OFAC sanctions list!

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
