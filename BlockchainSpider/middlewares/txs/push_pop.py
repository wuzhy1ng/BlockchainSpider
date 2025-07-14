from typing import List, Tuple

import scrapy

from BlockchainSpider.items import SyncItem
from BlockchainSpider.items.subgraph import AccountTransferItem, PopItem, UTXOTransferItem
from BlockchainSpider.middlewares.defs import LogMiddleware


def adapt_push_item(item: SyncItem) -> Tuple[str, List]:
    node, data = item['key'], item['data']
    edges = list()

    # adapt to account transfers
    if data.get(AccountTransferItem.__name__):
        for transfer in data[AccountTransferItem.__name__]:
            token_identity = [
                transfer['symbol'],
                transfer['contract_address']
            ]
            if transfer['token_id'] != '':
                token_identity.append(transfer['token_id'])
            edge = {key: transfer[key] for key in transfer.fields}
            edge['from'] = transfer['address_from']
            edge['to'] = transfer['address_to']
            edge['timeStamp'] = transfer['timestamp']
            edge['symbol'] = '_'.join(token_identity)
            edges.append(edge)

    # adapt to utxo transfers
    if data.get(UTXOTransferItem.__name__):
        for transfer in data[UTXOTransferItem.__name__]:
            if not transfer['is_spent']:
                continue
            edge = {key: transfer[key] for key in transfer.fields}
            edge['from'] = transfer['tx_from']
            edge['to'] = transfer['tx_to']
            edge['timeStamp'] = transfer['timestamp']
            edge['symbol'] = ''
            edges.append(edge)
    return node, edges


class PushAdapterMiddleware(LogMiddleware):
    SIGNAL_URL = 'dummy://push.signal'

    def __init__(self):
        self.context_pop_items = dict()  # node -> PopItem

    async def process_spider_output(self, response, result, spider):
        async for item in result:
            yield item
            # push transfer edges into the strategy
            if isinstance(item, SyncItem):
                node, edges = adapt_push_item(item)
                pop_item = self.context_pop_items.pop(node)
                yield scrapy.Request(
                    url=self.SIGNAL_URL,
                    cb_kwargs={
                        'node': node, 'edges': edges,
                        'context': pop_item.get_context_kwargs()
                    },
                    callback=spider.push_pop,
                    dont_filter=True,
                )
                continue
            # cache pop item context
            if isinstance(item, PopItem):
                node = item['node']
                self.context_pop_items[node] = item
                continue


class PushDownloadMiddleware:
    def process_request(self, request, spider):
        if request.url != PushAdapterMiddleware.SIGNAL_URL:
            return None
        return scrapy.http.Response(
            url=request.url,
            request=request,
        )
