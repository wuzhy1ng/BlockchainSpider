"""
数据库配置管理模块
"""
import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """数据库配置类"""
    
    # 数据库连接 URL（优先使用）
    db_url: Optional[str] = None
    
    # 数据库类型
    db_type: str = 'postgresql'
    
    # 连接配置（URL 未提供时使用）
    host: str = 'localhost'
    port: int = 5432
    user: str = 'postgres'
    password: str = ''
    database: str = 'blockchain'
    
    # 连接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    
    # 批量操作配置
    batch_size: int = 1000
    batch_timeout: int = 30
    
    # 表配置
    auto_create_tables: bool = True
    table_prefix: str = 'bs_'
    schema: Optional[str] = None
    
    # 错误处理
    retry_times: int = 3
    retry_delay: int = 1
    ignore_duplicate: bool = True
    
    # 日志配置
    echo: bool = False
    echo_pool: bool = False
    
    @classmethod
    def from_spider(cls, spider) -> 'DatabaseConfig':
        """从爬虫参数创建配置"""
        # 优先使用 db_url
        db_url = getattr(spider, 'db_url', None)
        
        if db_url:
            # 从 URL 解析配置
            return cls._from_url(
                db_url,
                batch_size=int(getattr(spider, 'batch_size', 1000)),
                auto_create_tables=bool(getattr(spider, 'auto_create_tables', True)),
                schema=getattr(spider, 'db_schema', None),
            )
        else:
            # 从独立参数创建
            return cls(
                db_type=getattr(spider, 'db_type', 'postgresql'),
                host=getattr(spider, 'db_host', 'localhost'),
                port=int(getattr(spider, 'db_port', 5432)),
                user=getattr(spider, 'db_user', 'postgres'),
                password=getattr(spider, 'db_password', ''),
                database=getattr(spider, 'db_name', 'blockchain'),
                batch_size=int(getattr(spider, 'batch_size', 1000)),
                auto_create_tables=bool(getattr(spider, 'auto_create_tables', True)),
                table_prefix=getattr(spider, 'table_prefix', 'bs_'),
                schema=getattr(spider, 'db_schema', None),
                echo=bool(getattr(spider, 'db_echo', False)),
            )
    
    @classmethod
    def _from_url(cls, db_url: str, **kwargs) -> 'DatabaseConfig':
        """从数据库 URL 创建配置"""
        import re
        
        # 解析 PostgreSQL URL: postgresql://user:password@host:port/database
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, db_url)
        
        if not match:
            raise ValueError(f'Invalid database URL format: {db_url}')
        
        user, password, host, port, database = match.groups()
        
        return cls(
            db_url=db_url,
            db_type='postgresql',
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            **kwargs
        )
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """从环境变量创建配置"""
        # 优先使用 DATABASE_URL
        db_url = os.getenv('DATABASE_URL')
        
        if db_url:
            return cls._from_url(
                db_url,
                batch_size=int(os.getenv('DB_BATCH_SIZE', '1000')),
                schema=os.getenv('DB_SCHEMA', None),
            )
        else:
            return cls(
                db_type=os.getenv('DB_TYPE', 'postgresql'),
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5432')),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'blockchain'),
                batch_size=int(os.getenv('DB_BATCH_SIZE', '1000')),
                table_prefix=os.getenv('DB_TABLE_PREFIX', 'bs_'),
                schema=os.getenv('DB_SCHEMA', None),
            )
    
    def get_connection_url(self) -> str:
        """获取数据库连接 URL"""
        # 如果已经有 URL，直接返回（添加驱动）
        if self.db_url:
            if self.db_url.startswith('postgresql://'):
                return self.db_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
            return self.db_url
        
        # 从配置参数构建 URL
        if self.db_type == 'postgresql':
            url = f'postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'
        else:
            raise ValueError(f'Unsupported database type: {self.db_type}')
        
        return url
    
    def __str__(self) -> str:
        """字符串表示（隐藏密码）"""
        return (
            f'DatabaseConfig(db_type={self.db_type}, '
            f'host={self.host}, port={self.port}, '
            f'user={self.user}, database={self.database})'
        ) 