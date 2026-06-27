"""
Signal Embedder - converts signal features to embeddings for vector storage.
Uses sentence-transformers for local embeddings (no API needed).
"""

import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Default embedding model (runs locally, no API key needed)
DEFAULT_MODEL = "all-MiniLM-L6-v2"


class SignalEmbedder:
    """Embeds signal features into vector representations."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or DEFAULT_MODEL
        self._model = None
    
    def get_model(self):
        """Lazy-load the embedding model."""
        if self._model is not None:
            return self._model
        
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
            return self._model
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
    
    def embed_signal(self, signal_data: Dict[str, Any]) -> List[float]:
        """
        Convert signal features to embedding vector.
        
        Args:
            signal_data: Dict with signal features (close, rsi, macd, etc.)
        
        Returns:
            Embedding vector as list of floats
        """
        # Create a text representation of the signal for embedding
        text = self._signal_to_text(signal_data)
        
        model = self.get_model()
        embedding = model.encode(text)
        return embedding.tolist()
    
    def embed_batch(self, signals: List[Dict[str, Any]]) -> List[List[float]]:
        """Embed multiple signals at once."""
        texts = [self._signal_to_text(s) for s in signals]
        model = self.get_model()
        embeddings = model.encode(texts)
        return embeddings.tolist()
    
    def _signal_to_text(self, signal: Dict[str, Any]) -> str:
        """
        Convert signal features to a descriptive text string.
        This captures the semantic meaning of the signal for embedding.
        """
        parts = []
        
        # Asset
        if 'asset' in signal:
            parts.append(f"Asset: {signal['asset']}")
        
        # Direction
        signal_val = signal.get('signal', 0)
        direction = {1: 'BUY', -1: 'SELL', 0: 'HOLD'}.get(signal_val, 'UNKNOWN')
        parts.append(f"Signal: {direction}")
        
        # Key technical indicators
        if 'rsi' in signal:
            rsi = signal['rsi']
            if rsi > 70:
                parts.append("RSI overbought")
            elif rsi < 30:
                parts.append("RSI oversold")
            else:
                parts.append(f"RSI neutral at {rsi:.1f}")
        
        if 'macd' in signal:
            macd = signal['macd']
            if macd > 0:
                parts.append("MACD bullish")
            else:
                parts.append("MACD bearish")
        
        if 'ema_cross' in signal:
            if signal['ema_cross'] > 0:
                parts.append("EMA crossover bullish")
            else:
                parts.append("EMA crossover bearish")
        
        if 'volume_ratio' in signal:
            vol = signal['volume_ratio']
            if vol > 1.5:
                parts.append("High volume")
            elif vol < 0.5:
                parts.append("Low volume")
        
        if 'atr' in signal:
            atr = signal['atr']
            parts.append(f"Volatility ATR {atr:.2f}")
        
        if 'price_change_pct' in signal:
            chg = signal['price_change_pct']
            if chg > 0.5:
                parts.append("Strong upward momentum")
            elif chg < -0.5:
                parts.append("Strong downward momentum")
        
        return " | ".join(parts) if parts else "Unknown signal pattern"
