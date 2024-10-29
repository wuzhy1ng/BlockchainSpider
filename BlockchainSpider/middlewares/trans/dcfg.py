import json
import logging
from typing import Dict, List

import scrapy
from pyevmasm import evmasm

from BlockchainSpider.items import DCFGBlockItem, DCFGEdgeItem
from BlockchainSpider.middlewares.trans import TraceMiddleware
from BlockchainSpider.utils.decorator import log_debug_tracing

JS_TRACER = """{
    blocks: [],
    edges: [],
    bid2idx: {},
    bid2vis: {},
    context: {
        'cur_bid': null,
        'pre_op': null,
        'call_value': 0,
        'call_gas': 0,
        'call_selector': null,
        'addrStack': [],
        'index': 0,
    },
    slice_op: { // JUMP, JUMPI
        0x56: true, 0x57: true,
    },
    call_op: { // CALL, CALLCODE, STATICCALL, DELEGATECALL, CREATE, CREATE2, SELFDESTRUCT
        0xF1: true, 0xF2: true,
        0xFA: true, 0xF4: true,
        0xF0: true, 0xF5: true,
        0xFF: true,
    },
    byte2Hex: function (byte) {
        if (byte < 0x10) return '0' + byte.toString(16);
        return byte.toString(16);
    },
    array2Hex: function (arr) {
        var retVal = '';
        for (var i = 0; i < arr.length; i++) retVal += this.byte2Hex(arr[i]);
        return retVal;
    },
    getAddr: function (addr) {
        return '0x' + this.array2Hex(addr);
    },
    step: function (log, db) {
        // parse step args
        pc = log.getPC();
        op = log.op.toNumber();
        if (this.context.addrStack.length === 0) {
            this.context.addrStack.push(this.getAddr(log.contract.getAddress()));
        }
        address = this.context.addrStack[this.context.addrStack.length - 1];

        // init an new block and add the edge
        if (this.context.cur_bid == null) {
            this.context.cur_bid = address + '#' + pc;
            this.bid2idx[this.context.cur_bid] = this.blocks.length;
            this.blocks.push({
                'bid': this.context.cur_bid,
                'ops': [op],
            });
            this.context.pre_op = op;
            return
        }

        // just add opcode for current block
        if (this.slice_op[this.context.pre_op] === undefined && 
            this.call_op[this.context.pre_op] === undefined) {
            if (!this.bid2vis[this.context.cur_bid]) {
                this.blocks[this.bid2idx[this.context.cur_bid]]['ops'].push(op);
            }
            this.context.pre_op = op;
            return
        }

        // add the edge and flash the ops in the (new) block
        new_bid = address + '#' + pc;
        edge = {
            'from': this.context.cur_bid,
            'to': new_bid,
            'type': this.context.pre_op,
            'index': this.context.index,
        };
        if (this.call_op[this.context.pre_op]) {
            edge['value'] = this.context.call_value;
            edge['gas'] = this.context.call_gas;
            edge['selector'] = this.context.call_selector;
        }
        if (this.bid2idx[new_bid] == undefined) {
            this.bid2idx[new_bid] = this.blocks.length;
            this.blocks.push({
                'bid': new_bid,
                'ops': [op],
            });
        }
        edge['from'] = this.bid2idx[edge['from']];
        edge['to'] = this.bid2idx[edge['to']];
        this.edges.push(edge);
        this.bid2vis[this.context.cur_bid] = true;

        // update context
        this.context.cur_bid = new_bid;
        this.context.pre_op = op;
        this.context.index += 1;
    },
    fault: function (log, db) {},
    enter: function (cf) {
        this.context.addrStack.push(this.getAddr(cf.getTo()));
        let value = cf.getValue();
        this.context.call_value = (value === undefined)? '0': value.toString();
        let gas = cf.getGas();
        this.context.call_gas = (gas === undefined)? '0': gas.toString();
        let input = this.array2Hex(cf.getInput());
        this.context.call_selector = '0x' + input.slice(0, 8);
    },
    exit: function (fr) {
        this.context.addrStack.pop();
    },
    result: function (ctx, db) {
        var blocks = [];
        for (const block of this.blocks) {
            let addr_pc = block['bid'].split('#');
            blocks.push({
                'contract_address': addr_pc[0],
                'start_pc': Number(addr_pc[1]),
                'operations': block['ops'],
            });
        }
        return {
            'blocks': blocks,
            'edges': this.edges,
        };
    }
}"""

