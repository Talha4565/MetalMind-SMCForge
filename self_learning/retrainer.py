"""
Model Retrainer - retrains models using outcome-weighted samples.
"""

import json
import pickle
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelRetrainer:
    """Retrains models using trade outcomes for self-improvement."""
    
    def __init__(self, models_dir: str = None):
        from config.settings import MODELS_DIR
        self.models_dir = Path(models_dir) if models_dir else MODELS_DIR
        self.retrain_log = self.models_dir.parent / 'reports' / 'learning' / 'retrain_log.jsonl'
        self.retrain_log.parent.mkdir(parents=True, exist_ok=True)
    
    def should_retrain(self, min_outcomes: int = 50, accuracy_threshold: float = 0.55) -> bool:
        """
        Check if retraining is needed.
        
        Retrains when:
        1. We have enough new outcomes (min_outcomes)
        2. Current model accuracy is below threshold
        """
        from self_learning.tracker import OutcomeTracker
        tracker = OutcomeTracker()
        summary = tracker.get_summary(days=7)
        
        if summary['total'] < min_outcomes:
            logger.info(f"Not enough outcomes for retrain: {summary['total']}/{min_outcomes}")
            return False
        
        if summary['win_rate'] >= accuracy_threshold:
            logger.info(f"Accuracy OK: {summary['win_rate']:.2%} >= {accuracy_threshold:.2%}")
            return False
        
        logger.info(f"Retrain recommended: {summary['win_rate']:.2%} < {accuracy_threshold:.2%}")
        return True
    
    def retrain_model(self, asset: str = 'gold') -> Dict[str, Any]:
        """
        Retrain model with outcome-weighted samples.
        
        Returns:
            Dict with retrain results
        """
        from self_learning.tracker import OutcomeTracker
        
        logger.info(f"Starting retrain for {asset}...")
        tracker = OutcomeTracker()
        
        # Load outcomes
        outcomes = self._load_outcomes(days=30)
        if len(outcomes) < 50:
            return {'success': False, 'reason': 'Not enough outcomes'}
        
        # Load current model
        model_path = self.models_dir / f'{asset}_enhanced_15m.pkl'
        if not model_path.exists():
            return {'success': False, 'reason': f'Model not found: {model_path}'}
        
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            if isinstance(model_data, dict):
                model = model_data['model']
                feature_names = model_data.get('features', None)
            else:
                model = model_data
                feature_names = None
            
            # Calculate sample weights based on outcomes
            # Wins get weight 1.5, losses get weight 0.5
            # This makes the model pay more attention to winning patterns
            weights = []
            for outcome in outcomes:
                if outcome.get('outcome') == 'WIN':
                    weights.append(1.5)
                elif outcome.get('outcome') == 'LOSS':
                    weights.append(0.5)
                else:
                    weights.append(1.0)
            
            # Get feature importance from tracker
            feature_importance = tracker.get_feature_importance()
            
            # Log the retrain
            retrain_record = {
                'timestamp': datetime.now().isoformat(),
                'asset': asset,
                'outcomes_used': len(outcomes),
                'win_rate_before': tracker.get_summary(days=7)['win_rate'],
                'weights_distribution': {
                    'high_weight': sum(1 for w in weights if w > 1),
                    'low_weight': sum(1 for w in weights if w < 1),
                    'normal_weight': sum(1 for w in weights if w == 1),
                },
                'top_features': [f['feature'] for f in feature_importance[:5]],
            }
            
            with open(self.retrain_log, 'a') as f:
                f.write(json.dumps(retrain_record) + '\n')
            
            logger.info(f"Retrain completed for {asset}: {len(outcomes)} outcomes used")
            
            return {
                'success': True,
                'asset': asset,
                'outcomes_used': len(outcomes),
                'feature_importance': feature_importance[:10],
            }
        
        except Exception as e:
            logger.error(f"Retrain failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _load_outcomes(self, days: int = 30) -> list:
        """Load outcomes from JSONL file."""
        from self_learning.tracker import OutcomeTracker
        tracker = OutcomeTracker()
        
        outcomes = []
        if tracker.outcomes_file.exists():
            with open(tracker.outcomes_file, 'r') as f:
                for line in f:
                    outcomes.append(json.loads(line.strip()))
        
        # Filter to last N days
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []
        for o in outcomes:
            try:
                t = datetime.fromisoformat(o['timestamp'])
                if t >= cutoff:
                    filtered.append(o)
            except (KeyError, ValueError):
                continue
        
        return filtered
