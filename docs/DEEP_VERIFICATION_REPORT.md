# MetalMind SMCForge — Deep Codebase Verification Report

**Date:** July 2, 2026  
**Method:** Actual test execution, import verification, dependency checking — no file-counting or surface analysis.

---

## Test Results (Live Execution)

### Unit Tests: 197 passed, 7 failed, 6 warnings

The 7 failures are ALL in `tests/unit/test_volume_features.py`. The tests check for old column names that no longer exist after the feature pipeline was refactored to use multi-window naming:

| Test | Looking For | Actual Column | Root Cause |
|------|------------|---------------|------------|
| `test_cvd_columns_added` | `cvd` | `CVD_4`, `CVD_16`, `CVD_96` | Test uses old single-column name |
| `test_cvd_is_numeric` | `cvd` | `CVD_4` etc. | Same stale reference |
| `test_imbalance_columns_added` | `volume_imbalance` | `Imbal_4`, `Imbal_16`, `Imbal_96` | Test uses old name |
| `test_imbalance_range` | `volume_imbalance` | `Imbal_4` etc. | Same |
| `test_wick_columns_added` | `upper_wick_ratio` | `Wick_4`, `Wick_16`, `Wick_96` | Test uses old name |
| `test_returns_columns` | `return_1` | `Ret_4`, `Ret_16`, `Ret_96` | Test uses old name |
| `test_session_flags_added` | `is_london` | `session_london` | Test uses old name |

**Assessment:** The code works correctly. The tests are stale — they were written before the multi-window refactor and never updated. This is a test maintenance issue, not a code bug. The feature pipeline produces valid columns with the new naming scheme.

### Integration Tests: 14 errors, 0 passes — COMPLETELY BROKEN

Every single integration test fails at setup. Two separate root causes:

**Root Cause 1 — Missing `etl_pipeline` fixture (8 tests):**  
`tests/integration/test_etl_pipeline.py` uses `def test_successful_pipeline(self, etl_pipeline):` but there is no `conftest.py` in `tests/integration/` defining the `etl_pipeline` fixture. The fixture was never created.

**Root Cause 2 — Missing `engineer_all_features`, `xgb`, `backtest_engine` fixtures (6 tests):**  
`tests/integration/test_feature_model_pipeline.py` defines `engineered_data` fixture that depends on `engineer_all_features`, but that fixture is defined in `tests/unit/conftest.py` which is not visible to the integration directory. Same chain for `xgb` and `backtest_engine`.

**Assessment:** The integration tests were written but their fixture setup was never completed. The tests themselves are correct — they just can't run because the conftest plumbing is missing. This means the ETL pipeline, feature-to-model pipeline, and backtest integration are NOT covered by automated tests.

### Smoke Tests: 27 passed, 1 error

The 1 error is `tests/smoke/test_e2e_app.py::test` — this is NOT a real pytest test. It's a script that defines `def test(name, passed, detail='')` as a helper function. Pytest collects it because of the `test_` prefix, then fails because it tries to inject `name` as a fixture. The script is designed to run standalone (`python test_e2e_app.py`) against a live server, not via pytest.

**Assessment:** The actual smoke tests (test_smoke.py) all pass. The e2e script needs to be excluded from pytest collection or renamed.

---

## Flask App Startup

```
CRITICAL:root:SECRET VALIDATION FAILED — refusing to start:
  SECRET_KEY is set to a placeholder — generate a real value
```

The Flask app refuses to start because `.env` has placeholder secrets. This is INTENTIONAL — the `_validate_secrets()` function in `api/app/main.py` rejects startup with placeholder values. This is a security feature, not a bug.

**What this means for demo:** You need to set real secrets in `.env` before running. If you're using Docker, the secrets should be in the Docker environment.

---

## Module Import Verification

All core modules import successfully:
- `api.app.main` — imports (but crashes on secret validation, not import error)
- `features.pipeline` — OK
- `self_learning.tracker` — OK
- `signal_memory.client` — OK
- `etl.pipeline` — OK
- `backtesting.engine` — OK
- `explainability.shap_analyzer` — OK

No ImportError or missing module issues across the entire codebase.

---

## What This Means for Defense

### Real issues to fix before defense:

1. **7 stale unit tests** — Tests check old column names. The code works, tests don't. Fix: update 7 test assertions to match new column names (`cvd` → `CVD_4`, etc.). ~15 minutes of work.

2. **14 broken integration tests** — Missing conftest fixtures. Fix: create `tests/integration/conftest.py` with the required fixtures. ~30 minutes of work.

3. **1 misclassified e2e script** — `test_e2e_app.py` isn't a pytest test. Fix: rename to `e2e_smoke_test.py` or add `conftest.py` to exclude it. ~2 minutes.

### Not issues (working as designed):

4. **Flask won't start without real secrets** — Security feature. Set real values in `.env` or Docker env.

5. **Resend SDK warning** — "Resend SDK not installed. Emails will be logged to console only." Expected in dev mode.

### The honest numbers:

| Category | Claimed | Actual |
|----------|---------|--------|
| Unit tests | 210+ | 204 collected, 197 pass, 7 fail |
| Integration tests | "all pass" | 14 broken (missing fixtures) |
| Smoke tests | 25 | 27 collected, 27 pass (1 miscategorized script) |
| Module imports | All work | All work |
| Flask startup | Works | Works only with real secrets |
