# MetalMind SMCForge — Interaction Sequence Diagram

## Prediction Flow (GET /api/predictions/latest)

```mermaid
sequenceDiagram
    participant Browser as Next.js Client
    participant API as Flask API<br/>(main.py:694)
    participant Cache as PredictionCache<br/>(TTL: 300s)
    participant Data as CSV Data Layer<br/>(loaders.py)
    participant Features as Feature Pipeline<br/>(100 features)
    participant Model as XGBoost Model<br/>(enhanced_15m.pkl)
    participant SHAP as SHAP TreeExplainer
    participant ActiveTrades as ActiveTradeTracker
    participant Logger as PredictionLogger<br/>(JSONL + ChromaDB)

    Note over Browser,Logger: === REQUEST CYCLE (every 60s via TanStack Query) ===

    Browser->>API: GET /api/predictions/latest?asset=gold
    Note over API: Rate limited: 100 req/min<br/>Public endpoint (no JWT required)

    API->>API: Validate asset param (gold|silver)

    API->>Model: model_manager.get_or_load_model(asset)
    Note over Model: Lazy-loaded from disk<br/>1500-tree XGBoost classifier<br/>82.7% test accuracy

    API->>Cache: prediction_cache.get(cache_key)
    alt Cache MISS (first request or TTL expired)
        Cache-->>API: None
        API->>Data: load_asset_data(asset, primary_tf='15m')
        Note over Data: Reads CSV files:<br/>Gold_15m_Candlestick.csv<br/>+ 5m, 30m, 1h aligned data<br/>2004–present (~60K rows)

        API->>Features: engineer_all_features(df, add_labels=False)
        Note over Features: Pipeline:<br/>1. Volume microstructure (VWAP, CVD, imbalance)<br/>2. SMC (FVG, BOS, liquidity sweeps, order blocks)<br/>3. Multi-TF (5m, 30m, 1h trends/ATR/RSI)<br/>→ 100 features

        API->>Features: compute_v4_features(df)
        Note over Features: V4 live features:<br/>trend_ema_cross, session flags

        API->>API: Inject live MT5 price into latest bar
        Note over API: Reads data/mt5_prices.json<br/>(written by host mt5_price_cache.py)

        API->>Cache: prediction_cache.set(cache_key, df)
    else Cache HIT
        Cache-->>API: Cached DataFrame (100 features)
    end

    API->>API: Align features with model's expected feature_names
    Note over API: Handle missing/extra columns<br/>between trained model and current pipeline

    API->>Model: model.predict(X) + predict_proba(X)
    Model-->>API: predictions[], probabilities[]

    API->>API: Signal decision logic
    Note over API: if trend_ema_cross==1 AND proba>=0.5<br/>   AND confidence>=0.65 → BUY (1)<br/>if trend_ema_cross==0 AND proba<0.5<br/>   AND confidence>=0.65 → SELL (-1)<br/>else → HOLD (0)

    API->>SHAP: TreeExplainer(model).shap_values(latest_bar)
    SHAP-->>API: Top 5 SHAP contributions
    Note over SHAP: Computed fresh each cycle<br/>No hash cache — always current

    API->>ActiveTrades: get_active(asset)
    alt Active trade exists
        ActiveTrades-->>API: Frozen TP/SL/signal
        Note over API: Override latest bar:<br/>signal = frozen_signal<br/>tp_price = frozen_tp<br/>sl_price = frozen_sl<br/>trade_active = true
    else No active trade
        API->>API: Calculate TP/SL from entry price
        Note over API: tp = price × (1 + 0.45%)<br/>sl = price × (1 - 0.15%)
        alt confidence > 65% AND signal != HOLD
            API->>ActiveTrades: open_trade(asset, signal, entry, tp, sl)
            Note over ActiveTrades: 🔒 Trade locked<br/>TP/SL frozen until resolution
            API->>Logger: log_prediction(asset, signal, confidence, price, tp, sl)
            Logger->>Logger: Append to predictions_YYYYMMDD.jsonl
            Logger->>Logger: Store in ChromaDB (signal_patterns collection)
        end
    end

    API-->>Browser: HTTP 200 JSON
    Note over API,Browser: {<br/>  asset: "gold",<br/>  predictions: [{<br/>    timestamp, signal (1|0|-1),<br/>    confidence, probability,<br/>    price, tp_price, sl_price,<br/>    shap_values: [{feature, contribution}×5],<br/>    trade_active: bool<br/>  }×100],<br/>  total_signals, data_range<br/>}

    Browser->>Browser: React state update
    Note over Browser: TerminalSignalPanel renders:<br/>- Signal hero (BUY/SELL/HOLD)<br/>- TP/SL levels<br/>- SHAP key drivers (diverging bars)<br/>- "TRADE ACTIVE" banner if locked<br/>- WebSocket status indicator

    Browser->>Browser: TradingViewChart iframe (OANDA:XAUUSD)
    Browser->>Browser: TerminalStatsBar updates (live price, model info)
```

