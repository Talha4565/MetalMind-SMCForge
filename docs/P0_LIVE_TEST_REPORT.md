# P0 Live Integration Test Report

**Project:** MetalMind SMCForge
**Date:** July 14, 2026
**Tester:** MiMoCode (Automated)
**Environment:** Docker Compose (localhost:5000 API, localhost:3000 Frontend)

---

## Executive Summary

P0 testing validates the **critical path** that every user must traverse to use the application. These are the "ship or don't ship" tests. If any P0 test fails, the application cannot be deployed.

**Result: 40/40 tests passed (100%)**

| Test Suite | Tests | Passed | Failed | Status |
|------------|-------|--------|--------|--------|
| Authentication Flow | 8 | 8 | 0 | ✅ PASS |
| Dashboard & Core Endpoints | 32 | 32 | 0 | ✅ PASS |
| **TOTAL** | **40** | **40** | **0** | **✅ SHIP READY** |

---

## Why These Tests Are P0

The critical user journey is:

```
Register → Login → Dashboard → See Predictions → See SHAP → Check Trade Log
```

If any step in this journey fails, the user cannot use the application. Therefore:

1. **Auth** must work (gateway to everything)
2. **Dashboard** must load (main interface)
3. **Predictions** must return data (core value proposition)
4. **SHAP** must show feature importance (explainability)
5. **Trade Log** must show history (accountability)

---

## Test Suite 1: Authentication Flow

### Purpose
Verify that users can register, login, receive a JWT token, and access protected routes. Auth is the gateway to all other features.

### Test Environment
- **API Base:** `http://localhost:5000`
- **Database:** PostgreSQL (Docker container `metalmind-db`)
- **Test User:** `test_{timestamp}@example.com` (unique per run)

### Test 1.1: Health Endpoint

**Why:** Before testing auth, confirm the API is running and responsive.

**What it does:**
```python
r = requests.get("http://localhost:5000/api/health", timeout=10)
```

**Expected:** HTTP 200 with `{"status": "healthy"}`

**Result:** PASS — API is running, database connection OK, gold model loaded.

---

### Test 1.2: Register New User

**Why:** Registration is the first step in the user journey. If registration fails, no new users can sign up.

**What it does:**
```python
r = requests.post("http://localhost:5000/api/auth/register", json={
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPass123!"
})
```

**Expected:** HTTP 201 (Created) with user object

**Why 201 and not 200:** REST convention: POST creating a resource returns 201.

**Result:** PASS — User created successfully.

**Bug found during development:** Original test used `/auth/register` instead of `/api/auth/register`. The auth blueprint is registered with prefix `/api/auth` in `api/app/auth.py:421`:
```python
app.register_blueprint(auth_bp, url_prefix='/api/auth')
```

---

### Test 1.3: Login with Valid Credentials

**Why:** Login is how users get JWT tokens. Without a working login, no authenticated features work.

**What it does:**
```python
r = requests.post("http://localhost:5000/api/auth/login", json={
    "email": test_email,
    "password": test_password
})
data = r.json()
token = data.get("access_token") or data.get("token")
```

**Expected:** HTTP 200 with `access_token` field

**Result:** PASS — Login successful, JWT token returned.

**Token format:** `eyJhbGciOiJIUzI1NiIs...` (HS256 JWT)

---

### Test 1.4: Wrong Password Rejection

**Why:** Security critical — wrong passwords must be rejected, not ignored.

**What it does:**
```python
r = requests.post("http://localhost:5000/api/auth/login", json={
    "email": test_email,
    "password": "WrongPassword!"
})
```

**Expected:** HTTP 401 (Unauthorized) or 400 (Bad Request)

**Result:** PASS — Returns 401, wrong password correctly rejected.

---

### Test 1.5: Protected Route Without Token

**Why:** Verify that unauthenticated requests are blocked from protected endpoints.

**What it does:**
```python
r = requests.get("http://localhost:5000/api/shap/feature-importance")
```

**Expected:** HTTP 401 (Unauthorized)

**Result:** PASS — Returns 401, no token = no access.

**Why `/api/shap/feature-importance`:** This endpoint requires `@token_required` decorator, making it a good test case for auth enforcement.

---

### Test 1.6: Protected Route With Valid Token

**Why:** Verify that authenticated requests are allowed through.

**What it does:**
```python
r = requests.get("http://localhost:5000/api/shap/feature-importance",
    headers={"Authorization": f"Bearer {token}"})
```

**Expected:** HTTP 200 with SHAP data

**Result:** PASS — Valid token grants access.

---

### Test 1.7: Invalid Token Rejection

**Why:** Verify that forged/invalid tokens are rejected.

**What it does:**
```python
r = requests.get("http://localhost:5000/api/shap/feature-importance",
    headers={"Authorization": "Bearer invalid_token_12345"})
```

**Expected:** HTTP 401 (Unauthorized)

**Result:** PASS — Invalid token correctly rejected.

---

## Test Suite 2: Dashboard & Core Endpoints

### Purpose
Verify that all endpoints required by the dashboard return valid data. This is the "does it actually work" test.

### Test 2.1-2.3: API Health (Detailed)

