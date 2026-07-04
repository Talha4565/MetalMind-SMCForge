"""
Signal Retriever - searches for similar past signals and adjusts confidence.
"""

import logging
from typing import Dict, Any, List, Optional
from .client import SignalMemoryClient
from .embedder import SignalEmbedder, ChromaDBEmbeddingFunction

logger = logging.getLogger(__name__)


class SignalRetriever:
    """Searches ChromaDB for similar past signals and adjusts confidence."""
    
    def __init__(self, client: SignalMemoryClient = None, embedder: SignalEmbedder = None):
        self.client = client or SignalMemoryClient()
        self.embedder = embedder or SignalEmbedder()
        self.collection_name = "signal_patterns"
    
    def get_collection(self):
        """Get the signal patterns collection."""
        return self.client.get_collection(self.collection_name)
    
    def find_similar(self, signal_data: Dict[str, Any], n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar past signals.
        
        Args:
            signal_data: Current signal features
            n_results: Number of similar signals to return
        
        Returns:
            List of similar signals with metadata and distances
        """
        collection = self.get_collection()
        
        if collection.count() == 0:
            logger.info("No signals stored yet")
            return []
        
        # Embed the current signal
        query_embedding = self.embedder.embed_signal(signal_data)
        
        # Search for similar signals
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
            include=["metadatas", "distances", "documents"]
        )
        
        if not results or not results.get('ids') or not results['ids'][0]:
            return []
        
        # Format results
        similar_signals = []
        for i in range(len(results['ids'][0])):
            similar_signals.append({
                'id': results['ids'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results['distances'] else 0,
                'document': results['documents'][0][i] if results['documents'] else '',
            })
        
        return similar_signals
    
    def adjust_confidence(self, signal_data: Dict[str, Any], base_confidence: float) -> float:
        """
        Adjust confidence based on similar past signals.
        
        If similar signals historically won → boost confidence
        If similar signals historically lost → reduce confidence
        
        Args:
            signal_data: Current signal features
            base_confidence: Model's predicted confidence (0-1)
        
        Returns:
            Adjusted confidence (0-1)
        """
        similar = self.find_similar(signal_data, n_results=10)
        
        if not similar:
            return base_confidence
        
        # Calculate win rate of similar signals
        wins = 0
        losses = 0
        total_weight = 0
        
        for sig in similar:
            meta = sig.get('metadata', {})
            distance = sig.get('distance', 1.0)
            
            # Weight by similarity (closer = more weight)
            weight = max(0.1, 1.0 - distance)
            
            outcome = meta.get('actual_outcome', None)
            if outcome == 'WIN':
                wins += weight
                total_weight += weight
            elif outcome == 'LOSS':
                losses += weight
                total_weight += weight
        
        if total_weight == 0:
            return base_confidence
        
        win_rate = wins / total_weight
        
        # Adjust confidence based on historical win rate
        # If similar signals won 70% of the time, boost confidence by 10%
        adjustment = (win_rate - 0.5) * 0.2  # +/- 10% max adjustment
        
        adjusted = base_confidence + adjustment
        adjusted = max(0.0, min(1.0, adjusted))  # Clamp to [0, 1]
        
        logger.info(f"Confidence adjusted: {base_confidence:.3f} → {adjusted:.3f} "
                    f"(win_rate={win_rate:.2%}, n_similar={len(similar)})")
        
        return adjusted
    
    def get_signal_stats(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get statistics about similar past signals.
        
        Returns:
            Dict with win_rate, avg_confidence, count, etc.
        """
        similar = self.find_similar(signal_data, n_results=50)
        
        if not similar:
            return {'count': 0, 'win_rate': 0, 'avg_confidence': 0}
        
        wins = 0
        losses = 0
        confidences = []
        
        for sig in similar:
            meta = sig.get('metadata', {})
            outcome = meta.get('actual_outcome', None)
            confidence = meta.get('confidence', 0)
            
            if outcome == 'WIN':
                wins += 1
            elif outcome == 'LOSS':
                losses += 1
            
            confidences.append(confidence)
        
        evaluated = wins + losses
        win_rate = wins / evaluated if evaluated > 0 else 0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'count': len(similar),
            'wins': wins,
            'losses': losses,
            'evaluated': evaluated,
            'win_rate': round(win_rate, 3),
            'avg_confidence': round(avg_confidence, 4),
        }
