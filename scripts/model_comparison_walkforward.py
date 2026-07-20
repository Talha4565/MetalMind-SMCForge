"""
V4 vs V5 Model Comparison — Walk-Forward Cross-Validation

4 tests x 2 evaluation methods = 8 scenarios total:
- V4 + simple (low costs, 4mo train, fixed params)
- V4 + stress (high costs, 2mo train, Optuna per fold)
- V5 + simple (low costs, 4mo train, fixed params)
- V5 + stress (high costs, 2mo train, Optuna per fold)

Each test runs: single-split baseline + walk-forward + forward test.
Uses the SAME 89 features that V4/V5 were originally trained on.

Standalone — copies models, does NOT touch originals.

Usage:
    python scripts/model_comparison_walkforward.py
    python scripts/model_comparison_walkforward.py --capital 10000
"""

import sys
import pickle
import json
import logging
import argparse
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import BACKTEST_CONFIG, MODELS_DIR, REPORTS_DIR, get_label_params
from data.loaders import load_asset_data
from features.pipeline import engineer_all_features
from features.v4_features import compute_v4_features
from backtesting.engine import BacktestEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s — %(levelname)s — %(message)s')
logger = logging.getLogger(__name__)

COPY_DIR = project_root / 'models' / '_comparison_copies'


# ============================================================================
# 1. MODEL COPYING
# ============================================================================

def copy_models():
    """Copy V4 and V5 to safe locations. Skip if already exist."""
    COPY_DIR.mkdir(parents=True, exist_ok=True)
    
    copies = {
        'v4': MODELS_DIR / 'gold_regression_system.pkl',
        'v5': MODELS_DIR / 'gold_v5.pkl',
    }
    
    for name, src in copies.items():
        dst = COPY_DIR / f'gold_{name}_copy.pkl'
        if not dst.exists():
            shutil.copy2(src, dst)
            logger.info(f'Copied {src.name} -> {dst.name}')
        else:
            logger.info(f'{dst.name} already exists, skipping')
    
    return {name: COPY_DIR / f'gold_{name}_copy.pkl' for name in copies}


def load_model_copy(path: Path) -> Dict:
    """Load a model copy and extract feature list + model type."""
    with open(path, 'rb') as f:
        data = pickle.load(f)
    
    return {
        'features': data['features'],
        'direction_model': data['direction_model'],
        'n_features': len(data['features']),
    }


# ============================================================================
# 2. WALK-FORWARD FOLD GENERATOR
# ============================================================================

def generate_folds(
    df: pd.DataFrame,
    train_months: int,
    test_months: int,
    step_months: int,
    forward_test_months: int = 0,
) -> Tuple[List[Dict], pd.DataFrame]:
    """Generate folds, optionally reserving last N months for forward test."""
    dates = df.index
    end = dates.max()
    
    if forward_test_months > 0:
        ft_start = end - pd.DateOffset(months=forward_test_months)
        wf_df = df[dates < ft_start]
        forward_df = df[dates >= ft_start]
    else:
        wf_df = df
        forward_df = pd.DataFrame()
    
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
    
    return folds, forward_df


# ============================================================================
# 3. TRAIN + BACKTEST (the core engine)
# ============================================================================

