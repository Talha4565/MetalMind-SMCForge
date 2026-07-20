"""Scan CSVs for $0 OHLC values that would kill the model."""
import pandas as pd
from pathlib import Path

gold_dir = Path(r"C:\Users\Talha\ml-signals\Gold Dataset")
silver_dir = Path(r"C:\Users\Talha\ml-signals\Silver Dataset")

files = [
    (gold_dir / "Gold_5m_Candlestick.csv", "gold_5m"),
    (gold_dir / "Gold_15m_Candlestick_4Y.csv", "gold_15m"),
    (gold_dir / "Gold_30m_Candlestick.csv", "gold_30m"),
    (gold_dir / "Gold_1h_Candlestick.csv", "gold_1h"),
    (silver_dir / "Silver_5m_Candlestick.csv", "silver_5m"),
    (silver_dir / "Silver_15m_Candlestick.csv", "silver_15m"),
    (silver_dir / "Silver_30m_Candlestick.csv", "silver_30m"),
    (silver_dir / "Silver_1h_Candlestick.csv", "silver_1h"),
]

print("SCANNING FOR $0 IN OHLC COLUMNS")
print("=" * 60)
total_zeros = 0

for fpath, name in files:
    if not fpath.exists():
        print(f"{name}: FILE NOT FOUND")
        continue
    df = pd.read_csv(fpath)
    row_count = len(df)
    # Check recent data (last 2000 rows) + full scan for zeros
    recent = df.tail(2000)
    has_issue = False
    for col in ["Open", "High", "Low", "Close"]:
        zeros_recent = len(recent[recent[col] == 0])
        zeros_all = len(df[df[col] == 0])
        if zeros_recent > 0:
            print(f"ZERO: {name} {col} = {zeros_recent} bars in last 2000")
            total_zeros += zeros_recent
            has_issue = True
        elif zeros_all > 0:
            print(f"ZERO (historical): {name} {col} = {zeros_all} bars total")
            has_issue = True

    if not has_issue:
        # Quick sanity: are values reasonable?
        is_gold = "Gold" in name
        min_expected = 1000 if is_gold else 10
        min_val = recent[["Open", "High", "Low", "Close"]].min().min()
        max_val = recent[["Open", "High", "Low", "Close"]].max().max()
        print(f"OK: {name} ({row_count:,} rows, range ${min_val:.2f}-${max_val:.2f})")

print()
if total_zeros == 0:
    print("NO $0 VALUES FOUND in any OHLC column")
else:
    print(f"TOTAL $0 BARS: {total_zeros}  -  MODEL WOULD BE AFFECTED")

# Check today's bars
print()
print("=" * 60)
print("TODAY (2026.07.20) - spot check of new bars")
print("=" * 60)
for fpath, name in files:
    if not fpath.exists():
        continue
    df = pd.read_csv(fpath)
    today = df[df["Date"] == "2026.07.20"]
    if len(today) > 0:
        first = today.iloc[0]
        last = today.iloc[-1]
        print(f"{name}: {len(today)} bars | First: {first['Time']} C={first['Close']} | Last: {last['Time']} C={last['Close']}")
    else:
        print(f"{name}: no bars for today")
