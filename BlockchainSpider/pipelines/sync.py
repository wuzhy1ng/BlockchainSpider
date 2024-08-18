from BlockchainSpider.items import SyncItem


def unpacked_sync_item(func):
    def wrapper(self, item: SyncItem, spider):
        for sync_items in item['data'].values():
            for sync_item in sync_items:
                func(self, sync_item, spider)
        func(self, item, spider)
        return item

    return wrapper
