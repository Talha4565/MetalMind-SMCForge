# MetalMind SMCForge — Proposal vs Reality Report

**Date:** July 2, 2026  
**Purpose:** What the proposal promised vs what was actually built, contradictions, and assessment of whether changes improved or worsened the project.

---

## Module 1: Authentication

**Proposal:** JWT auth, Sign Up/Login/Logout  
**Reality:** JWT with access + refresh tokens, bcrypt password hashing, email OTP verification via Resend, TOTP 2FA with QR code, rate limiting on all endpoints, account soft-delete, password strength validation (8 chars min, mixed case + number + special char).

**Contradiction:** None on functionality. Proposal was minimal; implementation exceeded it.

**Extra beyond proposal:** 2FA (TOTP), rate limiting, password strength rules, account deletion, avatar upload.

**Assessment:** Strictly better. No changes needed for defense.

---

## Module 2: User Profile & Settings

**Proposal:** Manage personal details, change passwords, configure theme and default landing view.  
**Reality:** Full CRUD profile (name, email with re-verification on change), password change with strength validation, UserSettings model storing theme, default asset, default timeframe, notification preferences. Frontend page at `/dashboard/profile` with form validation via react-hook-form + zod.

**Contradiction:** None.

**Extra:** Avatar upload endpoint, account status display (active/inactive, verified/unverified), member-since date.

**Assessment:** Matches and exceeds. No issues.

---

## Module 3: Data API Connector

**Proposal:** "Fetches up-to-date historical price data for Gold and Silver from the external data source (Kaggle/API)." Frontend: "Streamlit"  
**Reality:** Multi-timeframe loader (`data/loaders.py`) reads local CSV files (Gold 5m/15m/30m/1h, Silver 5m/15m/30m/1h) from `Gold Dataset/` and `Silver Dataset/` directories. Data originally sourced from Kaggle, now updated via MT5 or yfinance. ETL pipeline (`etl/`) handles extraction + transformation + loading. Automated 15-minute updates via APScheduler.

**Contradiction 1 — Data source:** Proposal says "Kaggle/API". Reality uses Kaggle for historical data + MT5/yfinance for live updates. The Kaggle mention is technically still true (data was originally from Kaggle), but the live update mechanism is different.

**Contradiction 2 — Frontend framework:** Proposal says "Streamlit". Reality uses Next.js 16 + React 19 + TradingView Lightweight Charts + shadcn/ui. This is a major architectural change — Streamlit is a Python prototyping tool, Next.js is a production React framework. The change is a strict upgrade in capability, UI quality, and deployment flexibility.

**Contradiction 3 — "Interactive Plotly.js visualizations":** The proposal's DOCX (not the section 5 module list, but earlier descriptions) mentions "interactive Plotly.js visualizations". The actual charting uses TradingView Lightweight Charts embedded via iframe. TradingView is arguably better for financial charts (real candlesticks, professional look, live data from OANDA), but it's a third-party embed, not a custom Plotly integration.

**Assessment:** The three contradictions exist but all represent upgrades. For defense: say "originally planned Streamlit + Plotly, upgraded to Next.js + TradingView for production-grade UX and real financial charting." That's a positive narrative, not a gap.

---

## Module 4: Forecasting Configuration

**Proposal:** User interface to customize prediction by selecting Commodity (Gold/Silver) and Timeframe (15-min, 1-hour).  
**Reality:** `config/settings.py` defines ASSETS dict with Gold/Silver mapped to 5m/15m/30m/1h CSV paths. FEATURE_CONFIG controls SMC feature parameters. LABEL_CONFIG has asset-specific TP/SL thresholds. BACKTEST_CONFIG and MODEL_CONFIG handle training parameters. Frontend has asset toggle on dashboard.

**Contradiction:** Proposal mentions only 15-min and 1-hour timeframes. Reality supports 5m, 15m, 30m, and 1h — more granular than proposed.

**Assessment:** Better than promised. No defense risk.

---

## Module 5: Watchlist Management

**Proposal:** Save and monitor preferred asset/timeframe combos in a dedicated list.  
**Reality:** Full CRUD via `/api/watchlist` — add, remove, update, reorder. WatchlistItem model with display_name, notifications_enabled, alert_threshold, notes, and order fields. Frontend page at `/dashboard/watchlist`. Bulk reorder endpoint to avoid N+1 queries.

