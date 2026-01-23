"""
Train XGBoost model for Silver (XAG/USD) predictions.
Uses the same pipeline as Gold model for consistency.

NOTE: Silver has lower volatility than Gold, so label parameters 
may need adjustment. If you get all zero labels, reduce take_profit_pct
in config/settings.py or modify the BASELINE_CONFIG['label_params'].
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.train_enhanced import EnhancedModelTrainer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_silver_model(primary_tf: str = "15m"):
    """
    Train Silver model using the same enhanced pipeline as Gold.
    
    Args:
        primary_tf: Primary timeframe for predictions (default "15m")
    """
    logger.info("="*60)
    logger.info("🥈 SILVER (XAG/USD) MODEL TRAINING")
    logger.info("="*60)
    
    # Initialize trainer with Silver asset
    trainer = EnhancedModelTrainer(
        primary_tf=primary_tf,
        asset="silver"  # Specify Silver asset
    )
    
    # Load and prepare Silver data
    logger.info("\n📊 Step 1: Loading Silver data...")
    try:
        trainer.prepare_data(session_filter=True)
    except Exception as e:
        logger.error(f"Error during data preparation: {e}")
        logger.error("This might be due to insufficient data after filtering.")
        logger.error("Try disabling session_filter or check your data files.")
        raise
    
    # Check if we have any positive labels
    if hasattr(trainer, 'train_y') and trainer.train_y is not None:
        positive_labels = (trainer.train_y == 1).sum()
        total_labels = len(trainer.train_y)
        logger.info(f"\n📊 Label distribution: {positive_labels}/{total_labels} positive ({positive_labels/total_labels*100:.2f}%)")
        
        if positive_labels == 0:
            logger.error("\n" + "="*60)
            logger.error("❌ TRAINING CANNOT PROCEED")
            logger.error("="*60)
            logger.error("No positive labels found in the training data!")
            logger.error("")
            logger.error("Reason: The take profit threshold is too high for Silver.")
            logger.error("Silver (XAG/USD) has lower volatility than Gold (XAU/USD).")
            logger.error("")
            logger.error("SOLUTION:")
            logger.error("1. Open: ml-signals/config/settings.py")
            logger.error("2. Find: BASELINE_CONFIG['label_params']['take_profit_pct']")
            logger.error("3. Change from: 0.0045 (0.45%)")
            logger.error("4. Try: 0.002 to 0.003 (0.2% to 0.3%) for Silver")
            logger.error("")
            logger.error("Alternatively, use different label parameters specific to Silver.")
            logger.error("="*60)
            raise ValueError("Cannot train model with zero positive labels. Adjust label parameters.")
    
    # Hyperparameter tuning
    logger.info("\n🎯 Step 2: Hyperparameter tuning...")
    trainer.tune_hyperparameters(n_trials=30)
    
    # Train final model
    logger.info("\n🚀 Step 3: Training final model...")
    trainer.train_final_model()
    
    # Evaluate
    logger.info("\n📈 Step 4: Evaluation...")
    trainer.evaluate_and_compare()
    
    # Save model
    output_path = Path(__file__).parent / "processed" / "silver_model_enhanced.pkl"
    output_path.parent.mkdir(exist_ok=True)
    
    import joblib
    joblib.dump(trainer.model, output_path)
    logger.info(f"\n✅ Silver model saved to: {output_path}")
    
    logger.info("\n" + "="*60)
    logger.info("🎉 SILVER MODEL TRAINING COMPLETE!")
    logger.info("="*60)
    
    return trainer


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Silver XGBoost model")
    parser.add_argument("--timeframe", default="15m", help="Primary timeframe (default: 15m)")
    
    args = parser.parse_args()
    
    trainer = train_silver_model(primary_tf=args.timeframe)
