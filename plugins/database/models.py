"""
数据库模型定义
支持 BlockchainSpider 所有数据类型
"""
from sqlalchemy import Column, String, BigInteger, Numeric, DateTime, Text, Integer, Boolean, Index, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()


class TransactionModel(Base):
    """交易数据模型"""
    __tablename__ = 'bs_transactions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), unique=True, nullable=False, index=True)
    transaction_index = Column(Integer, nullable=True)
    block_hash = Column(String(66), nullable=True, index=True)
    block_number = Column(BigInteger, nullable=True, index=True)
    timestamp = Column(BigInteger, nullable=True, index=True)
    address_from = Column(String(42), nullable=True, index=True)
    address_to = Column(String(42), nullable=True, index=True)
    value = Column(Numeric(78, 0), nullable=True, default=0)
    gas = Column(BigInteger, nullable=True)
    gas_price = Column(BigInteger, nullable=True)
    nonce = Column(BigInteger, nullable=True)
    input = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_tx_block_from', 'block_number', 'address_from'),
        Index('idx_tx_block_to', 'block_number', 'address_to'),
        Index('idx_tx_timestamp', 'timestamp'),
    )


class TransactionReceiptModel(Base):
    """交易收据模型"""
    __tablename__ = 'bs_transaction_receipts'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), unique=True, nullable=False, index=True)
    block_number = Column(BigInteger, nullable=True, index=True)
    gas_used = Column(BigInteger, nullable=True)
    cumulative_gas_used = Column(BigInteger, nullable=True)
    contract_address = Column(String(42), nullable=True, index=True)
    status = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BlockModel(Base):
    """区块数据模型"""
    __tablename__ = 'bs_blocks'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    block_hash = Column(String(66), unique=True, nullable=False, index=True)
    block_number = Column(BigInteger, unique=True, nullable=False, index=True)
    parent_hash = Column(String(66), nullable=True)
    difficulty = Column(Numeric(78, 0), nullable=True)
    total_difficulty = Column(Numeric(78, 0), nullable=True)
    size = Column(BigInteger, nullable=True)
    gas_limit = Column(BigInteger, nullable=True)
    gas_used = Column(BigInteger, nullable=True)
    miner = Column(String(42), nullable=True, index=True)
    receipts_root = Column(String(66), nullable=True)
    timestamp = Column(BigInteger, nullable=True, index=True)
    logs_bloom = Column(Text, nullable=True)
    nonce = Column(String(66), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Token20TransferModel(Base):
    """ERC20 代币转账模型"""
    __tablename__ = 'bs_token20_transfers'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), nullable=False, index=True)
    log_index = Column(Integer, nullable=True)
    block_number = Column(BigInteger, nullable=True, index=True)
    timestamp = Column(BigInteger, nullable=True, index=True)
    contract_address = Column(String(42), nullable=False, index=True)
    address_from = Column(String(42), nullable=True, index=True)
    address_to = Column(String(42), nullable=True, index=True)
    value = Column(Numeric(78, 0), nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_token20_tx_contract', 'transaction_hash', 'contract_address'),
        Index('idx_token20_block_contract', 'block_number', 'contract_address'),
        Index('idx_token20_from_to', 'address_from', 'address_to'),
    )


class Token721TransferModel(Base):
    """ERC721 NFT 转账模型"""
    __tablename__ = 'bs_token721_transfers'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), nullable=False, index=True)
    log_index = Column(String(20), nullable=True)
    block_number = Column(BigInteger, nullable=True, index=True)
    timestamp = Column(BigInteger, nullable=True, index=True)
    contract_address = Column(String(42), nullable=False, index=True)
    address_from = Column(String(42), nullable=True, index=True)
    address_to = Column(String(42), nullable=True, index=True)
    token_id = Column(Numeric(78, 0), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_token721_contract_tokenid', 'contract_address', 'token_id'),
        Index('idx_token721_from_to', 'address_from', 'address_to'),
    )


class Token1155TransferModel(Base):
    """ERC1155 代币转账模型"""
    __tablename__ = 'bs_token1155_transfers'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), nullable=False, index=True)
    log_index = Column(Integer, nullable=True)
    block_number = Column(String(20), nullable=True, index=True)
    timestamp = Column(BigInteger, nullable=True, index=True)
    contract_address = Column(String(42), nullable=False, index=True)
    address_operator = Column(String(42), nullable=True, index=True)
    address_from = Column(String(42), nullable=True, index=True)
    address_to = Column(String(42), nullable=True, index=True)
    token_ids = Column(JSONB, nullable=True)
    values = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EventLogModel(Base):
    """事件日志模型"""
    __tablename__ = 'bs_event_logs'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), nullable=False, index=True)
    block_number = Column(BigInteger, nullable=True, index=True)
    contract_address = Column(String(42), nullable=True, index=True)
    log_index = Column(Integer, nullable=True)
    topics = Column(JSONB, nullable=True)
    data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_log_tx_index', 'transaction_hash', 'log_index'),
        Index('idx_log_contract_block', 'contract_address', 'block_number'),
    )


