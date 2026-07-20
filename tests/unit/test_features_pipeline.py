"""Unit tests for features.pipeline module."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestEngineerAllFeatures:
    """Test the complete feature engineering pipeline."""

    def test_adds_many_features(self, small_ohlcv_df, engineer_all_features):
        result = engineer_all_features(small_ohlcv_df, add_labels=False, asset='gold')
        assert len(result.columns) > 30, f"Expected >30 columns, got {len(result.columns)}"

    def test_original_columns_preserved(self, small_ohlcv_df, engineer_all_features):
        result = engineer_all_features(small_ohlcv_df, add_labels=False, asset='gold')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            assert col in result.columns

    def test_labels_added_when_requested(self, small_ohlcv_df, engineer_all_features):
        result = engineer_all_features(small_ohlcv_df, add_labels=True, asset='gold')
        assert 'target' in result.columns

    def test_no_labels_when_disabled(self, small_ohlcv_df, engineer_all_features):
        result = engineer_all_features(small_ohlcv_df, add_labels=False, asset='gold')
        assert 'target' not in result.columns

    def test_does_not_modify_original(self, small_ohlcv_df, engineer_all_features):
        original_cols = list(small_ohlcv_df.columns)
        original_len = len(small_ohlcv_df)
        engineer_all_features(small_ohlcv_df, add_labels=False, asset='gold')
        assert list(small_ohlcv_df.columns) == original_cols
        assert len(small_ohlcv_df) == original_len

    def test_no_nans_in_output(self, small_ohlcv_df, engineer_all_features):
        result = engineer_all_features(small_ohlcv_df, add_labels=False, asset='gold')
        nan_counts = result.isna().sum()
        cols_with_nans = nan_counts[nan_counts > 0]
        assert len(cols_with_nans) == 0, f"Columns with NaN: {cols_with_nans.to_dict()}"

    def test_no_infs_in_output(self, small_ohlcv_df, engineer_all_features):
        result = engineer_all_features(small_ohlcv_df, add_labels=False, asset='gold')
        for col in result.columns:
            assert not np.isinf(result[col]).any(), f"{col} contains inf values"

    def test_gold_vs_silver_features(self, small_ohlcv_df, engineer_all_features):
        gold = engineer_all_features(small_ohlcv_df, add_labels=True, asset='gold')
        silver = engineer_all_features(small_ohlcv_df, add_labels=True, asset='silver')
        assert len(gold.columns) == len(silver.columns)

    def test_with_mtf_columns(self, small_ohlcv_df, engineer_all_features):
        df = small_ohlcv_df.copy()
        df['1h_close'] = df['close'] + 0.5
        df['1h_high'] = df['high'] + 1
        df['1h_low'] = df['low'] - 1
        result = engineer_all_features(df, add_labels=False, asset='gold')
        assert any(c.startswith('htf_') for c in result.columns), "Should add HTF features"

    def test_feature_count_reasonable(self, small_ohlcv_df, engineer_all_features):
        result = engineer_all_features(small_ohlcv_df, add_labels=True, asset='gold')
        assert 30 <= len(result.columns) <= 200, f"Feature count {len(result.columns)} seems unreasonable"
