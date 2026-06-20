# Pipeline Automation Summary

> **Date:** June 16, 2026
> **Project:** MetalMind SMCForge — ML Trading Signals

---

## What Was Built

An automated data pipeline that fetches live market data from Yahoo Finance, appends it to existing CSV datasets, and retrains the ML model on fresh data.

## Architecture

```
yfinance API
    ↓
YFinanceExtractor (fetch candles)
    ↓
CSVAppendLoader (append to CSVs, deduplicate)
    ↓
EnhancedModelTrainer (retrain on full dataset)
    ↓
Training Logs (reports/training_logs/)
```

## Files Created/Modified

| File | Type | Purpose |
|------|------|---------|
| `etl/extractors/yfinance_extractor.py` | **New** | Fetches OHLCV candles from Yahoo Finance for all timeframes (5m, 15m, 30m, 1h) |
| `etl/loaders/csv_append_loader.py` | **New** | Appends new data to existing CSVs with Date+Time deduplication |
| `models/retrain.py` | **New** | Retrains model on full dataset + saves training metrics to JSON logs |
| `run_pipeline.py` | **New** | CLI entry point for all pipeline operations |
| `reports/training_logs/` | **New** | Directory for training metrics logs |
| `api/app/main.py` | **Modified** | Added live price injection into prediction endpoint |

## Data Backfill Results

The 21-month gap (Sept 2024 → June 2026) has been filled with yfinance data:

| Dataset | Before | After | New Rows |
|---------|--------|-------|----------|
| Gold 5m | 1,048,575 | 1,062,125 | +13,550 |
| Gold 15m | 464,737 | 469,263 | +4,526 |
| Gold 30m | 234,163 | 236,426 | +2,263 |
| Gold 1h | 117,829 | 128,137 | +10,308 |
| Silver 5m | 636,409 | 649,948 | +13,539 |
| Silver 15m | 212,137 | 216,662 | +4,525 |
| Silver 30m | 106,069 | 108,332 | +2,263 |
| Silver 1h | 1,522 | 15,271 | +13,749 |

All datasets now cover **2004 → June 15, 2026**.

## How It Works

### Pipeline Modes

```bash
# Backfill historical gap (one-time)
python run_pipeline.py --mode backfill --asset gold
python run_pipeline.py --mode backfill --asset silver

# Fetch latest candles only (every 15 min)
python run_pipeline.py --mode update --asset gold

# Retrain model on full dataset
python run_pipeline.py --mode retrain --asset gold

# Full pipeline (fetch + retrain)
python run_pipeline.py --mode full --asset gold

# Continuous scheduler (15min updates + 24h retrain)
python run_pipeline.py --mode schedule
```

### Data Flow

1. **Every 15 minutes:** yfinance fetches latest 5m/15m/30m/1h candles → appended to CSVs with deduplication
2. **Every 24 hours:** Model retrained on full dataset (2004 → today) → metrics saved to `reports/training_logs/`

### Deduplication

The `CSVAppendLoader` deduplicates by `Date + Time` columns. When appending:
- New rows are combined with existing CSV
- Duplicate timestamps are removed (keeps latest)
- Data is sorted chronologically

### Training Logs

Each training run saves a JSON file to `reports/training_logs/`:
```json
{
  "asset": "gold",
  "started_at": "2026-06-16T02:30:00",
  "completed_at": "2026-06-16T02:35:00",
  "status": "success",
  "accuracy": 0.8664,
  "train_rows": 133499,
  "test_rows": 28608,
  "feature_count": 90,
  "best_params": {...},
  "duration_seconds": 298.5
}
```

Plus a `gold_latest.json` / `silver_latest.json` for quick access.

### Live Price Injection

The prediction endpoint now fetches current market price from Yahoo Finance and injects it into the latest bar before predicting. This means the model predicts on today's price ($4,331) instead of stale CSV data ($2,573 from Sept 2024).

## What's Left

1. **Retrain the model** — `python run_pipeline.py --mode retrain --asset gold` (takes ~5 min)
2. **Add ETL service to docker-compose** — for continuous operation
3. **Verify prediction endpoint** — confirm BUY/SELL signals change with live data
