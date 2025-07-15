from BlockchainSpider.items import SyncItem


def unpacked_sync_item(func):
    def wrapper(self, item, spider):
        if not isinstance(item, SyncItem):
            return func(self, item, spider)

        # process and filter out the sync data
        sync_key, sync_data = item['key'], item['data']
        pipline_data = dict()
        for key in sync_data.keys():
            reserved_items = list()
            for item in sync_data[key]:
                rlt = func(self, item, spider)
                if rlt is not None:
                    reserved_items.append(rlt)
            pipline_data[key] = reserved_items
        return SyncItem(key=sync_key, data=pipline_data)

    return wrapper