class TraceModel(Base):
    """交易追踪模型"""
    __tablename__ = 'bs_traces'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), nullable=False, index=True)
    block_number = Column(BigInteger, nullable=True, index=True)
    trace_address = Column(JSONB, nullable=True)
    trace_type = Column(String(20), nullable=True)
    call_type = Column(String(20), nullable=True)
    address_from = Column(String(42), nullable=True, index=True)
    address_to = Column(String(42), nullable=True, index=True)
    value = Column(Numeric(78, 0), nullable=True)
    gas = Column(BigInteger, nullable=True)
    gas_used = Column(BigInteger, nullable=True)
    input = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AccountTransferModel(Base):
    """账户转账模型（转账子图）"""
    __tablename__ = 'bs_account_transfers'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transfer_id = Column(String(100), unique=True, nullable=False)
    hash = Column(String(66), nullable=True, index=True)
    address_from = Column(String(42), nullable=True, index=True)
    address_to = Column(String(42), nullable=True, index=True)
    value = Column(String(100), nullable=True)
    token_id = Column(String(100), nullable=True)
    timestamp = Column(BigInteger, nullable=True, index=True)
    block_number = Column(BigInteger, nullable=True, index=True)
    contract_address = Column(String(42), nullable=True, index=True)
    symbol = Column(String(20), nullable=True)
    decimals = Column(Integer, nullable=True)
    gas = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LabelReportModel(Base):
    """标签报告模型"""
    __tablename__ = 'bs_label_reports'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    labels = Column(JSONB, nullable=True)
    urls = Column(JSONB, nullable=True)
    addresses = Column(JSONB, nullable=True)
    transactions = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)
    reporter = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SolanaTransactionModel(Base):
    """Solana 交易模型"""
    __tablename__ = 'bs_solana_transactions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signature = Column(String(88), unique=True, nullable=False, index=True)
    signer = Column(String(44), nullable=True, index=True)
    block_time = Column(BigInteger, nullable=True, index=True)
    block_height = Column(BigInteger, nullable=True, index=True)
    version = Column(String(20), nullable=True)
    fee = Column(BigInteger, nullable=True)
    compute_consumed = Column(BigInteger, nullable=True)
    err = Column(Text, nullable=True)
    recent_blockhash = Column(String(44), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SolanaBlockModel(Base):
    """Solana 区块模型"""
    __tablename__ = 'bs_solana_blocks'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    block_hash = Column(String(44), unique=True, nullable=False, index=True)
    block_height = Column(BigInteger, unique=True, nullable=False, index=True)
    block_time = Column(BigInteger, nullable=True, index=True)
    parent_slot = Column(String(20), nullable=True)
    previous_blockhash = Column(String(44), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContractModel(Base):
    """合约字节码模型"""
    __tablename__ = 'bs_contracts'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    address = Column(String(42), unique=True, nullable=False, index=True)
    code = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TokenApprovalModel(Base):
    """代币授权模型"""
    __tablename__ = 'bs_token_approvals'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), nullable=False, index=True)
    log_index = Column(Integer, nullable=True)
    block_number = Column(String(20), nullable=True, index=True)
    timestamp = Column(BigInteger, nullable=True, index=True)
    contract_address = Column(String(42), nullable=False, index=True)
    address_from = Column(String(42), nullable=True, index=True)
    address_to = Column(String(42), nullable=True, index=True)
    value = Column(Numeric(78, 0), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TokenApprovalAllModel(Base):
    """代币全部授权模型"""
    __tablename__ = 'bs_token_approval_all'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), nullable=False, index=True)
    log_index = Column(Integer, nullable=True)
    block_number = Column(String(20), nullable=True, index=True)
    timestamp = Column(BigInteger, nullable=True, index=True)
    contract_address = Column(String(42), nullable=False, index=True)
    address_from = Column(String(42), nullable=True, index=True)
    address_to = Column(String(42), nullable=True, index=True)
    approved = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TokenPropertyModel(Base):
    """代币属性模型"""
    __tablename__ = 'bs_token_properties'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_address = Column(String(42), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    token_symbol = Column(String(20), nullable=True)
    decimals = Column(Integer, nullable=True)
    total_supply = Column(Numeric(78, 0), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NFTMetadataModel(Base):
    """NFT 元数据模型"""
    __tablename__ = 'bs_nft_metadata'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_address = Column(String(42), nullable=False, index=True)
    token_id = Column(Numeric(78, 0), nullable=False, index=True)
    uri = Column(Text, nullable=True)
    data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_nft_contract_token', 'contract_address', 'token_id', unique=True),
    )


class TronTransactionModel(Base):
    """TRON 交易模型"""
    __tablename__ = 'bs_tron_transactions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(64), unique=True, nullable=False, index=True)
    transaction_index = Column(Integer, nullable=True)
    block_hash = Column(String(64), nullable=True, index=True)
    block_number = Column(BigInteger, nullable=True, index=True)
    block_version = Column(Integer, nullable=True)
    timestamp = Column(BigInteger, nullable=True, index=True)
    raw_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UTXOTransferModel(Base):
    """UTXO 转账模型（比特币）"""
    __tablename__ = 'bs_utxo_transfers'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transfer_id = Column(String(100), unique=True, nullable=False)
    tx_from = Column(String(100), nullable=True, index=True)
    tx_to = Column(String(100), nullable=True, index=True)
    address = Column(String(100), nullable=True, index=True)
    value = Column(String(100), nullable=True)
    is_spent = Column(Boolean, nullable=True)
    is_coinbase = Column(Boolean, nullable=True)
    timestamp = Column(BigInteger, nullable=True, index=True)
    block_number = Column(BigInteger, nullable=True, index=True)
    fee = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SourceCodeModel(Base):
    """合约源代码模型"""
    __tablename__ = 'bs_source_codes'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_address = Column(String(42), unique=True, nullable=False, index=True)
    compiler_version = Column(String(50), nullable=True)
    evm_version = Column(String(50), nullable=True)
    contract_name = Column(String(100), nullable=True)
    library = Column(Text, nullable=True)
    proxy = Column(String(42), nullable=True)
    optimization = Column(Boolean, nullable=True)
    runs = Column(Integer, nullable=True)
    source_code = Column(Text, nullable=True)
    constructor_arguments = Column(Text, nullable=True)
    license = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ABIModel(Base):
    """合约 ABI 模型"""
    __tablename__ = 'bs_abis'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_address = Column(String(42), unique=True, nullable=False, index=True)
    abi = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SignModel(Base):
    """函数签名模型"""
    __tablename__ = 'bs_signatures'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sign = Column(String(10), unique=True, nullable=False, index=True)
    text = Column(String(500), nullable=True)
    sign_type = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SolanaBalanceChangesModel(Base):
    """Solana 余额变化模型"""
    __tablename__ = 'bs_solana_balance_changes'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signature = Column(String(88), nullable=False, index=True)
    account = Column(String(44), nullable=True, index=True)
    mint = Column(String(44), nullable=True, index=True)
    owner = Column(String(44), nullable=True, index=True)
    program_id = Column(String(44), nullable=True, index=True)
    pre_amount = Column(String(50), nullable=True)
    post_amount = Column(String(50), nullable=True)
    decimals = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SolanaInstructionModel(Base):
    """Solana 指令模型"""
    __tablename__ = 'bs_solana_instructions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signature = Column(String(88), nullable=False, index=True)
    trace_id = Column(String(50), nullable=True)
    data = Column(Text, nullable=True)
    program_id = Column(String(44), nullable=True, index=True)
    accounts = Column(JSONB, nullable=True)
    dtype = Column(String(50), nullable=True)
    info = Column(JSONB, nullable=True)
    program = Column(String(44), nullable=True)
    memo = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SolanaLogModel(Base):
    """Solana 日志模型"""
    __tablename__ = 'bs_solana_logs'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signature = Column(String(88), nullable=False, index=True)
    index = Column(String(20), nullable=True)
    log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# 模型映射：Item 类名 -> 数据库模型类
MODEL_MAPPING = {
    # EVM 链数据
    'TransactionItem': TransactionModel,
    'TransactionReceiptItem': TransactionReceiptModel,
    'BlockItem': BlockModel,
    'Token20TransferItem': Token20TransferModel,
    'Token721TransferItem': Token721TransferModel,
    'Token1155TransferItem': Token1155TransferModel,
    'EventLogItem': EventLogModel,
    'TraceItem': TraceModel,
    'ContractItem': ContractModel,
    'TokenApprovalItem': TokenApprovalModel,
    'TokenApprovalAllItem': TokenApprovalAllModel,
    'TokenPropertyItem': TokenPropertyModel,
    'NFTMetadataItem': NFTMetadataModel,
    
    # 转账子图数据
    'AccountTransferItem': AccountTransferModel,
    'UTXOTransferItem': UTXOTransferModel,
    
    # 标签数据
    'LabelReportItem': LabelReportModel,
    
    # Solana 数据
    'SolanaTransactionItem': SolanaTransactionModel,
    'SolanaBlockItem': SolanaBlockModel,
    'SolanaBalanceChangesItem': SolanaBalanceChangesModel,
    'SolanaInstructionItem': SolanaInstructionModel,
    'SolanaLogItem': SolanaLogModel,
    'SPLTokenActionItem': SolanaInstructionModel,  # 复用指令模型
    'SPLMemoItem': SolanaInstructionModel,         # 复用指令模型
    'ValidateVotingItem': SolanaInstructionModel,  # 复用指令模型
    'SystemItem': SolanaInstructionModel,          # 复用指令模型
    
    # TRON 数据
    'TronTransactionItem': TronTransactionModel,
    
    # 合约数据
    'SourceCodeItem': SourceCodeModel,
    'ABIItem': ABIModel,
    'SignItem': SignModel,
}


# 字段映射：处理 Item 字段名与数据库字段名的差异
FIELD_MAPPING = {
    'id': 'transfer_id',  # AccountTransferItem 和 UTXOTransferItem 的 id 字段映射
    'address': 'contract_address',  # EventLogItem 的 address 字段映射
} 