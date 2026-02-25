import click
from saimoo.data.storage.database import init_db
from saimoo.services.data_service import DataService
from saimoo.utils.types import AdjustType
from loguru import logger

@click.command()
@click.option('--symbol', help='Stock symbol to sync (e.g., 600000)', required=True)
@click.option('--days', default=365, help='Number of days to sync back')
@click.option('--adjust', type=click.Choice(['qfq', 'hfq', 'none']), default='qfq', help='Adjustment type')
def sync_bars(symbol, days, adjust):
    """Sync daily bars from AkShare (and Tushare if configured) to local database"""
    init_db() # Ensure tables exist
    
    adjust_enum = AdjustType(adjust)
    
    service = DataService()
    
    logger.info(f"Syncing {symbol} for last {days} days ({adjust})...")
    
    try:
        count = service.sync_data(symbol, days=days, adjust=adjust_enum)
        if count > 0:
            logger.success(f"Successfully synced {count} bars (AkShare). Verification might have run if Tushare is configured.")
        else:
            logger.warning("No new data synced.")
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")

if __name__ == '__main__':
    sync_bars()
