"""
PostgreSQL 数据库适配器
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import IntegrityError, OperationalError
from typing import List, Dict, Any, Type
import logging
import time
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .config import DatabaseConfig
from .models import Base


class PostgreSQLAdapter:
    """PostgreSQL 数据库适配器"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = None
        self.session_factory = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _ensure_database_exists(self):
        """
        确保数据库存在，如果不存在则自动创建
        """
        try:
            # 连接到默认的 postgres 数据库
            self.logger.info('=' * 60)
            self.logger.info(f'🔍 Checking if database "{self.config.database}" exists...')
            
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database='postgres'  # 连接到默认数据库
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # 检查数据库是否存在
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.config.database,)
            )
            exists = cursor.fetchone()
            
            if exists:
                self.logger.info(f'✓ Database "{self.config.database}" already exists')
            else:
                # 创建数据库
                self.logger.info(f'📁 Database "{self.config.database}" does not exist')
                self.logger.info(f'🔨 Creating database "{self.config.database}"...')
                cursor.execute(f'CREATE DATABASE {self.config.database}')
                self.logger.info(f'✅ Database "{self.config.database}" created successfully!')
            
            cursor.close()
            conn.close()
            self.logger.info('=' * 60)
            
        except psycopg2.Error as e:
            self.logger.warning(f'⚠️  Could not auto-create database: {e}')
            self.logger.info('Attempting to connect anyway...')
    
    def connect(self):
        """建立数据库连接"""
        try:
            # 先尝试确保数据库存在
            self._ensure_database_exists()
            
            # 构建连接 URL
            connection_url = self.config.get_connection_url()
            
            # 创建引擎
            self.engine = create_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                echo=self.config.echo,
                echo_pool=self.config.echo_pool,
            )
            
            # 添加连接池事件监听
            @event.listens_for(self.engine, 'connect')
            def receive_connect(dbapi_conn, connection_record):
                self.logger.debug('Database connection established')
            
            @event.listens_for(self.engine, 'checkout')
            def receive_checkout(dbapi_conn, connection_record, connection_proxy):
                self.logger.debug('Connection checked out from pool')
            
            # 创建会话工厂
            self.session_factory = sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
            )
            
            # 测试连接
            self.logger.info('🔌 Testing database connection...')
            from sqlalchemy import text
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            self.logger.info('✅ Database connection test successful!')
            
            self.logger.info('=' * 60)
            self.logger.info(f'✅ PostgreSQL connected: {self.config}')
            self.logger.info('=' * 60)
            
        except Exception as e:
            self.logger.error(f'Failed to connect to PostgreSQL: {e}')
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            self.engine.dispose()
            self.logger.info('PostgreSQL connection closed')
    
    def create_tables(self, models_to_create=None):
        """
        创建数据表
        
        Args:
            models_to_create: 要创建的模型列表，None 表示创建所有表
        """
        try:
            from sqlalchemy import text
            self.logger.info('=' * 60)
            self.logger.info('📊 Creating database tables...')
            
            # 如果指定了 schema，则创建 schema
            if self.config.schema:
                self.logger.info(f'🔨 Creating schema "{self.config.schema}"...')
                with self.engine.connect() as conn:
                    conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {self.config.schema}'))
                    conn.commit()
                self.logger.info(f'✓ Schema "{self.config.schema}" created')
            
            # 创建表
            if models_to_create is None:
                # 创建所有表
                table_count = len(Base.metadata.tables)
                self.logger.info(f'🔨 Creating all {table_count} tables...')
                Base.metadata.create_all(self.engine)
            else:
                # 只创建指定的表
                table_count = len(models_to_create)
                self.logger.info(f'🔨 Creating {table_count} tables (on-demand)...')
                tables_to_create = [model.__table__ for model in models_to_create]
                Base.metadata.create_all(self.engine, tables=tables_to_create)
            
            # 列出创建的表
            self.logger.info(f'✅ Successfully created {table_count} tables')
            
            self.logger.info('=' * 60)
            
        except Exception as e:
            self.logger.error(f'Failed to create PostgreSQL tables: {e}')
            raise
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        if not self.session_factory:
            raise RuntimeError('Database not connected')
        return self.session_factory()
    
    def insert_batch(self, model_class: Type, data_list: List[Dict[str, Any]]) -> int:
        """
        批量插入数据
        
        Args:
            model_class: 模型类
            data_list: 数据列表
            
        Returns:
            成功插入的记录数
        """
        if not data_list:
            return 0
        
        session = self.get_session()
        inserted_count = 0
        
        try:
            # 使用 bulk_insert_mappings 提高性能
            session.bulk_insert_mappings(
                model_class,
                data_list,
                render_nulls=False,
            )
            session.commit()
            inserted_count = len(data_list)
            self.logger.debug(
                f'Batch inserted {inserted_count} records into {model_class.__tablename__}'
            )
            
        except IntegrityError as e:
            session.rollback()
            
            if self.config.ignore_duplicate:
                # 逐条插入，忽略重复数据
                inserted_count = self._insert_one_by_one(
                    session, model_class, data_list
                )
            else:
                self.logger.error(f'Integrity error in batch insert: {e}')
                raise
                
        except OperationalError as e:
            session.rollback()
            self.logger.error(f'Operational error in batch insert: {e}')
            
            # 重试机制
            for retry in range(self.config.retry_times):
                try:
                    time.sleep(self.config.retry_delay * (retry + 1))
                    self.logger.info(f'Retrying batch insert (attempt {retry + 1})')
                    
                    session = self.get_session()
                    session.bulk_insert_mappings(model_class, data_list)
                    session.commit()
                    inserted_count = len(data_list)
                    break
                    
                except Exception as retry_e:
                    self.logger.error(f'Retry {retry + 1} failed: {retry_e}')
                    session.rollback()
                    
        except Exception as e:
            session.rollback()
            self.logger.error(f'Unexpected error in batch insert: {e}')
            raise
            
        finally:
            session.close()
        
        return inserted_count
    
    def insert_single(self, model_class: Type, data: Dict[str, Any]) -> bool:
        """
        单条插入数据
        
        Args:
            model_class: 模型类
            data: 数据字典
            
        Returns:
            是否插入成功
        """
        session = self.get_session()
        
        try:
            instance = model_class(**data)
            session.add(instance)
            session.commit()
            self.logger.debug(f'Inserted 1 record into {model_class.__tablename__}')
            return True
            
        except IntegrityError as e:
            session.rollback()
            
            if self.config.ignore_duplicate:
                self.logger.debug(f'Duplicate record ignored: {e}')
                return False
            else:
                self.logger.error(f'Integrity error in single insert: {e}')
                raise
                
        except Exception as e:
            session.rollback()
            self.logger.error(f'Error in single insert: {e}')
            raise
            
        finally:
            session.close()
    
    def _insert_one_by_one(
        self,
        session: Session,
        model_class: Type,
        data_list: List[Dict[str, Any]]
    ) -> int:
        """
        逐条插入数据（用于处理重复键冲突）
        
        Args:
            session: 数据库会话
            model_class: 模型类
            data_list: 数据列表
            
        Returns:
            成功插入的记录数
        """
        inserted_count = 0
        
        for data in data_list:
            try:
                instance = model_class(**data)
                session.add(instance)
                session.commit()
                inserted_count += 1
                
            except IntegrityError:
                session.rollback()
                self.logger.debug('Duplicate record skipped')
                continue
                
            except Exception as e:
                session.rollback()
                self.logger.error(f'Error inserting record: {e}')
                continue
        
        self.logger.info(
            f'Inserted {inserted_count}/{len(data_list)} records '
            f'(ignored {len(data_list) - inserted_count} duplicates)'
        )
        
        return inserted_count
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            from sqlalchemy import text
            session = self.get_session()
            try:
                session.execute(text('SELECT 1'))
                return True
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f'Database health check failed: {e}')
            return False
    
    def get_table_count(self, model_class: Type) -> int:
        """获取表记录数"""
        session = self.get_session()
        try:
            count = session.query(model_class).count()
            return count
        finally:
            session.close()
    
    def truncate_table(self, model_class: Type):
        """清空表数据"""
        session = self.get_session()
        try:
            session.query(model_class).delete()
            session.commit()
            self.logger.info(f'Table {model_class.__tablename__} truncated')
        except Exception as e:
            session.rollback()
            self.logger.error(f'Failed to truncate table: {e}')
            raise
        finally:
            session.close() 