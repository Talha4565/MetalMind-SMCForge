"""
MT5 Live Price Cache — runs on Windows host (not in Docker).

Fetches live spot prices from MetaTrader 5 every 15 seconds
and writes them to data/mt5_prices.json for the Docker API to read.

Usage:
    python scripts/mt5_price_cache.py

Requires:
    - MetaTrader 5 terminal running (demo or real account)
    - MetaTrader5 Python package (pip install MetaTrader5)
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

OUTPUT_FILE = Path(__file__).parent.parent / 'data' / 'mt5_prices.json'
SYMBOLS = {
    'gold': 'XAUUSD',
    'silver': 'XAGUSD',
}
POLL_INTERVAL = 5  # seconds


def fetch_prices():
    """Fetch live prices from MT5 for all symbols."""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("ERROR: MetaTrader5 package not installed. Run: pip install MetaTrader5")
        sys.exit(1)

    if not mt5.initialize():
        print(f"ERROR: MT5 initialize failed — {mt5.last_error()}")
        print("Make sure MetaTrader 5 terminal is running and logged in.")
        return None

    prices = {}
    for asset, symbol in SYMBOLS.items():
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"WARNING: No tick data for {symbol}")
            continue

        info = mt5.symbol_info(symbol)
        if info is None:
            continue

        prices[asset] = {
            'symbol': symbol,
            'bid': tick.bid,
            'ask': tick.ask,
            'price': (tick.bid + tick.ask) / 2,  # mid price
            'spread': round((tick.ask - tick.bid) / info.point, 1),
            'timestamp': datetime.now().isoformat(),
        }

    mt5.shutdown()
    return prices


def write_cache(prices):
    """Write prices to JSON file atomically."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    cache = {
        'source': 'mt5',
        'updated_at': datetime.now().isoformat(),
        'prices': prices,
    }

    tmp = OUTPUT_FILE.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        json.dump(cache, f, indent=2)
    tmp.replace(OUTPUT_FILE)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='MT5 Price Cache')
    parser.add_argument('--once', action='store_true', help='Run once and exit (for scheduled tasks)')
    args = parser.parse_args()

    print(f"MT5 Price Cache — writing to {OUTPUT_FILE}")

    if args.once:
        prices = fetch_prices()
        if prices:
            write_cache(prices)
            ts = datetime.now().strftime('%H:%M:%S')
            for asset, data in prices.items():
                print(f"  [{ts}] {asset.upper()}: ${data['price']:.2f} (spread {data['spread']})")
        else:
            print("  No prices fetched")
        return

    print(f"Polling every {POLL_INTERVAL}s. Press Ctrl+C to stop.\n")
    while True:
        try:
            prices = fetch_prices()
            if prices:
                write_cache(prices)
                ts = datetime.now().strftime('%H:%M:%S')
                for asset, data in prices.items():
                    print(f"  [{ts}] {asset.upper()}: ${data['price']:.2f} (spread {data['spread']})")
            else:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] No prices fetched")
        except Exception as e:
            print(f"  ERROR: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
