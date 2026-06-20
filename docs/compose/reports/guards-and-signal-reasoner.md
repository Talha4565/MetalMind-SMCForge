---
feature: guards-and-signal-reasoner
status: delivered
specs: []
plans:
  - docs/superpowers/plans/2026-06-20-guards-and-signal-reasoner-agent.md
branch: main
commits: a3c1db4..036d4e4
---

# Guards + Signal Reasoner Agent — Final Report

## What Was Built

Two deterministic guardrails and one LLM agent were added to the ml-signals trading system to protect against bad data and bad alerts. The **DataQualityGate** runs after data extraction and before transformation, detecting single-candle price spikes and deciding whether to continue the pipeline run. The **AlertRiskGate** runs at the live alert call site (`api/app/main.py:688`) before sending email alerts, enforcing per-asset cooldowns (30 min default), optional session-window filtering, and optional volatility suppression. The **SignalReasoner** agent makes one LLM call to NVIDIA NIM to evaluate whether a trading signal should actually be sent, considering RSI, trend alignment, and recent model accuracy. All three components are fail-open: if anything breaks, alerts still go through.

## Architecture

```
Extract → [DataQualityGate] → Transform → Load
                                            ↓
Predict → should_alert()? → [AlertRiskGate] → [SignalReasoner] → send_alert()
```

### Components

| Component | File | Integration Point |
|-----------|------|-------------------|
| `DataQualityGate` | `etl/guards/data_quality_gate.py` | `etl/pipeline.py` after extract (line 97) |
| `AlertRiskGate` | `etl/guards/alert_risk_gate.py` | `api/app/main.py:688` before `send_alert()` |
| `NemotronClient` | `etl/agents/llm_client.py` | Used by SignalReasoner |
| `SignalReasoner` | `etl/agents/signal_reasoner.py` | `api/app/main.py:688` after AlertRiskGate |

### Data Flow

1. **DataQualityGate.validate(df, asset)** returns `ValidationResult(passed, rows_before, rows_after, issues, should_continue, cleaned_df)`. If `should_continue=False`, the pipeline returns `SKIPPED` immediately.

2. **AlertRiskGate.check(asset, price, atr, signal, confidence, now)** returns `RiskDecision(approved, reason)`. Per-asset cooldown state is held in-memory (`_last_alert` dict).

3. **SignalReasoner.evaluate(asset, signal, confidence, rsi, atr, ema20, ema50, price)** returns `AgentDecision(approved, reason, source)`. The `source` field is `"llm"` (NVIDIA NIM responded), `"fail_open"` (API unavailable, approve anyway), or `"disabled"` (`ML_AGENT_ENABLED=false`).

### Design Decisions

- **Guards are validators, not agents.** The YAML files in `.claude/agents/` were aspirational. The actual implementation uses deterministic if/else logic — no LLM, no tool loop. This is honest naming for what the code does.

- **DataQualityGate only covers gaps.** `CSVExtractor.validate()` and `DataQualityTransformer` already handle nulls, duplicates, and OHLC validation. The gate only adds price-spike detection and the `should_continue` decision.

- **AlertRiskGate lives at the call site, not in `etl/alerts.py`.** `EmailAlertService` is a transport class (SMTP). Market logic (session hours, cooldowns) belongs at `main.py:688`, not inside the email sender.

- **Fail-open by design.** If NVIDIA NIM is down, times out, or returns garbage, the agent returns `approved=True` with `source="fail_open"`. The deterministic `AlertRiskGate` still runs underneath. Silently swallowing alerts because a free API hiccupped is worse than no agent.

- **Backtest isolation is structural.** `ML_AGENT_ENABLED` defaults to `false`. The agent is only imported by `api/app/main.py`. `backtesting/` and `models/` contain zero references to `SignalReasoner` or `NemotronClient`.

- **Spread check dropped.** The dataset is single-source OHLC candles. No bid/ask feed exists. The check is unimplementable.

- **Volatility suppression is opt-in.** `enforce_volatility=False` by default. High-volatility is often when signals are most profitable — this is a philosophical choice, not a bug.

## Usage

### DataQualityGate (enabled by default)

```python
from etl.guards.data_quality_gate import DataQualityGate
gate = DataQualityGate()
result = gate.validate(df, asset="gold")
if not result.should_continue:
    print(f"Blocked: {result.issues}")
```

Config in `config/settings.py`:
```python
DATA_QUALITY_GATE_CONFIG = {
    "max_price_change_pct": 0.10,  # 10% max single-candle move
    "min_rows_required": 50,       # Skip if fewer rows survive
    "enabled": True,
}
```

### AlertRiskGate (enabled by default)

```python
from etl.guards.alert_risk_gate import AlertRiskGate
gate = AlertRiskGate()
decision = gate.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8)
if not decision.approved:
    print(f"Suppressed: {decision.reason}")
```

Config:
```python
ALERT_RISK_GATE_CONFIG = {
    "enabled": True,
    "min_alert_interval_min": 30,    # Cooldown per asset
    "suppress_weekends": True,
    "enforce_session": False,        # Opt-in
    "enforce_volatility": False,     # Opt-in
}
```

### SignalReasoner (disabled by default)

```bash
# Enable in .env
ML_AGENT_ENABLED=true
NVIDIA_API_KEY=nvapi-...
ML_AGENT_TIMEOUT_SEC=8
```

```python
from etl.agents.signal_reasoner import SignalReasoner
from etl.agents.llm_client import NemotronClient

reasoner = SignalReasoner(client=NemotronClient(), pred_logger=prediction_logger)
decision = reasoner.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0, ema20=2000, ema50=1990, price=2005)
print(f"Approved: {decision.approved}, Source: {decision.source}, Reason: {decision.reason}")
```

## Verification

**63/63 tests pass** across 6 test files:

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/unit/test_data_quality_gate.py` | 6 | All pass |
| `tests/unit/test_alert_risk_gate.py` | 9 | All pass |
| `tests/unit/test_llm_client.py` | 6 | All pass |
| `tests/unit/test_signal_reasoner.py` | 7 | All pass |
| `tests/integration/test_etl_pipeline.py` | 8 | All pass |
| `tests/smoke/test_smoke.py` | 27 | All pass |

**Backtest isolation verified:** `grep -rn "signal_reasoner\|SignalReasoner\|NemotronClient" backtesting/ models/` returns zero matches.

## Journey Log

- [pivot] Original proposal called these "agents" — renamed to "guards" (validators) for the deterministic components. Only `SignalReasoner` is a genuine LLM agent.
- [fix] Integration points were initially wrong (putting data gate to "skip retrain" — `ETLPipeline.run()` does no retrain). Corrected to: data gate prevents bad data from loading, alert gate runs at `main.py:688`.
- [fix] Existing `BaseExtractor.validate()` and `DataQualityTransformer` already cover nulls/duplicates/OHLC. DataQualityGate only adds price-spike detection — no duplication.
- [lesson] Test env var scoping: `patch.dict(os.environ, ...)` only sets the var inside the context manager. Tests that construct inside the context but call methods outside it must wrap the entire test.
- [lesson] MockExtractor returns 3 rows — DataQualityGate's default `min_rows_required=50` blocks all existing integration tests. Injected a permissive gate via constructor parameter.

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `docs/superpowers/plans/2026-06-20-guards-and-signal-reasoner-agent.md` | Implementation plan | Complete — 9 tasks, all executed |
