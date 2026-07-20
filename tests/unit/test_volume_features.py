"""Unit tests for features.volume_features module."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestVWAPDeviation:
    """Test VWAP deviation feature."""

    def test_vwap_columns_added(self, small_ohlcv_df, volume_features):
        result = volume_features["add_vwap_deviation"](small_ohlcv_df)
        for w in [4, 16, 96]:
            assert f'VWAPd_{w}' in result.columns

    def test_vwap_no_inf(self, small_ohlcv_df, volume_features):
        result = volume_features["add_vwap_deviation"](small_ohlcv_df)
        for col in result.columns:
            if col.startswith('VWAPd_'):
                assert not np.isinf(result[col]).any(), f"{col} contains inf"

    def test_vwap_does_not_modify_original(self, small_ohlcv_df, volume_features):
        original_cols = list(small_ohlcv_df.columns)
        volume_features["add_vwap_deviation"](small_ohlcv_df)
        assert list(small_ohlcv_df.columns) == original_cols


class TestCumulativeVolumeDelta:
    """Test CVD feature."""

    def test_cvd_columns_added(self, small_ohlcv_df, volume_features):
        result = volume_features["add_cumulative_volume_delta"](small_ohlcv_df)
        assert 'CVD_4' in result.columns
        assert 'CVD_16' in result.columns
        assert 'CVD_96' in result.columns

    def test_cvd_is_numeric(self, small_ohlcv_df, volume_features):
        result = volume_features["add_cumulative_volume_delta"](small_ohlcv_df)
        assert pd.api.types.is_numeric_dtype(result['CVD_4'])


class TestVolumeImbalance:
    """Test volume imbalance feature."""

    def test_imbalance_columns_added(self, small_ohlcv_df, volume_features):
        result = volume_features["add_volume_imbalance"](small_ohlcv_df)
        assert 'Imbal_4' in result.columns
        assert 'Imbal_16' in result.columns
        assert 'Imbal_96' in result.columns

    def test_imbalance_range(self, small_ohlcv_df, volume_features):
        result = volume_features["add_volume_imbalance"](small_ohlcv_df)
        valid = result['Imbal_4'].dropna()
        assert (valid >= -1).all() and (valid <= 1).all()


class TestWickRatio:
    """Test wick ratio feature."""

    def test_wick_columns_added(self, small_ohlcv_df, volume_features):
        result = volume_features["add_wick_ratio"](small_ohlcv_df)
        assert 'Wick_4' in result.columns
        assert 'Wick_16' in result.columns
        assert 'Wick_96' in result.columns


class TestReturnsVolatility:
    """Test returns and volatility features."""

    def test_returns_columns(self, small_ohlcv_df, volume_features):
        result = volume_features["add_basic_returns_volatility"](small_ohlcv_df)
        assert 'Ret_4' in result.columns
        assert 'Std_4' in result.columns
        assert 'Ret_16' in result.columns
        assert 'Std_16' in result.columns


class TestSessionFlags:
    """Test session flag features."""

    def test_session_flags_added(self, small_ohlcv_df, volume_features):
        result = volume_features["add_session_flags"](small_ohlcv_df)
        assert 'session_asia' in result.columns
        assert 'session_london' in result.columns
        assert 'session_ny' in result.columns
        assert 'session_overlap' in result.columns


class TestAllVolumeFeatures:
    """Test combined volume feature pipeline."""

    def test_adds_many_columns(self, small_ohlcv_df, volume_features):
        result = volume_features["add_all_volume_features"](small_ohlcv_df)
        assert len(result.columns) > len(small_ohlcv_df.columns)

    def test_original_columns_preserved(self, small_ohlcv_df, volume_features):
        result = volume_features["add_all_volume_features"](small_ohlcv_df)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            assert col in result.columns

    def test_does_not_modify_original(self, small_ohlcv_df, volume_features):
        original_len = len(small_ohlcv_df.columns)
        volume_features["add_all_volume_features"](small_ohlcv_df)
        assert len(small_ohlcv_df.columns) == original_len
