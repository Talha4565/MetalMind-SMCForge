"""
Signal Memory - ChromaDB-based vector storage for trading signals.

Stores signal features, metadata, and outcomes for similarity search
and self-learning. Uses ChromaDB with sentence-transformers embeddings.
"""

from .client import SignalMemoryClient
from .embedder import SignalEmbedder
from .retriever import SignalRetriever
from .updater import SignalUpdater

__all__ = ['SignalMemoryClient', 'SignalEmbedder', 'SignalRetriever', 'SignalUpdater']
