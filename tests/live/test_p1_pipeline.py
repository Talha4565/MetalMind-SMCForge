"""
P1 LIVE TEST: Pipeline & Orchestrator Endpoints
Tests pipeline status, details, orchestrator health
Run: python tests/live/test_p1_pipeline.py
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
print("P1 LIVE TEST: PIPELINE & ORCHESTRATOR")
print("=" * 60)

# Test 1: Pipeline Status
print("\n1. Pipeline Status")
try:
    r = requests.get(f"{BASE}/api/pipeline/status", timeout=10)
    data = r.json()
    test("Status endpoint returns 200", r.status_code == 200)
    test("Has overall status", "status" in data)
    test("Status is active or degraded", data.get("status") in ["active", "degraded"])
    test("Has data_freshness", "data_freshness" in data)
    test("Gold freshness present", "gold" in data.get("data_freshness", {}))
    test("Silver freshness present", "silver" in data.get("data_freshness", {}))
    test("Has models info", "models" in data)
    test("Gold model info present", "gold" in data.get("models", {}))
    test("Has last_update", "last_update" in data)
except Exception as e:
    test("Pipeline status", False, str(e)[:80])

# Test 2: Pipeline Details
print("\n2. Pipeline Details")
try:
    r = requests.get(f"{BASE}/api/pipeline/details", timeout=10)
    data = r.json()
    test("Details endpoint returns 200", r.status_code == 200)
    test("Has pipelines object", "pipelines" in data)
    pipelines = data.get("pipelines", {})
    test("Has ETL pipeline", "etl" in pipelines)
    test("Has Features pipeline", "features" in pipelines)
    test("Has Training pipeline", "training" in pipelines)
    if "etl" in pipelines:
        test("ETL has name", "name" in pipelines["etl"])
        test("ETL has status", "status" in pipelines["etl"])
        test("ETL has schedule", "schedule" in pipelines["etl"])
    test("Has data object", "data" in data)
    test("Has models object", "models" in data)
    test("Has health object", "health" in data)
except Exception as e:
    test("Pipeline details", False, str(e)[:80])

# Test 3: Pipeline Health
print("\n3. Pipeline Health")
try:
    r = requests.get(f"{BASE}/api/pipeline/health", timeout=10)
    data = r.json()
    test("Health endpoint returns 200", r.status_code == 200)
    test("Has update_status", "update_status" in data)
    test("Has retrain_status", "retrain_status" in data)
    test("Has consecutive_failures", "consecutive_failures" in data)
    test("Has last_update", "last_update" in data)
    test("Has last_retrain", "last_retrain" in data)
    test("No consecutive failures", data.get("consecutive_failures", 0) == 0)
except Exception as e:
    test("Pipeline health", False, str(e)[:80])

# Test 4: Orchestrator Status
print("\n4. Orchestrator Status")
try:
    r = requests.get(f"{BASE}/api/orchestrator/status", timeout=10)
    data = r.json()
    test("Orchestrator returns 200", r.status_code == 200)
    test("Has pipeline object", "pipeline" in data)
    test("Has mt5_cache object", "mt5_cache" in data)
    test("Has chromadb object", "chromadb" in data)
    test("Has retrain object", "retrain" in data)
    test("Has timestamp", "timestamp" in data)
    
    # MT5 Cache details
    mt5 = data.get("mt5_cache", {})
    test("MT5 cache exists", mt5.get("exists") == True)
    test("MT5 cache fresh", mt5.get("fresh") == True)
    
    # ChromaDB details
    chroma = data.get("chromadb", {})
    test("ChromaDB connected", chroma.get("connected") == True)
    test("ChromaDB has signals", chroma.get("signal_count", 0) > 0, f"{chroma.get('signal_count', 0)} signals")
    
    # Retrain details
    retrain = data.get("retrain", {})
    test("Retrain has outcomes", "outcomes_available" in retrain)
    test("Retrain has win_rate", "win_rate" in retrain)
    test("Win rate above threshold", retrain.get("win_rate", 0) >= 0.55, f"{retrain.get('win_rate', 0)*100:.1f}%")
    
    # Pipeline freshness
    pipeline = data.get("pipeline", {})
    freshness = pipeline.get("freshness", {})
    test("Gold data fresh", freshness.get("gold", {}).get("is_fresh") == True)
    test("Silver data fresh", freshness.get("silver", {}).get("is_fresh") == True)
    
    # Pipeline health
    health = pipeline.get("health", {})
    test("Health: no failures", health.get("consecutive_failures", 0) == 0)
    test("Health: update status OK", health.get("update_status") == "success")
    test("Health: retrain status OK", health.get("retrain_status") == "success")
    
    # Pipeline backups
    backups = pipeline.get("backups", [])
    test("Has model backups", len(backups) > 0, f"{len(backups)} backups")
except Exception as e:
    test("Orchestrator status", False, str(e)[:80])

# Test 5: ETL Health
print("\n5. ETL Health")
try:
    r = requests.get(f"{BASE}/api/etl/health", timeout=10)
    data = r.json()
    test("ETL health returns 200", r.status_code == 200)
    test("ETL status is healthy", data.get("status") == "healthy")
except Exception as e:
    test("ETL health", False, str(e)[:80])

# Summary
print("\n" + "=" * 60)
passed = sum(1 for r in RESULTS if r["passed"])
total = len(RESULTS)
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print("=" * 60)
