import sys
import time

from BlockchainSpider.strategies import PushPopModel


class TTR(PushPopModel):
    def __init__(
            self,
            source, alpha: float = 0.15,
            beta: float = 0.8,
            epsilon: float = 1e-5,
    ):
        super().__init__(source)
        self.alpha = alpha
        self.beta = beta
        self.epsilon = epsilon

    def push(self, node, edges: list, **kwargs):
        raise NotImplementedError()

    def pop(self):
        raise NotImplementedError()


class TTRBase(TTR):
    name = 'TTRBase'

    def __init__(
            self,
            source,
            alpha: float = 0.15,
            beta: float = 0.8,
            epsilon: float = 1e-5,
    ):
        super().__init__(source, alpha, beta, epsilon)
        self.p = dict()
        self.r = {source: 1.0}
        self._vis = set()

    def push(self, node, edges: list, **kwargs):
        # init residual vector
        if self.r.get(node) is None:
            self.r[node] = 0

        # copy residual vector and clear old value
        r = self.r[node]
        self.r[node] = 0

        # push
        self._self_push(node, r)
        self._forward_push(node, edges, r)
        self._backward_push(node, edges, r)

        # yield edges
        if node not in self._vis:
            self._vis.add(node)
            yield from edges

    def _self_push(self, node, r):
        self.p[node] = self.p.get(node, 0) + self.alpha * r

    def _forward_push(self, node, edges: list, r):
        out_edges = list()
        for e in edges:
            if e['from'] == node:
                out_edges.append(e)

        out_edges_cnt = len(out_edges)
        for e in out_edges:
            inc = (1 - self.alpha) * self.beta * r / out_edges_cnt if out_edges_cnt > 0 else 0
            self.r[e['to']] = self.r.get(e['to'], 0) + inc

    def _backward_push(self, node, edges: list, r):
        in_edges = list()
        for e in edges:
            if e['to'] == node:
                in_edges.append(e)

        in_edges_cnt = len(in_edges)
        for e in in_edges:
            inc = (1 - self.alpha) * (1 - self.beta) * r / in_edges_cnt if in_edges_cnt > 0 else 0
            self.r[e['from']] = self.r.get(e['from'], 0) + inc

    def pop(self):
        node, r = None, self.epsilon
        for _node, _r in self.r.items():
            if _r > r:
                node, r = _node, _r
        return dict(node=node, residual=r) if node is not None else None


class TTRWeight(TTR):
    name = 'TTRWeight'

    def __init__(self, source, alpha: float = 0.15, beta: float = 0.8, epsilon=1e-5):
        super().__init__(source, alpha, beta, epsilon)
        self.p = dict()
        self.r = {source: 1.0}
        self._vis = set()

    def push(self, node, edges: list, **kwargs):
        # residual vector空值判定
        if self.r.get(node) is None:
            self.r[node] = 0

        # 拷贝一份residual vector，原有的清空
        r = self.r[node]
        self.r[node] = 0

        # push过程
        self._self_push(node, r)
        self._forward_push(node, edges, r)
        self._backward_push(node, edges, r)

        # yield edges
        if node not in self._vis:
            self._vis.add(node)
            yield from edges

    def _self_push(self, node, r):
        self.p[node] = self.p.get(node, 0) + self.alpha * r

    def _forward_push(self, node, edges: list, r):
        out_sum = 0
        out_edges = list()
        for e in edges:
            if e['from'] == node:
                out_sum += e['value']
                out_edges.append(e)
        for e in out_edges:
            inc = (1 - self.alpha) * self.beta * (e['value'] / out_sum) * r if out_sum > 0 else 0
            self.r[e['to']] = self.r.get(e['to'], 0) + inc
            # yield e

    def _backward_push(self, node, edges: list, r):
        in_sum = 0
        in_edges = list()
        for e in edges:
            if e['to'] == node:
                in_sum += e['value']
                in_edges.append(e)
        for e in in_edges:
            inc = (1 - self.alpha) * (1 - self.beta) * (e['value'] / in_sum) * r if in_sum > 0 else 0
            self.r[e['from']] = self.r.get(e['from'], 0) + inc
            # yield e

    def pop(self):
        node, r = None, self.epsilon
        for _node, _r in self.r.items():
            if _r > r:
                node, r = _node, _r
        return dict(node=node, residual=r) if node is not None else None


