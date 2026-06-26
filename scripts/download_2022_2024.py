"""Download 2022-2024 15m gold data from MT5 and concatenate with existing."""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
GOLD_DIR = PROJECT_ROOT / "Gold Dataset"

if not mt5.initialize():
    print("MT5 init failed:", mt5.last_error())
    exit(1)

print("MT5 initialized")

from_date = datetime(2022, 5, 1)
to_date = datetime(2024, 5, 13)

rates = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_M15, from_date, to_date)

if rates is None or len(rates) == 0:
    print("copy_rates_range returned nothing, trying copy_rates_from_pos with 100K bars...")
    rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M15, 0, 100000)

if rates is None or len(rates) == 0:
    print("ERROR: No data available from MT5")
    mt5.shutdown()
    exit(1)

df = pd.DataFrame(rates)
df["time"] = pd.to_datetime(df["time"], unit="s")
df["Date"] = df["time"].dt.strftime("%Y.%m.%d")
df["Time"] = df["time"].dt.strftime("%H:%M")
df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "tick_volume": "Volume"}, inplace=True)
df = df[["Date", "Time", "Open", "High", "Low", "Close", "Volume"]]

first_date = df["Date"].iloc[0]
last_date = df["Date"].iloc[-1]
print(f"Downloaded {len(df)} rows: {first_date} to {last_date}")

# Save as separate file
old_file = GOLD_DIR / "Gold_15m_2022_2024.csv"
df.to_csv(old_file, index=False)
print(f"Saved to {old_file}")

# Load existing data
existing_file = GOLD_DIR / "Gold_15m_Candlestick.csv"
existing = pd.read_csv(existing_file)
print(f"Existing: {len(existing)} rows ({existing['Date'].iloc[0]} to {existing['Date'].iloc[-1]})")

# Concatenate: old data on top, existing data on bottom
combined = pd.concat([df, existing], ignore_index=True)
combined.drop_duplicates(subset=["Date", "Time"], keep="last", inplace=True)
combined.sort_values(["Date", "Time"], inplace=True)
combined.reset_index(drop=True, inplace=True)

print(f"Combined: {len(combined)} rows ({combined['Date'].iloc[0]} to {combined['Date'].iloc[-1]})")

# Backup existing file
backup = GOLD_DIR / "Gold_15m_Candlestick_backup.csv"
existing.to_csv(backup, index=False)
print(f"Backed up existing to {backup}")

# Overwrite
combined.to_csv(existing_file, index=False)
print(f"Updated {existing_file}")

mt5.shutdown()
print("Done!")
