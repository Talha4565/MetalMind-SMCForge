#!/usr/bin/env python3
"""
MT5 OHLCV Bar Updater  -  runs on Windows host (not in Docker).

Appends completed OHLCV bars from MetaTrader 5 to CSV datasets
for all 4 timeframes × 2 assets (gold/silver). Runs alongside
mt5_price_cache.py  -  they are independent processes.

Usage:
    python scripts/mt5_bar_updater.py
    python scripts/mt5_bar_updater.py --poll-interval 10 --backfill-max 100
    python scripts/mt5_bar_updater.py --dry-run

Requires:
    - MetaTrader 5 terminal running and logged in
    - MetaTrader5 Python package (pip install MetaTrader5)
    - pandas
"""

import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

# Ensure project root is on sys.path for config import
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import GOLD_DATASET_DIR, SILVER_DATASET_DIR

# ---------------------------------------------------------------------------
# Series definitions (8 total: 4 timeframes x 2 assets)
# ---------------------------------------------------------------------------
# Each entry: key (short id), MT5 symbol, MT5 timeframe constant name,
#             period_sec (bar duration in seconds), CSV file path.
# The tf_name is resolved at runtime against the installed mt5 module.
# ---------------------------------------------------------------------------
SERIES = [
    # Gold
    {"key": "gold_5m",  "symbol": "XAUUSD", "tf_name": "TIMEFRAME_M5",  "period_sec": 300,
     "file": GOLD_DATASET_DIR / "Gold_5m_Candlestick.csv"},
    {"key": "gold_15m", "symbol": "XAUUSD", "tf_name": "TIMEFRAME_M15", "period_sec": 900,
     "file": GOLD_DATASET_DIR / "Gold_15m_Candlestick_4Y.csv"},
    {"key": "gold_30m", "symbol": "XAUUSD", "tf_name": "TIMEFRAME_M30", "period_sec": 1800,
     "file": GOLD_DATASET_DIR / "Gold_30m_Candlestick.csv"},
    {"key": "gold_1h",  "symbol": "XAUUSD", "tf_name": "TIMEFRAME_H1",  "period_sec": 3600,
     "file": GOLD_DATASET_DIR / "Gold_1h_Candlestick.csv"},
    # Silver
    {"key": "silver_5m",  "symbol": "XAGUSD", "tf_name": "TIMEFRAME_M5",  "period_sec": 300,
     "file": SILVER_DATASET_DIR / "Silver_5m_Candlestick.csv"},
    {"key": "silver_15m", "symbol": "XAGUSD", "tf_name": "TIMEFRAME_M15", "period_sec": 900,
     "file": SILVER_DATASET_DIR / "Silver_15m_Candlestick.csv"},
    {"key": "silver_30m", "symbol": "XAGUSD", "tf_name": "TIMEFRAME_M30", "period_sec": 1800,
     "file": SILVER_DATASET_DIR / "Silver_30m_Candlestick.csv"},
    {"key": "silver_1h",  "symbol": "XAGUSD", "tf_name": "TIMEFRAME_H1",  "period_sec": 3600,
     "file": SILVER_DATASET_DIR / "Silver_1h_Candlestick.csv"},
]

# Live price cache (merged from mt5_price_cache.py)
PRICE_CACHE_FILE = PROJECT_ROOT / "data" / "mt5_prices.json"
PRICE_SYMBOLS = {"gold": "XAUUSD", "silver": "XAGUSD"}

logger = logging.getLogger("mt5_bar_updater")


# ============================================================================
# HELPERS
# ============================================================================

