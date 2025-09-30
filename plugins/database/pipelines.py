"""
数据库导出管道
"""
import logging
from typing import Dict, List, Any
from datetime import datetime

from BlockchainSpider.pipelines.sync import unpacked_sync_item
from .config import DatabaseConfig
from .adapter import PostgreSQLAdapter
from .models import MODEL_MAPPING, FIELD_MAPPING
from .utils import convert_item_to_dict, handle_jsonb_fields, clean_data


class DatabasePipeline:
    """
    数据库导出管道
    
    支持将 BlockchainSpider 爬取的数据直接写入 PostgreSQL 数据库
    """
    
    def __init__(self):
        self.config = None
        self.adapter = None
        self.batch_data = {}
        self.batch_size = 1000
        self.logger = logging.getLogger(self.__class__.__name__)
        self.used_models = set()  # 记录实际使用的模型
        
        # 统计信息
        self.stats = {
            'total_items': 0,
            'inserted_items': 0,
            'failed_items': 0,
            'duplicate_items': 0,
        }
    
    def open_spider(self, spider):
        """初始化数据库连接"""
        try:
            self.logger.info('')
            self.logger.info('╔' + '═' * 58 + '╗')
            self.logger.info('║' + ' ' * 10 + '🚀 Database Pipeline Starting' + ' ' * 18 + '║')
            self.logger.info('╚' + '═' * 58 + '╝')
            self.logger.info('')
            
            # 从爬虫获取配置
            self.logger.info('📝 Loading database configuration...')
            self.config = DatabaseConfig.from_spider(spider)
            self.batch_size = self.config.batch_size
            self.logger.info(f'✓ Batch size: {self.batch_size}')
            self.logger.info(f'✓ Auto create tables: {self.config.auto_create_tables}')
            self.logger.info(f'✓ Database: {self.config.database}')
            self.logger.info('')
            
            # 创建数据库适配器
            self.logger.info('🔧 Initializing PostgreSQL adapter...')
            self.adapter = PostgreSQLAdapter(self.config)
            self.adapter.connect()
            
            # 注意：暂不创建表，等收到第一个数据项时按需创建
            # 这样可以避免创建不需要的表
            
            # 健康检查
            self.logger.info('🏥 Performing health check...')
            if not self.adapter.health_check():
                raise RuntimeError('❌ Database health check failed')
            self.logger.info('✅ Health check passed!')
            
            self.logger.info('')
            self.logger.info('╔' + '═' * 58 + '╗')
            self.logger.info('║' + ' ' * 8 + '✅ Database Pipeline Ready!' + ' ' * 20 + '║')
            self.logger.info('║' + f' Type: {self.config.db_type}'.ljust(59) + '║')
            self.logger.info('║' + f' Host: {self.config.host}:{self.config.port}'.ljust(59) + '║')
            self.logger.info('║' + f' Database: {self.config.database}'.ljust(59) + '║')
            self.logger.info('╚' + '═' * 58 + '╝')
            self.logger.info('')
            
        except Exception as e:
            self.logger.error(f'Failed to initialize database pipeline: {e}')
            raise
    
    @unpacked_sync_item
    def process_item(self, item, spider):
        """处理数据项"""
        if not self.adapter:
            return item
        
        try:
            self.stats['total_items'] += 1
            
            # 获取对应的模型类
            item_class_name = item.__class__.__name__
            model_class = MODEL_MAPPING.get(item_class_name)
            
            if not model_class:
                self.logger.debug(f'No model mapping for {item_class_name}, skipping')
                return item
            
            # 按需创建表（第一次遇到这种类型时）
            if model_class not in self.used_models:
                self._ensure_table_exists(model_class)
                self.used_models.add(model_class)
            
            # 转换数据格式
            data = self._convert_and_clean_item(item, item_class_name)
            
            # 添加到批量数据
            if item_class_name not in self.batch_data:
                self.batch_data[item_class_name] = []
            
            self.batch_data[item_class_name].append(data)
            
            # 检查是否需要批量插入
            if len(self.batch_data[item_class_name]) >= self.batch_size:
                self._flush_batch(item_class_name, model_class)
            
            return item
            
        except Exception as e:
            self.logger.error(f'Error processing item: {e}', exc_info=True)
            self.stats['failed_items'] += 1
            return item
    
    def _ensure_table_exists(self, model_class):
        """
        确保表存在（按需创建）
        
        Args:
            model_class: 数据库模型类
        """
        if not self.config.auto_create_tables:
            return
        
        try:
            self.adapter.create_tables(models_to_create=[model_class])
            self.logger.info(f'📊 Created table: {model_class.__tablename__}')
        except Exception as e:
            self.logger.warning(f'Failed to create table {model_class.__tablename__}: {e}')
    
    def _convert_and_clean_item(self, item, item_class_name: str) -> Dict[str, Any]:
        """
        转换和清理数据项
        
        Args:
            item: Scrapy Item 对象
            item_class_name: Item 类名
            
        Returns:
            清理后的数据字典
        """
        # 转换为字典
        data = convert_item_to_dict(item, FIELD_MAPPING)
        
        # 清理数据
        data = clean_data(data)
        
        # 处理特殊字段
        data = self._handle_special_fields(data, item_class_name)
        
        # 添加创建时间
        if 'created_at' not in data:
            data['created_at'] = datetime.utcnow()
        
        return data
    
    def _handle_special_fields(self, data: Dict[str, Any], item_class_name: str) -> Dict[str, Any]:
        """
        处理特殊字段
        
        Args:
            data: 数据字典
            item_class_name: Item 类名
            
        Returns:
            处理后的数据字典
        """
        # EventLogItem: 处理 topics 字段
        if item_class_name == 'EventLogItem':
            # topics 字段需要转换为 JSONB
            if 'topics' in data and not isinstance(data['topics'], (list, dict)):
                data['topics'] = []
            data = handle_jsonb_fields(data, ['topics'])
        
        # Token1155TransferItem: 处理数组字段
        if item_class_name == 'Token1155TransferItem':
            data = handle_jsonb_fields(data, ['token_ids', 'values'])
        
        # TraceItem: 处理 trace_address 字段
        if item_class_name == 'TraceItem':
            data = handle_jsonb_fields(data, ['trace_address'])
        
        # LabelReportItem: 处理所有 JSON 字段
        if item_class_name == 'LabelReportItem':
            data = handle_jsonb_fields(data, ['labels', 'urls', 'addresses', 'transactions'])
        
        # TronTransactionItem: 处理 raw_data 字段
        if item_class_name == 'TronTransactionItem':
            data = handle_jsonb_fields(data, ['raw_data'])
        
        # ABIItem: 处理 abi 字段
        if item_class_name == 'ABIItem':
            data = handle_jsonb_fields(data, ['abi'])
        
        # SolanaInstructionItem 及其子类: 处理 JSON 字段
        if item_class_name in ['SolanaInstructionItem', 'SPLTokenActionItem', 'SPLMemoItem', 'ValidateVotingItem', 'SystemItem']:
            data = handle_jsonb_fields(data, ['accounts', 'info'])
        
        return data
    
    def _flush_batch(self, item_class_name: str, model_class):
        """
        执行批量插入
        
        Args:
            item_class_name: Item 类名
            model_class: 数据库模型类
        """
        if item_class_name not in self.batch_data:
            return
        
        data_list = self.batch_data[item_class_name]
        if not data_list:
            return
        
        try:
            inserted_count = self.adapter.insert_batch(model_class, data_list)
            
            self.stats['inserted_items'] += inserted_count
            self.stats['duplicate_items'] += len(data_list) - inserted_count
            
            # 使用更醒目的日志
            if inserted_count == len(data_list):
                self.logger.info(
                    f'💾 Inserted {inserted_count} {item_class_name} → {model_class.__tablename__}'
                )
            else:
                self.logger.info(
                    f'💾 Inserted {inserted_count}/{len(data_list)} {item_class_name} → '
                    f'{model_class.__tablename__} (skipped {len(data_list) - inserted_count} duplicates)'
                )
            
        except Exception as e:
            self.logger.error(
                f'Failed to flush batch for {item_class_name}: {e}',
                exc_info=True
            )
            self.stats['failed_items'] += len(data_list)
            
        finally:
            self.batch_data[item_class_name] = []
    
    def close_spider(self, spider):
        """关闭爬虫时处理剩余数据"""
        try:
            # 处理剩余的批量数据
            for item_class_name, data_list in self.batch_data.items():
                if data_list:
                    model_class = MODEL_MAPPING.get(item_class_name)
                    if model_class:
                        inserted_count = self.adapter.insert_batch(model_class, data_list)
                        
                        self.stats['inserted_items'] += inserted_count
                        self.stats['duplicate_items'] += len(data_list) - inserted_count
                        
                        self.logger.info(
                            f'Final flush: {inserted_count}/{len(data_list)} '
                            f'{item_class_name} records'
                        )
            
            # 打印统计信息
            self._print_stats()
            
            # 关闭数据库连接
            if self.adapter:
                self.adapter.disconnect()
            
            self.logger.info('Database pipeline closed')
            
        except Exception as e:
            self.logger.error(f'Error closing database pipeline: {e}', exc_info=True)
    
    def _print_stats(self):
        """打印统计信息"""
        self.logger.info('')
        self.logger.info('╔' + '═' * 58 + '╗')
        self.logger.info('║' + ' ' * 15 + '📊 Final Statistics' + ' ' * 23 + '║')
        self.logger.info('╠' + '═' * 58 + '╣')
        self.logger.info('║' + f'  Total items processed: {self.stats["total_items"]}'.ljust(59) + '║')
        self.logger.info('║' + f'  ✅ Successfully inserted: {self.stats["inserted_items"]}'.ljust(59) + '║')
        self.logger.info('║' + f'  ⏭️  Duplicate items: {self.stats["duplicate_items"]}'.ljust(59) + '║')
        self.logger.info('║' + f'  ❌ Failed items: {self.stats["failed_items"]}'.ljust(59) + '║')
        self.logger.info('╚' + '═' * 58 + '╝')
        self.logger.info('')
        
        if self.stats['inserted_items'] > 0:
            self.logger.info('🎉 Data successfully saved to PostgreSQL database!')
            self.logger.info(f'   Database: {self.config.database}')
            self.logger.info(f'   Location: {self.config.host}:{self.config.port}')
            self.logger.info('') 