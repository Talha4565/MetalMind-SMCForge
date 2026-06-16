"""Unit tests for features.multi_timeframe module."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from features.multi_timeframe import (
    add_higher_timeframe_features,
    add_all_multi_timeframe_features
)


class TestHigherTimeframeFeatures:
    """Test higher timeframe feature extraction."""

    def _make_mtf_df(self, n=200):
        """Create a DataFrame with multi-timeframe aligned columns."""
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        close_15m = 2000.0 + np.random.randn(n).cumsum() * 2
        return pd.DataFrame({
            'open': close_15m - 1,
            'high': close_15m + 2,
            'low': close_15m - 2,
            'close': close_15m,
            'volume': np.random.randint(100, 5000, n),
            '1h_close': close_15m + np.random.randn(n) * 0.5,
            '1h_high': close_15m + 3,
            '1h_low': close_15m - 3,
        }, index=dates)

    def test_htf_columns_added(self):
        df = self._make_mtf_df()
        result = add_higher_timeframe_features(df, ['1h_close', '1h_high', '1h_low'], '1h')
        assert 'htf_1h_trend' in result.columns
        assert 'htf_1h_atr' in result.columns
        assert 'htf_1h_rsi' in result.columns
        assert 'htf_1h_dist_high' in result.columns
        assert 'htf_1h_dist_low' in result.columns
        assert 'htf_1h_momentum' in result.columns

    def test_htf_trend_is_binary(self):
        df = self._make_mtf_df()
        result = add_higher_timeframe_features(df, ['1h_close', '1h_high', '1h_low'], '1h')
        valid = result['htf_1h_trend'].dropna()
        assert set(valid.unique()) <= {0, 1}

    def test_htf_atr_non_negative(self):
        df = self._make_mtf_df()
        result = add_higher_timeframe_features(df, ['1h_close', '1h_high', '1h_low'], '1h')
        valid = result['htf_1h_atr'].dropna()
        assert (valid >= 0).all()

    def test_htf_rsi_in_range(self):
        df = self._make_mtf_df()
        result = add_higher_timeframe_features(df, ['1h_close', '1h_high', '1h_low'], '1h')
        valid = result['htf_1h_rsi'].dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_htf_no_close_col_returns_unchanged(self):
        n = 100
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({
            'open': np.ones(n) * 2000,
            'high': np.ones(n) * 2001,
            'low': np.ones(n) * 1999,
            'close': np.ones(n) * 2000,
            'volume': np.ones(n) * 100
        }, index=dates)
        result = add_higher_timeframe_features(df, ['1h_high'], '1h')
        assert result.shape == df.shape

    def test_does_not_modify_original(self):
        df = self._make_mtf_df()
        original_cols = list(df.columns)
        add_higher_timeframe_features(df, ['1h_close', '1h_high', '1h_low'], '1h')
        assert list(df.columns) == original_cols


class TestAllMultiTimeframeFeatures:
    """Test the combined multi-timeframe feature pipeline."""

    def test_adds_htf_features(self):
        dates = pd.date_range('2024-01-01', periods=200, freq='15min')
        close = 2000.0 + np.random.randn(200).cumsum() * 2
        df = pd.DataFrame({
            'open': close - 1,
            'high': close + 2,
            'low': close - 2,
            'close': close,
            'volume': np.random.randint(100, 5000, 200),
            '1h_close': close + 0.5,
            '1h_high': close + 3,
            '1h_low': close - 3,
        }, index=dates)
        result = add_all_multi_timeframe_features(df)
        assert any(c.startswith('htf_') for c in result.columns)

    def test_no_htf_data_returns_original_columns(self):
        dates = pd.date_range('2024-01-01', periods=100, freq='15min')
        df = pd.DataFrame({
            'open': np.ones(100) * 2000,
            'high': np.ones(100) * 2001,
            'low': np.ones(100) * 1999,
            'close': np.ones(100) * 2000,
            'volume': np.ones(100) * 100
        }, index=dates)
        result = add_all_multi_timeframe_features(df)
        assert list(result.columns) == list(df.columns)

    def test_multiple_timeframes(self):
        dates = pd.date_range('2024-01-01', periods=200, freq='15min')
        close = 2000.0 + np.random.randn(200).cumsum() * 2
        df = pd.DataFrame({
            'open': close - 1,
            'high': close + 2,
            'low': close - 2,
            'close': close,
            'volume': np.random.randint(100, 5000, 200),
            '30m_close': close + 0.3,
            '30m_high': close + 2.5,
            '30m_low': close - 2.5,
            '1h_close': close + 0.5,
            '1h_high': close + 3,
            '1h_low': close - 3,
        }, index=dates)
        result = add_all_multi_timeframe_features(df)
        htf_30m = [c for c in result.columns if 'htf_30m_' in c]
        htf_1h = [c for c in result.columns if 'htf_1h_' in c]
        assert len(htf_30m) > 0
        assert len(htf_1h) > 0
