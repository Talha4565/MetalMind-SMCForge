"""
Main entry point for ML-Signals trading system.
Orchestrates training, backtesting, and evaluation.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from models.train_enhanced import train_enhanced_model, EnhancedModelTrainer
from backtesting.engine import BacktestEngine
from explainability.shap_analyzer import ShapAnalyzer
from data.loaders import load_gold_data
from features.pipeline import engineer_all_features
from config.settings import PROJECT_ROOT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_mode(args):
    """Training mode: Train enhanced model."""
    logger.info("🚀 Starting training mode...")
    
    model, results = train_enhanced_model(
        primary_tf=args.timeframe,
        n_trials=args.optuna_trials
    )
    
    logger.info(f"✅ Training complete! Accuracy: {results['enhanced_accuracy']:.2%}")
    

def backtest_mode(args):
    """Backtest mode: Test trained model."""
    logger.info("🚀 Starting backtest mode...")
    
    import pickle
    from config.settings import MODEL_CONFIG
    
    # Load model
    model_path = MODEL_CONFIG['enhanced_model_path']
    if not model_path.exists():
        logger.error(f"Model not found at {model_path}. Train first with --mode train")
        return
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load and prepare data
    trainer = EnhancedModelTrainer(primary_tf=args.timeframe)
    trainer.prepare_data(session_filter=True)
    
    # Get test predictions
    test_pred = model.predict(trainer.test_x)
    
    # Run backtest
    test_df = trainer.test_x.copy()
    test_df['open'] = test_df.get('open', trainer.test_x.iloc[:, 0])  # Fallback
    test_df['high'] = test_df.get('high', trainer.test_x.iloc[:, 1])
    test_df['low'] = test_df.get('low', trainer.test_x.iloc[:, 2])
    test_df['close'] = test_df.get('close', trainer.test_x.iloc[:, 3])
    
    engine = BacktestEngine()
    results = engine.run_backtest(test_df, test_pred)
    
    # Print summary
    engine.print_summary()
    
    logger.info("✅ Backtest complete!")


def explain_mode(args):
    """Explainability mode: Analyze model with SHAP."""
    logger.info("🚀 Starting explainability mode...")
    
    import pickle
    from config.settings import MODEL_CONFIG, REPORTS_DIR
    
    # Load model
    model_path = MODEL_CONFIG['enhanced_model_path']
    if not model_path.exists():
        logger.error(f"Model not found at {model_path}. Train first with --mode train")
        return
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load data
    trainer = EnhancedModelTrainer(primary_tf=args.timeframe)
    trainer.prepare_data(session_filter=True)
    
    # SHAP analysis
    analyzer = ShapAnalyzer(model)
    
    logger.info("Computing SHAP values...")
    analyzer.compute_shap_values(trainer.test_x)
    
    # Generate plots
    plots_dir = REPORTS_DIR / "shap_plots"
    plots_dir.mkdir(exist_ok=True, parents=True)
    
    logger.info("Generating feature importance plot...")
    analyzer.plot_feature_importance(
        trainer.test_x,
        top_n=20,
        save_path=plots_dir / "feature_importance.png"
    )
    
    logger.info("Generating summary plot...")
    analyzer.plot_summary(
        trainer.test_x,
        top_n=20,
        save_path=plots_dir / "summary_plot.png"
    )
    
    # Print top features
    top_features = analyzer.get_top_features(20)
    print("\n📊 Top 20 Features by SHAP Importance:")
    print(top_features.to_string(index=False))
    
    logger.info(f"✅ SHAP analysis complete! Plots saved to {plots_dir}")


def full_pipeline(args):
    """Full pipeline: Train, backtest, and explain."""
    logger.info("🚀 Running full pipeline...")
    
    # Train
    logger.info("\n" + "="*80)
    logger.info("PHASE 1: TRAINING")
    logger.info("="*80)
    train_mode(args)
    
    # Backtest
    logger.info("\n" + "="*80)
    logger.info("PHASE 2: BACKTESTING")
    logger.info("="*80)
    backtest_mode(args)
    
    # Explain
    logger.info("\n" + "="*80)
    logger.info("PHASE 3: EXPLAINABILITY")
    logger.info("="*80)
    explain_mode(args)
    
    logger.info("\n✅ Full pipeline complete!")


def main():
    parser = argparse.ArgumentParser(
        description="ML-Signals: Smart Money Concepts Trading System"
    )
    
    parser.add_argument(
        '--mode',
        choices=['train', 'backtest', 'explain', 'full'],
        default='full',
        help='Operation mode (default: full)'
    )
    
    parser.add_argument(
        '--timeframe',
        default='15m',
        help='Primary timeframe (default: 15m)'
    )
    
    parser.add_argument(
        '--optuna-trials',
        type=int,
        default=30,
        help='Number of Optuna trials for hyperparameter tuning (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Route to appropriate mode
    modes = {
        'train': train_mode,
        'backtest': backtest_mode,
        'explain': explain_mode,
        'full': full_pipeline
    }
    
    modes[args.mode](args)


if __name__ == "__main__":
    main()
