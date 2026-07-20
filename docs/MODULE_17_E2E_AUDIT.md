# MetalMind SMCForge — 17-Module E2E Audit

**Date:** July 2, 2026  
**Method:** CodeGraph + subagent deep exploration + manual code reading. No test execution — pure source-level verification against the Combined Workflow (Define → Execute → Validate).

---

## Summary

| Category | Count | Modules |
|----------|-------|---------|
| Fully working, no issues | 9 | Auth, Profile, Data Connector, Watchlist, Dashboard, Backtest, Metrics, Features, Training |
| Working with minor gaps | 4 | Config, SHAP, Export, ETL |
| Partially working | 3 | Orchestrator, Self-Learning, Signal Memory |
| Dead / not implemented | 1 | Airflow |

---

## TIER 1 — Fully Working (9 modules)

### 1. Authentication (JWT/OTP/2FA)
All endpoints present: register, login, verify-email, resend-otp, refresh. Services: security_service (OTP via secrets.randbelow), email_service (Resend SDK + demo fallback), password_service (bcrypt 12 rounds, strength validation). Frontend: login, register, verify-email, verify-success pages. 2FA: setup/enable/disable endpoints in profile.py. Blueprint registered at main.py:220. **Gap:** No dedicated unit test file for JWT lifecycle, OTP flow, or 2FA enable/disable.

### 2. User Profile & Settings
Full CRUD: GET/PUT profile, PUT password, GET/PUT settings, POST avatar, DELETE account. UserSettings model: theme, default_timeframe, default_asset, notifications, avatar_url. Frontend profile page with edit form and password change. **No gaps.**

### 3. Data API Connector
MultiTimeframeLoader reads CSVs for gold/silver across 5m/15m/30m/1h. Aligns to primary timeframe (15m default). Session filter for London+NY overlap. Chronological 70/15/15 train/val/test split. **No gaps.**

### 5. Watchlist Management
CRUD: GET list, POST add, PUT update, DELETE remove, POST reorder, GET symbols. WatchlistItem model with composite unique constraint (user_id, symbol). Frontend page with WatchlistTable component. **No gaps.**

### 6. Prediction Dashboard
TradingView iframe with interval switcher. SignalCard via WebSocket (Socket.IO). PipelineSummary polls every 60s. Live price from MT5 cache. Terminal-style dark theme. **Minor:** SignalCard.tsx exists but dashboard uses TerminalSignalPanel — not broken, just alternate component.

### 8. Backtest Execution
BacktestEngine: long-only simulation, TP/SL per-bar, slippage+commission, timeout exit, equity curve. BacktestManager runs async in daemon thread. POST /api/backtest/run returns 202. GET /api/backtest/results reads JSON. **No gaps.**

### 9. Performance Metrics
All 6 metrics computed in engine.py: win_rate (315), profit_factor (319), sharpe_ratio (334), sortino_ratio (343), calmar_ratio (351), max_drawdown_pct (329). Session breakdown (Asian/London/NY). **Gap:** API response omits sharpe/sortino/calmar — only win_rate, profit_factor, max_drawdown reach frontend.

### 15. Feature Engineering Pipeline
Volume: 22 features (VWAPd×3, CVD×3, Imbal×3, Wick×3, Ret×3, Std×3, 4 session flags). SMC: 21 features (FVG×5, BOS×6, liquidity×4, order block×4, premium/discount×4, market structure×6). Multi-TF: 18 features (6 per timeframe × 3). V4: 21 features (CVD slopes, ADX, ATR, EMA trend). Total: ~82 engineered features. Wired to main.py, train_v5.py, ETL transformer. **No gaps.**

### 16. Model Training
train_v5.py: Optuna 20 trials, Ratchet convergence loop (5 iterations), scale_pos_weight for imbalance. train_enhanced.py: Optuna 30 trials. Artifacts: gold_v5.pkl, gold_regression_system.pkl, enhanced_15m.pkl, silver models. **Minor:** train_enhanced.py omits gamma from best_params when building final model.

---

## TIER 2 — Working With Minor Gaps (4 modules)

### 4. Forecasting Config
ASSETS dict: gold (XAU/USD) + silver (XAG/USD), each with 5m/15m/30m/1h paths. FEATURE_CONFIG, BACKTEST_CONFIG, MODEL_CONFIG all present. **Gap:** LABEL_CONFIG split across BASELINE_CONFIG.label_params, GOLD_LABEL_PARAMS, SILVER_LABEL_PARAMS — functional but inconsistent naming.

