# 数据落库 (Storage) 模块设计方案

**版本**: v1.0
**日期**: 2026-02-11
**状态**: 已评审

---

## 1. 设计目标

构建高效、可靠的本地数据存储层，支持：
- 多源数据的统一持久化（清洗后的标准格式）。
- 高效的时间序列数据查询（日线、分钟线）。
- 基础信息管理（标的列表、交易日历）。
- 易于扩展的数据库后端（默认 SQLite，支持迁移至 PostgreSQL/MySQL）。

## 2. 技术选型

- **ORM 框架**: SQLAlchemy 2.0+
  - *理由*: Python 生态事实标准，支持异步（可选），强大的模型映射与迁移能力。
- **数据库**:
  - **默认**: SQLite (文件型，零配置，适合单机/回测)。
  - **扩展**: PostgreSQL (适合多并发实盘/海量数据)。
- **迁移工具**: Alembic (后续引入，用于 Schema 变更管理)。

## 3. 数据库模型设计 (Schema)

所有表均包含 `created_at` 和 `updated_at` 字段用于审计。

### 3.1 证券基础信息表 (`securities`)
存储股票、指数等标的基础信息。

| 字段名 | 类型 | 说明 | 约束 |
| :--- | :--- | :--- | :--- |
| `symbol` | String(20) | 标的代码 (如 600000.SH) | PK |
| `name` | String(50) | 中文名称 | |
| `type` | Enum | 类型 (stock, index, etf) | |
| `list_date` | Date | 上市日期 | |
| `delist_date` | Date | 退市日期 | Nullable |
| `cn_spell` | String(50) | 拼音缩写 (方便搜索) | |

### 3.2 交易日历表 (`trade_calendars`)
存储各大交易所的交易日历。

| 字段名 | 类型 | 说明 | 约束 |
| :--- | :--- | :--- | :--- |
| `exchange` | String(10) | 交易所 (SSE, SZSE) | PK, Composite |
| `date` | Date | 日期 | PK, Composite |
| `is_open` | Boolean | 是否开市 | |

### 3.3 日线行情表 (`daily_bars`)
存储清洗后的日线级别复权数据。

| 字段名 | 类型 | 说明 | 约束 |
| :--- | :--- | :--- | :--- |
| `symbol` | String(20) | 标的代码 | PK, Composite, FK |
| `date` | Date | 交易日期 | PK, Composite |
| `open` | Float | 开盘价 | |
| `high` | Float | 最高价 | |
| `low` | Float | 最低价 | |
| `close` | Float | 收盘价 | |
| `volume` | Float | 成交量 | |
| `amount` | Float | 成交额 | |
| `turnover` | Float | 换手率 | |
| `pct_chg` | Float | 涨跌幅 | |
| `adjust` | Enum | 复权类型 (qfq, hfq, none) | PK, Composite |

> **索引策略**:
> - 复合主键 `(symbol, date, adjust)` 天然支持按标的和时间范围查询。
> - 额外索引 `(date, symbol)` 用于横截面全市场查询。

## 4. 接口设计

### 4.1 Storage 抽象接口

位于 `src/saimoo/data/storage/base.py`。

```python
class DataStorage(ABC):
    
    @abstractmethod
    def save_securities(self, securities: List[Security]) -> int:
        """批量保存标的信息"""
        pass

    @abstractmethod
    def get_security(self, symbol: str) -> Optional[Security]:
        """查询单个标的"""
        pass

    @abstractmethod
    def save_daily_bars(self, bars: List[BarData]) -> int:
        """批量保存日线数据 (Upsert)"""
        pass

    @abstractmethod
    def get_daily_bars(
        self, 
        symbol: str, 
        start: date, 
        end: date, 
        adjust: AdjustType = AdjustType.QFQ
    ) -> List[BarData]:
        """查询日线数据"""
        pass
    
    @abstractmethod
    def get_latest_date(self, symbol: str, adjust: AdjustType) -> Optional[date]:
        """查询某标的最新已有数据日期 (用于增量更新)"""
        pass
```

### 4.2 SQL 实现类 (`SqlAlchemyStorage`)

位于 `src/saimoo/data/storage/sql_storage.py`。
- 使用 SQLAlchemy `Session` 进行管理。
- 使用 `sqlite` 的 `INSERT OR REPLACE` 或通用 `merge` 策略处理重复数据 (Upsert)。

## 5. 数据流与使用场景

1.  **初始化**: 应用启动时，通过 `Config` 加载数据库 URL，初始化 `SqlAlchemyStorage` 单例。
2.  **数据同步 (Ingestion)**:
    - 调用 `AkShareProvider` 下载数据。
    - 调用 `Storage.save_daily_bars` 存入数据库。
3.  **回测/研究**:
    - 策略层调用 `Storage.get_daily_bars` 获取历史数据，而非直接请求外网。

## 6. 目录结构调整

```
src/saimoo/data/storage/
├── __init__.py
├── base.py          # 抽象接口
├── models.py        # SQLAlchemy ORM 模型定义
├── sql_storage.py   # 具体实现
└── database.py      # 数据库连接与 Session 工厂
```

## 7. 待办事项

1. 定义 ORM Models (`models.py`)。
2. 实现 `SqlAlchemyStorage` 类。
3. 编写 CRUD 单元测试。
4. 集成到 CLI 工具 (`saimoo sync`)。