def train_and_backtest(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_names: List[str],
    asset: str,
    capital: float,
    commission_pct: float,
    slippage_pct: float,
    use_optuna: bool = False,
    n_trials: int = 15,
) -> Dict[str, Any]:
    """Train XGBoost from scratch on train_df, test on test_df."""
    import xgboost as xgb
    
    # Prepare training data — use ONLY the 89 features from V4/V5
    if 'target' in train_df.columns:
        X_train = train_df[feature_names]
        y_train = train_df['target']
    else:
        from features.labels import generate_labels
        train_df = train_df.copy()
        train_df['target'] = generate_labels(train_df, asset=asset)
        X_train = train_df[feature_names]
        y_train = train_df['target']
    
    # Drop rows with NaN in features
    valid_mask = X_train.notna().all(axis=1) & y_train.notna()
    X_train = X_train[valid_mask]
    y_train = y_train[valid_mask]
    
    X_test = test_df[feature_names]
    valid_test = X_test.notna().all(axis=1)
    X_test_clean = X_test[valid_test]
    
    if len(X_train) < 50 or len(X_test_clean) < 10:
        return {'win_rate': 0, 'n_trades': 0, 'total_return_pct': 0, 'sharpe_ratio': 0,
                'max_drawdown_pct': 0, 'profit_factor': 0, 'model_accuracy': 0}
    
    if use_optuna:
        import optuna
        from sklearn.metrics import accuracy_score
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        
        split_idx = int(len(X_train) * 0.8)
        X_tr, X_val = X_train.iloc[:split_idx], X_train.iloc[split_idx:]
        y_tr, y_val = y_train.iloc[:split_idx], y_train.iloc[split_idx:]
        
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
        
        best = study.best_params
        best['n_estimators'] = 500
        best['objective'] = 'binary:logistic'
        best['eval_metric'] = 'logloss'
        best['random_state'] = 42
        best['verbosity'] = 0
        
        model = xgb.XGBClassifier(**best)
    else:
        # Fixed params (simple mode)
        model = xgb.XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.7,
            objective='binary:logistic', eval_metric='logloss',
            random_state=42, verbosity=0,
        )
    
    model.fit(X_train, y_train, verbose=0)
    
    # Generate signals
    try:
        proba = model.predict_proba(X_test_clean)[:, 1]
    except Exception:
        proba = np.full(len(X_test_clean), 0.5)
    
    signals = (proba >= 0.65).astype(int)
    
    # Run backtest
    engine = BacktestEngine(asset=asset, initial_capital=capital,
                            commission_pct=commission_pct, slippage_pct=slippage_pct)
    results = engine.run_backtest(test_df.loc[X_test_clean.index], signals)
    metrics = results.get('metrics', {})
    
    # Model accuracy
    try:
        y_test = test_df.loc[X_test_clean.index, 'target'] if 'target' in test_df.columns else None
        if y_test is not None:
            from sklearn.metrics import accuracy_score
            pred = model.predict(X_test_clean)
            metrics['model_accuracy'] = float(accuracy_score(y_test, pred))
    except Exception:
        metrics['model_accuracy'] = 0.0
    
    return metrics


# ============================================================================
# 4. SCENARIO RUNNER
# ============================================================================

def run_scenario(
    model_name: str,
    model_data: Dict,
    df: pd.DataFrame,
    capital: float,
    train_months: int,
    test_months: int,
    step_months: int,
    commission_pct: float,
    slippage_pct: float,
    use_optuna: bool,
    n_trials: int,
    forward_test_months: int,
) -> Dict[str, Any]:
    """Run one complete scenario: folds + single-split + forward test."""
    feature_names = model_data['features']
    asset = 'gold'
    
    # Generate folds
    folds, forward_df = generate_folds(df, train_months, test_months, step_months, forward_test_months)
    
    if len(folds) < 2:
        logger.warning(f'Not enough folds ({len(folds)})')
        return {'folds': [], 'single_split': {}, 'forward_test': {}, 'aggregated': {}}
    
    # Run each fold
    fold_results = []
    for fold_info in folds:
        metrics = train_and_backtest(
            fold_info['train_df'], fold_info['test_df'],
            feature_names, asset, capital,
            commission_pct, slippage_pct,
            use_optuna=use_optuna, n_trials=n_trials,
        )
        result = {**fold_info, **metrics}
        result.pop('train_df', None)
        result.pop('test_df', None)
        fold_results.append(result)
    
    # Aggregate
    agg = aggregate_metrics(fold_results)
    
    # Single-split baseline
    from data.loaders import train_val_test_split
    train_df, val_df, test_df = train_val_test_split(df, 0.70, 0.15, 0.15)
    single = train_and_backtest(
        train_df, test_df, feature_names, asset, capital,
        commission_pct, slippage_pct,
        use_optuna=use_optuna, n_trials=n_trials,
    )
    
    # Forward test
    forward_result = {}
    if len(forward_df) > 0:
        wf_train = df[df.index < forward_df.index.min()]
        forward_result = train_and_backtest(
            wf_train, forward_df, feature_names, asset, capital,
            commission_pct, slippage_pct,
            use_optuna=use_optuna, n_trials=n_trials + 5,
        )
    
    return {
        'folds': fold_results,
        'single_split': single,
        'forward_test': forward_result,
        'aggregated': agg,
    }


# ============================================================================
# 5. AGGREGATION
# ============================================================================

METRIC_KEYS = ['win_rate', 'profit_factor', 'sharpe_ratio', 'max_drawdown_pct', 'total_return_pct', 'model_accuracy']

def aggregate_metrics(folds: List[Dict]) -> Dict:
    agg = {}
    for key in METRIC_KEYS:
        values = [f.get(key, 0) for f in folds if key in f and np.isfinite(f.get(key, 0))]
        if values:
            agg[key] = {'mean': float(np.mean(values)), 'std': float(np.std(values))}
        else:
            agg[key] = {'mean': 0, 'std': 0}
    return agg


# ============================================================================
# 6. REPORT
# ============================================================================

