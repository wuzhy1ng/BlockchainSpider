# OFAC

Launch the following command in the console to crawl the labels from OFAC.

```shell
scrapy crawl labels.ofac -a out=/path/to/output/data
```

the argument for OFAC label spider including:

- **out**: the output directory, default is `./data`.