"""
Test script for signal memory and self-learning integration.
Run this to verify ChromaDB is working correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_signal_memory():
    """Test the signal memory system."""
    print("=" * 60)
    print("Testing Signal Memory System")
    print("=" * 60)
    
    try:
        # Test 1: Initialize ChromaDB client
        print("\n1. Initializing ChromaDB client...")
        from signal_memory import SignalMemoryClient
        client = SignalMemoryClient(persistent=True)
        print("   ✓ ChromaDB client initialized")
        
        # Test 2: Initialize embedder
        print("\n2. Initializing embedder...")
        from signal_memory import SignalEmbedder
        embedder = SignalEmbedder()
        print("   ✓ Embedder initialized")
        
        # Test 3: Store a test signal
        print("\n3. Storing test signal...")
        from signal_memory import SignalUpdater
        updater = SignalUpdater(client, embedder)
        
        test_signal = {
            'asset': 'gold',
            'signal': 1,  # BUY
            'confidence': 0.75,
            'price': 2350.0,
            'rsi': 65.0,
            'macd': 0.5,
            'atr': 15.0,
            'ema_cross': 1,
            'volume_ratio': 1.2,
        }
        
        signal_id = updater.store_signal(test_signal)
        print(f"   ✓ Signal stored with ID: {signal_id}")
        
        # Test 4: Search for similar signals
        print("\n4. Searching for similar signals...")
        from signal_memory import SignalRetriever
        retriever = SignalRetriever(client, embedder)
        
        similar = retriever.find_similar(test_signal, n_results=3)
        print(f"   ✓ Found {len(similar)} similar signals")
        
        # Test 5: Adjust confidence
        print("\n5. Testing confidence adjustment...")
        adjusted = retriever.adjust_confidence(test_signal, 0.70)
        print(f"   ✓ Confidence adjusted: 0.70 → {adjusted:.3f}")
        
        # Test 6: Get collection stats
        print("\n6. Getting collection stats...")
        stats = updater.get_collection_stats()
        print(f"   ✓ Stats: {stats}")
        
        # Test 7: Test self-learning tracker
        print("\n7. Testing self-learning tracker...")
        from self_learning.tracker import OutcomeTracker
        tracker = OutcomeTracker()
        
        # Log some outcomes
        tracker.log_outcome(
            signal_id='test_1',
            asset='gold',
            signal=1,
            confidence=0.75,
            price=2355.0,
            entry_price=2350.0,
            outcome='WIN',
            pnl=0.21,
            features={'rsi': 65.0, 'macd': 0.5}
        )
        
        tracker.log_outcome(
            signal_id='test_2',
            asset='gold',
            signal=-1,
            confidence=0.68,
            price=2345.0,
            entry_price=2350.0,
            outcome='LOSS',
            pnl=-0.21,
            features={'rsi': 45.0, 'macd': -0.3}
        )
        
        summary = tracker.get_summary(days=1)
        print(f"   ✓ Outcomes logged: {summary}")
        
        # Test 8: Get feature importance
        print("\n8. Getting feature importance...")
        importance = tracker.get_feature_importance()
        print(f"   ✓ Top features: {[f['feature'] for f in importance[:3]]}")
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
        return True
    
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_signal_memory()
    sys.exit(0 if success else 1)
