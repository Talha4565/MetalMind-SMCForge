"""Shared test fixtures for MetalMind-SMCForge tests."""
import sys
import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_ohlcv_df():
    """Generate a realistic sample OHLCV DataFrame for testing."""
    np.random.seed(42)
    n = 500
    dates = pd.date_range('2024-01-01', periods=n, freq='15min')
    trend = np.linspace(1800, 1900, n)
    noise = np.random.randn(n) * 5
    close = trend + noise
    return pd.DataFrame({
        'open': close - np.random.rand(n) * 2,
        'high': close + np.random.rand(n) * 5 + 1,
        'low': close - np.random.rand(n) * 5 - 1,
        'close': close,
        'volume': np.random.randint(100, 10000, n)
    }, index=dates)


@pytest.fixture
def small_ohlcv_df():
    """Small OHLCV DataFrame for fast unit tests."""
    np.random.seed(42)
    n = 100
    dates = pd.date_range('2024-06-01', periods=n, freq='15min')
    close = 2000.0 + np.random.randn(n).cumsum() * 2
    return pd.DataFrame({
        'open': close - np.random.rand(n) * 1,
        'high': close + np.random.rand(n) * 2,
        'low': close - np.random.rand(n) * 2,
        'close': close,
        'volume': np.random.randint(100, 5000, n)
    }, index=dates)


@pytest.fixture
def trending_up_df():
    """DataFrame with clear uptrend for label testing."""
    n = 200
    dates = pd.date_range('2024-01-01', periods=n, freq='15min')
    close = np.linspace(1800, 2000, n)
    return pd.DataFrame({
        'open': close - 1,
        'high': close + 3,
        'low': close - 3,
        'close': close,
        'volume': np.full(n, 1000)
    }, index=dates)


@pytest.fixture
def trending_down_df():
    """DataFrame with clear downtrend for label testing."""
    n = 200
    dates = pd.date_range('2024-01-01', periods=n, freq='15min')
    close = np.linspace(2000, 1800, n)
    return pd.DataFrame({
        'open': close + 1,
        'high': close + 3,
        'low': close - 3,
        'close': close,
        'volume': np.full(n, 1000)
    }, index=dates)


@pytest.fixture
def flat_df():
    """DataFrame with flat/oscillating prices (no clear trend)."""
    n = 200
    dates = pd.date_range('2024-01-01', periods=n, freq='15min')
    close = 2000.0 + np.sin(np.linspace(0, 10 * np.pi, n)) * 2
    return pd.DataFrame({
        'open': close - 0.5,
        'high': close + 1,
        'low': close - 1,
        'close': close,
        'volume': np.full(n, 1000)
    }, index=dates)


@pytest.fixture
def gap_df():
    """DataFrame with price gaps for FVG testing."""
    n = 100
    dates = pd.date_range('2024-01-01', periods=n, freq='15min')
    close = np.ones(n) * 2000.0
    # Create a gap: bar 10 high < bar 12 low
    close[9] = 2000.0
    close[10] = 2000.0
    close[11] = 2010.0  # gap up
    close[12] = 2015.0
    return pd.DataFrame({
        'open': close - 1,
        'high': close + np.random.rand(n) * 2,
        'low': close - np.random.rand(n) * 2,
        'close': close,
        'volume': np.full(n, 1000)
    }, index=dates)


@pytest.fixture
def sample_signals():
    """Sample trading signals array."""
    np.random.seed(42)
    return np.random.choice([0, 1], size=100, p=[0.85, 0.15])


@pytest.fixture
def project_root():
    """Return project root path."""
    return PROJECT_ROOT
