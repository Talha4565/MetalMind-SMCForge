"""
P0 LIVE TEST: Dashboard & Core Endpoints
Tests predictions, SHAP, trade log, market price
Run: python tests/live/test_dashboard.py
"""
import requests
import json

BASE = "http://localhost:5000"
RESULTS = []

def test(name, passed, detail=""):
    RESULTS.append({"test": name, "passed": passed, "detail": detail})
    s = "PASS" if passed else "FAIL"
    print(f"  [{s}] {name}" + (f" — {detail}" if detail else ""))

print("=" * 60)
print("P0 LIVE TEST: DASHBOARD & CORE ENDPOINTS")
print("=" * 60)

# Test 1: API Health
print("\n1. API Health")
try:
    r = requests.get(f"{BASE}/api/health", timeout=10)
    data = r.json()
    test("Health returns 200", r.status_code == 200)
    test("Database OK", data.get("checks", {}).get("database") == "ok")
    test("Gold model loaded", data.get("checks", {}).get("models", {}).get("gold") == True)
except Exception as e:
    test("Health endpoint", False, str(e)[:80])

# Test 2: Live Price
print("\n2. Live Price (MT5)")
try:
    r = requests.get(f"{BASE}/api/market/price?asset=gold", timeout=10)
    data = r.json()
    test("Price endpoint returns 200", r.status_code == 200)
    test("Price has value", data.get("price") is not None, f"${data.get('price', 'N/A')}")
    test("Source is MT5", data.get("source") == "mt5")
except Exception as e:
    test("Live price", False, str(e)[:80])

# Test 3: Predictions
print("\n3. Predictions (Gold)")
try:
    r = requests.get(f"{BASE}/api/predictions/latest?asset=gold&limit=5", timeout=30)
    data = r.json()
    test("Predictions endpoint returns 200", r.status_code == 200)
    preds = data.get("predictions", [])
    test("Has predictions", len(preds) > 0, f"{len(preds)} predictions")
    if preds:
        p = preds[-1]
        test("Prediction has signal", "signal" in p)
        test("Prediction has confidence", "confidence" in p)
        test("Prediction has price", "price" in p)
        test("Prediction has SHAP values", "shap_values" in p)
        test("SHAP has features", len(p.get("shap_values", [])) > 0, f"{len(p.get('shap_values', []))} features")
except Exception as e:
    test("Predictions", False, str(e)[:80])

# Test 4: SHAP Values
print("\n4. SHAP Values")
try:
    r = requests.get(f"{BASE}/api/predictions/latest?asset=gold&limit=1", timeout=30)
    data = r.json()
    pred = data["predictions"][-1]
    shap = pred.get("shap_values", [])
    test("SHAP values present", len(shap) > 0)
    if shap:
        first = shap[0]
        test("SHAP has feature name", "feature" in first)
        test("SHAP has contribution", "contribution" in first)
        test("Feature name is string", isinstance(first["feature"], str))
        test("Contribution is number", isinstance(first["contribution"], (int, float)))
except Exception as e:
    test("SHAP values", False, str(e)[:80])

# Test 5: Trade Log
print("\n5. Trade Log")
try:
    r = requests.get(f"{BASE}/api/predictions/history?days=30&limit=10", timeout=10)
    data = r.json()
    test("Trade log endpoint returns 200", r.status_code == 200)
    test("Has predictions", len(data.get("predictions", [])) > 0)
    test("Has summary", "summary" in data)
    summary = data.get("summary", {})
    test("Summary has total", "total_predictions" in summary)
    test("Summary has wins", "wins" in summary)
except Exception as e:
    test("Trade log", False, str(e)[:80])

# Test 6: Pipeline Status
print("\n6. Pipeline Status")
try:
    r = requests.get(f"{BASE}/api/pipeline/status", timeout=10)
    data = r.json()
    test("Pipeline status returns 200", r.status_code == 200)
    test("Has gold data freshness", "gold" in data.get("data_freshness", {}))
    test("Has silver data freshness", "silver" in data.get("data_freshness", {}))
    test("Has model info", "gold" in data.get("models", {}))
except Exception as e:
    test("Pipeline status", False, str(e)[:80])

# Test 7: Orchestrator Status
print("\n7. Orchestrator Status")
try:
    r = requests.get(f"{BASE}/api/orchestrator/status", timeout=10)
    data = r.json()
    test("Orchestrator returns 200", r.status_code == 200)
    test("Has MT5 cache info", "mt5_cache" in data)
    test("Has ChromaDB info", "chromadb" in data)
    test("Has freshness info", "freshness" in data.get("pipeline", {}))
    test("Has health info", "health" in data.get("pipeline", {}))
except Exception as e:
    test("Orchestrator status", False, str(e)[:80])

# Summary
print("\n" + "=" * 60)
passed = sum(1 for r in RESULTS if r["passed"])
total = len(RESULTS)
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print("=" * 60)
