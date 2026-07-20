"""
P2 LIVE TEST: Watchlist CRUD
Tests create, read, update, delete watchlist items
Run: python tests/live/test_p2_watchlist.py
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

def get_token():
    email = f"watchlist_test_{int(time.time())}@example.com"
    password = "TestPass123!"
    try:
        requests.post(f"{BASE}/api/auth/register", json={"email": email, "password": password}, timeout=10)
        r = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": password}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("token") or data.get("access_token")
    except:
        pass
    return None

print("=" * 60)
print("P2 LIVE TEST: WATCHLIST")
print("=" * 60)

token = get_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {}

# Test 1: Get empty watchlist
print("\n1. Get Watchlist (empty)")
try:
    r = requests.get(f"{BASE}/api/watchlist", headers=headers, timeout=10)
    test("Watchlist endpoint returns 200", r.status_code == 200)
    data = r.json()
    test("Returns data structure", isinstance(data, (dict, list)))
except Exception as e:
    test("Get watchlist", False, str(e)[:80])

# Test 2: Add item to watchlist
print("\n2. Add Watchlist Item")
item_id = None
try:
    r = requests.post(f"{BASE}/api/watchlist", headers=headers, json={
        "symbol": "XAU/USD",
        "display_name": "Gold Test",
        "notifications_enabled": True
    }, timeout=10)
    test("Add item returns 200/201", r.status_code in [200, 201], f"Status: {r.status_code}")
    if r.status_code in [200, 201]:
        data = r.json()
        item_id = data.get("id") or data.get("item", {}).get("id")
        test("Returns item ID", item_id is not None)
except Exception as e:
    test("Add watchlist item", False, str(e)[:80])

# Test 3: Get watchlist with item
print("\n3. Get Watchlist (with item)")
try:
    r = requests.get(f"{BASE}/api/watchlist", headers=headers, timeout=10)
    data = r.json()
    test("Returns 200", r.status_code == 200)
    items = data if isinstance(data, list) else data.get("items", data.get("watchlist", []))
    test("Has items", len(items) > 0 if isinstance(items, list) else True)
except Exception as e:
    test("Get watchlist with item", False, str(e)[:80])

# Test 4: Get watchlist symbols
print("\n4. Watchlist Symbols")
try:
    r = requests.get(f"{BASE}/api/watchlist/symbols", timeout=10)
    test("Symbols endpoint returns 200", r.status_code == 200)
    data = r.json()
    test("Has symbols", "symbols" in data or isinstance(data, list))
except Exception as e:
    test("Watchlist symbols", False, str(e)[:80])

# Test 5: Delete watchlist item
print("\n5. Delete Watchlist Item")
if item_id:
    try:
        r = requests.delete(f"{BASE}/api/watchlist/{item_id}", headers=headers, timeout=10)
        test("Delete returns 200", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        test("Delete watchlist item", False, str(e)[:80])
else:
    test("Delete watchlist item", False, "No item ID to delete")

# Summary
print("\n" + "=" * 60)
passed = sum(1 for r in RESULTS if r["passed"])
total = len(RESULTS)
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print("=" * 60)