class TTRTime(TTR):
    name = 'TTRTime'

    def __init__(self, source, alpha: float = 0.15, beta: float = 0.8, epsilon=1e-5):
        super().__init__(source, alpha, beta, epsilon)
        self.p = dict()
        self.r = dict()
        self._vis = set()

    def push(self, node, edges: list, **kwargs):
        # residual vector空值判定
        if self.r.get(node) is None:
            self.r[node] = dict()

        # 当更新的是源节点时
        if node == self.source and self.source not in self._vis:
            self._vis.add(self.source)

            # first self push
            self.p[self.source] = self.alpha

            # first forward and backward push
            out_sum = sum([e['value'] if e['from'] == self.source else 0 for e in edges])
            in_sum = sum([e['value'] if e['to'] == self.source else 0 for e in edges])
            for e in edges:
                if e['from'] == self.source and out_sum != 0:
                    self.r[self.source][e['timeStamp']] = \
                        (1 - self.alpha) * self.beta * e['value'] / out_sum
                elif e['to'] == self.source and in_sum != 0:
                    self.r[self.source][e['timeStamp']] = \
                        (1 - self.alpha) * (1 - self.beta) * e['value'] / in_sum
            if out_sum == 0:
                # 如果对某个节点的expand结果始终是一样的那么可以改成注释这行代码
                # self.p[self.source] += (1 - self.alpha) * self.beta
                self.r[self.source][0] = (1 - self.alpha) * self.beta
            if in_sum == 0:
                # 如果对某个节点的expand结果始终是一样的那么可以改成注释这行代码
                # self.p[self.source] += (1 - self.alpha) * (1 - self.beta)
                self.r[self.source][sys.maxsize] = (1 - self.alpha) * (1 - self.beta)

            return

        # 拷贝一份residual vector，原有的清空
        r = self.r[node]
        self.r[node] = dict()

        # push过程
        self._self_push(node, r)
        self._forward_push(node, edges, r)
        self._backward_push(node, edges, r)

        # yield edges
        if node not in self._vis:
            self._vis.add(node)
            yield from edges

    def _self_push(self, node, r: dict):
        sum_r = 0
        for _, v in r.items():
            sum_r += v
        self.p[node] = self.p.get(node, 0) + self.alpha * sum_r

    def _forward_push(self, node, edges: list, r: dict):
        """
        将流动权重沿着时序递增的输出边传播，并返回传播的输出边
        :param node: 扩展节点
        :param edges: 扩展得到的边
        :return: 传播的输出边
        """
        # 取出所有输出的边和chip
        es_out = list()
        for e in edges:
            if e['from'] == node:
                es_out.append(e)
        r_node = [(t, v) for t, v in r.items()]

        # 根据时间排序-从小到大
        es_out.sort(key=lambda _e: _e['timeStamp'])
        r_node.sort(key=lambda _c: _c[0])

        # 累计叠加，计算每个chip之后的value之和
        j = len(es_out) - 1
        sum_w, W = 0, dict()
        for i in range(len(r_node) - 1, -1, -1):
            c = r_node[i]
            while j >= 0 and es_out[j]['timeStamp'] > c[0]:
                sum_w += es_out[j]['value']
                j -= 1
            W[c] = sum_w

        # 将流动传播给出度邻居
        j = 0
        d = 0
        for i in range(0, len(es_out)):
            e = es_out[i]
            while j < len(r_node) and e['timeStamp'] > r_node[j][0]:
                d += (r_node[j][1] / W[r_node[j]]) if W[r_node[j]] > 0 else 0
                j += 1

            if self.r.get(e['to']) is None:
                self.r[e['to']] = dict()
            inc = (1 - self.alpha) * self.beta * e['value'] * d
            self.r[e['to']][e['timeStamp']] = self.r[e['to']].get(e['timeStamp'], 0) + inc

        # 当流动权重碎片缺失输出边时将回流到自身
        while j < len(r_node):
            self.r[node][r_node[j][0]] = self.r[node].get(r_node[j][0], 0) + \
                                         (1 - self.alpha) * self.beta * r_node[j][1]
            j += 1

    def _backward_push(self, node, edges: list, r: dict):
        """
        将流动权重沿着时序递增的输入边传播，并返回传播的输入边
        :param node: 扩展节点
        :param edges: 扩展得到的边
        :return: 传播的输入边
        """
        # 取出所有输出的边和chip
        es_in = list()
        for e in edges:
            if e['to'] == node:
                es_in.append(e)
        r_node = [(t, v) for t, v in r.items()]

        # 根据时间排序-从小到大
        es_in.sort(key=lambda _e: _e['timeStamp'])
        r_node.sort(key=lambda _c: _c[0])

        # 累计叠加，计算每个chip之前的value之和
        j = 0
        sum_w, W = 0, dict()
        for i in range(0, len(r_node)):
            c = r_node[i]
            while j < len(es_in) and es_in[j]['timeStamp'] < c[0]:
                sum_w += es_in[j]['value']
                j += 1
            W[c] = sum_w

        # 将流动传播给入度邻居
        j = len(r_node) - 1
        d = 0
        for i in range(len(es_in) - 1, -1, -1):
            e = es_in[i]
            while j >= 0 and e['timeStamp'] < r_node[j][0]:
                d += (r_node[j][1] / W[r_node[j]]) if W[r_node[j]] > 0 else 0
                j -= 1

            if self.r.get(e['from']) is None:
                self.r[e['from']] = dict()
            inc = (1 - self.alpha) * (1 - self.beta) * e['value'] * d
            self.r[e['from']][e['timeStamp']] = self.r[e['from']].get(e['timeStamp'], 0) + inc

        # 当流动权重碎片缺失输入边时将回流到自身
        while j >= 0:
            self.r[node][r_node[j][0]] = self.r[node].get(r_node[j][0], 0) + \
                                         (1 - self.alpha) * (1 - self.beta) * r_node[j][1]
            j -= 1

    def pop(self):
        node, r = None, self.epsilon
        for _node, chips in self.r.items():
            sum_r = 0
            for v in chips.values():
                sum_r += v
            if sum_r > r:
                node, r = _node, sum_r

        return dict(node=node, residual=r) if node is not None else None


