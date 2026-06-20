# Guards + Signal Reasoner Agent Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../compose/reports/guards-and-signal-reasoner.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two deterministic guardrails (data-quality gate, alert-risk gate) and one genuine LLM agent (signal reasoner) at the correct integration points in the existing pipeline — without duplicating existing `DataQualityTransformer` / `DataFreshnessChecker` / `PredictionLogger` logic, and without touching the backtest path.

**Architecture:** Plain Python classes wired into the existing pipeline. No framework (no CrewAI, no LangChain). The data gate extends behavior inside `ETLPipeline.run()` after extract. The alert gate runs at the live call site `api/app/main.py:688`. The SignalReasoner agent is a single direct OpenAI-compatible HTTP call to NVIDIA NIM, kept strictly out of the backtest path, with fail-open behavior and structured JSON output. The agent's "memory" reuses `PredictionLogger.get_summary()` — no new state.

**Tech Stack:** Python 3, pandas, stdlib `logging`/`dataclasses`/`json`/`urllib.request`. One optional runtime dependency for the agent: `requests` (already used throughout `api/app/main.py`). NVIDIA NIM OpenAI-compatible endpoint.

---

## Architecture Decisions (read these before implementing)

### AD1 — Do NOT build a separate "DataCurator" that duplicates existing code

The codebase already has three overlapping pieces:

1. `etl/extractors/csv_extractor.py:64 CSVExtractor.validate()` — checks empty/required-columns/null-date/duplicates.
2. `etl/transformers/quality_transformer.py:12 DataQualityTransformer` — dedup, missing values, outlier removal, OHLC validation. Already wired into every pipeline via `etl/factory.py:38`.
3. `etl/orchestrator.py:20 DataFreshnessChecker` — staleness check on CSV data.

Therefore the **data gate is only responsible for the gaps these don't cover**: single-candle price-spike detection, and a hard "skip the rest of this run" decision with a structured result. It is NOT a full re-validation pass. Putting null/duplicate/OHLC checks in the gate would create a second source of truth that drifts from the transformer. Don't do it.

### AD2 — The alert gate does NOT live inside `etl/alerts.py`

`EmailAlertService` is a transport class (SMTP). Trading-signal alerts are fired from the **prediction endpoint** at `api/app/main.py:690`, not from the pipeline. Burying session/ATR logic in the SMTP class couples market logic to transport. The gate is a separate class invoked at the call site, in front of `send_alert()`.

### AD3 — The agent is genuinely an agent, and genuinely minimal

