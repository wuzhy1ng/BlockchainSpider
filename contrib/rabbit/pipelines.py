import asyncio
import json

import aio_pika


class RabbitMQPipeline:
    def open_spider(self, spider):
        print('Building connection to RabbitMQ: {}'.format(
            spider.__dict__.get('rabbit_uri')
        ))
        task = aio_pika.connect(spider.__dict__.get('rabbit_uri'))
        self._conn = asyncio.get_event_loop().run_until_complete(task)
        task = self._conn.channel()
        self._chan = asyncio.get_event_loop().run_until_complete(task)
        task = self._chan.declare_exchange(
            name=spider.__dict__.get('rabbit_exchange'),
            durable=True,
        )
        self._exchange = asyncio.get_event_loop().run_until_complete(task)

    async def process_item(self, item, spider):
        body = json.dumps(dict(item))
        message = aio_pika.Message(
            body=body.encode(),
            delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT,
        )
        mq_routing_key = item.__class__.__name__
        await self._exchange.publish(
            message=message,
            routing_key=mq_routing_key,
        )

    def close_spider(self, spider):
        self._conn.close()
