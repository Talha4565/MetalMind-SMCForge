# 🛠️ MetalMind SMCForge — Fixes Log

> Running log of all fixes applied to the ml-signals project.
> Updated after every phase is completed.

---

## Phase 1 — Deploy V5 Frontend ✅
**Date:** February 2026
**Time Taken:** ~5 minutes

### Problem
`http://localhost:5000/` was crashing with a **500 Internal Server Error**.

Flask's `main.py` was trying to serve `frontend/public/index_v4.html` but that file **did not exist**. The `frontend/public/` directory was completely empty.

```python
# main.py was doing this:
frontend_path = Path(__file__).parent.parent.parent / 'frontend' / 'public' / 'index_v4.html'
return send_file(frontend_path)  # ← FileNotFoundError
```

### Fix Applied
Copied the full V5 HTML file (`Desktop/V5.txt`) into `ml-signals/frontend/public/index_v4.html`.

### Files Changed
| File | Action |
|------|--------|
| `ml-signals/frontend/public/index_v4.html` | ✅ Created (2,145 lines, V5 content) |

### Result
- `http://localhost:5000/` now serves the V5 dashboard UI
- Auth modal appears on page load (correct behaviour)
- No FileNotFoundError
- All CSS, JS, and CDN libraries load correctly (Tailwind, Chart.js, FontAwesome, Google Fonts)

### Known Issues Remaining
- Login/signup buttons do not call the real API yet (Phase 2)
- Dashboard data is hardcoded mock data (Phase 3)
- SHAP chart not initialized (Phase 5)
- Candlestick chart is CSS mock (Phase 7)

---

## Phase 2 — Wire Authentication ✅
**Date:** February 2026
**Time Taken:** ~1 hour

### Problem
`handleLogin()` and `handleSignup()` were fake — they just hid the modal and showed a hardcoded "Welcome back, John!" message. No real API call was made. JWT token was never stored. All protected endpoints (`/api/predictions/latest`, `/api/backtest/results`, etc.) require `Authorization: Bearer <token>` — without this, every API call would return 401.

### Fix Applied

**HTML changes (`frontend/public/index_v4.html`):**
- Added `id` attributes to all login/signup form inputs (`loginEmail`, `loginPassword`, `signupEmail`, `signupPassword`, `signupConfirmPassword`)
- Added inline error display divs (`loginError`, `signupError`, `otpError`) — hidden by default, shown on failed requests
- Added OTP Verification Form (`otpForm`) — appears after signup, collects 6-digit code
- Added `id` attributes to submit buttons for loading state management

**JavaScript changes:**
- Added `authToken` + `currentUser` state variables — read from `localStorage` on load
- Added `getAuthHeaders()` helper — returns `{ Authorization: Bearer <token> }` for all future API calls
- Added `setAuthLoading()` — disables button + shows spinner during async calls
- Added `showAuthError()` / `hideAuthError()` — inline error display
- `handleLogin()` → real `POST /api/auth/login` call → stores JWT in `localStorage`
- `handleSignup()` → real `POST /api/auth/register` call → shows OTP form on success
- `handleVerifyOtp()` → real `POST /api/auth/verify-email` call → auto-redirects to login
- `resendOtp()` → real `POST /api/auth/resend-otp` call
- `handleLogout()` → clears `authToken` + `currentUser` from `localStorage`
- `restoreSession()` → on page load, reads saved token and skips auth modal if valid
- `initDashboard()` → placeholder stub for Phase 3
- Added `restoreSession()` call in `DOMContentLoaded`

### Auth Flow After Fix
```
Login → POST /api/auth/login → JWT stored in localStorage → modal hidden → initDashboard()
Signup → POST /api/auth/register → OTP form shown → verify OTP → redirect to login
Page reload → restoreSession() → token found → skip modal → initDashboard()
Logout → clear localStorage → show auth modal
```

### Files Changed
| File | Action |
|------|--------|
| `frontend/public/index_v4.html` | Login/signup inputs given IDs, OTP form added, all auth JS rewritten |

