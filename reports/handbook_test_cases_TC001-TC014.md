# MetalMind SMCForge — Handbook Test Cases (TC-001 to TC-014)

> Generated: 2026-07-19 | Test Environment: Docker Compose (API + DB + ChromaDB + Frontend + ETL)

## Traceability Matrix

| TC-ID | Requirement | Module | Type | Status |
|-------|------------|--------|------|--------|
| TC-001 | User Login Valid Credentials | Auth | Functional | ✅ Pass |
| TC-002 | Login Rejection Invalid Password | Auth | Functional | ✅ Pass |
| TC-003 | Silver ML Forecast Generation | Forecast | Functional | ✅ Pass |
| TC-004 | Unauthenticated Forecast Attempt | Forecast | Security | ✅ Pass |
| TC-005 | 1-Year Gold Candlestick Chart | Chart | Functional | ✅ Pass |
| TC-006 | Watchlist Add and Persistence | Watchlist | Functional | ✅ Pass |
| TC-007 | Invalid Date Range Validation | Backtest | Functional | ✅ Pass |
| TC-008 | Gold ML Forecast Generation | Forecast | Functional | ✅ Pass |
| TC-009 | User Registration with Validation | Auth | Functional | ✅ Pass |
| TC-010 | SHAP Explainability Data Retrieval | Explainability | Functional | ✅ Pass |
| TC-011 | Backtest Execution and Results Retrieval | Backtest | Functional | ✅ Pass |
| TC-012 | Pipeline Status and Health Monitoring | Pipeline | Functional | ✅ Pass |
| TC-013 | Password Change with Strength Validation | Profile | Functional | ✅ Pass |
| TC-014 | 2FA Setup and Enable Flow | Profile | Security | ✅ Pass |

---

## Test Case TC-008: Gold ML Forecast Generation

| Field | Value |
|-------|-------|
| **Project Name** | MetalMind SMCForge |
| **Module** | Forecast |
| **Test Case ID** | TC-008 |
| **Test Case Name** | Gold XGBoost Forecast Generation |
| **Objective** | Verify forecast generation for gold commodity with valid response structure. |
| **Preconditions** | User authenticated. Gold OHLCV data present. Gold model artifact loaded. |
| **Test Steps** | 1. Login and navigate to dashboard. 2. Select 'GOLD' from dashboard navigation. 3. Observe signal display. 4. Inspect API response via Network tab. |
| **Expected Result** | HTTP 200. Valid direction, probabilities, SHAP values, expected_value, and timestamp in response. |
| **Postconditions** | Gold forecast cached. Dashboard updated with signal annotation. |
| **Actual Result** | HTTP 200 returned. Signal direction, confidence, probability, TP/SL prices, and SHAP values all present. |
| **Status** | Pass |
| **Notes** | Warm-up call takes 4-5s (model lazy-load + feature engineering). Subsequent cached calls complete in <1s. |
| **Tested By** | Talha |
| **Test Date** | 19 July 2026 |
| **Attachments** | `reports/performance_benchmark.json` |

---

## Test Case TC-009: User Registration with Validation

| Field | Value |
|-------|-------|
| **Project Name** | MetalMind SMCForge |
| **Module** | Auth |
| **Test Case ID** | TC-009 |
| **Test Case Name** | User Registration with Input Validation |
| **Objective** | Verify that a new user can register with valid credentials and that invalid inputs are rejected. |
| **Preconditions** | No existing account with the test email. |
| **Test Steps** | 1. Navigate to /auth/register. 2. Enter name, email, password. 3. Click 'Register'. 4. Test with invalid email (no @). 5. Test with weak password (no special char). 6. Test with existing email. |
| **Expected Result** | Valid input: HTTP 201, redirect to login. Invalid email: HTTP 400 'Invalid email format'. Weak password: HTTP 400 validation error. Duplicate email: HTTP 409 Conflict. |
| **Postconditions** | New user record in database with bcrypt-hashed password. OTP record created. |
| **Actual Result** | All cases pass. Valid registration creates user. Invalid email returns 400 with JSON error. Weak password returns validation message. |
| **Status** | Pass |
| **Notes** | Dev mode auto-verifies email (FLASK_ENV=development). OTP code no longer leaked in response body (fixed 19 July 2026). |
| **Tested By** | Talha |
| **Test Date** | 19 July 2026 |
| **Attachments** | `reports/security_scan.json` |

---

## Test Case TC-010: SHAP Explainability Data Retrieval

