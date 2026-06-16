"""Unit tests for etl.prediction_logger module."""
import sys
import json
import tempfile
from pathlib import Path
import pytest
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl.prediction_logger import PredictionLogger


class TestPredictionLogger:
    """Test prediction logging functionality."""

    def _make_logger(self, tmp_path):
        return PredictionLogger(log_dir=str(tmp_path))

    def test_creates_log_directory(self, tmp_path):
        log_dir = tmp_path / 'predictions'
        logger = self._make_logger(log_dir)
        assert log_dir.exists()

    def test_log_prediction_returns_record(self, tmp_path):
        logger = self._make_logger(tmp_path)
        record = logger.log_prediction(
            asset='gold',
            signal=1,
            confidence=0.85,
            price=2000.0,
            shap_values=[{'feature': 'rsi', 'contribution': 0.1}],
            model_version='v1.0'
        )
        assert record['asset'] == 'gold'
        assert record['signal'] == 1
        assert record['signal_text'] == 'BUY'
        assert record['confidence'] == 0.85
        assert record['price'] == 2000.0

    def test_log_prediction_creates_file(self, tmp_path):
        logger = self._make_logger(tmp_path)
        logger.log_prediction(asset='gold', signal=1, confidence=0.8, price=2000.0)
        assert logger.current_file.exists()

    def test_log_prediction_appends_to_file(self, tmp_path):
        logger = self._make_logger(tmp_path)
        logger.log_prediction(asset='gold', signal=1, confidence=0.8, price=2000.0)
        logger.log_prediction(asset='silver', signal=-1, confidence=0.7, price=25.0)
        with open(logger.current_file, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_log_prediction_json_format(self, tmp_path):
        logger = self._make_logger(tmp_path)
        logger.log_prediction(asset='gold', signal=0, confidence=0.5, price=2000.0)
        with open(logger.current_file, 'r') as f:
            record = json.loads(f.readline())
        assert 'timestamp' in record
        assert 'asset' in record
        assert 'signal' in record
        assert 'confidence' in record
        assert record['actual_outcome'] is None

    def test_log_sell_signal(self, tmp_path):
        logger = self._make_logger(tmp_path)
        record = logger.log_prediction(asset='gold', signal=-1, confidence=0.9, price=2000.0)
        assert record['signal_text'] == 'SELL'

    def test_log_hold_signal(self, tmp_path):
        logger = self._make_logger(tmp_path)
        record = logger.log_prediction(asset='gold', signal=0, confidence=0.5, price=2000.0)
        assert record['signal_text'] == 'HOLD'

    def test_log_batch(self, tmp_path):
        logger = self._make_logger(tmp_path)
        preds = [
            {'asset': 'gold', 'signal': 1, 'confidence': 0.8, 'price': 2000.0},
            {'asset': 'silver', 'signal': -1, 'confidence': 0.7, 'price': 25.0},
        ]
        logger.log_batch(preds)
        with open(logger.current_file, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_shap_values_truncated(self, tmp_path):
        logger = self._make_logger(tmp_path)
        shap_vals = [{'feature': f'f{i}', 'contribution': i * 0.1} for i in range(20)]
        record = logger.log_prediction(
            asset='gold', signal=1, confidence=0.8, price=2000.0,
            shap_values=shap_vals
        )
        assert len(record['shap_values']) == 5

    def test_get_summary_empty(self, tmp_path):
        logger = self._make_logger(tmp_path)
        summary = logger.get_summary(days=1)
        assert summary['total_predictions'] == 0
        assert summary['buy_signals'] == 0

    def test_get_summary_with_data(self, tmp_path):
        logger = self._make_logger(tmp_path)
        logger.log_prediction(asset='gold', signal=1, confidence=0.8, price=2000.0)
        logger.log_prediction(asset='gold', signal=-1, confidence=0.7, price=1990.0)
        summary = logger.get_summary(days=1)
        assert summary['total_predictions'] == 2
        assert summary['buy_signals'] == 1
        assert summary['sell_signals'] == 1
