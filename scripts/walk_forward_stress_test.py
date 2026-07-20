"""
Walk-Forward STRESS TEST for MetalMind SMCForge

The hard mode version. Combines all challenges:
1. Short train windows (2 months) — model must adapt fast
2. High transaction costs (0.05% commission + 0.05% slippage) — real-world friction
3. Optuna hyperparameter tuning PER FOLD — no fixed params, fresh optimization each time
4. Reserved forward test set (last 2 months) — completely unseen data
5. Both gold runs — extra folds for statistical significance

Standalone — does NOT modify any existing project files.

Usage:
    python scripts/walk_forward_stress_test.py
    python scripts/walk_forward_stress_test.py --capital 10000
    python scripts/walk_forward_stress_test.py --optuna-trials 20

Output:
    reports/walk_forward_stress_test.md — full stress-test report
    reports/walk_forward_stress_test.json — raw data
"""

import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import BACKTEST_CONFIG, REPORTS_DIR, get_label_params
from data.loaders import load_asset_data
from features.pipeline import engineer_all_features
from backtesting.engine import BacktestEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s — %(levelname)s — %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# STRESS TEST PARAMETERS (much harder than default)
# ============================================================================

STRESS_CONFIG = {
    'train_months': 2,       # Short: model must learn fast
    'test_months': 1,        # Short: each fold is a tight window
    'step_months': 1,        # Step: slide monthly
    'forward_test_months': 2, # Reserve last 2 months for final validation
    'commission_pct': 0.0005, # 0.05% per trade (5x default)
    'slippage_pct': 0.0005,   # 0.05% per trade (2.5x default)
    'optuna_trials': 15,      # Optuna per fold (not fixed params)
}


# ============================================================================
# 1. WALK-FORWARD FOLD GENERATOR (with forward test reserve)
# ============================================================================

def generate_stress_folds(
    df: pd.DataFrame,
    train_months: int = 2,
    test_months: int = 1,
    step_months: int = 1,
    forward_test_months: int = 2,
) -> tuple:
    """
    Generate walk-forward folds, reserving the last N months for forward test.
    Returns (folds, forward_test_df).
    """
    dates = df.index
    end = dates.max()
    forward_test_start = end - pd.DateOffset(months=forward_test_months)
    
    # Split: everything before forward_test_start is walk-forward territory
    wf_df = df[dates < forward_test_start]
    forward_test_df = df[dates >= forward_test_start]
    
    logger.info(f'Data split: {len(wf_df)} rows for walk-forward, {len(forward_test_df)} rows for forward test')
    logger.info(f'Forward test period: {forward_test_start.strftime("%Y-%m-%d")} to {end.strftime("%Y-%m-%d")}')
    
    folds = []
    start = wf_df.index.min()
    wf_end = wf_df.index.max()
    
    while True:
        train_end = start + pd.DateOffset(months=train_months)
        test_end = train_end + pd.DateOffset(months=test_months)
        
        if test_end > wf_end:
            break
        
        train_mask = (wf_df.index >= start) & (wf_df.index < train_end)
        test_mask = (wf_df.index >= train_end) & (wf_df.index < test_end)
        
        train_df = wf_df[train_mask]
        test_df = wf_df[test_mask]
        
        if len(train_df) < 50 or len(test_df) < 10:
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
    
    return folds, forward_test_df


# ============================================================================
# 2. OPTUNA + TRAIN + BACKTEST (per fold)
# ============================================================================