**Contradiction:** None. Matches exactly what was proposed.

**Extra:** Notification preferences, alert thresholds, notes per item, bulk reorder.

**Assessment:** Clean match. No issues.

---

## Module 6: Prediction Dashboard

**Proposal:** "Displays the current Prediction Signal (Buy/Sell/Neutral) and the model's Confidence Score using dynamic, real-time chart visualizations (e.g., Plotly)." Frontend: Streamlit.  
**Reality:** Next.js dashboard at `/dashboard` with TradingView chart iframe, SignalCard component showing BUY/SELL/HOLD with confidence percentage, SHAP feature importance bars, WebSocket real-time updates (30s interval), prediction caching with 5-min TTL. Live price from MT5 via `/api/market/price`.

**Contradiction 1 — Plotly → TradingView:** As discussed in Module 3. TradingView iframe embeds instead of Plotly.js. The landing page even advertises "TradingView Charts" explicitly.

**Contradiction 2 — Streamlit → Next.js:** Same as Module 3.

**Contradiction 3 — Real-time mechanism:** Proposal doesn't specify how "real-time" works. Reality uses WebSocket (Socket.IO) for live prediction push + HTTP polling as fallback. This is more sophisticated than a Streamlit refresh loop.

**Assessment:** All contradictions are upgrades. The TradingView embedding is the most visible deviation — an examiner familiar with Plotly would notice. Prepare the answer: "TradingView was chosen over Plotly because it provides professional-grade financial charting with live OANDA data feeds, which is more relevant for day traders than static Plotly charts."

---

## Module 7: Model Explainability (SHAP)

**Proposal:** "Visualizes the feature importance (SHAP values), providing transparency by showing why the model made a specific prediction based on the quantified SMC features."  
**Reality:** `explainability/shap_analyzer.py` uses `shap.TreeExplainer` on the XGBoost model. `api/app/shap_cache.py` caches SHAP results in-memory with mock fallback. API endpoints: `/api/shap/feature-importance` and `/api/shap/plot`. Frontend SignalCard shows top 3 SHAP feature contributions as horizontal bar charts with friendly labels.

**Contradiction:** None. SHAP is implemented exactly as described.

**Extra:** SHAP caching layer, mock fallback when model unavailable, per-prediction SHAP breakdown on the dashboard (not just global feature importance).

**Assessment:** This is a strong module. The "why" behind each trade is visible — exactly what was promised. For defense, emphasize that SHAP is computed per-prediction, not just globally.

---

## Module 8: Backtest Execution & Reporting

**Proposal:** "Provides the interface for the user to initiate a backtest over selected historical periods and generates an initial high-level summary of the simulation results."  
**Reality:** `backtesting/engine.py` — BacktestEngine class with long-only trade simulation, TP/SL exits, slippage + commission handling, timeout exits after max bars, equity curve generation. API endpoint `POST /api/backtest/run` runs in background thread with progress tracking. Results saved to `reports/backtest_results/`. Frontend page at `/backtest`.

**Contradiction 1 — "5-fold time series cross-validation":** The proposal's DOCX claims walk-forward cross-validation. The actual engine is a single sequential train/test split. There is no walk-forward or k-fold CV implemented. This is a genuine gap.

**Contradiction 2 — Short trades:** Proposal doesn't specify direction. Reality implements only long-only trades. Short selling is not supported (listed as remaining item in audit report).

**Assessment:** The walk-forward claim is the biggest documentation mismatch. The single-split backtest works and produces real results, but if the proposal promises cross-validation and it doesn't exist, that needs either implementation or an honest "future work" framing. The ablation study (which was implemented) helps offset this.

---

## Module 9: Performance Metrics

**Proposal:** "Displays the quantitative outcomes of the backtest runs, including Accuracy, Sharpe Ratio, Max Drawdown, and Hit Rate."  
**Reality:** `backtesting/engine.py` computes: Win Rate, Profit Factor, Max Drawdown (%), Sharpe Ratio (annualized with sqrt(252)), Sortino Ratio (downside deviation only), Calmar Ratio (annual return / max drawdown), total trades, net profit. API returns all metrics as JSON.