class TTRRedirect(TTR):
    name = 'TTRRedirect'

    def __init__(self, source, alpha: float = 0.15, beta: float = 0.8, epsilon=1e-5):
        super().__init__(source, alpha, beta, epsilon)
        self.p = dict()
        self.r = dict()
        self._vis = set()

    def push(self, node, edges: list, **kwargs):
        start = time.time()

        # if residual vector is none, add empty list
        if self.r.get(node) is None:
            self.r[node] = list()

        # push on first time
        if node == self.source and node not in self._vis:
            self._vis.add(self.source)

            # calc value of each symbol
            in_sum = dict()
            out_sum = dict()
            symbols = set()
            for e in edges:
                symbols.add(e.get('symbol'))
                if e.get('to') == self.source:
                    in_sum[e.get('symbol')] = in_sum.get(e.get('symbol'), 0) + e.get('value', 0)
                elif e.get('from') == self.source:
                    out_sum[e.get('symbol')] = out_sum.get(e.get('symbol'), 0) + e.get('value', 0)

            # first self push
            self.p[self.source] = self.alpha * len(symbols)

            # first forward and backward push
            for e in edges:
                if e.get('from') == self.source and out_sum.get(e.get('symbol'), 0) != 0:
                    if self.r.get(e.get('to')) is None:
                        self.r[e.get('to')] = list()
                    value = (1 - self.alpha) * self.beta * e.get('value', 0) / out_sum[e.get('symbol')]
                    if value > 0:
                        self.r[e.get('to')].append(dict(
                            value=value,
                            timestamp=e.get('timeStamp'),
                            symbol=e.get('symbol')
                        ))
                elif e.get('to') == self.source and in_sum.get(e.get('symbol'), 0) != 0:
                    if self.r.get(e.get('from')) is None:
                        self.r[e.get('from')] = list()
                    value = (1 - self.alpha) * (1 - self.beta) * e.get('value', 0) / in_sum[e.get('symbol')]
                    if value > 0:
                        self.r[e.get('from')].append(dict(
                            value=value,
                            timestamp=e.get('timeStamp'),
                            symbol=e.get('symbol')
                        ))

            for symbol in symbols:
                if out_sum.get(symbol, 0) == 0:
                    self.r[self.source].append(dict(
                        value=(1 - self.alpha) * self.beta,
                        timestamp=0,
                        symbol=symbol
                    ))
                elif in_sum.get(symbol, 0) == 0:
                    self.r[self.source].append(dict(
                        value=(1 - self.alpha) * (1 - self.beta),
                        timestamp=sys.maxsize,
                        symbol=symbol
                    ))
            return

        # copy residual vector with sort and clear
        r = self.r[node]
        r.sort(key=lambda x: x.get('timestamp', 0))
        self.r[node] = list()

        # aggregate edges
        agg_es = self._get_aggregated_edges(node, edges)
        agg_es.sort(key=lambda x: x.get_timestamp())

        # push
        self._self_push(node, r)
        self._forward_push(node, agg_es, r)
        self._backward_push(node, agg_es, r)

        # marge chips
        for node, chips in self.r.items():
            _chips = dict()
            for chip in chips:
                key = (chip.get('symbol'), chip.get('timestamp'))
                if _chips.get(key) is None:
                    _chips[key] = chip
                    continue
                _chips[key]['value'] += chip.get('value', 0)
            self.r[node] = [v for v in _chips.values()]

        # yield edges
        if node not in self._vis:
            self._vis.add(node)
            yield from edges

    def _self_push(self, node, r: list):
        sum_r = 0
        for chip in r:
            sum_r += chip.get('value', 0)
        self.p[node] = self.p.get(node, 0) + self.alpha * sum_r

    def _forward_push(self, node, aggregated_edges: list, r: list):
        if len(r) == 0:
            return

        # calc the weight sum after each chip
        j = len(aggregated_edges) - 1
        sum_w, W = dict(), dict()
        for i in range(len(r) - 1, -1, -1):
            c = r[i]
            while j >= 0 and aggregated_edges[j].get_timestamp() > c.get('timestamp', 0):
                e = aggregated_edges[j]
                profits = e.get_output_profits()
                for profit in profits:
                    sum_w[profit.symbol] = sum_w.get(profit.symbol, 0) + profit.value
                j -= 1
            W[str(c)] = sum_w.get(c.get('symbol'), 0)

        # construct index for distributing profit
        symbol_agg_es = dict()
        symbol_agg_es_idx = dict()
        for i, e in enumerate(aggregated_edges):
            for profit in e.get_output_profits():
                if symbol_agg_es.get(profit.symbol) is None:
                    symbol_agg_es[profit.symbol] = list()
                    symbol_agg_es_idx[profit.symbol] = list()
                symbol_agg_es[profit.symbol].append(e)
                symbol_agg_es_idx[profit.symbol].append(i)
        distributing_index = dict()
        for symbol in symbol_agg_es.keys():
            es_idx = symbol_agg_es_idx[symbol]
            index = [0 for _ in range(len(aggregated_edges))]
            j = 0
            for i in range(len(index)):
                if j < len(es_idx) and es_idx[j] <= i:
                    j += 1 if j < len(es_idx) else 0
                index[i] = j
            distributing_index[symbol] = index

        # push residual to neighbors
        j = 0
        d = dict()
        for i in range(0, len(aggregated_edges)):
            e = aggregated_edges[i]
            output_profits = e.get_output_profits()
            if len(output_profits) == 0:
                continue

            while j < len(r) and e.get_timestamp() > r[j].get('timestamp', 0):
                c = r[j]
                symbol = c.get('symbol')
                inc_d = (c.get('value', 0) / W[str(c)]) if W[str(c)] != 0 else 0
                d[symbol] = d.get(symbol, 0) + inc_d
                j += 1

            for profit in output_profits:
                inc = (1 - self.alpha) * self.beta * profit.value * d.get(profit.symbol, 0)
                if inc == 0:
                    continue

                distributing_profits = self._get_distributing_profit_v2(
                    direction=-1,
                    symbol=profit.symbol,
                    index=i,
                    aggregated_edges=aggregated_edges,
                    distributing_index=distributing_index,
                    symbol_agg_es_idx=symbol_agg_es_idx,
                    chip_value=inc
                )
                for dp in distributing_profits:
                    if self.r.get(dp.address) is None:
                        self.r[dp.address] = list()
                    self.r[dp.address].append(dict(
                        value=inc / len(distributing_profits),
                        symbol=dp.symbol,
                        timestamp=dp.timestamp,
                    ))

        # recycle the residual without push
        cs = dict()
        while j < len(r):
            c = r[j]
            key = c.get('symbol'), c.get('timestamp')
            cs[key] = cs.get(key, 0) + (1 - self.alpha) * self.beta * c.get('value', 0)
            j += 1
        for key, value in cs.items():
            self.r[node].append(dict(
                value=value,
                symbol=key[0],
                timestamp=key[1]
            ))

    def _backward_push(self, node, aggregated_edges: list, r: list):
        if len(r) == 0:
            return

        # calc the weight sum before each chip
        j = 0
        sum_w, W = dict(), dict()
        for i in range(0, len(r)):
            c = r[i]
            while j < len(aggregated_edges) and aggregated_edges[j].get_timestamp() < c.get('timestamp', 0):
                e = aggregated_edges[j]
                profits = e.get_input_profits()
                for profit in profits:
                    sum_w[profit.symbol] = sum_w.get(profit.symbol, 0) + profit.value
                j += 1
            W[i] = sum_w.get(c.get('symbol'), 0)

        # construct index for distributing profit
        symbol_agg_es = dict()
        symbol_agg_es_idx = dict()
        for i, e in enumerate(aggregated_edges):
            for profit in e.get_output_profits():
                if symbol_agg_es.get(profit.symbol) is None:
                    symbol_agg_es[profit.symbol] = list()
                    symbol_agg_es_idx[profit.symbol] = list()
                symbol_agg_es[profit.symbol].append(e)
                symbol_agg_es_idx[profit.symbol].append(i)
        distributing_index = dict()
        for symbol in symbol_agg_es.keys():
            es_idx = symbol_agg_es_idx[symbol]
            index = [0 for _ in range(len(aggregated_edges))]
            j = len(es_idx) - 1
            for i in range(len(index) - 1, -1, -1):
                if j > 0 and es_idx[j] >= i:
                    j -= 1 if j > 0 else 0
                index[i] = j
            distributing_index[symbol] = index

        # push residual to neighbors
        j = len(r) - 1
        d = dict()
        for i in range(len(aggregated_edges) - 1, -1, -1):
            e = aggregated_edges[i]
            input_profits = e.get_input_profits()
            if len(input_profits) == 0:
                continue

            while j >= 0 and e.get_timestamp() < r[j].get('timestamp', 0):
                c = r[j]
                symbol = c.get('symbol')
                inc_d = (c.get('value', 0) / W[j]) if W[j] != 0 else 0
                d[symbol] = d.get(symbol, 0) + inc_d
                j -= 1

            for profit in input_profits:
                inc = (1 - self.alpha) * (1 - self.beta) * profit.value * d.get(profit.symbol, 0)
                if inc == 0:
                    continue

                distributing_profits = self._get_distributing_profit_v2(
                    direction=1,
                    symbol=profit.symbol,
                    index=i,
                    aggregated_edges=aggregated_edges,
                    distributing_index=distributing_index,
                    symbol_agg_es_idx=symbol_agg_es_idx,
                    chip_value=inc
                )
                for dp in distributing_profits:
                    if self.r.get(dp.address) is None:
                        self.r[dp.address] = list()
                    self.r[dp.address].append(dict(
                        value=inc / len(distributing_profits),
                        symbol=dp.symbol,
                        timestamp=dp.timestamp,
                    ))

        # recycle the residual without push
        cs = dict()
        while j >= 0:
            c = r[j]
            key = c.get('symbol'), c.get('timestamp')
            cs[key] = cs.get(key, 0) + (1 - self.alpha) * (1 - self.beta) * c.get('value', 0)
            j -= 1
        for key, value in cs.items():
            self.r[node].append(dict(
                value=value,
                symbol=key[0],
                timestamp=key[1]
            ))

    def pop(self):
        node, r = None, self.epsilon
        for _node, chips in self.r.items():
            sum_r = 0
            for chip in chips:
                sum_r += chip.get('value', 0)
            if sum_r > r:
                node, r = _node, sum_r

        return dict(node=node, residual=r) if node is not None else None

    def _get_distributing_profit_v2(
            self,
            direction: int,
            symbol: str,
            index: int,
            aggregated_edges: list,
            distributing_index: dict,
            symbol_agg_es_idx: dict,
            chip_value: float,
    ) -> list:
        """

        :param direction: 1 means input and -1 means output
        :param index: current aggregated edge index
        :param aggregated_edges:
        :return: a list of profit
        """
        rlt = list()

        stack = list()
        stack.append((direction, symbol, index))
        vis = set()
        while len(stack) > 0:
            args = stack.pop()
            if args in vis:
                continue
            vis.add(args)

            direction, symbol, index = args
            cur_e = aggregated_edges[index]
            no_reverse_profits = [profit for profit in cur_e.profits if profit.value * direction > 0]
            reverse_profits = [profit for profit in cur_e.profits if profit.value * direction < 0]

            if len(stack) > 0 and chip_value / len(stack) < self.epsilon:
                return [profit for profit in no_reverse_profits if profit.symbol == symbol]

            if len(reverse_profits) == 1:
                profit = reverse_profits[0]

                _symbol_agg_es_idx = symbol_agg_es_idx.get(profit.symbol)
                _distributing_index = distributing_index.get(profit.symbol)
                if _symbol_agg_es_idx is None or _distributing_index is None:
                    continue

                if direction < 0:
                    indices = _symbol_agg_es_idx[_distributing_index[index]:]
                else:
                    indices = _symbol_agg_es_idx[:_distributing_index[index]]

                for _index in indices:
                    stack.append((direction, profit.symbol, _index))
            else:
                rlt.extend([profit for profit in no_reverse_profits if profit.symbol == symbol])

        return rlt

    def _get_swapped_aggregate_edge_indices(
            self,
            direction: int,
            profit,
            index: int,
            aggregated_edges: list,
    ):
        rlt = list()
        indices = range(index + 1, len(aggregated_edges)) if direction < 0 else range(0, index)
        for _index in indices:
            profits = aggregated_edges[_index].profits
            profits = [p for p in profits if p.symbol == profit.symbol and p.value * profit.value < 0]
            if len(profits) > 0:
                rlt.append(_index)
        return rlt

    def _get_distributing_profit(
            self,
            direction: int,
            symbol: str,
            index: int,
            aggregated_edges: list,
    ) -> list:
        """

        :param direction: 1 means input and -1 means output
        :param index: current aggregated edge index
        :param aggregated_edges:
        :return: a list of profit
        """
        rlt = list()

        stack = list()
        stack.append((direction, symbol, index))
        vis = set()
        while len(stack) > 0:
            args = stack.pop()
            if args in vis:
                continue
            vis.add(args)

            direction, symbol, index = args
            cur_e = aggregated_edges[index]
            no_reverse_profits = [profit for profit in cur_e.profits if profit.value * direction > 0]
            reverse_profits = [profit for profit in cur_e.profits if profit.value * direction < 0]
            if len(reverse_profits) == 1:
                profit = reverse_profits[0]
                indices = self._get_swapped_aggregate_edge_indices(direction, profit, index, aggregated_edges)
                for _index in indices:
                    stack.append((direction, symbol, _index))
            else:
                rlt.extend([profit for profit in no_reverse_profits if profit.symbol == symbol])

        return rlt

    def _get_aggregated_edges(self, node, edges: list) -> list:
        """
        :param node:
        :param edges: hash, from, to, value, timeStamp, symbol
        :return:
        """
        aggregated_edges = dict()
        for edge in edges:
            _hash = edge.get('hash')
            aggregated_edge = TTRRedirect.AggregatedEdge(
                _hash=_hash,
                _profits=[TTRRedirect.AggregatedEdgeProfit(
                    _address=edge.get('to') if edge.get('from') == node else edge.get('from'),
                    _value=-edge.get('value') if edge.get('from') == node else edge.get('value'),
                    _timestamp=edge.get('timeStamp'),
                    _symbol=edge.get('symbol')
                )],
                _aggregated_edges=[edge],
            )

            aggregated_edge = aggregated_edge.aggregate(aggregated_edges.get(_hash))
            aggregated_edges[_hash] = aggregated_edge
            if len(aggregated_edge.profits) == 0:
                del aggregated_edges[_hash]
        return [aggregated_edge for aggregated_edge in aggregated_edges.values()]

    class AggregatedEdge:
        def __init__(
                self,
                _hash: str,
                _profits: list,
                _aggregated_edges: list,
        ):
            self.hash = _hash
            self.profits = _profits
            self.aggregated_edges = _aggregated_edges

        def aggregate(self, aggregated_edge):
            if aggregated_edge is None:
                return self
            assert isinstance(aggregated_edge, self.__class__)

            # 1. collect all edges
            self.aggregated_edges.extend(aggregated_edge.aggregated_edges)

            # 2. according to symbol to classify profit and aggregate
            aggregated_profits = dict()
            for profit in self.profits + aggregated_edge.profits:
                key = (profit.symbol, profit.address)
                _profit = aggregated_profits.get(key)
                if _profit is None:
                    if profit.value != 0:
                        aggregated_profits[key] = profit
                    continue

                if _profit.value + profit.value == 0:
                    del aggregated_profits[key]
                    continue

                sgn = 1 if _profit.value > 0 else -1
                sgn *= 1 if _profit.value + profit.value > 0 else -1
                aggregated_value = _profit.value + profit.value
                if sgn < 0:
                    _profit = profit
                _profit.value = aggregated_value
                aggregated_profits[key] = _profit
            self.profits = [v for v in aggregated_profits.values()]

            return self

        def get_input_profit(self, symbol):
            for profit in self.profits:
                if profit.symbol == symbol and profit.value > 0:
                    return profit

        def get_output_profit(self, symbol):
            for profit in self.profits:
                if profit.symbol == symbol and profit.value < 0:
                    return profit

        def get_output_profits(self):
            rlt = list()
            for profit in self.profits:
                if profit.value < 0:
                    rlt.append(profit)
            return rlt

        def get_input_profits(self):
            rlt = list()
            for profit in self.profits:
                if profit.value > 0:
                    rlt.append(profit)
            return rlt

        def get_output_symbols(self):
            symbols = set()
            for profit in self.profits:
                if profit.value < 0:
                    symbols.add(profit.symbol)
            return symbols

        def get_input_symbols(self):
            symbols = set()
            for profit in self.profits:
                if profit.value > 0:
                    symbols.add(profit.symbol)
            return symbols

        def get_timestamp(self):
            timestamp = 0
            if len(self.profits) > 0:
                timestamp = self.profits[0].timestamp
            return timestamp

    class AggregatedEdgeProfit:
        def __init__(
                self,
                _address: str,
                _value: float,
                _timestamp: int,
                _symbol: str,
        ):
            self.address = _address
            self.value = _value
            self.timestamp = _timestamp
            self.symbol = _symbol
