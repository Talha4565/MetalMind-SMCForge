"""
Signal Reasoner — a genuine (if minimal) LLM agent (AD3).

Perceives: market context (RSI, ATR, EMAs, price, signal direction, confidence)
           + recent model accuracy pulled from PredictionLogger (this is the agent's memory).
Reasons:  one OpenAI-compatible chat call, structured JSON output.
Acts:     returns AgentDecision(approved, reason, source). Never raises.

Backtest safety (AD4): this module is imported ONLY by api/app/main.py.
Never import it from backtesting/. Fail-open (AD5) on any error.
"""
import os
import json
import logging
from dataclasses import dataclass
from typing import Optional

from config.settings import SIGNAL_REASONER_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class AgentDecision:
    approved: bool
    reason: str
    source: str  # "llm" | "fail_open" | "disabled"


class SignalReasoner:
    """One-shot LLM signal validator. Backtest-safe by construction."""

    def __init__(self, client=None, pred_logger=None, config: dict = None):
        cfg = {**(SIGNAL_REASONER_CONFIG or {}), **(config or {})}
        self.cfg = cfg
        self.enabled_env_var = cfg.get("enabled_env_var", "ML_AGENT_ENABLED")
        self.client = client
        self.pred_logger = pred_logger

    def _is_enabled(self) -> bool:
        return os.getenv(self.enabled_env_var, "false").strip().lower() == "true"

    def evaluate(
        self,
        asset: str,
        signal: int,
        confidence: float,
        rsi: float,
        atr: float,
        ema20: float,
        ema50: float,
        price: float,
    ) -> AgentDecision:
        # 1. Hard bypass switch (AD4) — default OFF so backtests/historical replays
        #    are never nondeterministic.
        if not self._is_enabled():
            return AgentDecision(approved=True, reason="agent_disabled_by_env",
                                 source="disabled")

        # 2. Fail-open if there's no usable client
        if self.client is None or not getattr(self.client, "is_available", lambda: False)():
            return AgentDecision(approved=True, reason="agent_unavailable",
                                 source="fail_open")

        # 3. Perceive — memory comes from PredictionLogger, no new state
        recent_accuracy = self._recent_accuracy_pct()

        # 4. Reason — structured JSON output so we never string-parse APPROVE/REJECT
        prompt = self._build_prompt(
            asset=asset, signal=signal, confidence=confidence, rsi=rsi,
            atr=atr, ema20=ema20, ema50=ema50, price=price,
            recent_accuracy=recent_accuracy,
        )
        raw = self.client.chat([{"role": "user", "content": prompt}])

        # 5. Fail-open on any transport/parsing failure (AD5)
        if raw is None:
            return AgentDecision(approved=True, reason="agent_no_response",
                                 source="fail_open")

        try:
            data = json.loads(raw)
            approved = bool(data.get("approved"))
            reason = str(data.get("reason", ""))[:200]
            return AgentDecision(approved=approved, reason=reason or "llm_decision",
                                 source="llm")
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"[SignalReasoner] unparseable LLM response: {e}; raw={raw[:120]}")
            return AgentDecision(approved=True, reason=f"fail_open_unparseable_{e}",
                                 source="fail_open")

    def _recent_accuracy_pct(self) -> Optional[float]:
        if self.pred_logger is None:
            return None
        try:
            s = self.pred_logger.get_summary(days=1)
            evaluated = s.get("evaluated", 0)
            if evaluated == 0:
                return None
            return round(100.0 * s.get("wins", 0) / evaluated, 1)
        except Exception as e:
            logger.warning(f"[SignalReasoner] could not read recent accuracy: {e}")
            return None

    def _build_prompt(self, asset, signal, confidence, rsi, atr,
                      ema20, ema50, price, recent_accuracy) -> str:
        direction = "BUY" if signal == 1 else "SELL"
        trend = "uptrend (EMA20 > EMA50)" if ema20 > ema50 else "downtrend (EMA20 < EMA50)"
        acc_str = f"{recent_accuracy}%" if recent_accuracy is not None else "no data yet"
        return f"""You are a trading-signal validator for {asset.upper()}.

Model output: {direction} signal at confidence {confidence:.0%}.
Price: {price:.2f} | EMA20: {ema20:.2f} | EMA50: {ema50:.2f} -> {trend}
RSI(14): {rsi:.1f} | ATR(14): {atr:.2f}
Recent model accuracy (last day): {acc_str}

Decide whether to send this signal as an alert. Consider overbought/oversold,
trend alignment, and whether the model has been reliable recently.

Respond with ONLY a JSON object, no prose:
{{"approved": true|false, "reason": "one short sentence"}}"""
