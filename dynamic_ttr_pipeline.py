import sys
import logging
import csv
import threading
from decimal import Decimal, InvalidOperation
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy import signals
from BlockchainSpider.items.sync import SyncItem
import networkx as nx


def _parse_value_to_decimal(value_raw) -> Decimal:
    """把不同格式的 value 规范化为 Decimal（wei）。支持 int、str、hex string。"""
    if value_raw is None:
        return Decimal(0)
    # hex string like '0x...'
    if isinstance(value_raw, str) and value_raw.startswith('0x'):
        try:
            return Decimal(int(value_raw, 16))
        except Exception:
            return Decimal(0)
    try:
        # 先尝试直接转 Decimal
        return Decimal(str(value_raw))
    except (InvalidOperation, ValueError, TypeError):
        try:
            return Decimal(int(value_raw))
        except Exception:
            return Decimal(0)


class DynamicTTRPipeline:
    """A Scrapy pipeline that batches transfers and feeds them to DTTR.

    Configurable via Scrapy settings (see defaults below).
    """

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dttr_path = settings.get('DTT_PATH')
        if dttr_path:
            sys.path.insert(0, dttr_path)

        from algos.dttr import DTTR

        batch_size = settings.getint('DTT_BATCH_SIZE', 100)
        reverse_edge = settings.getbool('DTT_REVERSE_EDGE', True)
        result_file = settings.get('DTT_RESULT_FILE', None)
        
        # 处理 DTT_SOURCE - 可能是列表或字符串
        dttr_source = settings.get('DTT_SOURCE', ['0x7a250d5630b4cf539739df2c5dacb4c659f2488d'])
        if isinstance(dttr_source, str):
            # 如果是字符串，尝试解析为列表
            try:
                import ast
                dttr_source = ast.literal_eval(dttr_source)
            except:
                # 如果解析失败，将其作为单个地址
                dttr_source = [dttr_source]
        elif not isinstance(dttr_source, list):
            dttr_source = list(dttr_source)
        
        dttr_alpha = settings.getfloat('DTT_ALPHA', 0.15)
        dttr_epsilon = Decimal(str(settings.get('DTT_EPSILON', '0.001')))
        dttr_is_in_usd = settings.getbool('DTT_IS_IN_USD', False)
        dttr_is_reduce_swap = settings.getbool('DTT_IS_REDUCE_SWAP', True)
        dttr_is_log_value = settings.getbool('DTT_IS_LOG_VALUE', True)

        pipe = cls(
            DTTR=DTTR,
            dttr_source=dttr_source,
            dttr_alpha=dttr_alpha,
            dttr_epsilon=dttr_epsilon,
            dttr_is_in_usd=dttr_is_in_usd,
            dttr_is_reduce_swap=dttr_is_reduce_swap,
            dttr_is_log_value=dttr_is_log_value,
            batch_size=batch_size,
            reverse_edge=reverse_edge,
            result_file=result_file,
        )

        crawler.signals.connect(pipe.close_spider, signal=signals.spider_closed)
        return pipe
    #默认设置，可在 settings.py 中覆盖
    def __init__(
            self,
            DTTR,
            dttr_source,
            dttr_alpha=0.15,
            dttr_epsilon=Decimal('0.001'),
            dttr_is_in_usd=False, 
            dttr_is_reduce_swap=True,
            dttr_is_log_value=True,
            batch_size=100,
            reverse_edge=True,     # 是否反向边
            result_file=None,
    ):
        self.logger = logging.getLogger(__name__)
        # 初始化 DTTR 实例
        try:
            self.ttr_instance = DTTR(
                source=dttr_source,
                alpha=dttr_alpha,
                epsilon=dttr_epsilon,
                is_in_usd=dttr_is_in_usd,
                is_reduce_swap=dttr_is_reduce_swap,
                is_log_value=dttr_is_log_value,
            )
        except Exception:
            self.logger.exception('无法初始化 DTTR 实例')
            raise

        self.batch_graph = nx.MultiDiGraph()
        self.lock = threading.Lock()
        self.batch_size = int(batch_size)
        self.reverse_edge = bool(reverse_edge)
        self.result_file = result_file

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if not isinstance(item, SyncItem):
            return item

        data = adapter.get('data', {}) or {}

        # TransferItem(外部交易) 常为零值,真正转账在 Token20/721/1155/TraceItem
        transfers = []
        
        # 1. 添加外部交易 
        external_txs = data.get('AccountTransferItem') or data.get('TransferItem') or data.get('TransactionItem')
        if external_txs:
            transfers.extend(external_txs)
        
        # 2. ERC-20 代币转账
        if data.get('Token20TransferItem'):
            transfers.extend(data['Token20TransferItem'])
            self.logger.info(f'检测到 {len(data["Token20TransferItem"])} 条 ERC-20 转账')
        
        # 3. ERC-721 NFT 转账
        if data.get('Token721TransferItem'):
            transfers.extend(data['Token721TransferItem'])
            self.logger.info(f'检测到 {len(data["Token721TransferItem"])} 条 ERC-721 转账')
        
        # 4. ERC-1155 多代币转账
        if data.get('Token1155TransferItem'):
            for item_1155 in data['Token1155TransferItem']:
                token_ids = item_1155.get('token_ids', [])
                values = item_1155.get('values', [])
                if len(token_ids) == len(values):
                    for token_id, value in zip(token_ids, values):
                        transfers.append({
                            'address_from': item_1155.get('address_from'),
                            'address_to': item_1155.get('address_to'),
                            'value': value,
                            'contract_address': item_1155.get('contract_address', ''),
                            'timestamp': item_1155.get('timestamp', 0),
                            'token_id': token_id,
                        })
            self.logger.info(f'检测到 {len(data["Token1155TransferItem"])} 条 ERC-1155 转账')
        
        # 5. 内部 ETH 转账
        if data.get('TraceItem'):
            transfers.extend(data['TraceItem'])
            self.logger.info(f'检测到 {len(data["TraceItem"])} 条内部 ETH 转账')

        if not transfers:
            raise DropItem('SyncItem 无 transfers')

        self.logger.info(f'准备处理 {len(transfers)} 条转账记录')
        processed_count = 0
        dropped_no_address = 0

        for transfer in transfers:
            raw_value = transfer.get('value', 0)
            value_decimal = _parse_value_to_decimal(raw_value)

            # 注意：如果 DTT_IS_IN_USD=True，DTTR 会自动调用 get_usd_value 转换
            # 在这里保留原始值（wei/lamports/sun），让 DTTR 根据 contractAddress 和 timeStamp 查询实时价格
            value_str = str(value_decimal)

            from_addr = (transfer.get('address_from') or transfer.get('from') or '').lower()
            to_addr = (transfer.get('address_to') or transfer.get('to') or '').lower()
            if not from_addr or not to_addr:
                dropped_no_address += 1
                self.logger.debug('缺少地址，跳过: %s', transfer)
                continue

            if self.reverse_edge:
                from_addr, to_addr = to_addr, from_addr
            
            # 规范化 contract_address：
            # - Token20/721/1155TransferItem 有 contract_address 字段
            # - TransactionItem/TraceItem（原生 ETH）contract_address 为空串
            # - 空串代表原生币（ETH/BNB/MATIC 等），DTTR 会根据链识别
            contract_addr = transfer.get('contract_address', '')
            if not contract_addr:
                # 兼容旧字段名
                contract_addr = transfer.get('contractAddress', '')

            # 受保护地修改 batch_graph
            # 重要：contractAddress 和 timeStamp 用于 DTTR 的 USD 价格查询（若启用 DTT_IS_IN_USD）
            flush_now = False
            with self.lock:
                self.batch_graph.add_edge(
                    from_addr,
                    to_addr,
                    value=value_str,
                    contractAddress=contract_addr,
                    timeStamp=int(transfer.get('timestamp', 0) or 0)
                )
                processed_count += 1
                edge_count = self.batch_graph.number_of_edges()
                if edge_count >= self.batch_size:
                    # 交换出去当前图并新建一个
                    g_to_process = self.batch_graph
                    self.batch_graph = nx.MultiDiGraph()
                    flush_now = True

            if flush_now:
                try:
                    # 在锁外调用 dttr（可能耗时）
                    self.ttr_instance.transaction_arrive(g_to_process)
                    self.logger.info(f'已 flush batch: edges={edge_count}, 处理={processed_count}, 丢弃无地址={dropped_no_address}')
                except Exception:
                    self.logger.exception('DTTR 处理失败')

        self.logger.info(f'本批次完成: 处理={processed_count}, 丢弃无地址={dropped_no_address}')
        return item

    def close_spider(self, spider):
        # flush 剩余数据
        with self.lock:
            g_remaining = self.batch_graph if self.batch_graph.number_of_edges() > 0 else None
            self.batch_graph = nx.MultiDiGraph()

        if g_remaining:
            try:
                self.ttr_instance.transaction_arrive(g_remaining)
            except Exception:
                self.logger.exception('DTTR 处理剩余 batch 失败')

        # 持久化结果：优先使用配置的 result_file（DTT_RESULT_FILE），否则使用 spider.name 并保证以 .csv 结尾
        import os
        if isinstance(self.result_file, str) and self.result_file:
            file_path = self.result_file
        else:
            spider_name = getattr(spider, 'name', 'DTTR_result')
            file_path = os.path.join(os.getcwd(), f'{spider_name}.csv')

        # 如果用户传入的路径没有 .csv 扩展名，追加它
        if not file_path.lower().endswith('.csv'):
            file_path = file_path + '.csv'

        # 确保目录存在
        dirpath = os.path.dirname(file_path)
        if dirpath and not os.path.exists(dirpath):
            try:
                os.makedirs(dirpath, exist_ok=True)
            except Exception:
                self.logger.exception('创建结果目录失败：%s', dirpath)

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['区块链地址', '重要性得分(p值)'])
                sorted_result = sorted(self.ttr_instance.p.items(), key=lambda x: x[1], reverse=True)
                for addr, p_value in sorted_result:
                    # p_value 可能是 Decimal
                    try:
                        writer.writerow([addr, float(p_value)])
                    except Exception:
                        writer.writerow([addr, str(p_value)])
            self.logger.info('DTTR 结果已保存到：%s', file_path)
        except Exception:
            self.logger.exception('写 DTTR 结果 CSV 失败')