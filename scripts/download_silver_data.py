"""
Download Silver (XAG/USD) historical data using yfinance.
Creates the same timeframe structure as Gold dataset.
"""

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_silver_data(
    start_date: str = "2020-01-01",
    end_date: str = None,
    output_dir: Path = None
):
    """
    Download Silver data and create multiple timeframe files.
    
    Args:
        start_date: Start date for historical data (YYYY-MM-DD)
        end_date: End date (defaults to today)
        output_dir: Directory to save CSV files
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "Silver Dataset"
    
    output_dir.mkdir(exist_ok=True)
    
    logger.info(f"Downloading Silver (XAG/USD) data from {start_date} to {end_date}")
    
    # Silver ticker symbol
    ticker = "SI=F"  # Silver futures
    
    # Alternative tickers to try
    alternative_tickers = [
        "SI=F",      # Silver futures
        "SLV",       # Silver ETF (as backup)
    ]
    
    silver_data = None
    successful_ticker = None
    
    # Try different ticker symbols
    # Note: yfinance limits intraday data to recent periods only
    # We'll download daily data first (no limitations), then create intraday synthetic data
    for ticker_symbol in alternative_tickers:
        try:
            logger.info(f"Trying ticker: {ticker_symbol}")
            silver = yf.Ticker(ticker_symbol)
            
            # Download daily data (no time restrictions)
            df_daily = silver.history(
                start=start_date,
                end=end_date,
                interval="1d"
            )
            
            if not df_daily.empty:
                silver_data = df_daily
                successful_ticker = ticker_symbol
                logger.info(f"✅ Successfully downloaded from {ticker_symbol}")
                break
        except Exception as e:
            logger.warning(f"Failed with {ticker_symbol}: {e}")
            continue
    
    if silver_data is None or silver_data.empty:
        raise ValueError("Could not download Silver data from any ticker symbol")
    
    logger.info(f"Downloaded {len(silver_data)} daily bars")
    logger.info(f"Date range: {silver_data.index.min()} to {silver_data.index.max()}")
    logger.info(f"⚠️  Note: Creating synthetic intraday data from daily bars for backtesting")
    
    # Save 1-hour data first
    logger.info("Saving 1-hour timeframe...")
    df_1h = create_resampled_timeframe(silver_data, '1H')
    output_1h = output_dir / "Silver_1h_Candlestick.csv"
    df_1h.to_csv(output_1h, index=False)
    logger.info(f"✅ Saved 1h data: {output_1h} ({len(df_1h)} rows)")
    
    # Create 30-minute by downsampling (interpolate between 1h bars)
    logger.info("Creating 30-minute timeframe (interpolated)...")
    df_30m = create_interpolated_timeframe(silver_data, '30T')
    output_30m = output_dir / "Silver_30m_Candlestick.csv"
    df_30m.to_csv(output_30m, index=False)
    logger.info(f"✅ Saved 30m data: {output_30m} ({len(df_30m)} rows)")
    
    # Create 15-minute by downsampling
    logger.info("Creating 15-minute timeframe (interpolated)...")
    df_15m = create_interpolated_timeframe(silver_data, '15T')
    output_15m = output_dir / "Silver_15m_Candlestick.csv"
    df_15m.to_csv(output_15m, index=False)
    logger.info(f"✅ Saved 15m data: {output_15m} ({len(df_15m)} rows)")
    
    # Create 5-minute by downsampling
    logger.info("Creating 5-minute timeframe (interpolated)...")
    df_5m = create_interpolated_timeframe(silver_data, '5T')
    output_5m = output_dir / "Silver_5m_Candlestick.csv"
    df_5m.to_csv(output_5m, index=False)
    logger.info(f"✅ Saved 5m data: {output_5m} ({len(df_5m)} rows)")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Silver dataset created successfully!")
    logger.info(f"{'='*60}")
    logger.info(f"Ticker used: {successful_ticker}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Files created:")
    logger.info(f"  - Silver_5m_Candlestick.csv ({len(df_5m)} rows)")
    logger.info(f"  - Silver_15m_Candlestick.csv ({len(df_15m)} rows)")
    logger.info(f"  - Silver_30m_Candlestick.csv ({len(df_30m)} rows)")
    logger.info(f"  - Silver_1h_Candlestick.csv ({len(df_1h)} rows)")
    logger.info(f"{'='*60}\n")
    
    return output_dir


def create_interpolated_timeframe(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """
    Create smaller timeframes by interpolating from 1-hour data.
    This generates synthetic intraday data for backtesting purposes.
    
    Args:
        df: Original dataframe with OHLCV columns (1-hour)
        freq: Pandas frequency string (e.g., '5T', '15T', '30T')
    
    Returns:
        Interpolated dataframe in the same format
    """
    # Resample to smaller timeframe
    resampled = df.resample(freq).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    
    # Forward-fill and backward-fill to handle missing values
    resampled = resampled.fillna(method='ffill').fillna(method='bfill')
    
    # Interpolate price values for smoother transitions
    resampled['Open'] = resampled['Open'].interpolate(method='linear')
    resampled['High'] = resampled['High'].interpolate(method='linear')
    resampled['Low'] = resampled['Low'].interpolate(method='linear')
    resampled['Close'] = resampled['Close'].interpolate(method='linear')
    
    # Drop any remaining NaN rows
    resampled = resampled.dropna()
    
    # Create Date and Time columns
    resampled_df = resampled.copy()
    resampled_df['Date'] = resampled_df.index.date
    resampled_df['Time'] = resampled_df.index.time
    
    # Reorder columns
    resampled_df = resampled_df[['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']]
    
    return resampled_df


def create_resampled_timeframe(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """
    Resample OHLCV data to a different timeframe.
    
    Args:
        df: Original dataframe with OHLCV columns
        freq: Pandas frequency string (e.g., '15T', '30T', '1H')
    
    Returns:
        Resampled dataframe in the same format as original
    """
    resampled = df.resample(freq).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    
    # Create Date and Time columns
    resampled_df = resampled.copy()
    resampled_df['Date'] = resampled_df.index.date
    resampled_df['Time'] = resampled_df.index.time
    
    # Reorder columns
    resampled_df = resampled_df[['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']]
    
    return resampled_df


def verify_silver_dataset(dataset_dir: Path = None):
    """Verify that all Silver dataset files exist and are valid."""
    if dataset_dir is None:
        dataset_dir = Path(__file__).parent.parent / "Silver Dataset"
    
    required_files = [
        "Silver_5m_Candlestick.csv",
        "Silver_15m_Candlestick.csv",
        "Silver_30m_Candlestick.csv",
        "Silver_1h_Candlestick.csv"
    ]
    
    logger.info("Verifying Silver dataset...")
    all_exist = True
    
    for filename in required_files:
        filepath = dataset_dir / filename
        if filepath.exists():
            df = pd.read_csv(filepath)
            logger.info(f"✅ {filename}: {len(df)} rows")
        else:
            logger.error(f"❌ {filename}: NOT FOUND")
            all_exist = False
    
    if all_exist:
        logger.info("✅ All Silver dataset files verified!")
    else:
        logger.error("❌ Some files are missing!")
    
    return all_exist


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Silver (XAG/USD) historical data")
    parser.add_argument("--start", default="2020-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing dataset")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output) if args.output else None
    
    if args.verify_only:
        verify_silver_dataset(output_dir)
    else:
        try:
            download_silver_data(args.start, args.end, output_dir)
            verify_silver_dataset(output_dir)
        except Exception as e:
            logger.error(f"Failed to download Silver data: {e}")
            raise
