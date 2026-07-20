#!/usr/bin/env python
"""
Fetch Historical Data — Updates CSV files with latest market data from yfinance.

Usage:
    python scripts/fetch_historical_data.py              # Fetch all assets
    python scripts/fetch_historical_data.py --asset gold # Fetch gold only
    python scripts/fetch_historical_data.py --once       # Run once (for cron)

This script should be run periodically (e.g., every 4 hours) to keep
CSV data fresh for the ML pipeline.
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from etl.extractors.yfinance_extractor import YFinanceExtractor
from etl.loaders.csv_append_loader import CSVAppendLoader
from config.settings import GOLD_DATASET_DIR, SILVER_DATASET_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_and_append(asset: str, interval: str = '15m') -> bool:
    """
    Fetch latest data from yfinance and append to CSV.
    
    Args:
        asset: 'gold' or 'silver'
        interval: '5m', '15m', '30m', or '1h'
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Fetching {asset} {interval} data...")
        
        # Extract data
        extractor = YFinanceExtractor(asset=asset, intervals=[interval])
        data = extractor.extract()
        
        if interval not in data or data[interval].empty:
            logger.warning(f"No data returned for {asset} {interval}")
            return False
        
        df = data[interval]
        logger.info(f"Fetched {len(df)} bars for {asset} {interval}")
        
        # Determine output directory
        if asset == 'gold':
            output_dir = GOLD_DATASET_DIR
        else:
            output_dir = SILVER_DATASET_DIR
        
        # Load and append using CSVAppendLoader
        loader = CSVAppendLoader(output_dir=str(output_dir), asset=asset)
        loader.load(data)  # Store the data dict
        success = loader.run(data)  # Process and append
        
        if success:
            csv_path = output_dir / f"{asset.title()}_{interval}_Candlestick.csv"
            logger.info(f"✅ Successfully appended data to {csv_path.name}")
            
            # Verify freshness
            import pandas as pd
            final_df = pd.read_csv(csv_path)
            last_date = pd.to_datetime(final_df['Date'].iloc[-1])
            age_hours = (pd.Timestamp.now() - last_date).total_seconds() / 3600
            logger.info(f"   Data now {age_hours:.1f} hours old")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch {asset} {interval}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Fetch Historical Market Data')
    parser.add_argument(
        '--asset',
        choices=['gold', 'silver', 'all'],
        default='all',
        help='Asset to fetch (default: all)'
    )
    parser.add_argument(
        '--interval',
        choices=['5m', '15m', '30m', '1h'],
        default='15m',
        help='Timeframe to fetch (default: 15m)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for cron/scheduled tasks)'
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("HISTORICAL DATA FETCH")
    print("=" * 60)
    
    assets = ['gold', 'silver'] if args.asset == 'all' else [args.asset]
    
    results = {}
    for asset in assets:
        print(f"\nFetching {asset.upper()}...")
        success = fetch_and_append(asset, args.interval)
        results[asset] = success
    
    # Summary
    print("\n" + "=" * 60)
    print("RESULTS:")
    for asset, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {asset.upper()}: {status}")
    print("=" * 60)
    
    all_success = all(results.values())
    sys.exit(0 if all_success else 1)


if __name__ == '__main__':
    main()
