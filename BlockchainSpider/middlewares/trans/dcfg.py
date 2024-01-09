import asyncio
import json
import logging
import time
from typing import Dict, Union

import scrapy
from pybloom import ScalableBloomFilter

from BlockchainSpider.items import DCFGBlock, DCFGEdge
from BlockchainSpider.middlewares.trans import TraceMiddleware
from BlockchainSpider.utils.decorator import log_debug_tracing

js_tracer = """{
    blocks: {},
    edges: [],
    context: {
        'cur_bid': null,
        'pre_op': null,
        'call_value': 0,
        'call_gas': 0,
        'call_selector': null,
        'addrStack': [],
        'index': 0,
    },
    slice_op: {
        'JUMP': true, 'JUMPI': true,
    },
    call_op: {
        'CALL': true, 'CALLCODE': true,
        'STATICCALL': true, 'DELEGATECALL': true,
        'CREATE': true, 'CREATE2': true,
        'SELFDESTRUCT': true,
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
        op = log.op.toString();
        if (this.context.addrStack.length === 0) {
            this.context.addrStack.push(this.getAddr(log.contract.getAddress()));
        }
        address = this.context.addrStack[this.context.addrStack.length - 1];

        // init an new block and add the edge
        if (this.context.cur_bid == null) {
            this.context.cur_bid = address + '#' + pc;
            this.blocks[this.context.cur_bid] = [op];
            this.context.pre_op = op;
            return
        }

        // just add opcode for current block
        if (this.slice_op[this.context.pre_op] === undefined && 
            this.call_op[this.context.pre_op] === undefined) {
            this.blocks[this.context.cur_bid].push(op);
            this.context.pre_op = op;
            return
        }

        // slice an new block and add the edge
        new_bid = address + '#' + pc;
        edge = {
            'from': this.context.cur_bid,
            'to': new_bid,
            'type': this.context.pre_op,
            'index': this.context.index,
        }
        if (this.call_op[this.context.pre_op]) {
            edge['value'] = this.context.call_value;
            edge['gas'] = this.context.call_gas;
            edge['selector'] = this.context.call_selector;
        }
        this.edges.push(edge);
        this.context.cur_bid = new_bid;
        this.blocks[this.context.cur_bid] = [op];
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
        for (const [bid, ops] of Object.entries(this.blocks)) {
            let addr_pc = bid.split('#');
            blocks.push({
                'contract_address': addr_pc[0],
                'start_pc': Number(addr_pc[1]),
                'operations': ops,
            });
        }
        var edges = [];
        for (const edge of this.edges) {
            let addr_pc_from = edge['from'].split('#');
            let addr_pc_to = edge['to'].split('#');
            edges.push({
                'address_from': addr_pc_from[0],
                'start_pc_from': Number(addr_pc_from[1]),
                'address_to': addr_pc_to[0],
                'start_pc_to': Number(addr_pc_to[1]),
                'flow_type': edge['type'],
                'value': edge['value'],
                'gas': edge['gas'],
                'selector': edge['selector'],
                'index': edge['index'],
            });
        }
        return {
            'blocks': blocks,
            'edges': edges,
        };
    }
}"""


class DCFGMiddleware(TraceMiddleware):
    def __init__(self):
        super().__init__()
        self.bloom4blockid = ScalableBloomFilter(
            initial_capacity=1024,
            error_rate=1e-4,
            mode=ScalableBloomFilter.SMALL_SET_GROWTH,
        )

    @log_debug_tracing
    async def parse_debug_trace_block(self, response: scrapy.http.Response, **kwargs):
        data = json.loads(response.text)
        data = data.get('result')
        if response is None:
            self.log(
                message="debug_traceBlockByNumber is not available.",
                level=logging.WARNING,
            )
            return

        # parse trance item
        for result in data:
            for item in self.parse_dcfg_items(result, **kwargs):
                yield item

    @log_debug_tracing
    def parse_debug_transaction(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')

        # parse trance item
        for item in self.parse_dcfg_items(result, **kwargs):
            yield item

    def parse_dcfg_items(self, result: Dict, **kwargs) -> Union[DCFGBlock, DCFGEdge]:
        for block in result['blocks']:
            block_id = '{}#{}'.format(
                block['contract_address'],
                block['start_pc']
            )
            if block_id in self.bloom4blockid:
                continue
            self.bloom4blockid.add(block_id)
            yield DCFGBlock(
                contract_address=block['contract_address'],
                start_pc=block['start_pc'],
                operations=block['operations'],
            )
        for edge in result['edges']:
            yield DCFGEdge(
                transaction_hash=kwargs['transaction_hash'],
                address_from=edge['address_from'],
                start_pc_from=edge['start_pc_from'],
                address_to=edge['address_to'],
                start_pc_to=edge['start_pc_to'],
                flow_type=edge['flow_type'],
                value=int(edge.get('value', 0)),
                gas=int(edge.get('gas', 0)),
                selector=edge.get('selector', '0x'),
            )

    async def get_request_debug_trace_block(
            self, block_number: int, priority: int, cb_kwargs: dict
    ) -> scrapy.Request:
        await self._lock.acquire()
        delta = time.time() - self._last_ts
        sleep_range = 3
        if delta < sleep_range:
            await asyncio.sleep(sleep_range - delta)
        self._last_ts = time.time()
        self._lock.release()
        return scrapy.Request(
            # url=await self.provider_bucket.get(),
            url='https://eth-mainnet.nodereal.io/v1/317f6d43dd4c4acea1fa00515cf02f90',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "method": "debug_traceBlockByNumber",
                "params": [hex(block_number), {"tracer": js_tracer}],
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
                "params": [txhash, {"tracer": js_tracer}],
                "id": 1
            }),
            priority=priority,
            callback=self.parse_debug_transaction,
            cb_kwargs=cb_kwargs if cb_kwargs else dict(),
        )