| Field | Value |
|-------|-------|
| **Project Name** | MetalMind SMCForge |
| **Module** | Explainability |
| **Test Case ID** | TC-010 |
| **Test Case Name** | SHAP Feature Importance Data Retrieval |
| **Objective** | Verify that SHAP feature importance data is returned correctly for both gold and silver. |
| **Preconditions** | Model loaded. SHAP cache populated or computable. |
| **Test Steps** | 1. Call GET /api/shap/feature-importance?asset=gold. 2. Call GET /api/shap/feature-importance?asset=silver. 3. Verify response structure: feature names, importance values, expected_value. 4. Verify sorted by absolute contribution. |
| **Expected Result** | HTTP 200 for both assets. Response contains feature_importance array with feature names and contribution values. expected_value present. |
| **Postconditions** | SHAP data cached for subsequent requests. |
| **Actual Result** | HTTP 200 in ~9ms (p50) from cache. Gold: 100 features with SHAP values. Silver: 89 features with SHAP values. Expected_value present for both. |
| **Status** | Pass |
| **Notes** | Cold computation takes 3-5s depending on model load state. Cache lifetime: model load duration. Recompute flag available at ?recompute=true. |
| **Tested By** | Talha |
| **Test Date** | 19 July 2026 |
| **Attachments** | `reports/performance_benchmark.json` (SHAP endpoint: p50=9ms) |

---

## Test Case TC-011: Backtest Execution and Results Retrieval

| Field | Value |
|-------|-------|
| **Project Name** | MetalMind SMCForge |
| **Module** | Backtest |
| **Test Case ID** | TC-011 |
| **Test Case Name** | Backtest Execution and Results Retrieval |
| **Objective** | Verify that a backtest can be executed and results retrieved from history. |
| **Preconditions** | User authenticated. Model loaded. Historical OHLCV data present. |
| **Test Steps** | 1. Navigate to /backtest. 2. Select asset (gold/silver). 3. Set date range, initial capital. 4. Click 'Run Simulation'. 5. Monitor progress bar. 6. Verify result appears in history table. 7. Expand row for detailed metrics. |
| **Expected Result** | Backtest starts via POST /api/backtest/run and returns 202. Progress polling updates every 1.5s. Results appear in history on completion. Sharpe, Sortino, max drawdown, profit factor, win rate all present. |
| **Postconditions** | Backtest record saved to reports/backtest_results/. History table updated with new entry. |
| **Actual Result** | Backtest accepted (202). Progress tracked at 10/30/50/70/80/100%. Results display win rate, profit factor, net profit, Sharpe, Sortino, max DD, total trades in expanded row. |
| **Status** | Pass |
| **Notes** | Rate limited to 6/hour (was 1/hour before fix). Pre-computed results in reports/backtest_results/ load instantly. |
| **Tested By** | Talha |
| **Test Date** | 19 July 2026 |
| **Attachments** | `reports/backtest_results/gold_backtest.json`, `reports/backtest_results/silver_backtest.json` |

---

## Test Case TC-012: Pipeline Status and Health Monitoring

| Field | Value |
|-------|-------|
| **Project Name** | MetalMind SMCForge |
| **Module** | Pipeline |
| **Test Case ID** | TC-012 |
| **Test Case Name** | Pipeline Status and Health Monitoring |
| **Objective** | Verify that the pipeline status endpoint returns accurate health data for all subsystems. |
| **Preconditions** | API running. MT5 cache file present (may be stale). ChromaDB accessible. |
| **Test Steps** | 1. Call GET /api/pipeline/status. 2. Call GET /api/pipeline/details. 3. Call GET /api/orchestrator/status. 4. Verify response fields: data freshness (gold/silver), model info, pipeline health, system status. |
| **Expected Result** | All endpoints return HTTP 200. Pipeline status shows ETL, features, training stages. Orchestrator status includes MT5 cache, ChromaDB, retrain status. |
| **Postconditions** | Pipeline health file updated with latest check. |
| **Actual Result** | Pipeline status: HTTP 200. Shows data age, model status, pipeline stages. Orchestrator: MT5 cache exists (may be stale), ChromaDB connected with signal count, retrain status accurate. |
| **Status** | Pass |
| **Notes** | Consecutive failures counter only increments during scheduled pipeline runs, not during manual status checks. MT5 cache staleness expected on weekends (market closed). |
| **Tested By** | Talha |
| **Test Date** | 19 July 2026 |
| **Attachments** | `reports/pipeline_health.json`, `reports/pipeline_status.json` |

---

## Test Case TC-013: Password Change with Strength Validation

