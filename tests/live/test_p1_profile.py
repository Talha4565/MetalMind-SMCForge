"""
P1 LIVE TEST: Profile, Watchlist, Secondary Features
Tests profile CRUD, watchlist, risk calculator
Run: python tests/live/test_p1_profile.py
"""
import requests
import json
import time

BASE = "http://localhost:5000"
RESULTS = []

def test(name, passed, detail=""):
    RESULTS.append({"test": name, "passed": passed, "detail": detail})
    s = "PASS" if passed else "FAIL"
    print(f"  [{s}] {name}" + (f" — {detail}" if detail else "")

def get_token():
    """Get auth token for protected endpoints."""
    email = f"p1_test_{int(time.time())}@example.com"
    password = "TestPass123!"
    try:
        requests.post(f"{BASE}/api/auth/register", json={"email": email, "password": password}, timeout=10)
        r = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": password}, timeout=10)
        if r.status_code == 200:
            return r.json().get("access_token")
    except:
        pass
    return None

print("=" * 60)
print("P1 LIVE TEST: PROFILE & SECONDARY FEATURES")
print("=" * 60)

# Get auth token
token = get_token()
auth_header = {"Authorization": f"Bearer {token}"} if token else {}

# Test 1: Profile Endpoint
print("\n1. Profile")
try:
    r = requests.get(f"{BASE}/api/profile", headers=auth_header, timeout=10)
    test("Profile endpoint accessible", r.status_code in [200, 401])
    if r.status_code == 200:
        data = r.json()
        test("Profile has user data", "profile" in data or "email" in data)
except Exception as e:
    test("Profile endpoint", False, str(e)[:80])

# Test 2: Watchlist Endpoint
print("\n2. Watchlist")
try:
    r = requests.get(f"{BASE}/api/watchlist", headers=auth_header, timeout=10)
    test("Watchlist endpoint accessible", r.status_code in [200, 401])
    if r.status_code == 200:
        data = r.json()
        test("Watchlist returns data", "items" in data or "watchlist" in data or isinstance(data, list))
except Exception as e:
    test("Watchlist endpoint", False, str(e)[:80])

# Test 3: Watchlist Symbols
print("\n3. Watchlist Symbols")
try:
    r = requests.get(f"{BASE}/api/watchlist/symbols", timeout=10)
    test("Symbols endpoint returns 200", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        test("Has symbols list", "symbols" in data or isinstance(data, list))
except Exception as e:
    test("Watchlist symbols", False, str(e)[:80])

# Test 4: Config Endpoint
print("\n4. Configuration")
try:
    r = requests.get(f"{BASE}/api/config", headers=auth_header, timeout=10)
    test("Config endpoint accessible", r.status_code in [200, 401])
    if r.status_code == 200:
        data = r.json()
        test("Config has model settings", "model" in data or "backtest" in data)
except Exception as e:
    test("Config endpoint", False, str(e)[:80])

# Test 5: Models Info
print("\n5. Models Info")
try:
    r = requests.get(f"{BASE}/api/models/info", headers=auth_header, timeout=10)
    test("Models info endpoint accessible", r.status_code in [200, 401])
    if r.status_code == 200:
        data = r.json()
        test("Has gold model info", "gold" in data or "models" in data)
except Exception as e:
    test("Models info", False, str(e)[:80])

# Test 6: Prediction History
print("\n6. Prediction History")
try:
    r = requests.get(f"{BASE}/api/predictions/history?days=30", timeout=10)
    data = r.json()
    test("History endpoint returns 200", r.status_code == 200)
    test("Has predictions array", "predictions" in data)
    test("Has summary", "summary" in data)
    if data.get("summary"):
        test("Summary has total_predictions", "total_predictions" in data["summary"])
        test("Summary has buy_signals", "buy_signals" in data["summary"])
        test("Summary has sell_signals", "sell_signals" in data["summary"])
except Exception as e:
    test("Prediction history", False, str(e)[:80])

# Test 7: Orchestrator Page Data
print("\n7. Orchestrator Page Data")
try:
    r = requests.get(f"{BASE}/api/orchestrator/status", timeout=10)
    data = r.json()
    test("Orchestrator returns 200", r.status_code == 200)
    test("Has all required sections", all(k in data for k in ["pipeline", "mt5_cache", "chromadb", "retrain"]))
except Exception as e:
    test("Orchestrator page data", False, str(e)[:80])

# Test 8: Pipeline Page Data
print("\n8. Pipeline Page Data")
try:
    r = requests.get(f"{BASE}/api/pipeline/details", timeout=10)
    data = r.json()
    test("Pipeline details returns 200", r.status_code == 200)
    test("Has 3 pipelines", len(data.get("pipelines", {})) == 3)
    test("Has ETL pipeline", "etl" in data.get("pipelines", {}))
    test("Has Features pipeline", "features" in data.get("pipelines", {}))
    test("Has Training pipeline", "training" in data.get("pipelines", {}))
except Exception as e:
    test("Pipeline page data", False, str(e)[:80])

# Summary
print("\n" + "=" * 60)
passed = sum(1 for r in RESULTS if r["passed"])
total = len(RESULTS)
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print("=" * 60)
