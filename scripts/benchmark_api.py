"""
MetalMind SMCForge — API Performance Benchmark Suite
Measures p50, p95, p99 latency for all key endpoints.
Run: python scripts/benchmark_api.py
Requires: pip install requests
"""

import requests
import time
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "http://localhost:5000"
N_WARMUP = 2
N_SAMPLES = 30
TIMEOUT = 30

ENDPOINTS = [
    {"name": "POST /auth/login", "method": "POST", "path": "/api/auth/login",
     "body": {"email": "benchmark@test.com", "password": "Bench123!x"}, "nfr": None},
    {"name": "GET /api/health", "method": "GET", "path": "/api/health", "body": None, "nfr": None},
    {"name": "POST /forecast/gold", "method": "GET", "path": "/api/predictions/latest?asset=gold", "body": None, "nfr": "p95 ≤ 800ms"},
    {"name": "POST /forecast/silver", "method": "GET", "path": "/api/predictions/latest?asset=silver", "body": None, "nfr": "p95 ≤ 800ms"},
    {"name": "GET /chart/gold (1-year)", "method": "GET", "path": "/api/predictions/history?days=365&asset=gold", "body": None, "nfr": "p95 ≤ 300ms"},
    {"name": "GET /shap/global", "method": "GET", "path": "/api/shap/feature-importance?asset=gold", "body": None, "nfr": None},
    {"name": "POST /backtest (3-year)", "method": "POST", "path": "/api/backtest/run",
     "body": {"asset": "gold", "start_date": "2023-01-01", "end_date": "2026-01-01", "strategy": "SMC_FORGE_V1", "initial_capital": 10000}, "nfr": "p95 ≤ 5000ms"},
    {"name": "GET /api/orchestrator/status", "method": "GET", "path": "/api/orchestrator/status", "body": None, "nfr": None},
    {"name": "GET /api/market/price", "method": "GET", "path": "/api/market/price?asset=gold", "body": None, "nfr": None},
    {"name": "GET /api/pipeline/status", "method": "GET", "path": "/api/pipeline/status", "body": None, "nfr": None},
]


def measure(endpoint: dict) -> dict:
    """Run N_SAMPLES requests and compute latency percentiles."""
    latencies = []
    errors = []
    token = None

    # Get auth token if login endpoint
    if "login" in endpoint["path"]:
        try:
            r = requests.post(f"{BASE_URL}/api/auth/register",
                              json={"email": "benchmark@test.com", "password": "Bench123!x"},
                              timeout=TIMEOUT)
        except Exception:
            pass  # user may already exist

        try:
            r = requests.post(f"{BASE_URL}/api/auth/login",
                              json=endpoint["body"], timeout=TIMEOUT)
            if r.status_code == 200:
                token = r.json().get("token", "")
        except Exception:
            pass

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # Warmup
    for _ in range(N_WARMUP):
        try:
            if endpoint["method"] == "GET":
                requests.get(f"{BASE_URL}{endpoint['path']}", headers=headers, timeout=TIMEOUT)
            else:
                requests.post(f"{BASE_URL}{endpoint['path']}", json=endpoint["body"], headers=headers, timeout=TIMEOUT)
        except Exception:
            pass

    # Measure
    for _ in range(N_SAMPLES):
        try:
            start = time.perf_counter()
            if endpoint["method"] == "GET":
                r = requests.get(f"{BASE_URL}{endpoint['path']}", headers=headers, timeout=TIMEOUT)
            else:
                r = requests.post(f"{BASE_URL}{endpoint['path']}", json=endpoint["body"], headers=headers, timeout=TIMEOUT)
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)
            if r.status_code >= 500:
                errors.append(f"HTTP {r.status_code}")
        except Exception as e:
            errors.append(str(e)[:80])

    if not latencies:
        return {"name": endpoint["name"], "error": "All requests failed", "errors": errors}

    sorted_lat = sorted(latencies)
    n = len(sorted_lat)

    def percentile(p):
        idx = int(n * p / 100)
        return round(sorted_lat[min(idx, n - 1)], 1)

    return {
        "name": endpoint["name"],
        "samples": n,
        "errors": len(errors),
        "error_details": errors[:3] if errors else [],
        "p50_ms": percentile(50),
        "p95_ms": percentile(95),
        "p99_ms": percentile(99),
        "min_ms": round(min(latencies), 1),
        "max_ms": round(max(latencies), 1),
        "mean_ms": round(statistics.mean(latencies), 1),
        "stdev_ms": round(statistics.stdev(latencies), 1) if n > 1 else 0,
        "nfr_target": endpoint.get("nfr"),
        "nfr_pass": None,  # computed below
    }


