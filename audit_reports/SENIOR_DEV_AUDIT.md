# 🔴 Senior Developer Audit — MetalMind SMCForge

**Auditor:** Senior SWE Review  
**Date:** 2026-06-20  
**Scope:** Scaling readiness, development readiness, FYP defensibility  
**Verdict:** **NOT production-ready** — 4 critical, 11 major, 8 minor findings

---

## Table of Contents

1. [Critical Findings (Must Fix Before Any Defense)](#1-critical-findings)
2. [Major Findings (Architectural / Security Weaknesses)](#2-major-findings)
3. [Minor Findings (Code Quality / Maintainability)](#3-minor-findings)
4. [What's Done Well](#4-whats-done-well)
5. [FYP-Specific Recommendations](#5-fyp-specific-recommendations)
6. [Priority Action Matrix](#6-priority-action-matrix)

---

## 1. Critical Findings

### 🔴 C1 — Password Hashes and User Data Committed to Git

**Severity:** CRITICAL — Immediate credential leak  
**Location:** `instance/metalmind_smc.db`, `api/instance/metalmind_smc.db` (tracked in git)  
**Evidence:**
```
git ls-files "*.db" → instance/metalmind_smc.db, api/instance/metalmind_smc.db, metalmind_smc.db
```
The committed databases contain **9 real user rows** with bcrypt password hashes, TOTP secrets, emails (`talhaqamar102@gmail.com`, `bamoxab103@noihse.com`), session IPs, and OTP codes. Even though `.gitignore` lists `*.db` later, these files were `git add`-f'd before the gitignore rule and remain tracked.

**Impact:** Anyone who clones the repo gets real password hashes. bcrypt makes cracking slow but not impossible. TOTP secrets + emails = full account takeover if email is compromised.

**Fix:**
1. `git rm --cached instance/metalmind_smc.db api/instance/metalmind_smc.db metalmind_smc.db`
2. Add to `.gitignore` with a `!.gitkeep` pattern for the directory
3. **Rewrite git history** with `git filter-branch` or BFG to remove all DB blobs
4. **Rotate all credentials** — every password in those hashes must be changed
5. Regenerate TOTP secrets for all affected users

---

### 🔴 C2 — Resend API Key Exposed on Disk

**Severity:** CRITICAL  
**Location:** `.env` (line 20)  
**Evidence:** `RESEND_API_KEY=re_hKr1Cdpi_Q3d8V89WPoidSQXB2rxvULKj`

The `.env` itself is correctly gitignored and NOT tracked. However:
- The key is a **real, active API key** sitting on disk with no encryption
- If this machine is ever compromised or shared, the key leaks
- The key is mounted directly into Docker containers via `env_file: .env`
- No `.env` validation checks that secrets have been changed from defaults

**Fix:** Rotate the Resend key immediately. Add a startup check that rejects known-compromised keys.

---

### 🔴 C3 — Hardcoded "Insight" Text in Dashboard

**Severity:** CRITICAL for FYP — This is a static placeholder pretending to be AI-generated analysis  
**Location:** `frontend-next/src/app/dashboard/page.tsx:163-165`

```tsx
<p className="text-sm text-muted-foreground leading-relaxed">
  Order flow suggests a liquidity grab below recent lows.
  Watch for displacement higher before committing to longs.
</p>
```

This is **hardcoded English text** — not generated from model output, SHAP values, or any data pipeline. If a reviewer clicks around the dashboard, they will see this text *never changes* regardless of asset, signal, or time. An FYP defense committee will catch this immediately.

**Fix:** Either:
- Remove the "Insight" card entirely, OR
- Generate it dynamically from the top SHAP features of the current prediction

---

### 🔴 C4 — Test Collection Takes 3+ Minutes (Unacceptable for CI)

**Severity:** CRITICAL  
**Evidence:** `pytest --co -q` collected 252 tests in **203 seconds** (3:23)

Test collection alone takes over 3 minutes because nearly every test module imports the full ML pipeline (`features.pipeline`, `data.loaders`, `shap`, `xgboost`, `optuna`) at module level. The actual `thorough-check` report couldn't even run coverage because the process was too slow.

**Impact:** CI pipeline will timeout or be unbearably slow. No developer will run tests locally.

**Fix:**
1. Move all heavy imports inside test functions or `@pytest.fixture`
2. Mock `load_asset_data()` and `engineer_all_features()` in unit tests — they load multi-MB CSVs
3. Use `conftest.py`-level session-scoped fixtures for shared data
4. Target: collection < 5 seconds

---

## 2. Major Findings

### 🟠 M1 — `unsafe-inline` and `unsafe-eval` in CSP (XSS Vector)

**Location:** `api/app/main.py:153-154`  
```python
"script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com ..."
```
The Content Security Policy allows `unsafe-inline` and `unsafe-eval` for scripts. This completely defeats XSS protection. A single injected `<script>` anywhere in the DOM will execute.

**Fix:** Use nonce-based CSP or hash-based CSP. Move Tailwind to build-time (it's already in Next.js — the CDN reference is redundant).

---

### 🟠 M2 — `unsafe-eval` Required by TradingView Widget (Architectural Trap)

**Location:** `frontend-next/src/components/Charts/TradingViewChart.tsx`

The TradingView embed uses `new Function()` internally, which requires `unsafe-eval`. You cannot have both real CSP and TradingView. This is a known architectural tradeoff.

**Fix:** Use `sandbox` attribute on the TradingView iframe to isolate it, then remove `unsafe-eval` from the main page CSP. Alternatively, use lightweight-charts (already in `package.json`) for the live chart and keep TradingView only in a sandboxed iframe.

---

### 🟠 M3 — 11 NPM Vulnerabilities (3 High, 7 Moderate, 1 Low)

**Evidence:** `npm audit` output
- **`hono`** — 8 CVEs including IP restriction bypass, path traversal on Windows, CORS reflection with credentials
- **`ws`** — uninitialized memory disclosure, memory exhaustion DoS
- **`form-data`** — CRLF injection
- **`@babel/core`** — arbitrary file read via sourcemap
- **`js-yaml`** — quadratic-complexity DoS
- **`postcss`** — XSS via unescaped `</style>` (requires `npm audit fix --force` which downgrades Next.js)

**Fix:** Run `npm audit fix`. For the postcss issue, pin to Next.js ≥ 16.3.1-canary.6 when available.

---

### 🟠 M4 — Flask-Bcrypt AND Werkzeug Bcrypt Duplication

**Location:** `api/requirements.txt`
```
bcrypt>=4.1.2
flask-bcrypt==1.0.1
```
`flask-bcrypt==1.0.1` depends on an older `bcrypt` and is effectively deprecated. You're importing both `flask_bcrypt.Bcrypt` (in `extensions.py`) and `bcrypt` directly. The `password_service.py` likely uses one or the other.

**Fix:** Drop `flask-bcrypt`. Use `bcrypt` directly (it's already imported). This removes an unmaintained dependency.

---

### 🟠 M5 — No Rate Limit Storage Backend (Memory-Only)

**Location:** `api/app/extensions.py:17`
```python
storage_uri="memory://"
```
Rate limits are stored in-memory. This means:
- Every Gunicorn worker has its own rate limit counter
- Rate limits are trivially bypassed with multiple workers
- Limits reset on every container restart

**Fix:** Use Redis (`storage_uri="redis://redis:6379"`) for distributed rate limiting, or at minimum use Memcached.

---

### 🟠 M6 — `datetime.utcnow()` Deprecated — Python 3.12+ Breaking Change Path

**Location:** Used in ~30 places across `auth.py`, `database.py`, `main.py`, `shap_cache.py`  
`datetime.utcnow()` is deprecated since Python 3.12 and will be removed in a future version. Your Dockerfile uses Python 3.11, but this is a migration debt.

**Fix:** Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)` (which you already use inconsistently in some places).

---

### 🟠 M7 — Backtesting Engine: Only Long Trades (Direction Mismatch)

**Location:** `backtesting/engine.py:75`
```python
if signal == 0:
    return None  # signal==0 means "no trade", never "short"
```

The `Trade` dataclass has a `direction` field (`'long'` or `'short'`), and the model output is binary (0/1). But the engine only simulates long trades. A signal=0 means "hold", never "go short". The `direction` field is always hardcoded to `'long'` — it's dead code that suggests incomplete functionality.

For FYP: If you claim the system generates BUY/SELL signals, the backtester must simulate both.

**Fix:** Either remove the `direction` field and clarify signal=1 means BUY-only, or implement short simulation.

---

### 🟠 M8 — Label Generation Uses Close-Only (Ignores High/Low for TP/SL Hit Detection)

**Location:** `features/labels.py:49`
```python
future_price = close[i + k]
```

Labels check if the **close price** hits TP/SL within max_bars. But in reality, price can hit TP/SL intra-bar on the high or low, then close back. The backtester (`engine.py:96-104`) correctly uses high/low for TP/SL detection, but the labels don't. This creates an inconsistency between training labels and backtest evaluation.

**Impact:** Labels are less accurate than the backtester assumes — the model learns from a flawed signal.

**Fix:** Use `high[i+k]` and `low[i+k]` for TP/SL detection in labels (matching the backtester logic).

---

### 🟠 M9 — `pickle.load()` on Untrusted Paths (RCE Vector)

**Location:** `api/app/main.py:230`, `models/retrain.py:72`, multiple locations

```python
with open(model_path, 'rb') as f:
    model_data = pickle.load(f)
```

Pickle deserialization of untrusted files is an RCE vector. While model files are currently only loaded from `models/`, the CI workflow commits retrained models to git. A compromised CI runner could inject a malicious pickle.

**Fix:** Use `joblib.load()` or `sklearn`'s safe loader. At minimum, verify pickle file hashes before loading.

---

### 🟠 M10 — Docker Compose Uses Hardcoded PostgreSQL Credentials

**Location:** `docker-compose.yml:53-54`
```yaml
POSTGRES_USER: postgres
POSTGRES_PASSWORD: postgres
```

The production database password is `postgres` in the compose file. Even with `.env` override, anyone who runs `docker compose up` without setting env vars gets a default-password database exposed on port 5432.

**Fix:** Use `${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}` syntax to enforce env var usage.

---

### 🟠 M11 — No Database Migrations Run in Production Docker Mode

**Location:** `api/app/database.py:246-267`

The `init_database()` function skips `create_all()` in production mode and says "use migrations." But the Dockerfile's `CMD` runs gunicorn directly — migrations only run if the `docker-compose.yml` `command` override is used. The `api/Dockerfile` default ENTRYPOINT (`docker-entrypoint.sh`) runs migrations, but `docker-compose.yml` overrides both ENTRYPOINT and CMD.

This means: the default `api/Dockerfile` is correct, but `docker-compose.yml` **bypasses it** with its own `command:`. If someone builds the Docker image without compose, migrations are handled. With compose, they're handled by the `sh -c "flask db upgrade..."` fallback. This is fragile.

---

## 3. Minor Findings

### 🟡 m1 — Duplicate `import threading` and `import time` in `main.py`

**Location:** `api/app/main.py:23,26` — `threading` imported twice; `time` imported but only used in the background thread function.

---

### 🟡 m2 — Bare `except:` Clause Swallows Errors

**Location:** `api/app/main.py:241-242`
```python
except:
    feature_names = None
```
This catches `KeyboardInterrupt`, `SystemExit`, and every other exception silently.

**Fix:** `except (AttributeError, KeyError): feature_names = None`

---

### 🟡 m3 — `return None` Used After `for...else` Without `break`

**Location:** `backtesting/engine.py:148`
```python
for k in range(1, self.max_bars + 1):
    ...
else:
    ...  # timeout exit
    return Trade(...)
return None  # UNREACHABLE — the `else` clause always returns
```
Line 169 `return None` is dead code because the `else` clause on the for loop always returns a Trade object.

---

### 🟡 m4 — Sharpe Ratio Printed Twice in `print_summary()`

**Location:** `backtesting/engine.py:335,388` — Both print `"Sharpe Ratio: {sharpe:.2f}"`.

---

### 🟡 m5 — `main.py` is 1,297 Lines — God File

**Location:** `api/app/main.py` contains: Flask app setup, CORS proxy class, 4 manager classes (ModelManager, PredictionCache, FileCache, BacktestManager), 12+ route handlers, WebSocket handlers, and background thread logic.

This should be split into at least: `app/__init__.py` (factory), `routes/predictions.py`, `routes/backtest.py`, `routes/shap.py`, `managers/model.py`, etc.

---

### 🟡 m6 — No `package-lock.json` Integrity Check

The `package-lock.json` exists but no lockfile verification is done in CI. `npm ci` should be used instead of `npm install` in Docker builds.

---

### 🟡 m7 — ETL Orchestrator Health Alert Uses Raw SMTP (Not Resend)

**Location:** `etl/orchestrator.py:225-238`

The health monitor has its own raw SMTP implementation instead of using the `EmailService` (which uses Resend). This is a second, untested email path.

---

### 🟡 m8 — Dashboard Claims "89 features" Hardcoded

**Location:** `frontend-next/src/app/dashboard/page.tsx:131`
```tsx
<p>Model: XGBoost · 89 features</p>
```
This is a magic number. If you retrain with different features, this lies.

---

## 4. What's Done Well

| Area | Assessment |
|---|---|
| **Architecture (high-level)** | Clean separation: `etl/`, `features/`, `models/`, `backtesting/`, `api/`, `frontend-next/`. ETL factory pattern with extractors/transformers/loaders is textbook. |
| **Auth system** | JWT + refresh tokens + 2FA + OTP email verification. Token refresh interceptor in the frontend is well-implemented with queue-based dedup. httpOnly cookies for refresh tokens. |
| **Security middleware** | CSP headers, X-Frame-Options, HSTS, Referrer-Policy, Permissions-Policy, ProxyFix — all present. Error handler middleware catches 404/405/unexpected. |
| **Feature engineering pipeline** | Volume + SMC + multi-timeframe with proper separation. Labels use triple-barrier method (conceptually correct, needs high/low fix). |
| **Model versioning** | Backup before retrain, rollback on failure, keep-only-5 cleanup — production-quality orchestration. |
| **Docker setup** | Non-root user in API container, resource limits, health checks, named volumes. Multi-service compose with proper `depends_on` + `condition: service_healthy`. |
| **CI/CD pipeline** | Automated data updates every 15min + daily retrain via GitHub Actions. Data freshness checking. |
| **Test structure** | Unit/integration/smoke separation. 252 tests across 17 files with proper conftest fixtures. |
| **Rate limiting** | Per-endpoint limits on all API routes. Flask-Limiter properly configured. |
| **Thread safety** | `ModelManager`, `PredictionCache`, `BacktestManager` all use `threading.Lock()`. |
| **Database pooling** | `pool_pre_ping`, `pool_recycle`, `pool_size=20`, `max_overflow=10` — well-tuned for production. |

---

## 5. FYP-Specific Recommendations

### For Defense Readiness

1. **Remove the hardcoded "Insight" card** (C3) or make it dynamic. A reviewer *will* ask "how is this generated?"

2. **Prepare a reproducibility script**: `python run.py --mode full --asset gold` should be a single command that fetches data, engineers features, trains, evaluates, and produces a report. Currently `run.py`, `run_pipeline.py`, and `run_etl.py` overlap.

3. **Fix the label/backtest inconsistency** (M8). If asked "how do you know the labels are correct?", the current close-only labels won't survive scrutiny against the high/low-based backtester.

4. **Clarify signal semantics**: Is signal=1 "BUY" or "TRADE"? The frontend shows BUY/SELL/HOLD but the model only outputs 0/1. A defense committee will notice this gap immediately.

5. **Add a results summary page or export** that shows: model accuracy, AUC, Sharpe, max drawdown, total trades, win rate — all auto-generated. The current dashboard only shows "latest signal + confidence."

6. **Document the feature list**: 89 features claimed but no single document lists them all with descriptions. Add a `docs/features.md`.

### For Scaling Readiness

7. **Replace in-memory rate limiting with Redis** (M5) before any multi-worker deployment.

8. **Split `main.py`** (m5) — a 1,300-line Flask file won't scale with team size.

9. **Add API versioning**: All routes are `/api/...` with no version prefix. Use `/api/v1/...` from day one.

10. **Add proper logging**: Currently `logging.basicConfig(level=logging.INFO)` in multiple files. Use a single config in `config/settings.py` and `dictConfig`.

---

## 6. Priority Action Matrix

| # | Finding | Severity | Effort | Action |
|---|---------|----------|--------|--------|
| C1 | DB files with password hashes in git | 🔴 CRITICAL | Medium | `git rm --cached`, rewrite history, rotate creds |
| C2 | Resend API key on disk | 🔴 CRITICAL | Low | Rotate key, add startup validation |
| C3 | Hardcoded "Insight" text | 🔴 CRITICAL | Low | Remove or make dynamic from SHAP |
| C4 | Test collection 3+ min | 🔴 CRITICAL | High | Lazy imports, mock heavy deps in unit tests |
| M1 | `unsafe-inline` + `unsafe-eval` in CSP | 🟠 MAJOR | Medium | Nonce-based CSP, sandbox TradingView |
| M3 | 11 npm vulnerabilities | 🟠 MAJOR | Low | `npm audit fix` |
| M4 | Duplicate bcrypt packages | 🟠 MAJOR | Low | Drop flask-bcrypt |
| M5 | In-memory rate limiting | 🟠 MAJOR | Medium | Add Redis to compose |
| M8 | Label generation uses close-only | 🟠 MAJOR | Medium | Use high/low in labels.py |
| M9 | pickle.load on model files | 🟠 MAJOR | Medium | Switch to joblib or add hash verification |
| M10 | Hardcoded DB password in compose | 🟠 MAJOR | Low | Use `${VAR:?error}` syntax |
| M6 | Deprecated `datetime.utcnow()` | 🟠 MAJOR | Medium | Bulk replace with `datetime.now(tz=timezone.utc)` |
| M7 | Backtest: long-only, dead direction field | 🟠 MAJOR | Low | Remove direction or implement shorts |
| M1 | Docker bypasses entrypoint | 🟠 MAJOR | Low | Align compose command with Dockerfile intent |
| m5 | main.py is 1,300 lines | 🟡 MINOR | High | Split into routes/managers modules |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Critical findings | 4 |
| Major findings | 11 |
| Minor findings | 8 |
| Total findings | 23 |
| Python files audited | ~50 |
| Frontend files audited | ~55 |
| Test files reviewed | 17 (252 tests) |
| Lines of backend code reviewed | ~4,500 |
| Lines of frontend code reviewed | ~3,200 |

**Bottom line:** The architecture is solid and shows real engineering maturity. The CI/CD pipeline, auth system, feature engineering, and Docker setup are well above average for an FYP. However, the 4 critical issues (committed credentials, hardcoded insight text, test performance) are **defense-stoppers** and must be fixed before any presentation. The label/backtest inconsistency (M8) is the most academically dangerous finding — it undermines the validity of your reported results.
