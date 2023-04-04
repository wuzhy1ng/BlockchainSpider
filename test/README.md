# About TRacer

### Q1: Implementation details of comparison method?

Different methods have different implementations in graph expansion and extracting, see [the design with graph expansion](https://870167019.gitbook.io/blockchainspider/subgraph-spiders/overview) and [the overview of extractors](https://870167019.gitbook.io/blockchainspider/extractors/overview) in documentation.

| methods | graph expansion                     | extract                                   |
| ------- | ----------------------------------- | ----------------------------------------- |
| BFS     | BFS transaction subgraph spider     | Deduplicate extractor                     |
| Poison  | Poison transaction subgraph spider  | Deduplicate extractor                     |
| Haircut | Haircut transaction subgraph spider | Deduplicate extractor                     |
| APPR    | APPR transaction subgraph spider    | Deduplicate and Local community extractor |
| TTR     | TTR transaction subgraph spider     | Deduplicate and Local community extractor |

### Q2: How can I reproduce the relationship among epsilon, recall, and the number of nodes?

Run on the following commands to reproduce:

```shell
BlockchainSpider/test$ python parameters.py -o ./data/epsilons
BlockchainSpider$ python extract.py deduplicate -i ./test/data/epsilons/epsilon_0.1 -o ./test/data/epsilons/epsilon_0.1_de
BlockchainSpider$ python extract.py localcomm -i ./test/data/epsilons/epsilon_0.1_de -o ./test/data/epsilons/epsilon_0.1_lcm
BlockchainSpider$ python extract.py deduplicate -i ./test/data/epsilons/epsilon_0.05 -o ./test/data/epsilons/epsilon_0.05_de
BlockchainSpider$ python extract.py localcomm -i ./test/data/epsilons/epsilon_0.05_de -o ./test/data/epsilons/epsilon_0.05_lcm
......
BlockchainSpider/test$ python epsilons.py \
-i ./data/epsilons/epsilon_0.1_lcm,./data/epsilons/epsilon_0.05_lcm,... \
-x 1e-1,5e-2,...
```



### Q3: How can I reproduce the ablation experiment?

Run on the following commands to reproduce:

```shell
BlockchainSpider/test$ python compare.py -o ./data/ablation -m ttr
BlockchainSpider/test$ python compare.py -o ./data/ablation -m ttr_time
BlockchainSpider$ python extract.py deduplicate -i ./test/data/ablation/all/raw -o ./test/data/ablation/all/deduplicate
BlockchainSpider$ python extract.py localcomm -i ./test/data/ablation/all/deduplicate -o ./test/data/ablation/all/localcomm
BlockchainSpider$ python extract.py deduplicate -i ./test/data/ablation/pattern/raw -o ./test/data/ablation/pattern/deduplicate
BlockchainSpider$ python extract.py localcomm -i ./test/data/ablation/pattern/deduplicate -o ./test/data/ablation/pattern/localcomm
BlockchainSpider/test$ python metrics.py -i ./data/ablation/all/localcomm
BlockchainSpider/test$ python metrics.py -i ./data/ablation/pattern/localcomm
BlockchainSpider/test$ python metrics.py -i ./data/ablation/all/deduplicate
```



### Q4: How can I reproduce the relationship between the top n most relevant nodes and the recall?

Run on the following commands to reproduce:

```shell
BlockchainSpider/test$ python compare.py -o ./data/haircut -m haircut
BlockchainSpider/test$ python compare.py -o ./data/appr -m appr
BlockchainSpider/test$ python compare.py -o ./data/ttr -m ttr
BlockchainSpider$ python extract.py deduplicate -i ./test/data/haircut/raw -o ./test/data/haircut/deduplicate
BlockchainSpider$ python extract.py deduplicate -i ./test/data/appr/raw -o ./test/data/appr/deduplicate
BlockchainSpider$ python extract.py localcomm -i ./test/data/appr/deduplicate -o ./test/data/appr/localcomm
BlockchainSpider$ python extract.py deduplicate -i ./test/data/ttr/raw -o ./test/data/ttr/deduplicate
BlockchainSpider$ python extract.py localcomm -i ./test/data/ttr/deduplicate -o ./test/data/ttr/localcomm
BlockchainSpider/test$ python rank_recall.py -i ./data/haircut/deduplicate,./data/appr/localcomm,./data/ttr/localcomm -l Haircut,APPR,TRacer
```

