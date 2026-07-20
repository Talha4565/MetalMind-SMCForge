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
        Retrain model using the full training pipeline.
        
        Delegates to models/retrain.py which handles:
        - Fresh data loading and feature engineering
        - Optuna hyperparameter tuning
        - Model training with proper train/val/test split
        - Model artifact saving
        
        Returns:
            Dict with retrain results
        """
        from self_learning.tracker import OutcomeTracker
        from models.retrain import retrain_model as full_retrain
        
        logger.info(f"Starting retrain for {asset}...")
        tracker = OutcomeTracker()
        
        # Log outcome context before retraining
        outcomes = self._load_outcomes(days=30)
        win_rate_before = tracker.get_summary(days=7)['win_rate']
        feature_importance = tracker.get_feature_importance()
        
        retrain_record = {
            'timestamp': datetime.now().isoformat(),
            'asset': asset,
            'outcomes_available': len(outcomes),
            'win_rate_before': win_rate_before,
            'top_features': [f['feature'] for f in feature_importance[:5]],
        }
        
        try:
            # Delegate to the full training pipeline
            result = full_retrain(asset, n_trials=20)
            
            retrain_record['status'] = result.get('status', 'unknown')
            retrain_record['accuracy'] = result.get('accuracy')
            retrain_record['model_path'] = result.get('model_path')
            
            with open(self.retrain_log, 'a') as f:
                f.write(json.dumps(retrain_record) + '\n')
            
            logger.info(f"Retrain completed for {asset}: accuracy={result.get('accuracy', 'N/A')}")
            
            return {
                'success': result.get('status') == 'success',
                'asset': asset,
                'accuracy': result.get('accuracy'),
                'model_path': result.get('model_path'),
                'outcomes_available': len(outcomes),
                'win_rate_before': win_rate_before,
                'feature_importance': feature_importance[:10],
            }
        
        except Exception as e:
            retrain_record['status'] = 'failed'
            retrain_record['error'] = str(e)
            with open(self.retrain_log, 'a') as f:
                f.write(json.dumps(retrain_record) + '\n')
            
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
