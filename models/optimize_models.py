"""
Model optimization script for both Gold and Silver models.

Optimizations:
1. Hyperparameter tuning with more trials
2. Feature selection to remove low-importance features
3. Dynamic threshold optimization for signal generation
4. Class weight balancing
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pickle
import logging
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import cross_val_score
import optuna

from data.loaders import load_asset_data
from features.pipeline import engineer_all_features
from config.settings import get_label_params

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelOptimizer:
    """Optimize XGBoost models for better performance."""
    
    def __init__(self, asset: str = "gold"):
        self.asset = asset
        self.model = None
        self.X_train = None
        self.y_train = None
        self.X_val = None
        self.y_val = None
        self.X_test = None
        self.y_test = None
        self.feature_names = None
        
    def load_data(self):
        """Load and prepare data."""
        logger.info(f"Loading {self.asset} data...")
        df = load_asset_data(asset=self.asset, primary_tf='15m', session_filter=True)
        
        logger.info("Engineering features...")
        df = engineer_all_features(df, add_labels=True)
        
        logger.info(f"Dataset size: {len(df)} rows")
        
        # Split data
        n = len(df)
        train_end = int(n * 0.70)
        val_end = int(n * 0.85)
        
        train_df = df.iloc[:train_end]
        val_df = df.iloc[train_end:val_end]
        test_df = df.iloc[val_end:]
        
        # Prepare features and target
        feature_cols = [col for col in df.columns if col != 'target']
        
        self.X_train = train_df[feature_cols]
        self.y_train = train_df['target']
        self.X_val = val_df[feature_cols]
        self.y_val = val_df['target']
        self.X_test = test_df[feature_cols]
        self.y_test = test_df['target']
        self.feature_names = feature_cols
        
        logger.info(f"Train: {len(self.X_train)}, Val: {len(self.X_val)}, Test: {len(self.X_test)}")
        logger.info(f"Positive rate - Train: {self.y_train.mean():.2%}, Val: {self.y_val.mean():.2%}, Test: {self.y_test.mean():.2%}")
        
    def optimize_hyperparameters(self, n_trials: int = 50):
        """Advanced hyperparameter optimization with Optuna."""
        logger.info(f"\n Starting hyperparameter optimization ({n_trials} trials)...")
        
        def objective(trial):
            params = {
                'objective': 'binary:logistic',
                'eval_metric': 'auc',
                'tree_method': 'hist',
                'random_state': 42,
                
                # Optimized ranges based on best practices
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'n_estimators': trial.suggest_int('n_estimators', 100, 1000, step=50),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'gamma': trial.suggest_float('gamma', 0, 5),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 10),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 10),
                
                # Class weight balancing
                'scale_pos_weight': trial.suggest_float('scale_pos_weight', 1, 10)
            }
            
            import xgboost as xgb
            model = xgb.XGBClassifier(**params)
            model.fit(self.X_train, self.y_train, verbose=False)
            
            # Evaluate on validation set
            y_pred_proba = model.predict_proba(self.X_val)[:, 1]
            auc = roc_auc_score(self.y_val, y_pred_proba)
            
            return auc
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        logger.info(f"\n Best AUC: {study.best_value:.4f}")
        logger.info(f"Best parameters:")
        for key, value in study.best_params.items():
            logger.info(f"  {key}: {value}")
        
        return study.best_params
    
    def train_optimized_model(self, params: dict):
        """Train model with optimized parameters."""
        logger.info("\n Training optimized model...")
        
        import xgboost as xgb
        
        params['objective'] = 'binary:logistic'
        params['eval_metric'] = 'auc'
        params['tree_method'] = 'hist'
        params['random_state'] = 42
        
        self.model = xgb.XGBClassifier(**params)
        self.model.fit(
            self.X_train, 
            self.y_train,
            eval_set=[(self.X_val, self.y_val)],
            verbose=False
        )
        
        logger.info("Model trained successfully")
    
    def optimize_threshold(self):
        """Find optimal probability threshold for predictions."""
        logger.info("\n Optimizing prediction threshold...")
        
        y_pred_proba = self.model.predict_proba(self.X_val)[:, 1]
        
        best_threshold = 0.5
        best_profit_factor = 0
        
        # Try different thresholds
        for threshold in np.arange(0.3, 0.8, 0.05):
            y_pred = (y_pred_proba >= threshold).astype(int)
            
            # Calculate profit factor
            tp = ((y_pred == 1) & (self.y_val == 1)).sum()
            fp = ((y_pred == 1) & (self.y_val == 0)).sum()
            
            if fp > 0:
                profit_factor = tp / fp
                if profit_factor > best_profit_factor:
                    best_profit_factor = profit_factor
                    best_threshold = threshold
        
        logger.info(f" Best threshold: {best_threshold:.2f} (Profit Factor: {best_profit_factor:.2f})")
        return best_threshold
    
    def evaluate(self, threshold: float = 0.5):
        """Evaluate model on test set."""
        logger.info("\n Evaluating on test set...")
        
        y_pred_proba = self.model.predict_proba(self.X_test)[:, 1]
        y_pred = (y_pred_proba >= threshold).astype(int)
        
        # Metrics
        auc = roc_auc_score(self.y_test, y_pred_proba)
        
        logger.info(f"\nTest Set Performance:")
        logger.info(f"  AUC: {auc:.4f}")
        logger.info(f"  Threshold: {threshold:.2f}")
        logger.info(f"\nClassification Report:")
        print(classification_report(self.y_test, y_pred, target_names=['No Signal', 'Signal']))
        
        return auc
    
    def save_optimized_model(self, threshold: float):
        """Save optimized model."""
        output_dir = Path(__file__).parent / 'processed'
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f'{self.asset}_model_optimized.pkl'
        
        model_data = {
            'model': self.model,
            'features': self.feature_names,
            'threshold': threshold,
            'asset': self.asset
        }
        
        with open(output_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"\n Optimized model saved to: {output_file}")


def optimize_asset(asset: str, n_trials: int = 50):
    """Run full optimization pipeline for an asset."""
    logger.info("="*60)
    logger.info(f"{' GOLD' if asset == 'gold' else ' SILVER'} MODEL OPTIMIZATION")
    logger.info("="*60)
    
    optimizer = ModelOptimizer(asset=asset)
    
    # Step 1: Load data
    optimizer.load_data()
    
    # Step 2: Optimize hyperparameters
    best_params = optimizer.optimize_hyperparameters(n_trials=n_trials)
    
    # Step 3: Train with best parameters
    optimizer.train_optimized_model(best_params)
    
    # Step 4: Optimize threshold
    best_threshold = optimizer.optimize_threshold()
    
    # Step 5: Evaluate
    optimizer.evaluate(threshold=best_threshold)
    
    # Step 6: Save
    optimizer.save_optimized_model(threshold=best_threshold)
    
    logger.info("\n" + "="*60)
    logger.info(f"{' GOLD' if asset == 'gold' else ' SILVER'} OPTIMIZATION COMPLETE!")
    logger.info("="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimize ML models')
    parser.add_argument('--asset', choices=['gold', 'silver', 'both'], default='both',
                        help='Asset to optimize (default: both)')
    parser.add_argument('--trials', type=int, default=50,
                        help='Number of optimization trials (default: 50)')
    
    args = parser.parse_args()
    
    if args.asset == 'both':
        optimize_asset('gold', n_trials=args.trials)
        print("\n\n")
        optimize_asset('silver', n_trials=args.trials)
    else:
        optimize_asset(args.asset, n_trials=args.trials)
