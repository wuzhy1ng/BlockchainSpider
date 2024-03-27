import json
import os

from BlockchainSpider.items import ABIItem


class ABIPipeline:
    def process_item(self, item, spider):
        if spider.out_dir is None or not isinstance(item, ABIItem):
            return item

        # write item
        fn = os.path.join(spider.out_dir, '{}.json'.format(item['contract_address']))
        with open(fn, 'w') as f:
            json.dump(item['abi'], f)
        return item
