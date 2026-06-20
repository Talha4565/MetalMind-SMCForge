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
        # Both the spike row AND the recovery row are dropped (>10% change in both directions)
        assert result.rows_after < len(df)
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
