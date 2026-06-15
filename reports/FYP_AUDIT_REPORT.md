# MetalMind SMCForge - Final Year Project (FYP) Implementation Audit

**Audit Date:** June 16, 2026  
**Auditor:** Code Audit System  
**Project:** MetalMind SMCForge - Explainable AI-Powered Commodity Forecasting Platform  
**Scope:** Document actual repository implementation and alignment with available code

---

## Executive Summary

This report documents the actual system architecture, implemented modules, and documentation gaps found in the `ml-signals` repository. It is a factual implementation audit based on repository contents, without assuming or evaluating unsupported project claims.

Key observations:
- The repository contains a functional Flask backend, ETL pipeline support, SHAP explainability, backtesting, and user profile/watchlist services.
- Several implemented features are present in code but not fully described in existing documentation.
- The primary recommended work is documentation alignment and clearer descriptions of existing implementation details.

---

## 1. Technology Stack

### 1.1 Frontend

| Component | Actual Version | Notes |
|-----------|----------------|-------|
| Next.js | 16.2.6 | Frontend application in `frontend-next` |
| React | 19.2.4 | Latest React version used in the frontend |
| Tailwind CSS | v4 | Configured in `frontend-next` |
| TradingView Lightweight Charts | 5.2.0 | Used for financial chart rendering |
| NextAuth.js | 4.24.14 | Authentication and session management |
| React Query | 5.100.9 | Data fetching and caching |
| shadcn/ui | 4.7.0 | UI component library |
| socket.io-client | 4.8.3 | Real-time event client support |

### 1.2 Backend

| Component | Actual Version | Notes |
|-----------|----------------|-------|
| Flask | 3.0.0 | Backend framework |
| SQLAlchemy | 2.0.23 | ORM for application data |
| XGBoost | 2.0.3 | Model training and inference |
| SHAP | 0.44.0 | Explainability analysis |
| Flask-SocketIO | 5.x | Real-time updates and Socket.IO support |
| flask_limiter | present | API rate limiting |
| flask_compress | present | Response compression |

---

## 2. Backend Architecture

### 2.1 Core Backend Files

- `api/app/main.py`: Flask application setup, middleware, CORS and security headers, Socket.IO initialization, blueprint registration, and model manager.
- `api/app/auth.py`: Authentication and JWT handling.
- `api/app/database.py`: SQLAlchemy initialization and models.
- `api/app/etl_routes.py`: ETL control endpoints.
- `api/app/profile.py`: Profile, password, and settings endpoints.
- `api/app/watchlist.py`: Watchlist CRUD endpoints.
- `api/app/shap_cache.py`: SHAP caching support.
- `api/app/middleware/`: Error handling and request middleware.

### 2.2 Data Storage Strategy

- Historical market data lives in CSV files under `/Gold Dataset/` and `/Silver Dataset/`.
- Model artifacts are stored under `models/processed/`.
- Backtest results are written as JSON under `reports/backtest_results/`.
- User and session data are managed through SQLAlchemy and can be configured for SQLite or PostgreSQL.

---

## 3. ETL Pipeline

### 3.1 ETL API Endpoints

Implemented ETL management endpoints in `api/app/etl_routes.py`:
- `POST /api/etl/run`
- `GET /api/etl/status`
- `GET /api/etl/schedule`
- `POST /api/etl/schedule/start`
- `POST /api/etl/schedule/stop`
- `GET /api/etl/metrics`
- `GET /api/etl/health`

### 3.2 Pipeline Components

The `etl/` directory contains:
- `extractors/`: data extraction logic.
- `loaders/`: data loading utilities.
- `transformers/`: feature engineering and transformation logic.
- `scheduler.py`: recurring execution scheduler.
- `factory.py`: pipeline assembly utilities.
- `config.py`: ETL configuration management.

### 3.3 Recommended Documentation

- Add a dedicated ETL architecture section describing pipeline stages and schedule management.
- Document how gold and silver pipelines are created and executed.
- Describe the meaning of metrics and health status endpoints.

---

## 4. Feature Engineering and Models

### 4.1 Feature Engineering

Feature engineering is implemented through the `features/` package and includes a mix of technical indicators and smart money concept features such as:
- RSI, EMA, ATR, MACD, Bollinger Bands
- Fair value gaps, break of structure, liquidity sweeps, order blocks
- Multi-timeframe feature support across 5m, 15m, 30m, and 1h data

### 4.2 Model Artifacts

The repository includes model artifacts for gold and silver:
- `models/processed/enhanced_15m.pkl`
- `models/processed/silver_model_enhanced.pkl`
- `models/processed/silver_model_optimized.pkl`

### 4.3 Training and Inference

- `models/train_enhanced.py` implements enhanced model training.
- `run.py --mode train` invokes training with configurable timeframe and Optuna trials.
- `api/app/main.py` performs lazy model loading for inference.
- `run.py --mode explain` uses SHAP utilities for explainability analysis.

---

## 5. SHAP Explainability

### 5.1 Implementation

Implemented explainability support includes:
- `explainability/shap_analyzer.py` for SHAP computation and plot generation.
- `api/app/shap_cache.py` for caching computed SHAP results.
- Backend endpoints for SHAP outputs.

### 5.2 Observations

- SHAP values are computed in the backend and can be returned to consumers.
- The code supports static SHAP plot generation and cached retrieval.
- The system separates SHAP computation from frontend rendering.

### 5.3 Recommended Documentation

- Document the SHAP computation workflow and cache usage.
- Clarify output formats available to the frontend or external consumers.
- Describe which SHAP plots are generated and how they are used.

