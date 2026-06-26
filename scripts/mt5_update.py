"""
MT5 Spot Data Updater — Run locally on Windows.
Fetches latest candles from MT5 and appends to existing CSVs.
No Yahoo Finance, no synthetic data — real XAUUSD/XAGUSD spot prices.

Usage:
    python scripts/mt5_update.py              # Update both assets
    python scripts/mt5_update.py --asset gold  # Update gold only

Requires: MetaTrader 5 terminal running with demo account.
"""

import MetaTrader5 as mt5
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
GOLD_DIR = PROJECT_ROOT / "Gold Dataset"
SILVER_DIR = PROJECT_ROOT / "Silver Dataset"

SYMBOLS = {
    'gold': 'XAUUSD',
    'silver': 'XAGUSD',
}

TIMEFRAMES = {
    '5m': (mt5.TIMEFRAME_M5, 500),
    '15m': (mt5.TIMEFRAME_M15, 500),
    '30m': (mt5.TIMEFRAME_M30, 500),
    '1h': (mt5.TIMEFRAME_H1, 500),
}


def fetch_latest(symbol: str, timeframe: int, count: int) -> pd.DataFrame:
    """Fetch latest N candles from MT5."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['Date'] = df['time'].dt.strftime('%Y.%m.%d')
    df['Time'] = df['time'].dt.strftime('%H:%M')
    df.rename(columns={
        'open': 'Open', 'high': 'High', 'low': 'Low',
        'close': 'Close', 'tick_volume': 'Volume'
    }, inplace=True)
    return df[['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']]


def append_to_csv(csv_path: pd.DataFrame, new_df: pd.DataFrame) -> int:
    """Append new data to CSV, deduplicate, return new row count."""
    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        combined = pd.concat([existing, new_df], ignore_index=True)
        before = len(combined)
        combined = combined.drop_duplicates(subset=['Date', 'Time'], keep='last')
        combined = combined.sort_values(['Date', 'Time']).reset_index(drop=True)
        combined.to_csv(csv_path, index=False)
        return before - len(combined)
    else:
        new_df.to_csv(csv_path, index=False)
        return 0


def update_asset(asset: str):
    """Update all timeframes for an asset."""
    symbol = SYMBOLS[asset]
    output_dir = GOLD_DIR if asset == 'gold' else SILVER_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if not mt5.initialize():
        raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        mt5.shutdown()
        raise ValueError(f"Symbol {symbol} not found in Market Watch")

    if not symbol_info.visible:
        mt5.symbol_select(symbol, True)

    logger.info(f"Updating {asset.upper()} ({symbol}) spot data...")

    for tf_name, (tf_const, count) in TIMEFRAMES.items():
        csv_path = output_dir / f"{asset.title()}_{tf_name}_Candlestick.csv"
        new_df = fetch_latest(symbol, tf_const, count)

        if new_df.empty:
            logger.warning(f"  {tf_name}: no data")
            continue

        dupes = append_to_csv(csv_path, new_df)
        total = len(pd.read_csv(csv_path))
        logger.info(f"  {tf_name}: +{len(new_df)} fetched, {dupes} dupes removed, {total} total rows")

    mt5.shutdown()
    logger.info(f"✅ {asset.upper()} update complete!")


def main():
    parser = argparse.ArgumentParser(description="MT5 Spot Data Updater")
    parser.add_argument("--asset", choices=["gold", "silver", "both"], default="both")
    args = parser.parse_args()

    if args.asset in ("gold", "both"):
        update_asset("gold")
    if args.asset in ("silver", "both"):
        update_asset("silver")

    logger.info("Run 'git add' + 'git push' to upload to GitHub Actions for retraining.")


if __name__ == "__main__":
    main()
