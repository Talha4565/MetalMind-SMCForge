"""Unit tests for SignalReasoner. LLM is always mocked."""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl.agents.signal_reasoner import SignalReasoner, AgentDecision


def fake_pred_summary(**kw):
    base = {"total_predictions": 0, "evaluated": 0, "wins": 0, "losses": 0}
    base.update(kw)
    return base


class TestSignalReasoner:
    def _make_reasoner(self, client_content=None):
        client = MagicMock()
        client.is_available.return_value = True
        client.chat.return_value = client_content
        return SignalReasoner(client=client, pred_logger=MagicMock(get_summary=lambda days=1: fake_pred_summary()))

    def test_parses_approve_json(self):
        with patch.dict(os.environ, {"ML_AGENT_ENABLED": "true"}, clear=False):
            r = self._make_reasoner(client_content='{"approved": true, "reason": "trend aligned"}')
            d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                           ema20=2000, ema50=1990, price=2005)
        assert d.approved is True
        assert d.reason == "trend aligned"
        assert d.source == "llm"

    def test_parses_reject_json(self):
        with patch.dict(os.environ, {"ML_AGENT_ENABLED": "true"}, clear=False):
            r = self._make_reasoner(client_content='{"approved": false, "reason": "overbought"}')
            d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=78, atr=2.0,
                           ema20=2000, ema50=1990, price=2005)
        assert d.approved is False
        assert d.source == "llm"

    def test_fail_open_on_malformed_response(self):
        # AD5: garbage from the LLM -> approve (fail open)
        with patch.dict(os.environ, {"ML_AGENT_ENABLED": "true"}, clear=False):
            r = self._make_reasoner(client_content="APPROVE - looks good")  # not JSON
            d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                           ema20=2000, ema50=1990, price=2005)
        assert d.approved is True
        assert d.source == "fail_open"
        assert "unparseable" in d.reason.lower() or "fail" in d.reason.lower()

    def test_fail_open_on_none_response(self):
        with patch.dict(os.environ, {"ML_AGENT_ENABLED": "true"}, clear=False):
            r = self._make_reasoner(client_content=None)
            d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                           ema20=2000, ema50=1990, price=2005)
        assert d.approved is True
        assert d.source == "fail_open"

    def test_disabled_returns_pass_through(self):
        with patch.dict(os.environ, {"ML_AGENT_ENABLED": "false"}, clear=False):
            r = SignalReasoner(client=MagicMock(), pred_logger=MagicMock())
            d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                           ema20=2000, ema50=1990, price=2005)
            assert d.approved is True
            assert d.source == "disabled"

    def test_no_client_fail_open(self):
        with patch.dict(os.environ, {"ML_AGENT_ENABLED": "true"}, clear=False):
            r = SignalReasoner(client=None, pred_logger=MagicMock())
            d = r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                           ema20=2000, ema50=1990, price=2005)
            assert d.approved is True

    def test_uses_recent_accuracy_as_memory(self):
        """The agent's 'memory' comes from PredictionLogger.get_summary — not new state."""
        logger = MagicMock(get_summary=lambda days=1: fake_pred_summary(
            total_predictions=20, evaluated=10, wins=3, losses=7))  # 30% recent accuracy
        client = MagicMock()
        client.is_available.return_value = True
        client.chat.return_value = '{"approved": true, "reason": "ok"}'
        with patch.dict(os.environ, {"ML_AGENT_ENABLED": "true"}, clear=False):
            r = SignalReasoner(client=client, pred_logger=logger)
            r.evaluate(asset="gold", signal=1, confidence=0.8, rsi=55, atr=2.0,
                       ema20=2000, ema50=1990, price=2005)
        # The prompt sent to the LLM must reference recent accuracy
        sent_messages = client.chat.call_args[0][0]
        prompt_text = " ".join(m["content"] for m in sent_messages)
        assert "30%" in prompt_text or "accuracy" in prompt_text.lower()
