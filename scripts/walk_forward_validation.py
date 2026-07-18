"""
Walk-Forward Cross-Validation for MetalMind SMCForge

Standalone script — does NOT modify any existing project files.
Imports from: features/pipeline, data/loaders, backtesting/engine, config/settings.

Usage:
    python scripts/walk_forward_validation.py --asset gold
    python scripts/walk_forward_validation.py --asset silver
    python scripts/walk_forward_validation.py --asset both

Output:
    reports/walk_forward_{asset}.md — per-fold breakdown + summary statistics
    reports/walk_forward_comparison.md — single-split vs walk-forward comparison
"""

import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import BACKTEST_CONFIG, REPORTS_DIR
from data.loaders import load_asset_data
from features.pipeline import engineer_all_features
from backtesting.engine import BacktestEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s — %(levelname)s — %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# 1. WALK-FORWARD FOLD GENERATOR
# ============================================================================

def generate_walk_forward_folds(
    df: pd.DataFrame,
    train_months: int = 12,
    test_months: int = 3,
    step_months: int = 3,
) -> List[Dict[str, Any]]:
    """
    Generate chronological walk-forward train/test splits.
    
    Each fold:
    - train: [start, start + train_months)
    - test:  [start + train_months, start + train_months + test_months)
    - then slide forward by step_months
    
    Returns list of dicts with train_df, test_df, and date ranges.
    """
    folds = []
    dates = df.index
    start = dates.min()
    end = dates.max()
    
    while True:
        train_end = start + pd.DateOffset(months=train_months)
        test_end = train_end + pd.DateOffset(months=test_months)
        
        if test_end > end:
            break
        
        train_mask = (dates >= start) & (dates < train_end)
        test_mask = (dates >= train_end) & (dates < test_end)
        
        train_df = df[train_mask]
        test_df = df[test_mask]
        
        if len(train_df) < 100 or len(test_df) < 20:
            start += pd.DateOffset(months=step_months)
            continue
        
        folds.append({
            'fold': len(folds) + 1,
            'train_start': start.strftime('%Y-%m-%d'),
            'train_end': train_end.strftime('%Y-%m-%d'),
            'test_start': train_end.strftime('%Y-%m-%d'),
            'test_end': test_end.strftime('%Y-%m-%d'),
            'train_rows': len(train_df),
            'test_rows': len(test_df),
            'train_df': train_df,
            'test_df': test_df,
        })
        
        start += pd.DateOffset(months=step_months)
    
    return folds


# ============================================================================
# 2. SINGLE-FOLD TRAIN + BACKTEST
# ============================================================================

def train_and_backtest_fold(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    asset: str,
    feature_names: List[str] = None,
    capital: float = 1000,
) -> Dict[str, Any]:
    """
    Train XGBoost on train_df, generate signals on test_df, run backtest.
    
    Uses fixed hyperparameters (no Optuna) for speed.
    Returns dict with fold metrics.
    """
    import xgboost as xgb
    
    # Separate features and labels for training
    if 'target' in train_df.columns:
        X_train = train_df.drop(columns=['target'])
        y_train = train_df['target']
    else:
        # If no target column, generate labels
        from features.labels import generate_labels
        train_df = train_df.copy()
        train_df['target'] = generate_labels(train_df, asset=asset)
        X_train = train_df.drop(columns=['target'])
        y_train = train_df['target']
    
    # Drop non-numeric columns
    X_train = X_train.select_dtypes(include=[np.number])
    feature_names = list(X_train.columns)
    
    # Prepare test data
    X_test = test_df[feature_names] if feature_names else test_df.select_dtypes(include=[np.number])
    
    # Train XGBoost with fixed params
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.7,
        objective='binary:logistic',
        eval_metric='logloss',
        random_state=42,
        use_label_encoder=False,
    )
    
    model.fit(X_train, y_train, verbose=0)
    
    # Generate signals on test data
    try:
        proba = model.predict_proba(X_test)[:, 1]
    except Exception:
        proba = np.full(len(X_test), 0.5)
    
    # Apply trend filter if available
    if 'trend_ema_cross' in X_test.columns:
        signals = np.zeros(len(X_test), dtype=int)
        for i in range(len(X_test)):
            trend = X_test.iloc[i].get('trend_ema_cross', 0)
            confidence = max(proba[i], 1 - proba[i])
            if trend == 1 and proba[i] >= 0.5 and confidence >= 0.65:
                signals[i] = 1  # BUY
            elif trend == 0 and proba[i] < 0.5 and confidence >= 0.65:
                signals[i] = 1  # BUY (for backtest long-only)
            else:
                signals[i] = 0  # HOLD
    else:
        signals = (proba >= 0.65).astype(int)
    
    # Run backtest on test data
    engine = BacktestEngine(asset=asset, initial_capital=capital)
    results = engine.run_backtest(test_df, signals)
    metrics = results.get('metrics', {})
    
    # Add model metrics
    from sklearn.metrics import accuracy_score, roc_auc_score
    try:
        y_test = test_df['target'] if 'target' in test_df.columns else None
        if y_test is not None:
            pred = model.predict(X_test)
            metrics['model_accuracy'] = float(accuracy_score(y_test, pred))
            metrics['model_auc'] = float(roc_auc_score(y_test, proba)) if len(np.unique(y_test)) > 1 else 0.0
    except Exception:
        metrics['model_accuracy'] = 0.0
        metrics['model_auc'] = 0.0
    
    return metrics


