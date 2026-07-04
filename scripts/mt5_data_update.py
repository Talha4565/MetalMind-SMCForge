"""
MT5 Data Update — runs on Windows host (not in Docker).

Fetches latest OHLCV candles from MetaTrader 5 and appends to CSV files.
The Docker API reads these CSV files directly via volume mounts.

Usage:
    python scripts/mt5_data_update.py                  # Update all timeframes for gold+silver
    python scripts/mt5_data_update.py --asset gold     # Update gold only
    python scripts/mt5_data_update.py --intervals 15m  # Update only 15m candles

Requires:
    - MetaTrader 5 terminal running (demo or real account)
    - MetaTrader5 Python package (pip install MetaTrader5)
"""

import csv
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent.parent / 'Gold Dataset'
SILVER_DIR = Path(__file__).parent.parent / 'Silver Dataset'

SYMBOLS = {
    'gold': 'XAUUSD',
    'silver': 'XAGUSD',
}

# MT5 timeframe constants
TIMEFRAME_MAP = {
    '5m':  5,    # mt5.TIMEFRAME_M5
    '15m': 15,   # mt5.TIMEFRAME_M15
    '30m': 30,   # mt5.TIMEFRAME_M30
    '1h':  16385, # mt5.TIMEFRAME_H1
}

# How many bars to fetch per timeframe
# MT5 demo: M5-M30 ~50K bars, H1 ~66K bars
BARS_TO_FETCH = {
    '5m':  50000,
    '15m': 50000,
    '30m': 50000,
    '1h':  66000,
}


def fetch_candles(symbol: str, timeframe: str, count: int):
    """Fetch candles from MT5."""
    import MetaTrader5 as mt5

    if not mt5.initialize():
        print(f"ERROR: MT5 initialize failed — {mt5.last_error()}")
        return None

    if not mt5.symbol_select(symbol, True):
        print(f"ERROR: Could not select {symbol}")
        mt5.shutdown()
        return None

    tf = TIMEFRAME_MAP.get(timeframe)
    if tf is None:
        print(f"ERROR: Unknown timeframe {timeframe}")
        mt5.shutdown()
        return None

    rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        print(f"WARNING: No data returned for {symbol} {timeframe}")
        return None

    return rates


def append_to_csv(csv_path: Path, rates, asset: str, timeframe: str):
    """Append MT5 rates to CSV file, deduplicating by Date+Time."""
    if csv_path.exists():
        existing_rows = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
        existing_keys = {(r.get('Date', ''), r.get('Time', '')) for r in existing_rows}
    else:
        existing_rows = []
        existing_keys = set()

    new_count = 0
    dup_count = 0

    for rate in rates:
        dt = datetime.fromtimestamp(rate['time'])
        date_str = dt.strftime('%Y.%m.%d')
        time_str = dt.strftime('%H:%M')

        if (date_str, time_str) in existing_keys:
            dup_count += 1
            continue

        existing_rows.append({
            'Date': date_str,
            'Time': time_str,
            'Open': round(rate['open'], 5),
            'High': round(rate['high'], 5),
            'Low': round(rate['low'], 5),
            'Close': round(rate['close'], 5),
            'Volume': int(rate['tick_volume']),
        })
        existing_keys.add((date_str, time_str))
        new_count += 1

    # Sort by Date+Time
    existing_rows.sort(key=lambda r: (r.get('Date', ''), r.get('Time', '')))

    # Write back
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
        writer.writeheader()
        writer.writerows(existing_rows)

    print(f"  {csv_path.name}: +{new_count} new, {dup_count} dupes, total {len(existing_rows)} rows")


def main():
    parser = argparse.ArgumentParser(description='MT5 Data Update')
    parser.add_argument('--asset', choices=['gold', 'silver'], default=None, help='Asset to update (default: both)')
    parser.add_argument('--intervals', nargs='+', default=['5m', '15m', '30m', '1h'], help='Timeframes to update')
    args = parser.parse_args()

    assets = [args.asset] if args.asset else ['gold', 'silver']

    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("ERROR: MetaTrader5 package not installed. Run: pip install MetaTrader5")
        sys.exit(1)

    for asset in assets:
        symbol = SYMBOLS[asset]
        data_dir = DATA_DIR if asset == 'gold' else SILVER_DIR
        print(f"\n{'='*50}")
        print(f"Updating {asset.upper()} ({symbol})")
        print(f"{'='*50}")

        for tf in args.intervals:
            count = BARS_TO_FETCH.get(tf, 2000)
            print(f"  Fetching {tf} ({count} bars)...")
            rates = fetch_candles(symbol, tf, count)
            if rates is not None:
                csv_path = data_dir / f"{asset.title()}_{tf}_Candlestick.csv"
                append_to_csv(csv_path, rates, asset, tf)

    print(f"\nDone at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
