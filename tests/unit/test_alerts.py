"""Unit tests for etl.alerts module."""
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl.alerts import EmailAlertService


class TestEmailAlertService:
    """Test email alert service."""

    def test_init_without_env(self):
        service = EmailAlertService(
            smtp_host='smtp.gmail.com',
            smtp_port=587,
            sender_email='test@test.com',
            sender_password='password',
            recipient_email='recipient@test.com'
        )
        assert service.enabled is True

    def test_init_without_credentials(self):
        service = EmailAlertService(
            smtp_host='',
            sender_email='',
            sender_password='',
            recipient_email=''
        )
        assert service.enabled is False

    def test_should_alert_buy_above_threshold(self):
        service = EmailAlertService(
            sender_email='test@test.com',
            sender_password='pass',
            recipient_email='rec@test.com',
            confidence_threshold=0.70
        )
        assert service.should_alert(signal=1, confidence=0.85) is True

    def test_should_alert_sell_above_threshold(self):
        service = EmailAlertService(
            sender_email='test@test.com',
            sender_password='pass',
            recipient_email='rec@test.com',
            confidence_threshold=0.70
        )
        assert service.should_alert(signal=-1, confidence=0.80) is True

    def test_should_not_alert_below_threshold(self):
        service = EmailAlertService(
            sender_email='test@test.com',
            sender_password='pass',
            recipient_email='rec@test.com',
            confidence_threshold=0.70
        )
        assert service.should_alert(signal=1, confidence=0.60) is False

    def test_should_not_alert_hold(self):
        service = EmailAlertService(
            sender_email='test@test.com',
            sender_password='pass',
            recipient_email='rec@test.com',
            confidence_threshold=0.70
        )
        assert service.should_alert(signal=0, confidence=0.95) is False

    def test_should_not_alert_when_disabled(self):
        service = EmailAlertService(
            sender_email='',
            sender_password='',
            recipient_email=''
        )
        assert service.should_alert(signal=1, confidence=0.95) is False

    def test_send_alert_disabled_returns_false(self):
        service = EmailAlertService(
            sender_email='',
            sender_password='',
            recipient_email=''
        )
        result = service.send_alert(
            asset='gold', signal=1, confidence=0.9, price=2000.0
        )
        assert result is False

    def test_send_alert_below_threshold_returns_false(self):
        service = EmailAlertService(
            sender_email='test@test.com',
            sender_password='pass',
            recipient_email='rec@test.com',
            confidence_threshold=0.70
        )
        result = service.send_alert(
            asset='gold', signal=1, confidence=0.5, price=2000.0
        )
        assert result is False

    @patch('etl.alerts.smtplib.SMTP')
    def test_send_alert_success(self, mock_smtp):
        service = EmailAlertService(
            smtp_host='smtp.gmail.com',
            smtp_port=587,
            sender_email='test@gmail.com',
            sender_password='app_password',
            recipient_email='recipient@gmail.com',
            confidence_threshold=0.70
        )
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda s: mock_server
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = service.send_alert(
            asset='gold',
            signal=1,
            confidence=0.85,
            price=2000.0,
            shap_values=[{'feature': 'rsi_14', 'contribution': 0.05}]
        )
        assert result is True

    @patch('etl.alerts.smtplib.SMTP')
    def test_send_alert_with_shap_values(self, mock_smtp):
        service = EmailAlertService(
            smtp_host='smtp.gmail.com',
            smtp_port=587,
            sender_email='test@gmail.com',
            sender_password='app_password',
            recipient_email='recipient@gmail.com',
            confidence_threshold=0.70
        )
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda s: mock_server
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = service.send_alert(
            asset='silver',
            signal=-1,
            confidence=0.90,
            price=25.50,
            shap_values=[
                {'feature': 'cvd_16', 'contribution': -0.03},
                {'feature': 'rsi_14', 'contribution': 0.02}
            ]
        )
        assert result is True

    @patch('etl.alerts.smtplib.SMTP')
    def test_send_alert_smtp_error_returns_false(self, mock_smtp):
        service = EmailAlertService(
            smtp_host='smtp.gmail.com',
            smtp_port=587,
            sender_email='test@gmail.com',
            sender_password='app_password',
            recipient_email='recipient@gmail.com',
            confidence_threshold=0.70
        )
        mock_smtp.return_value.__enter__ = MagicMock(side_effect=Exception("Connection refused"))
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = service.send_alert(
            asset='gold', signal=1, confidence=0.9, price=2000.0
        )
        assert result is False

    def test_default_threshold(self):
        service = EmailAlertService(
            sender_email='test@test.com',
            sender_password='pass',
            recipient_email='rec@test.com'
        )
        assert service.confidence_threshold == 0.70
