# FYP Report V1 — Verification Against Codebase

**Report**: `FYP REPORT V1.docx`  
**Verified**: 2026-06-17  
**Result**: 4 accurate, 3 moderate gaps, 3 critical gaps

---

## Summary

| Status | Count | Items |
|--------|-------|-------|
| ✅ Accurate | 4 | SQLite, accuracy, export, responsive |
| ⚠️ Moderate | 3 | Feature count, Next.js version, WCAG |
| ❌ Critical | 3 | Plotly.js, walk-forward, ablation studies |

---

## ❌ Critical Issues (Must Fix Before Submission)

### 1. Plotly.js — WRONG LIBRARY
- **Report claims**: "interactive Plotly.js candlestick visualizations"
- **Code has**: TradingView iframe embeds (`TradingViewChart.tsx` line 76)
- **Reality**: Zero Plotly.js installed or used. No `plotly` in `package.json`
- **Fix**: Update report to say "TradingView Lightweight Charts" or "TradingView widget embeds"

### 2. Walk-Forward Validation — NOT IMPLEMENTED
- **Report claims**: "5-fold time series cross-validation with 60-day training windows and 20-day test windows"
- **Code has**: Only a config placeholder in `config/settings.py` (lines 150-155)
- **Reality**: `backtesting/engine.py` is a simple sequential backtest with no rolling retraining
- **Fix**: Either implement walk-forward or remove the claim. The backtest engine runs one pass, not rolling windows.

### 3. Ablation Studies — NO CODE EXISTS
- **Report claims**: "Removing SMC features reduced accuracy by 4.2 percentage points (63.8% vs 68.0%)"
- **Code has**: Zero ablation scripts. No `*ablation*` files found.
- **Reality**: Results appear to be manually computed without reproducible code
- **Fix**: Create `scripts/ablation_study.py` that trains models with/without SMC features, or remove the specific numbers

---

## ⚠️ Moderate Issues (Update Report)

### 4. Feature Count — UNDERSTATED
- **Report claims**: "23 predictive variables"
- **Code has**: **89 features** (confirmed by `reports/training_logs/gold_latest.json`)
- **Reality**: 19 volume + 29 SMC + 18 multi-TF + 15 aligned OHLCV + base = 89
- **Fix**: Update to "89 predictive variables" or "60+ engineered features"

### 5. Next.js Version — WRONG
- **Report claims**: "Next.js 14"
- **Code has**: `"next": "16.2.6"` in `package.json`
- **Fix**: Update to "Next.js 16"

### 6. WCAG 2.1 AA — MINIMAL EVIDENCE
- **Report claims**: Accessibility compliance and testing
- **Code has**: Basic `aria-*` from shadcn/ui; no axe-core, no pa11y, no Lighthouse CI
- **Fix**: Either add accessibility testing or soften claim to "basic accessibility via shadcn/ui primitives"

---

## ✅ Accurate Claims

### 7. SQLite Database — CORRECT
- Report says SQLite with SQLAlchemy ORM
- Code has SQLite as default (`database.py` line 224), PostgreSQL via env var
- **Verdict**: Accurate for development config

### 8. Model Accuracy — EXCEEDS TARGETS
- Report claims min 65% accuracy, claims 68% achieved
- Code has: **73.7% gold, 72.5% silver** (training logs)
- **Verdict**: Code exceeds reported targets (report is conservative)

### 9. PDF/CSV Export — IMPLEMENTED
- Report claims export functionality
- Code has: `backtesting/export.py` with CSV + PDF export, API endpoint at `/api/backtest/export`
- **Verdict**: Fully implemented

### 10. Responsive Design — IMPLEMENTED
- Report claims responsive across devices
- Code has: 62+ Tailwind responsive breakpoints, mobile sidebar, adaptive grids
- **Verdict**: Thoroughly implemented

---

## Additional Report Issues

### Content Quality
- **Chapter 3 (System Analysis)**: Has use cases and domain model — looks complete
- **Chapter 4 (System Design)**: Has architecture, UML, ERD, deployment — looks complete
- **Chapter 5 (Implementation)**: Module descriptions match code structure
- **Chapter 6 (Testing)**: Lists 14 test cases — need to verify they match actual tests
- **Chapter 7 (Conclusion)**: Standard conclusion section

### Missing from Report
- No mention of the GitHub Actions CI/CD pipeline
- No mention of Docker Compose deployment
- No mention of WebSocket real-time updates
- No mention of email alerts / notification system
- No mention of prediction logging and audit trail

### Version Mismatches
| Item | Report Says | Code Has |
|------|-------------|----------|
| Next.js | 14 | 16.2.6 |
| Charting | Plotly.js | TradingView embeds |
| Features | 23 | 89 |
| Accuracy | 68% | 73.7% |

---

## Recommended Actions

### Priority 1 (Before Submission)
1. Fix Plotly.js → TradingView reference throughout report
2. Remove or qualify walk-forward validation claim
3. Either implement ablation study or remove specific numbers
4. Update feature count from 23 to 89
5. Update Next.js version from 14 to 16

### Priority 2 (Nice to Have)
6. Add CI/CD and Docker to report
7. Add WebSocket real-time to report
8. Soften WCAG claim or add accessibility testing
9. Verify test cases in Chapter 6 match actual pytest tests
