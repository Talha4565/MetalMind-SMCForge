"""
Signal Updater - stores signal outcomes for self-learning.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from .client import SignalMemoryClient
from .embedder import SignalEmbedder, ChromaDBEmbeddingFunction

logger = logging.getLogger(__name__)


class SignalUpdater:
    """Stores signals and updates outcomes for self-learning."""
    
    def __init__(self, client: SignalMemoryClient = None, embedder: SignalEmbedder = None):
        self.client = client or SignalMemoryClient()
        self.embedder = embedder or SignalEmbedder()
        self.collection_name = "signal_patterns"
    
    def get_collection(self):
        """Get the signal patterns collection."""
        return self.client.get_collection(self.collection_name)
    
    def store_signal(self, signal_data: Dict[str, Any], prediction_id: str = None) -> str:
        """
        Store a signal with its features and metadata.
        
        Args:
            signal_data: Dict with signal features
            prediction_id: Optional unique ID for the prediction
        
        Returns:
            ID of the stored signal
        """
        collection = self.get_collection()
        
        # Generate ID if not provided
        if prediction_id is None:
            prediction_id = f"sig_{int(datetime.now().timestamp())}_{hash(str(signal_data)) % 10000}"
        
        # Create document text for embedding
        from .retriever import SignalRetriever
        retriever = SignalRetriever(self.client, self.embedder)
        document = retriever.embedder._signal_to_text(signal_data)
        
        # Prepare metadata
        metadata = {
            'asset': signal_data.get('asset', 'unknown'),
            'signal': signal_data.get('signal', 0),
            'confidence': signal_data.get('confidence', 0),
            'price': signal_data.get('price', 0),
            'timestamp': datetime.now().isoformat(),
            'actual_outcome': None,
            'actual_pnl': None,
        }
        
        # Add key features to metadata for filtering
        for key in ['rsi', 'macd', 'atr', 'ema_cross', 'volume_ratio']:
            if key in signal_data:
                metadata[key] = float(signal_data[key])
        
        # Store in ChromaDB with embedding
        try:
            embedding = self.embedder.embed_signal(signal_data)
            collection.upsert(
                ids=[prediction_id],
                documents=[document],
                embeddings=[embedding],
                metadatas=[metadata]
            )
        except Exception as e:
            # Fallback: store without embedding (won't support similarity search)
            logger.warning(f"Could not compute embedding, storing without: {e}")
            collection.upsert(
                ids=[prediction_id],
                documents=[document],
                metadatas=[metadata]
            )
        
        logger.info(f"Stored signal: {prediction_id} ({metadata['signal']})")
        return prediction_id
    
    def update_outcome(self, signal_id: str, outcome: str, pnl: float = None):
        """
        Update a signal with its actual outcome.
        
        Args:
            signal_id: ID of the signal to update
            outcome: 'WIN' or 'LOSS'
            pnl: Actual PnL percentage
        """
        collection = self.get_collection()
        
        try:
            # Get existing record
            result = collection.get(ids=[signal_id], include=["metadatas"])
            
            if not result or not result.get('ids') or not result['ids']:
                logger.warning(f"Signal {signal_id} not found")
                return
            
            # Update metadata
            metadata = result['metadatas'][0]
            metadata['actual_outcome'] = outcome
            metadata['actual_pnl'] = pnl
            metadata['outcome_checked_at'] = datetime.now().isoformat()
            
            # Update in ChromaDB
            collection.update(
                ids=[signal_id],
                metadatas=[metadata]
            )
            
            logger.info(f"Updated signal {signal_id}: {outcome} (PnL: {pnl}%)")
        
        except Exception as e:
            logger.error(f"Failed to update signal {signal_id}: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about stored signals."""
        collection = self.get_collection()
        count = collection.count()
        
        if count == 0:
            return {'total': 0, 'wins': 0, 'losses': 0, 'pending': 0}
        
        # Sample to get stats
        sample_size = min(1000, count)
        results = collection.get(limit=sample_size, include=["metadatas"])
        
        wins = 0
        losses = 0
        pending = 0
        
        for meta in results['metadatas']:
            outcome = meta.get('actual_outcome')
            if outcome == 'WIN':
                wins += 1
            elif outcome == 'LOSS':
                losses += 1
            else:
                pending += 1
        
        return {
            'total': count,
            'wins': wins,
            'losses': losses,
            'pending': pending,
            'win_rate': round(wins / (wins + losses), 3) if (wins + losses) > 0 else 0,
        }
