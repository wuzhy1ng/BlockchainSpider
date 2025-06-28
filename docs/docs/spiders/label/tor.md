# Tor

The Tor label spider allows you to crawl the Tor network for cryptocurrency labels (e.g., address, transaction hash). 
Before crawling the label on Tor, **please ensure that Tor (port: 9150) is available in your host**.
Tor is a network solution for anonymizing communications on the internet.
Therefore, there are a lot of illegal activities using cryptocurrency for transactions in the Tor network.

Launch the following command in the console to crawl the labels from the Tor network.

```shell
scrapy crawl labels.tor \
-a out=/path/to/output/data \
-a source=http://6nhmgdpnyoljh5uzr5kwlatx2u3diou4ldeommfxjz3wkhalzgjqxzqd.onion
```

the argument for the Tor label spider, including:

- **out**: the output directory, default is `./data`.
- **source**: the source site (.onion) for crawling the tor network.