from enum import Enum


class ETHDataTypes(Enum):
    META = 'meta'
    EXTERNAL = 'external'
    INTERNAL = 'internal'
    ERC20 = 'erc20'
    ERC721 = 'erc721'
    ERC1155 = 'erc1155'
    LOG = 'logs'
    TOKEN = 'token'

    @staticmethod
    def has(item):
        items = ETHDataTypes.__dict__['_member_map_']
        items = {_item.value for _item in items.values()}
        return item in items