def generate_report(results: Dict[str, Dict], capital: float) -> str:
    lines = []
    lines.append('# V4 vs V5 Model Comparison — Walk-Forward Analysis')
    lines.append('')
    lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Capital:** ${capital:,.0f}')
    lines.append(f'**Asset:** Gold (XAU/USD)')
    lines.append(f'**Features:** 89 (same for both V4 and V5)')
    lines.append('')
    
    # Summary table
    lines.append('## Summary: All 8 Scenarios')
    lines.append('')
    lines.append('| Scenario | Eval Method | Win Rate | Return | Sharpe | Max DD | Trades |')
    lines.append('|----------|------------|----------|--------|--------|--------|--------|')
    
    for scenario_name, data in results.items():
        agg = data.get('aggregated', {})
        single = data.get('single_split', {})
        forward = data.get('forward_test', {})
        
        # Single split
        ss_wr = single.get('win_rate', 0)
        ss_ret = single.get('total_return_pct', 0)
        ss_sh = single.get('sharpe_ratio', 0)
        ss_dd = single.get('max_drawdown_pct', 0)
        ss_nt = single.get('n_trades', 0)
        lines.append(f'| {scenario_name} | Single-Split | {ss_wr:.1%} | {ss_ret:+.1f}% (${capital*ss_ret/100:+,.0f}) | {ss_sh:.2f} | {ss_dd:.1f}% | {ss_nt} |')
        
        # Walk-forward
        wf_wr = agg.get('win_rate', {}).get('mean', 0)
        wf_ret = agg.get('total_return_pct', {}).get('mean', 0)
        wf_sh = agg.get('sharpe_ratio', {}).get('mean', 0)
        wf_dd = agg.get('max_drawdown_pct', {}).get('mean', 0)
        wf_nt = np.mean([f.get('n_trades', 0) for f in data.get('folds', [])]) if data.get('folds') else 0
        lines.append(f'| {scenario_name} | Walk-Forward | {wf_wr:.1%} | {wf_ret:+.1f}% (${capital*wf_ret/100:+,.0f}) | {wf_sh:.2f} | {wf_dd:.1f}% | {wf_nt:.0f} |')
        
        # Forward test
        if forward:
            ft_wr = forward.get('win_rate', 0)
            ft_ret = forward.get('total_return_pct', 0)
            ft_sh = forward.get('sharpe_ratio', 0)
            ft_dd = forward.get('max_drawdown_pct', 0)
            ft_nt = forward.get('n_trades', 0)
            lines.append(f'| {scenario_name} | Forward Test | {ft_wr:.1%} | {ft_ret:+.1f}% (${capital*ft_ret/100:+,.0f}) | {ft_sh:.2f} | {ft_dd:.1f}% | {ft_nt} |')
    
    lines.append('')
    
    # Per-scenario detail
    for scenario_name, data in results.items():
        lines.append(f'## {scenario_name} — Per-Fold Detail')
        lines.append('')
        lines.append('| Fold | Period | Win Rate | Return | Trades | Equity |')
        lines.append('|------|--------|----------|--------|--------|--------|')
        
        for f in data.get('folds', []):
            period = f'{f["test_start"]} -> {f["test_end"]}'
            wr = f.get('win_rate', 0)
            ret = f.get('total_return_pct', 0)
            nt = f.get('n_trades', 0)
            eq = capital * (1 + ret / 100)
            lines.append(f'| {f["fold"]} | {period} | {wr:.1%} | {ret:+.1f}% | {nt} | ${eq:,.0f} |')
        lines.append('')
    
    # V4 vs V5 comparison
    lines.append('## V4 vs V5 Head-to-Head')
    lines.append('')
    
    for eval_method, key in [('Single-Split', 'single_split'), ('Walk-Forward', 'aggregated'), ('Forward Test', 'forward_test')]:
        v4_data = results.get('V4-Simple', {}).get(key, {})
        v5_data = results.get('V5-Simple', {}).get(key, {})
        
        if key == 'aggregated':
            v4_wr = v4_data.get('win_rate', {}).get('mean', 0)
            v5_wr = v5_data.get('win_rate', {}).get('mean', 0)
            v4_ret = v4_data.get('total_return_pct', {}).get('mean', 0)
            v5_ret = v5_data.get('total_return_pct', {}).get('mean', 0)
        else:
            v4_wr = v4_data.get('win_rate', 0)
            v5_wr = v5_data.get('win_rate', 0)
            v4_ret = v4_data.get('total_return_pct', 0)
            v5_ret = v5_data.get('total_return_pct', 0)
        
        winner = 'V5' if v5_wr > v4_wr else 'V4' if v4_wr > v5_wr else 'TIE'
        lines.append(f'**{eval_method}:** V4={v4_wr:.1%} ({v4_ret:+.1f}%) vs V5={v5_wr:.1%} ({v5_ret:+.1f}%) — Winner: {winner}')
    
    lines.append('')
    
    # Verdict
    lines.append('## Verdict')
    lines.append('')
    
    # Check forward test results
    v4_ft = results.get('V4-Simple', {}).get('forward_test', {})
    v5_ft = results.get('V5-Simple', {}).get('forward_test', {})
    v4_ft_ret = v4_ft.get('total_return_pct', 0)
    v5_ft_ret = v5_ft.get('total_return_pct', 0)
    
    if v4_ft_ret > 0 and v5_ft_ret > 0:
        lines.append('**Both models survive forward testing.** The feature engineering + XGBoost architecture generalizes.')
    elif v4_ft_ret > 0 or v5_ft_ret > 0:
        lines.append('**One model survives forward testing.** Check which version to deploy.')
    else:
        lines.append('**Neither model survives forward testing under these conditions.** Consider more data or different approach.')
    
    lines.append('')
    lines.append('---')
    lines.append('*Generated by `scripts/model_comparison_walkforward.py`*')
    
    return '\n'.join(lines)


