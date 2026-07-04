"""
Signal Embedder - converts signal features to embeddings for vector storage.
Uses NVIDIA NIM API for embeddings (free tier: 1000 req/day).
Falls back to local sentence-transformers if API unavailable.
"""

import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1/embeddings"
NVIDIA_NIM_MODEL = "nvidia/nv-embedqa-e5-v5"


class ChromaDBEmbeddingFunction:
    """Wrapper that makes SignalEmbedder compatible with ChromaDB."""
    
    def __init__(self, embedder: 'SignalEmbedder'):
        self.embedder = embedder
        self.name = "signal_embedding"
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        return [self.embedder._embed_via_api(text) for text in input]


class SignalEmbedder:
    """Embeds signal features into vector representations."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('NVIDIA_API_KEY', '')
        self._model = None
        self._use_api = bool(self.api_key)
    
    def get_model(self):
        """Get embedding function (API or local fallback)."""
        if self._use_api:
            return self  # API mode — self has embed_signal method
        # Fallback to local sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            if self._model is None:
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded local embedding model")
            return self._model
        except ImportError:
            logger.warning("sentence-transformers not installed, using API fallback")
            self._use_api = True
            return self
    
    def embed_signal(self, signal_data: Dict[str, Any]) -> List[float]:
        """Convert signal features to embedding vector."""
        text = self._signal_to_text(signal_data)
        
        if self._use_api:
            return self._embed_via_api(text)
        
        model = self.get_model()
        embedding = model.encode(text)
        return embedding.tolist()
    
    def _embed_via_api(self, text: str) -> List[float]:
        """Embed text via NVIDIA NIM API."""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": NVIDIA_NIM_MODEL,
            "input": [text],
            "input_type": "query",
        }
        
        try:
            resp = requests.post(NVIDIA_NIM_URL, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"NVIDIA NIM API error: {e}")
            raise
    
    def embed_batch(self, signals: List[Dict[str, Any]]) -> List[List[float]]:
        """Embed multiple signals at once."""
        texts = [self._signal_to_text(s) for s in signals]
        
        if self._use_api:
            import requests
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {"model": NVIDIA_NIM_MODEL, "input": texts, "input_type": "query"}
            resp = requests.post(NVIDIA_NIM_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            return [d["embedding"] for d in resp.json()["data"]]
        
        model = self.get_model()
        embeddings = model.encode(texts)
        return embeddings.tolist()
    
    def _signal_to_text(self, signal: Dict[str, Any]) -> str:
        """Convert signal features to descriptive text for embedding."""
        parts = []
        
        if 'asset' in signal:
            parts.append(f"Asset: {signal['asset']}")
        
        signal_val = signal.get('signal', 0)
        direction = {1: 'BUY', -1: 'SELL', 0: 'HOLD'}.get(signal_val, 'UNKNOWN')
        parts.append(f"Signal: {direction}")
        
        if 'rsi' in signal:
            rsi = signal['rsi']
            if rsi > 70:
                parts.append("RSI overbought")
            elif rsi < 30:
                parts.append("RSI oversold")
            else:
                parts.append(f"RSI neutral at {rsi:.1f}")
        
        if 'macd' in signal:
            parts.append("MACD bullish" if signal['macd'] > 0 else "MACD bearish")
        
        if 'ema_cross' in signal:
            parts.append("EMA crossover bullish" if signal['ema_cross'] > 0 else "EMA crossover bearish")
        
        if 'volume_ratio' in signal:
            vol = signal['volume_ratio']
            if vol > 1.5:
                parts.append("High volume")
            elif vol < 0.5:
                parts.append("Low volume")
        
        if 'atr' in signal:
            parts.append(f"Volatility ATR {signal['atr']:.2f}")
        
        if 'price_change_pct' in signal:
            chg = signal['price_change_pct']
            if chg > 0.5:
                parts.append("Strong upward momentum")
            elif chg < -0.5:
                parts.append("Strong downward momentum")
        
        return " | ".join(parts) if parts else "Unknown signal pattern"
