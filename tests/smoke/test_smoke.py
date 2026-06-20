"""Smoke tests — quick verification that all modules import and basic flows work."""
import sys
from pathlib import Path
import pytest
import importlib

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestModuleImports:
    """Verify all critical modules can be imported."""

    def test_import_config_settings(self):
        mod = importlib.import_module('config.settings')
        assert hasattr(mod, 'PROJECT_ROOT')
        assert hasattr(mod, 'ASSETS')

    def test_import_features_labels(self):
        mod = importlib.import_module('features.labels')
        assert hasattr(mod, 'generate_labels')

    def test_import_features_smc(self):
        mod = importlib.import_module('features.smc_features')
        assert hasattr(mod, 'add_all_smc_features')

    def test_import_features_volume(self):
        mod = importlib.import_module('features.volume_features')
        assert hasattr(mod, 'add_all_volume_features')

    def test_import_features_multi_tf(self):
        mod = importlib.import_module('features.multi_timeframe')
        assert hasattr(mod, 'add_all_multi_timeframe_features')

    def test_import_features_pipeline(self):
        mod = importlib.import_module('features.pipeline')
        assert hasattr(mod, 'engineer_all_features')

    def test_import_backtesting_engine(self):
        mod = importlib.import_module('backtesting.engine')
        assert hasattr(mod, 'BacktestEngine')

    def test_import_data_loaders(self):
        mod = importlib.import_module('data.loaders')
        assert hasattr(mod, 'MultiTimeframeLoader')

    def test_import_etl_pipeline(self):
        mod = importlib.import_module('etl.pipeline')
        assert hasattr(mod, 'ETLPipeline')

    def test_import_etl_exceptions(self):
        mod = importlib.import_module('etl.exceptions')
        assert hasattr(mod, 'PipelineError')

    def test_import_etl_config(self):
        mod = importlib.import_module('etl.config')
        assert hasattr(mod, 'ETLConfig')

    def test_import_etl_prediction_logger(self):
        mod = importlib.import_module('etl.prediction_logger')
        assert hasattr(mod, 'PredictionLogger')

    def test_import_etl_alerts(self):
        mod = importlib.import_module('etl.alerts')
        assert hasattr(mod, 'EmailAlertService')

    def test_import_shap_analyzer(self):
        mod = importlib.import_module('explainability.shap_analyzer')
        assert hasattr(mod, 'ShapAnalyzer')