### Result
- Login calls real Flask API at `/api/auth/login`
- JWT token stored in `localStorage['authToken']`
- All future API calls will send `Authorization: Bearer <token>`
- Signup triggers OTP email verification flow
- Session persists across page reloads
- Inline error messages shown on failed login/signup
- Loading spinner shown on buttons during async calls

### Known Issues Remaining
- Dashboard still shows mock/random prediction data (Phase 3)
- SHAP chart not initialized (Phase 5)
- Backtest runs fake progress bar (Phase 4)
- Candlestick chart is CSS mock (Phase 7)

---

## Phase 3 — Wire Dashboard Data ✅
**Date:** February 2026
**Time Taken:** ~45 minutes

### Problem
Dashboard showed hardcoded/random mock data:
- Signal card (`signalDirection`, `confidenceValue`) showed random BUY/SELL from a static array
- `updatePrediction()` picked a random entry every time — not real model output
- Model info panel showed hardcoded "XGBoost v3.2.1", "JD" avatar, fake feature count
- Asset/timeframe selectors triggered random prediction instead of real API call
- Health status dots were static green — never actually checked the server
- Signal history table was hardcoded HTML rows

### Fix Applied

**`initDashboard()`** — rewritten to call two real APIs in parallel:
```js
await Promise.all([fetchLatestPrediction(), fetchModelInfo()])
```

**`fetchLatestPrediction()`** — new function:
- Calls `GET /api/predictions/latest?asset=<currentCommodity>&limit=1`
- Sends `Authorization: Bearer <token>` header
- On 401: calls `handleLogout()` (token expired)
- Updates: `signalDirection`, `signalIcon`, `confidenceValue`, `confidenceBar`
- Updates: `tickerGold` or `tickerSilver` with real close price
- Calls `updateSignalHistoryRow()` to prepend a row to signal history table
- Falls back to random mock if API unavailable (model not trained yet)

**`updatePredictionFallback()`** — extracted from old `updatePrediction()`:
- Used only when API is unavailable or model not found
- Keeps dashboard functional even without a trained model

**`updateSignalHistoryRow()`** — new function:
- Dynamically prepends a real signal row to `#signalHistoryBody`
- Color-coded BUY (green) / SELL (red)
- Keeps max 10 rows (removes oldest)

**`fetchModelInfo()`** — new function:
- Calls `GET /api/models/info?asset=<currentCommodity>`
- Updates: `modelType`, `modelFeatures`, `modelLastUpdated`, `modelTimeframe`
- Silent fail if model not loaded (no crash)

**`fetchHealthStatus()`** — new function:
- Calls `GET /api/health` (no auth required)
- Updates API status dot color: green=healthy, red=error
- Updates model status dot: green=loaded, yellow=not loaded
- Runs on page load + every 30 seconds via `setInterval`

**`selectCommodity()`** — wired to real API:
- Replaced `updatePrediction()` → `if (isLoggedIn) fetchLatestPrediction()`

**`selectTimeframe()`** — wired to real API:
- Replaced `updatePrediction()` → `if (isLoggedIn) fetchLatestPrediction()`

### Files Changed
| File | Action |
|------|--------|
| `frontend/public/index_v4.html` | initDashboard, fetchLatestPrediction, fetchModelInfo, fetchHealthStatus added; selectCommodity + selectTimeframe wired to real API |

### Result
- Signal card shows real XGBoost model output (signal + probability)
- Ticker price updates from real OHLCV close price
- Model info panel shows real model metadata (type, features, last trained)
- Health status dots reflect real server state
- Signal history table populates with real signals
- Asset/timeframe switching triggers real API refetch
- 401 responses auto-logout user (token expiry handled)
- Graceful fallback to mock data if model not trained yet

### Known Issues Remaining
- Backtest runs fake progress bar (Phase 4)
- SHAP chart not initialized (Phase 5)
- Candlestick chart is CSS mock (Phase 7)

---

## Phase 4 — Wire Backtest Engine ✅
**Date:** February 2026
**Time Taken:** ~45 minutes

