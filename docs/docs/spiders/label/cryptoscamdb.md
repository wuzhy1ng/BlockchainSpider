# CryptoScamsDB

Launch the following command in the console to crawl the labels from CryptoScamDB.

```shell
scrapy crawl labels.cryptoscamdb -a out=/path/to/output/data
```

the argument for CryptoScamDB label spider including:

- **out**: the output directory, default is `./data`.