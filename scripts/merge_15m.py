"""Merge Gold_15m_2022_2024.csv + Gold_15m_Candlestick.csv into Gold_15m_Candlestick_4Y.csv"""
import pandas as pd
from pathlib import Path

base = Path(r'C:\Users\Talha\ml-signals\Gold Dataset')

old = pd.read_csv(base / 'Gold_15m_2022_2024.csv')
new = pd.read_csv(base / 'Gold_15m_Candlestick.csv')

print(f"Old: {len(old):,} rows | {old['Date'].iloc[0]} -> {old['Date'].iloc[-1]}")
print(f"New: {len(new):,} rows | {new['Date'].iloc[0]} -> {new['Date'].iloc[-1]}")

merged = pd.concat([old, new], ignore_index=True)
merged['DateTime'] = pd.to_datetime(merged['Date'] + ' ' + merged['Time'], format='mixed')
merged = merged.sort_values('DateTime').reset_index(drop=True)

dupes = merged['DateTime'].duplicated().sum()
print(f"Duplicates: {dupes}")
print(f"Merged: {len(merged):,} rows | {merged['Date'].iloc[0]} -> {merged['Date'].iloc[-1]}")

merged = merged.drop(columns=['DateTime'])
merged.to_csv(base / 'Gold_15m_Candlestick_4Y.csv', index=False)

out = base / 'Gold_15m_Candlestick_4Y.csv'
print(f"Saved: {out.name} ({out.stat().st_size / 1024:.0f} KB)")

# Delete backup
bak = base / 'Gold_15m_Candlestick_backup.csv'
if bak.exists():
    bak.unlink()
    print(f"Deleted: {bak.name}")
else:
    print("Backup already gone")

print("\nDone.")
