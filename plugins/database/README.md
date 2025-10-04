# Database Export Plugin

PostgreSQL 数据库导出插件，支持将 BlockchainSpider 爬取的区块链数据直接写入数据库。

---

## 📁 插件结构

```
plugins/database/
├── __init__.py          # 插件入口
├── config.py            # 配置管理
├── models.py            # 数据模型（25张表）
├── adapter.py           # PostgreSQL 适配器
├── pipelines.py         # 主管道类
├── utils.py             # 工具函数
├── requirements.txt     # 依赖列表
└── README.md            # 本文档
```

**总代码量**: ~1500 行

---

## ⚡ 快速开始

### 1. 安装依赖

```bash
pip install -r plugins/database/requirements.txt
```

### 2. 启用管道

编辑 `BlockchainSpider/settings.py`:

```python
ITEM_PIPELINES = {
    'plugins.database.pipelines.DatabasePipeline': 100,
}
```

### 3. 运行爬虫

**使用数据库 URL（推荐）**:

```bash
scrapy crawl trans.block.evm \
  -a start_blk=19000000 \
  -a end_blk=19000100 \
  -a providers=https://eth.llamarpc.com \
  -a db_url=postgresql://postgres:123456@localhost:5432/blockchain
```

**就这么简单！** 插件会自动创建数据库和表结构。

> 💡 也可以使用独立参数：`-a db_user=postgres -a db_password=123456 -a db_name=blockchain`

---

## 📊 功能特性

- ✅ 自动创建数据库（如果不存在）
- ✅ 自动创建 25 张表和索引
- ✅ 批量插入优化（1000条/批）
- ✅ 连接池管理
- ✅ 自动去重
- ✅ 错误重试
- ✅ 支持 EVM、Solana、TRON、Bitcoin 等多链
- ✅ 完整覆盖所有 30+ 种数据类型

---

## ⚙️ 配置参数

### 方式 1: 使用数据库 URL（推荐）

| 参数 | 格式 | 示例 |
|------|------|------|
| `db_url` | `postgresql://user:password@host:port/database` | `postgresql://postgres:123456@localhost:5432/blockchain` |
| `batch_size` | 整数 | `1000` |

### 方式 2: 使用独立参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `db_host` | localhost | 数据库主机 |
| `db_port` | 5432 | 数据库端口 |
| `db_user` | postgres | 用户名 |
| `db_password` | - | 密码 |
| `db_name` | blockchain | 数据库名 |
| `batch_size` | 1000 | 批量大小 |

**注意**: `db_url` 优先级更高，如果提供了 `db_url`，其他参数会被忽略。

---

## 📋 数据库表结构

插件会自动创建以下 **25 张表**，完整覆盖所有 BlockchainSpider 数据类型：

### EVM 链数据 (13张)
- `bs_blocks` - 区块数据
- `bs_transactions` - 交易数据
- `bs_transaction_receipts` - 交易收据
- `bs_event_logs` - 事件日志
- `bs_traces` - 交易追踪
- `bs_token20_transfers` - ERC20 代币转账
- `bs_token721_transfers` - ERC721 NFT 转账
- `bs_token1155_transfers` - ERC1155 代币转账
- `bs_token_approvals` - 代币授权
- `bs_token_approval_all` - 代币全部授权
- `bs_token_properties` - 代币属性
- `bs_nft_metadata` - NFT 元数据
- `bs_contracts` - 合约字节码

### Solana 链数据 (5张)
- `bs_solana_blocks` - 区块
- `bs_solana_transactions` - 交易
- `bs_solana_balance_changes` - 余额变化
- `bs_solana_instructions` - 指令（包含 SPL Token）
- `bs_solana_logs` - 日志

### TRON 链数据 (1张)
- `bs_tron_transactions` - TRON 交易

### 转账子图数据 (2张)
- `bs_account_transfers` - 账户转账
- `bs_utxo_transfers` - UTXO 转账（比特币）

### 标签数据 (1张)
- `bs_label_reports` - 标签报告

### 合约数据 (3张)
- `bs_source_codes` - 合约源代码
- `bs_abis` - 合约 ABI
- `bs_signatures` - 函数签名

---

## 🌐 多链数据管理

### 推荐方案：独立数据库

为每条链创建独立的数据库，数据完全隔离：

```bash
# 以太坊
scrapy crawl trans.block.evm \
  -a providers=https://eth.llamarpc.com \
  -a start_blk=19000000 \
  -a end_blk=19000100 \
  -a db_url=postgresql://postgres:123456@localhost:5432/ethereum

# BSC
scrapy crawl trans.block.evm \
  -a providers=https://bsc-dataseed.binance.org \
  -a start_blk=30000000 \
  -a end_blk=30000100 \
  -a db_url=postgresql://postgres:123456@localhost:5432/bsc

# Solana
scrapy crawl trans.block.solana \
  -a providers=https://api.mainnet-beta.solana.com \
  -a start_slot=200000000 \
  -a end_slot=200001000 \
  -a db_url=postgresql://postgres:123456@localhost:5432/solana
```

---

## 🔍 使用示例

### 示例 1: 爬取以太坊数据（使用 URL）

```bash
scrapy crawl trans.block.evm \
  -a start_blk=19000000 \
  -a end_blk=19001000 \
  -a providers=https://eth.llamarpc.com \
  -a db_url=postgresql://postgres:123456@localhost:5432/ethereum
```

### 示例 2: 爬取转账子图（使用 URL）

```bash
scrapy crawl txs.blockscan \
  -a source=0xeb31973e0febf3e3d7058234a5ebbae1ab4b8c23 \
  -a apikeys=YOUR_API_KEY \
  -a db_url=postgresql://postgres:123456@localhost:5432/ethereum
```

### 示例 3: 同时输出文件和入库

```python
# 在 settings.py 中配置
ITEM_PIPELINES = {
    'plugins.database.pipelines.DatabasePipeline': 100,  # 数据库
    'BlockchainSpider.pipelines.trans.EVMTrans2csvPipeline': 200,  # 文件备份
}
```

---

## 🐳 Docker PostgreSQL

### 启动 PostgreSQL

```bash
docker run -d \
  --name blockchain-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=123456 \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15
```

### 查看数据

```bash
# 连接数据库
docker exec -it blockchain-postgres psql -U postgres -d ethereum

# 查看表
\dt

# 查询数据
SELECT * FROM bs_blocks ORDER BY block_number DESC LIMIT 10;
SELECT COUNT(*) FROM bs_transactions;

# 退出
\q
```

---

## ❓ 常见问题

**Q: 会自动创建数据库吗？**  
A: 是的！插件会自动检测并创建数据库。

**Q: 需要手动创建表吗？**  
A: 不需要！插件会自动创建所有 25 张表。

**Q: 爬取多条链怎么办？**  
A: 推荐使用不同的数据库名：`-a db_name=ethereum`, `-a db_name=bsc`

**Q: 启用数据库后还会输出文件吗？**  
A: 不会。如需同时输出文件，请在 settings.py 中同时配置文件管道。

**Q: 支持哪些区块链？**  
A: 支持 40+ 条 EVM 链、Solana、TRON、Bitcoin。

**Q: 支持哪些数据类型？**  
A: 支持 30+ 种数据类型，包括交易、代币转账、事件日志、追踪、标签、合约等。

---

## 📝 依赖说明

```
psycopg2-binary>=2.9.0    # PostgreSQL 驱动
sqlalchemy>=2.0.0         # ORM 框架
python-dateutil>=2.8.0    # 日期处理
```

---

**简单、强大、开箱即用！** 🚀 