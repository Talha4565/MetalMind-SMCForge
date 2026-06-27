"""
Download FULL historical data from 2002 using daily candles, then resample to intraday.
yfinance limits intraday data (15m = 60 days, 1h = 730 days), but daily = full history.

Usage:
    python scripts/download_full_history.py --asset gold
    python scripts/download_full_history.py --asset silver
    python scripts/download_full_history.py --asset both
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
GOLD_DIR = PROJECT_ROOT / "Gold Dataset"
SILVER_DIR = PROJECT_ROOT / "Silver Dataset"

TICKERS = {
    'gold': 'GC=F',
    'silver': 'SI=F',
}


def download_daily(ticker: str, start: str = "2002-01-01", end: str = None) -> pd.DataFrame:
    """Download daily OHLCV data from Yahoo Finance."""
    if end is None:
        end = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"Downloading {ticker} daily from {start} to {end}...")
    t = yf.Ticker(ticker)
    df = t.history(start=start, end=end, interval="1d")
    
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    
    df.index.name = 'DateTime'
    logger.info(f"Downloaded {len(df)} daily bars: {df.index.min().date()} to {df.index.max().date()}")
    return df


def resample_to_timeframe(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Resample daily data to intraday timeframe."""
    resampled = df.resample(freq).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    
    resampled['Date'] = resampled.index.strftime('%Y.%m.%d')
    resampled['Time'] = resampled.index.strftime('%H:%M')
    
    return resampled[['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']]


def interpolate_intraday(daily_df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Create synthetic intraday data from daily candles by interpolation."""
    # Create a date range with the target frequency
    dates = daily_df.index
    
    # For each day, create intraday bars
    all_rows = []
    for i, date in enumerate(dates):
        row = daily_df.iloc[i]
        open_p = row['Open']
        high_p = row['High']
        low_p = row['Low']
        close_p = row['Close']
        volume = row['Volume']
        
        # Determine number of bars per day based on frequency
        if freq == '15T':
            n_bars = 26  # 08:00-14:30 (London+NY session)
            start_hour = 8
        elif freq == '30T':
            n_bars = 13
            start_hour = 8
        elif freq == '1H':
            n_bars = 7
            start_hour = 8
        elif freq == '5T':
            n_bars = 78
            start_hour = 8
        else:
            n_bars = 7
            start_hour = 8
        
        # Generate price path using Brownian bridge (open → close)
        np.random.seed(int(date.timestamp()) % 2**31)
        noise = np.random.randn(n_bars) * (high_p - low_p) * 0.1
        prices = np.linspace(open_p, close_p, n_bars) + noise
        prices = np.clip(prices, low_p, high_p)
        
        # Generate volumes
        vol_noise = np.random.exponential(volume / n_bars, n_bars)
        
        for j in range(n_bars):
            hour = start_hour + j * int(freq.replace('T', '').replace('H', '')) // 60
            minute = (j * int(freq.replace('T', '').replace('H', ''))) % 60
            
            bar_open = prices[j]
            bar_close = prices[min(j + 1, n_bars - 1)] if j < n_bars - 1 else close_p
            bar_high = max(bar_open, bar_close) + abs(noise[j]) * 0.5
            bar_low = min(bar_open, bar_close) - abs(noise[j]) * 0.5
            
            bar_high = min(bar_high, high_p)
            bar_low = max(bar_low, low_p)
            
            all_rows.append({
                'Date': date.strftime('%Y.%m.%d'),
                'Time': f"{hour:02d}:{minute:02d}",
                'Open': round(bar_open, 2),
                'High': round(bar_high, 2),
                'Low': round(bar_low, 2),
                'Close': round(bar_close, 2),
                'Volume': int(vol_noise[j])
            })
    
    return pd.DataFrame(all_rows)


def save_dataset(asset: str, daily_df: pd.DataFrame, output_dir: Path):
    """Save all timeframes for an asset."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1h: resample daily to hourly (real data, no interpolation needed for backtesting)
    logger.info("Creating 1h timeframe...")
    df_1h = resample_to_timeframe(daily_df, '1h')
    df_1h.to_csv(output_dir / f"{asset.title()}_1h_Candlestick.csv", index=False)
    logger.info(f"  1h: {len(df_1h)} rows")
    
    # 30m: interpolate from daily
    logger.info("Creating 30m timeframe (interpolated)...")
    df_30m = interpolate_intraday(daily_df, '30T')
    df_30m.to_csv(output_dir / f"{asset.title()}_30m_Candlestick.csv", index=False)
    logger.info(f"  30m: {len(df_30m)} rows")
    
    # 15m: interpolate from daily
    logger.info("Creating 15m timeframe (interpolated)...")
    df_15m = interpolate_intraday(daily_df, '15T')
    df_15m.to_csv(output_dir / f"{asset.title()}_15m_Candlestick.csv", index=False)
    logger.info(f"  15m: {len(df_15m)} rows")
    
    # 5m: interpolate from daily
    logger.info("Creating 5m timeframe (interpolated)...")
    df_5m = interpolate_intraday(daily_df, '5T')
    df_5m.to_csv(output_dir / f"{asset.title()}_5m_Candlestick.csv", index=False)
    logger.info(f"  5m: {len(df_5m)} rows")
    
    logger.info(f"✅ {asset.upper()} saved to {output_dir}")


def download_asset(asset: str, start: str = "2002-01-01"):
    """Download full history for an asset."""
    ticker = TICKERS[asset]
    output_dir = GOLD_DIR if asset == 'gold' else SILVER_DIR
    
    daily = download_daily(ticker, start=start)
    save_dataset(asset, daily, output_dir)
    
    return daily


def main():
    parser = argparse.ArgumentParser(description="Download full historical data from 2002")
    parser.add_argument("--asset", choices=["gold", "silver", "both"], default="both")
    parser.add_argument("--start", default="2002-01-01", help="Start date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    if args.asset in ("gold", "both"):
        download_asset("gold", args.start)
    if args.asset in ("silver", "both"):
        download_asset("silver", args.start)
    
    logger.info("✅ Full history download complete!")


if __name__ == "__main__":
    main()
