"""
Database Export Plugin for BlockchainSpider
支持 PostgreSQL 数据库的区块链数据导出插件
"""

from .pipelines import DatabasePipeline
from .config import DatabaseConfig
from .models import Base, MODEL_MAPPING

__version__ = '1.0.0'
__author__ = 'BlockchainSpider Team'

# 导出主要类
__all__ = [
    'DatabasePipeline',
    'DatabaseConfig',
    'Base',
    'MODEL_MAPPING',
] 