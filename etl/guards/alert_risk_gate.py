"""
Alert risk gate — deterministic checks run at the LIVE alert call site
(api/app/main.py:688), in front of EmailAlertService.send_alert().

Scope (AD2): transport logic stays in etl/alerts.py; market logic lives here.
The biggest single win is the per-asset cooldown (stops alert spam in choppy sessions).
Volatility and session checks are opt-in (AD7) — off by default.
"""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import logging

from config.settings import ALERT_RISK_GATE_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class RiskDecision:
    """Outcome of an alert risk check."""
    approved: bool
    reason: str


def _parse_hhmm(s: str) -> int:
    """'07:00' -> minutes-since-midnight (420)."""
    h, m = s.split(":")
    return int(h) * 60 + int(m)


class AlertRiskGate:
    """Deterministic alert suppression rules with per-asset cooldown state."""

    def __init__(self, config: dict = None, historical_atr: float = None):
        cfg = {**(ALERT_RISK_GATE_CONFIG or {}), **(config or {})}
        self.enabled = bool(cfg.get("enabled", True))
        self.min_alert_interval_min = int(cfg.get("min_alert_interval_min", 30))
        self.suppress_weekends = bool(cfg.get("suppress_weekends", True))
        self.enforce_session = bool(cfg.get("enforce_session", False))
        self.enforce_volatility = bool(cfg.get("enforce_volatility", False))
        self.session_start_min = _parse_hhmm(cfg.get("session_start_utc", "07:00"))
        self.session_end_min = _parse_hhmm(cfg.get("session_end_utc", "21:00"))
        self.max_atr_multiplier = float(cfg.get("max_atr_multiplier", 2.0))
        self.historical_atr = historical_atr  # optional baseline for volatility check
        self._last_alert: Dict[str, datetime] = {}  # asset -> last approved time

    def check(
        self,
        asset: str,
        price: float,
        atr: float,
        signal: int,
        confidence: float,
        now: Optional[datetime] = None,
    ) -> RiskDecision:
        if not self.enabled:
            return RiskDecision(approved=True, reason="gate_disabled")

        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # 1. Weekend
        if self.suppress_weekends and now.weekday() >= 5:
            return RiskDecision(approved=False, reason="weekend_market_closed")

        # 2. Session window (opt-in)
        if self.enforce_session:
            minutes = now.hour * 60 + now.minute
            if not (self.session_start_min <= minutes <= self.session_end_min):
                return RiskDecision(approved=False, reason="outside_session_window")

        # 3. Volatility (opt-in)
        if self.enforce_volatility and self.historical_atr and atr > self.max_atr_multiplier * self.historical_atr:
            return RiskDecision(
                approved=False,
                reason=f"volatility_too_high_atr_{atr:.2f}_vs_{self.historical_atr:.2f}",
            )

        # 4. Cooldown (per asset) — the high-ROI check
        last = self._last_alert.get(asset)
        if last is not None and (now - last) < timedelta(minutes=self.min_alert_interval_min):
            return RiskDecision(
                approved=False,
                reason=f"cooldown_{int((now - last).total_seconds() // 60)}min_of_{self.min_alert_interval_min}min",
            )

        # Approved — record for future cooldown
        self._last_alert[asset] = now
        logger.info(f"[AlertRiskGate] approved {asset} signal={signal} conf={confidence:.2f}")
        return RiskDecision(approved=True, reason="passed")
