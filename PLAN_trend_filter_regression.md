# Plan: Trend Filter + Regression Outputs for Gold Model

## Goal
Transform the binary BUY/SELL model into a complete trade signal system that:
1. Filters signals by higher-timeframe trend direction
2. Predicts entry price, take-profit level, and stop-loss level
3. Logs which barrier (TP or SL) was hit first

## Phase 1: Trend Filter

### What
Add 1h trend direction as a filter before model prediction. Only allow signals aligned with the dominant trend.

### Implementation
1. **Compute 1h trend features:**
   - 1h EMA-50 vs 1h EMA-200 crossover (golden/death cross)
   - 1h price relative to 1h EMA-50 (above = uptrend, below = downtrend)
   - 1h ADX > 25 (trending market)

2. **Filter logic:**
   - If 1h trend = UP: allow BUY signals, block SELL signals
   - If 1h trend = DOWN: allow SELL signals, block BUY signals
   - If 1h trend = SIDEWAYS (ADX < 20): block all signals (HOLD)

3. **Expected impact:**
   - Eliminates countertrend trades (SELL in bull market)
   - Reduces total signals but improves win rate
   - Aligns model with dominant market direction

### Files to modify
- `models/experiment_binary_v2.py` → add trend features + filter
- `models/backtest_binary.py` → add trend filter to backtest

## Phase 2: Regression Outputs (Entry/TP/SL)

### What
Instead of just predicting direction, predict:
- Entry price (current bar close)
- Take-profit level (where to exit profitably)
- Stop-loss level (where to cut losses)

### Implementation

1. **Multi-output model:**
   - Output 1: Direction (BUY/SELL) — binary classification
   - Output 2: TP distance (percentage from entry) — regression
   - Output 3: SL distance (percentage from entry) — regression

2. **Training labels:**
   - For each bar, look ahead up to max_bars:
     - If TP hit first: direction=BUY, TP=actual distance, SL=0.3% (fixed)
     - If SL hit first: direction=SELL, TP=0.3% (fixed), SL=actual distance
     - If neither hit: label = NaN (excluded)

3. **Model architecture:**
   - Option A: Three separate XGBoost models (classification + 2 regression)
   - Option B: Single XGBoost with multi-output wrapper
   - **Recommended: Option A** — simpler, independent tuning

4. **Dynamic TP/SL based on ATR:**
   - TP = max(ATR * 2, 0.3%) — at least 0.3%, scaled by volatility
   - SL = max(ATR * 1.5, 0.2%) — tighter than TP for positive expectancy
   - This adapts to market conditions

5. **Trade logging:**
   - Entry: current price
   - TP: entry ± predicted TP distance
   - SL: entry ∓ predicted SL distance
   - Outcome: which barrier hit first (tracked in real-time)

### Files to create/modify
- `models/experiment_regression.py` — new training script
- `etl/prediction_logger.py` — add TP/SL to logged predictions
- `api/app/main.py` — serve TP/SL in prediction response
- `frontend-next/src/app/dashboard/signals/page.tsx` — display TP/SL

## Execution Order

1. **Phase 1: Trend filter** (simpler, immediate impact)
   - Add 1h trend features to data loading
   - Add filter logic to model prediction
   - Re-run backtest with filter
   - Compare: win rate, profit factor, max drawdown

2. **Phase 2: Regression outputs** (more complex, bigger impact)
   - Build TP/SL regression models
   - Integrate with existing binary classifier
   - Update prediction API to return entry/TP/SL
   - Update frontend to display trade signals
   - Re-run backtest with dynamic TP/SL
   - Compare: profit factor, expectancy, drawdown

## Success Metrics

| Metric | Current | Phase 1 Target | Phase 2 Target |
|---|---|---|---|
| Win rate | 65.6% | 70%+ | 72%+ |
| Profit factor | 1.89 | 2.0+ | 2.5+ |
| Max drawdown | 15.5% | <12% | <10% |
| SELL in bull market | 176 trades | <50 trades | <30 trades |
| Expectancy | $40/trade | $50+/trade | $60+/trade |

## Risk Considerations

- Trend filter may reduce total signals (fewer trades = less opportunity)
- Regression TP/SL may overfit to historical volatility patterns
- Dynamic TP/SL requires real-time ATR calculation at prediction time
- Need to validate that TP/SL predictions generalize to unseen data
