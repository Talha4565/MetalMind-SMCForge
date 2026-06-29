"""Unit tests for explainability.shap_analyzer module."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def _train_dummy_model(xgb, n_features=10, n_samples=200):
    """Train a small dummy XGBoost model for SHAP testing."""
    np.random.seed(42)
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    y = np.random.choice([0, 1], size=n_samples, p=[0.7, 0.3])
    model = xgb.XGBClassifier(
        n_estimators=10, max_depth=3, random_state=42,
        use_label_encoder=False, eval_metric='logloss'
    )
    model.fit(X, y)
    return model, X


class TestShapAnalyzer:
    """Test SHAP analyzer functionality."""

    def test_initialization(self, shap_analyzer_cls, xgb):
        model, _ = _train_dummy_model(xgb)
        analyzer = shap_analyzer_cls(model, sample_size=100)
        assert analyzer.model is model
        assert analyzer.sample_size == 100
        assert analyzer.shap_values is None

    def test_compute_shap_values(self, shap_analyzer_cls, xgb):
        model, X = _train_dummy_model(xgb, n_features=5, n_samples=50)
        analyzer = shap_analyzer_cls(model, sample_size=50)
        shap_vals = analyzer.compute_shap_values(X)
        assert shap_vals is not None
        assert shap_vals.shape[0] == 50
        assert shap_vals.shape[1] == 5

    def test_compute_shap_with_sampling(self, shap_analyzer_cls, xgb):
        model, X = _train_dummy_model(xgb, n_features=5, n_samples=200)
        analyzer = shap_analyzer_cls(model, sample_size=50)
        shap_vals = analyzer.compute_shap_values(X)
        assert shap_vals.shape[0] == 50

    def test_get_top_features(self, shap_analyzer_cls, xgb):
        model, X = _train_dummy_model(xgb, n_features=10, n_samples=100)
        analyzer = shap_analyzer_cls(model, sample_size=100)
        analyzer.compute_shap_values(X)
        top = analyzer.get_top_features(n=5)
        assert len(top) == 5
        assert 'feature' in top.columns
        assert 'importance' in top.columns
        assert top['importance'].is_monotonic_decreasing

    def test_get_top_features_before_compute_raises(self, shap_analyzer_cls, xgb):
        model, _ = _train_dummy_model(xgb)
        analyzer = shap_analyzer_cls(model)
        with pytest.raises(ValueError):
            analyzer.get_top_features()

    def test_explainer_created_after_compute(self, shap_analyzer_cls, xgb):
        model, X = _train_dummy_model(xgb, n_features=5, n_samples=50)
        analyzer = shap_analyzer_cls(model)
        assert analyzer.explainer is None
        analyzer.compute_shap_values(X)
        assert analyzer.explainer is not None
