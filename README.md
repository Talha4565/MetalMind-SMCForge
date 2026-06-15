# MetalMind SMCForge

> AI-powered trading signals for Gold (XAU/USD) and Silver (XAG/USD) using Smart Money Concepts and XGBoost machine learning.

## Overview

MetalMind SMCForge is a full-stack ML trading system that combines Smart Money Concepts (SMC) with XGBoost machine learning to generate buy/sell/hold signals for precious metals. The system features explainable AI (SHAP), automated backtesting, live price feeds, and email alerts.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend   │────▶│   Flask API  │────▶│  XGBoost    │
│   Next.js    │     │   + SocketIO │     │  Models      │
│   Dashboard  │     │              │     │  (Gold/Silver)│
└─────────────┘     └──────┬───────┘     └──────┬──────┘
                           │                     │
                    ┌──────▼───────┐     ┌──────▼──────┐
                    │   PostgreSQL │     │  CSV Data   │
                    │   Database   │     │  (2004-Now) │
                    └──────────────┘     └──────┬──────┘
                                                │
                                       ┌────────▼────────┐
                                       │  ETL Pipeline   │
                                       │  (yfinance →    │
                                       │   CSV → Train)  │
                                       └─────────────────┘
```

## Features

- **ML Predictions**: XGBoost classifier with 90 features (volume, SMC, multi-timeframe)
- **SHAP Explainability**: Every prediction includes top contributing features
- **Automated Backtesting**: Walk-forward backtest with slippage, commission, TP/SL
- **Live Price Feeds**: Real-time gold/silver prices via Yahoo Finance
- **Email Alerts**: BUY/SELL signals with >70% confidence
- **Prediction Logging**: Every prediction logged with actual outcomes
- **Dark/Light Mode**: Theme toggle with trading terminal aesthetic
- **TradingView Charts**: Embedded live candlestick charts

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Run
```bash
git clone https://github.com/Talha4565/MetalMind-SMCForge.git
cd MetalMind-SMCForge
docker compose up -d
```

### Access
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:5000/api/health
- **Database**: localhost:5432 (postgres/postgres)

## Project Structure

```
ml-signals/
├── api/                    # Flask API + SocketIO
│   ├── app/main.py         # Main API endpoints
│   ├── app/auth.py         # Authentication
│   ├── app/shap_cache.py   # SHAP computation cache
│   └── Dockerfile
├── config/                 # Configuration
│   └── settings.py         # All project settings
├── data/                   # Data loaders
│   └── loaders.py          # Multi-timeframe data loading
├── etl/                    # ETL Pipeline
│   ├── extractors/
│   │   ├── yfinance_extractor.py  # Live data from Yahoo Finance
│   │   └── csv_extractor.py       # CSV data extraction
│   ├── loaders/
│   │   └── csv_append_loader.py   # Append data to CSVs
│   ├── pipeline.py         # ETL orchestrator
│   ├── scheduler.py        # APScheduler-based scheduling
│   ├── alerts.py           # Email alert service
│   └── prediction_logger.py # Prediction logging
├── features/               # Feature engineering
│   ├── pipeline.py         # Full feature pipeline
│   ├── labels.py           # Target label generation
│   └── smc_features.py     # Smart Money Concepts features
├── models/                 # ML models
│   ├── train_enhanced.py   # XGBoost training pipeline
│   ├── retrain.py          # Automated retraining
│   └── enhanced_15m.pkl    # Trained gold model
├── backtesting/            # Backtesting engine
│   └── engine.py           # Walk-forward backtest
├── Gold Dataset/           # Gold OHLCV data (2004-2026)
├── Silver Dataset/         # Silver OHLCV data (2020-2026)
├── reports/
│   ├── training_logs/      # Model training metrics
│   ├── predictions/        # Prediction logs
│   └── backtest_results/   # Backtest results
├── frontend-next/          # Next.js dashboard
│   ├── src/app/            # Pages (dashboard, auth, backtest)
│   ├── src/components/     # UI components
│   └── src/lib/            # API client, hooks, utils
├── docker-compose.yml      # Docker orchestration
├── run_pipeline.py         # ETL + training pipeline CLI
└── start_api.py            # API server entry point
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/predictions/latest` | GET | Latest ML predictions (with SHAP) |
| `/api/market/price` | GET | Live price from Yahoo Finance |
| `/api/shap/feature-importance` | GET | SHAP feature importance |
| `/api/backtest/run` | POST | Run backtest |
| `/api/backtest/results` | GET | Get backtest results |
| `/api/auth/login` | POST | User login |
| `/api/auth/register` | POST | User registration |
| `/api/watchlist` | GET/POST/DELETE | Watchlist management |

## ML Pipeline

### Model Training
```bash
# Train gold model (90 features, Optuna tuning)
python run_pipeline.py --mode retrain --asset gold

# Train silver model
python run_pipeline.py --mode retrain --asset silver
```

### Automated Pipeline
```bash
# Backfill historical data
python run_pipeline.py --mode backfill --asset gold

# Fetch latest candles
python run_pipeline.py --mode update --asset gold

# Full pipeline (fetch + retrain)
python run_pipeline.py --mode full --asset gold

# Continuous scheduler (15min updates + 24h retrain)
python run_pipeline.py --mode schedule
```

### Pipeline Architecture
1. **Every 15 min**: yfinance fetches 5m/15m/30m/1h candles → appends to CSVs
2. **Every 24 hours**: Model retrains on full dataset (2004 → today) → metrics logged
3. **Every prediction**: Logged to `reports/predictions/` with SHAP values
4. **BUY/SELL > 70%**: Email alert sent

## Backtest Results

| Metric | Gold | Silver |
|--------|------|--------|
| Total Return | +497% | +30% |
| Win Rate | 49.8% | 50.0% |
| Profit Factor | 1.67 | 1.67 |
| Max Drawdown | -7.58% | -9.96% |
| Sharpe Ratio | 3.58 | 3.96 |

## Email Alerts

Set environment variables in `.env`:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=recipient@gmail.com
```

Alerts are sent when model predicts BUY/SELL with confidence > 70%.

## Tech Stack

- **Frontend**: Next.js 16, React, Tailwind CSS, shadcn/ui
- **Backend**: Flask, Flask-SocketIO, SQLAlchemy
- **ML**: XGBoost, Optuna, SHAP, scikit-learn
- **Data**: yfinance, pandas, numpy
- **Database**: PostgreSQL 15
- **Infrastructure**: Docker, Docker Compose
- **Scheduling**: APScheduler

## License

MIT
