# RabbitMQ

[RabbitMQ](https://www.rabbitmq.com/) is a reliable message queue.
The RabbitMQ pipeline provides an implementation that imports all BlockchainSpider outputs into RabbitMQ.

To enable this pipeline, you should **first** install the dependencies:
```shell
pip install -r plugins/rabbit/requirements.txt
```

And add the configuration in `BlockchainSpider/settings.py`:
```python
ITEM_PIPELINES = {
    'plugins.rabbit.pipelines.RabbitMQPipeline': 666,
}
```

**Next**, start your spider command with the specific arguments:

- **`rabbit_uri`**: The URI of the RabbitMQ server, e.g., `amqp://guest:guest@localhost:5672`.
- **`rabbit_exchange`**: The RabbitMQ exchange to publish messages to.
- **`rabbit_routing_prefix`**: The **prefix** for the routing key. 
The route key for each kind of item is prefixed with this prefix.

For example, if you want to import all the data generated by `trans.block.evm` into RabbitMQ (localhost:5672),
you can start the following command:
```shell
scrapy crawl trans.block.evm \
-a providers=https://eth.llamarpc.com \
-a start_blk=19000000 \
-a rabbit_uri=amqp://guest:guest@localhost:5672 \
-a rabbit_exchange=BlockchainSpider \
-a rabbit_routing_prefix=trans.block.evm.ethereum
```
Note that the `trans.block.evm` Spider outputs `SyncItem`. 
If you wish to receive `SyncItem` via RabbitMQ,
then you need to listen to the BlockchainSpider exchange, with the routing key: `trans.block.evm.ethereum.SyncItem`.