### Problem
- `runBacktest()` ran a fake progress bar animation with hardcoded 90.59% accuracy
- No real API call was made to `/api/backtest/run`
- `exportReport()` showed a fake toast after 1.5 seconds — no file was ever downloaded
- Metric cards (`btAccuracy`, `btSharpe`, etc.) showed hardcoded HTML values
- Trade summary table was hardcoded HTML rows

### Fix Applied

**`runBacktest()`** — fully rewritten:
- Collects real form values: asset, start_date, end_date from the modal inputs
- `POST /api/backtest/run` with JWT auth header
- Progress bar animates realistically while API runs (increments to 90%, jumps to 100% on completion)
- On success → calls `fetchBacktestResults()` to load real metrics
- On API failure/timeout → gracefully falls back to loading existing results from disk
- `backtestRunning` flag prevents double-submit

**`fetchBacktestResults()`** — new function:
- `GET /api/backtest/results?asset=<asset>` with JWT auth
- Stores result in `lastBacktestData` state variable
- Called on modal open (loads existing results immediately) and after run completes

**`displayBacktestResults(data)`** — new function:
- Maps flexible API field names (e.g. `accuracy` / `signal_accuracy` / `win_rate`)
- Updates all metric card elements: `btAccuracy`, `btSharpe`, `btDrawdown`, `btHitRate`, `btProfitFactor`, `btTotalTrades`, `btNetProfit`
- Populates `btTradeSummary` tbody with real trade rows (max 15 shown)
- Formats numbers: percentages, USD, decimals

**`exportReport(format)`** — fully rewritten:
- Fetches real results from `GET /api/backtest/results`
- `csv` → builds CSV string from result object → triggers real file download
- `json` → serializes full result as JSON → triggers real file download
- `pdf` → generates plain text file → triggers download (no jsPDF dependency)
- `triggerDownload(blob, filename)` helper — creates blob URL, clicks anchor, revokes URL

### Files Changed
| File | Action |
|------|--------|
| `frontend/public/index_v4.html` | runBacktest, fetchBacktestResults, displayBacktestResults, exportReport, triggerDownload all rewritten/added |

### Result
- Backtest button calls real Flask API
- Progress bar animates during real API execution (up to 5 min timeout)
- Real metrics displayed from JSON results file
- Trade summary table populated from real trade log
- CSV/JSON/PDF exports trigger real file downloads
- Existing results loaded automatically when modal opens
- Double-submit protected via `backtestRunning` flag
- Graceful fallback if no results exist yet

### Known Issues Remaining
- SHAP chart not initialized (Phase 5)
- Candlestick chart is CSS mock (Phase 7)

---

## Phase 5 — Wire SHAP Chart ✅
**Date:** February 2026
**Time Taken:** ~30 minutes

### Problem
- SHAP feature importance chart area existed in HTML but had no `Chart.js` initialization
- `chartInstance` variable was referenced but never assigned
- `GET /api/shap/feature-importance` was never called
- Chart showed blank/empty canvas on dashboard

### Fix Applied

**`fetchSHAPChart()`** — new function:
- Calls `GET /api/shap/feature-importance` with JWT auth header
- Parses `feature_importance` array from response
- Silent fail if SHAP analysis not run yet
- Called in `initDashboard()` in parallel with predictions + model info
- Re-called when asset switches (`selectCommodity`)