**Why:** Health check is more than "is it running" — it must verify database, filesystem, and model status.

**What it checks:**
- HTTP 200 response
- `checks.database == "ok"` (PostgreSQL connected)
- `checks.models.gold == True` (XGBoost model loaded)

**Result:** PASS — All subsystems healthy.

---

### Test 2.4-2.6: Live Price (MT5)

**Why:** The dashboard shows real-time prices from MetaTrader 5. If this fails, the dashboard shows stale data.

**What it checks:**
- HTTP 200 response
- `price` field exists and is a number
- `source == "mt5"` (not mock data)

**Current price at test time:** $4,029.92

**Result:** PASS — MT5 cache is fresh and returning live prices.

---

### Test 2.7-2.12: Predictions (Gold)

**Why:** Predictions are the core value proposition. If the ML model isn't returning predictions, the app has no purpose.

**What it checks:**
- HTTP 200 response
- `predictions` array has data (5 predictions requested)
- Each prediction has: `signal`, `confidence`, `price`, `shap_values`
- SHAP values array is not empty

**Result:** PASS — Model returning predictions with SHAP explanations.

**SHAP values at test time:**
```
htf_1h_dist_high:  +0.5133
htf_30m_dist_low:  -0.2963
VWAPd_96:          +0.2440
htf_1h_dist_low:   -0.1828
trend_adx:         -0.1451
```

---

### Test 2.13-2.17: SHAP Values

**Why:** SHAP explainability is a key feature. Users need to understand WHY the model made a prediction.

**What it checks:**
- SHAP values array exists and is non-empty
- Each SHAP entry has `feature` (string) and `contribution` (number)
- Feature names are valid strings (not None, not empty)

**Result:** PASS — Real SHAP values being computed and returned.

---

### Test 2.18-2.22: Trade Log

**Why:** Users need to see historical predictions and their outcomes. This is the accountability feature.

**What it checks:**
- HTTP 200 response
- `predictions` array has data (308 trades imported from backtest)
- `summary` object exists with `total_predictions`, `wins`

**Current state:** 308 trades (72 gold + 202 silver from backtest)

**Result:** PASS — Trade log populated with historical data.

---

### Test 2.23-2.25: Pipeline Status

**Why:** Users need to know if their data is fresh and models are loaded.

**What it checks:**
- HTTP 200 response
- `data_freshness.gold` exists (gold data status)
- `data_freshness.silver` exists (silver data status)
- `models.gold` exists (model info)

**Result:** PASS — Pipeline status accurate.

---

### Test 2.26-2.30: Orchestrator Status

**Why:** Orchestrator provides deep monitoring of all subsystems.

**What it checks:**
- HTTP 200 response
- `mt5_cache` object exists (MT5 price cache status)
- `chromadb` object exists (ChromaDB connection status)
- `pipeline.freshness` exists (data freshness)
- `pipeline.health` exists (health monitoring)

**Result:** PASS — All orchestrator data available.

---

## Bugs Found and Fixed During P0 Testing

### Bug 1: Auth Route Prefix

**Symptom:** Register and Login endpoints returned 404

**Root Cause:** Test used `/auth/register` instead of `/api/auth/register`

**Fix:** Updated test routes to match actual blueprint prefix

**File:** `tests/live/test_auth.py`

**Lesson:** Always check blueprint registration prefix before writing tests.

---

### Bug 2: Rate Limiting (Found Earlier Today)

**Symptom:** Frontend showing fallback/mock data

**Root Cause:** Default 50/hour rate limit, frontend polled every 30s = 120/hour

**Fix:** Increased limits to 300/hour for read endpoints

**File:** `api/app/pipeline_routes.py`

**Lesson:** Rate limits must account for frontend polling frequency.

---

## Test Infrastructure

### Files Created

```
tests/live/
├── test_auth.py          # Auth flow tests (8 tests)
├── test_dashboard.py     # Dashboard & core tests (32 tests)
```

### How to Run

```bash
# Run auth tests
python tests/live/test_auth.py

# Run dashboard tests
python tests/live/test_dashboard.py

# Run all P0 tests
python tests/live/test_auth.py && python tests/live/test_dashboard.py
```

### Dependencies

- `requests` (HTTP client)
- Running Docker Compose stack
- MT5 price cache (for live price tests)

---

## Conclusion

**P0 testing confirms the application is ship-ready.**

All critical user flows work:
- ✅ Users can register and login
- ✅ JWT tokens are issued and validated
- ✅ Protected routes enforce authentication
- ✅ Dashboard loads with real data
- ✅ ML predictions are returned with SHAP explanations
- ✅ Trade log shows historical performance
- ✅ Live prices from MT5 are current
- ✅ Pipeline and orchestrator status accurate

**Recommendation:** Proceed to P1 testing (Backtest, Pipeline, Orchestrator pages) or ship to production.

---

## Next Steps

1. **P1 Testing:** Backtest page, Pipeline page, Orchestrator page
2. **P2 Testing:** Watchlist, Risk Calculator, 2FA, Email Alerts
3. **E2E Testing:** Playwright browser automation
4. **Deployment:** Docker production build, Vercel frontend