---

## Active Trade Resolution Flow

```mermaid
sequenceDiagram
    participant ETL as ETL Monitor<br/>(etl_monitor.py)
    participant MT5 as MT5 Price Cache<br/>(mt5_prices.json)
    participant API as Flask API<br/>(prediction cycle)
    participant ActiveTrades as ActiveTradeTracker
    participant Tracker as OutcomeTracker<br/>(JSONL)
    participant Logger as PredictionLogger

    Note over ETL,Tracker: === OUTCOME CHECK (every prediction cycle) ===

    ETL->>MT5: Read mt5_prices.json
    MT5-->>ETL: {gold: $3,990, silver: $55.51}

    API->>ActiveTrades: For each asset: check_outcome(asset, current_price)

    alt Active trade exists
        ActiveTrades->>ActiveTrades: Compare price vs frozen TP/SL

        alt Price >= TP (BUY) or Price <= TP (SELL)
            Note over ActiveTrades: ✅ WIN_TP
            ActiveTrades->>ActiveTrades: trade.status = 'closed'
            ActiveTrades->>Tracker: log_outcome(signal_id, asset, WIN_TP, pnl)
            Tracker->>Tracker: Dedup check → append to trade_outcomes.jsonl
            ActiveTrades-->>API: {outcome: WIN_TP, pnl: +0.35%}
        else Price <= SL (BUY) or Price >= SL (SELL)
            Note over ActiveTrades: ❌ LOSS_SL
            ActiveTrades->>ActiveTrades: trade.status = 'closed'
            ActiveTrades->>Tracker: log_outcome(signal_id, asset, LOSS_SL, pnl)
            ActiveTrades-->>API: {outcome: LOSS_SL, pnl: -0.15%}
        else Still within range
            ActiveTrades-->>API: null (still active)
        end
    end

    Note over ActiveTrades: Trade closed → cleared from memory<br/>Ready for next signal on same asset

    API->>Logger: check_outcomes(live_prices)
    Note over Logger: Legacy path: evaluates all<br/>unresolved predictions in JSONL<br/>Marks actual_outcome + actual_pnl
```

---

## ETL Pipeline Flow (Background)

```mermaid
sequenceDiagram
    participant Cron as ETL Monitor<br/>(30min cycle)
    participant MT5 as MT5 Check
    participant YFinance as YFinance Fallback
    participant CSV as CSV Append Loader
    participant Health as Pipeline Health

    Cron->>Cron: Check data freshness (gold, silver)
    Note over Cron: max_age_hours = 25

    alt Data STALE (>25h old)
        Cron->>MT5: Try MetaTrader5 import
        alt MT5 available (Windows host)
            MT5-->>Cron: Fetch latest candles via MT5
        else MT5 not installed (Docker)
            MT5-->>Cron: ImportError
            Cron->>YFinance: YFinanceExtractor(asset, intervals)
            YFinance->>YFinance: yf.Ticker('GC=F').history()
            YFinance-->>Cron: Dict[interval, DataFrame]
            Cron->>CSV: CSVAppendLoader.run(data_dict)
            CSV->>CSV: Append to CSV, deduplicate by Date+Time
        end
        Cron->>Health: record_update(success=True)
    else Data FRESH
        Cron->>Health: No update needed
    end

    Cron->>Cron: Check retrain conditions (every 6h)
    Note over Cron: outcomes >= 50 AND<br/>accuracy < 55% → trigger retrain
```

---

## Key Architecture Notes

| Component | Technology | Details |
|-----------|-----------|---------|
| **API** | Flask 3.0 + SocketIO | Port 5000, CORS enabled, rate limited |
| **ML Model** | XGBoost 2.0 | 1500 trees, max_depth=5, Optuna-tuned |
| **Features** | 100 engineered | Volume (VWAP, CVD), SMC (FVG, BOS, OB), Multi-TF (5m/30m/1h), V4 (trend) |
| **Data** | CSV files | 2004–present, 15m primary, 4 timeframes aligned |
| **Explainability** | SHAP TreeExplainer | Top 5 features per prediction, computed on-demand |
| **Live Prices** | MT5 cache file | Written by host machine, read by Docker container |
| **Prediction Storage** | JSONL + ChromaDB | Daily files + vector similarity search |
| **User Data** | PostgreSQL 15 | Auth, profiles, watchlists |
| **Active Trades** | In-memory tracker | One trade per asset, frozen TP/SL until resolution |
| **Outcome Tracking** | OutcomeTracker | Deduplicated JSONL, signal_id based |
| **Frontend** | Next.js 16 + React 19 | Bloomberg Terminal aesthetic, TradingView charts |