def setup_logging():
    """Configure logging with the project's preferred timestamp format."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def import_mt5():
    """Import and validate the MetaTrader5 package. Exits on failure."""
    try:
        import MetaTrader5 as mt5  # noqa
    except ImportError:
        logger.error("MetaTrader5 package not installed. Run: pip install MetaTrader5")
        sys.exit(1)
    return mt5


def resolve_timeframes(mt5_mod):
    """Map series keys to MT5 timeframe constants (resolved at runtime)."""
    result = {}
    for s in SERIES:
        tf = getattr(mt5_mod, s["tf_name"], None)
        if tf is None:
            logger.error(
                "MT5 timeframe %s not found  -  MT5 version may be incompatible.",
                s["tf_name"],
            )
            sys.exit(1)
        result[s["key"]] = tf
    return result


def read_last_bar_time(filepath):
    """
    Read the last completed bar's timestamp from a CSV file.

    Reads only the last ~200 bytes  -  efficient for files of any size.
    Returns the Unix epoch (int) of the last bar, or None if the file is
    empty / missing / unparseable.
    """
    if not filepath.is_file():
        return None

    try:
        with open(filepath, "rb") as fh:
            fh.seek(0, 2)                     # SEEK_END
            size = fh.tell()
            if size == 0:
                return None
            read_size = min(200, size)
            fh.seek(size - read_size)
            tail = fh.read(read_size).decode("utf-8").rstrip()
    except Exception as exc:
        logger.warning("Cannot read %s: %s", filepath.name, exc)
        return None

    lines = tail.split("\n")
    last_line = lines[-1].strip() if lines else ""
    if not last_line:
        return None

    parts = last_line.split(",")
    if len(parts) < 7:
        return None

    # Parse date and time (strptime %H accepts both "1:00" and "01:00")
    try:
        dt = datetime.strptime(f"{parts[0]} {parts[1]}", "%Y.%m.%d %H:%M")
    except ValueError:
        return None
    return int(dt.timestamp())


def format_bar_row(bar):
    """
    Convert a single mt5 bar (numpy record) into a CSV-row dict.

    Uses tick_volume (NOT real_volume  -  always 0 for XAUUSD/XAGUSD CFDs).
    Returns None if any OHLC value is <= 0 (broker glitch / empty bar  -  would
    kill the model with division-by-zero in feature engineering).
    """
    open_p  = float(bar["open"])
    high_p  = float(bar["high"])
    low_p   = float(bar["low"])
    close_p = float(bar["close"])

    if open_p <= 0 or high_p <= 0 or low_p <= 0 or close_p <= 0:
        bar_dt = datetime.fromtimestamp(int(bar["time"]), tz=timezone.utc)
        logger.warning(
            "SKIPPED bar at %s  -  zero/negative OHLC (O=%s H=%s L=%s C=%s)  -  broker glitch?",
            bar_dt.strftime("%Y.%m.%d %H:%M"), open_p, high_p, low_p, close_p,
        )
        return None

    bar_dt = datetime.fromtimestamp(int(bar["time"]), tz=timezone.utc)
    return {
        "Date":   bar_dt.strftime("%Y.%m.%d"),
        "Time":   bar_dt.strftime("%H:%M"),
        "Open":   open_p,
        "High":   high_p,
        "Low":    low_p,
        "Close":  close_p,
        "Volume": bar["tick_volume"],
    }


def bar_datetime_str(bar):
    """Return a human-readable 'YYYY.MM.DD HH:MM' string for a bar."""
    return datetime.fromtimestamp(int(bar["time"]), tz=timezone.utc).strftime("%Y.%m.%d %H:%M")


def stale_description(epoch_now, epoch_bar):
    """Human-readable duration for log messages (e.g. '2.9d', '45m')."""
    secs = epoch_now - epoch_bar
    if secs < 0:
        return "0s"
    if secs < 60:
        return f"{secs:.0f}s"
    if secs < 3600:
        return f"{secs / 60:.1f}m"
    if secs < 86400:
        return f"{secs / 3600:.1f}h"
    return f"{secs / 86400:.1f}d"


# ============================================================================
# BACKFILL
# ============================================================================

def get_backfill_bars(mt5, symbol, tf, last_epoch, max_bars):
    """
    Fetch all completed bars from MT5 that are strictly newer than *last_epoch*.

    Uses ``copy_rates_range`` for a single efficient bulk read.  The
    latest completed bar (via ``copy_rates_from_pos``) is used as an upper
    bound so the forming (incomplete) bar is never included.

    Returns a list of numpy records sorted by time ascending.
    """
    # Latest *completed* bar  -  this is our upper bound
    latest = mt5.copy_rates_from_pos(symbol, tf, 1, 1)
    if latest is None or len(latest) == 0:
        return []
    latest_epoch = int(latest[0]["time"])

    if latest_epoch <= last_epoch:
        return []                                # nothing new on MT5

    # Fetch all bars in the gap (request a 1-hr future buffer for safety)
    now_epoch = int(time.time())
    all_rates = mt5.copy_rates_range(
        symbol, tf, last_epoch + 1, now_epoch + 3600,
    )
    if all_rates is None or len(all_rates) == 0:
        return []

    # Strict bounds: > last_epoch and <= latest_completed
    result = [
        b for b in all_rates
        if last_epoch < int(b["time"]) <= latest_epoch
    ]
    result.sort(key=lambda b: int(b["time"]))

    if max_bars > 0 and len(result) > max_bars:
        result = result[-max_bars:]

    return result


# ============================================================================
# WRITE HELPERS
# ============================================================================

def write_batch(filepath, bar_records):
    """Append a list of bar dicts to a CSV file in one batch."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(bar_records)
    df.to_csv(filepath, mode="a", header=False, index=False)


