# Walk-Forward CV Feasibility Analysis

**Following Combined Workflow: Senior Engineering Partner + Ratchet**
**Date:** July 2, 2026
**Scope:** Read-only analysis. No changes to the project.

---

## Phase 1: Define

**Spec:** Should we implement walk-forward cross-validation for MetalMind's backtest engine?

**Success criteria:**
1. Does the single-split backtest produce misleading performance numbers?
2. Would walk-forward reveal instability the single split hides?
3. Is the 2-3 hour cost justified for an FYP defense?
4. What does the examiner gain from seeing walk-forward results?

**Tier:** MVP (FYP)

---

## Phase 2: Execute (Analysis)

### Current State

The backtest flow works like this:

1. `data/loaders.py:train_val_test_split()` splits data chronologically: 70% train, 15% val, 15% test
2. `models/train_enhanced.py` trains on the 70% train set
3. `backtesting/engine.py:run_backtest()` evaluates on the 15% test set
4. Results: single win_rate, single Sharpe, single max_drawdown

**The problem:** This gives you ONE number for each metric. If the model happened to perform well on that specific 15% test window, you report good results. If it performed poorly, you report bad results. There's no way to know if the result is stable or lucky.

### What Walk-Forward Would Do

With the config that already exists (12-month train, 3-month test, 3-month step):

```
Data: Jan 2020 ──────────────────────────────────── Dec 2024

Fold 1: [Jan 2020 ──── Dec 2020] train → [Jan 2021 ─── Mar 2021] test
Fold 2: [Apr 2020 ──── Mar 2021] train → [Apr 2021 ─── Jun 2021] test
Fold 3: [Jul 2020 ──── Jun 2021] train → [Jul 2021 ─── Sep 2021] test
...and so on, sliding forward 3 months each time
```

Each fold trains on 12 months of data, tests on the next 3 months, then slides forward. You get 12-15 folds instead of 1 result.

**Output:** Average win_rate across folds, standard deviation of win_rate, worst-fold drawdown, best-fold Sharpe. This tells you "the model consistently achieves 55-65% win rate across different market regimes" — much stronger than "62% on one test set."

### The Honest Assessment

**Arguments FOR implementing it:**

1. **Examiner credibility.** An examiner who knows ML will ask "how do you know this isn't overfitting to one time period?" Walk-forward is the standard answer. Without it, you're vulnerable to that question.

2. **The config already exists.** `BACKTEST_CONFIG.walk_forward` has the settings. Implementing it is connecting the config to the actual code — not designing from scratch.

3. **The data supports it.** You have 4+ years of 15-minute data (2020-2024). That's enough for 12+ walk-forward folds with 12-month train windows.

4. **It catches regime changes.** Gold behavior in 2020 (COVID crash) is different from 2022 (rate hikes) is different from 2024. A single split might train on calm markets and test on volatile ones, or vice versa. Walk-forward tests across all regimes.

**Arguments AGAINST implementing it:**

1. **Time cost.** 2-3 hours minimum. Each fold requires: retrain model (Optuna + fit), run backtest, collect metrics. 12 folds = 12 full training runs. On your hardware, each training run takes ~2-5 minutes. Total: 30-60 minutes just for computation, plus implementation time.

2. **The single split already works.** Your current results (win_rate, profit_factor, Sharpe) are real — they're just from one window. For an FYP, this is acceptable if you frame it honestly: "single-period chronological backtest, future work includes walk-forward validation."

3. **It doesn't fix the real gaps.** Walk-forward won't fix the self-learning retrain being a no-op, or the feature count mismatch in the DOCX. Those are higher priority.

4. **Risk of worse-looking results.** Walk-forward might reveal that the model performs well in some periods and poorly in others. If you report the average, it might be lower than the single-split number. That's more honest but less impressive.

### What the Code Would Look Like

Separate file, doesn't touch the existing backtest engine:

```python
# scripts/walk_forward_validation.py (NEW, standalone)

def walk_forward_split(df, train_months=12, test_months=3, step_months=3):
    """Generate walk-forward train/test splits."""
    folds = []
    dates = df.index
    start = dates[0]
    
    while True:
        train_end = start + pd.DateOffset(months=train_months)
        test_end = train_end + pd.DateOffset(months=test_months)
        
        if test_end > dates[-1]:
            break
        
        train_mask = (dates >= start) & (dates < train_end)
        test_mask = (dates >= train_end) & (dates < test_end)
        
        folds.append({
            'train': df[train_mask],
            'test': df[test_mask],
            'train_start': start,
            'train_end': train_end,
            'test_start': train_end,
            'test_end': test_end,
        })
        
        start += pd.DateOffset(months=step_months)
    
    return folds

def run_walk_forward(asset='gold', ...):
    """Run full walk-forward validation."""
    # For each fold: train model, run backtest, collect metrics
    # Return: average metrics + standard deviation + per-fold breakdown
```

---

## Phase 3: Validate

### Does it meet success criteria?

| Criterion | Verdict |
|-----------|---------|
| Does single-split hide instability? | Yes — one number across all market regimes |
| Would walk-forward reveal it? | Yes — per-fold metrics show regime sensitivity |
| Is 2-3 hrs justified for FYP? | Borderline — valuable but not critical |
| What does examiner gain? | Credibility + regime analysis + anti-overfitting evidence |

### Recommendation

**Implement it, but as a separate script that produces a report — not wired into the main backtest flow.**

Why separate:
- Doesn't break the existing backtest (which works and is wired to the frontend)
- Produces a standalone report you can reference in defense
- If results are worse than single-split, you can choose not to show it
- If results are better or similar, it strengthens your case

**Time estimate:** 2 hours for the script + 30 minutes for the training runs + 30 minutes for the report = 3 hours total.

**Priority:** After the self-learning retrain fix and DOCX updates. This is polish, not foundation.

---

## Decision

| Option | Effort | Risk | Value |
|--------|--------|------|-------|
| A: Rewrite DOCX to "single-period split" | 15 min | None | Honest, no new code |
| B: Implement walk-forward as standalone script | 3 hrs | Low (separate file) | Stronger defense, regime analysis |
| C: Wire walk-forward into main backtest engine | 5+ hrs | Medium (breaks existing flow) | Overkill for FYP |

**My recommendation: Option B.** Write a standalone `scripts/walk_forward_validation.py` that produces a comparison report: single-split vs walk-forward. Use the report in defense, don't wire it into the live system.
