import asyncio
import json
from typing import Dict, List

import aio_pika


class RabbitMQPipeline:
    def open_spider(self, spider):
        self.inited = False
        self.rabbit_uri = spider.__dict__.get('rabbit_uri')
        self.rabbit_exchange = spider.__dict__.get('rabbit_exchange')
        self.rabbit_routing_prefix = spider.__dict__.get('rabbit_routing_prefix')

    async def init_rabbit(self):
        print('Building connection to RabbitMQ: {}'.format(self.rabbit_uri))
        self._conn = await aio_pika.connect_robust(self.rabbit_uri)
        self._chan = await self._conn.channel()
        self._exchange = await self._chan.declare_exchange(
            name=self.rabbit_exchange,
            durable=True,
        )

    async def process_item(self, item, spider):
        if not self.inited:
            await self.init_rabbit()
            self.inited = True
        item_dict = self.dict_serialize(item)
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

    def dict_serialize(self, item: Dict):
        if not getattr(item, 'keys', None):
            return item

        result = dict()
        for key in item.keys():
            value = item[key]
            if isinstance(value, List):
                for i in range(len(value)):
                    value[i] = self.dict_serialize(value[i])
            elif isinstance(value, Dict):
                value = self.dict_serialize(value)
            result[key] = value
        return result

    def close_spider(self, spider):
        task = self._conn.close()
        asyncio.get_event_loop().run_until_complete(task)
