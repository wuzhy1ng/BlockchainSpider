from enum import Enum


class ETHDataTypes(Enum):
    META = 'meta'
    TRANSACTION = 'transaction'
    TRACE = 'trace'
    LOG = 'log'
    CONTRACT = 'contract'
    ERC20 = 'erc20'
    ERC721 = 'erc721'
    ERC1155 = 'erc1155'
    APPROVE = 'approve'
    APPROVEALL = 'approveall'
    TOKEN = 'token'
    NFT = 'nft'

    @staticmethod
    def has(item):
        items = ETHDataTypes.__dict__['_member_map_']
        items = {_item.value for _item in items.values()}
        return item in items


class TokenType(Enum):
    TOKEN20 = '20'
    TOKEN721 = '721'
    TOKEN1155 = '1155'

    @staticmethod
    def has(item):
        items = TokenType.__dict__['_member_map_']
        items = {_item.value for _item in items.values()}
        return item in items
