"""
P1 LIVE TEST: Backtest Endpoints
Tests backtest run, status, results, export
Run: python tests/live/test_p1_backtest.py
"""
import requests
import json
import time

BASE = "http://localhost:5000"
RESULTS = []

def test(name, passed, detail=""):
    RESULTS.append({"test": name, "passed": passed, "detail": detail})
    s = "PASS" if passed else "FAIL"
    print(f"  [{s}] {name}" + (f" — {detail}" if detail else ""))

print("=" * 60)
print("P1 LIVE TEST: BACKTEST")
print("=" * 60)

# Test 1: Get existing backtest results
print("\n1. Backtest Results (Gold)")
try:
    r = requests.get(f"{BASE}/api/backtest/results?asset=gold", timeout=10)
    data = r.json()
    test("Results endpoint returns 200", r.status_code == 200)
    test("Has summary", "summary" in data)
    if "summary" in data:
        s = data["summary"]
        test("Has win_rate", "win_rate" in s, f"{s.get('win_rate', 0)*100:.1f}%")
        test("Has profit_factor", "profit_factor" in s, f"{s.get('profit_factor', 0):.2f}")
        test("Has total_trades", "n_trades" in s, f"{s.get('n_trades', 0)} trades")
    test("Has trades array", "trades" in data)
    test("Trades is non-empty", len(data.get("trades", [])) > 0, f"{len(data.get('trades', []))} trades")
except Exception as e:
    test("Backtest results", False, str(e)[:80])

# Test 2: Backtest results structure
print("\n2. Backtest Trade Structure")
try:
    r = requests.get(f"{BASE}/api/backtest/results?asset=gold", timeout=10)
    data = r.json()
    if data.get("trades"):
        trade = data["trades"][0]
        test("Trade has entry_time", "entry_time" in trade)
        test("Trade has entry_price", "entry_price" in trade)
        test("Trade has exit_time", "exit_time" in trade)
        test("Trade has exit_price", "exit_price" in trade)
        test("Trade has direction", "direction" in trade)
        test("Trade has pnl_usd", "pnl_usd" in trade)
        test("Trade has hit_tp", "hit_tp" in trade)
        test("Trade has hit_sl", "hit_sl" in trade)
except Exception as e:
    test("Trade structure", False, str(e)[:80])

# Test 3: Backtest status
print("\n3. Backtest Status")
try:
    r = requests.get(f"{BASE}/api/backtest/status", timeout=10)
    data = r.json()
    test("Status endpoint returns 200", r.status_code == 200)
    test("Has running field", "running" in data)
    test("Has progress field", "progress" in data)
    test("Not currently running", data.get("running") == False)
except Exception as e:
    test("Backtest status", False, str(e)[:80])

# Test 4: Silver backtest results
print("\n4. Backtest Results (Silver)")
try:
    r = requests.get(f"{BASE}/api/backtest/results?asset=silver", timeout=10)
    data = r.json()
    test("Silver results endpoint returns 200", r.status_code == 200)
    test("Has summary", "summary" in data)
    if "summary" in data:
        test("Has win_rate", "win_rate" in data["summary"])
except Exception as e:
    test("Silver backtest", False, str(e)[:80])

# Test 5: Invalid asset
print("\n5. Invalid Asset")
try:
    r = requests.get(f"{BASE}/api/backtest/results?asset=bitcoin", timeout=10)
    test("Invalid asset returns 400", r.status_code == 400, f"Status: {r.status_code}")
except Exception as e:
    test("Invalid asset", False, str(e)[:80])

# Summary
print("\n" + "=" * 60)
passed = sum(1 for r in RESULTS if r["passed"])
total = len(RESULTS)
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print("=" * 60)
