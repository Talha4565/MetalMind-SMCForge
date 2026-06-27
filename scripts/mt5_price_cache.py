"""
MT5 Price Cache — Writes live spot prices to JSON for the API to read.
Run this alongside MT5 terminal. The API reads the cached prices.

Usage:
    python scripts/mt5_price_cache.py
    (Runs continuously, updates every 5 seconds)
"""

import MetaTrader5 as mt5
import json
import time
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
CACHE_FILE = PROJECT_ROOT / "reports" / "mt5_prices.json"

SYMBOLS = {
    'gold': 'XAUUSD',
    'silver': 'XAGUSD',
}


def update_prices():
    """Fetch prices from MT5 and write to cache file."""
    if not mt5.initialize():
        return False

    prices = {}
    for asset, symbol in SYMBOLS.items():
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            prices[asset] = {
                'price': tick.ask,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': round(tick.ask - tick.bid, 2),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }

    mt5.shutdown()

    if prices:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(prices, indent=2))
        return True
    return False


def main():
    print("MT5 Price Cache — Updates every 5 seconds")
    print(f"Cache file: {CACHE_FILE}")
    print("Press Ctrl+C to stop\n")

    while True:
        try:
            success = update_prices()
            if success:
                prices = json.loads(CACHE_FILE.read_text())
                gold = prices.get('gold', {}).get('price', 'N/A')
                silver = prices.get('silver', {}).get('price', 'N/A')
                print(f"[{datetime.now().strftime('%H:%M:%S')}] XAUUSD={gold} XAGUSD={silver}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] MT5 not connected")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nStopped.")
            break


if __name__ == "__main__":
    main()
