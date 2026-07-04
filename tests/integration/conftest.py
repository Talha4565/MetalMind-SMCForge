"""Fixtures for integration tests — mirrors unit/conftest.py for integration scope."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="session")
def engineer_all_features():
    from features.pipeline import engineer_all_features
    return engineer_all_features


@pytest.fixture(scope="session")
def xgb():
    import xgboost as xgb
    return xgb


@pytest.fixture(scope="session")
def backtest_engine():
    from backtesting.engine import BacktestEngine, Trade
    return BacktestEngine, Trade


@pytest.fixture(scope="session")
def etl_pipeline():
    from etl.pipeline import ETLPipeline, PipelineResult, PipelineStatus
    return ETLPipeline, PipelineResult, PipelineStatus
