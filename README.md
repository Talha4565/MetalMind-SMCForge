# MetalMind SMCForge

<p align="center">
  <strong>AI-powered trading signals for Gold & Silver.</strong><br/>
  XGBoost + Smart Money Concepts + SHAP explainability.<br/>
  20 years of tick data. Every prediction explained.
</p>

<p align="center">
  <a href="#deploy">Deploy</a> ·
  <a href="#features">Features</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#api">API</a> ·
  <a href="#ml-pipeline">ML Pipeline</a> ·
  <a href="#performance">Performance</a>
</p>

---

## Why MetalMind?

Most trading signal services give you a number. We give you the *why*. Every BUY, SELL, or HOLD signal comes with SHAP feature attribution showing exactly which market forces drove the prediction — order blocks, liquidity sweeps, volatility patterns — in plain English.

| | MetalMind | Generic Signal Services |
|---|---|---|
| **Explainability** | SHAP on every signal | Black box |
| **Training Data** | 20 years tick data | Undisclosed |
| **Model** | XGBoost with Optuna tuning | Unknown |
| **Assets** | Gold + Silver, separate tuned models | Usually one-size-fits-all |
| **Self-hosted** | Docker, 5 containers, your hardware | Cloud-only |
| **Real-time** | WebSocket streaming + MT5 live prices | Delayed |

---

## Features

### ML Engine
- **Dual XGBoost models** — Gold (82.7% accuracy, 100 features) and Silver (73.9%, 89 features), each with independently tuned hyperparameters via Optuna Bayesian optimization
- **Smart Money Concepts** — Order blocks, fair value gaps, liquidity sweeps, breaker blocks, and multi-timeframe structure analysis
- **Walk-forward validation** — 4-fold out-of-sample testing. 81.6% mean accuracy. No look-ahead bias
- **Automated daily retraining** — GitHub Actions pipeline retrains both models every 24 hours on fresh data

### Explainability
- **Per-prediction SHAP** — Every signal includes feature contribution breakdown. Know *why* the model said BUY
- **Ablation verified** — SMC features add +4.2pp accuracy over classical technicals alone (McNemar p=0.008, statistically significant)
- **Global feature importance** — Understand which features drive the model across the entire dataset

### Trading Infrastructure
- **Real-time MT5 integration** — Live OHLCV bar streaming across 4 timeframes (5m/15m/30m/1h). Completed bars appended to training datasets automatically
- **Automated backtesting** — Walk-forward backtest with configurable slippage, commission, take-profit/stop-loss. 1,674 gold trades analyzed
- **Live price ticker** — Bid/ask spread, real-time updates every 5 seconds from MT5
- **Trade log** — Every prediction logged with actual outcome tracking. Profit factor, win rate, Sharpe ratio computed

### Platform
- **Dedicated gold & silver dashboards** — Separate pages with asset-specific visual identity. Gold foil aesthetic for XAU/USD, platinum for XAG/USD
- **Bloomberg-terminal design** — Dark, data-dense, monospace-first. Built for traders who live in numbers
- **WebSocket streaming** — Real-time signal updates without polling
- **NextAuth.js authentication** — JWT-based auth with 2FA/TOTP support, session management, and role-based access
- **Responsive** — Full dashboard on desktop, adapted layouts on tablet and mobile

### DevOps
- **Docker Compose** — 5 containers (API, Frontend, PostgreSQL, ChromaDB, ETL). One command deploy
- **GitHub Actions CI/CD** — Automated daily retrain + model commit. Green pipeline: 5+ consecutive successful runs
- **Auto-start MT5 script** — Windows host runs bar updater on boot via Task Scheduler. Zero manual intervention
- **Health monitoring** — Pipeline health dashboard, data freshness checks, ChromaDB signal memory status
- **Rate limiting** — Per-endpoint rate limits prevent abuse. Watchlist: 60/min, Backtest: 6/hr, Auth: 10/min

