import asyncio
import json

import aio_pika


class RabbitMQPipeline:
    def open_spider(self, spider):
        print('Building connection to RabbitMQ: {}'.format(
            spider.__dict__.get('rabbit_uri')
        ))
        task = aio_pika.connect_robust(spider.__dict__.get('rabbit_uri'))
        self._conn = asyncio.get_event_loop().run_until_complete(task)
        task = self._conn.channel()
        self._chan = asyncio.get_event_loop().run_until_complete(task)
        task = self._chan.declare_exchange(
            name=spider.__dict__.get('rabbit_exchange'),
            durable=True,
        )
        self._exchange = asyncio.get_event_loop().run_until_complete(task)
        self._routing_prefix = spider.__dict__.get('rabbit_routing_prefix')

    async def process_item(self, item, spider):
        body = json.dumps(dict(item))
        message = aio_pika.Message(
            body=body.encode(),
            delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT,
        )
        routing_key = '%s.%s' % (self._routing_prefix, item.__class__.__name__)
        await self._exchange.publish(
            message=message,
            routing_key=routing_key,
        )

    def close_spider(self, spider):
        task = self._conn.close()
        asyncio.get_event_loop().run_until_complete(task)
