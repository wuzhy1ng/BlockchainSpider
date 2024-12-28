import asyncio
import json
from typing import Dict, List

import aio_pika


def dict_serialize(item: Dict):
    if not getattr(item, 'keys', None):
        return item

    result = dict()
    for key in item.keys():
        value = item[key]
        if isinstance(value, List):
            for i in range(len(value)):
                value[i] = dict_serialize(value[i])
        elif isinstance(value, Dict):
            value = dict_serialize(value)
        result[key] = value
    return result


class RabbitMQPipeline:
    def open_spider(self, spider):
        self.rabbit_uri = spider.__dict__.get('rabbit_uri')
        self.rabbit_exchange = spider.__dict__.get('rabbit_exchange')
        self.rabbit_routing_prefix = spider.__dict__.get('rabbit_routing_prefix')
        self._loop = asyncio.get_event_loop()
        self._loop.run_until_complete(self.init_rabbit())

    async def init_rabbit(self):
        print('Building connection to RabbitMQ: {}'.format(self.rabbit_uri))
        self._conn = await aio_pika.connect_robust(self.rabbit_uri)
        self._chan = await self._conn.channel()
        self._exchange = await self._chan.declare_exchange(
            name=self.rabbit_exchange,
            durable=True,
        )

    async def process_item(self, item, spider):
        item_dict = dict_serialize(item)
        body = json.dumps(item_dict)
        message = aio_pika.Message(
            body=body.encode(),
            delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT,
        )
        routing_key = '%s.%s' % (self.rabbit_routing_prefix, item.__class__.__name__)
        await self._exchange.publish(
            message=message,
            routing_key=routing_key,
        )

    def close_spider(self, spider):
        task = self._conn.close()
        self._loop.create_task(task)