# ============================================================================
# 7. MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='V4 vs V5 Walk-Forward Comparison')
    parser.add_argument('--capital', type=float, default=5000)
    parser.add_argument('--optuna-trials', type=int, default=15)
    args = parser.parse_args()
    
    capital = args.capital
    
    # Copy models
    logger.info('Copying models to safe location...')
    model_paths = copy_models()
    v4_data = load_model_copy(model_paths['v4'])
    v5_data = load_model_copy(model_paths['v5'])
    logger.info(f'V4: {v4_data["n_features"]} features, V5: {v5_data["n_features"]} features')
    
    # Load data
    logger.info('Loading gold data...')
    df = load_asset_data(asset='gold', primary_tf='15m', session_filter=False)
    df = engineer_all_features(df, add_labels=True, asset='gold')
    # Add V4-specific features (CVD slopes, ADX, ATR, trend, HTF indicators)
    df = compute_v4_features(df)
    logger.info(f'Data: {len(df)} rows, {len(df.columns)} columns')
    
    # Run 4 scenarios
    all_results = {}
    
    scenarios = [
        ('V4-Simple', v4_data, 4, 1, 1, 0.0001, 0.0002, False, args.optuna_trials, 2),
        ('V4-Stress', v4_data, 2, 1, 1, 0.0005, 0.0005, True, args.optuna_trials, 2),
        ('V5-Simple', v5_data, 4, 1, 1, 0.0001, 0.0002, False, args.optuna_trials, 2),
        ('V5-Stress', v5_data, 2, 1, 1, 0.0005, 0.0005, True, args.optuna_trials, 2),
    ]
    
    for name, model, train_m, test_m, step_m, comm, slip, optuna, trials, fwd_m in scenarios:
        logger.info(f'\n{"=" * 60}')
        logger.info(f'RUNNING: {name}')
        logger.info(f'{"=" * 60}')
        
        result = run_scenario(
            model_name=name,
            model_data=model,
            df=df,
            capital=capital,
            train_months=train_m,
            test_months=test_m,
            step_months=step_m,
            commission_pct=comm,
            slippage_pct=slip,
            use_optuna=optuna,
            n_trials=trials,
            forward_test_months=fwd_m,
        )
        
        all_results[name] = result
        
        agg = result.get('aggregated', {})
        ft = result.get('forward_test', {})
        logger.info(f'{name}: WF avg return={agg.get("total_return_pct", {}).get("mean", 0):+.1f}%, Forward={ft.get("total_return_pct", 0):+.1f}%')
    
    # Generate report
    report = generate_report(all_results, capital)
    
    report_dir = REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = report_dir / 'model_comparison_walkforward.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f'\nReport saved: {report_path}')
    
    # Save JSON
    json_path = report_dir / 'model_comparison_walkforward.json'
    
    def make_serializable(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return str(obj)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=make_serializable)
    logger.info(f'JSON saved: {json_path}')
    
    # Print final summary
    logger.info(f'\n{"=" * 60}')
    logger.info('FINAL SUMMARY')
    logger.info(f'{"=" * 60}')
    for name, data in all_results.items():
        agg = data.get('aggregated', {})
        ft = data.get('forward_test', {})
        ss = data.get('single_split', {})
        wf_ret = agg.get('total_return_pct', {}).get('mean', 0)
        ft_ret = ft.get('total_return_pct', 0)
        ss_ret = ss.get('total_return_pct', 0)
        logger.info(f'{name}: SS={ss_ret:+.1f}% | WF={wf_ret:+.1f}% | FT={ft_ret:+.1f}%')


if __name__ == '__main__':
    main()
