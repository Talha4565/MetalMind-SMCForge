"""
Thin OpenAI-compatible client for NVIDIA NIM.

Intentionally minimal (AD3): one method, chat(), that returns the raw content
string or None on ANY failure (timeout, HTTP error, malformed JSON, missing key).
Callers must treat None as "agent unavailable" and fail open (AD5).
"""
import os
import logging
from typing import Optional, List, Dict

from openai import OpenAI, APIError, APIConnectionError, APITimeoutError

from config.settings import SIGNAL_REASONER_CONFIG

logger = logging.getLogger(__name__)


class NemotronClient:
    """OpenAI-compatible client for NVIDIA NIM. Never raises on transport errors."""

    def __init__(self, api_key: str = None, config: dict = None):
        cfg = {**(SIGNAL_REASONER_CONFIG or {}), **(config or {})}
        self.model = cfg.get("model", "nvidia/nemotron-3-ultra-550b-a55b")
        self.temperature = float(cfg.get("temperature", 0.1))
        self.top_p = float(cfg.get("top_p", 0.95))
        self.max_tokens = int(cfg.get("max_tokens", 200))
        try:
            self.timeout = float(os.getenv(
                cfg.get("timeout_env_var", "ML_AGENT_TIMEOUT_SEC"),
                cfg.get("default_timeout_sec", 8)
            ))
        except (TypeError, ValueError):
            self.timeout = 8.0
        self.api_key = api_key or os.getenv(cfg.get("api_key_env_var", "NVIDIA_API_KEY"))

        self._client = None
        if self.api_key:
            try:
                self._client = OpenAI(
                    base_url="https://integrate.api.nvidia.com/v1",
                    api_key=self.api_key,
                    timeout=self.timeout,
                )
            except Exception as e:
                logger.warning(f"[NemotronClient] failed to init OpenAI client: {e}")
                self._client = None

    def is_available(self) -> bool:
        return self._client is not None

    def chat(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Return assistant content string, or None on any failure."""
        if not self.is_available():
            return None

        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
            )
            return completion.choices[0].message.content
        except APITimeoutError as e:
            logger.warning(f"[NemotronClient] timeout: {e}")
            return None
        except APIConnectionError as e:
            logger.warning(f"[NemotronClient] connection error: {e}")
            return None
        except APIError as e:
            logger.warning(f"[NemotronClient] API error: {e}")
            return None
        except (IndexError, AttributeError) as e:
            logger.warning(f"[NemotronClient] malformed response: {e}")
            return None
        except Exception as e:
            logger.warning(f"[NemotronClient] unexpected error: {e}")
            return None