class TestBasicFlows:
    """Smoke test core data flows end-to-end."""

    def test_config_helpers_work(self):
        from config.settings import get_label_params, get_session_times, get_xgboost_params
        assert isinstance(get_label_params('gold'), dict)
        assert isinstance(get_session_times(), dict)
        assert isinstance(get_xgboost_params(), dict)

    def test_label_generation_smoke(self):
        import pandas as pd
        import numpy as np
        from features.labels import generate_labels
        n = 50
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({
            'open': np.linspace(2000, 2100, n),
            'high': np.linspace(2005, 2105, n),
            'low': np.linspace(1995, 2095, n),
            'close': np.linspace(2000, 2100, n),
            'volume': np.full(n, 1000)
        }, index=dates)
        labels = generate_labels(df, asset='gold')
        assert len(labels) == n

    def test_smc_features_smoke(self):
        import pandas as pd
        import numpy as np
        from features.smc_features import add_all_smc_features
        n = 100
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({
            'open': 2000.0 + np.random.randn(n).cumsum(),
            'high': 2000.0 + np.random.randn(n).cumsum() + 2,
            'low': 2000.0 + np.random.randn(n).cumsum() - 2,
            'close': 2000.0 + np.random.randn(n).cumsum(),
            'volume': np.random.randint(100, 1000, n)
        }, index=dates)
        result = add_all_smc_features(df)
        assert len(result.columns) > len(df.columns)

    def test_volume_features_smoke(self):
        import pandas as pd
        import numpy as np
        from features.volume_features import add_all_volume_features
        n = 100
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({
            'open': 2000.0 + np.random.randn(n).cumsum(),
            'high': 2000.0 + np.random.randn(n).cumsum() + 2,
            'low': 2000.0 + np.random.randn(n).cumsum() - 2,
            'close': 2000.0 + np.random.randn(n).cumsum(),
            'volume': np.random.randint(100, 1000, n)
        }, index=dates)
        result = add_all_volume_features(df)
        assert len(result.columns) > len(df.columns)

    def test_feature_pipeline_smoke(self):
        import pandas as pd
        import numpy as np
        from features.pipeline import engineer_all_features
        n = 100
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({
            'open': 2000.0 + np.random.randn(n).cumsum(),
            'high': 2000.0 + np.random.randn(n).cumsum() + 2,
            'low': 2000.0 + np.random.randn(n).cumsum() - 2,
            'close': 2000.0 + np.random.randn(n).cumsum(),
            'volume': np.random.randint(100, 1000, n)
        }, index=dates)
        result = engineer_all_features(df, add_labels=True, asset='gold')
        assert 'target' in result.columns
        assert len(result.columns) > 20

    def test_backtest_smoke(self):
        import pandas as pd
        import numpy as np
        from backtesting.engine import BacktestEngine
        n = 50
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({
            'open': 2000.0 + np.random.randn(n).cumsum(),
            'high': 2000.0 + np.random.randn(n).cumsum() + 3,
            'low': 2000.0 + np.random.randn(n).cumsum() - 3,
            'close': 2000.0 + np.random.randn(n).cumsum(),
            'volume': np.full(n, 1000)
        }, index=dates)
        engine = BacktestEngine(asset='gold')
        signals = np.zeros(n, dtype=int)
        signals[5] = 1
        signals[20] = 1
        results = engine.run_backtest(df, signals)
        assert 'metrics' in results

    def test_etl_config_smoke(self):
        from etl.config import ETLConfig
        config = ETLConfig()
        assert config.schedule_interval_minutes == 15

    def test_prediction_logger_smoke(self, tmp_path):
        from etl.prediction_logger import PredictionLogger
        logger = PredictionLogger(log_dir=str(tmp_path))
        record = logger.log_prediction(asset='gold', signal=1, confidence=0.8, price=2000.0)
        assert record['asset'] == 'gold'

    def test_email_alert_service_smoke(self):
        from etl.alerts import EmailAlertService
        service = EmailAlertService(
            sender_email='test@test.com',
            sender_password='pass',
            recipient_email='rec@test.com'
        )
        assert service.should_alert(signal=1, confidence=0.9) is True
        assert service.should_alert(signal=0, confidence=0.9) is False

    def test_shap_analyzer_smoke(self):
        import numpy as np
        import pandas as pd
        import xgboost as xgb
        from explainability.shap_analyzer import ShapAnalyzer
        X = pd.DataFrame(np.random.randn(50, 5), columns=[f'f{i}' for i in range(5)])
        y = np.random.choice([0, 1], 50)
        model = xgb.XGBClassifier(n_estimators=10, random_state=42,
                                   use_label_encoder=False, eval_metric='logloss')
        model.fit(X, y)
        analyzer = ShapAnalyzer(model, sample_size=50)
        shap_vals = analyzer.compute_shap_values(X)
        assert shap_vals is not None

    def test_etl_exceptions_smoke(self):
        from etl.exceptions import PipelineError, ExtractionError, LoadError
        try:
            raise PipelineError("test")
        except PipelineError as e:
            assert str(e) == "test"

    def test_alert_risk_gate_smoke(self):
        from etl.guards.alert_risk_gate import AlertRiskGate, RiskDecision
        gate = AlertRiskGate({"enabled": True})
        d = gate.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8)
        assert isinstance(d, RiskDecision)

    def test_signal_reasoner_smoke(self):
        from etl.agents.signal_reasoner import SignalReasoner, AgentDecision
        r = SignalReasoner(client=None, pred_logger=None)
        d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                       ema20=2000, ema50=1990, price=2005)
        assert isinstance(d, AgentDecision)
