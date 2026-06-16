"""Unit tests for config.settings module."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestConfigSettings:
    """Test configuration settings and helper functions."""

    def test_project_root_exists(self):
        from config.settings import PROJECT_ROOT
        assert PROJECT_ROOT.exists()
        assert PROJECT_ROOT.is_dir()

    def test_data_dir_exists(self):
        from config.settings import DATA_DIR
        assert DATA_DIR.exists()

    def test_models_dir_exists(self):
        from config.settings import MODELS_DIR
        assert MODELS_DIR.exists()

    def test_reports_dir_exists(self):
        from config.settings import REPORTS_DIR
        assert REPORTS_DIR.exists()

    def test_assets_config_has_gold_and_silver(self):
        from config.settings import ASSETS
        assert 'gold' in ASSETS
        assert 'silver' in ASSETS

    def test_gold_asset_structure(self):
        from config.settings import ASSETS
        gold = ASSETS['gold']
        assert gold['name'] == 'XAU/USD'
        assert '5m' in gold['files']
        assert '15m' in gold['files']
        assert '30m' in gold['files']
        assert '1h' in gold['files']

    def test_silver_asset_structure(self):
        from config.settings import ASSETS
        silver = ASSETS['silver']
        assert silver['name'] == 'XAG/USD'
        assert '5m' in silver['files']
        assert '15m' in silver['files']

    def test_get_asset_file_gold_15m(self):
        from config.settings import get_asset_file
        path = get_asset_file('gold', '15m')
        assert isinstance(path, Path)

    def test_get_asset_file_silver_15m(self):
        from config.settings import get_asset_file
        path = get_asset_file('silver', '15m')
        assert isinstance(path, Path)

    def test_get_asset_file_invalid_asset(self):
        from config.settings import get_asset_file
        with pytest.raises(KeyError):
            get_asset_file('bitcoin', '15m')

    def test_get_asset_file_invalid_timeframe(self):
        from config.settings import get_asset_file
        with pytest.raises(KeyError):
            get_asset_file('gold', '2m')

    def test_get_label_params_gold(self):
        from config.settings import get_label_params
        params = get_label_params('gold')
        assert 'take_profit_pct' in params
        assert 'stop_loss_pct' in params
        assert 'max_bars' in params
        assert params['take_profit_pct'] > 0
        assert params['stop_loss_pct'] > 0
        assert params['max_bars'] > 0

    def test_get_label_params_silver(self):
        from config.settings import get_label_params
        params = get_label_params('silver')
        assert params['take_profit_pct'] > 0
        assert params['stop_loss_pct'] > 0

    def test_get_label_params_default_is_gold(self):
        from config.settings import get_label_params
        gold = get_label_params('gold')
        default = get_label_params()
        assert gold == default

    def test_gold_has_higher_volatility_thresholds_than_silver(self):
        from config.settings import get_label_params
        gold = get_label_params('gold')
        silver = get_label_params('silver')
        assert gold['take_profit_pct'] > silver['take_profit_pct']
        assert gold['stop_loss_pct'] > silver['stop_loss_pct']

    def test_get_session_times(self):
        from config.settings import get_session_times
        times = get_session_times()
        assert 'enabled' in times
        assert 'start_time' in times
        assert 'end_time' in times
        assert isinstance(times['start_time'], str)
        assert isinstance(times['end_time'], str)

    def test_get_xgboost_params(self):
        from config.settings import get_xgboost_params
        params = get_xgboost_params()
        assert 'n_estimators' in params
        assert 'objective' in params
        assert params['objective'] == 'binary:logistic'
        assert params['random_state'] == 42

    def test_baseline_config_structure(self):
        from config.settings import BASELINE_CONFIG
        assert 'primary_timeframe' in BASELINE_CONFIG
        assert BASELINE_CONFIG['primary_timeframe'] == '15m'
        assert 'label_params' in BASELINE_CONFIG
        assert 'train_split' in BASELINE_CONFIG
        assert 'xgboost_params' in BASELINE_CONFIG

    def test_feature_config_structure(self):
        from config.settings import FEATURE_CONFIG
        assert 'volume_features' in FEATURE_CONFIG
        assert 'smc_features' in FEATURE_CONFIG
        assert 'multi_timeframe' in FEATURE_CONFIG
        assert 'technical' in FEATURE_CONFIG

    def test_backtest_config_structure(self):
        from config.settings import BACKTEST_CONFIG
        assert 'initial_capital' in BACKTEST_CONFIG
        assert BACKTEST_CONFIG['initial_capital'] > 0
        assert 'risk_per_trade_usd' in BACKTEST_CONFIG
        assert 'commission_pct' in BACKTEST_CONFIG
        assert 'slippage_pct' in BACKTEST_CONFIG

    def test_model_config_structure(self):
        from config.settings import MODEL_CONFIG
        assert 'baseline_model_path' in MODEL_CONFIG
        assert 'enhanced_model_path' in MODEL_CONFIG
        assert 'ensemble_size' in MODEL_CONFIG

    def test_train_split_sums_to_one(self):
        from config.settings import BASELINE_CONFIG
        split = BASELINE_CONFIG['train_split']
        total = split['train'] + split['val'] + split['test']
        assert abs(total - 1.0) < 0.01

    def test_api_config_structure(self):
        from config.settings import API_CONFIG
        assert 'host' in API_CONFIG
        assert 'port' in API_CONFIG
        assert API_CONFIG['port'] == 5000