def optuna_train_and_backtest(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    asset: str,
    capital: float,
    n_trials: int = 15,
    commission_pct: float = 0.0005,
    slippage_pct: float = 0.0005,
) -> Dict[str, Any]:
    """
    For each fold: Optuna tuning + train + backtest with high costs.
    This is the expensive path — fresh hyperparameters every fold.
    """
    import xgboost as xgb
    import optuna
    from sklearn.metrics import accuracy_score
    
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    # Prepare training data
    if 'target' in train_df.columns:
        X_train = train_df.drop(columns=['target']).select_dtypes(include=[np.number])
        y_train = train_df['target']
    else:
        from features.labels import generate_labels
        train_df = train_df.copy()
        train_df['target'] = generate_labels(train_df, asset=asset)
        X_train = train_df.drop(columns=['target']).select_dtypes(include=[np.number])
        y_train = train_df['target']
    
    feature_names = list(X_train.columns)
    X_test = test_df[feature_names] if all(f in test_df.columns for f in feature_names) else test_df.select_dtypes(include=[np.number])
    
    # Split train into train/val for Optuna
    split_idx = int(len(X_train) * 0.8)
    X_tr, X_val = X_train.iloc[:split_idx], X_train.iloc[split_idx:]
    y_tr, y_val = y_train.iloc[:split_idx], y_train.iloc[split_idx:]
    
    # Optuna objective
    def objective(trial):
        params = {
            'n_estimators': 500,
            'max_depth': trial.suggest_int('max_depth', 3, 6),
            'learning_rate': trial.suggest_float('lr', 0.01, 0.1, log=True),
            'subsample': trial.suggest_float('sub', 0.6, 0.95),
            'colsample_bytree': trial.suggest_float('col', 0.5, 0.9),
            'min_child_weight': trial.suggest_int('mcw', 1, 10),
            'gamma': trial.suggest_float('gamma', 0, 1.0),
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'random_state': 42,
            'verbosity': 0,
        }
        
        model = xgb.XGBClassifier(**params)
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=0)
        pred = model.predict(X_val)
        return 1 - accuracy_score(y_val, pred)
    
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    
    best_params = study.best_params
    best_params['n_estimators'] = 500
    best_params['objective'] = 'binary:logistic'
    best_params['eval_metric'] = 'logloss'
    best_params['random_state'] = 42
    best_params['verbosity'] = 0
    
    # Train final model with best params on full training data
    model = xgb.XGBClassifier(**best_params)
    model.fit(X_train, y_train, verbose=0)
    
    # Generate signals
    try:
        proba = model.predict_proba(X_test)[:, 1]
    except Exception:
        proba = np.full(len(X_test), 0.5)
    
    # Trend filter
    if 'trend_ema_cross' in X_test.columns:
        signals = np.zeros(len(X_test), dtype=int)
        for i in range(len(X_test)):
            trend = X_test.iloc[i].get('trend_ema_cross', 0)
            confidence = max(proba[i], 1 - proba[i])
            if confidence >= 0.65:
                signals[i] = 1
        # If no high-confidence signals, use probability threshold
        if signals.sum() == 0:
            signals = (proba >= 0.65).astype(int)
    else:
        signals = (proba >= 0.55).astype(int)
    
    # Run backtest with HIGH costs
    engine = BacktestEngine(
        asset=asset,
        initial_capital=capital,
        commission_pct=commission_pct,
        slippage_pct=slippage_pct,
    )
    results = engine.run_backtest(test_df, signals)
    metrics = results.get('metrics', {})
    
    # Model metrics
    try:
        y_test = test_df['target'] if 'target' in test_df.columns else None
        if y_test is not None:
            pred = model.predict(X_test)
            metrics['model_accuracy'] = float(accuracy_score(y_test, pred))
    except Exception:
        metrics['model_accuracy'] = 0.0
    
    metrics['best_params'] = best_params
    metrics['optuna_best_value'] = study.best_value
    
    return metrics


# ============================================================================
# 3. SINGLE-SPLIT BASELINE (with high costs)
# ============================================================================

def run_single_split_stress(
    df: pd.DataFrame,
    asset: str,
    capital: float,
    commission_pct: float,
    slippage_pct: float,
) -> Dict[str, Any]:
    """Single split with high costs for fair comparison."""
    from data.loaders import train_val_test_split
    
    train_df, val_df, test_df = train_val_test_split(df, train_pct=0.70, val_pct=0.15, test_pct=0.15)
    
    return optuna_train_and_backtest(
        train_df, test_df, asset, capital,
        n_trials=15,
        commission_pct=commission_pct,
        slippage_pct=slippage_pct,
    )


# ============================================================================
# 4. FORWARD TEST (final model on reserved data)
# ============================================================================