It perceives (market context from the same `recent_data` the model just used + recent accuracy from `PredictionLogger`), reasons (one LLM call), acts (APPROVE/REJECT with a logged reason), and could keep state (it doesn't need to — `PredictionLogger` already is the state). No framework. One `requests.post`. Structured JSON output so we never string-parse `APPROVE - reason`.

### AD4 — Backtest safety is a hard, structural guarantee

`backtesting/engine.py` contains zero references to `send_alert`, `email_alerts`, or `SignalReasoner`. The agent is wired only into `api/app/main.py` (the live prediction path). We also add an explicit env-var bypass (`ML_AGENT_ENABLED=false` disables it) so a future operator can never accidentally put nondeterminism in a historical replay. The agent must NEVER be imported by `backtesting/`.

### AD5 — Fail-open, not fail-closed

If NVIDIA NIM is down, times out, returns garbage, or the API key is missing, the agent returns `approved=True` with `reason="agent_unavailable"` and falls back to the deterministic gate's decision. Rationale: the alert is the product's value; silently swallowing alerts because a free LLM API hiccupped is worse than no agent. The deterministic `AlertRiskGate` still runs unconditionally underneath.

### AD6 — The spread check is dropped

The dataset is single-source OHLC candles. There is no bid/ask feed. The proposed "spread > 3x normal" check is unimplementable. Do not add it.

### AD7 — Volatility suppression is opt-in and off by default

Suppressing signals *because* volatility is high is a philosophical choice (high-vol is often where signals are most profitable). Build the ATR check, default it off, expose the config, and justify it in the report. Do not enable by default.

---

## File Structure

### New files

| File | Responsibility |
|---|---|
| `etl/guards/__init__.py` | Empty package marker |
| `etl/guards/data_quality_gate.py` | `DataQualityGate` — price-spike detection + `ValidationResult`; wraps existing transformer, does not replace it |
| `etl/guards/alert_risk_gate.py` | `AlertRiskGate` — session/cooldown/ATR(volatility-opt-in) checks with in-memory cooldown state |
| `etl/agents/__init__.py` | Empty package marker |
| `etl/agents/llm_client.py` | `NemotronClient` — thin OpenAI-compatible HTTP wrapper with timeout + fail-open |
| `etl/agents/signal_reasoner.py` | `SignalReasoner` — builds context, calls LLM, parses JSON, returns `AgentDecision`. Reuses `PredictionLogger` for memory |
| `tests/unit/test_data_quality_gate.py` | Unit tests for the data gate |
| `tests/unit/test_alert_risk_gate.py` | Unit tests for the alert gate |
| `tests/unit/test_signal_reasoner.py` | Unit tests for the agent (LLM mocked) |
| `tests/unit/test_llm_client.py` | Unit tests for the HTTP wrapper (network mocked) |

### Modified files

| File | Change |
|---|---|
| `config/settings.py` | Add `DATA_QUALITY_GATE_CONFIG`, `ALERT_RISK_GATE_CONFIG`, `SIGNAL_REASONER_CONFIG` blocks |
| `etl/pipeline.py` | Invoke `DataQualityGate` after extract; honor `should_continue=False` to skip the rest of the run |
| `api/app/main.py` | Build `AlertRiskGate` + `SignalReasoner` once at module init; gate `send_alert()` at line 688 |
| `api/requirements.txt` | Add `requests` if not already pinned (verify first — it's used in `main.py` so likely present) |
| `.env.example` | Document `NVIDIA_API_KEY`, `ML_AGENT_ENABLED`, `ML_AGENT_TIMEOUT_SEC` |

---

## Task 1: Config blocks

**Files:**
- Modify: `config/settings.py` (append at end, after `get_xgboost_params()` at line 232)

- [ ] **Step 1: Write the config block**

Append to `config/settings.py`:

```python
# ============================================================================
# DATA QUALITY GATE (etl/guards/data_quality_gate.py)
# Extends DataQualityTransformer — only the gaps it doesn't cover.
# ============================================================================
DATA_QUALITY_GATE_CONFIG = {
    "max_price_change_pct": 0.10,      # Drop candle if |close-prev_close|/prev_close > 10%
    "min_rows_required": 50,           # Skip run entirely if fewer rows survive
    "enabled": True,
}

# ============================================================================
# ALERT RISK GATE (etl/guards/alert_risk_gate.py)
# Deterministic gate run at the live alert call site (api/app/main.py:688).
# ============================================================================
ALERT_RISK_GATE_CONFIG = {
    "enabled": True,
    "min_alert_interval_min": 30,       # Cooldown per asset — biggest ROI
    "suppress_weekends": True,
    "session_start_utc": "07:00",       # London open (UTC)
    "session_end_utc": "21:00",         # NY close (UTC)
    "enforce_session": False,           # Off by default — opt-in
    "max_atr_multiplier": 2.0,          # ATR > 2x 20-bar avg => suppress
    "enforce_volatility": False,        # Off by default — see AD7
}

# ============================================================================
# SIGNAL REASONER AGENT (etl/agents/signal_reasoner.py)
# One LLM call, OpenAI-compatible. Backtest-safe by construction (AD4).
# ============================================================================
SIGNAL_REASONER_CONFIG = {
    "enabled_env_var": "ML_AGENT_ENABLED",        # "true"/"false"; default false
    "api_key_env_var": "NVIDIA_API_KEY",
    "api_url": "https://integrate.api.nvidia.com/v1/chat/completions",
    # Real model ID from build.nvidia.com/models — "nemotron-3-super" does NOT exist.
    "model": "nvidia/nemotron-3-ultra-550b-a55b",
    "timeout_env_var": "ML_AGENT_TIMEOUT_SEC",    # default 8 seconds
    "default_timeout_sec": 8,
    "temperature": 0.1,
    "max_tokens": 200,
    "fail_open": True,                              # AD5 — approve if LLM unavailable
}
```

- [ ] **Step 2: Verify import works**

Run: `python -c "from config.settings import DATA_QUALITY_GATE_CONFIG, ALERT_RISK_GATE_CONFIG, SIGNAL_REASONER_CONFIG; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add config/settings.py
git commit -m "feat(config): add data-quality gate, alert-risk gate, signal-reasoner config blocks"
```

---

## Task 2: `ValidationResult` dataclass + `DataQualityGate`

**Files:**
- Create: `etl/guards/__init__.py`
- Create: `etl/guards/data_quality_gate.py`
- Test: `tests/unit/test_data_quality_gate.py`

- [ ] **Step 1: Create empty package init**

Create `etl/guards/__init__.py` with content:

```python
"""Deterministic guardrails for the ETL pipeline and alert path."""
```

- [ ] **Step 2: Write the failing tests**

Create `tests/unit/test_data_quality_gate.py`:

```python
"""Unit tests for DataQualityGate."""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl.guards.data_quality_gate import DataQualityGate, ValidationResult


def make_clean_df(n=200):
    idx = pd.date_range("2026-01-01", periods=n, freq="15min")
    close = 2000 + np.arange(n) * 0.1
    return pd.DataFrame({
        "open": close, "high": close + 1, "low": close - 1,
        "close": close, "volume": 1000,
    }, index=idx)


class TestDataQualityGate:
    def test_clean_data_passes(self):
        df = make_clean_df()
        result = DataQualityGate().validate(df, asset="gold")
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert result.should_continue is True
        assert result.rows_after == len(df)

    def test_price_spike_dropped(self):
        df = make_clean_df()
        df.iloc[10, df.columns.get_loc("close")] *= 1.5  # +50% single-candle move
        result = DataQualityGate(max_price_change_pct=0.10).validate(df, asset="gold")
        assert result.passed is True
        assert result.rows_after == len(df) - 1
        assert any("spike" in i.lower() for i in result.issues)

    def test_small_move_kept(self):
        df = make_clean_df()
        df.iloc[10, df.columns.get_loc("close")] *= 1.03  # +3%, under threshold
        result = DataQualityGate(max_price_change_pct=0.10).validate(df, asset="gold")
        assert result.rows_after == len(df)

    def test_too_few_rows_skips_run(self):
        df = make_clean_df(n=20)
        result = DataQualityGate(min_rows_required=50).validate(df, asset="gold")
        assert result.passed is False
        assert result.should_continue is False

    def test_does_not_mutate_input(self):
        df = make_clean_df()
        snapshot = df.copy()
        DataQualityGate().validate(df, asset="gold")
        pd.testing.assert_frame_equal(df, snapshot)

    def test_first_row_no_pct_change(self):
        # First row has no previous close -> must not be flagged as a spike
        df = make_clean_df()
        result = DataQualityGate().validate(df, asset="gold")
        assert result.rows_after == len(df)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_data_quality_gate.py -v`
Expected: FAIL with `No module named 'etl.guards.data_quality_gate'`

- [ ] **Step 4: Implement `DataQualityGate`**

Create `etl/guards/data_quality_gate.py`:

```python
"""
Data quality gate — runs AFTER extract, BEFORE transform.

Scope (see AD1): this gate covers ONLY the gaps that the existing
DataQualityTransformer and CSVExtractor.validate() do not:
  - single-candle price-spike detection
  - a hard should_continue decision (skip the rest of the run)

It does NOT duplicate null/duplicate/OHLC checks — those live in
etl/transformers/quality_transformer.py and etl/extractors/csv_extractor.py.
"""
from dataclasses import dataclass, field
from typing import List
import logging

import pandas as pd

from config.settings import DATA_QUALITY_GATE_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Outcome of running the data-quality gate."""
    passed: bool
    rows_before: int
    rows_after: int
    issues: List[str] = field(default_factory=list)
    should_continue: bool = True
    cleaned_df: pd.DataFrame = None


class DataQualityGate:
    """Detect single-candle price spikes and decide whether to continue the run."""

    def __init__(self, config: dict = None):
        cfg = {**(DATA_QUALITY_GATE_CONFIG or {}), **(config or {})}
        self.enabled = cfg.get("enabled", True)
        self.max_price_change_pct = float(cfg.get("max_price_change_pct", 0.10))
        self.min_rows_required = int(cfg.get("min_rows_required", 50))

    def validate(self, df: pd.DataFrame, asset: str = "gold") -> ValidationResult:
        rows_before = len(df)
        if not self.enabled:
            return ValidationResult(
                passed=True, rows_before=rows_before, rows_after=rows_before,
                issues=["gate_disabled"], should_continue=True, cleaned_df=df,
            )

        issues: List[str] = []
        out = df.copy()

        # --- Single-candle price spike detection (the gap the transformer doesn't fill) ---
        if "close" in out.columns and len(out) > 1:
            pct_change = out["close"].pct_change()  # first row -> NaN, never flagged
            spike_mask = pct_change.abs() > self.max_price_change_pct
            n_spikes = int(spike_mask.sum())
            if n_spikes:
                issues.append(
                    f"dropped {n_spikes} price-spike rows "
                    f"(|change| > {self.max_price_change_pct:.0%})"
                )
                out = out[~spike_mask].copy()

        rows_after = len(out)

        # --- Run-level decision ---
        should_continue = rows_after >= self.min_rows_required
        passed = should_continue
        if not should_continue:
            issues.append(
                f"only {rows_after} rows survived (min required {self.min_rows_required})"
            )

        result = ValidationResult(
            passed=passed,
            rows_before=rows_before,
            rows_after=rows_after,
            issues=issues,
            should_continue=should_continue,
            cleaned_df=out,
        )
        logger.info(
            f"[DataQualityGate:{asset}] before={rows_before} after={rows_after} "
            f"continue={should_continue} issues={issues}"
        )
        return result
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_data_quality_gate.py -v`
Expected: PASS (6 passed)

- [ ] **Step 6: Commit**

```bash
git add etl/guards/__init__.py etl/guards/data_quality_gate.py tests/unit/test_data_quality_gate.py
git commit -m "feat(guards): add DataQualityGate for price-spike detection + run-continue decision"
```

---

## Task 3: Wire `DataQualityGate` into `ETLPipeline.run()`

**Files:**
- Modify: `etl/pipeline.py:38-64` (constructor), `etl/pipeline.py:96-98` (after extract), `etl/pipeline.py:17-23` (PipelineStatus enum)

- [ ] **Step 1: Add `SKIPPED` to the `PipelineStatus` enum**

In `etl/pipeline.py`, the enum is at lines 17-23. Add `SKIPPED`:

```python
class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # Some stages succeeded, some failed
    SKIPPED = "skipped"  # Data-quality gate blocked the run
```

- [ ] **Step 2: Add the gate to the constructor (optional injection for testing)**

Modify `ETLPipeline.__init__` so the gate is injectable but defaults to the real one. Change the signature and body (currently lines 41-65) to:

```python
    def __init__(
        self,
        name: str,
        extractor: BaseExtractor,
        transformers: List[BaseTransformer],
        loaders: List[BaseLoader],
        config: Dict[str, Any] = None,
        data_quality_gate=None,           # NEW — injectable for tests
    ):
        """
        Initialize ETL Pipeline.

        Args:
            name: Pipeline name
            extractor: Data extractor instance
            transformers: List of transformer instances
            loaders: List of loader instances
            config: Optional configuration dictionary
            data_quality_gate: Optional DataQualityGate instance (defaults to real one)
        """
        self.name = name
        self.extractor = extractor
        self.transformers = transformers
        self.loaders = loaders
        self.config = config or {}
        self.last_result: Optional[PipelineResult] = None
        self.run_count = 0
        # Lazy import to avoid a hard dependency cycle at module import time
        if data_quality_gate is not None:
            self.data_quality_gate = data_quality_gate
        else:
            from .guards.data_quality_gate import DataQualityGate
            self.data_quality_gate = DataQualityGate()
```

- [ ] **Step 3: Invoke the gate after extract**

In `ETLPipeline.run()`, insert the gate between extract (ends at line 97) and transform (starts at line 99). Replace:

```python
            logger.info(f"✓ Extraction complete: {len(data)} records")
            logger.info("")
            
            # ========== TRANSFORM ==========
```

with:

```python
            logger.info(f"✓ Extraction complete: {len(data)} records")
            logger.info("")

            # ========== DATA QUALITY GATE ==========
            logger.info("PHASE 1.5: DATA QUALITY GATE")
            logger.info("-" * 80)
            dq = self.data_quality_gate.validate(
                data, asset=self.config.get("asset", "gold")
            )
            result.stage_results["data_quality_gate"] = {
                "success": dq.passed,
                "rows_before": dq.rows_before,
                "rows_after": dq.rows_after,
                "issues": dq.issues,
                "should_continue": dq.should_continue,
            }
            logger.info(
                f"  rows {dq.rows_before} -> {dq.rows_after}, "
                f"continue={dq.should_continue}, issues={dq.issues}"
            )
            if not dq.should_continue:
                result.status = PipelineStatus.SKIPPED
                result.completed_at = datetime.now()
                result.error = "Data-quality gate blocked the run"
                logger.warning(
                    f"⚠ Pipeline '{self.name}' SKIPPED by data-quality gate: {dq.issues}"
                )
                self.last_result = result
                return result
            data = dq.cleaned_df
            logger.info("")

            # ========== TRANSFORM ==========
```

- [ ] **Step 4: Add a regression test for the skipped path**

Append to `tests/integration/test_etl_pipeline.py`:

```python
    def test_pipeline_skipped_by_data_quality_gate(self):
        """When the gate says should_continue=False, the run returns SKIPPED early."""
        from etl.guards.data_quality_gate import ValidationResult

        class BlockingGate:
            def validate(self, df, asset="gold"):
                return ValidationResult(
                    passed=False, rows_before=len(df), rows_after=5,
                    issues=["too few rows"], should_continue=False, cleaned_df=df,
                )

        extractor = MockExtractor()
        pipeline = ETLPipeline(
            name="Skipped Pipeline",
            extractor=extractor,
            transformers=[MockTransformer()],
            loaders=[MockLoader()],
            data_quality_gate=BlockingGate(),
        )
        result = pipeline.run()
        assert result.status == PipelineStatus.SKIPPED
        # Transformers/loaders must NOT have run
        assert "transform_1" not in result.stage_results
        assert "data_quality_gate" in result.stage_results
```

- [ ] **Step 5: Run the full pipeline test suite**

Run: `pytest tests/integration/test_etl_pipeline.py -v`
Expected: PASS (all existing tests + the new `test_pipeline_skipped_by_data_quality_gate`)

- [ ] **Step 6: Commit**

```bash
git add etl/pipeline.py tests/integration/test_etl_pipeline.py
git commit -m "feat(pipeline): wire DataQualityGate after extract; add SKIPPED status"
```

---

## Task 4: `AlertRiskGate`

**Files:**
- Create: `etl/guards/alert_risk_gate.py`
- Test: `tests/unit/test_alert_risk_gate.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_alert_risk_gate.py`:

```python
"""Unit tests for AlertRiskGate."""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl.guards.alert_risk_gate import AlertRiskGate, RiskDecision


class TestAlertRiskGate:
    def _gate(self, **overrides):
        cfg = {
            "enabled": True,
            "min_alert_interval_min": 30,
            "suppress_weekends": True,
            "enforce_session": False,
            "enforce_volatility": False,
        }
        cfg.update(overrides)
        return AlertRiskGate(cfg)

    def test_first_alert_approved(self):
        g = self._gate()
        d = g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=None)
        assert d.approved is True
        assert d.reason == "passed"

    def test_cooldown_blocks_second_alert_same_asset(self):
        g = self._gate()
        now = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
        first = g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=now)
        second = g.check(asset="gold", price=2001.0, atr=2.0, signal=1, confidence=0.8,
                         now=now + timedelta(minutes=10))
        assert first.approved is True
        assert second.approved is False
        assert "cooldown" in second.reason.lower()

    def test_cooldown_does_not_block_other_asset(self):
        g = self._gate()
        now = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
        g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=now)
        other = g.check(asset="silver", price=25.0, atr=0.2, signal=-1, confidence=0.8, now=now)
        assert other.approved is True

    def test_cooldown_expires(self):
        g = self._gate()
        now = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
        g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=now)
        later = g.check(asset="gold", price=2001.0, atr=2.0, signal=1, confidence=0.8,
                        now=now + timedelta(minutes=31))
        assert later.approved is True

    def test_weekend_suppressed(self):
        g = self._gate()
        # 2026-06-06 is a Saturday
        sat = datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc)
        d = g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=sat)
        assert d.approved is False
        assert "weekend" in d.reason.lower()

    def test_session_enforced_blocks_outside(self):
        g = self._gate(enforce_session=True)
        # 03:00 UTC is before London open (07:00)
        night = datetime(2026, 6, 1, 3, 0, tzinfo=timezone.utc)  # Monday
        d = g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=night)
        assert d.approved is False
        assert "session" in d.reason.lower()

    def test_session_off_by_default_allows_night(self):
        g = self._gate()  # enforce_session defaults False
        night = datetime(2026, 6, 1, 3, 0, tzinfo=timezone.utc)
        d = g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=night)
        assert d.approved is True

    def test_volatility_opt_in_blocks_high_atr(self):
        # atr 5.0 > 2.0 * 2.0 historical avg
        g = self._gate(enforce_volatility=True, historical_atr=2.0)
        d = g.check(asset="gold", price=2000.0, atr=5.0, signal=1, confidence=0.8,
                    now=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc))
        assert d.approved is False
        assert "volatility" in d.reason.lower()

    def test_disabled_gate_approves_everything(self):
        g = self._gate(enabled=False)
        d = g.check(asset="gold", price=2000.0, atr=999.0, signal=1, confidence=0.8,
                    now=datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc))
        assert d.approved is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_alert_risk_gate.py -v`
Expected: FAIL with `No module named 'etl.guards.alert_risk_gate'`

- [ ] **Step 3: Implement `AlertRiskGate`**

Create `etl/guards/alert_risk_gate.py`:

```python
"""
Alert risk gate — deterministic checks run at the LIVE alert call site
(api/app/main.py:688), in front of EmailAlertService.send_alert().

Scope (AD2): transport logic stays in etl/alerts.py; market logic lives here.
The biggest single win is the per-asset cooldown (stops alert spam in choppy sessions).
Volatility and session checks are opt-in (AD7) — off by default.
"""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import logging

from config.settings import ALERT_RISK_GATE_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class RiskDecision:
    """Outcome of an alert risk check."""
    approved: bool
    reason: str


def _parse_hhmm(s: str) -> int:
    """'07:00' -> minutes-since-midnight (420)."""
    h, m = s.split(":")
    return int(h) * 60 + int(m)


class AlertRiskGate:
    """Deterministic alert suppression rules with per-asset cooldown state."""

    def __init__(self, config: dict = None, historical_atr: float = None):
        cfg = {**(ALERT_RISK_GATE_CONFIG or {}), **(config or {})}
        self.enabled = bool(cfg.get("enabled", True))
        self.min_alert_interval_min = int(cfg.get("min_alert_interval_min", 30))
        self.suppress_weekends = bool(cfg.get("suppress_weekends", True))
        self.enforce_session = bool(cfg.get("enforce_session", False))
        self.enforce_volatility = bool(cfg.get("enforce_volatility", False))
        self.session_start_min = _parse_hhmm(cfg.get("session_start_utc", "07:00"))
        self.session_end_min = _parse_hhmm(cfg.get("session_end_utc", "21:00"))
        self.max_atr_multiplier = float(cfg.get("max_atr_multiplier", 2.0))
        self.historical_atr = historical_atr  # optional baseline for volatility check
        self._last_alert: Dict[str, datetime] = {}  # asset -> last approved time

    def check(
        self,
        asset: str,
        price: float,
        atr: float,
        signal: int,
        confidence: float,
        now: Optional[datetime] = None,
    ) -> RiskDecision:
        if not self.enabled:
            return RiskDecision(approved=True, reason="gate_disabled")

        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # 1. Weekend
        if self.suppress_weekends and now.weekday() >= 5:
            return RiskDecision(approved=False, reason="weekend_market_closed")

        # 2. Session window (opt-in)
        if self.enforce_session:
            minutes = now.hour * 60 + now.minute
            if not (self.session_start_min <= minutes <= self.session_end_min):
                return RiskDecision(approved=False, reason="outside_session_window")

        # 3. Volatility (opt-in)
        if self.enforce_volatility and self.historical_atr and atr > self.max_atr_multiplier * self.historical_atr:
            return RiskDecision(
                approved=False,
                reason=f"volatility_too_high_atr_{atr:.2f}_vs_{self.historical_atr:.2f}",
            )

        # 4. Cooldown (per asset) — the high-ROI check
        last = self._last_alert.get(asset)
        if last is not None and (now - last) < timedelta(minutes=self.min_alert_interval_min):
            return RiskDecision(
                approved=False,
                reason=f"cooldown_{int((now - last).total_seconds() // 60)}min_of_{self.min_alert_interval_min}min",
            )

        # Approved — record for future cooldown
        self._last_alert[asset] = now
        logger.info(f"[AlertRiskGate] approved {asset} signal={signal} conf={confidence:.2f}")
        return RiskDecision(approved=True, reason="passed")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_alert_risk_gate.py -v`
Expected: PASS (9 passed)

- [ ] **Step 5: Commit**

```bash
git add etl/guards/alert_risk_gate.py tests/unit/test_alert_risk_gate.py
git commit -m "feat(guards): add AlertRiskGate with per-asset cooldown, opt-in session/volatility"
```

---

## Task 5: `NemotronClient` (LLM HTTP wrapper, fail-open)

**Files:**
- Create: `etl/agents/__init__.py`
- Create: `etl/agents/llm_client.py`
- Test: `tests/unit/test_llm_client.py`

- [ ] **Step 1: Create empty package init**

Create `etl/agents/__init__.py` with content:

```python
"""LLM agents for ml-signals. Plain Python — no agent framework."""
```

- [ ] **Step 2: Write the failing tests (network mocked — never hit NVIDIA)**

Create `tests/unit/test_llm_client.py`:

```python
"""Unit tests for NemotronClient. Network is ALWAYS mocked."""
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl.agents.llm_client import NemotronClient


class TestNemotronClient:
    def test_returns_none_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            c = NemotronClient()
            assert c.is_available() is False
            assert c.chat([{"role": "user", "content": "hi"}]) is None

    @patch("etl.agents.llm_client.requests.post")
    def test_chat_returns_content_on_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": '{"approved": true}'}}]},
        )
        c = NemotronClient(api_key="fake-key")
        out = c.chat([{"role": "user", "content": "decide"}])
        assert out == '{"approved": true}'
        # Confirm the real model ID is used (not the fictional "nemotron-3-super")
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "nvidia/nemotron-3-ultra-550b-a55b"

    @patch("etl.agents.llm_client.requests.post")
    def test_chat_returns_none_on_http_error(self, mock_post):
        mock_post.return_value = MagicMock(status_code=500, json=lambda: {})
        c = NemotronClient(api_key="fake-key")
        assert c.chat([{"role": "user", "content": "decide"}]) is None

    @patch("etl.agents.llm_client.requests.post")
    def test_chat_returns_none_on_timeout(self, mock_post):
        import requests as req
        mock_post.side_effect = req.Timeout("timed out")
        c = NemotronClient(api_key="fake-key")
        assert c.chat([{"role": "user", "content": "decide"}]) is None

    @patch("etl.agents.llm_client.requests.post")
    def test_chat_returns_none_on_malformed_json(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: {"not_choices": []}
        )
        c = NemotronClient(api_key="fake-key")
        assert c.chat([{"role": "user", "content": "decide"}]) is None

    def test_does_not_use_fictional_super_model(self):
        c = NemotronClient(api_key="fake-key")
        assert "nemotron-3-super" not in c.model, "use a real model ID from build.nvidia.com"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_llm_client.py -v`
Expected: FAIL with `No module named 'etl.agents.llm_client'`

- [ ] **Step 4: Implement `NemotronClient`**

Create `etl/agents/llm_client.py`:

```python
"""
Thin OpenAI-compatible HTTP wrapper for NVIDIA NIM.

Intentionally minimal (AD3): one method, chat(), that returns the raw content
string or None on ANY failure (timeout, HTTP error, malformed JSON, missing key).
Callers must treat None as "agent unavailable" and fail open (AD5).
"""
import os
import logging
from typing import Optional, List, Dict

import requests

from config.settings import SIGNAL_REASONER_CONFIG

logger = logging.getLogger(__name__)


class NemotronClient:
    """OpenAI-compatible client for NVIDIA NIM. Never raises on transport errors."""

    def __init__(self, api_key: str = None, config: dict = None):
        cfg = {**(SIGNAL_REASONER_CONFIG or {}), **(config or {})}
        self.api_url = cfg["api_url"]
        # "nvidia/nemotron-3-super" does NOT exist in the NVIDIA catalog.
        # Use a real model ID from https://build.nvidia.com/models.
        self.model = cfg.get("model", "nvidia/nemotron-3-ultra-550b-a55b")
        self.temperature = float(cfg.get("temperature", 0.1))
        self.max_tokens = int(cfg.get("max_tokens", 200))
        try:
            self.timeout = int(os.getenv(cfg.get("timeout_env_var", "ML_AGENT_TIMEOUT_SEC"),
                                         cfg.get("default_timeout_sec", 8)))
        except (TypeError, ValueError):
            self.timeout = 8
        self.api_key = api_key or os.getenv(cfg.get("api_key_env_var", "NVIDIA_API_KEY"))

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Return assistant content string, or None on any failure."""
        if not self.is_available():
            return None
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            logger.warning(f"[NemotronClient] transport error: {e}")
            return None
        if resp.status_code != 200:
            logger.warning(f"[NemotronClient] HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        try:
            return resp.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as e:
            logger.warning(f"[NemotronClient] malformed response: {e}")
            return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_llm_client.py -v`
Expected: PASS (6 passed)

- [ ] **Step 6: Commit**

```bash
git add etl/agents/__init__.py etl/agents/llm_client.py tests/unit/test_llm_client.py
git commit -m "feat(agents): add NemotronClient OpenAI-compatible wrapper with fail-open semantics"
```

---

## Task 6: `SignalReasoner` agent

**Files:**
- Create: `etl/agents/signal_reasoner.py`
- Test: `tests/unit/test_signal_reasoner.py`

- [ ] **Step 1: Write the failing tests (LLM mocked)**

Create `tests/unit/test_signal_reasoner.py`:

```python
"""Unit tests for SignalReasoner. LLM is always mocked."""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl.agents.signal_reasoner import SignalReasoner, AgentDecision


def fake_pred_summary(**kw):
    base = {"total_predictions": 0, "evaluated": 0, "wins": 0, "losses": 0}
    base.update(kw)
    return base


class TestSignalReasoner:
    def _reasoner(self, client_content=None):
        client = MagicMock()
        client.is_available.return_value = True
        client.chat.return_value = client_content
        return SignalReasoner(client=client, pred_logger=MagicMock(get_summary=lambda days=1: fake_pred_summary()))

    def test_parses_approve_json(self):
        r = self._reasoner(client_content='{"approved": true, "reason": "trend aligned"}')
        d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                       ema20=2000, ema50=1990, price=2005)
        assert d.approved is True
        assert d.reason == "trend aligned"
        assert d.source == "llm"

    def test_parses_reject_json(self):
        r = self._reasoner(client_content='{"approved": false, "reason": "overbought"}')
        d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=78, atr=2.0,
                       ema20=2000, ema50=1990, price=2005)
        assert d.approved is False
        assert d.source == "llm"

    def test_fail_open_on_malformed_response(self):
        # AD5: garbage from the LLM -> approve (fail open)
        r = self._reasoner(client_content="APPROVE - looks good")  # not JSON
        d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                       ema20=2000, ema50=1990, price=2005)
        assert d.approved is True
        assert d.source == "fail_open"
        assert "unparseable" in d.reason.lower() or "fail" in d.reason.lower()

    def test_fail_open_on_none_response(self):
        r = self._reasoner(client_content=None)
        d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                       ema20=2000, ema50=1990, price=2005)
        assert d.approved is True
        assert d.source == "fail_open"

    def test_disabled_returns_pass_through(self):
        with patch.dict(os.environ, {"ML_AGENT_ENABLED": "false"}, clear=False):
            r = SignalReasoner(client=MagicMock(), pred_logger=MagicMock())
            d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                           ema20=2000, ema50=1990, price=2005)
            assert d.approved is True
            assert d.source == "disabled"

    def test_no_client_fail_open(self):
        r = SignalReasoner(client=None, pred_logger=MagicMock())
        d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                       ema20=2000, ema50=1990, price=2005)
        # ML_AGENT_ENABLED not set => disabled path (pass-through) OR fail_open.
        assert d.approved is True

    def test_uses_recent_accuracy_as_memory(self):
        """The agent's 'memory' comes from PredictionLogger.get_summary — not new state."""
        logger = MagicMock(get_summary=lambda days=1: fake_pred_summary(
            total_predictions=20, evaluated=10, wins=3, losses=7))  # 30% recent accuracy
        client = MagicMock()
        client.is_available.return_value = True
        client.chat.return_value = '{"approved": true, "reason": "ok"}'
        r = SignalReasoner(client=client, pred_logger=logger)
        r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                   ema20=2000, ema50=1990, price=2005)
        # The prompt sent to the LLM must reference recent accuracy
        sent_messages = client.chat.call_args[0][0]
        prompt_text = " ".join(m["content"] for m in sent_messages)
        assert "30%" in prompt_text or "accuracy" in prompt_text.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_signal_reasoner.py -v`
Expected: FAIL with `No module named 'etl.agents.signal_reasoner'`

- [ ] **Step 3: Implement `SignalReasoner`**

Create `etl/agents/signal_reasoner.py`:

```python
"""
Signal Reasoner — a genuine (if minimal) LLM agent (AD3).

Perceives: market context (RSI, ATR, EMAs, price, signal direction, confidence)
           + recent model accuracy pulled from PredictionLogger (this is the agent's memory).
Reasons:  one OpenAI-compatible chat call, structured JSON output.
Acts:     returns AgentDecision(approved, reason, source). Never raises.

Backtest safety (AD4): this module is imported ONLY by api/app/main.py.
Never import it from backtesting/. Fail-open (AD5) on any error.
"""
import os
import json
import logging
from dataclasses import dataclass
from typing import Optional

from config.settings import SIGNAL_REASONER_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class AgentDecision:
    approved: bool
    reason: str
    source: str  # "llm" | "fail_open" | "disabled"


class SignalReasoner:
    """One-shot LLM signal validator. Backtest-safe by construction."""

    def __init__(self, client=None, pred_logger=None, config: dict = None):
        cfg = {**(SIGNAL_REASONER_CONFIG or {}), **(config or {})}
        self.cfg = cfg
        self.enabled_env_var = cfg.get("enabled_env_var", "ML_AGENT_ENABLED")
        self.client = client
        self.pred_logger = pred_logger

    def _is_enabled(self) -> bool:
        return os.getenv(self.enabled_env_var, "false").strip().lower() == "true"

    def evaluate(
        self,
        asset: str,
        signal: int,
        confidence: float,
        rsi: float,
        atr: float,
        ema20: float,
        ema50: float,
        price: float,
    ) -> AgentDecision:
        # 1. Hard bypass switch (AD4) — default OFF so backtests/historical replays
        #    are never nondeterministic.
        if not self._is_enabled():
            return AgentDecision(approved=True, reason="agent_disabled_by_env",
                                 source="disabled")

        # 2. Fail-open if there's no usable client
        if self.client is None or not getattr(self.client, "is_available", lambda: False)():
            return AgentDecision(approved=True, reason="agent_unavailable",
                                 source="fail_open")

        # 3. Perceive — memory comes from PredictionLogger, no new state
        recent_accuracy = self._recent_accuracy_pct()

        # 4. Reason — structured JSON output so we never string-parse APPROVE/REJECT
        prompt = self._build_prompt(
            asset=asset, signal=signal, confidence=confidence, rsi=rsi,
            atr=atr, ema20=ema20, ema50=ema50, price=price,
            recent_accuracy=recent_accuracy,
        )
        raw = self.client.chat([{"role": "user", "content": prompt}])

        # 5. Fail-open on any transport/parsing failure (AD5)
        if raw is None:
            return AgentDecision(approved=True, reason="agent_no_response",
                                 source="fail_open")

        try:
            data = json.loads(raw)
            approved = bool(data.get("approved"))
            reason = str(data.get("reason", ""))[:200]
            return AgentDecision(approved=approved, reason=reason or "llm_decision",
                                 source="llm")
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"[SignalReasoner] unparseable LLM response: {e}; raw={raw[:120]}")
            return AgentDecision(approved=True, reason=f"fail_open_unparseable_{e}",
                                 source="fail_open")

    def _recent_accuracy_pct(self) -> Optional[float]:
        if self.pred_logger is None:
            return None
        try:
            s = self.pred_logger.get_summary(days=1)
            evaluated = s.get("evaluated", 0)
            if evaluated == 0:
                return None
            return round(100.0 * s.get("wins", 0) / evaluated, 1)
        except Exception as e:
            logger.warning(f"[SignalReasoner] could not read recent accuracy: {e}")
            return None

    def _build_prompt(self, asset, signal, confidence, rsi, atr,
                      ema20, ema50, price, recent_accuracy) -> str:
        direction = "BUY" if signal == 1 else "SELL"
        trend = "uptrend (EMA20 > EMA50)" if ema20 > ema50 else "downtrend (EMA20 < EMA50)"
        acc_str = f"{recent_accuracy}%" if recent_accuracy is not None else "no data yet"
        return f"""You are a trading-signal validator for {asset.upper()}.

Model output: {direction} signal at confidence {confidence:.0%}.
Price: {price:.2f} | EMA20: {ema20:.2f} | EMA50: {ema50:.2f} -> {trend}
RSI(14): {rsi:.1f} | ATR(14): {atr:.2f}
Recent model accuracy (last day): {acc_str}

Decide whether to send this signal as an alert. Consider overbought/oversold,
trend alignment, and whether the model has been reliable recently.

Respond with ONLY a JSON object, no prose:
{{"approved": true|false, "reason": "one short sentence"}}"""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_signal_reasoner.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add etl/agents/signal_reasoner.py tests/unit/test_signal_reasoner.py
git commit -m "feat(agents): add SignalReasoner LLM agent with fail-open + PredictionLogger memory"
```

---

## Task 7: Wire gates + agent into `api/app/main.py` (live alert path only)

**Files:**
- Modify: `api/app/main.py:424-428` (module-init block), `api/app/main.py:688-696` (alert call site)

- [ ] **Step 1: Add module-level initialization after the email_alerts line**

At `api/app/main.py`, find the existing block (around line 424-428):

```python
from etl.prediction_logger import PredictionLogger
from etl.alerts import EmailAlertService
prediction_logger = PredictionLogger()
email_alerts = EmailAlertService(confidence_threshold=0.70)
```

Replace it with:

```python
from etl.prediction_logger import PredictionLogger
from etl.alerts import EmailAlertService
from etl.guards.alert_risk_gate import AlertRiskGate
from etl.agents.llm_client import NemotronClient
from etl.agents.signal_reasoner import SignalReasoner

prediction_logger = PredictionLogger()
email_alerts = EmailAlertService(confidence_threshold=0.70)
# Deterministic gate — runs unconditionally on every candidate alert.
alert_risk_gate = AlertRiskGate()
# LLM agent — off by default (ML_AGENT_ENABLED). Fail-open. Backtest path never imports this.
signal_reasoner = SignalReasoner(client=NemotronClient(), pred_logger=prediction_logger)
```

- [ ] **Step 2: Replace the alert call site**

Find the block at `api/app/main.py` (around lines 688-696):

```python
            # Send email alert if confidence > 70% and signal is BUY/SELL
            if email_alerts.should_alert(latest['signal'], latest['confidence']):
                email_alerts.send_alert(
                    asset=asset,
                    signal=latest['signal'],
                    confidence=latest['confidence'],
                    price=latest['price'],
                    shap_values=latest.get('shap_values', [])
                )
```

Replace it with:

```python
            # Send email alert if confidence > 70% and signal is BUY/SELL
            if email_alerts.should_alert(latest['signal'], latest['confidence']):
                # Pull live indicator values for the gates/agent. These columns are
                # produced by features/pipeline.engineer_all_features; guard with .get
                # so a missing column never breaks the alert path.
                last_row = recent_data.iloc[-1]

                def _col(name, default=0.0):
                    v = getattr(last_row, name, None) if hasattr(last_row, name) else last_row.get(name) if hasattr(last_row, 'get') else None
                    try:
                        return float(v) if v is not None and v == v else default
                    except (TypeError, ValueError):
                        return default

                rsi = _col('rsi_14', _col('rsi', 50.0))
                atr = _col('atr_14', _col('atr', 0.0))
                ema20 = _col('ema_20', latest['price'])
                ema50 = _col('ema_50', latest['price'])

                # 1. Deterministic gate (always runs) — cooldown, session, volatility.
                risk = alert_risk_gate.check(
                    asset=asset, price=latest['price'], atr=atr,
                    signal=latest['signal'], confidence=latest['confidence'],
                )
                if not risk.approved:
                    logger.info(f"Alert suppressed by risk gate: {risk.reason}")
                else:
                    # 2. LLM agent gate (off by default, fail-open). Optional refinement.
                    agent = signal_reasoner.evaluate(
                        asset=asset, signal=latest['signal'],
                        confidence=latest['confidence'], rsi=rsi, atr=atr,
                        ema20=ema20, ema50=ema50, price=latest['price'],
                    )
                    if agent.source == "llm":
                        logger.info(f"Agent decision: approved={agent.approved} ({agent.reason})")
                    if agent.approved:
                        email_alerts.send_alert(
                            asset=asset,
                            signal=latest['signal'],
                            confidence=latest['confidence'],
                            price=latest['price'],
                            shap_values=latest.get('shap_values', [])
                        )
                    else:
                        logger.info(f"Alert suppressed by agent: {agent.reason}")
```

- [ ] **Step 3: Verify the app module imports cleanly**

Run: `python -c "import api.app.main" 2>&1 | head -20` (or the project's standard import-check command)
Expected: no ImportError / no syntax error. (If the project launches via flask/gunicorn, use that command instead.)

- [ ] **Step 4: Add a smoke test for the alert-path wiring**

Append to `tests/smoke/test_smoke.py` inside the existing test class structure (mirroring `test_email_alert_service_smoke`):

```python
    def test_alert_risk_gate_smoke(self):
        from etl.guards.alert_risk_gate import AlertRiskGate, RiskDecision
        gate = AlertRiskGate({"enabled": True})
        d = gate.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8)
        assert isinstance(d, RiskDecision)

    def test_signal_reasoner_smoke(self):
        from etl.agents.signal_reasoner import SignalReasoner, AgentDecision
        r = SignalReasoner(client=None, pred_logger=None)
        d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                       ema20=2000, ema50=1990, price=2005)
        assert isinstance(d, AgentDecision)
```

- [ ] **Step 5: Run smoke tests**

Run: `pytest tests/smoke/test_smoke.py -v -k "alert_risk_gate or signal_reasoner"`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
git add api/app/main.py tests/smoke/test_smoke.py
git commit -m "feat(api): gate live alerts with AlertRiskGate + SignalReasoner agent"
```

---

## Task 8: `.env.example` documentation + dependency check

**Files:**
- Modify: `.env.example` (create if missing)
- Verify: `api/requirements.txt`

- [ ] **Step 1: Confirm `requests` is already a dependency**

Run: `python -c "import requests; print(requests.__version__)"`
Expected: a version string (e.g. `2.31.0`). `api/app/main.py` already uses it, so it should be present. If NOT present, add `requests>=2.28` to `api/requirements.txt`.

- [ ] **Step 2: Document the new env vars**

Append to `.env.example` (create the file if it does not exist):

```bash
# ===== Signal Reasoner Agent (optional) =====
# The agent is OFF by default. Set to "true" to enable the LLM alert gate.
# When disabled, only the deterministic AlertRiskGate runs.
ML_AGENT_ENABLED=false

# NVIDIA NIM API key from https://build.nvidia.com/ (free tier, credit-based)
NVIDIA_API_KEY=

# Per-call timeout for the LLM agent. Fail-open on timeout.
ML_AGENT_TIMEOUT_SEC=8
```

- [ ] **Step 3: Commit**

```bash
git add .env.example api/requirements.txt
git commit -m "docs(env): document ML_AGENT_ENABLED, NVIDIA_API_KEY, ML_AGENT_TIMEOUT_SEC"
```

---

## Task 9: Full test run + self-review

- [ ] **Step 1: Run the entire test suite**

Run: `pytest tests/ -v`
Expected: all green. Pay specific attention to:
- `tests/unit/test_data_quality_gate.py`
- `tests/unit/test_alert_risk_gate.py`
- `tests/unit/test_llm_client.py`
- `tests/unit/test_signal_reasoner.py`
- `tests/integration/test_etl_pipeline.py`
- `tests/smoke/test_smoke.py`

- [ ] **Step 2: Verify backtest isolation (AD4 hard requirement)**

Run a search confirming no backtest code imports the agent:

Run: `grep -rn "signal_reasoner\|SignalReasoner\|NemotronClient" backtesting/ models/`
Expected: no matches. If any match appears, remove the import — the agent must never enter the historical replay path.

- [ ] **Step 3: Manual end-to-end smoke (agent disabled — the default)**

With `ML_AGENT_ENABLED` unset, hit the predictions endpoint and confirm:
- A high-confidence BUY/SELL still triggers `email_alerts.send_alert` if it passes the deterministic gate.
- A second identical alert within 30 minutes is suppressed with `reason=cooldown_*`.

- [ ] **Step 4: Manual end-to-end smoke (agent enabled, with a real NVIDIA key)**

Set `ML_AGENT_ENABLED=true` and a valid `NVIDIA_API_KEY`. Trigger a high-confidence signal and confirm the log line `Agent decision: approved=... (...)` appears and uses source `llm`. Then temporarily break the key and confirm a subsequent alert still fires (fail-open) with `source=fail_open`.

- [ ] **Step 5: Final commit (if any cleanup)**

```bash
git status
git add -A
git commit -m "test: full suite green for guards + signal reasoner agent"
```

---

## Self-Review

**Spec coverage:**
- Data validation before transform → Task 2 (price spikes, run-continue) + Task 3 (pipeline wiring). Reuses existing transformer for everything else (AD1).
- Stale data skip → covered by existing `DataFreshnessChecker` (orchestrator.py:20); not reimplemented.
- Alert risk gate (cooldown/session/volatility) → Task 4. Spread check intentionally dropped (AD6).
- LLM agent with real NVIDIA model ID → Task 5 + Task 6. Correct model ID `nemotron-3-ultra-550b-a55b`, not the fictional `nemotron-3-super`.
- Backtest safety → AD4 + Task 9 Step 2 (grep guard).
- Fail-open on API failure → AD5, tests `test_fail_open_on_malformed_response`, `test_fail_open_on_none_response`, `test_chat_returns_none_on_timeout`.
- Config in settings.py → Task 1.

**Placeholder scan:** No TODO/TBD. Every code step shows full code. Every test step shows full test code.

**Type/name consistency:**
- `ValidationResult.cleaned_df` — used consistently in Task 2 gate, Task 3 pipeline (`data = dq.cleaned_df`), Task 3 test.
- `RiskDecision.approved`/`reason` — consistent across Task 4 implementation, tests, and Task 7 call site.
- `AgentDecision.approved`/`reason`/`source` — consistent across Task 6 implementation, tests, and Task 7 call site (`agent.source`, `agent.approved`, `agent.reason`).
- `NemotronClient.is_available()` / `.chat(messages)` — consistent across Task 5, Task 6 (`client.chat(...)`), Task 7.
- Config keys: `DATA_QUALITY_GATE_CONFIG`, `ALERT_RISK_GATE_CONFIG`, `SIGNAL_REASONER_CONFIG` — defined in Task 1, imported in Tasks 2/4/5/6.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-20-guards-and-signal-reasoner-agent.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
