"""
Signal Memory API endpoints.
Provides endpoints for storing, searching, and learning from signals.
"""

from flask import Blueprint, jsonify, request
from api.app.auth import token_required
import logging

logger = logging.getLogger(__name__)

memory_bp = Blueprint('memory', __name__, url_prefix='/api/memory')


@memory_bp.route('/similar', methods=['GET'])
@token_required
def find_similar(current_user_email):
    """Find similar past signals for a given signal pattern."""
    try:
        from signal_memory import SignalMemoryClient, SignalRetriever
        
        asset = request.args.get('asset', 'gold')
        signal = int(request.args.get('signal', 0))
        confidence = float(request.args.get('confidence', 0.5))
        
        # Build signal data from query params
        signal_data = {
            'asset': asset,
            'signal': signal,
            'confidence': confidence,
        }
        
        # Add optional features
        for key in ['rsi', 'macd', 'atr', 'ema_cross', 'volume_ratio', 'price']:
            val = request.args.get(key)
            if val is not None:
                signal_data[key] = float(val)
        
        retriever = SignalRetriever()
        similar = retriever.find_similar(signal_data, n_results=10)
        
        return jsonify({
            'similar_signals': similar,
            'count': len(similar),
        })
    
    except Exception as e:
        logger.error(f"Error finding similar signals: {e}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/stats', methods=['GET'])
@token_required
def get_stats(current_user_email):
    """Get signal memory statistics."""
    try:
        from signal_memory import SignalMemoryClient, SignalUpdater
        
        updater = SignalUpdater()
        stats = updater.get_collection_stats()
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/store', methods=['POST'])
@token_required
def store_signal(current_user_email):
    """Store a signal in memory."""
    try:
        from signal_memory import SignalUpdater
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        updater = SignalUpdater()
        signal_id = updater.store_signal(data)
        
        return jsonify({
            'signal_id': signal_id,
            'message': 'Signal stored successfully',
        })
    
    except Exception as e:
        logger.error(f"Error storing signal: {e}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/update-outcome', methods=['POST'])
@token_required
def update_outcome(current_user_email):
    """Update a signal with its actual outcome."""
    try:
        from signal_memory import SignalUpdater
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        signal_id = data.get('signal_id')
        outcome = data.get('outcome')
        pnl = data.get('pnl')
        
        if not signal_id or not outcome:
            return jsonify({'error': 'signal_id and outcome required'}), 400
        
        updater = SignalUpdater()
        updater.update_outcome(signal_id, outcome, pnl)
        
        return jsonify({'message': 'Outcome updated'})
    
    except Exception as e:
        logger.error(f"Error updating outcome: {e}")
        return jsonify({'error': str(e)}), 500


# Learning endpoints

@memory_bp.route('/learning/status', methods=['GET'])
@token_required
def learning_status(current_user_email):
    """Get self-learning status."""
    try:
        from self_learning.tracker import OutcomeTracker
        from self_learning.retrainer import ModelRetrainer
        
        tracker = OutcomeTracker()
        retrainer = ModelRetrainer()
        
        summary = tracker.get_summary(days=30)
        feature_importance = tracker.get_feature_importance()[:10]
        should_retrain = retrainer.should_retrain()
        
        return jsonify({
            'outcomes': summary,
            'top_features': feature_importance,
            'should_retrain': should_retrain,
        })
    
    except Exception as e:
        logger.error(f"Error getting learning status: {e}")
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/learning/retrain', methods=['POST'])
@token_required
def trigger_retrain(current_user_email):
    """Trigger model retraining with outcomes."""
    try:
        from self_learning.retrainer import ModelRetrainer
        
        data = request.get_json() or {}
        asset = data.get('asset', 'gold')
        
        retrainer = ModelRetrainer()
        result = retrainer.retrain_model(asset)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error triggering retrain: {e}")
        return jsonify({'error': str(e)}), 500