---

## Deploy

### Prerequisites
- Docker & Docker Compose
- Windows host with MetaTrader 5 (for live prices — optional, mock data works without it)
- Git

### One-command deploy
```bash
git clone https://github.com/Talha4565/MetalMind-SMCForge.git
cd MetalMind-SMCForge
docker compose up -d
```

### Start the MT5 bar updater (Windows host)
```bash
pip install MetaTrader5 pandas
python scripts/mt5_bar_updater.py --backfill-max 500
```

### Access
| Service | URL |
|---------|-----|
| **Gold Dashboard** | http://localhost:3000/dashboard/gold |
| **Silver Dashboard** | http://localhost:3000/dashboard/silver |
| **Landing Page** | http://localhost:3000 |
| **API Health** | http://localhost:5000/api/health |
| **Database** | localhost:5432 (postgres/postgres) |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Windows Host (MT5)                        │
│  mt5_bar_updater.py ──→ OHLCV bars ──→ CSV Datasets          │
│                      ──→ bid/ask    ──→ mt5_prices.json      │
└──────────────────────────┬───────────────────────────────────┘
                           │ (mounted volume)
┌──────────────────────────▼───────────────────────────────────┐
│                     Docker Environment                        │
│                                                               │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │ Frontend │   │ Flask API│   │ PostgreSQL│   │ ChromaDB │  │
│  │ Next.js  │──▶│ :5000    │──▶│   :5432   │   │  :8100   │  │
│  │ :3000    │   │ SocketIO │   │  Users,   │   │  Signal  │  │
│  │ Dashboard│   │ JWT Auth │   │  Watchlist│   │  Memory  │  │
│  └──────────┘   └────┬─────┘   └──────────┘   └──────────┘  │
│                      │                                        │
│               ┌──────▼──────┐                                 │
│               │  ETL + ML   │                                 │
│               │  XGBoost    │                                 │
│               │  SHAP       │                                 │
│               │  Backtest   │                                 │
│               └─────────────┘                                 │
└──────────────────────────────────────────────────────────────┘
```

**Data flow**: MT5 → CSV datasets → Feature engineering (100 columns) → XGBoost prediction → SHAP explanation → WebSocket stream → Dashboard

---

## API

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | — | System health (DB, filesystem, models) |
| `/api/auth/register` | POST | — | Create account (OTP verification) |
| `/api/auth/login` | POST | — | JWT login (2FA supported) |
| `/api/auth/verify-email` | POST | — | Verify email with OTP |
| `/api/predictions/latest?asset=gold` | GET | — | Latest prediction with SHAP values |
| `/api/predictions/history?days=7` | GET | — | Prediction history |
| `/api/market/price?asset=gold` | GET | — | Live bid/ask from MT5 |
| `/api/shap/feature-importance?asset=gold` | GET | JWT | Global SHAP feature importance |
| `/api/backtest/run` | POST | JWT | Run walk-forward backtest |
| `/api/backtest/results` | GET | JWT | Historical backtest results |
| `/api/backtest/export?format=csv` | GET | JWT | Export backtest report |
| `/api/watchlist` | GET/POST | JWT | Manage personal watchlist |
| `/api/watchlist/symbols` | GET | — | Available trading symbols |
| `/api/pipeline/status` | GET | — | Pipeline health and freshness |
| `/api/pipeline/details` | GET | — | Full pipeline detail (ETL, features, training) |
| `/api/orchestrator/status` | GET | — | Orchestrator health (MT5, ChromaDB, retrain) |
| `/api/profile` | GET/PUT | JWT | View and update profile |
| `/api/profile/password` | PUT | JWT | Change password |
| `/api/profile/settings` | GET/PUT | JWT | Preferences (theme, timeframe, asset) |
| `/api/profile/2fa/setup` | GET | JWT | TOTP 2FA setup with QR code |
| `/api/profile/2fa/enable` | POST | JWT | Enable 2FA |
| `/api/profile/2fa/disable` | POST | JWT | Disable 2FA |
| `/api/profile/avatar` | PUT | JWT | Upload profile picture |
| `/api/profile/delete` | DELETE | JWT | Delete account |
| `/api/models/info?asset=gold` | GET | JWT | Model metadata (version, size, features) |

---

## ML Pipeline

### Training
```bash
# Retrain with Optuna hyperparameter optimization
python run_pipeline.py --mode retrain --asset gold --trials 30

