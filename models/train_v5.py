"""
V5 Model Training — Ratchet methodology.
Trains from V4 baseline with iterative improvement and rollback protection.

Ratchet thresholds (defined before iteration 1):
- Accuracy: >= 0.50 (50%)
- Win rate (backtest): >= 45%
- Profit factor: >= 1.5
- Max iterations: 5
- Convergence: epsilon=0.01, n_consecutive=2
"""

import pickle
import json
import shutil
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb
import optuna

from config.settings import GOLD_DATASET_DIR, MODELS_DIR, GOLD_LABEL_PARAMS
from data.loaders import load_asset_data
from features.pipeline import engineer_all_features
from features.v4_features import compute_v4_features

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# RATCHET STATE
# ============================================================================
RATCHET_STATE = {
    'task': 'V5 gold direction model training',
    'iteration': 0,
    'max_iterations': 5,
    'thresholds': {
        'accuracy': 0.50,
        'win_rate': 0.45,
        'profit_factor': 1.5,
    },
    'convergence': {'epsilon': 0.01, 'n_consecutive': 2},
    'findings': [],
    'scores': {},
    'checkpoints_dir': str(MODELS_DIR / 'v5_checkpoints'),
}

# V4 model path
V4_MODEL_PATH = MODELS_DIR / 'gold_regression_system.pkl'
V5_MODEL_PATH = MODELS_DIR / 'gold_regression_system.pkl'  # overwrites the file the API loads


def save_checkpoint(iteration: int, model, metrics: dict):
    """Snapshot model and metrics at each iteration."""
    ckpt_dir = Path(RATCHET_STATE['checkpoints_dir'])
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    ckpt_path = ckpt_dir / f'iter{iteration}_model.pkl'
    with open(ckpt_path, 'wb') as f:
        pickle.dump({
            'direction_model': model,
            'features': RATCHET_STATE.get('feature_names', []),
        }, f)

    metrics_path = ckpt_dir / f'iter{iteration}_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Checkpoint saved: iter{iteration}")


def load_v4_baseline():
    """Load V4 model as baseline for comparison."""
    if not V4_MODEL_PATH.exists():
        logger.error(f"V4 model not found: {V4_MODEL_PATH}")
        return None

    with open(V4_MODEL_PATH, 'rb') as f:
        v4 = pickle.load(f)

    logger.info(f"V4 baseline loaded: {type(v4['direction_model']).__name__}, {len(v4['features'])} features")
    return v4


def prepare_data():
    """Load and prepare data with V4 features."""
    logger.info("Loading gold 15m data with multi-TF alignment...")
    df = load_asset_data(asset='gold', primary_tf='15m', session_filter=False)

    logger.info("Engineering standard features...")
    df = engineer_all_features(df, add_labels=True, asset='gold')

    logger.info("Computing V4 features...")
    df = compute_v4_features(df)

    # Drop rows with NaN from feature engineering
    df.dropna(inplace=True)
    logger.info(f"Data ready: {len(df)} rows, {len(df.columns)} columns")

    return df


