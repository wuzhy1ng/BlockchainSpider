import binascii

import async_lru
from web3 import Web3

from BlockchainSpider.utils.enum import TokenType
from BlockchainSpider.utils.web3 import web3_json_rpc, parse_bytes_data

ERC20_TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ERC721_TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ERC1155_SINGLE_TRANSFER_TOPIC = '0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62'
ERC1155_BATCH_TRANSFER_TOPIC = '0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb'
TOKEN_APPROVE_TOPIC = '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925'
TOKEN_APPROVE_ALL_TOPIC = '0x17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31'


@async_lru.alru_cache(maxsize=1024)
async def is_token721_contract(address: str, provider_bucket, timeout: int) -> bool:
    """
    Detect the contract is ERC721-based or not.

    :param address:
    :param provider_bucket:
    :param timeout:
    :return:
    """
    # detect ERC721, return if contract is ERC721
    # see https://ethereum.stackexchange.com/questions/44880/erc-165-query-on-erc-721-implementation
    data = await web3_json_rpc(
        tx_obj={
            "method": "eth_call",
            "params": [{
                'to': address,
                "data": "0x01ffc9a780ac58cd00000000000000000000000000000000000000000000000000000000",
            }, 'latest'
            ],
            "id": 1,
            "jsonrpc": "2.0"
        },
        provider=await provider_bucket.get(),
        timeout=timeout,
    )

    # parse response
    result = parse_bytes_data(data, ['bool'])
    if result is None:
        return False
    if len(result) > 0 and result[0] is False:
        return False

    # check decimals of erc20
    decimals = await get_token_decimals(
        address=address,
        provider_bucket=provider_bucket,
        timeout=timeout,
    )
    if decimals > 0:
        return False
    return True


@async_lru.alru_cache(maxsize=1024)
async def is_token1155_contract(address: str, provider_bucket, timeout: int) -> bool:
    """
    Detect the contract is ERC1155-based or not.

    :param address:
    :param provider_bucket:
    :param timeout:
    :return:
    """
    # detect ERC1155, return if contract is ERC1155
    # see https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1155.md
    data = await web3_json_rpc(
        tx_obj={
            "method": "eth_call",
            "params": [{
                'to': address,
                "data": "0x01ffc9a7d9b67a2600000000000000000000000000000000000000000000000000000000",
            }, 'latest'
            ],
            "id": 1,
            "jsonrpc": "2.0"
        },
        provider=await provider_bucket.get(),
        timeout=timeout,
    )

    # parse response
    result = parse_bytes_data(data, ['bool'])
    if result is None:
        return False
    return result[0] if len(result) > 0 else False


@async_lru.alru_cache(maxsize=1024)
async def get_token_name(address: str, provider_bucket, timeout: int) -> str:
    """
    query the token name for the given address.
    :param address:
    :param provider_bucket:
    :param timeout:
    :return:
    """
    name = ''
    data = await web3_json_rpc(
        tx_obj={
            "method": "eth_call",
            "params": [
                {'to': address, "data": Web3.keccak(text='name()').hex()[:2 + 8]},
                'latest'
            ],
            "id": 1,
            "jsonrpc": "2.0"
        },
        provider=await provider_bucket.get(),
        timeout=timeout,
    )
    result = parse_bytes_data(data, ["string", ])
    if result is not None:
        name = result[0]
    return name


@async_lru.alru_cache(maxsize=1024)
async def get_token_symbol(address: str, provider_bucket, timeout: int) -> str:
    """
    query the token symbol for the given address.
    :param address:
    :param provider_bucket:
    :param timeout:
    :return:
    """
    # fetch token symbol
    symbol = ''
    call_data = ['symbol()', 'SYMBOL()', 'symbol()', 'SYMBOL()']
    call_data_types = [["string", ], ["string", ], ["bytes32", ], ["bytes32", ]]
    for i in range(len(call_data)):
        data = await web3_json_rpc(
            tx_obj={
                "method": "eth_call",
                "params": [
                    {'to': address, "data": Web3.keccak(text=call_data[i]).hex()[:2 + 8]},
                    'latest'
                ],
                "id": 1,
                "jsonrpc": "2.0"
            },
            provider=await provider_bucket.get(),
            timeout=timeout,
        )
        result = parse_bytes_data(data, call_data_types[i])
        if result is not None:
            symbol = result[0]
            break
    return symbol if isinstance(symbol, str) else binascii.hexlify(symbol).decode()


@async_lru.alru_cache(maxsize=1024)
async def get_token_decimals(address: str, provider_bucket, timeout: int) -> int:
    """
    query the token decimals for the given address, e.g. ERC20 token.
    :param address:
    :param provider_bucket:
    :param timeout:
    :return:
    """
    decimals = -1
    call_data = ['decimals()', 'DECIMALS()']
    call_data_types = [["uint8", ], ["uint8", ]]
    for i in range(len(call_data)):
        data = await web3_json_rpc(
            tx_obj={
                "method": "eth_call",
                "params": [
                    {'to': address, "data": Web3.keccak(text=call_data[i]).hex()[:2 + 8]},
                    'latest'
                ],
                "id": 1,
                "jsonrpc": "2.0"
            },
            provider=await provider_bucket.get(),
            timeout=timeout,
        )
        result = parse_bytes_data(data, call_data_types[i])
        if result is not None:
            decimals = result[0]
            break
    return decimals


@async_lru.alru_cache(maxsize=1024)
async def get_token_total_supply(address: str, provider_bucket, timeout: int) -> int:
    """
    query the token supply for the given address.
    :param address:
    :param provider_bucket:
    :param timeout:
    :return:
    """
    total_supply = -1
    data = await web3_json_rpc(
        tx_obj={
            "method": "eth_call",
            "params": [
                {'to': address, "data": Web3.keccak(text='totalSupply()').hex()[:2 + 8]},
                'latest'
            ],
            "id": 1,
            "jsonrpc": "2.0"
        },
        provider=await provider_bucket.get(),
        timeout=timeout,
    )
    result = parse_bytes_data(data, ["uint256"])
    if result is not None:
        total_supply = result[0]
    return total_supply