# Update data from MT5
python run_pipeline.py --mode update --asset gold

# Full pipeline (update + retrain)
python run_pipeline.py --mode full --asset gold
```

### Automated daily pipeline (GitHub Actions)
1. Check data freshness (MT5 cache ≤ 25h old)
2. Retrain gold model with 30 Optuna trials
3. Retrain silver model with 30 Optuna trials
4. Commit updated models back to repository
5. Triggered: 03:00 UTC daily + manual dispatch

### Feature Engineering Pipeline
- **20 raw columns** (OHLCV × 4 timeframes) → **100 features**
- Volume microstructure, SMC concepts (FVG, order blocks, breaker blocks, liquidity sweeps)
- Multi-timeframe: 30m and 1h structure projected onto 15m primary
- Session killzone features: Asia, London, New York

---

## Performance

Real benchmarks from the live API (July 2026):

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| POST /auth/login | 10ms | 336ms | 379ms |
| GET /api/health | 9ms | 12ms | 19ms |
| GET /shap/global | 9ms | 11ms | 15ms |
| GET /api/market/price | 16ms | 34ms | 35ms |
| GET /api/pipeline/status | 232ms | 298ms | 317ms |
| POST /forecast/gold | 4,761ms | 6,538ms | 11,806ms |
| POST /forecast/silver | 4,483ms | 7,394ms | 7,983ms |

> Forecast endpoints include model inference + SHAP computation on 100-feature input. Warm-up cache available after first call. See `reports/performance_benchmark.json` for full data.

### Model Accuracy

| Metric | Gold | Silver |
|--------|------|--------|
| Training Accuracy | 82.7% | 73.9% |
| Walk-Forward (4-fold) | 81.6% | — |
| AUC-ROC | 0.74 | 0.73 |
| Backtest Win Rate | 41.3% | 50.0% |
| Backtest Profit Factor | 1.44 | 1.67 |

### Security Scan
Bandit: 0 High · 2 Medium · 9 Low. See `reports/security_scan.json`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **ML** | XGBoost 2.0.3, SHAP 0.44.0, Optuna 3.5.0, scikit-learn |
| **Backend** | Flask 3.0, Flask-SocketIO, Flask-JWT-Extended, SQLAlchemy 2.0 |
| **Frontend** | Next.js 16, React 19, Tailwind CSS, TanStack Query, Zod |
| **Database** | PostgreSQL 15 (prod), SQLite (dev fallback), Alembic migrations |
| **Vector Memory** | ChromaDB (signal pattern storage, similarity search) |
| **Real-time** | Socket.IO WebSocket, MT5 Python API |
| **Infrastructure** | Docker Compose, GitHub Actions, Windows Task Scheduler |
| **Monitoring** | Pipeline health dashboard, data freshness alerts, consecutive failure tracking |

---

## Testing

| Layer | Tests | Pass Rate |
|-------|-------|-----------|
| Unit (pytest) | 245 | 100% |
| E2E (Playwright) | 9 scenarios | 100% |
| Smoke | 38 health/API checks | 100% |
| Security (Bandit) | 11 findings | 0 critical/high |
| Performance (NFR) | 10 endpoints benchmarked | See above |

Handbook test cases TC-001 through TC-014 mapped to source code in `reports/handbook_test_cases_TC001-TC014.md`.

---

## License

MIT © MetalMind SMCForge