**Contradiction 1 — "Accuracy" metric:** The proposal lists "Accuracy" as a metric. The backtest engine does not compute classification accuracy (correct predictions / total predictions). It computes financial metrics (win rate, profit factor, etc.). This is a terminology mismatch — "Accuracy" in the proposal context likely means "how accurate are the signals" which translates to win rate in backtesting.

**Contradiction 2 — "Hit Rate":** The proposal lists "Hit Rate" as a separate metric. The engine computes "Win Rate" which is functionally the same thing.

**Assessment:** The actual metrics are more comprehensive than proposed (Sortino and Calmar were not in the proposal). The naming differences (Accuracy→Win Rate, Hit Rate→Win Rate) are cosmetic. For defense, say "Win Rate serves the same purpose as the proposed Hit Rate and Accuracy metrics."

---

## Module 10: Reporting & Export

**Proposal:** "Compiles backtest data, performance metrics, and key charts into professional, downloadable reports in formats such as CSV and PDF."  
**Reality:** `backtesting/export.py` — BacktestExporter class with `export_csv()` (trades, summary, equity curve — individual or combined) and `export_pdf()` (ReportLab primary, fpdf fallback). API endpoint `GET /api/backtest/export?format=csv|pdf`. 11 unit tests passing.

**Contradiction:** None. CSV and PDF export both implemented.

**Extra:** Dual PDF engine (ReportLab + fpdf fallback), individual vs combined CSV export options, tests for empty edge cases.

**Assessment:** Clean match. No defense risk.

---

## Summary of All Contradictions

### Contradictions that need defense preparation:

| # | What Changed | Severity | Defense Narrative |
|---|-------------|----------|-------------------|
| 1 | Streamlit → Next.js | **High visibility** | "Upgraded to Next.js for production-grade deployment, real-time WebSocket support, and professional UI — Streamlit is a prototyping tool" |
| 2 | Plotly → TradingView | **High visibility** | "TradingView provides live OANDA data feeds and professional financial charting relevant for day traders — Plotly is general-purpose" |
| 3 | Walk-forward CV missing | **Medium risk** | Either implement it (2-3 hours) or frame as "future work with honest limitation acknowledged" |
| 4 | 23 features → 89 features | **Low risk** | Positive change — more features than promised, ablation study validates which ones matter |
| 5 | 5m/15m/30m/1h timeframes | **Low risk** | More granular than proposed 15m/1h only |
| 6 | Kaggle → Kaggle + MT5 + yfinance | **Low risk** | Broader data sourcing, not a contradiction |
| 7 | Accuracy → Win Rate | **Cosmetic** | Same concept, financial terminology |

### Contradictions that are strictly positive (no defense needed):

- 2FA (TOTP) added beyond proposal scope
- Rate limiting added
- Avatar upload added
- Account deletion added
- SHAP caching layer added
- Sortino and Calmar ratios added (not in proposal)
- ETL pipeline + scheduler (not in proposal)
- Pipeline orchestrator with health monitoring (not in proposal)
- Self-learning retrain (not in proposal)
- Signal memory with ChromaDB (not in proposal)
- Feature engineering with 89 features across 10+ categories (not in proposal)

---

## What to Fix Before Defense

### Critical (must address):
1. **Walk-forward CV claim in DOCX** — Either implement basic walk-forward or change the claim to "single-period backtest" in the report. This is the most verifiable mismatch.

### Recommended:
2. **Update DOCX Plotly → TradingView** — Change "Plotly.js visualizations" to "TradingView financial charts" in the report to match reality.
3. **Update DOCX Streamlit → Next.js** — Change "Streamlit, Plotly, Tailwind CSS" to "Next.js, React, TradingView, Tailwind CSS" in the tools section.
4. **Feature count alignment** — Ensure the report says 89 features (or the actual count from the latest pipeline run), not 23.

### Optional (nice to have):
5. **Next.js version** — Report says 14, reality is 16.2.6. Update if mentioned.
6. **WCAG compliance** — Report may claim accessibility standards. Only basic shadcn/ui accessibility exists — no dedicated a11y testing.