def main():
    print("=" * 60)
    print("MetalMind SMCForge — API Performance Benchmark")
    print(f"Base URL: {BASE_URL}")
    print(f"Samples per endpoint: {N_SAMPLES} (warmup: {N_WARMUP})")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Health check first
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if r.status_code != 200:
            print(f"\n❌ API not healthy (HTTP {r.status_code}). Aborting.")
            sys.exit(1)
        print(f"\n✅ API healthy — {r.json().get('status', 'unknown')}")
    except Exception as e:
        print(f"\n❌ Cannot reach API at {BASE_URL}: {e}")
        print("Start the API first: docker compose up -d api")
        sys.exit(1)

    results = []
    for i, ep in enumerate(ENDPOINTS):
        print(f"\n[{i+1}/{len(ENDPOINTS)}] {ep['name']} ...", end=" ", flush=True)
        result = measure(ep)
        results.append(result)

        if "error" in result:
            print(f"❌ {result['error']}")
        elif result["errors"] > 0:
            print(f"⚠️  {result['samples']} samples, {result['errors']} errors, p95={result['p95_ms']}ms")
        else:
            # NFR check
            if result.get("nfr_target") and result["p95_ms"]:
                target_ms = None
                target_str = result["nfr_target"]
                if "800" in target_str:
                    target_ms = 800
                elif "300" in target_str:
                    target_ms = 300
                elif "5000" in target_str:
                    target_ms = 5000
                if target_ms:
                    result["nfr_pass"] = result["p95_ms"] <= target_ms
            status = "✅" if result.get("nfr_pass") is None or result["nfr_pass"] else "❌"
            print(f"{status} {result['samples']} samples, p50={result['p50_ms']}ms, p95={result['p95_ms']}ms, p99={result['p99_ms']}ms")

    # Summary table
    print("\n" + "=" * 90)
    print("PERFORMANCE TEST RESULTS")
    print("=" * 90)
    print(f"{'Endpoint':<35} {'p50(ms)':>8} {'p95(ms)':>8} {'p99(ms)':>8} {'NFR Target':>16} {'Status':>10}")
    print("-" * 90)

    nfr_pass = 0
    nfr_total = 0
    for r in results:
        nfr = r.get("nfr_target", "No target") if r.get("nfr_target") else "No target"
        if r.get("nfr_pass") is not None:
            nfr_total += 1
            if r["nfr_pass"]:
                nfr_pass += 1
                status = "PASS"
            else:
                status = "FAIL"
        elif "error" in r:
            status = "ERROR"
            nfr = "—"
        else:
            status = "Acceptable" if r.get("p50_ms", 0) < 500 else "Slow"

        name = r["name"][:34]
        print(f"{name:<35} {r.get('p50_ms', '—'):>8} {r.get('p95_ms', '—'):>8} {r.get('p99_ms', '—'):>8} {nfr:>16} {status:>10}")

    print("-" * 90)
    if nfr_total > 0:
        print(f"NFR Pass Rate: {nfr_pass}/{nfr_total} ({100*nfr_pass//nfr_total}%)")
    print(f"Total endpoints tested: {len(results)}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # Write report
    report = {
        "benchmark": "MetalMind SMCForge API Performance",
        "base_url": BASE_URL,
        "samples_per_endpoint": N_SAMPLES,
        "warmup_samples": N_WARMUP,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nfr_pass_count": nfr_pass,
        "nfr_total_count": nfr_total,
        "results": results,
    }

    out_path = Path(__file__).parent.parent / "reports" / "performance_benchmark.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 Report written to: {out_path}")


if __name__ == "__main__":
    main()
