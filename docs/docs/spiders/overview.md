# Overview

BlockchainSpider provides three kinds of spiders, i.e.,
transaction subgraph spiders, block spiders, and label spiders.

1. **Transfer subgraph spiders:**
   Given a specific address, transfer subgraph spiders collect (multi-hop)
   assets transfers data from <u>blockchain browser APIs, e.g., Blockscan, Tronscan.</u>
   The collected transfer data can be used to reveal the money flow for the interesting addresses on chain.

2. **Transaction spiders:**
   This kind of spider aims to construct the ETL (aka. Extra-Transform-Load)
   workflow for on-chain blocks/transactions.
   Transaction spiders rely on <u>RPC APIs of blockchain data providers.</u>
   The most popular usage is collecting transaction data, e.g., receipts, logs, trace, etc.

3. **Label spiders:**
   Label spiders crawl <u>some targeted sites</u>, scan the APIs or front-end files,
   and then collect the labels about on-chain addresses or transactions. 