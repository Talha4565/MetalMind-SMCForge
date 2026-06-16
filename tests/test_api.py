"""Phase 2: API Testing"""
import requests
import json
from datetime import datetime

results = []
def test(name, passed, detail=""):
    results.append({"test": name, "passed": passed, "detail": detail})
    s = "PASS" if passed else "FAIL"
    print(f"  [{s}] {name}" + (f" — {detail}" if detail else ""))

BASE = "http://localhost:5000"
FRONTEND = "http://localhost:3000"

print("=" * 60)
print("PHASE 2: API TESTING")
print("=" * 60)

# Health check
print("\n--- Health ---")
try:
    r = requests.get(f"{BASE}/api/health", timeout=10)
    test("API health check", r.status_code == 200, f"Status: {r.status_code}")
except Exception as e:
    test("API health check", False, str(e)[:80])

# Market price
print("\n--- Market Price ---")
for asset in ["gold", "silver"]:
    try:
        r = requests.get(f"{BASE}/api/market/price?asset={asset}", timeout=10)
        data = r.json()
        test(f"Live price for {asset}", r.status_code == 200 and "price" in data, f"Price: ${data.get('price', 'N/A')}")
    except Exception as e:
        test(f"Live price for {asset}", False, str(e)[:80])

# Predictions
print("\n--- Predictions ---")
for asset in ["gold", "silver"]:
    try:
        r = requests.get(f"{BASE}/api/predictions/latest?asset={asset}&limit=1", timeout=30)
        data = r.json()
        pred = data.get("predictions", [{}])[0]
        test(f"Predictions for {asset}", r.status_code == 200 and "signal" in pred,
             f"Signal: {pred.get('signal')}, Confidence: {pred.get('confidence', 0)*100:.1f}%")
        test(f"SHAP values present for {asset}", len(pred.get("shap_values", [])) > 0,
             f"{len(pred.get('shap_values', []))} features")
    except Exception as e:
        test(f"Predictions for {asset}", False, str(e)[:80])

# SHAP feature importance
print("\n--- SHAP ---")
try:
    r = requests.get(f"{BASE}/api/shap/feature-importance?asset=gold", timeout=30)
    # May need auth, check status
    test("SHAP endpoint responds", r.status_code in [200, 401], f"Status: {r.status_code}")
except Exception as e:
    test("SHAP endpoint", False, str(e)[:80])

# Model info
print("\n--- Model Info ---")
try:
    r = requests.get(f"{BASE}/api/models/info", timeout=10)
    test("Model info endpoint", r.status_code == 200, f"Status: {r.status_code}")
except Exception as e:
    test("Model info endpoint", False, str(e)[:80])

# Auth endpoints
print("\n--- Auth ---")
try:
    r = requests.get(f"{FRONTEND}/api/auth/csrf", timeout=10)
    test("CSRF endpoint", r.status_code == 200)
except Exception as e:
    test("CSRF endpoint", False, str(e)[:80])

try:
    r = requests.get(f"{FRONTEND}/api/auth/session", timeout=10)
    test("Session endpoint", r.status_code == 200)
except Exception as e:
    test("Session endpoint", False, str(e)[:80])

# Frontend pages
print("\n--- Frontend Pages ---")
pages = ["/", "/auth/login", "/auth/register", "/dashboard", "/dashboard/risk",
         "/dashboard/profile", "/dashboard/watchlist", "/backtest"]
for page_path in pages:
    try:
        r = requests.get(f"{FRONTEND}{page_path}", timeout=10)
        test(f"Page {page_path}", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        test(f"Page {page_path}", False, str(e)[:80])

# Summary
passed = sum(1 for r in results if r["passed"])
total = len(results)
print(f"\n{'=' * 60}")
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print(f"{'=' * 60}")

with open("reports/phase2_api_results.json", "w") as f:
    json.dump({"summary": {"total": total, "passed": passed}, "tests": results}, f, indent=2)
