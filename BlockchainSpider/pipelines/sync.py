from BlockchainSpider.items import SyncItem


def unpacked_sync_item(func):
    def wrapper(self, item, spider):
        if not isinstance(item, SyncItem):
            return func(self, item, spider)
        for sync_items in item['data'].values():
            for sync_item in sync_items:
                func(self, sync_item, spider)
        return item

    return wrapper
