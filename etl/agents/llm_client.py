"""
Thin OpenAI-compatible HTTP wrapper for NVIDIA NIM.

Intentionally minimal (AD3): one method, chat(), that returns the raw content
string or None on ANY failure (timeout, HTTP error, malformed JSON, missing key).
Callers must treat None as "agent unavailable" and fail open (AD5).
"""
import os
import logging
from typing import Optional, List, Dict

import requests

from config.settings import SIGNAL_REASONER_CONFIG

logger = logging.getLogger(__name__)


class NemotronClient:
    """OpenAI-compatible client for NVIDIA NIM. Never raises on transport errors."""

    def __init__(self, api_key: str = None, config: dict = None):
        cfg = {**(SIGNAL_REASONER_CONFIG or {}), **(config or {})}
        self.api_url = cfg["api_url"]
        self.model = cfg.get("model", "nvidia/nemotron-3-ultra-550b-a55b")
        self.temperature = float(cfg.get("temperature", 0.1))
        self.max_tokens = int(cfg.get("max_tokens", 200))
        try:
            self.timeout = int(os.getenv(cfg.get("timeout_env_var", "ML_AGENT_TIMEOUT_SEC"),
                                         cfg.get("default_timeout_sec", 8)))
        except (TypeError, ValueError):
            self.timeout = 8
        self.api_key = api_key or os.getenv(cfg.get("api_key_env_var", "NVIDIA_API_KEY"))

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Return assistant content string, or None on any failure."""
        if not self.is_available():
            return None
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            logger.warning(f"[NemotronClient] transport error: {e}")
            return None
        if resp.status_code != 200:
            logger.warning(f"[NemotronClient] HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        try:
            return resp.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as e:
            logger.warning(f"[NemotronClient] malformed response: {e}")
            return None