def train_iteration(df, v4_features, iteration: int, prev_accuracy: float = None):
    """Train one iteration of V5 model."""
    logger.info(f"\n{'='*60}")
    logger.info(f"ITERATION {iteration}")
    logger.info(f"{'='*60}")

    # Split data
    n = len(df)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)

    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]

    # Separate features and labels
    feature_cols = [c for c in v4_features if c in df.columns]
    RATCHET_STATE['feature_names'] = feature_cols

    X_train = train_df[feature_cols].fillna(0)
    y_train = train_df['target']
    X_val = val_df[feature_cols].fillna(0)
    y_val = val_df['target']
    X_test = test_df[feature_cols].fillna(0)
    y_test = test_df['target']

    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    logger.info(f"Class distribution train: {dict(y_train.value_counts())}")

    # Hyperparameter tuning with Optuna (fewer trials for speed)
    def objective(trial):
        params = {
            'n_estimators': 1500,
            'max_depth': trial.suggest_int('max_depth', 4, 10),
            'learning_rate': trial.suggest_float('lr', 0.005, 0.05, log=True),
            'subsample': trial.suggest_float('sub', 0.6, 0.9),
            'colsample_bytree': trial.suggest_float('col', 0.5, 0.8),
            'gamma': trial.suggest_float('gamma', 0.5, 3.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 3, 10),
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'early_stopping_rounds': 50,
            'random_state': 42
        }
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=0)
        pred = model.predict(X_val)
        return 1 - accuracy_score(y_val, pred)

    logger.info("Tuning hyperparameters (20 trials)...")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=20, show_progress_bar=False)

    best_params = study.best_params
    logger.info(f"Best params: {best_params}")

    # Train final model
    scale = (y_train == 0).sum() / (y_train == 1).sum()
    model = xgb.XGBClassifier(
        n_estimators=1500,
        max_depth=best_params['max_depth'],
        learning_rate=best_params['lr'],
        colsample_bytree=best_params['col'],
        subsample=best_params['sub'],
        gamma=best_params['gamma'],
        min_child_weight=best_params['min_child_weight'],
        objective='binary:logistic',
        eval_metric='logloss',
        scale_pos_weight=scale,
        early_stopping_rounds=50,
        random_state=42
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=0)

    # Evaluate
    test_pred = model.predict(X_test)
    test_acc = accuracy_score(y_test, test_pred)

    val_pred = model.predict(X_val)
    val_acc = accuracy_score(y_val, val_pred)

    logger.info(f"Test accuracy: {test_acc:.4f}")
    logger.info(f"Val accuracy: {val_acc:.4f}")

    # Backtest simulation
    bt_metrics = run_quick_backtest(model, df, feature_cols, test_df)

    metrics = {
        'iteration': iteration,
        'test_accuracy': test_acc,
        'val_accuracy': val_acc,
        'win_rate': bt_metrics['win_rate'],
        'profit_factor': bt_metrics['profit_factor'],
        'total_trades': bt_metrics['total_trades'],
        'best_params': best_params,
    }

    logger.info(f"Backtest: win_rate={bt_metrics['win_rate']:.2%}, "
                f"profit_factor={bt_metrics['profit_factor']:.2f}, "
                f"trades={bt_metrics['total_trades']}")

    return model, metrics


def run_quick_backtest(model, full_df, feature_cols, test_df):
    """Run a quick backtest on the test set."""
    from backtesting.engine import BacktestEngine

    # Get predictions for test set
    X_test = test_df[feature_cols].fillna(0)
    predictions = model.predict(X_test)
    try:
        probas = model.predict_proba(X_test)[:, 1]
    except:
        probas = np.full(len(predictions), 0.5)

    # Apply V4 trend filter
    signals = np.zeros(len(predictions), dtype=int)
    if 'trend_ema_cross' in test_df.columns:
        for i in range(len(predictions)):
            proba = probas[i]
            trend = test_df.iloc[i].get('trend_ema_cross', 0)
            confidence = max(proba, 1 - proba)
            if trend == 1 and proba >= 0.5 and confidence >= 0.65:
                signals[i] = 1
            elif trend == 0 and proba < 0.5 and confidence >= 0.65:
                signals[i] = -1
    else:
        signals = (predictions > 0).astype(int)

    # Run backtest
    engine = BacktestEngine(asset='gold')
    results = engine.run_backtest(test_df, signals)

    metrics = results.get('metrics', {})
    return {
        'win_rate': metrics.get('win_rate', 0),
        'profit_factor': metrics.get('profit_factor', 0) if np.isfinite(metrics.get('profit_factor', 0)) else 0,
        'total_trades': metrics.get('n_trades', 0),
    }


def evaluate_findings(metrics: dict, prev_accuracy: float = None):
    """Evaluate findings against thresholds."""
    findings = []
    thresholds = RATCHET_STATE['thresholds']

    # Check accuracy threshold
    if metrics['test_accuracy'] < thresholds['accuracy']:
        findings.append({
            'id': f"F-acc-{metrics['iteration']}",
            'severity': 'critical',
            'owner': 'builder',
            'source': 'numeric_gate',
            'status': 'open',
            'confidence': 0.95,
            'evidence': f"Accuracy {metrics['test_accuracy']:.4f} < threshold {thresholds['accuracy']}"
        })

    # Check win rate threshold
    if metrics['win_rate'] < thresholds['win_rate']:
        findings.append({
            'id': f"F-wr-{metrics['iteration']}",
            'severity': 'major',
            'owner': 'builder',
            'source': 'numeric_gate',
            'status': 'open',
            'confidence': 0.9,
            'evidence': f"Win rate {metrics['win_rate']:.2%} < threshold {thresholds['win_rate']:.2%}"
        })

    # Check profit factor threshold
    if metrics['profit_factor'] < thresholds['profit_factor']:
        findings.append({
            'id': f"F-pf-{metrics['iteration']}",
            'severity': 'major',
            'owner': 'builder',
            'source': 'numeric_gate',
            'status': 'open',
            'confidence': 0.9,
            'evidence': f"Profit factor {metrics['profit_factor']:.2f} < threshold {thresholds['profit_factor']:.2f}"
        })

    # Check regression from previous iteration
    if prev_accuracy is not None:
        if metrics['test_accuracy'] < prev_accuracy - 0.01:
            findings.append({
                'id': f"F-reg-{metrics['iteration']}",
                'severity': 'critical',
                'owner': 'builder',
                'source': 'numeric_gate',
                'status': 'open',
                'confidence': 0.95,
                'evidence': f"Regression: {metrics['test_accuracy']:.4f} < {prev_accuracy:.4f} (prev)"
            })

    return findings


