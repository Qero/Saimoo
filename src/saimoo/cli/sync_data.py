import click
from datetime import date, timedelta
from loguru import logger
from saimoo.data.storage.database import init_db, get_db
from saimoo.data.storage.sql_storage import SqlAlchemyStorage
from saimoo.data.sources.akshare_source import AkShareProvider
from saimoo.utils.types import AdjustType

@click.command()
@click.option('--symbol', help='Stock symbol to sync (e.g., 600000)', required=True)
@click.option('--days', default=365, help='Number of days to sync back')
@click.option('--adjust', type=click.Choice(['qfq', 'hfq', 'none']), default='qfq', help='Adjustment type')
def sync_bars(symbol, days, adjust):
    """Sync daily bars from AkShare to local database"""
    init_db() # Ensure tables exist
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    adjust_enum = AdjustType(adjust)
    
    db = next(get_db())
    storage = SqlAlchemyStorage(db)
    provider = AkShareProvider()
    
    # Check latest date to support incremental update
    latest_date = storage.get_latest_date(symbol, adjust_enum)
    if latest_date:
        logger.info(f"Latest data for {symbol} is {latest_date}")
        start_date = max(start_date, latest_date + timedelta(days=1))
    
    if start_date > end_date:
        logger.info("Data is up to date.")
        return

    logger.info(f"Syncing {symbol} from {start_date} to {end_date} ({adjust})...")
    
    bars = provider.get_daily_bars(symbol, start_date, end_date, adjust_enum)
    if not bars:
        logger.warning("No data fetched from source.")
        return
        
    count = storage.save_daily_bars(bars, adjust_enum)
    logger.success(f"Saved {count} bars to database.")

if __name__ == '__main__':
    sync_bars()