---

## 6. Backtesting

### 6.1 Implementation

The backtesting engine is implemented in `backtesting/engine.py` and includes:
- Long-only trade simulation with entry on the next bar.
- Slippage and commission handling.
- Take-profit and stop-loss exits.
- Timeout exits after a maximum bar count.
- Equity curve generation and trade-level metrics.

### 6.2 Execution Path

- `run.py --mode backtest` loads the trained model, prepares test data, and runs the backtest engine.
- Backtest results are saved as JSON under `reports/backtest_results/`.

### 6.3 Recommended Documentation

- Document the backtesting workflow, inputs, and output artifacts.
- Describe supported asset/timeframe combinations.
- Explain how the backtest engine calculates metrics and writes results.

---

## 7. User Profile and Watchlist

### 7.1 Profile API

The profile module supports:
- Retrieving user profile information.
- Updating user email with OTP verification.
- Changing passwords with strength validation.
- Managing user settings such as theme, default asset, timeframe, and notifications.

### 7.2 Watchlist API

The watchlist module supports:
- CRUD operations for watchlist items.
- Reordering entries.
- Item metadata such as notifications, alert thresholds, and notes.

### 7.3 Design Notes

- The current implementation uses a single `WatchlistItem` collection per user.
- Multiple named watchlists are not implemented in the current codebase.
- If this is intentional, document the design decision explicitly.

---

## 8. Authentication and Security

### 8.1 Implemented Features

- JWT-based authentication.
- Password hashing via bcrypt.
- Email OTP verification.
- TOTP 2FA support in profile flows.
- API rate limiting via `flask_limiter`.
- Security headers and request size limits in `api/app/main.py`.

### 8.2 Recommended Documentation

- Describe authentication flow and token management.
- Document password and OTP policies.
- Add a security summary for the final project report.

---

## 9. API Surface

### 9.1 Core Endpoints

| Feature | Endpoint | Notes |
|---------|----------|-------|
| ETL control | `/api/etl/run` | Trigger pipeline execution |
| ETL status | `/api/etl/status` | Check pipeline status |
| ETL scheduler | `/api/etl/schedule` | View scheduled jobs |
| Profile | `/api/profile` | Retrieve profile data |
| Password | `/api/profile/password` | Change password |
| Settings | `/api/profile/settings` | Manage user preferences |
| Watchlist | `/api/watchlist/*` | Manage watchlist entries |
| SHAP explainability | `/api/shap/feature-importance` | Feature importance outputs |
| Backtesting | `/api/backtest/run` | Execute backtest |

### 9.2 Additional Capabilities

- Socket.IO support for real-time event handling.
- Cached explainability results.
- Lazy model loading for efficient inference.
- Response compression and security-focused middleware.

---

## 10. Documentation Gaps

### 10.1 Recommended Updates

- Add a dedicated section describing the ETL pipeline and scheduler.
- Document backtesting input/output workflows and artifact locations.
- Document the SHAP explainability workflow and output formats.
- Describe the frontend technology stack and major dependencies.
- Explain the purpose of utility scripts such as `run.py`, `run_etl.py`, `debug_api.py`, and `verify_fixes.py`.
- Document the simplified watchlist design and user settings model.
- Clarify the current state of automated testing and planned coverage.

---

## 11. Dataset Inventory

### 11.1 Data Files

- `Gold_5m_Candlestick.csv`
- `Gold_15m_Candlestick.csv`
- `Gold_30m_Candlestick.csv`
- `Gold_1h_Candlestick.csv`
- `Silver_5m_Candlestick.csv`
- `Silver_15m_Candlestick.csv`
- `Silver_30m_Candlestick.csv`
- `Silver_1h_Candlestick.csv`

### 11.2 Observations

- Data is stored as raw intraday OHLCV CSV files.
- Timeframes include 5 minutes, 15 minutes, 30 minutes, and 1 hour.
- These files support feature engineering, model training, and backtesting.

---

## 12. Deployment Notes

### 12.1 Repository Deployment Support

- `Dockerfile` and `docker-compose.yml` enable containerized deployment.
- `api/Dockerfile` provides backend container configuration.
- `frontend-next/Dockerfile` provides frontend build/runtime configuration.
- `run.py` serves as a local CLI orchestrator for dev workflows.

### 12.2 Recommended Documentation

- Clarify development and production deployment requirements.
- Document database configuration options for SQLite and PostgreSQL.
- Add guidance for running containers and local development flows.

---

## 13. Conclusion

The `ml-signals` repository contains a solid implemented foundation for an explainable commodity forecasting platform. The most important remaining work is to align the written documentation with actual repository behavior and to document implemented features clearly.

This report is intended as a repository-focused implementation audit, not as a claim verification against an external FYP document.

---

## 14. Appendix: Implementation Inventory

- `api/app/main.py`: Flask app bootstrapping, Socket.IO, middleware, blueprint registration.
- `api/app/etl_routes.py`: Managed ETL endpoints.
- `api/app/profile.py`: Profile, password, and settings API.
- `api/app/watchlist.py`: Watchlist CRUD support.
- `api/app/shap_cache.py`: SHAP result caching.
- `backtesting/engine.py`: Backtesting engine and result generation.
- `run.py`: CLI for API, training, backtesting, explainability, and full pipeline.
- `etl/`: ETL extractors, loaders, transformers, scheduler, and factory.
- `explainability/`: SHAP analysis and plot utilities.
- `models/processed/`: Trained model artifacts.
- `reports/backtest_results/`: Generated backtest result JSON files.