| Field | Value |
|-------|-------|
| **Project Name** | MetalMind SMCForge |
| **Module** | Profile |
| **Test Case ID** | TC-013 |
| **Test Case Name** | Password Change with Strength Validation |
| **Objective** | Verify that a user can change their password with proper validation of old password and new password strength. |
| **Preconditions** | User authenticated with known current password. |
| **Test Steps** | 1. Navigate to /dashboard/profile. 2. Expand 'Security' section. 3. Click 'Change Password'. 4. Enter current password. 5. Enter new password (must meet strength rules). 6. Enter confirm password. 7. Click 'Update Password'. 8. Test with wrong current password. 9. Test with mismatched confirm. 10. Test with weak new password. |
| **Expected Result** | Correct: HTTP 200, 'Password changed successfully'. Wrong current: HTTP 401. Mismatch: client-side validation blocks. Weak: HTTP 400 with strength requirements. |
| **Postconditions** | Password hash updated in database (bcrypt). User can login with new password. |
| **Actual Result** | All cases pass. Bcrypt verify used for current password check. Strength validation enforces: 8+ chars, uppercase, lowercase, digit, special character. |
| **Status** | Pass |
| **Notes** | Rate limited to 5/minute. Password service centralized in api/app/services/password_service.py. |
| **Tested By** | Talha |
| **Test Date** | 19 July 2026 |
| **Attachments** | `api/app/services/password_service.py` |

---

## Test Case TC-014: 2FA Setup and Enable Flow

| Field | Value |
|-------|-------|
| **Project Name** | MetalMind SMCForge |
| **Module** | Profile |
| **Test Case ID** | TC-014 |
| **Test Case Name** | 2FA Setup and Enable Flow |
| **Objective** | Verify the complete 2FA setup flow: secret generation, QR code display, OTP verification, and enable/disable. |
| **Preconditions** | User authenticated. 2FA not currently enabled. |
| **Test Steps** | 1. Navigate to /dashboard/profile. 2. Locate 'Two-Factor Auth' section. 3. Click 'Setup 2FA'. 4. Observe QR code and secret key. 5. Scan QR with authenticator app. 6. Enter 6-digit TOTP code. 7. Click 'Enable'. 8. Logout and login again — verify 2FA prompt appears. 9. Enter valid TOTP to complete login. 10. Disable 2FA with valid TOTP. |
| **Expected Result** | Setup returns QR code (base64 PNG) and secret. Enable returns 200 on valid OTP. Login with 2FA prompts for code. Valid code completes login. Disable requires OTP confirmation. |
| **Postconditions** | `totp_enabled` set to True on user record. `totp_secret` stored encrypted. Login flow requires 2FA step. |
| **Actual Result** | Setup returns QR data URI and provisioning URI. Enable verifies TOTP with valid_window=1. Profile shows '2FA: Enabled'. Login prompts for code on enabled accounts. Disable requires valid OTP confirmation. |
| **Status** | Pass |
| **Notes** | Uses pyotp (RFC 6238). QR generated via qrcode library. provisioning_uri includes issuer='MetalMind SMCForge'. Rate limited to 3/minute for setup/enable/disable. |
| **Tested By** | Talha |
| **Test Date** | 19 July 2026 |
| **Attachments** | `api/app/profile.py` (2FA endpoints) |

---

## Evidence Map

Each test case maps to real project artifacts:

| TC-ID | Evidence File(s) |
|-------|-----------------|
| TC-001 | `api/app/auth.py` (login endpoint), `frontend-next/src/app/auth/login/page.tsx` |
| TC-002 | `api/app/auth.py:292-340` (login with invalid password) |
| TC-003 | `api/app/main.py:693` (predictions/silver), `reports/training_logs/silver_latest.json` |
| TC-004 | `api/app/auth.py:92-116` (token_required decorator) |
| TC-005 | `api/app/main.py:1117` (predictions/history), `frontend-next/src/components/Charts/TradingViewChart.tsx` |
| TC-006 | `api/app/watchlist.py` (CRUD), `frontend-next/src/components/Watchlist/WatchlistTable.tsx` |
| TC-007 | `frontend-next/src/app/backtest/page.tsx` (date validation) |
| TC-008 | `api/app/main.py:693` (predictions/gold), `reports/training_logs/gold_latest.json` |
| TC-009 | `api/app/auth.py:126-202` (register endpoint) |
| TC-010 | `api/app/main.py:1296` (shap/feature-importance), `reports/ablation_gold.json` |
| TC-011 | `api/app/main.py:1266` (backtest/run), `reports/backtest_results/` |
| TC-012 | `api/app/main.py:1157` (orchestrator/status), `api/app/pipeline_routes.py` |
| TC-013 | `api/app/profile.py:139-186` (password change), `api/app/services/password_service.py` |
| TC-014 | `api/app/profile.py:280-369` (2FA setup/enable/disable) |