NUM2OP_NAME = set()
for table in evmasm.instruction_tables.values():
    for key in table.keys():
        NUM2OP_NAME.add((key, table[key].name))
NUM2OP_NAME = sorted(list(NUM2OP_NAME), key=lambda _item: _item[0])
NUM2OP_NAME = {num: op for num, op in NUM2OP_NAME}


class DCFGMiddleware(TraceMiddleware):
    def __init__(self):
        super().__init__()

    @log_debug_tracing
    async def parse_debug_trace_block(self, response: scrapy.http.Response, **kwargs):
        data = json.loads(response.text)
        data = data.get('result')
        if data is None:
            self.log(
                message='On parse_debug_trace_block, `result` is None, '
                        'please check if your providers are fully available at debug_traceBlockByNumber.',
                level=logging.WARNING,
            )
            return

        # parse trace item
        transaction_hashes = kwargs.pop('transaction_hashes')
        for i, result in enumerate(data):
            kwargs['transaction_hash'] = transaction_hashes[i]
            for item in DCFGMiddleware.parse_dcfg_block_items(result['result'], **kwargs):
                yield item
            for item in DCFGMiddleware.parse_dcfg_edge_items(result['result'], **kwargs):
                yield item

    @log_debug_tracing
    async def parse_debug_transaction(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')
        if result is None:
            self.log(
                message='On parse_debug_transaction, `result` is None, '
                        'please check if your providers are fully available at debug_traceTransaction.',
                level=logging.WARNING,
            )
            return

        # parse trace item
        for item in DCFGMiddleware.parse_dcfg_block_items(result, **kwargs):
            yield item
        for item in DCFGMiddleware.parse_dcfg_edge_items(result, **kwargs):
            yield item

    @staticmethod
    def parse_dcfg_block_items(result: Dict, **kwargs) -> List[DCFGBlockItem]:
        items = list()
        for block in result['blocks']:
            operations = [
                NUM2OP_NAME[num] for num in block['operations']
                if NUM2OP_NAME.get(num)  # Note: may become outdated
            ]
            items.append(DCFGBlockItem(
                contract_address=block['contract_address'],
                start_pc=block['start_pc'],
                operations=operations,
                cb_kwargs={'transaction_hash': kwargs['transaction_hash']}
            ))
        return items

    @staticmethod
    def parse_dcfg_edge_items(result: Dict, **kwargs) -> List[DCFGEdgeItem]:
        items = list()
        blocks = result['blocks']
        for edge in result['edges']:
            items.append(DCFGEdgeItem(
                transaction_hash=kwargs['transaction_hash'],
                address_from=blocks[edge['from']]['contract_address'],
                start_pc_from=blocks[edge['from']]['start_pc'],
                address_to=blocks[edge['to']]['contract_address'],
                start_pc_to=blocks[edge['to']]['start_pc'],
                flow_type=NUM2OP_NAME[edge['type']],
                value=int(edge.get('value', -1)),
                gas=int(edge.get('gas', -1)),
                selector=edge.get('selector', '0x'),
                index=edge.get('index', 0),
            ))
        return items

    async def get_request_debug_trace_block(
            self, block_number: int, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "debug_traceBlockByNumber",
                "params": [hex(block_number), {"tracer": JS_TRACER}],
                "id": 1
            }),
            priority=priority,
            callback=self.parse_debug_trace_block,
            cb_kwargs=cb_kwargs if cb_kwargs else dict(),
        )

    async def get_request_debug_transaction(
            self, txhash: str, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "debug_traceTransaction",
                "params": [txhash, {"tracer": JS_TRACER}],
                "id": 1
            }),
            priority=priority,
            callback=self.parse_debug_transaction,
            cb_kwargs=cb_kwargs if cb_kwargs else dict(),
        )
