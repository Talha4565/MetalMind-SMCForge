"""Unit tests for features.labels module."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from features.labels import generate_labels


class TestLabelGeneration:
    """Test triple-barrier label generation."""

    def test_labels_are_binary(self, trending_up_df):
        labels = generate_labels(trending_up_df, asset='gold')
        unique_vals = set(labels.unique())
        assert unique_vals <= {0.0, 1.0}, f"Labels must be 0 or 1, got {unique_vals}"

    def test_labels_match_dataframe_index(self, small_ohlcv_df):
        labels = generate_labels(small_ohlcv_df, asset='gold')
        assert len(labels) == len(small_ohlcv_df)
        assert labels.index.equals(small_ohlcv_df.index)

    def test_uptrend_has_positive_labels(self):
        n = 200
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        # Steep uptrend: ~0.15% per bar to ensure TP hits within 6 bars
        close = 1800.0 + np.arange(n) * 3.0
        df = pd.DataFrame({
            'open': close - 1,
            'high': close + 3,
            'low': close - 3,
            'close': close,
            'volume': np.full(n, 1000)
        }, index=dates)
        labels = generate_labels(df, asset='gold')
        assert labels.sum() > 0, "Steep uptrend should generate positive labels"

    def test_downtrend_has_fewer_positive_labels(self):
        n = 200
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        close_down = 2000.0 - np.arange(n) * 3.0
        df_down = pd.DataFrame({
            'open': close_down + 1,
            'high': close_down + 3,
            'low': close_down - 3,
            'close': close_down,
            'volume': np.full(n, 1000)
        }, index=dates)
        labels = generate_labels(df_down, asset='gold')

        close_up = 1800.0 + np.arange(n) * 3.0
        df_up = pd.DataFrame({
            'open': close_up - 1,
            'high': close_up + 3,
            'low': close_up - 3,
            'close': close_up,
            'volume': np.full(n, 1000)
        }, index=dates)
        up_labels = generate_labels(df_up, asset='gold')
        assert labels.sum() <= up_labels.sum(), "Downtrend should have fewer positive labels"

    def test_labels_with_custom_params(self, small_ohlcv_df):
        labels_default = generate_labels(small_ohlcv_df, asset='gold')
        labels_tight = generate_labels(
            small_ohlcv_df,
            take_profit_pct=0.0001,
            stop_loss_pct=0.0001,
            max_bars=3,
            asset='gold'
        )
        assert len(labels_tight) == len(labels_default)

    def test_labels_gold_vs_silver_params(self, small_ohlcv_df):
        gold_labels = generate_labels(small_ohlcv_df, asset='gold')
        silver_labels = generate_labels(small_ohlcv_df, asset='silver')
        assert len(gold_labels) == len(silver_labels)

    def test_labels_last_bars_are_zero(self, small_ohlcv_df):
        labels = generate_labels(small_ohlcv_df, asset='gold')
        max_bars = 6
        assert labels.iloc[-max_bars:].sum() == 0, "Last max_bars labels should be 0"

    def test_custom_tp_higher_creates_more_labels(self, small_ohlcv_df):
        labels_low = generate_labels(
            small_ohlcv_df, take_profit_pct=0.05, stop_loss_pct=0.01, asset='gold'
        )
        labels_high = generate_labels(
            small_ohlcv_df, take_profit_pct=0.0001, stop_loss_pct=0.0001, asset='gold'
        )
        assert labels_high.sum() >= labels_low.sum(), "Lower TP threshold should produce more positive labels"

    def test_labels_series_name(self, small_ohlcv_df):
        labels = generate_labels(small_ohlcv_df, asset='gold')
        assert labels.name == 'target'

    def test_labels_with_empty_bars(self):
        n = 20
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({
            'open': np.full(n, 2000.0),
            'high': np.full(n, 2001.0),
            'low': np.full(n, 1999.0),
            'close': np.full(n, 2000.0),
            'volume': np.full(n, 100)
        }, index=dates)
        labels = generate_labels(df, asset='gold')
        assert labels.sum() == 0, "Flat prices with tight params should produce 0 positive labels"
