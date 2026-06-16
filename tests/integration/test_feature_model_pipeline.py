"""Integration tests for the feature engineering + model pipeline."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from features.pipeline import engineer_all_features
from features.labels import generate_labels
from backtesting.engine import BacktestEngine


@pytest.fixture
def engineered_data():
    """Generate synthetic OHLCV and run through feature pipeline."""
    np.random.seed(42)
    n = 500
    dates = pd.date_range('2024-01-01', periods=n, freq='15min')
    close = 2000.0 + np.random.randn(n).cumsum() * 2
    df = pd.DataFrame({
        'open': close - np.random.rand(n) * 2,
        'high': close + np.random.rand(n) * 3,
        'low': close - np.random.rand(n) * 3,
        'close': close,
        'volume': np.random.randint(100, 5000, n)
    }, index=dates)
    return engineer_all_features(df, add_labels=True, asset='gold')


class TestFeatureToModelPipeline:
    """Test features -> model training -> prediction pipeline."""

    def test_features_have_target(self, engineered_data):
        assert 'target' in engineered_data.columns

    def test_target_is_balanced_enough(self, engineered_data):
        target_dist = engineered_data['target'].value_counts(normalize=True)
        assert target_dist.min() > 0.05, "Target class distribution too skewed"

    def test_no_nans_in_features(self, engineered_data):
        assert engineered_data.isna().sum().sum() == 0

    def test_train_xgboost_model(self, engineered_data):
        X = engineered_data.drop(columns=['target'])
        y = engineered_data['target']
        split = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y.iloc[:split], y.iloc[split:]

        model = xgb.XGBClassifier(
            n_estimators=50, max_depth=4, random_state=42,
            use_label_encoder=False, eval_metric='logloss'
        )
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=0)

        predictions = model.predict(X_test)
        assert len(predictions) == len(X_test)
        assert set(predictions).issubset({0, 1})

    def test_model_has_predict_proba(self, engineered_data):
        X = engineered_data.drop(columns=['target'])
        y = engineered_data['target']
        split = int(len(X) * 0.8)
        model = xgb.XGBClassifier(
            n_estimators=50, max_depth=4, random_state=42,
            use_label_encoder=False, eval_metric='logloss'
        )
        model.fit(X.iloc[:split], y.iloc[:split], verbose=0)
        proba = model.predict_proba(X.iloc[split:])
        assert proba.shape[1] == 2
        assert (proba >= 0).all() and (proba <= 1).all()

    def test_backtest_with_model_signals(self, engineered_data):
        X = engineered_data.drop(columns=['target'])
        y = engineered_data['target']
        split = int(len(X) * 0.8)

        model = xgb.XGBClassifier(
            n_estimators=50, max_depth=4, random_state=42,
            use_label_encoder=False, eval_metric='logloss'
        )
        model.fit(X.iloc[:split], y.iloc[:split], verbose=0)
        signals = model.predict(X.iloc[split:])

        test_data = engineered_data.iloc[split:].copy()
        for col in test_data.columns:
            if col not in ['open', 'high', 'low', 'close', 'volume']:
                test_data = test_data.drop(columns=[col], errors='ignore')

        engine = BacktestEngine(asset='gold')
        results = engine.run_backtest(test_data, signals)
        assert 'metrics' in results
        assert 'equity_curve' in results
