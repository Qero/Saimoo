from datetime import date
from typing import List

import pandas as pd

from saimoo.data.sources.akshare_source import AkShareProvider
from saimoo.data.storage.database import get_db
from saimoo.data.storage.sql_storage import SqlAlchemyStorage
from saimoo.utils.types import AdjustType, BarData


class DataService:
    """数据服务层：封装数据获取与转换逻辑"""

    def __init__(self):
        self.db_gen = get_db()
        self.db = next(self.db_gen)
        self.storage = SqlAlchemyStorage(self.db)
        self.ak_provider = AkShareProvider()

    def get_bars_dataframe(
        self, symbol: str, start_date: date, end_date: date, adjust: AdjustType = AdjustType.QFQ, source: str = "local"
    ) -> pd.DataFrame:
        """获取K线数据并转换为 DataFrame"""
        bars: List[BarData] = []

        if source == "local":
            bars = self.storage.get_daily_bars(symbol, start_date, end_date, adjust)
        elif source == "akshare":
            bars = self.ak_provider.get_daily_bars(symbol, start_date, end_date, adjust)

        if not bars:
            return pd.DataFrame()

        # Convert to DataFrame
        data = [b.model_dump() for b in bars]
        df = pd.DataFrame(data)

        # Ensure date column is datetime
        df["date"] = pd.to_datetime(df["date"])
        return df

    def sync_data(self, symbol: str, days: int = 30, adjust: AdjustType = AdjustType.QFQ) -> int:
        """同步数据到本地"""
        from datetime import timedelta

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        bars = self.ak_provider.get_daily_bars(symbol, start_date, end_date, adjust)
        if bars:
            return self.storage.save_daily_bars(bars, adjust)
        return 0

    def get_stock_list(self) -> pd.DataFrame:
        """获取所有A股股票列表 (代码, 名称)"""
        import akshare as ak

        # ak.stock_info_a_code_name() 返回 code, name
        try:
            df = ak.stock_info_a_code_name()
            return df
        except Exception as e:
            # Fallback or empty if failed
            print(f"Error fetching stock list: {e}")
            return pd.DataFrame(columns=["code", "name"])
