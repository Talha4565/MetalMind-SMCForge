# 📊 MetalMind SMCForge — V5 Frontend Documentation

> **Version:** V5 | **File:** `index_v4.html` (served by Flask)
> **Date:** February 2026
> **Stack:** Vanilla HTML + Tailwind CSS CDN + Chart.js + Font Awesome + JetBrains Mono + Inter

---

## Table of Contents

1. [Product Requirements Document (PRD)](#1-product-requirements-document-prd)
2. [App Flow](#2-app-flow)
3. [Frontend Guidelines](#3-frontend-guidelines)
4. [Implementation Plan](#4-implementation-plan)

---

## 1. Product Requirements Document (PRD)

### 1.1 Product Overview

**MetalMind SMCForge V5** is a single-page, self-contained HTML dashboard for an AI-powered trading signals platform focused on Gold (XAU/USD) and Silver (XAG/USD). It is served directly by Flask as a static file — no build step, no Node.js, no React required. It communicates with the Flask REST API (`/api/*`) for all data operations.

The name "Neural Trading Engine v3.2" reflects its identity as the UI layer for a machine learning pipeline using Smart Money Concepts (SMC) methodology combined with XGBoost-based signal generation.

---

### 1.2 Problem Statement

Traders and ML researchers need a single interface to:
- Monitor live AI-generated BUY/SELL signals for gold and silver
- Visualize SMC chart annotations (Order Blocks, FVG zones, BOS/CHoCH lines)
- Run and evaluate backtests on historical data (2004–2024)
- Understand model decisions through SHAP feature importance
- Manage their watchlist, profile, and notification preferences

The V5 frontend delivers all of this in a **single HTML file** — no install, no build, works immediately when Flask serves it.

---

### 1.3 Target Users

| User | Need |
|------|------|
| **FYP Evaluators / Exam Committee** | See a professional, fully-featured dashboard that demonstrates the full system |
| **Trader / End User** | Monitor signals, run backtests, manage watchlist |
| **ML Developer** | Inspect SHAP feature importance, model accuracy metrics |

---

### 1.4 Modules (Features)

| Module | ID | Description |
|--------|----|-------------|
| Authentication | 1 | Login + Signup modal shown on page load |
| Settings & Profile | 2 | Tabbed modal: Profile, Preferences, Data Sources, Notifications, Security |
| Data Source Config | 3 | Kaggle dataset connection status, API key, refresh interval |
| Main Dashboard | 4 | Top navbar, ticker tape, asset selector, signal card, candlestick chart, SMC annotations, SHAP chart |
| Watchlist | 5 | Add/remove/click XAU/XAG pairs per timeframe |
| Signal History | 6 | Table of recent BUY/SELL signals |
| SHAP Explainability | 7 | Feature importance chart via Chart.js |
| Backtest Engine | 8 | Configuration form: asset, timeframe, date range, balance, risk, R:R |
| Backtest Results | 9 | Metrics: Accuracy, Sharpe, Drawdown, Hit Rate, Profit Factor + Equity Curve + Trade Summary |
| Export | 10 | CSV, PDF, JSON export of backtest results |
| Theme Toggle | 11 | Dark / Light mode via CSS class on `<html>` |

---

### 1.5 API Endpoints Consumed

| Method | Endpoint | Used By |
|--------|----------|---------|
| `POST` | `/api/auth/login` | Module 1 — Login |
| `POST` | `/api/auth/register` | Module 1 — Signup |
| `GET` | `/api/predictions/latest?asset=gold&limit=100` | Module 4 — Signal card |
| `GET` | `/api/shap/feature-importance` | Module 7 — SHAP chart |
| `GET` | `/api/backtest/results?asset=gold` | Module 9 — Results display |
| `POST` | `/api/backtest/run` | Module 8 — Run backtest |
| `GET/POST` | `/api/config` | Module 3 — Data source config |
| `GET` | `/api/models/info?asset=gold` | Module 4 — Model info panel |
| `GET` | `/api/health` | Status bar in navbar |
| `GET/POST/DELETE` | `/api/watchlist/*` | Module 5 — Watchlist CRUD |
| `GET/PUT` | `/api/profile` | Module 2 — Profile settings |

---

### 1.6 Non-Functional Requirements

| Requirement | Detail |
|-------------|--------|
| Zero build step | Single HTML file, CDN-only dependencies |
| No framework | Vanilla JS only — no React, Vue, or Angular |
| Dark-first | Default to dark mode on load |
| Responsive | Works on desktop (primary), tablet (secondary) |
| Auth-gated | Dashboard hidden behind auth modal on load |
| Flask-compatible | Served via `send_file()` from Flask at route `/` |

---

## 2. App Flow

### 2.1 Page Load Flow

```
Browser opens http://localhost:5000
        │
        ▼
Flask serves frontend/public/index_v4.html
        │
        ▼
HTML loads → CDN scripts load (Tailwind, Chart.js, FontAwesome, Fonts)
        │
        ▼
DOMContentLoaded fires → initApp()
        │
        ├─► Auth modal displayed (visible by default, blocks dashboard)
        ├─► Ticker tape starts animating
        └─► Scanline animation starts
```

---

### 2.2 Authentication Flow

```
Auth Modal Visible
        │
        ├─► User clicks LOGIN tab (default)
        │       │
        │       ▼
        │   Enter email + password
        │   Click "Access Dashboard"
        │       │
        │       ▼
        │   handleLogin() → POST /api/auth/login
        │       │
        │       ├─► Success → store JWT token
        │       │           → hide authModal
        │       │           → show main dashboard
        │       │           → fetch predictions, model info
        │       │
        │       └─► Failure → show error message in modal
        │
        └─► User clicks SIGN UP tab
                │
                ▼
            Enter first/last name, email, password, confirm
            Click "Create Account"
                │
                ▼
            handleSignup() → POST /api/auth/register
                │
                ├─► Success → auto-login → show dashboard
                └─► Failure → show error
```

---

### 2.3 Main Dashboard Flow

```
Dashboard Visible
        │
        ├─► TICKER TAPE: scrolling XAU/XAG price tickers (live or simulated)
        │
        ├─► NAVBAR
        │   ├─► Logo + Branding
        │   ├─► Asset Selector: [XAU/USD Gold] [XAG/USD Silver]
        │   ├─► Timeframe Selector: [5m] [15m] [1H] [4H] [1D]
        │   ├─► Status indicators: WebSocket, Model, API health
        │   └─► Icons: Watchlist, Backtest, Settings, Logout
        │
        ├─► LEFT COLUMN
        │   ├─► Signal Card: BUY/SELL badge + confidence % + price + timestamp
        │   ├─► SMC Candlestick Chart (CSS-rendered candles with annotations)
        │   │   ├─► Order Blocks (bullish green, bearish red)
        │   │   ├─► FVG Zones (purple dashed)
        │   │   ├─► BOS Lines (gold dashed)
        │   │   └─► CHoCH Lines (cyan dotted)
        │   └─► Model Info Panel: accuracy, features count, last trained
        │
        └─► RIGHT COLUMN
            ├─► SHAP Feature Importance Chart (Chart.js horizontal bar)
            ├─► Signal History Table (recent BUY/SELL signals)
            └─► ETL Status Panel (pipeline health indicators)
```

---

### 2.4 Backtest Flow

```
User clicks Backtest button in navbar
        │
        ▼
backtestModal opens
        │
        ▼
User configures:
  • Asset (Gold / Silver)
  • Timeframe (15m / 1H / 4H)
  • Start Date + End Date
  • Initial Balance ($)
  • Risk Per Trade (%)
  • Risk:Reward Ratio (1:2 / 1:3 / 1:4)
        │
        ▼
User clicks "Run Backtest"
        │
        ▼
runBacktest() → POST /api/backtest/run
        │
        ├─► Progress bar animates (simulated or real polling)
        │
        ▼
Results displayed:
  ┌─────────────────────────────────────────────────┐
  │  Accuracy  │  Sharpe  │  Drawdown  │  Hit Rate  │  Profit Factor  │
  └─────────────────────────────────────────────────┘
  │  Equity Curve (Chart.js line chart)              │
  │  Trade Summary Table                             │
  │  Financial Summary Table                         │
  └─────────────────────────────────────────────────┘
        │
        ▼
Export buttons:
  [Export CSV]  [Export PDF]  [Export JSON]
        │
        ▼
exportReport(type) → triggers download
```

---

### 2.5 Watchlist Flow

```
User clicks Watchlist icon
        │
        ▼
watchlistModal opens
        │
        ├─► Existing watchlist items shown:
        │   XAU/USD 15m → price → % change → BUY/SELL badge
        │   XAG/USD 1H  → price → % change → BUY/SELL badge
        │
        ├─► User selects asset+timeframe from dropdown → clicks Add
        │   addToWatchlist() → POST /api/watchlist
        │
        ├─► User clicks item → selectWatchlistItem(asset, timeframe)
        │   → closes modal → updates dashboard asset + timeframe
        │
        └─► User hovers item → trash icon appears → removeFromWatchlist()
            → DELETE /api/watchlist/{id}
```

---

### 2.6 Settings Flow

```
User clicks Settings gear icon
        │
        ▼
settingsModal opens (default: Profile tab)
        │
        ├─► Profile tab: name, email, timezone, trading experience → Save
        ├─► Preferences tab: theme toggle, default commodity, timeframe, risk %, chart style
        ├─► Data Sources tab: primary source selector, API key, refresh interval, data quality stats
        ├─► Notifications tab: Signal Alerts, Backtest Complete, Price Alerts, Email Reports, Model Retraining
        └─► Security tab: change password, enable 2FA, view sessions, danger zone (delete account)
```

---

### 2.7 Theme Toggle Flow

```
User clicks theme toggle (in Preferences or top navbar)
        │
        ▼
toggleTheme()
        │
        ├─► html.classList.toggle('dark')
        ├─► CSS overrides activate (html:not(.dark) selectors)
        └─► Toggle button icon flips (moon ↔ sun)
```

---

## 3. Frontend Guidelines

### 3.1 Architecture

- **Single HTML file** — all HTML, CSS, and JS in one `index_v4.html`
- **No build step** — served as-is by Flask `send_file()`
- **CDN dependencies only:**
  - Tailwind CSS (via CDN, config injected via `tailwind.config`)
  - Chart.js (via `cdn.jsdelivr.net`)
  - Font Awesome 6.4.0 (via Cloudflare CDN)
  - Google Fonts: Inter + JetBrains Mono

---

### 3.2 Color Palette

#### Dark Mode (Default — `html.dark`)

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#020617` (slate-950) | Page background |
| Surface | `#0f172a` (slate-900) | Cards, modals, inputs |
| Surface Elevated | `#1e293b` (slate-800) | Hover states, settings rows |
| Border | `#334155` (slate-700) | All borders |
| Text Primary | `#ffffff` | Headings, values |
| Text Secondary | `#cbd5e1` (slate-300) | Body text |
| Text Muted | `#94a3b8` (slate-400) | Labels, captions |
| Text Faint | `#64748b` (slate-500) | Placeholders |
| Gold Accent | `#fbbf24` | XAU, buttons, focus rings |
| Silver Accent | `#94a3b8` | XAG references |
| BUY Signal | `#22c55e` (green-500) | Buy badges, bullish candles, order blocks |
| SELL Signal | `#ef4444` (red-500) | Sell badges, bearish candles, order blocks |
| Neutral Signal | `#64748b` | Hold/neutral states |
| FVG Zone | `rgba(168, 85, 247, 0.1)` + purple border | Fair Value Gap zones |
| BOS Line | `rgba(251, 191, 36, 0.6)` | Break of Structure lines |
| CHoCH Line | `rgba(6, 182, 212, 0.6)` | Change of Character lines |
| Glass BG | `rgba(15, 23, 42, 0.85)` | Modal backdrop |

#### Light Mode (`html:not(.dark)`)

| Element | Override |
|---------|---------|
| `body` | `#f8fafc` background |
| `.bg-slate-900` | `#ffffff` |
| `.bg-slate-950` | `#f1f5f9` |
| `.bg-slate-800` | `#e2e8f0` |
| Text white | `#0f172a` |
| Text slate-300 | `#475569` |
| Text slate-400 | `#64748b` |
| Borders | `#cbd5e1` / `#e2e8f0` |

---

### 3.3 Typography

| Role | Font | Weight | Size |
|------|------|--------|------|
| UI / Body | Inter | 300–800 | 0.75rem–1.5rem |
| Prices / Metrics | JetBrains Mono | 400–700 | 0.75rem–1.5rem |
| Labels | Inter | 600 | `text-xs`, uppercase, tracking-wide |
| Signal badges | Inter | 700 | `text-[10px]` |

---

### 3.4 CSS Classes Reference

| Class | Purpose |
|-------|---------|
| `.glass` | `rgba(15,23,42,0.85)` + `backdrop-filter: blur(12px)` — modal backgrounds |
| `.gradient-border` | Gradient border via `::before` pseudo-element (green→teal→blue) |
| `.neural-pattern` | SVG dot grid background texture on `<body>` |
| `.scanline` | Animated horizontal line sweep — `position: fixed`, z-index 100 |
| `.ticker-tape` | `animation: ticker 40s linear infinite` — horizontal scroll |
| `.order-block-bullish` | Green gradient fill + left border — bullish OB |
| `.order-block-bearish` | Red gradient fill + left border — bearish OB |
| `.candle-green` | Green gradient + glow shadow — bullish candle body |
| `.candle-red` | Red gradient + glow shadow — bearish candle body |
| `.fvg-zone` | Purple fill + dashed top/bottom borders — Fair Value Gap |
| `.bos-line` | Gold dashed top border — Break of Structure |
| `.choch-line` | Cyan dotted top border — Change of Character |
| `.chart-grid` | CSS grid lines background — chart area |
| `.modal-overlay` | `rgba(0,0,0,0.8)` + `backdrop-filter: blur(4px)` |

---

### 3.5 Layout Structure

```
<body> [h-screen, flex, flex-col, overflow-hidden, neural-pattern]
│
├─ .scanline (fixed, z-100)
│
├─ #authModal (fixed, z-50) ← VISIBLE ON LOAD
│
├─ #settingsModal (fixed, z-50, hidden)
│
├─ #watchlistModal (fixed, z-50, hidden)
│
├─ #backtestModal (fixed, z-50, hidden)
│
├─ TICKER TAPE BAR (overflow-hidden, h-8)
│
├─ NAVBAR (flex, items-center, justify-between, px-4, py-3)
│   ├─ Logo
│   ├─ Asset Tabs [Gold | Silver]
│   ├─ Timeframe Tabs [5m | 15m | 1H | 4H | 1D]
│   ├─ Status Badges [WS | Model | API]
│   └─ Action Icons [Watchlist | Backtest | Settings | Logout]
│
└─ MAIN CONTENT (flex-1, grid grid-cols-3, gap-4, p-4, overflow-hidden)
    ├─ LEFT COLUMN (col-span-2)
    │   ├─ Signal Card
    │   ├─ Candlestick Chart + SMC Annotations
    │   └─ Model Info Panel
    │
    └─ RIGHT COLUMN (col-span-1)
        ├─ SHAP Feature Importance (Chart.js)
        ├─ Signal History Table
        └─ ETL Status Panel
```

---

### 3.6 JavaScript Architecture

All JS is vanilla, inline in a single `<script>` block at the bottom of `<body>`. Functions are organized by module:

```
Module 1 — Auth
├── switchAuthTab(tab)         Switch login/signup form
├── handleLogin()              POST /api/auth/login → hide modal
└── handleSignup()             POST /api/auth/register → auto-login

Module 2 — Settings
├── openSettingsModal()
├── closeSettingsModal()
└── switchSettingsTab(tab)     Show/hide settings content panels

Module 4 — Dashboard
├── initDashboard()            Fetch predictions, model info on login
├── selectAsset(asset)         Switch Gold/Silver
├── selectTimeframe(tf)        Switch 5m/15m/1H/4H/1D
├── updateSignalCard(data)     Render BUY/SELL badge + confidence
├── renderCandlesticks(data)   Draw CSS candles + SMC overlays
└── renderSHAPChart(data)      Chart.js horizontal bar chart

Module 5 — Watchlist
├── openWatchlistModal()
├── closeWatchlistModal()
├── addToWatchlist()           POST /api/watchlist
├── removeFromWatchlist(el)    DELETE /api/watchlist/{id}
└── selectWatchlistItem(a, tf) Switch asset+timeframe from watchlist

Module 8/9 — Backtest
├── openBacktestModal()
├── closeBacktestModal()
├── runBacktest()              POST /api/backtest/run + show progress
├── displayBacktestResults()   Render metrics + equity curve
└── exportReport(type)         Download CSV / PDF / JSON

Module 11 — Theme
└── toggleTheme()              Toggle html.dark class

Utilities
├── showToast(msg, type)       Toast notification
├── formatPrice(n)             Format to 2-5 decimal places
├── formatPercent(n)           Format with +/- prefix
└── getAuthToken()             Read JWT from localStorage
```

---

### 3.7 State Management

All state is managed with simple JS variables — no framework:

| Variable | Type | Purpose |
|----------|------|---------|
| `currentAsset` | `string` | `'gold'` or `'silver'` |
| `currentTimeframe` | `string` | `'15m'`, `'1h'`, etc. |
| `authToken` | `string` | JWT token from login |
| `currentUser` | `object` | `{email, username}` |
| `watchlistItems` | `array` | Local copy of watchlist |
| `isDarkMode` | `bool` | Current theme state |
| `backtestRunning` | `bool` | Prevent double-submit |
| `chartInstance` | `Chart` | Chart.js SHAP chart instance |

---

### 3.8 SMC Annotation System

V5 introduces CSS classes specifically for Smart Money Concepts chart overlays — the core differentiator of this project:

| SMC Concept | CSS Class | Visual |
|-------------|-----------|--------|
| Bullish Order Block | `.order-block-bullish` | Green gradient fill + left border |
| Bearish Order Block | `.order-block-bearish` | Red gradient fill + left border |
| Fair Value Gap | `.fvg-zone` | Purple fill + dashed top/bottom |
| Break of Structure | `.bos-line` | Gold dashed top border |
| Change of Character | `.choch-line` | Cyan dotted top border |
| Bullish Candle | `.candle-green` | Green gradient + green glow |
| Bearish Candle | `.candle-red` | Red gradient + red glow |

These are rendered as absolutely positioned `<div>` elements inside the chart container, overlaid on top of the candlestick visualization.

---

## 4. Implementation Plan

### 4.1 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| HTML Structure | ✅ Complete | All modals, navbar, layout present |
| CSS / Tailwind config | ✅ Complete | Dark/light mode, all SMC classes |
| Auth Modal (UI) | ✅ Complete | Login + signup forms |
| Settings Modal (UI) | ✅ Complete | All 5 tabs fully rendered |
| Watchlist Modal (UI) | ✅ Complete | Items, add/remove buttons |
| Backtest Modal (UI) | ✅ Complete | Config form + results display |
| Chart.js included | ✅ Complete | CDN loaded in `<head>` |
| JS functions | ⚠️ Partial | UI switching works; API calls need wiring |
| API integration | ❌ Missing | All `fetch()` calls need to point to `/api/*` |
| Auth token handling | ❌ Missing | JWT storage + Authorization header |
| Real chart rendering | ❌ Missing | Candlesticks are CSS mocks; need real data |
| SHAP Chart (Chart.js) | ❌ Missing | `chartInstance` not yet initialized |
| File exists at correct path | ❌ Missing | `frontend/public/index_v4.html` is empty |

---

### 4.2 Phase 1 — Deploy V5 File ✅ (Do First)

**Goal:** Fix the 500 crash. Get something visible at `http://localhost:5000`.

- [ ] Copy V5 content → `ml-signals/frontend/public/index_v4.html`
- [ ] Verify Flask serves it correctly at `/`
- [ ] Confirm auth modal appears on load
- [ ] Confirm no JS console errors on page load

**Time estimate:** 5 minutes

---

### 4.3 Phase 2 — Wire Authentication ⚡ (Critical)

**Goal:** Login/signup actually calls the Flask API and stores the JWT.

- [ ] `handleLogin()` → `fetch('/api/auth/login', {method: 'POST', body: JSON.stringify({email, password})})`
- [ ] On success: store JWT in `localStorage` → hide `#authModal` → call `initDashboard()`
- [ ] `handleSignup()` → `fetch('/api/auth/register', ...)` → auto-login on success
- [ ] Add `Authorization: Bearer <token>` header to all subsequent API calls
- [ ] On 401 response: show auth modal again (session expired)
- [ ] Show inline error messages in modal on failed login

**Time estimate:** 2–3 hours

---

### 4.4 Phase 3 — Wire Dashboard Data 📊

**Goal:** Signal card, model info, and ticker show real data from API.

- [ ] `initDashboard()` → fetch `GET /api/predictions/latest?asset=gold&limit=1`
- [ ] `updateSignalCard(data)` → render signal, confidence, price, timestamp
- [ ] Fetch `GET /api/models/info?asset=gold` → render model info panel
- [ ] Ticker tape → fetch latest prices and render in scrolling bar
- [ ] Asset/timeframe selector → refetch predictions on change
- [ ] WebSocket connection → `socket.io-client` or native WebSocket for live updates

**Time estimate:** 4–6 hours

---

### 4.5 Phase 4 — Wire Backtest 🧪

**Goal:** Backtest form submits to API and results are real (not hardcoded).

- [ ] `runBacktest()` → `fetch('/api/backtest/run', {method: 'POST', body: config})`
- [ ] Poll `GET /api/backtest/results` or use response directly
- [ ] Render real metrics (accuracy, Sharpe, drawdown, hit rate, profit factor)
- [ ] Replace hardcoded equity curve bars with Chart.js line chart using real data
- [ ] Replace hardcoded trade summary with real API response data
- [ ] `exportReport('csv')` → `fetch('/api/backtest/results')` → generate download

**Time estimate:** 4–5 hours

---

### 4.6 Phase 5 — Wire SHAP Chart 🧠

**Goal:** Feature importance chart shows real SHAP values from the model.

- [ ] `fetch('/api/shap/feature-importance')` on dashboard init
- [ ] Initialize `Chart.js` horizontal bar chart with real feature names + importances
- [ ] Destroy and re-create chart on asset change
- [ ] Handle case where SHAP values don't exist yet (show placeholder)

**Time estimate:** 2 hours

---

### 4.7 Phase 6 — Wire Watchlist & Settings 🔧

**Goal:** Watchlist persists to backend. Settings save to profile.

- [ ] `addToWatchlist()` → `POST /api/watchlist`
- [ ] `removeFromWatchlist()` → `DELETE /api/watchlist/{id}`
- [ ] Load existing watchlist on dashboard init → `GET /api/watchlist`
- [ ] Settings Profile "Save" → `PUT /api/profile`
- [ ] Settings Data Sources "Test Connection" → `GET /api/config`
- [ ] Settings Security "Update Password" → `PUT /api/auth/password`

**Time estimate:** 3 hours

---

### 4.8 Phase 7 — Candlestick Chart (Real Data) 📈

**Goal:** Replace CSS mock candles with real OHLCV data from API.

- [ ] Fetch recent OHLCV data from predictions endpoint (includes open/high/low/close)
- [ ] Render real candles dynamically as `<div>` elements with correct heights
- [ ] Position SMC annotations (OB, FVG, BOS, CHoCH) from API response fields
- [ ] Add timeframe selector → refetch + re-render on change

**Time estimate:** 6–8 hours (most complex phase)

---

### 4.9 Phase 8 — Docker Integration 🐳

**Goal:** V5 runs correctly inside Docker without any local setup.

- [ ] Confirm `frontend/public/index_v4.html` is copied into Docker image
- [ ] Confirm Flask `send_file()` path resolves correctly inside container
- [ ] API calls in JS use relative paths (`/api/...`) — no hardcoded `localhost:5000`
- [ ] WebSocket URL from env var (`VITE_WS_URL` equivalent)
- [ ] Write `Dockerfile` + `docker-compose.yml` for full stack

**Time estimate:** 2–3 hours

---

### 4.10 Priority Order

```
Phase 1  →  Deploy file (5 min)          — Fixes the 500 crash immediately
Phase 2  →  Authentication (3 hrs)       — Nothing works without a valid JWT
Phase 3  →  Dashboard data (6 hrs)       — Core value of the product
Phase 4  →  Backtest (5 hrs)             — Key FYP evaluation feature
Phase 5  →  SHAP chart (2 hrs)           — ML explainability showcase
Phase 6  →  Watchlist + Settings (3 hrs) — Polish + completeness
Phase 7  →  Real candlestick chart (8h)  — Most complex, do last
Phase 8  →  Docker (3 hrs)               — Deployment
```

**Total estimated effort:** ~30–35 hours of focused development

---

### 4.11 Known Issues in V5 (To Fix During Implementation)

| Issue | Severity | Fix |
|-------|----------|-----|
| All API calls are placeholder `console.log` | 🔴 Critical | Replace with real `fetch()` calls in each phase |
| Candlestick chart is CSS mock, not real data | 🟡 Medium | Phase 7 |
| Equity curve is hardcoded HTML divs | 🟡 Medium | Replace with Chart.js in Phase 4 |
| Watchlist items are hardcoded HTML | 🟡 Medium | Phase 6 |
| SHAP chart has no `Chart.js` initialization | 🟡 Medium | Phase 5 |
| JWT not stored or sent with requests | 🔴 Critical | Phase 2 |
| No error handling on fetch failures | 🟡 Medium | Add try/catch + toast notifications |
| Theme toggle doesn't persist on reload | 🟢 Low | `localStorage.setItem('theme', ...)` |
| Timezone in profile is hardcoded | 🟢 Low | Phase 6 |
| Signal history table is hardcoded | 🟡 Medium | Phase 3 |
