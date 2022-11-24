import scrapy


class BlockNumberItem(scrapy.Item):
    block_number = scrapy.Field()  # int


class BlockMetaItem(scrapy.Item):
    block_hash = scrapy.Field()  # str
    block_number = scrapy.Field()  # int
    parent_hash = scrapy.Field()  # str
    difficulty = scrapy.Field()  # int
    total_difficulty = scrapy.Field()  # int
    size = scrapy.Field()  # int
    transaction_count = scrapy.Field()  # int
    gas_limit = scrapy.Field()  # int
    gas_used = scrapy.Field()  # int
    miner = scrapy.Field()  # str
    receipts_root = scrapy.Field()  # str
    timestamp = scrapy.Field()  # int
    logs_bloom = scrapy.Field()  # str
    nonce = scrapy.Field()  # int


class ExternalTransactionItem(scrapy.Item):
    transaction_hash = scrapy.Field()  # str
    transaction_index = scrapy.Field()  # int
    block_hash = scrapy.Field()  # str
    block_number = scrapy.Field()  # int
    address_from = scrapy.Field()  # str
    address_to = scrapy.Field()  # str
    is_create_contract = scrapy.Field()  # bool
    value = scrapy.Field()  # int
    gas = scrapy.Field()  # int
    gas_price = scrapy.Field()  # int
    timestamp = scrapy.Field()  # int
    nonce = scrapy.Field()  # int
    input = scrapy.Field()  # str


class InternalTransactionItem(scrapy.Item):
    transaction_hash = scrapy.Field()  # str
    transaction_position = scrapy.Field()  # int
    trace_type = scrapy.Field()  # str
    trace_address = scrapy.Field()  # [int]
    subtraces = scrapy.Field()  # int
    block_number = scrapy.Field()  # int
    address_from = scrapy.Field()  # str
    address_to = scrapy.Field()  # str
    value = scrapy.Field()  # int
    gas = scrapy.Field()  # int
    gas_used = scrapy.Field()  # int
    timestamp = scrapy.Field()  # int
    input = scrapy.Field()  # str
    output = scrapy.Field()  # str


class ERC20TokenTransferItem(scrapy.Item):
    transaction_hash = scrapy.Field()  # str
    log_index = scrapy.Field()  # int
    block_number = scrapy.Field()  # int
    timestamp = scrapy.Field()  # int
    address_from = scrapy.Field()  # str
    address_to = scrapy.Field()  # str
    value = scrapy.Field()  # int
    contract_address = scrapy.Field()  # str
    token_symbol = scrapy.Field()  # str
    decimals = scrapy.Field()  # int
    total_supply = scrapy.Field()  # int


class ERC721TokenTransferItem(scrapy.Item):
    transaction_hash = scrapy.Field()  # str
    log_index = scrapy.Field()  # str
    block_number = scrapy.Field()  # int
    timestamp = scrapy.Field()  # int
    address_from = scrapy.Field()  # str
    address_to = scrapy.Field()  # str
    token_id = scrapy.Field()  # int
    contract_address = scrapy.Field()  # str
    token_symbol = scrapy.Field()  # str


class ERC1155TokenTransferItem(scrapy.Item):
    transaction_hash = scrapy.Field()  # str
    log_index = scrapy.Field()  # int
    block_number = scrapy.Field()  # str
    timestamp = scrapy.Field()  # int
    address_operator = scrapy.Field()  # str
    address_from = scrapy.Field()  # str
    address_to = scrapy.Field()  # str
    token_ids = scrapy.Field()  # [int]
    values = scrapy.Field()  # [int]
    contract_address = scrapy.Field()  # str


class LogItem(scrapy.Item):
    transaction_hash = scrapy.Field()  # str
    log_index = scrapy.Field()  # int
    block_number = scrapy.Field()  # str
    timestamp = scrapy.Field()  # int
    address = scrapy.Field()  # str
    topics = scrapy.Field()  # [str]
    data = scrapy.Field()  # str
    removed = scrapy.Field()  # bool


class ERCTokenItem(scrapy.Item):
    address = scrapy.Field()  # str
    is_erc20 = scrapy.Field()  # bool
    is_erc721 = scrapy.Field()  # bool
    is_erc1155 = scrapy.Field()  # bool
    token_symbol = scrapy.Field()  # str
    decimals = scrapy.Field()  # int
    total_supply = scrapy.Field()  # int


class TransactionMotifItem(scrapy.Item):
    transaction_hash = scrapy.Field()  # str
    frequency = scrapy.Field()  # dict