# ============================================================================
# 3. SINGLE-SPLIT BASELINE
# ============================================================================

def run_single_split_baseline(df: pd.DataFrame, asset: str, capital: float = 1000) -> Dict[str, Any]:
    """Run the standard single-split backtest for comparison."""
    from data.loaders import train_val_test_split
    
    train_df, val_df, test_df = train_val_test_split(df, train_pct=0.70, val_pct=0.15, test_pct=0.15)
    
    return train_and_backtest_fold(train_df, test_df, asset, capital=capital)


# ============================================================================
# 4. AGGREGATE METRICS
# ============================================================================

METRIC_KEYS = [
    'win_rate', 'profit_factor', 'sharpe_ratio', 'sortino_ratio',
    'calmar_ratio', 'max_drawdown_pct', 'n_trades', 'total_return_pct',
    'model_accuracy', 'model_auc',
]

def aggregate_fold_metrics(folds: List[Dict]) -> Dict[str, Any]:
    """Compute mean and std of metrics across all folds."""
    agg = {}
    for key in METRIC_KEYS:
        values = [f.get(key, 0) for f in folds if key in f and np.isfinite(f.get(key, 0))]
        if values:
            agg[key] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'n': len(values),
            }
        else:
            agg[key] = {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'n': 0}
    return agg


# ============================================================================
# 5. REPORT GENERATOR
# ============================================================================