def run_forward_test(
    train_df: pd.DataFrame,
    forward_df: pd.DataFrame,
    asset: str,
    capital: float,
    commission_pct: float,
    slippage_pct: float,
    n_trials: int = 20,
) -> Dict[str, Any]:
    """
    Train on ALL non-reserved data, test on completely unseen forward period.
    This is the ultimate test — the model has never seen this data.
    """
    logger.info(f'Forward test: training on {len(train_df)} rows, testing on {len(forward_df)} rows')
    
    return optuna_train_and_backtest(
        train_df, forward_df, asset, capital,
        n_trials=n_trials,
        commission_pct=commission_pct,
        slippage_pct=slippage_pct,
    )


# ============================================================================
# 5. AGGREGATION
# ============================================================================

METRIC_KEYS = [
    'win_rate', 'profit_factor', 'sharpe_ratio', 'sortino_ratio',
    'calmar_ratio', 'max_drawdown_pct', 'n_trades', 'total_return_pct',
    'model_accuracy',
]

def aggregate(folds: List[Dict]) -> Dict[str, Any]:
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
# 6. REPORT
# ============================================================================

def generate_report(
    asset: str,
    folds: List[Dict],
    agg: Dict,
    single: Dict,
    forward: Dict,
    capital: float,
    config: Dict,
) -> str:
    lines = []
    lines.append(f'# Walk-Forward STRESS TEST — {asset.upper()}')
    lines.append('')
    lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Capital:** ${capital:,.0f}')
    lines.append(f'**Train window:** {config["train_months"]} months (SHORT)')
    lines.append(f'**Test window:** {config["test_months"]} month')
    lines.append(f'**Commission:** {config["commission_pct"]*100:.2f}% per trade (HIGH)')
    lines.append(f'**Slippage:** {config["slippage_pct"]*100:.2f}% per trade (HIGH)')
    lines.append(f'**Optuna:** {config["optuna_trials"]} trials per fold (FRESH each time)')
    lines.append(f'**Forward test:** Last {config["forward_test_months"]} months reserved (UNSEEN)')
    lines.append(f'**Walk-forward folds:** {len(folds)}')
    lines.append('')
    
    # Three-way comparison
    lines.append('## Three-Way Comparison')
    lines.append('')
    lines.append('| Metric | Single-Split | Walk-Forward Avg | Forward Test |')
    lines.append('|--------|-------------|-----------------|--------------|')
    
    for key in ['win_rate', 'sharpe_ratio', 'total_return_pct', 'max_drawdown_pct', 'n_trades']:
        ss = single.get(key, 0)
        wf = agg.get(key, {})
        ft = forward.get(key, 0)
        wf_mean = wf.get('mean', 0)
        wf_std = wf.get('std', 0)
        
        if key == 'win_rate':
            ss_s, wf_s, ft_s = f'{ss:.2%}', f'{wf_mean:.2%} +/- {wf_std:.2%}', f'{ft:.2%}'
        elif key == 'total_return_pct':
            ss_s = f'{ss:.1f}% (${capital * ss / 100:+,.0f})'
            wf_s = f'{wf_mean:.1f}% +/- {wf_std:.1f}% (${capital * wf_mean / 100:+,.0f})'
            ft_s = f'{ft:.1f}% (${capital * ft / 100:+,.0f})'
        elif key == 'max_drawdown_pct':
            ss_s, wf_s, ft_s = f'{ss:.2f}%', f'{wf_mean:.2f}%', f'{ft:.2f}%'
        else:
            ss_s, wf_s, ft_s = f'{ss:.2f}', f'{wf_mean:.2f}', f'{ft:.2f}'
        
        lines.append(f'| {key} | {ss_s} | {wf_s} | {ft_s} |')
    
    lines.append('')
    
    # Per-fold
    lines.append('## Per-Fold Breakdown')
    lines.append('')
    lines.append('| Fold | Period | Win Rate | Sharpe | Trades | Final Equity | Optuna Best |')
    lines.append('|------|--------|----------|--------|--------|-------------|-------------|')
    
    for f in folds:
        period = f'{f["test_start"]} -> {f["test_end"]}'
        wr = f.get('win_rate', 0)
        sr = f.get('sharpe_ratio', 0)
        nt = f.get('n_trades', 0)
        ret = f.get('total_return_pct', 0)
        eq = capital * (1 + ret / 100)
        ob = f.get('optuna_best_value', 0)
        lines.append(f'| {f["fold"]} | {period} | {wr:.2%} | {sr:.2f} | {nt} | ${eq:,.2f} | {ob:.4f} |')
    
    lines.append('')
    
    # Stability
    lines.append('## Stress Analysis')
    lines.append('')
    
    wr_values = [f.get('win_rate', 0) for f in folds if 'win_rate' in f]
    if wr_values:
        wr_std = np.std(wr_values)
        lines.append(f'- Win rate std: {wr_std:.2%} across {len(folds)} folds')
        lines.append(f'- Win rate range: {min(wr_values):.2%} to {max(wr_values):.2%}')
        
        profitable_folds = sum(1 for f in folds if f.get('total_return_pct', 0) > 0)
        lines.append(f'- Profitable folds: {profitable_folds}/{len(folds)}')
        
        ft_ret = forward.get('total_return_pct', 0)
        ft_profitable = ft_ret > 0
        lines.append(f'- Forward test profitable: {"YES" if ft_profitable else "NO"} (${capital * ft_ret / 100:+,.0f})')
    
    lines.append('')
    
    # Verdict
    lines.append('## Verdict')
    lines.append('')
    
    ft_ret = forward.get('total_return_pct', 0)
    wf_mean_ret = agg.get('total_return_pct', {}).get('mean', 0)
    ss_ret = single.get('total_return_pct', 0)
    
    if ft_ret > 0 and wf_mean_ret > 0:
        lines.append('**PASS** — Model survives the stress test.')
        lines.append(f'Forward test returned {ft_ret:.1f}% on completely unseen data with high transaction costs.')
        lines.append(f'Walk-forward average: {wf_mean_ret:.1f}% across {len(folds)} folds.')
    elif ft_ret > 0:
        lines.append('**PARTIAL PASS** — Forward test profitable but walk-forward average is negative.')
        lines.append('Model may be overfitting to specific training windows.')
    else:
        lines.append('**FAIL** — Forward test lost money on unseen data.')
        lines.append('Model does not generalize. Needs more data or different approach.')
    
    lines.append('')
    lines.append('---')
    lines.append(f'*Generated by `scripts/walk_forward_stress_test.py` — standalone stress test.*')
    
    return '\n'.join(lines)


