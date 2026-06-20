"""Unit tests for NemotronClient. Network is ALWAYS mocked."""
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl.agents.llm_client import NemotronClient


class TestNemotronClient:
    def test_returns_none_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            c = NemotronClient()
            assert c.is_available() is False
            assert c.chat([{"role": "user", "content": "hi"}]) is None

    @patch("etl.agents.llm_client.requests.post")
    def test_chat_returns_content_on_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": '{"approved": true}'}}]},
        )
        c = NemotronClient(api_key="fake-key")
        out = c.chat([{"role": "user", "content": "decide"}])
        assert out == '{"approved": true}'
        # Confirm the real model ID is used (not the fictional "nemotron-3-super")
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "nvidia/nemotron-3-ultra-550b-a55b"

    @patch("etl.agents.llm_client.requests.post")
    def test_chat_returns_none_on_http_error(self, mock_post):
        mock_post.return_value = MagicMock(status_code=500, json=lambda: {})
        c = NemotronClient(api_key="fake-key")
        assert c.chat([{"role": "user", "content": "decide"}]) is None

    @patch("etl.agents.llm_client.requests.post")
    def test_chat_returns_none_on_timeout(self, mock_post):
        import requests as req
        mock_post.side_effect = req.Timeout("timed out")
        c = NemotronClient(api_key="fake-key")
        assert c.chat([{"role": "user", "content": "decide"}]) is None

    @patch("etl.agents.llm_client.requests.post")
    def test_chat_returns_none_on_malformed_json(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: {"not_choices": []}
        )
        c = NemotronClient(api_key="fake-key")
        assert c.chat([{"role": "user", "content": "decide"}]) is None

    def test_does_not_use_fictional_super_model(self):
        c = NemotronClient(api_key="fake-key")
        assert "nemotron-3-super" not in c.model, "use a real model ID from build.nvidia.com"
