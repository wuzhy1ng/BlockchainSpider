import csv
import io
import os

from pybloom import ScalableBloomFilter

from BlockchainSpider.items import SignatureItem, TransactionsItem
from BlockchainSpider.items.evm import BlockItem, TransactionItem, EventLogItem, TraceItem, ContractItem, \
    Token721TransferItem, Token20TransferItem, Token1155TransferItem, TokenApprovalItem, TokenApprovalAllItem, \
    TokenPropertyItem, NFTMetadataItem, TransactionReceiptItem, DCFGBlockItem, DCFGEdgeItem
from BlockchainSpider.items.solana import SolanaBlockItem, SolanaTransactionItem, SolanaInstructionItem, \
    SolanaLogItem, SolanaBalanceChangesItem, SPLTokenActionItem, ValidateVotingItem, SPLMemoItem
from BlockchainSpider.pipelines.sync import unpacked_sync_item


class EVMTrans2csvPipeline:
    def __init__(self):
        self.filename2file = dict()
        self.filename2writer = dict()
        self.filename2headers = dict()
        self.accepted_item_cls = {
            cls.__name__: True for cls in [
                BlockItem, TransactionItem, TransactionReceiptItem,
                EventLogItem, TraceItem, ContractItem,
                Token721TransferItem, Token20TransferItem, Token1155TransferItem,
                TokenApprovalItem, TokenApprovalAllItem,
                TokenPropertyItem, NFTMetadataItem,
                DCFGBlockItem, DCFGEdgeItem
            ]
        }
        self.deduplicate_item_cls = {
            TokenPropertyItem.__name__: 'contract_address',
        }
        self._cls4bloom = {
            cls_name: ScalableBloomFilter(
                initial_capacity=1024,
                error_rate=1e-4,
                mode=ScalableBloomFilter.SMALL_SET_GROWTH,
            ) for cls_name in self.deduplicate_item_cls.keys()
        }
        self.out_dir = None

    def open_spider(self, spider):
        self.out_dir = getattr(spider, 'out_dir')
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)

    @unpacked_sync_item
    def process_item(self, item, spider):
        if self.out_dir is None:
            return item

        # check the item is accepted
        cls_name = item.__class__.__name__
        if self.accepted_item_cls.get(cls_name) is None:
            return item

        # deduplicate items using bloom filter
        if self.deduplicate_item_cls.get(cls_name):
            bloom = self._cls4bloom[cls_name]
            field = self.deduplicate_item_cls[cls_name]
            if item[field] in bloom:
                return item
            bloom.add(item[field])

        # init output file
        fn = os.path.join(self.out_dir, '%s.csv' % cls_name)
        if not self.filename2file.get(fn):
            file = open(fn, 'w', encoding='utf-8', newline='\n', buffering=io.DEFAULT_BUFFER_SIZE)
            self.filename2file[fn] = file

            # init headers
            headers = sorted(item.keys())
            self.filename2headers[fn] = headers

            # init writer
            writer = csv.writer(file)
            writer.writerow(headers)
            self.filename2writer[fn] = writer

        # save to file cache
        self.filename2writer[fn].writerow([
            item[k] for k in self.filename2headers[fn]
        ])
        return item

    def close_spider(self, spider):
        for file in self.filename2file.values():
            file.flush()
            file.close()


class SolanaTrans2csvPipeline(EVMTrans2csvPipeline):
    def __init__(self):
        super().__init__()
        self.accepted_item_cls = {
            cls.__name__: True for cls in [
                SolanaBlockItem, SolanaTransactionItem,
                SolanaBalanceChangesItem, SolanaLogItem,
                SolanaInstructionItem, SPLTokenActionItem,
                SPLMemoItem, ValidateVotingItem,
            ]
        }


class SolanaSignature2csvPipeline(EVMTrans2csvPipeline):
    def __init__(self):
        super().__init__()
        self.accepted_item_cls = {
            cls.__name__: True for cls in [
                SignatureItem, TransactionsItem,
            ]
        }
