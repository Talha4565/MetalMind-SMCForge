"""
V6-Alpha: New Model — XGBoost + Optuna, ATR-based TP/SL, 0.01 lots

Standalone experimental model. Does NOT touch the main project.
Tests walk-forward + forward validation on a fresh XGBoost model.

Features: 89 (same as V4/V5)
Risk: 0.01 lots (1 oz gold)
SL/TP: ATR-based (adaptive)
Capital: $5,000
Confidence: 65% minimum

Usage:
    python scripts/v6_alpha_walkforward.py
    python scripts/v6_alpha_walkforward.py --capital 10000
"""

import sys
import json
import logging
import argparse
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import BACKTEST_CONFIG, REPORTS_DIR, get_label_params
from data.loaders import load_asset_data
from features.pipeline import engineer_all_features
from features.v4_features import compute_v4_features

logging.basicConfig(level=logging.INFO, format='%(asctime)s — %(levelname)s — %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# V6-ALPHA CONFIG
# ============================================================================

V6_CONFIG = {
    'lot_size': 0.01,            # 0.01 lots = 1 oz gold
    'gold_price_approx': 3200,   # Approximate gold price for lot value calc
    'atr_sl_multiplier': 1.5,    # SL at 1.5x ATR
    'atr_tp_multiplier': 3.0,    # TP at 3.0x ATR (2:1 RR)
    'atr_period': 14,            # ATR lookback
    'confidence_threshold': 0.65,
    'max_hold_bars': 24,         # Max 6 hours (24 x 15min)
    'commission_pct': 0.0001,    # 0.01% per trade
    'slippage_pct': 0.0002,      # 0.02% per trade
    'train_months': 2,
    'test_months': 1,
    'step_months': 1,
    'forward_test_months': 2,
    'optuna_trials': 20,
}


# ============================================================================
# ATR CALCULATION
# ============================================================================

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range."""
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    
    return tr.rolling(period).mean()


# ============================================================================
# CUSTOM BACKTEST ENGINE (ATR-based, lot-sized)
# ============================================================================

@dataclass
class V6Trade:
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp
    exit_price: float
    sl_price: float
    tp_price: float
    lot_size: float
    pnl_usd: float
    pnl_pips: float
    hit_tp: bool
    hit_sl: bool
    bars_held: int
    atr_at_entry: float


def run_v6_backtest(
    df: pd.DataFrame,
    signals: np.ndarray,
    atr: pd.Series,
    lot_size: float = 0.01,
    gold_price: float = 3200,
    sl_mult: float = 1.5,
    tp_mult: float = 3.0,
    max_hold: int = 24,
    commission_pct: float = 0.0001,
    slippage_pct: float = 0.0002,
) -> Dict[str, Any]:
    """
    Custom backtest with ATR-based TP/SL and lot sizing.
    
    0.01 lots gold = 1 oz = $gold_price notional
    P&L per $1 move = lot_size * 100 (standard gold contract)
    P&L per pip (0.01 move) = lot_size * $1
    """
    trades = []
    equity = 0.0  # Track P&L, not equity curve
    equity_curve = [0.0]
    
    for i in range(len(signals)):
        if signals[i] == 0:
            equity_curve.append(equity)
            continue
        
        if i + 1 >= len(df):
            break
        
        entry_price = df.iloc[i + 1]['open']
        current_atr = atr.iloc[i] if not np.isnan(atr.iloc[i]) else atr.dropna().mean()
        
        if np.isnan(current_atr) or current_atr <= 0:
            equity_curve.append(equity)
            continue
        
        sl_distance = current_atr * sl_mult
        tp_distance = current_atr * tp_mult
        
        sl_price = entry_price - sl_distance
        tp_price = entry_price + tp_distance
        
        entry_price *= (1 + slippage_pct)
        
        hit_tp = False
        hit_sl = False
        exit_price = entry_price
        bars_held = 0
        
        for k in range(1, max_hold + 1):
            exit_idx = i + 1 + k
            if exit_idx >= len(df):
                break
            
            high = df.iloc[exit_idx]['high']
            low = df.iloc[exit_idx]['low']
            bars_held = k
            
            if high >= tp_price:
                exit_price = tp_price * (1 - slippage_pct)
                hit_tp = True
                break
            elif low <= sl_price:
                exit_price = sl_price * (1 - slippage_pct)
                hit_sl = True
                break
        else:
            if i + 1 + max_hold < len(df):
                exit_idx = i + 1 + max_hold
                exit_price = df.iloc[exit_idx]['close'] * (1 - slippage_pct)
        
        # P&L calculation for gold
        # 0.01 lots = 1 oz. P&L = (exit - entry) * lot_size * 100
        price_move = exit_price - entry_price
        gross_pnl = price_move * lot_size * 100
        cost = entry_price * lot_size * 100 * (commission_pct * 2)
        net_pnl = gross_pnl - cost
        
        pnl_pips = price_move * 100  # Pips (each pip = $0.01 on gold)
        
        equity += net_pnl
        equity_curve.append(equity)
        
        trades.append(V6Trade(
            entry_time=df.index[i + 1],
            entry_price=entry_price,
            exit_time=df.index[min(i + 1 + bars_held, len(df) - 1)],
            exit_price=exit_price,
            sl_price=sl_price,
            tp_price=tp_price,
            lot_size=lot_size,
            pnl_usd=net_pnl,
            pnl_pips=pnl_pips,
            hit_tp=hit_tp,
            hit_sl=hit_sl,
            bars_held=bars_held,
            atr_at_entry=current_atr,
        ))
    
    # Calculate metrics
    if not trades:
        return {'trades': [], 'metrics': {}, 'equity_curve': equity_curve}
    
    pnls = [t.pnl_usd for t in trades]
    n_trades = len(trades)
    wins = [t for t in trades if t.pnl_usd > 0]
    losses = [t for t in trades if t.pnl_usd <= 0]
    
    win_rate = len(wins) / n_trades if n_trades > 0 else 0
    avg_win = np.mean([t.pnl_usd for t in wins]) if wins else 0
    avg_loss = np.mean([t.pnl_usd for t in losses]) if losses else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else np.inf
    
    total_return = sum(pnls)
    
    # Max drawdown
    eq = pd.Series(equity_curve)
    peak = eq.cummax()
    drawdown = eq - peak
    max_dd = drawdown.min()
    
    # Sharpe
    if len(pnls) > 1:
        returns = pd.Series(pnls) / 5000
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
    else:
        sharpe = 0
    
    # Sortino
    if len(pnls) > 1:
        returns = pd.Series(pnls) / 5000
        down = returns[returns < 0]
        down_std = down.std() if len(down) > 0 else 0
        sortino = (returns.mean() / down_std) * np.sqrt(252) if down_std != 0 else 0
    else:
        sortino = 0
    
    metrics = {
        'n_trades': n_trades,
        'win_rate': win_rate,
        'avg_win': float(avg_win),
        'avg_loss': float(avg_loss),
        'profit_factor': profit_factor,
        'total_return_usd': total_return,
        'total_return_pct': (total_return / 5000) * 100,
        'max_drawdown_usd': float(max_dd),
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'tp_hits': sum(1 for t in trades if t.hit_tp),
        'sl_hits': sum(1 for t in trades if t.hit_sl),
        'avg_bars_held': np.mean([t.bars_held for t in trades]),
    }
    
    return {
        'trades': [asdict(t) for t in trades],
        'metrics': metrics,
        'equity_curve': equity_curve,
    }


# ============================================================================
# WALK-FORWARD FOLD GENERATOR
# ============================================================================

def generate_folds(
    df: pd.DataFrame,
    train_months: int,
    test_months: int,
    step_months: int,
    forward_test_months: int = 0,
) -> Tuple[List[Dict], pd.DataFrame]:
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
    
    return folds, forward_df


# ============================================================================
# OPTUNA TRAIN + BACKTEST
# ============================================================================

def train_and_backtest_v6(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_names: List[str],
    asset: str,
    config: Dict,
    n_trials: int = 20,
) -> Dict[str, Any]:
    """Optuna-tuned XGBoost + ATR-based backtest."""
    import xgboost as xgb
    import optuna
    from sklearn.metrics import accuracy_score
    
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    # Prepare data
    if 'target' in train_df.columns:
        X_train = train_df[feature_names]
        y_train = train_df['target']
    else:
        from features.labels import generate_labels
        train_df = train_df.copy()
        train_df['target'] = generate_labels(train_df, asset=asset)
        X_train = train_df[feature_names]
        y_train = train_df['target']
    
    valid_mask = X_train.notna().all(axis=1) & y_train.notna()
    X_train = X_train[valid_mask]
    y_train = y_train[valid_mask]
    
    X_test = test_df[feature_names]
    valid_test = X_test.notna().all(axis=1)
    X_test_clean = X_test[valid_test]
    test_df_clean = test_df[valid_test]
    
    if len(X_train) < 50 or len(X_test_clean) < 10:
        return {'metrics': {}, 'trades': []}
    
    # Optuna tuning
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
    best.update({'n_estimators': 500, 'objective': 'binary:logistic',
                 'eval_metric': 'logloss', 'random_state': 42, 'verbosity': 0})
    
    model = xgb.XGBClassifier(**best)
    model.fit(X_train, y_train, verbose=0)
    
    # Predictions
    try:
        proba = model.predict_proba(X_test_clean)[:, 1]
    except Exception:
        proba = np.full(len(X_test_clean), 0.5)
    
    confidence = np.maximum(proba, 1 - proba)
    signals = np.zeros(len(X_test_clean), dtype=int)
    for i in range(len(X_test_clean)):
        if confidence[i] >= config['confidence_threshold'] and proba[i] >= 0.5:
            signals[i] = 1
    
    # ATR
    atr = compute_atr(test_df_clean, period=config['atr_period'])
    
    # Backtest
    results = run_v6_backtest(
        test_df_clean, signals, atr,
        lot_size=config['lot_size'],
        gold_price=config['gold_price_approx'],
        sl_mult=config['atr_sl_multiplier'],
        tp_mult=config['atr_tp_multiplier'],
        max_hold=config['max_hold_bars'],
        commission_pct=config['commission_pct'],
        slippage_pct=config['slippage_pct'],
    )
    
    # Model accuracy
    try:
        y_test = test_df_clean['target'] if 'target' in test_df_clean.columns else None
        if y_test is not None:
            pred = model.predict(X_test_clean)
            results['metrics']['model_accuracy'] = float(accuracy_score(y_test, pred))
    except Exception:
        results['metrics']['model_accuracy'] = 0.0
    
    results['metrics']['optuna_best'] = study.best_value
    results['metrics']['signals_generated'] = int(signals.sum())
    
    return results


# ============================================================================
# SINGLE-SPLIT BASELINE
# ============================================================================

def run_single_split(df, feature_names, asset, config, n_trials):
    from data.loaders import train_val_test_split
    train_df, val_df, test_df = train_val_test_split(df, 0.70, 0.15, 0.15)
    return train_and_backtest_v6(train_df, test_df, feature_names, asset, config, n_trials)


# ============================================================================
# AGGREGATE + REPORT
# ============================================================================

def aggregate(folds):
    keys = ['win_rate', 'profit_factor', 'sharpe_ratio', 'total_return_usd', 'n_trades', 'model_accuracy']
    agg = {}
    for k in keys:
        vals = [f.get(k, 0) for f in folds if k in f and np.isfinite(f.get(k, 0))]
        agg[k] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))} if vals else {'mean': 0, 'std': 0}
    return agg


def report(folds, agg, single, forward, config, capital):
    lines = []
    lines.append('# V6-Alpha Walk-Forward Report — GOLD')
    lines.append('')
    lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Capital:** ${capital:,.0f}')
    lines.append(f'**Lot size:** {config["lot_size"]} ({config["lot_size"] * 100:.0f} oz = ${config["lot_size"] * config["gold_price_approx"] * 100:,.0f} notional)')
    lines.append(f'**SL:** {config["atr_sl_multiplier"]}x ATR (adaptive)')
    lines.append(f'**TP:** {config["atr_tp_multiplier"]}x ATR (2:1 RR)')
    lines.append(f'**Confidence:** {config["confidence_threshold"]:.0%}')
    lines.append(f'**Optuna:** {config["optuna_trials"]} trials per fold')
    lines.append(f'**Folds:** {len(folds)}')
    lines.append('')
    
    lines.append('## Summary')
    lines.append('')
    lines.append('| Metric | Single-Split | Walk-Forward Avg | Forward Test |')
    lines.append('|--------|-------------|-----------------|--------------|')
    
    for k, label, fmt in [
        ('win_rate', 'Win Rate', lambda v: f'{v:.1%}'),
        ('total_return_usd', 'Total Return', lambda v: f'${v:+,.0f}'),
        ('sharpe_ratio', 'Sharpe', lambda v: f'{v:.2f}'),
        ('n_trades', 'Trades', lambda v: f'{v:.0f}'),
        ('profit_factor', 'Profit Factor', lambda v: f'{v:.2f}'),
    ]:
        ss = fmt(single.get(k, 0))
        wf = agg.get(k, {})
        wf_s = f'{fmt(wf.get("mean", 0))} +/- {fmt(wf.get("std", 0))}'
        ft = fmt(forward.get(k, 0))
        lines.append(f'| {label} | {ss} | {wf_s} | {ft} |')
    
    lines.append('')
    
    lines.append('## Per-Fold Detail')
    lines.append('')
    lines.append('| Fold | Period | Win Rate | Return | Trades | TP Hits | SL Hits | Avg Bars |')
    lines.append('|------|--------|----------|--------|--------|---------|---------|----------|')
    for f in folds:
        p = f'{f["test_start"]} -> {f["test_end"]}'
        lines.append(f'| {f["fold"]} | {p} | {f.get("win_rate",0):.1%} | ${f.get("total_return_usd",0):+,.0f} | {f.get("n_trades",0)} | {f.get("tp_hits",0)} | {f.get("sl_hits",0)} | {f.get("avg_bars_held",0):.0f} |')
    lines.append('')
    
    lines.append('---')
    lines.append('*Generated by `scripts/v6_alpha_walkforward.py`*')
    return '\n'.join(lines)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='V6-Alpha Walk-Forward')
    parser.add_argument('--capital', type=float, default=5000)
    parser.add_argument('--optuna-trials', type=int, default=20)
    args = parser.parse_args()
    
    config = V6_CONFIG.copy()
    config['optuna_trials'] = args.optuna_trials
    capital = args.capital
    
    logger.info(f'V6-Alpha Walk-Forward: ${capital:,.0f}, {config["lot_size"]} lots, ATR-based TP/SL')
    
    # Load data
    df = load_asset_data(asset='gold', primary_tf='15m', session_filter=False)
    df = engineer_all_features(df, add_labels=True, asset='gold')
    df = compute_v4_features(df)
    logger.info(f'Data: {len(df)} rows, {len(df.columns)} cols')
    
    # Get V4/V5 feature list
    with open('models/gold_regression_system.pkl', 'rb') as f:
        model_data = pickle.load(f)
    feature_names = model_data['features']
    
    # Generate folds
    folds, forward_df = generate_folds(
        df, config['train_months'], config['test_months'],
        config['step_months'], config['forward_test_months'],
    )
    logger.info(f'{len(folds)} folds + forward test')
    
    # Run folds
    fold_results = []
    for fi in folds:
        logger.info(f'Fold {fi["fold"]}/{len(folds)}: {fi["train_start"]}->{fi["test_start"]}')
        res = train_and_backtest_v6(fi['train_df'], fi['test_df'], feature_names, 'gold', config, config['optuna_trials'])
        m = res['metrics']
        result = {**fi, **m}
        result.pop('train_df', None)
        result.pop('test_df', None)
        fold_results.append(result)
        logger.info(f'  WR={m.get("win_rate",0):.1%} Return=${m.get("total_return_usd",0):+,.0f} Trades={m.get("n_trades",0)}')
    
    agg = aggregate(fold_results)
    
    # Single-split
    from data.loaders import train_val_test_split
    train_df, val_df, test_df = train_val_test_split(df, 0.70, 0.15, 0.15)
    single_res = train_and_backtest_v6(train_df, test_df, feature_names, 'gold', config, config['optuna_trials'])
    single = single_res['metrics']
    
    # Forward test
    ft_res = {}
    if len(forward_df) > 0:
        wf_train = df[df.index < forward_df.index.min()]
        ft_res = train_and_backtest_v6(wf_train, forward_df, feature_names, 'gold', config, config['optuna_trials'] + 5)
    forward = ft_res.get('metrics', {})
    
    # Report
    rpt = report(fold_results, agg, single, forward, config, capital)
    report_dir = REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    
    with open(report_dir / 'v6_alpha_walkforward.md', 'w', encoding='utf-8') as f:
        f.write(rpt)
    
    with open(report_dir / 'v6_alpha_walkforward.json', 'w', encoding='utf-8') as f:
        json.dump({'config': config, 'folds': fold_results, 'aggregated': agg, 'single': single, 'forward': forward}, f, indent=2, default=str)
    
    logger.info(f'Report: reports/v6_alpha_walkforward.md')
    logger.info(f'')
    logger.info(f'Results:')
    logger.info(f'  Single-split: ${single.get("total_return_usd",0):+,.0f} ({single.get("win_rate",0):.1%} WR, {single.get("n_trades",0)} trades)')
    logger.info(f'  Walk-forward: ${agg.get("total_return_usd",{}).get("mean",0):+,.0f} avg')
    logger.info(f'  Forward test: ${forward.get("total_return_usd",0):+,.0f} ({forward.get("win_rate",0):.1%} WR, {forward.get("n_trades",0)} trades)')


if __name__ == '__main__':
    main()
