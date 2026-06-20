"""Unit tests for AlertRiskGate."""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl.guards.alert_risk_gate import AlertRiskGate, RiskDecision


class TestAlertRiskGate:
    def _gate(self, **overrides):
        cfg = {
            "enabled": True,
            "min_alert_interval_min": 30,
            "suppress_weekends": True,
            "enforce_session": False,
            "enforce_volatility": False,
        }
        # historical_atr is a constructor param, not a config key
        historical_atr = overrides.pop("historical_atr", None)
        cfg.update(overrides)
        return AlertRiskGate(cfg, historical_atr=historical_atr)

    def test_first_alert_approved(self):
        g = self._gate()
        now = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)  # Monday
        d = g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=now)
        assert d.approved is True
        assert d.reason == "passed"

    def test_cooldown_blocks_second_alert_same_asset(self):
        g = self._gate()
        now = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
        first = g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=now)
        second = g.check(asset="gold", price=2001.0, atr=2.0, signal=1, confidence=0.8,
                         now=now + timedelta(minutes=10))
        assert first.approved is True
        assert second.approved is False
        assert "cooldown" in second.reason.lower()

    def test_cooldown_does_not_block_other_asset(self):
        g = self._gate()
        now = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
        g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=now)
        other = g.check(asset="silver", price=25.0, atr=0.2, signal=-1, confidence=0.8, now=now)
        assert other.approved is True

    def test_cooldown_expires(self):
        g = self._gate()
        now = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
        g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=now)
        later = g.check(asset="gold", price=2001.0, atr=2.0, signal=1, confidence=0.8,
                        now=now + timedelta(minutes=31))
        assert later.approved is True

    def test_weekend_suppressed(self):
        g = self._gate()
        # 2026-06-06 is a Saturday
        sat = datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc)
        d = g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=sat)
        assert d.approved is False
        assert "weekend" in d.reason.lower()

    def test_session_enforced_blocks_outside(self):
        g = self._gate(enforce_session=True)
        # 03:00 UTC is before London open (07:00)
        night = datetime(2026, 6, 1, 3, 0, tzinfo=timezone.utc)  # Monday
        d = g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=night)
        assert d.approved is False
        assert "session" in d.reason.lower()

    def test_session_off_by_default_allows_night(self):
        g = self._gate()  # enforce_session defaults False
        night = datetime(2026, 6, 1, 3, 0, tzinfo=timezone.utc)
        d = g.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8, now=night)
        assert d.approved is True

    def test_volatility_opt_in_blocks_high_atr(self):
        # atr 5.0 > 2.0 * 2.0 historical avg
        g = self._gate(enforce_volatility=True, historical_atr=2.0)
        d = g.check(asset="gold", price=2000.0, atr=5.0, signal=1, confidence=0.8,
                    now=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc))
        assert d.approved is False
        assert "volatility" in d.reason.lower()

    def test_disabled_gate_approves_everything(self):
        g = self._gate(enabled=False)
        d = g.check(asset="gold", price=2000.0, atr=999.0, signal=1, confidence=0.8,
                    now=datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc))
        assert d.approved is True
