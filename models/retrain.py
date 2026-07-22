"""
Retrain model after fresh data is appended to CSVs.
Logs training metrics to reports/training_logs/.
"""

import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def retrain_model(asset: str = 'gold', n_trials: int = 30) -> Dict[str, Any]:
    """
    Retrain model on full dataset (including newly appended data).
    
    Args:
        asset: 'gold' or 'silver'
        n_trials: Number of Optuna trials
    
    Returns:
        Dict with training metrics
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from models.train_enhanced import EnhancedModelTrainer
    from config.settings import REPORTS_DIR
    
    log_dir = REPORTS_DIR / 'training_logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    metrics = {
        'asset': asset,
        'started_at': datetime.now().isoformat(),
        'status': 'running',
    }
    
    try:
        logger.info(f"Starting retrain for {asset}...")
        
        # Train model
        trainer = EnhancedModelTrainer(primary_tf='15m', asset=asset)
        trainer.prepare_data(session_filter=True)
        
        metrics['data_rows'] = len(trainer.train_x) + len(trainer.val_x) + len(trainer.test_x)
        metrics['train_rows'] = len(trainer.train_x)
        metrics['val_rows'] = len(trainer.val_x)
        metrics['test_rows'] = len(trainer.test_x)
        metrics['feature_count'] = len(trainer.train_x.columns)
        
        # Tune hyperparameters
        best_params = trainer.tune_hyperparameters(n_trials=n_trials)
        metrics['best_params'] = best_params
        
        # Train final model
        trainer.train_final_model()
        
        # Evaluate
        results = trainer.evaluate_and_compare()
        metrics['accuracy'] = float(results['enhanced_accuracy'])
        
        # Save model — gold must write gold_regression_system.pkl (the file the API loads).
        # Preserve existing tp/sl models and feature names so the dict format stays compatible.
        if asset == 'silver':
            save_path = Path('models/silver_enhanced_15m.pkl')
            with open(save_path, 'wb') as f:
                pickle.dump(trainer.model, f)
        else:
            save_path = Path('models/gold_regression_system.pkl')
            # Wrap gold in the dict format the API load_model() expects
            feature_names = list(trainer.model.feature_names_in_) if hasattr(trainer.model, 'feature_names_in_') else []
            gold_dict = {
                'direction_model': trainer.model,
                'features': feature_names,
            }
            # Carry forward tp/sl models from existing file if present
            old_path = Path('models/gold_regression_system.pkl')
            if old_path.exists():
                try:
                    with open(old_path, 'rb') as f_old:
                        old_data = pickle.load(f_old)
                    if isinstance(old_data, dict):
                        gold_dict['tp_model'] = old_data.get('tp_model')
                        gold_dict['sl_model'] = old_data.get('sl_model')
                except Exception:
                    pass  # Keep direction_model only if old file unreadable
            with open(save_path, 'wb') as f:
                pickle.dump(gold_dict, f)
        
        metrics['model_path'] = str(save_path)
        metrics['status'] = 'success'
        
        # Save training log
        metrics['completed_at'] = datetime.now().isoformat()
        duration = (datetime.fromisoformat(metrics['completed_at']) - 
                   datetime.fromisoformat(metrics['started_at'])).total_seconds()
        metrics['duration_seconds'] = round(duration, 2)
        
        # Write to log file
        log_file = log_dir / f"{asset}_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Also update latest.json
        latest_file = log_dir / f"{asset}_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Training complete for {asset}: {metrics['accuracy']:.2%} accuracy")
        logger.info(f"Log saved to {log_file}")
        
    except Exception as e:
        metrics['status'] = 'failed'
        metrics['error'] = str(e)
        metrics['completed_at'] = datetime.now().isoformat()
        
        log_file = log_dir / f"{asset}_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.error(f"Training failed for {asset}: {e}")
        raise
    
    return metrics


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Retrain ML model')
    parser.add_argument('--asset', choices=['gold', 'silver'], default='gold')
    parser.add_argument('--trials', type=int, default=30)
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    result = retrain_model(args.asset, args.trials)
    print(json.dumps(result, indent=2))