### 7. Model Explainability (SHAP)
ShapAnalyzer wraps TreeExplainer. ShapCache singleton with mock fallback. /api/shap/feature-importance computes real SHAP or returns cache. Frontend SignalCard shows top 3 SHAP bars with friendly labels. **Gap:** /api/shap/plot serves pre-generated PNG from reports/shap_plots/ — returns 404 if file not created beforehand. No auto-generation hook.

### 10. Reporting & Export
BacktestExporter: CSV (trades, summary, equity, combined) and PDF (ReportLab primary, fpdf fallback). GET /api/backtest/export accepts format=csv|pdf and type=trades|summary|equity|all. **Gap:** Frontend backtest page has a client-side JSON download button (line 250-273) — it does NOT call the API CSV/PDF endpoint. The API works but is unreachable from the UI.

### 11. ETL Pipeline
ETLPipeline.run(): Extract → DataQualityGate → Transform chain → Load chain → PipelineResult. PipelineFactory creates Gold/Silver pipelines. ETLScheduler supports interval/daily/cron via APScheduler. 7 API endpoints in etl_routes.py. **Gap:** pipeline_status dict written from background thread without locks (race condition). Scheduler requires explicit /schedule/start call — won't fire automatically.

---

## TIER 3 — Partially Working (3 modules)

### 12. Pipeline Orchestrator
DataFreshnessChecker, ModelVersionManager, HealthMonitor, PipelineStatusTracker — all implemented. Integrated in main.py (/api/orchestrator/status) and run_pipeline.py (--mode status/freshness/backups). Frontend PipelineSummary polls every 60s. **Bug:** ModelVersionManager targets enhanced_15m.pkl for gold (orchestrator.py:92) but main.py ModelManager loads gold_regression_system.pkl — backup/rollback hits wrong file.

### 13. Self-Learning Retrainer
OutcomeTracker logs outcomes to JSONL, computes feature importance, generates win_rate summaries. ModelRetrainer.should_retrain() gates on min_outcomes + accuracy threshold. API endpoints: /api/memory/learning/status and /api/memory/learning/retrain. **Critical:** retrain_model() computes weights and logs the record but NEVER calls model.fit(). The retrain is a no-op. Also: main.py:972 hardcodes Docker path /app/reports/predictions — fails locally.

### 14. Signal Memory (ChromaDB)
SignalMemoryClient (embedded + HTTP modes), SignalEmbedder (NVIDIA NIM + sentence-transformers fallback), SignalRetriever (weighted confidence adjustment), SignalUpdater (store + outcome update). 4 API endpoints. chromadb in requirements. Instantiated in main.py:583. **Issues:** (1) Embedding function never passed to get_or_create_collection — ChromaDB uses null embedding, so query-time embedding mismatch with pre-computed embeddings. (2) No retry on ChromaDB connection failure — single failure crashes app. (3) get_collection_stats() only samples 1000 records — counts may be inaccurate.

---

## TIER 4 — Dead / Not Implemented (1 module)

### 17. Airflow DAGs
airflow/dags/retrain.py is empty (0 lines). Airflow is not in any requirements file. **Actual scheduling** lives in run_pipeline.py:117-159 via APScheduler — 15-min data fetch + daily 3 AM UTC retrain. The airflow/ directory is dead scaffolding.

---

## Priority Fixes for Defense

### Must fix (breaks demo or defense):
1. **Self-Learning retrain is a no-op** (Module 13) — retrain_model() never calls model.fit(). Either implement actual retraining or frame as "future work" in defense.
2. **Orchestrator model path mismatch** (Module 12) — backup/rollback targets wrong files. Could corrupt models during retrain.
3. **Signal Memory embedding mismatch** (Module 14) — queries return wrong results because embedding function not wired to collection.

### Should fix (visible gaps):
4. **Export button not wired** (Module 10) — frontend does client-side JSON, not API CSV/PDF.
5. **SHAP plot always 404** (Module 7) — no auto-generation hook.
6. **Backtest metrics not fully exposed** (Module 9) — Sharpe/Sortino/Calmar computed but not shown in UI.

### Nice to fix:
7. **7 stale unit tests** (already fixed this session).
8. **14 broken integration tests** (already fixed this session).
9. **Flask secret validation** (already fixed this session).
10. **Airflow dead code** — remove directory or implement.
