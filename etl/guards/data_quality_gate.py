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

    def __init__(self, config: dict = None, **kwargs):
        cfg = {**(DATA_QUALITY_GATE_CONFIG or {}), **(config or {}), **kwargs}
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
