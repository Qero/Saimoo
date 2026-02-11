import click
from loguru import logger

@click.group()
def cli():
    """Saimoo Quant Trading System CLI"""
    pass

@cli.command()
def version():
    """Show version"""
    click.echo("Saimoo v0.1.0")

@cli.command()
def check():
    """Check environment"""
    try:
        import pandas as pd
        import numpy as np
        import sqlalchemy
        
        logger.info("Environment check passed!")
        logger.info(f"Pandas: {pd.__version__}")
        logger.info(f"Numpy: {np.__version__}")
        logger.info(f"SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError as e:
        logger.error(f"Environment check failed: {e}")

if __name__ == "__main__":
    cli()