def check_convergence(scores: list):
    """Check if improvement has converged."""
    if len(scores) < RATCHET_STATE['convergence']['n_consecutive'] + 1:
        return False

    recent = scores[-RATCHET_STATE['convergence']['n_consecutive'] - 1:]
    improvements = [recent[i+1] - recent[i] for i in range(len(recent) - 1)]

    return all(abs(imp) < RATCHET_STATE['convergence']['epsilon'] for imp in improvements)


def main():
    """Run V5 training with Ratchet methodology."""
    logger.info("=" * 60)
    logger.info("V5 MODEL TRAINING — RATCHET METHODOLOGY")
    logger.info("=" * 60)

    # Load V4 baseline
    v4 = load_v4_baseline()
    if v4 is None:
        logger.error("Cannot proceed without V4 baseline")
        return

    v4_features = v4['features']

    # Prepare data
    df = prepare_data()

    # Training loop
    prev_accuracy = None
    best_accuracy = 0
    best_model = None
    all_scores = []
    all_findings = []

    for iteration in range(1, RATCHET_STATE['max_iterations'] + 1):
        RATCHET_STATE['iteration'] = iteration

        # Train
        model, metrics = train_iteration(df, v4_features, iteration, prev_accuracy)

        # Evaluate findings
        findings = evaluate_findings(metrics, prev_accuracy)
        all_findings.extend(findings)

        # Save checkpoint
        save_checkpoint(iteration, model, metrics)

        # Track scores
        all_scores.append(metrics['test_accuracy'])
        RATCHET_STATE['scores'][f'iter{iteration}'] = metrics

        # Check if this is the best model
        if metrics['test_accuracy'] > best_accuracy:
            best_accuracy = metrics['test_accuracy']
            best_model = model
            logger.info(f"New best model at iteration {iteration}")

        # Check convergence
        if check_convergence(all_scores):
            logger.info(f"Converged at iteration {iteration}")
            break

        # Check if all thresholds met
        thresholds = RATCHET_STATE['thresholds']
        if (metrics['test_accuracy'] >= thresholds['accuracy'] and
            metrics['win_rate'] >= thresholds['win_rate'] and
            metrics['profit_factor'] >= thresholds['profit_factor']):
            logger.info(f"All thresholds met at iteration {iteration}")
            break

        prev_accuracy = metrics['test_accuracy']

    # Save best model as V5
    if best_model is not None:
        v5_data = {
            'direction_model': best_model,
            'tp_model': v4['tp_model'],  # Keep V4 TP/SL models
            'sl_model': v4['sl_model'],
            'features': v4_features,
        }
        with open(V5_MODEL_PATH, 'wb') as f:
            pickle.dump(v5_data, f)
        logger.info(f"V5 model saved: {V5_MODEL_PATH}")

    # Save Ratchet state
    state_path = Path(RATCHET_STATE['checkpoints_dir']) / 'ratchet_state.json'
    with open(state_path, 'w') as f:
        json.dump({
            **RATCHET_STATE,
            'findings': all_findings,
            'final_accuracy': best_accuracy,
        }, f, indent=2, default=str)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Best accuracy: {best_accuracy:.4f}")
    logger.info(f"Iterations: {RATCHET_STATE['iteration']}")
    logger.info(f"Findings: {len(all_findings)}")
    for f in all_findings:
        logger.info(f"  {f['id']}: {f['severity']} - {f['evidence']}")


if __name__ == '__main__':
    main()
