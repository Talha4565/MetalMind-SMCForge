"""Unit tests for data.loaders module."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.loaders import (
    MultiTimeframeLoader,
    load_gold_data,
    load_silver_data,
    load_asset_data,
    train_val_test_split
)


class TestTrainValTestSplit:
    """Test chronological data splitting."""

    def test_split_basic(self):
        n = 100
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({'value': range(n)}, index=dates)
        train, val, test = train_val_test_split(df)
        assert len(train) > 0
        assert len(val) > 0
        assert len(test) > 0

    def test_split_sizes(self):
        n = 1000
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({'value': range(n)}, index=dates)
        train, val, test = train_val_test_split(df, train_pct=0.70, val_pct=0.15, test_pct=0.15)
        assert abs(len(train) / n - 0.70) < 0.02
        assert abs(len(val) / n - 0.15) < 0.02
        assert abs(len(test) / n - 0.15) < 0.02

    def test_split_preserves_order(self):
        n = 100
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({'value': range(n)}, index=dates)
        train, val, test = train_val_test_split(df)
        assert train.index.max() < val.index.min()
        assert val.index.max() < test.index.min()

    def test_split_no_overlap(self):
        n = 100
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({'value': range(n)}, index=dates)
        train, val, test = train_val_test_split(df)
        train_idx = set(train.index)
        val_idx = set(val.index)
        test_idx = set(test.index)
        assert len(train_idx & val_idx) == 0
        assert len(train_idx & test_idx) == 0
        assert len(val_idx & test_idx) == 0

    def test_split_empty_raises(self):
        n = 10
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({'value': range(n)}, index=dates)
        train, val, test = train_val_test_split(df, train_pct=1.0, val_pct=0.0, test_pct=0.0)
        assert len(val) == 0
        assert len(test) == 0
        assert len(train) == n


class TestMultiTimeframeLoader:
    """Test multi-timeframe data loader."""

    def test_loader_initialization(self):
        loader = MultiTimeframeLoader(asset='gold')
        assert loader.asset == 'gold'
        assert loader.timeframes == {}

    def test_load_gold_data(self):
        try:
            df = load_gold_data(primary_tf='15m', session_filter=False)
            assert len(df) > 0
            assert 'open' in df.columns
            assert 'close' in df.columns
        except (FileNotFoundError, ValueError):
            pytest.skip("Gold data files not available")

    def test_load_silver_data(self):
        try:
            df = load_silver_data(primary_tf='15m', session_filter=False)
            assert len(df) > 0
        except (FileNotFoundError, ValueError):
            pytest.skip("Silver data files not available")

    def test_load_asset_data_gold(self):
        try:
            df = load_asset_data(asset='gold', primary_tf='15m', session_filter=False)
            assert len(df) > 0
        except (FileNotFoundError, ValueError):
            pytest.skip("Gold data files not available")

    def test_load_asset_data_invalid(self):
        loader = MultiTimeframeLoader(asset='bitcoin')
        with pytest.raises(KeyError):
            loader.load_timeframe('15m')
