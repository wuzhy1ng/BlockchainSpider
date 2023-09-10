import asyncio
import json
import traceback
from typing import Union

import aiohttp
from multidict import CIMultiDict
from web3 import Web3


async def web3_json_rpc(tx_obj: dict, provider: str, timeout: int):
    """
    Request the JSON-RPC of the web3 providers, and return the raw data of the `result`.

    :param tx_obj:
    :param provider:
    :param timeout:
    :return:
    """
    client = aiohttp.ClientSession(
        loop=asyncio.get_event_loop(),
        timeout=aiohttp.ClientTimeout(total=timeout)
    )
    try:
        rsp = await client.request(
            url=provider,
            method='POST',
            headers=CIMultiDict(**{'Content-Type': 'application/json'}),
            data=json.dumps(tx_obj),
        )
        data = await rsp.read()
    except:
        traceback.print_exc()
        return
    finally:
        await client.close()

    # parse response
    data = data.decode()
    data = json.loads(data)
    return data.get('result')


def parse_bytes_data(data: bytes, output_types: list) -> Union[tuple, None]:
    """
    Parse the web3 bytes data from the given output types.

    :param data:
    :param output_types:
    :return:
    """
    if not isinstance(data, str) or data == '0x':
        return

    # parse using web3
    try:
        data = bytes.fromhex(data[2:])
        result = Web3().codec.decode_abi(output_types, data)
    except:
        return
    return result


def bytes_to_string(data: bytes):
    if data is None:
        return ''
    try:
        b = data.decode('utf-8')
    except UnicodeDecodeError as _:
        return ''
    return b


def hex_to_dec(hex_string: str) -> int:
    if hex_string is None:
        return -1
    try:
        return int(hex_string, 16)
    except ValueError:
        return -1


def word_to_address(param: str) -> str:
    if param is None:
        return ''
    if len(param) >= 40:
        return ('0x' + param[-40:]).lower()
    else:
        return param.lower()


def chunk_string(string, length):
    return (string[0 + i:length + i] for i in range(0, len(string), length))


def split_to_words(data: str) -> list:
    if data and len(data) > 2:
        data_without_0x = data[2:]
        words = list(chunk_string(data_without_0x, 64))
        words_with_0x = list(map(lambda word: '0x' + word, words))
        return words_with_0x
    return []
