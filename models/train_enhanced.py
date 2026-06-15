"""
Enhanced model training pipeline with baseline comparison.
Trains XGBoost model with SMC + multi-timeframe features.
"""

import pandas as pd
import numpy as np
import pickle
import logging
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import optuna

from config.settings import (
    MODEL_CONFIG, BASELINE_CONFIG, PROJECT_ROOT,
    get_xgboost_params
)
from data.loaders import load_gold_data, load_silver_data, load_asset_data, train_val_test_split
from features.pipeline import engineer_all_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedModelTrainer:
    """Trains enhanced model and compares against baseline."""
    
    def __init__(self, primary_tf: str = "15m", asset: str = "gold"):
        self.primary_tf = primary_tf
        self.asset = asset
        self.model = None
        self.best_params = None
        self.baseline_model = None
        
    def load_baseline_model(self):
        """Load existing baseline model for comparison."""
        baseline_path = MODEL_CONFIG['baseline_model_path']
        
        if baseline_path.exists():
            logger.info(f"Loading baseline model from {baseline_path}")
            with open(baseline_path, 'rb') as f:
                self.baseline_model = pickle.load(f)
            logger.info("✅ Baseline model loaded")
        else:
            logger.warning(f"⚠️ Baseline model not found at {baseline_path}")
    
    def prepare_data(self, session_filter: bool = True):
        """Load and prepare data with full feature engineering."""
        logger.info("=" * 80)
        logger.info(f"STEP 1: DATA PREPARATION ({self.asset.upper()})")
        logger.info("=" * 80)
        
        # Load multi-timeframe data
        logger.info(f"Loading {self.asset} {self.primary_tf} data with multi-timeframe context...")
        df = load_asset_data(asset=self.asset, primary_tf=self.primary_tf, session_filter=session_filter)
        logger.info(f"Loaded {len(df)} rows")
        
        # Apply feature engineering
        logger.info("Applying complete feature engineering pipeline...")
        df = engineer_all_features(df, add_labels=True, asset=self.asset)
        logger.info(f"Engineered {len(df.columns)} features")
        
        # Split data
        logger.info("Splitting into train/val/test...")
        train_df, val_df, test_df = train_val_test_split(
            df,
            train_pct=BASELINE_CONFIG['train_split']['train'],
            val_pct=BASELINE_CONFIG['train_split']['val'],
            test_pct=BASELINE_CONFIG['train_split']['test']
        )
        
        # Separate features and labels
        self.train_x = train_df.drop(columns='target')
        self.train_y = train_df['target']
        self.val_x = val_df.drop(columns='target')
        self.val_y = val_df['target']
        self.test_x = test_df.drop(columns='target')
        self.test_y = test_df['target']
        
        logger.info(f"✅ Data ready: {len(self.train_x)} train, {len(self.val_x)} val, {len(self.test_x)} test")
        
        return self.train_x, self.train_y, self.val_x, self.val_y, self.test_x, self.test_y
    
    def tune_hyperparameters(self, n_trials: int = 30):
        """Tune hyperparameters with Optuna."""
        logger.info("=" * 80)
        logger.info("STEP 2: HYPERPARAMETER TUNING")
        logger.info("=" * 80)
        
        def objective(trial):
            params = {
                'n_estimators': 1000,
                'max_depth': trial.suggest_int('max_depth', 3, 5),
                'learning_rate': trial.suggest_float('lr', 0.01, 0.05, log=True),
                'subsample': trial.suggest_float('sub', 0.6, 0.9),
                'colsample_bytree': trial.suggest_float('col', 0.5, 0.8),
                'objective': 'binary:logistic',
                'eval_metric': 'logloss',
                'early_stopping_rounds': 50,
                'random_state': 42
            }
            
            model = xgb.XGBClassifier(**params)
            model.fit(self.train_x, self.train_y, 
                     eval_set=[(self.val_x, self.val_y)], 
                     verbose=0)
            
            pred = model.predict(self.val_x)
            return 1 - accuracy_score(self.val_y, pred)
        
        logger.info(f"Starting Optuna optimization ({n_trials} trials)...")
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        self.best_params = study.best_params
        best_acc = 1 - study.best_value
        
        logger.info(f"✅ Best params: {self.best_params}")
        logger.info(f"✅ Best validation accuracy: {best_acc:.2%}")
        
        return self.best_params
    
    def train_final_model(self):
        """Train final model with best hyperparameters."""
        logger.info("=" * 80)
        logger.info("STEP 3: FINAL MODEL TRAINING")
        logger.info("=" * 80)
        
        # Calculate class weights
        scale = (self.train_y == 0).sum() / (self.train_y == 1).sum()
        logger.info(f"Class imbalance ratio: {scale:.2f}:1")
        
        # Build model with best params
        self.model = xgb.XGBClassifier(
            n_estimators=1500,
            max_depth=self.best_params['max_depth'],
            learning_rate=self.best_params['lr'],
            colsample_bytree=self.best_params['col'],
            subsample=self.best_params['sub'],
            objective='binary:logistic',
            eval_metric='logloss',
            scale_pos_weight=scale,
            early_stopping_rounds=50,
            random_state=42
        )
        
        logger.info("Training final model...")
        self.model.fit(
            self.train_x, self.train_y,
            eval_set=[(self.val_x, self.val_y)],
            verbose=0
        )
        
        logger.info("✅ Training complete")
    
    def evaluate_and_compare(self):
        """Evaluate enhanced model and compare with baseline."""
        logger.info("=" * 80)
        logger.info("STEP 4: EVALUATION & COMPARISON")
        logger.info("=" * 80)
        
        # Enhanced model predictions
        enhanced_pred = self.model.predict(self.test_x)
        enhanced_prob = self.model.predict_proba(self.test_x)[:, 1]
        enhanced_acc = accuracy_score(self.test_y, enhanced_pred)
        
        logger.info("\n📊 ENHANCED MODEL RESULTS:")
        logger.info(f"Test Accuracy: {enhanced_acc:.2%}")
        logger.info("\nClassification Report:")
        print(classification_report(self.test_y, enhanced_pred))
        
        # Baseline comparison (if available)
        if self.baseline_model is not None:
            try:
                # Get baseline features (only those it was trained on)
                baseline_features = self.baseline_model.get_booster().feature_names
                
                # Check if test_x has all baseline features
                missing_features = set(baseline_features) - set(self.test_x.columns)
                if missing_features:
                    logger.warning(f"⚠️ Baseline model expects features not in enhanced dataset: {missing_features}")
                    logger.info("Skipping baseline comparison")
                else:
                    baseline_test_x = self.test_x[baseline_features]
                    baseline_pred = self.baseline_model.predict(baseline_test_x)
                    baseline_acc = accuracy_score(self.test_y, baseline_pred)
                    
                    logger.info("\n📊 BASELINE MODEL RESULTS:")
                    logger.info(f"Test Accuracy: {baseline_acc:.2%}")
                    
                    logger.info("\n🎯 IMPROVEMENT:")
                    improvement = (enhanced_acc - baseline_acc) * 100
                    logger.info(f"Accuracy gain: {improvement:+.2f} percentage points")
                    
                    if enhanced_acc > baseline_acc:
                        logger.info("✅ Enhanced model OUTPERFORMS baseline!")
                    elif enhanced_acc == baseline_acc:
                        logger.info("⚠️ Enhanced model MATCHES baseline")
                    else:
                        logger.info("❌ Enhanced model UNDERPERFORMS baseline")
            
            except Exception as e:
                logger.warning(f"Could not compare with baseline: {e}")
        
        return {
            'enhanced_accuracy': enhanced_acc,
            'enhanced_predictions': enhanced_pred,
            'enhanced_probabilities': enhanced_prob
        }
    
    def save_model(self, filename: str = "enhanced_15m.pkl"):
        """Save trained model."""
        save_path = MODEL_CONFIG['enhanced_model_path'].parent / filename
        save_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(save_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        logger.info(f"✅ Model saved to {save_path}")
        return save_path
    
    def run_complete_pipeline(self, n_trials: int = 30):
        """Run complete training pipeline."""
        logger.info("\n" + "=" * 80)
        logger.info("ENHANCED MODEL TRAINING PIPELINE")
        logger.info("=" * 80 + "\n")
        
        # Load baseline for comparison
        self.load_baseline_model()
        
        # Prepare data
        self.prepare_data(session_filter=True)
        
        # Tune hyperparameters
        self.tune_hyperparameters(n_trials=n_trials)
        
        # Train final model
        self.train_final_model()
        
        # Evaluate and compare
        results = self.evaluate_and_compare()
        
        # Save model
        model_path = self.save_model()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ PIPELINE COMPLETE")
        logger.info("=" * 80)
        
        return self.model, results


def train_enhanced_model(primary_tf: str = "15m", n_trials: int = 30):
    """
    Convenience function to train enhanced model.
    
    Args:
        primary_tf: Primary timeframe (default "15m")
        n_trials: Number of Optuna trials (default 30)
    
    Returns:
        Trained model and evaluation results
    """
    trainer = EnhancedModelTrainer(primary_tf=primary_tf)
    return trainer.run_complete_pipeline(n_trials=n_trials)


if __name__ == "__main__":
    # Train enhanced model
    model, results = train_enhanced_model(primary_tf="15m", n_trials=30)
    
    print("\n✅ Training complete!")
    print(f"Enhanced model accuracy: {results['enhanced_accuracy']:.2%}")