def generate_walk_forward_report(
    asset: str,
    folds: List[Dict],
    aggregated: Dict,
    single_split: Dict,
    capital: float = 1000,
) -> str:
    """Generate a markdown report comparing walk-forward vs single-split."""
    
    lines = []
    lines.append(f'# Walk-Forward Validation Report — {asset.upper()}')
    lines.append(f'')
    lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Folds:** {len(folds)}')
    lines.append(f'**Config:** Walk-forward validation')
    lines.append(f'**Capital:** ${capital:,.0f}')
    lines.append(f'')
    
    # Summary comparison
    lines.append('## Summary: Single-Split vs Walk-Forward')
    lines.append('')
    lines.append('| Metric | Single-Split | Walk-Forward (mean +/- std) | Difference |')
    lines.append('|--------|-------------|--------------------------|------------|')
    
    for key in ['win_rate', 'profit_factor', 'sharpe_ratio', 'max_drawdown_pct', 'total_return_pct', 'model_accuracy']:
        ss = single_split.get(key, 0)
        wf = aggregated.get(key, {})
        wf_mean = wf.get('mean', 0)
        wf_std = wf.get('std', 0)
        diff = wf_mean - ss
        diff_str = f'{diff:+.4f}' if abs(diff) < 1 else f'{diff:+.2f}'
        
        if key in ['win_rate', 'model_accuracy']:
            ss_str = f'{ss:.2%}'
            wf_str = f'{wf_mean:.2%} +/- {wf_std:.2%}'
        elif key == 'max_drawdown_pct':
            ss_str = f'{ss:.2f}%'
            wf_str = f'{wf_mean:.2f}% +/- {wf_std:.2f}%'
        elif key == 'total_return_pct':
            ss_dollar = capital * ss / 100
            wf_dollar = capital * wf_mean / 100
            ss_str = f'{ss:.1f}% (${ss_dollar:+,.0f})'
            wf_str = f'{wf_mean:.1f}% +/- {wf_std:.1f}% (${wf_dollar:+,.0f})'
            diff_str = f'${wf_dollar - ss_dollar:+,.0f}'
        else:
            ss_str = f'{ss:.4f}'
            wf_str = f'{wf_mean:.4f} +/- {wf_std:.4f}'
        
        lines.append(f'| {key} | {ss_str} | {wf_str} | {diff_str} |')
    
    lines.append('')
    
    # Per-fold breakdown
    lines.append('## Per-Fold Breakdown')
    lines.append('')
    lines.append('| Fold | Period | Train Rows | Test Rows | Win Rate | Sharpe | Trades | Final Equity |')
    lines.append('|------|--------|-----------|-----------|----------|--------|--------|--------------|')
    
    for f in folds:
        period = f'{f["test_start"]} -> {f["test_end"]}'
        wr = f.get('win_rate', 0)
        sr = f.get('sharpe_ratio', 0)
        nt = f.get('n_trades', 0)
        ret_pct = f.get('total_return_pct', 0)
        final_eq = capital * (1 + ret_pct / 100)
        lines.append(f'| {f["fold"]} | {period} | {f["train_rows"]} | {f["test_rows"]} | {wr:.2%} | {sr:.2f} | {nt} | ${final_eq:,.2f} |')
    
    lines.append('')
    
    # Stability analysis
    lines.append('## Stability Analysis')
    lines.append('')
    
    wr_values = [f.get('win_rate', 0) for f in folds if 'win_rate' in f]
    if wr_values:
        wr_std = np.std(wr_values)
        wr_range = max(wr_values) - min(wr_values)
        
        if wr_std < 0.05:
            stability = 'STABLE — win rate varies less than 5% across periods'
        elif wr_std < 0.10:
            stability = 'MODERATE — some variation across market regimes'
        else:
            stability = 'UNSTABLE — significant performance variation across periods'
        
        lines.append(f'**Win Rate Stability:** {stability}')
        lines.append(f'- Standard deviation: {wr_std:.2%}')
        lines.append(f'- Range: {min(wr_values):.2%} — {max(wr_values):.2%}')
        lines.append(f'- Coefficient of variation: {wr_std / np.mean(wr_values):.2%}' if np.mean(wr_values) > 0 else '')
    lines.append('')
    
    # Verdict
    lines.append('## Verdict')
    lines.append('')
    
    ss_wr = single_split.get('win_rate', 0)
    wf_wr = aggregated.get('win_rate', {}).get('mean', 0)
    
    if abs(ss_wr - wf_wr) < 0.03:
        lines.append('The single-split result is **representative** — walk-forward average is within 3% of the single-split number.')
        lines.append('This suggests the model is not significantly overfitting to one time period.')
    elif wf_wr > ss_wr:
        lines.append('The walk-forward average is **higher** than the single-split — the single-split may have been conservative.')
    else:
        lines.append('The walk-forward average is **lower** than the single-split — the single-split may have been optimistic.')
        lines.append(f'Difference: {ss_wr - wf_wr:.2%} — consider reporting the walk-forward average instead.')
    
    lines.append('')
    lines.append('---')
    lines.append(f'*This report was generated by `scripts/walk_forward_validation.py` — a standalone experimental tool.*')
    
    return '\n'.join(lines)


