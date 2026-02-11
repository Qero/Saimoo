from enum import Enum
from datetime import date
from typing import Optional
from pydantic import BaseModel

class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    MINUTE_60 = "60m"

class AdjustType(str, Enum):
    NONE = "none"      # 不复权
    QFQ = "qfq"        # 前复权
    HFQ = "hfq"        # 后复权

class BarData(BaseModel):
    """标准K线数据模型"""
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    turnover: Optional[float] = None  # 换手率
    pct_chg: Optional[float] = None   # 涨跌幅

class TradeCalendar(BaseModel):
    """交易日历模型"""
    exchange: str
    date: date
    is_open: bool
