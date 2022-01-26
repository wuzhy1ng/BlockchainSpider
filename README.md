# BlockchainSpider
Blockchain spiders aim to collect data of public chains, including:

- **Label data**: the labels of address or transaction
- **Transaction subgraph**: the subgraph with a center of specific address
- **Block data**: the blocks on chains (TODO)
- ...



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

That 's great! In this section, we will demonstrate how to crawl a transaction subgraph of [KuCoin hacker](https://etherscan.io/address/0xeb31973e0febf3e3d7058234a5ebbae1ab4b8c23) on Ethereum and trace the illegal fund of the hacker!

Run on this command as follow:

```shell
scrapy crawl txs.eth.ttr -a source=0xeb31973e0febf3e3d7058234a5ebbae1ab4b8c23
```

You can find the transaction data on `./data/0xeb3...c23.csv` on finished. 

Try to import the transaction data and the importance of the addresses in the subgraph `./data/importance/0xeb3...c23.csv` to [Gephi](https://gephi.org/).



The hacker is related to Tornado.Cash, a mixing server, it shows that the hacker took part in money laundering! 



### 💡Collect label data

In this section, we will demonstrate how to collect labeled addresses in OFAC sanctions list!

Run on this command as follow:

```shell	
scrapy crawl labels.ofac
```

You can find the label data on `./data/labels.ofac`, each row of this file is a json object just like this:

```json

```

**Note**: Please indicate the source when using crawling labels.



## 📖Document

For more usage and configuration information, consult the documentation.



## 🔬Experiments

We designed the experimental code for different subgraph sampling strategies.

Please execute the code in `./test` to reproduce the experimental results.

- `parameters.py`: Parameter sensitivity experiment.
- `compare.py`: Comparative experiment.
- `metrics.py`: Export evaluation metrics.