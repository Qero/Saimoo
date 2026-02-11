import click
from datetime import date, timedelta
from loguru import logger
from saimoo.data.sources.akshare_source import AkShareProvider
from saimoo.data.sources.tushare_source import TushareProvider
from saimoo.utils.types import AdjustType

@click.command()
@click.option('--source', type=click.Choice(['akshare', 'tushare']), default='akshare', help='Data source')
@click.option('--symbol', default='600000', help='Stock symbol (e.g. 600000)')
@click.option('--days', default=10, help='Number of days to fetch')
@click.option('--token', envvar='TUSHARE_TOKEN', help='Tushare token (required for tushare source)')
def verify_data(source, symbol, days, token):
    """Verify data source connectivity and data format"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Verifying {source} source for {symbol} from {start_date} to {end_date}")

    provider = None
    if source == 'akshare':
        provider = AkShareProvider()
    elif source == 'tushare':
        if not token:
            logger.error("Tushare token is required! Set TUSHARE_TOKEN env var or pass --token")
            return
        provider = TushareProvider(token=token)
    
    # 1. Test Daily Bars
    logger.info("Fetching daily bars...")
    bars = provider.get_daily_bars(symbol, start_date, end_date, AdjustType.QFQ)
    
    if bars:
        logger.success(f"Successfully fetched {len(bars)} bars")
        logger.info(f"First bar: {bars[0]}")
        logger.info(f"Last bar: {bars[-1]}")
    else:
        logger.warning("No bars returned")

    # 2. Test Calendar (Tushare only for now)
    if source == 'tushare':
        logger.info("Fetching trade calendar...")
        cals = provider.get_trade_calendar(start_date, end_date)
        if cals:
            logger.success(f"Successfully fetched {len(cals)} calendar days")
            open_days = [c.date for c in cals if c.is_open]
            logger.info(f"Open trading days: {len(open_days)}")
        else:
            logger.warning("No calendar data returned")

if __name__ == '__main__':
    verify_data()