# ============================================================================
# 6. MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Walk-Forward Cross-Validation')
    parser.add_argument('--asset', choices=['gold', 'silver', 'both'], default='gold')
    parser.add_argument('--train-months', type=int, default=12)
    parser.add_argument('--test-months', type=int, default=3)
    parser.add_argument('--step-months', type=int, default=3)
    parser.add_argument('--capital', type=float, default=1000, help='Initial capital in USD')
    args = parser.parse_args()
    
    assets = ['gold', 'silver'] if args.asset == 'both' else [args.asset]
    
    for asset in assets:
        logger.info(f'{"=" * 60}')
        logger.info(f'WALK-FORWARD VALIDATION: {asset.upper()}')
        logger.info(f'{"=" * 60}')
        
        # Load data
        logger.info(f'Loading {asset} data...')
        df = load_asset_data(asset=asset, primary_tf='15m', session_filter=False)
        logger.info(f'Loaded {len(df)} rows from {df.index.min()} to {df.index.max()}')
        
        # Engineer features once on full dataset
        logger.info('Engineering features...')
        df = engineer_all_features(df, add_labels=True, asset=asset)
        logger.info(f'Features engineered: {len(df.columns)} columns')
        
        # Generate walk-forward folds
        logger.info(f'Generating folds ({args.train_months}mo train, {args.test_months}mo test, {args.step_months}mo step)...')
        folds = generate_walk_forward_folds(
            df,
            train_months=args.train_months,
            test_months=args.test_months,
            step_months=args.step_months,
        )
        logger.info(f'Generated {len(folds)} folds')
        
        if len(folds) < 2:
            logger.warning(f'Not enough folds ({len(folds)}) for meaningful analysis. Need at least 2.')
            continue
        
        # Run each fold
        fold_results = []
        for fold_info in folds:
            logger.info(f'Fold {fold_info["fold"]}/{len(folds)}: train {fold_info["train_start"]}→{fold_info["train_end"]}, test {fold_info["test_start"]}→{fold_info["test_end"]}')
            
            metrics = train_and_backtest_fold(
                fold_info['train_df'],
                fold_info['test_df'],
                asset=asset,
                capital=args.capital,
            )
            
            # Merge fold metadata with metrics
            result = {**fold_info, **metrics}
            # Remove dataframe references before storing
            result.pop('train_df', None)
            result.pop('test_df', None)
            fold_results.append(result)
            
            wr = metrics.get('win_rate', 0)
            nt = metrics.get('n_trades', 0)
            logger.info(f'  → Win rate: {wr:.2%}, Trades: {nt}')
        
        # Aggregate metrics
        aggregated = aggregate_fold_metrics(fold_results)
        
        # Run single-split baseline
        logger.info('Running single-split baseline for comparison...')
        single_split = run_single_split_baseline(df, asset, capital=args.capital)
        
        # Generate report
        report = generate_walk_forward_report(asset, fold_results, aggregated, single_split, capital=args.capital)
        
        # Save report
        report_dir = REPORTS_DIR
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f'walk_forward_{asset}.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f'Report saved: {report_path}')
        
        # Also save raw data as JSON
        json_path = report_dir / f'walk_forward_{asset}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'asset': asset,
                'config': {
                    'train_months': args.train_months,
                    'test_months': args.test_months,
                    'step_months': args.step_months,
                },
                'n_folds': len(folds),
                'folds': fold_results,
                'aggregated': aggregated,
                'single_split': single_split,
            }, f, indent=2, default=str)
        logger.info(f'JSON data saved: {json_path}')
        
        # Print summary
        logger.info(f'\n{"=" * 60}')
        logger.info(f'RESULTS: {asset.upper()}')
        logger.info(f'{"=" * 60}')
        for key in ['win_rate', 'sharpe_ratio', 'model_accuracy']:
            ss = single_split.get(key, 0)
            wf = aggregated.get(key, {})
            if key in ['win_rate', 'model_accuracy']:
                logger.info(f'  {key}: single={ss:.2%}, walk-forward={wf.get("mean", 0):.2%} ± {wf.get("std", 0):.2%}')
            else:
                logger.info(f'  {key}: single={ss:.4f}, walk-forward={wf.get("mean", 0):.4f} ± {wf.get("std", 0):.4f}')


if __name__ == '__main__':
    main()
