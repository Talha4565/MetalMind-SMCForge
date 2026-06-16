"""Unit tests for features.volume_features module."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from features.volume_features import (
    add_vwap_deviation,
    add_cumulative_volume_delta,
    add_volume_imbalance,
    add_wick_ratio,
    add_basic_returns_volatility,
    add_session_flags,
    add_all_volume_features
)


class TestVWAPDeviation:
    """Test VWAP deviation feature."""

    def test_vwap_columns_added(self, small_ohlcv_df):
        result = add_vwap_deviation(small_ohlcv_df)
        for w in [4, 16, 96]:
            assert f'VWAPd_{w}' in result.columns

    def test_vwap_no_inf(self, small_ohlcv_df):
        result = add_vwap_deviation(small_ohlcv_df)
        for w in [4, 16, 96]:
            assert not np.isinf(result[f'VWAPd_{w}']).any(), f"VWAPd_{w} contains inf"

    def test_vwap_custom_windows(self, small_ohlcv_df):
        result = add_vwap_deviation(small_ohlcv_df, windows=[4, 10])
        assert 'VWAPd_4' in result.columns
        assert 'VWAPd_10' in result.columns
        assert 'VWAPd_16' not in result.columns

    def test_vwap_does_not_modify_original(self, small_ohlcv_df):
        original_cols = list(small_ohlcv_df.columns)
        add_vwap_deviation(small_ohlcv_df)
        assert list(small_ohlcv_df.columns) == original_cols


class TestCumulativeVolumeDelta:
    """Test CVD feature."""

    def test_cvd_columns_added(self, small_ohlcv_df):
        result = add_cumulative_volume_delta(small_ohlcv_df)
        for w in [4, 16, 96]:
            assert f'CVD_{w}' in result.columns

    def test_cvd_positive_for_uptrend(self, small_ohlcv_df):
        df = small_ohlcv_df.copy()
        df['close'] = df['open'] + 1  # All green candles
        result = add_cumulative_volume_delta(df)
        assert (result['CVD_4'].dropna() >= 0).all(), "All green candles should have positive CVD"

    def test_cvd_negative_for_downtrend(self, small_ohlcv_df):
        df = small_ohlcv_df.copy()
        df['close'] = df['open'] - 1  # All red candles
        result = add_cumulative_volume_delta(df)
        assert (result['CVD_4'].dropna() <= 0).all(), "All red candles should have negative CVD"


class TestVolumeImbalance:
    """Test volume imbalance feature."""

    def test_imbalance_columns_added(self, small_ohlcv_df):
        result = add_volume_imbalance(small_ohlcv_df)
        for w in [4, 16, 96]:
            assert f'Imbal_{w}' in result.columns

    def test_imbalance_range(self, small_ohlcv_df):
        result = add_volume_imbalance(small_ohlcv_df)
        for w in [4, 16, 96]:
            valid = result[f'Imbal_{w}'].dropna()
            assert valid.min() >= -1, f"Imbalance {w} below -1"
            assert valid.max() <= 1, f"Imbalance {w} above 1"


class TestWickRatio:
    """Test wick ratio feature."""

    def test_wick_columns_added(self, small_ohlcv_df):
        result = add_wick_ratio(small_ohlcv_df)
        for w in [4, 16, 96]:
            assert f'Wick_{w}' in result.columns

    def test_wick_ratio_non_negative(self, small_ohlcv_df):
        result = add_wick_ratio(small_ohlcv_df)
        for w in [4, 16, 96]:
            valid = result[f'Wick_{w}'].dropna()
            assert (valid >= 0).all(), f"Wick_{w} should be non-negative"


class TestReturnsVolatility:
    """Test returns and volatility features."""

    def test_return_columns_added(self, small_ohlcv_df):
        result = add_basic_returns_volatility(small_ohlcv_df)
        for w in [4, 16, 96]:
            assert f'Ret_{w}' in result.columns
            assert f'Std_{w}' in result.columns

    def test_std_non_negative(self, small_ohlcv_df):
        result = add_basic_returns_volatility(small_ohlcv_df)
        for w in [4, 16, 96]:
            valid = result[f'Std_{w}'].dropna()
            assert (valid >= 0).all(), f"Std_{w} should be non-negative"


class TestSessionFlags:
    """Test session flag features."""

    def test_session_columns_added(self, small_ohlcv_df):
        result = add_session_flags(small_ohlcv_df)
        assert 'session_asia' in result.columns
        assert 'session_london' in result.columns
        assert 'session_ny' in result.columns
        assert 'session_overlap' in result.columns

    def test_session_flags_are_binary(self, small_ohlcv_df):
        result = add_session_flags(small_ohlcv_df)
        for col in ['session_asia', 'session_london', 'session_ny', 'session_overlap']:
            assert set(result[col].unique()) <= {0, 1}

    def test_sessions_are_mutually_consistent(self, small_ohlcv_df):
        result = add_session_flags(small_ohlcv_df)
        # Overlap should be subset of both london and ny
        overlap_mask = result['session_overlap'] == 1
        if overlap_mask.any():
            assert (result.loc[overlap_mask, 'session_london'] == 1).all()
            assert (result.loc[overlap_mask, 'session_ny'] == 1).all()


class TestAllVolumeFeatures:
    """Test combined volume feature pipeline."""

    def test_adds_many_columns(self, small_ohlcv_df):
        result = add_all_volume_features(small_ohlcv_df)
        assert len(result.columns) > len(small_ohlcv_df.columns) + 10

    def test_original_columns_preserved(self, small_ohlcv_df):
        result = add_all_volume_features(small_ohlcv_df)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            assert col in result.columns

    def test_row_count_preserved(self, small_ohlcv_df):
        result = add_all_volume_features(small_ohlcv_df)
        assert len(result) == len(small_ohlcv_df)

    def test_no_infs_in_output(self, small_ohlcv_df):
        result = add_all_volume_features(small_ohlcv_df)
        for col in result.columns:
            assert not np.isinf(result[col]).any(), f"{col} contains inf values"
