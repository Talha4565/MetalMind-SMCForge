"""
Download historical intraday data from MetaTrader 5.
H1: back to 1998 (66K+ bars)
M15: back to ~2024 (50K bars)
M5: back to ~2025 (limited)

Requirements:
    pip install MetaTrader5 pandas

Usage:
    python scripts/download_mt5_data.py
"""

import MetaTrader5 as mt5
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
GOLD_DIR = PROJECT_ROOT / "Gold Dataset"
SILVER_DIR = PROJECT_ROOT / "Silver Dataset"

SYMBOLS = {
    'gold': 'XAUUSD',
    'silver': 'XAGUSD',
}


def download_mt5(symbol: str, timeframe: int, count: int = 80000) -> pd.DataFrame:
    """Download data from MT5 using copy_rates_from_pos."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['Date'] = df['time'].dt.strftime('%Y.%m.%d')
    df['Time'] = df['time'].dt.strftime('%H:%M')
    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'tick_volume': 'Volume'
    }, inplace=True)
    
    return df[['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']]


def download_asset(asset: str):
    """Download all timeframes for an asset."""
    symbol = SYMBOLS[asset]
    output_dir = GOLD_DIR if asset == 'gold' else SILVER_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not mt5.initialize():
        raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
    
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        mt5.shutdown()
        raise ValueError(f"Symbol {symbol} not found")
    
    if not symbol_info.visible:
        mt5.symbol_select(symbol, True)
    
    timeframes = {
        '5m': (mt5.TIMEFRAME_M5, 50000),
        '15m': (mt5.TIMEFRAME_M15, 50000),
        '30m': (mt5.TIMEFRAME_M30, 50000),
        '1h': (mt5.TIMEFRAME_H1, 80000),
    }
    
    for tf_name, (tf_const, max_count) in timeframes.items():
        logger.info(f"Downloading {symbol} {tf_name} (max {max_count} bars)...")
        df = download_mt5(symbol, tf_const, max_count)
        
        if df.empty:
            logger.warning(f"  {tf_name}: no data available")
            continue
        
        filename = f"{asset.title()}_{tf_name}_Candlestick.csv"
        df.to_csv(output_dir / filename, index=False)
        logger.info(f"  {tf_name}: {len(df)} rows ({df['Date'].iloc[0]} to {df['Date'].iloc[-1]})")
    
    mt5.shutdown()
    logger.info(f"✅ {asset.upper()} download complete!")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download data from MetaTrader 5")
    parser.add_argument("--asset", choices=["gold", "silver", "both"], default="both")
    args = parser.parse_args()
    
    if args.asset in ("gold", "both"):
        download_asset("gold")
    if args.asset in ("silver", "both"):
        download_asset("silver")


if __name__ == "__main__":
    main()
