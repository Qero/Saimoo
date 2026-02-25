from datetime import date, timedelta
from typing import List, Optional

import pandas as pd
from loguru import logger

from saimoo.config.settings import settings
from saimoo.data.sources.akshare_source import AkShareProvider
from saimoo.data.sources.tushare_source import TushareProvider
from saimoo.data.storage.database import get_db
from saimoo.data.storage.sql_storage import SqlAlchemyStorage
from saimoo.services.verification_service import VerificationService
from saimoo.utils.types import AdjustType, BarData


class DataService:
    """数据服务层：封装数据获取与转换逻辑"""

    def __init__(self):
        self.db_gen = get_db()
        self.db = next(self.db_gen)
        self.storage = SqlAlchemyStorage(self.db)
        self.ak_provider = AkShareProvider()
        
        self.tushare_provider = None
        if settings.TUSHARE_TOKEN:
            try:
                self.tushare_provider = TushareProvider(settings.TUSHARE_TOKEN)
            except Exception as e:
                logger.warning(f"Failed to init TushareProvider: {e}")
        
        self.verification_service = VerificationService(self.storage)

    def get_bars_dataframe(
        self, symbol: str, start_date: date, end_date: date, adjust: AdjustType = AdjustType.QFQ, source: str = "local"
    ) -> pd.DataFrame:
        """获取K线数据并转换为 DataFrame"""
        bars: List[BarData] = []

        if source == "local":
            # Default to reading from AkShare table locally
            bars = self.storage.get_daily_bars(symbol, start_date, end_date, adjust, source="akshare")
        elif source == "akshare":
            bars = self.ak_provider.get_daily_bars(symbol, start_date, end_date, adjust)
        elif source == "tushare" and self.tushare_provider:
            bars = self.tushare_provider.get_daily_bars(symbol, start_date, end_date, adjust)

        if not bars:
            return pd.DataFrame()

        # Convert to DataFrame
        data = [b.model_dump() for b in bars]
        df = pd.DataFrame(data)

        # Ensure date column is datetime
        df["date"] = pd.to_datetime(df["date"])
        return df

    def sync_data(self, symbol: str, days: int = 30, adjust: AdjustType = AdjustType.QFQ) -> int:
        """同步数据到本地，并尝试校验"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        count = 0
        
        # 1. Sync AkShare Data (Primary)
        try:
            bars_ak = self.ak_provider.get_daily_bars(symbol, start_date, end_date, adjust)
            if bars_ak:
                count = self.storage.save_daily_bars(bars_ak, adjust, source="akshare")
        except Exception as e:
            logger.error(f"Failed to sync AkShare data: {e}")

        # 2. Sync Tushare Data (Secondary) & Verify
        if self.tushare_provider:
            try:
                bars_ts = self.tushare_provider.get_daily_bars(symbol, start_date, end_date, adjust)
                if bars_ts:
                    self.storage.save_daily_bars(bars_ts, adjust, source="tushare")
                
                # Verify data consistency
                # Verification range is usually what we just synced
                # Or verify the latest available date
                self.verification_service.verify_data(symbol, start_date, end_date, adjust)
                
            except Exception as e:
                logger.error(f"Failed to sync/verify Tushare data: {e}")
        
        return count

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

    def get_verification_status(self, symbol: str, adjust: AdjustType = AdjustType.QFQ) -> Optional[dict]:
        """获取最近的数据校验状态"""
        # Retrieve verification result for the latest available date
        # Ideally we should query by symbol and order by date desc
        # But get_verification_result needs specific date.
        # We can find the latest date in DB first.
        latest_date = self.storage.get_latest_date(symbol, adjust, source="akshare")
        if not latest_date:
            return None
            
        return self.storage.get_verification_result(symbol, latest_date, adjust)
