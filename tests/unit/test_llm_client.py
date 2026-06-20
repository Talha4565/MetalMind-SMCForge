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

    def test_chat_returns_content_on_success(self):
        mock_msg = MagicMock()
        mock_msg.content = '{"approved": true}'
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        with patch.dict(os.environ, {"NVIDIA_API_KEY": "fake-key"}, clear=False):
            c = NemotronClient()
            c._client = MagicMock()
            c._client.chat.completions.create.return_value = mock_completion

            out = c.chat([{"role": "user", "content": "decide"}])
            assert out == '{"approved": true}'
            _, kwargs = c._client.chat.completions.create.call_args
            assert kwargs["model"] == "nvidia/nemotron-3-ultra-550b-a55b"

    def test_chat_returns_none_on_api_error(self):
        from openai import APIStatusError
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "fake-key"}, clear=False):
            c = NemotronClient()
            c._client = MagicMock()
            c._client.chat.completions.create.side_effect = APIStatusError(
                message="error", response=MagicMock(status_code=500), body=None
            )
            assert c.chat([{"role": "user", "content": "decide"}]) is None

    def test_chat_returns_none_on_timeout(self):
        from openai import APITimeoutError
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "fake-key"}, clear=False):
            c = NemotronClient()
            c._client = MagicMock()
            c._client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())
            assert c.chat([{"role": "user", "content": "decide"}]) is None

    def test_chat_returns_none_on_connection_error(self):
        from openai import APIConnectionError
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "fake-key"}, clear=False):
            c = NemotronClient()
            c._client = MagicMock()
            c._client.chat.completions.create.side_effect = APIConnectionError(request=MagicMock())
            assert c.chat([{"role": "user", "content": "decide"}]) is None

    def test_does_not_use_fictional_super_model(self):
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "fake-key"}, clear=False):
            c = NemotronClient()
            assert "nemotron-3-super" not in c.model, "use a real model ID from build.nvidia.com"
