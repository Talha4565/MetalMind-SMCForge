"""Verify MT5 bar time matches existing CSV timestamps."""
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
import pandas as pd
from pathlib import Path

if not mt5.initialize():
    print("MT5 not running. Cannot verify.")
    exit()

# Fetch last 1000 bars to ensure overlap with CSV (CSV ends Jul 17, today is Jul 20)
rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M15, 0, 1000)
if rates is None or len(rates) == 0:
    print("No rates from MT5")
    mt5.shutdown()
    exit()

print(f"Fetched {len(rates)} bars from MT5")

base = Path(r"C:\Users\Talha\ml-signals\Gold Dataset")
df = pd.read_csv(base / "Gold_15m_Candlestick_4Y.csv")
print(f"CSV has {len(df):,} rows, ends at {df['Date'].iloc[-1]} {df['Time'].iloc[-1]}")

# Convert MT5 bars to a dict keyed by date+time string
mt5_bars = {}
for bar in rates:
    bar_epoch = int(bar["time"])
    bar_dt = datetime.fromtimestamp(bar_epoch, tz=timezone.utc)
    key = f"{bar_dt.strftime('%Y.%m.%d')} {bar_dt.strftime('%H:%M')}"
    mt5_bars[key] = {
        "epoch": bar_epoch,
        "open": bar["open"],
        "high": bar["high"],
        "low": bar["low"],
        "close": bar["close"],
        "tick_volume": bar["tick_volume"],
    }

# Find overlap: CSV rows whose date+time exists in MT5
matches = 0
mismatches = 0
mismatch_examples = []

for _, row in df.iterrows():
    key = f"{row['Date']} {row['Time']}"
    if key in mt5_bars:
        mb = mt5_bars[key]
        o_diff = abs(float(row["Open"]) - mb["open"])
        c_diff = abs(float(row["Close"]) - mb["close"])
        if o_diff < 0.5 and c_diff < 0.5:
            matches += 1
        else:
            mismatches += 1
            if len(mismatch_examples) < 5:
                mismatch_examples.append({
                    "key": key,
                    "csv_open": row["Open"],
                    "mt5_open": mb["open"],
                    "csv_close": row["Close"],
                    "mt5_close": mb["close"],
                    "o_diff": o_diff,
                    "c_diff": c_diff,
                })

total_overlap = matches + mismatches
print(f"\nOverlapping bars (MT5 & CSV both have): {total_overlap}")
print(f"Matches (diff < 0.5):  {matches}")
print(f"Mismatches (diff >= 0.5): {mismatches}")

if mismatches > 0:
    print("\nMismatch examples:")
    for ex in mismatch_examples:
        print(f"  {ex['key']}: CSV O={ex['csv_open']} C={ex['csv_close']} | MT5 O={ex['mt5_open']:.2f} C={ex['mt5_close']:.2f} | O_diff={ex['o_diff']:.4f} C_diff={ex['c_diff']:.4f}")

if total_overlap == 0:
    print("\nWARNING: Zero overlap between MT5 and CSV timestamps!")
    print("This means the broker time conversion is wrong.")
    print(f"\nSample MT5 times (UTC):")
    for key in list(mt5_bars.keys())[:5]:
        print(f"  {key}")
    print(f"\nSample CSV times (last 5):")
    for _, row in df.tail(5).iterrows():
        print(f"  {row['Date']} {row['Time']}")
else:
    match_pct = (matches / total_overlap) * 100
    print(f"\nMatch rate: {match_pct:.1f}%")
    if match_pct > 99:
        print("VERDICT: CONSISTENT — utcfromtimestamp matches CSV data")
    elif match_pct > 90:
        print("VERDICT: MOSTLY CONSISTENT — minor discrepancies in price (normal for bid/ask differences)")
    else:
        print("VERDICT: INCONSISTENT — time conversion or data source mismatch")

mt5.shutdown()
print("\nDone.")