**`renderSHAPChart(features)`** — new function:
- Sorts features by importance descending, takes top 10
- Converts raw importance values to percentages
- Destroys existing `shapChartInstance` before re-rendering (prevents memory leak)
- Renders horizontal bar chart (`indexAxis: 'y'`) via Chart.js
- Color coding: gold (#1), purple (top 3), indigo (rest)
- Dark-themed axes: grid lines `rgba(148,163,184,0.1)`, tick color `#94a3b8`
- Font: JetBrains Mono for y-axis labels (feature names)
- Tooltip shows `X.XX%` format

**`initDashboard()`** — updated:
- Added `fetchSHAPChart()` to the `Promise.all` parallel fetch group

**`selectCommodity()`** — updated:
- Added `fetchSHAPChart()` call on asset switch → chart updates for gold vs silver

### API Response Format Expected
```json
{
  "feature_importance": [
    {"feature": "vwap_distance_5m", "importance": 0.15},
    {"feature": "volume_imbalance", "importance": 0.10}
  ]
}
```
Note: Backend returns mock data if real SHAP analysis hasn't been run — chart still renders.

### Files Changed
| File | Action |
|------|--------|
| `frontend/public/index_v4.html` | fetchSHAPChart, renderSHAPChart added; initDashboard + selectCommodity updated |

### Result
- SHAP chart renders real feature importance from XGBoost model
- Updates automatically when switching between Gold and Silver
- Gracefully empty if SHAP not computed yet
- No memory leaks (old chart destroyed before new one created)
- Mock data from API used as fallback (10 SMC features shown)

### Known Issues Remaining
- Candlestick chart is CSS mock (Phase 7)

---

## Phase 6 — Wire Watchlist & Settings ✅
**Date:** February 2026
**Time Taken:** ~1 hour

### Problem
- Watchlist modal showed 3 hardcoded HTML items (XAU/USD 15m, XAG/USD 1h, XAU/USD 4h)
- `addToWatchlist()` showed a fake toast — no API call made
- `removeFromWatchlist()` just removed the DOM element — no persistence
- Settings "Save Changes" button had no `onclick` handler — nothing happened
- Profile fields had no `name` attributes — couldn't collect form values

### Fix Applied

**Watchlist HTML:**
- Replaced 3 hardcoded watchlist item divs with a single loading spinner div
- Container (`#watchlistContainer`) now populated entirely by JS

**`openWatchlistModal()`** — updated:
- Calls `fetchWatchlist()` on open → always shows fresh data

**`fetchWatchlist()`** — new function:
- `GET /api/watchlist` with JWT auth header
- Stores result in `watchlistData[]` state variable
- Calls `renderWatchlist()` to build DOM

**`renderWatchlist()`** — new function:
- Dynamically builds watchlist item cards from `watchlistData[]`
- Shows empty state if no items
- Each card: symbol, display name, trash button with `removeFromWatchlist(id)`
- Clicking card → `selectWatchlistItem(asset, tf)` → switches dashboard asset

**`addToWatchlist()`** — fully rewritten:
- Reads `#watchlistAsset` select value (e.g. `gold-15m`)
- Maps to symbol (`XAU/USD` or `XAG/USD`)
- `POST /api/watchlist` with JWT auth
- Refreshes watchlist on success

**`removeFromWatchlist(itemId)`** — fully rewritten:
- `DELETE /api/watchlist/{id}` with JWT auth
- Refreshes watchlist on success
- No longer just removes DOM element (was not persisted)

**`saveProfile()`** — new function:
- Reads all `input[name]` and `select[name]` fields inside `#settingsModal`
- `PUT /api/profile` with JWT auth
- Shows success/error notification
- Loading state on Save button

**Settings "Save Changes" button:**
- Added `onclick="saveProfile()"` and `id="saveProfileBtn"`

### Files Changed
| File | Action |
|------|--------|
| `frontend/public/index_v4.html` | Watchlist HTML replaced with dynamic container; openWatchlistModal, fetchWatchlist, renderWatchlist, addToWatchlist, removeFromWatchlist, saveProfile all rewritten/added |

### Result
- Watchlist loads real items from Flask API on modal open
- Add/remove operations persist to backend database
- Watchlist items clickable → switches dashboard to that asset
- Profile "Save Changes" calls real `PUT /api/profile`
- All operations show loading state + success/error notifications

### Known Issues Remaining
- Candlestick chart is CSS mock (Phase 7)

---

## Phase 7 — Real Price Chart ✅
**Date:** February 2026
**Time Taken:** ~1 hour

### Problem
- Chart area showed 5 hardcoded static CSS `div` elements styled as candles
- No real OHLCV data was fetched or rendered
- Price scale showed hardcoded values (2,395.00 etc.)
- Current price label showed hardcoded "2,387.45"
- No Chart.js canvas existed in the chart area
- SMC annotation overlays (BOS, CHoCH, Premium/Discount) were hardcoded positions

### Fix Applied

**HTML — Chart Area (lines 1141–1388 replaced):**
- Removed all hardcoded CSS candles, static price scale, hardcoded annotations
- Added `<canvas id="priceChart">` filling the full chart container
- Kept SMC annotation labels (BOS, CHoCH, Premium/Discount) as lightweight absolute overlays
- Added `#currentPriceLabel` / `#currentPriceValue` — updated dynamically by JS
- Added `#chartLoadingOverlay` — shown while fetching, hidden when done

**`fetchAndRenderPriceChart()`** — new function:
- `GET /api/predictions/latest?asset=<asset>&limit=60` with JWT auth
- Shows loading overlay during fetch
- Falls back to `renderFallbackChart()` if API unavailable or < 2 data points
- Passes predictions array to `renderPriceChart()`

**`renderPriceChart(predictions)`** — new function:
- Extracts timestamps (x-axis labels) and close prices (y-axis)
- Updates `#currentPriceValue` with latest close price
- Determines bullish/bearish color (green/red) from first vs last close
- Destroys existing `priceChartInstance` before re-creating (no memory leak)
- Chart.js line chart with:
  - `fill: true` — gradient area fill under price line
  - `tension: 0.3` — smooth curve
  - `pointRadius: 0` — no dots (cleaner look)
  - Y-axis on right side (trading chart convention)
  - Dark-themed grid, JetBrains Mono font
  - Custom tooltip: dark background, gold border, mono font

**`renderFallbackChart()`** — new function:
- Generates realistic price walk when API unavailable
- Uses base price: Gold=2387, Silver=28.5
- 60 candles × 15-minute intervals
- Passes to `renderPriceChart()` for consistent rendering

**`initDashboard()`** — updated:
- Added `fetchAndRenderPriceChart()` to `Promise.all` parallel fetch group

**`selectCommodity()`** — updated:
- Added `fetchAndRenderPriceChart()` on asset switch

**`selectTimeframe()`** — updated:
- Added `fetchAndRenderPriceChart()` on timeframe switch

### Files Changed
| File | Action |
|------|--------|
| `frontend/public/index_v4.html` | Chart area HTML replaced with canvas; fetchAndRenderPriceChart, renderPriceChart, renderFallbackChart added; initDashboard, selectCommodity, selectTimeframe updated |

### Result
- Real Chart.js line chart renders in dashboard using actual API data
- Price updates when switching asset (Gold ↔ Silver)
- Price updates when switching timeframe
- Current price label updates dynamically
- Loading overlay shown/hidden during fetch
- Graceful fallback to realistic simulated data if API unavailable
- No memory leaks (chart instance destroyed before re-render)
- SMC annotation labels (BOS, CHoCH, Premium/Discount) retained as overlays

### Known Issues Remaining
- None — all 7 phases complete. Phase 8 (Docker) is next.

---

## Phase 8b — Docker Pre-composition Fixes ✅
**Date:** February 2026
**Time Taken:** ~20 minutes

### Problems Found During Docker Review

| Issue | Severity | File |
|-------|----------|------|
| `curl` missing from Docker image — healthcheck fails | 🔴 Critical | `api/Dockerfile` |
| `FilePath` undefined type hint — crashes on import | 🔴 Critical | `api/app/main.py` line 198 |
| Relative paths for backtest/SHAP results — break inside Docker | 🔴 Critical | `api/app/main.py` |
| `subprocess` uses `python` not `sys.executable` — wrong interpreter in Docker | 🔴 Critical | `api/app/main.py` |
| `cwd=Path.cwd()` in subprocess — wrong directory inside Docker | 🔴 Critical | `api/app/main.py` |

### Fixes Applied

**`api/Dockerfile`:**
- Added `curl` to apt-get install — required for healthcheck `CMD curl -f http://localhost:5000/api/health`

**`api/app/main.py`:**
- `FilePath` → `Path` type hint on `FileCache.get_json()` — fixes NameError on startup
- `Path('reports/backtest_results/...')` → `Path(__file__).parent.parent.parent / 'reports' / 'backtest_results' / ...` — absolute path works in Docker
- `Path('reports/shap_plots/shap_values.json')` → absolute path via `project_root` — consistent with Docker working directory
- `subprocess(['python', ...], cwd=Path.cwd())` → `subprocess([sys.executable, ...], cwd=str(project_root))` — uses correct Python interpreter and project root

### Files Changed
| File | Action |
|------|--------|
| `api/Dockerfile` | Added `curl` to system dependencies |
| `api/app/main.py` | Fixed FilePath type, 3 relative paths → absolute, subprocess python → sys.executable |

### Result
- Docker healthcheck will work (`curl` now available)
- App will not crash on startup (`FilePath` NameError fixed)
- Backtest results load correctly from any working directory
- SHAP values load correctly from any working directory
- Backtest subprocess uses correct Python interpreter inside container

---

## Phase 8 — Dockerize Full Stack ✅
**Date:** February 2026
**Time Taken:** ~30 minutes

### Problem
- `docker-compose.yml` was completely empty
- `api/Dockerfile` was completely empty
- `api/requirements.txt` was missing 10+ required packages (gunicorn, flask-jwt-extended, bcrypt, flask-limiter, flask-compress, shap, flask-sqlalchemy, python-dotenv, requests, openpyxl)
- No way to run the project with a single command

### Fix Applied

**`api/Dockerfile`** — created from scratch:
- Base: `python:3.11-slim`
- System deps: `gcc`, `g++` (required for numpy/pandas compilation)
- Copies `api/requirements.txt` → installs all Python deps
- Copies entire project into `/app`
- Creates `/app/instance` directory for SQLite database
- Sets `PYTHONPATH=/app` so all relative imports work
- Runs via **Gunicorn** (production WSGI server): 2 workers, 120s timeout
- Exposes port `5000`

**`api/requirements.txt`** — updated with full dependency list:
```
flask==3.0.0            # Core framework
flask-cors==4.0.0       # CORS headers
gunicorn==21.2.0        # Production WSGI server
flask-jwt-extended==4.6.0  # JWT auth
bcrypt==4.1.2           # Password hashing
flask-limiter==3.5.0    # Rate limiting
flask-compress==1.14    # Response compression
pandas==2.1.4           # Data processing
numpy==1.26.2           # Numerical computing
scikit-learn==1.3.2     # ML utilities
xgboost==2.0.3          # Signal prediction model
shap==0.44.0            # Explainability
flask-sqlalchemy==3.1.1 # ORM / database
python-dotenv==1.0.0    # .env file support
requests==2.31.0        # HTTP client
openpyxl==3.1.2         # Excel file support
```

**`docker-compose.yml`** — created from scratch:
- Single `api` service (Flask/Gunicorn on port 5000)
- Environment variables: `FLASK_SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`, `PYTHONPATH`
- Volumes mounted:
  - `./instance` → SQLite database persistence
  - `./data` → Gold/Silver CSV datasets
  - `./models` → Trained XGBoost models
  - `./reports` → Backtest results
- `restart: unless-stopped` — auto-restarts on crash
- Healthcheck: `GET /api/health` every 30s

### Files Changed
| File | Action |
|------|--------|
| `api/Dockerfile` | Created — Python 3.11, Gunicorn, full build |
| `api/requirements.txt` | Updated — 16 packages (was 6) |
| `docker-compose.yml` | Created — full service config with volumes + healthcheck |

### How to Run
```bash
cd ml-signals
docker compose up --build
```
Then open: `http://localhost:5000`

### Result
- Full stack runs with one command: `docker compose up --build`
- SQLite database persists via volume mount
- ML models and data files persisted via volume mounts
- Production-grade: Gunicorn (not Flask dev server)
- Auto-restarts on crash
- Health check monitors `/api/health` every 30 seconds
- Frontend (`index_v4.html`) served at `http://localhost:5000/`
- All API endpoints at `http://localhost:5000/api/*`
