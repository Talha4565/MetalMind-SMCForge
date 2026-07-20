"""Lazy-import fixtures for unit tests — avoids loading ML pipeline at collection time."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="session")
def engineer_all_features():
    from features.pipeline import engineer_all_features
    return engineer_all_features


@pytest.fixture(scope="session")
def data_loaders():
    from data.loaders import (
        MultiTimeframeLoader, load_gold_data, load_silver_data,
        load_asset_data, train_val_test_split,
    )
    return {
        "MultiTimeframeLoader": MultiTimeframeLoader,
        "load_gold_data": load_gold_data,
        "load_silver_data": load_silver_data,
        "load_asset_data": load_asset_data,
        "train_val_test_split": train_val_test_split,
    }


@pytest.fixture(scope="session")
def shap_analyzer_cls():
    from explainability.shap_analyzer import ShapAnalyzer
    return ShapAnalyzer


@pytest.fixture(scope="session")
def xgb():
    import xgboost as xgb
    return xgb


@pytest.fixture(scope="session")
def smc_features():
    from features.smc_features import (
        detect_fair_value_gaps, detect_break_of_structure,
        detect_liquidity_sweeps, detect_order_blocks,
        add_premium_discount_zones, add_market_structure,
        add_all_smc_features,
    )
    return {
        "detect_fair_value_gaps": detect_fair_value_gaps,
        "detect_break_of_structure": detect_break_of_structure,
        "detect_liquidity_sweeps": detect_liquidity_sweeps,
        "detect_order_blocks": detect_order_blocks,
        "add_premium_discount_zones": add_premium_discount_zones,
        "add_market_structure": add_market_structure,
        "add_all_smc_features": add_all_smc_features,
    }


@pytest.fixture(scope="session")
def volume_features():
    from features.volume_features import (
        add_vwap_deviation, add_cumulative_volume_delta,
        add_volume_imbalance, add_wick_ratio,
        add_basic_returns_volatility, add_session_flags,
        add_all_volume_features,
    )
    return {
        "add_vwap_deviation": add_vwap_deviation,
        "add_cumulative_volume_delta": add_cumulative_volume_delta,
        "add_volume_imbalance": add_volume_imbalance,
        "add_wick_ratio": add_wick_ratio,
        "add_basic_returns_volatility": add_basic_returns_volatility,
        "add_session_flags": add_session_flags,
        "add_all_volume_features": add_all_volume_features,
    }


@pytest.fixture(scope="session")
def multi_timeframe():
    from features.multi_timeframe import (
        add_higher_timeframe_features, add_all_multi_timeframe_features,
    )
    return {
        "add_higher_timeframe_features": add_higher_timeframe_features,
        "add_all_multi_timeframe_features": add_all_multi_timeframe_features,
    }


@pytest.fixture(scope="session")
def labels_module():
    from features.labels import generate_labels
    return generate_labels


@pytest.fixture(scope="session")
def backtest_engine():
    from backtesting.engine import BacktestEngine, Trade
    return BacktestEngine, Trade


@pytest.fixture(scope="session")
def etl_pipeline():
    from etl.pipeline import ETLPipeline, PipelineResult, PipelineStatus
    return ETLPipeline, PipelineResult, PipelineStatus


@pytest.fixture(scope="session")
def etl_base_classes():
    from etl.extractors.base import BaseExtractor
    from etl.transformers.base import BaseTransformer
    from etl.loaders.base import BaseLoader
    return BaseExtractor, BaseTransformer, BaseLoader


@pytest.fixture(scope="session")
def etl_config_and_exceptions():
    from etl.exceptions import (
        ETLException, ExtractionError, TransformationError,
        LoadError, ValidationError, ConfigurationError, PipelineError,
    )
    from etl.config import ETLConfig
    return {
        "ETLException": ETLException,
        "ExtractionError": ExtractionError,
        "TransformationError": TransformationError,
        "LoadError": LoadError,
        "ValidationError": ValidationError,
        "ConfigurationError": ConfigurationError,
        "PipelineError": PipelineError,
        "ETLConfig": ETLConfig,
    }


@pytest.fixture(scope="session")
def email_alert_service():
    from etl.alerts import EmailAlertService
    return EmailAlertService
