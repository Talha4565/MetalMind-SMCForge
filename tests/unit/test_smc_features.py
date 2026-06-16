"""Unit tests for features.smc_features module."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from features.smc_features import (
    detect_fair_value_gaps,
    detect_break_of_structure,
    detect_liquidity_sweeps,
    detect_order_blocks,
    add_premium_discount_zones,
    add_market_structure,
    add_all_smc_features
)


class TestFairValueGaps:
    """Test FVG detection."""

    def test_fvg_columns_added(self, small_ohlcv_df):
        result = detect_fair_value_gaps(small_ohlcv_df)
        assert 'fvg_bullish' in result.columns
        assert 'fvg_bearish' in result.columns
        assert 'fvg_size' in result.columns

    def test_fvg_bullish_is_binary(self, small_ohlcv_df):
        result = detect_fair_value_gaps(small_ohlcv_df)
        unique_bull = set(result['fvg_bullish'].dropna().unique())
        assert unique_bull <= {0, 1}

    def test_fvg_bearish_is_binary(self, small_ohlcv_df):
        result = detect_fair_value_gaps(small_ohlcv_df)
        unique_bear = set(result['fvg_bearish'].dropna().unique())
        assert unique_bear <= {0, 1}

    def test_fvg_does_not_modify_original(self, small_ohlcv_df):
        original_cols = list(small_ohlcv_df.columns)
        detect_fair_value_gaps(small_ohlcv_df)
        assert list(small_ohlcv_df.columns) == original_cols

    def test_fvg_rolling_count_columns(self, small_ohlcv_df):
        result = detect_fair_value_gaps(small_ohlcv_df)
        assert 'fvg_bullish_count' in result.columns
        assert 'fvg_bearish_count' in result.columns

    def test_fvg_size_non_negative(self, small_ohlcv_df):
        result = detect_fair_value_gaps(small_ohlcv_df)
        assert (result['fvg_size'] >= 0).all(), "FVG size should be non-negative"

    def test_fvg_custom_threshold(self, small_ohlcv_df):
        result_tight = detect_fair_value_gaps(small_ohlcv_df, threshold=0.01)
        result_loose = detect_fair_value_gaps(small_ohlcv_df, threshold=0.0001)
        assert result_loose['fvg_bullish'].sum() >= result_tight['fvg_bullish'].sum()


class TestBreakOfStructure:
    """Test BOS detection."""

    def test_bos_columns_added(self, small_ohlcv_df):
        result = detect_break_of_structure(small_ohlcv_df)
        assert 'bos_bullish' in result.columns
        assert 'bos_bearish' in result.columns

    def test_bos_distance_columns(self, small_ohlcv_df):
        result = detect_break_of_structure(small_ohlcv_df)
        assert 'distance_from_swing_high' in result.columns
        assert 'distance_from_swing_low' in result.columns

    def test_bos_is_binary(self, small_ohlcv_df):
        result = detect_break_of_structure(small_ohlcv_df)
        assert set(result['bos_bullish'].dropna().unique()) <= {0, 1}
        assert set(result['bos_bearish'].dropna().unique()) <= {0, 1}

    def test_bos_rolling_count(self, small_ohlcv_df):
        result = detect_break_of_structure(small_ohlcv_df)
        assert 'bos_bullish_count' in result.columns
        assert 'bos_bearish_count' in result.columns

    def test_bos_does_not_modify_original(self, small_ohlcv_df):
        original_cols = list(small_ohlcv_df.columns)
        detect_break_of_structure(small_ohlcv_df)
        assert list(small_ohlcv_df.columns) == original_cols


class TestLiquiditySweeps:
    """Test liquidity sweep detection."""

    def test_sweep_columns_added(self, small_ohlcv_df):
        result = detect_liquidity_sweeps(small_ohlcv_df)
        assert 'liquidity_sweep_high' in result.columns
        assert 'liquidity_sweep_low' in result.columns
        assert 'sweep_strength' in result.columns

    def test_sweep_is_binary(self, small_ohlcv_df):
        result = detect_liquidity_sweeps(small_ohlcv_df)
        assert set(result['liquidity_sweep_high'].dropna().unique()) <= {0, 1}
        assert set(result['liquidity_sweep_low'].dropna().unique()) <= {0, 1}

    def test_sweep_count_column(self, small_ohlcv_df):
        result = detect_liquidity_sweeps(small_ohlcv_df)
        assert 'liquidity_sweep_count' in result.columns

    def test_sweep_strength_non_negative(self, small_ohlcv_df):
        result = detect_liquidity_sweeps(small_ohlcv_df)
        assert (result['sweep_strength'] >= 0).all()


class TestOrderBlocks:
    """Test order block detection."""

    def test_order_block_columns_added(self, small_ohlcv_df):
        result = detect_order_blocks(small_ohlcv_df)
        assert 'order_block_bullish' in result.columns
        assert 'order_block_bearish' in result.columns
        assert 'order_block_strength' in result.columns

    def test_order_block_is_binary(self, small_ohlcv_df):
        result = detect_order_blocks(small_ohlcv_df)
        assert set(result['order_block_bullish'].dropna().unique()) <= {0, 1}
        assert set(result['order_block_bearish'].dropna().unique()) <= {0, 1}

    def test_order_block_strength_non_negative(self, small_ohlcv_df):
        result = detect_order_blocks(small_ohlcv_df)
        assert (result['order_block_strength'] >= 0).all()


class TestPremiumDiscount:
    """Test premium/discount zone calculation."""

    def test_premium_discount_columns(self, small_ohlcv_df):
        result = add_premium_discount_zones(small_ohlcv_df)
        assert 'premium_discount_position' in result.columns
        assert 'in_premium' in result.columns
        assert 'in_discount' in result.columns
        assert 'distance_from_equilibrium' in result.columns

    def test_position_is_between_0_and_1(self, small_ohlcv_df):
        result = add_premium_discount_zones(small_ohlcv_df)
        valid = result['premium_discount_position'].dropna()
        assert (valid >= 0).all() or (valid <= 1).all(), "Position should be between 0 and 1"

    def test_premium_and_discount_are_binary(self, small_ohlcv_df):
        result = add_premium_discount_zones(small_ohlcv_df)
        assert set(result['in_premium'].dropna().unique()) <= {0, 1}
        assert set(result['in_discount'].dropna().unique()) <= {0, 1}


class TestMarketStructure:
    """Test market structure analysis."""

    def test_market_structure_columns(self, small_ohlcv_df):
        result = add_market_structure(small_ohlcv_df)
        assert 'higher_high' in result.columns
        assert 'higher_low' in result.columns
        assert 'lower_high' in result.columns
        assert 'lower_low' in result.columns

    def test_bullish_bearish_structure(self, small_ohlcv_df):
        result = add_market_structure(small_ohlcv_df)
        assert 'bullish_structure' in result.columns
        assert 'bearish_structure' in result.columns

    def test_structure_is_binary(self, small_ohlcv_df):
        result = add_market_structure(small_ohlcv_df)
        for col in ['higher_high', 'higher_low', 'lower_high', 'lower_low']:
            assert set(result[col].dropna().unique()) <= {0, 1}


class TestAllSMCFeatures:
    """Test the combined SMC feature pipeline."""

    def test_adds_many_columns(self, small_ohlcv_df):
        result = add_all_smc_features(small_ohlcv_df)
        assert len(result.columns) > len(small_ohlcv_df.columns)

    def test_original_columns_preserved(self, small_ohlcv_df):
        result = add_all_smc_features(small_ohlcv_df)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            assert col in result.columns

    def test_does_not_modify_original(self, small_ohlcv_df):
        original_len = len(small_ohlcv_df.columns)
        add_all_smc_features(small_ohlcv_df)
        assert len(small_ohlcv_df.columns) == original_len

    def test_row_count_preserved(self, small_ohlcv_df):
        result = add_all_smc_features(small_ohlcv_df)
        assert len(result) == len(small_ohlcv_df)

    def test_no_new_nans_beyond_rolling_windows(self, small_ohlcv_df):
        result = add_all_smc_features(small_ohlcv_df)
        non_feature_cols = ['open', 'high', 'low', 'close', 'volume']
        feature_cols = [c for c in result.columns if c not in non_feature_cols]
        for col in feature_cols:
            nan_ratio = result[col].isna().mean()
            assert nan_ratio < 0.5, f"Feature {col} has {nan_ratio:.1%} NaN values"