def write_one(filepath, row_dict):
    """Append a single bar dict to a CSV file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([row_dict])
    df.to_csv(filepath, mode="a", header=False, index=False)


# ============================================================================
# LIVE PRICE CACHE (merged from mt5_price_cache.py)
# ============================================================================

def write_price_cache(mt5):
    """Fetch live bid/ask from MT5 and write atomic JSON for the Docker API."""
    prices = {}
    for asset, symbol in PRICE_SYMBOLS.items():
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            continue
        info = mt5.symbol_info(symbol)
        if info is None:
            continue
        prices[asset] = {
            "symbol": symbol,
            "bid": tick.bid,
            "ask": tick.ask,
            "price": (tick.bid + tick.ask) / 2.0,
            "spread": round((tick.ask - tick.bid) / info.point, 1),
            "timestamp": datetime.now().isoformat(),
        }

    if not prices:
        return False

    cache = {"source": "mt5", "updated_at": datetime.now().isoformat(), "prices": prices}
    PRICE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = PRICE_CACHE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(cache, f, indent=2)
    tmp.replace(PRICE_CACHE_FILE)
    return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="MT5 OHLCV Bar Updater  -  append completed bars to CSV datasets",
    )
    parser.add_argument(
        "--poll-interval", type=int, default=2,
        help="Seconds between polls (default: 2)",
    )
    parser.add_argument(
        "--backfill-max", type=int, default=500,
        help="Max bars to backfill per series on first run (default: 500, 0 = unlimited)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch bars but do not write  -  only log what would be written",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Run one poll cycle (backfill + live prices) and exit (for Task Scheduler)",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # MT5 initialisation
    # ------------------------------------------------------------------
    mt5 = import_mt5()
    timeframes = resolve_timeframes(mt5)

    if not mt5.initialize():
        err = mt5.last_error()
        logger.error("MT5 initialize failed  -  %s", err)
        logger.error("Make sure MetaTrader 5 terminal is running and logged in.")
        sys.exit(1)

    logger.info("STARTED  -  watching %d series", len(SERIES))

    # ------------------------------------------------------------------
    # Start-up: recover last-written bar times from CSV files
    # ------------------------------------------------------------------
    now = int(time.time())
    last_written = {}                           # series_key -> epoch | None
    for s in SERIES:
        key = s["key"]
        epoch = read_last_bar_time(s["file"])
        if epoch is not None:
            last_written[key] = epoch
            logger.info(
                "%s: last bar at %s (stale by %s)",
                key,
                datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y.%m.%d %H:%M"),
                stale_description(now, epoch),
            )
        else:
            last_written[key] = None
            logger.info("%s: no existing data  -  will skip until CSV exists", key)

    # ------------------------------------------------------------------
    # Backfill any gaps (stale files since last run)
    # ------------------------------------------------------------------
    for s in SERIES:
        key = s["key"]
        last_epoch = last_written.get(key)
        if last_epoch is None:
            continue                             # no data yet, nothing to backfill

        # Quick check: is there anything newer on MT5?
        latest = mt5.copy_rates_from_pos(s["symbol"], timeframes[key], 1, 1)
        if latest is None or len(latest) == 0:
            continue
        if int(latest[0]["time"]) <= last_epoch:
            continue                             # CSV is already up to date

        try:
            bars = get_backfill_bars(
                mt5, s["symbol"], timeframes[key],
                last_epoch, args.backfill_max,
            )
        except Exception as exc:
            logger.error("%s: backfill fetch error: %s", key, exc)
            continue

        if not bars:
            continue

        count = len(bars)
        logger.info("%s: backfilling %d bars...", key, count)

        if args.dry_run:
            logger.info("%s: (dry-run) would write %d bars", key, count)
            for bar in bars:
                logger.info(
                    "%s: would-backfill bar at %s O=%s C=%s V=%s",
                    key, bar_datetime_str(bar),
                    bar["open"], bar["close"], bar["tick_volume"],
                )
            continue

        start_ts = time.time()
        try:
            rows = [r for bar in bars if (r := format_bar_row(bar)) is not None]
            if not rows:
                logger.warning("%s: all backfill bars rejected (zero OHLC)", key)
                continue
            write_batch(s["file"], rows)
            last_written[key] = int(bars[-1]["time"])
            elapsed = time.time() - start_ts
            logger.info(
                "%s: backfill complete (%d bars in %.1fs)  -  last bar at %s",
                key, count, elapsed,
                datetime.fromtimestamp(last_written[key], tz=timezone.utc).strftime("%Y.%m.%d %H:%M"),
            )
        except Exception as exc:
            logger.error("%s: backfill write failed: %s", key, exc)

    # ------------------------------------------------------------------
    # Switch to poll loop  -  bars + live prices
    # ------------------------------------------------------------------
    poll_interval = max(1, args.poll_interval)
    logger.info("Polling every %ds (bars + live prices). Press Ctrl+C to stop.\n", poll_interval)

    try:
        while True:
            poll_start = time.time()

            # --- Completed bars (OHLCV -> CSV) ---
            for s in SERIES:
                key = s["key"]
                last_epoch = last_written.get(key)
                if last_epoch is None:
                    continue

                try:
                    rates = mt5.copy_rates_from_pos(
                        s["symbol"], timeframes[key], 1, 1,
                    )
                except Exception as exc:
                    logger.error("%s: MT5 query error: %s", key, exc)
                    continue

                if rates is None or len(rates) == 0:
                    continue

                bar = rates[0]
                bar_epoch = int(bar["time"])

                if bar_epoch <= last_epoch:
                    continue

                if args.dry_run:
                    logger.info(
                        "%s: would-append bar at %s O=%s C=%s V=%s",
                        key, bar_datetime_str(bar),
                        bar["open"], bar["close"], bar["tick_volume"],
                    )
                    last_written[key] = bar_epoch
                    continue

                try:
                    row = format_bar_row(bar)
                    if row is None:
                        last_written[key] = bar_epoch
                        continue
                    write_one(s["file"], row)
                    last_written[key] = bar_epoch
                    logger.info(
                        "%s: appended bar at %s O=%s C=%s V=%s",
                        key, bar_datetime_str(bar),
                        bar["open"], bar["close"], bar["tick_volume"],
                    )
                except Exception as exc:
                    logger.error("%s: write error: %s", key, exc)

            # --- Live bid/ask prices (for LiveTicker / API) ---
            if not args.dry_run:
                try:
                    write_price_cache(mt5)
                except Exception as exc:
                    logger.error("Price cache write error: %s", exc)

            # --once: run one cycle and exit
            if args.once:
                logger.info("--once: cycle complete, exiting.")
                break

            # Sleep for the remaining poll interval
            elapsed = time.time() - poll_start
            sleep_sec = max(0.1, poll_interval - elapsed)
            time.sleep(sleep_sec)

    except KeyboardInterrupt:
        logger.info("Shutdown by user.")
    finally:
        mt5.shutdown()
        logger.info("MT5 disconnected. Goodbye.")


if __name__ == "__main__":
    main()