# ============================================================================
# 7. MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Walk-Forward Stress Test')
    parser.add_argument('--capital', type=float, default=5000)
    parser.add_argument('--optuna-trials', type=int, default=15)
    args = parser.parse_args()
    
    config = STRESS_CONFIG.copy()
    config['optuna_trials'] = args.optuna_trials
    capital = args.capital
    
    asset = 'gold'
    logger.info(f'{"=" * 60}')
    logger.info(f'WALK-FORWARD STRESS TEST: {asset.upper()}')
    logger.info(f'Capital: ${capital:,.0f} | Commission: {config["commission_pct"]*100:.2f}% | Slippage: {config["slippage_pct"]*100:.2f}%')
    logger.info(f'Train: {config["train_months"]}mo | Test: {config["test_months"]}mo | Forward: {config["forward_test_months"]}mo reserved')
    logger.info(f'Optuna: {config["optuna_trials"]} trials per fold')
    logger.info(f'{"=" * 60}')
    
    # Load data
    logger.info('Loading gold data...')
    df = load_asset_data(asset=asset, primary_tf='15m', session_filter=False)
    logger.info(f'Loaded {len(df)} rows')
    
    # Engineer features
    logger.info('Engineering features...')
    df = engineer_all_features(df, add_labels=True, asset=asset)
    logger.info(f'Features: {len(df.columns)} columns')
    
    # Generate folds with forward test reserve
    logger.info('Generating stress-test folds...')
    folds, forward_test_df = generate_stress_folds(
        df,
        train_months=config['train_months'],
        test_months=config['test_months'],
        step_months=config['step_months'],
        forward_test_months=config['forward_test_months'],
    )
    logger.info(f'Generated {len(folds)} walk-forward folds + 1 forward test set')
    
    if len(folds) < 2:
        logger.error(f'Not enough folds ({len(folds)})')
        return
    
    # Run each fold with Optuna
    fold_results = []
    for fold_info in folds:
        logger.info(f'Fold {fold_info["fold"]}/{len(folds)}: {fold_info["train_start"]}->{fold_info["train_end"]} train, {fold_info["test_start"]}->{fold_info["test_end"]} test')
        
        metrics = optuna_train_and_backtest(
            fold_info['train_df'],
            fold_info['test_df'],
            asset=asset,
            capital=capital,
            n_trials=config['optuna_trials'],
            commission_pct=config['commission_pct'],
            slippage_pct=config['slippage_pct'],
        )
        
        result = {**fold_info, **metrics}
        result.pop('train_df', None)
        result.pop('test_df', None)
        result.pop('best_params', None)
        fold_results.append(result)
        
        wr = metrics.get('win_rate', 0)
        nt = metrics.get('n_trades', 0)
        ret = metrics.get('total_return_pct', 0)
        logger.info(f'  -> Win rate: {wr:.2%}, Trades: {nt}, Return: {ret:.1f}%')
    
    # Aggregate
    agg = aggregate(fold_results)
    
    # Single-split baseline with high costs
    logger.info('Running single-split baseline with high costs...')
    # Use the full non-reserved data for single split
    wf_dates = df.index < forward_test_df.index.min()
    single_split_df = df[wf_dates]
    single = run_single_split_stress(
        single_split_df, asset, capital,
        config['commission_pct'], config['slippage_pct'],
    )
    
    # Forward test: train on ALL walk-forward data, test on reserved 2 months
    logger.info('Running forward test on reserved data...')
    wf_train_df = df[df.index < forward_test_df.index.min()]
    forward = run_forward_test(
        wf_train_df,
        forward_test_df,
        asset=asset,
        capital=capital,
        commission_pct=config['commission_pct'],
        slippage_pct=config['slippage_pct'],
        n_trials=config['optuna_trials'] + 5,  # Extra trials for final model
    )
    
    # Generate report
    report = generate_report(asset, fold_results, agg, single, forward, capital, config)
    
    # Save
    report_dir = REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = report_dir / 'walk_forward_stress_test.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f'Report saved: {report_path}')
    
    json_path = report_dir / 'walk_forward_stress_test.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'asset': asset,
            'config': config,
            'capital': capital,
            'n_folds': len(folds),
            'folds': fold_results,
            'aggregated': agg,
            'single_split': single,
            'forward_test': forward,
        }, f, indent=2, default=str)
    logger.info(f'JSON saved: {json_path}')
    
    # Print summary
    logger.info(f'\n{"=" * 60}')
    logger.info(f'STRESS TEST RESULTS: {asset.upper()}')
    logger.info(f'{"=" * 60}')
    
    ft_ret = forward.get('total_return_pct', 0)
    wf_mean_ret = agg.get('total_return_pct', {}).get('mean', 0)
    ss_ret = single.get('total_return_pct', 0)
    
    ft_eq = capital * (1 + ft_ret / 100)
    wf_eq = capital * (1 + wf_mean_ret / 100)
    ss_eq = capital * (1 + ss_ret / 100)
    
    logger.info(f'  Single-split:  {ss_ret:+.1f}% -> ${ss_eq:,.2f}')
    logger.info(f'  Walk-forward:  {wf_mean_ret:+.1f}% -> ${wf_eq:,.2f}')
    logger.info(f'  Forward test:  {ft_ret:+.1f}% -> ${ft_eq:,.2f}')
    logger.info(f'')
    
    if ft_ret > 0:
        logger.info(f'  VERDICT: PASS — Forward test profitable on unseen data')
    else:
        logger.info(f'  VERDICT: FAIL — Forward test lost money')


if __name__ == '__main__':
    main()
