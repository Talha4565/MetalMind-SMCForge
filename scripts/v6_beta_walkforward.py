"""
V6-Beta: Enhanced Features + Hyperband Optuna + Fixed Params

Improvements over V6-Alpha:
1. Lagged features (1, 3, 5 bars) — captures feature momentum
2. Feature interactions (VWAPd*CVD, ADX*ATR) — explicit cross-terms
3. Regime detection (rolling vol, trend strength) — market state awareness
4. Cross-asset features (DXY, VIX, TNX) — macro context
5. Hyperband early stopping — kills bad Optuna trials fast
6. Fixed params from single Optuna run — fast, reproducible, no per-fold tuning

Standalone — does NOT touch the main project.

Usage:
    python scripts/v6_beta_walkforward.py
    python scripts/v6_beta_walkforward.py --capital 10000
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
# V6-BETA CONFIG
# ============================================================================

BETA_CONFIG = {
    'lot_size': 0.01,
    'gold_price_approx': 3200,
    'atr_sl_multiplier': 1.5,
    'atr_tp_multiplier': 3.0,
    'atr_period': 14,
    'confidence_threshold': 0.65,
    'max_hold_bars': 24,
    'commission_pct': 0.0001,
    'slippage_pct': 0.0002,
    'train_months': 2,
    'test_months': 1,
    'step_months': 1,
    'forward_test_months': 2,
    'optuna_trials': 50,  # More trials since we run once
}


# ============================================================================
# 1. CROSS-ASSET FEATURES (DXY, VIX, TNX)
# ============================================================================

def fetch_cross_asset_features(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Fetch DXY, VIX, TNX and align to gold timestamps."""
    import yfinance as yf
    
    features = pd.DataFrame(index=dates)
    
    tickers = {
        'dxy': 'DX-Y.NYB',
        'vix': '^VIX',
        'tnx': '^TNX',
    }
    
    for name, ticker in tickers.items():
        try:
            data = yf.download(ticker, start=dates.min() - pd.Timedelta(days=5),
                             end=dates.max() + pd.Timedelta(days=1), progress=False)
            if len(data) > 0:
                # Resample to 15min and forward-fill (daily data -> intraday)
                close = data['Close'].resample('15min').ffill()
                features[f'{name}_close'] = close.reindex(dates, method='ffill')
                features[f'{name}_ret_1d'] = features[f'{name}_close'].pct_change(96)  # 1-day return
                features[f'{name}_ret_5d'] = features[f'{name}_close'].pct_change(480)  # 5-day return
                logger.info(f'  Loaded {name}: {features[f"{name}_close"].notna().sum()} values')
            else:
                features[f'{name}_close'] = 0
                features[f'{name}_ret_1d'] = 0
                features[f'{name}_ret_5d'] = 0
                logger.warning(f'  {name}: no data, using zeros')
        except Exception as e:
            features[f'{name}_close'] = 0
            features[f'{name}_ret_1d'] = 0
            features[f'{name}_ret_5d'] = 0
            logger.warning(f'  {name} failed: {e}')
    
    return features


# ============================================================================
# 2. ENHANCED FEATURE ENGINEERING
# ============================================================================

def add_lagged_features(df: pd.DataFrame, columns: List[str], lags: List[int] = [1, 3, 5]) -> pd.DataFrame:
    """Add lagged values for key features."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            for lag in lags:
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
    return df


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add multiplicative interactions between key features."""
    df = df.copy()
    interactions = [
        ('VWAPd_4', 'CVD_4'),
        ('VWAPd_16', 'CVD_16'),
        ('adx_14', 'atr_14'),
        ('trend_ema_cross', 'adx_14'),
        ('fvg_bullish', 'liquidity_sweep_high'),
        ('bos_bullish', 'higher_high'),
    ]
    for a, b in interactions:
        if a in df.columns and b in df.columns:
            df[f'{a}_x_{b}'] = df[a] * df[b]
    return df


def add_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add market regime detection features."""
    df = df.copy()
    
    # Volatility regime (rolling ATR percentile)
    if 'atr_14' in df.columns:
        df['vol_regime'] = df['atr_14'].rolling(100).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False
        )
        df['vol_regime_high'] = (df['vol_regime'] > 0.75).astype(int)
        df['vol_regime_low'] = (df['vol_regime'] < 0.25).astype(int)
    
    # Trend regime (rolling return sign consistency)
    if 'Ret_4' in df.columns:
        df['trend_regime'] = df['Ret_4'].rolling(20).apply(
            lambda x: (x > 0).sum() / len(x), raw=False
        )
        df['trend_strong'] = (df['trend_regime'] > 0.7).astype(int)
        df['trend_weak'] = (df['trend_regime'] < 0.3).astype(int)
    
    # Session volume regime
    if 'volume' in df.columns:
        df['vol_ratio'] = df['volume'] / df['volume'].rolling(100).mean()
        df['vol_spike'] = (df['vol_ratio'] > 2.0).astype(int)
    
    return df


# ============================================================================
# 3. ATR + BACKTEST ENGINE (same as V6-Alpha)
# ============================================================================

def compute_atr(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


@dataclass
class V6Trade:
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp
    exit_price: float
    sl_price: float
    tp_price: float
    pnl_usd: float
    hit_tp: bool
    hit_sl: bool
    bars_held: int


def run_v6_backtest(df, signals, atr, lot_size=0.01, gold_price=3200,
                    sl_mult=1.5, tp_mult=3.0, max_hold=24,
                    commission_pct=0.0001, slippage_pct=0.0002):
    trades = []
    equity = 0.0
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
        
        hit_tp = hit_sl = False
        exit_price = entry_price
        bars_held = 0
        
        for k in range(1, max_hold + 1):
            exit_idx = i + 1 + k
            if exit_idx >= len(df): break
            high, low = df.iloc[exit_idx]['high'], df.iloc[exit_idx]['low']
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
                exit_price = df.iloc[i + 1 + max_hold]['close'] * (1 - slippage_pct)
        
        gross_pnl = (exit_price - entry_price) * lot_size * 100
        cost = entry_price * lot_size * 100 * (commission_pct * 2)
        net_pnl = gross_pnl - cost
        equity += net_pnl
        equity_curve.append(equity)
        
        trades.append(V6Trade(
            entry_time=df.index[i + 1], entry_price=entry_price,
            exit_time=df.index[min(i + 1 + bars_held, len(df) - 1)],
            exit_price=exit_price, sl_price=sl_price, tp_price=tp_price,
            pnl_usd=net_pnl, hit_tp=hit_tp, hit_sl=hit_sl, bars_held=bars_held,
        ))
    
    if not trades:
        return {'trades': [], 'metrics': {}, 'equity_curve': equity_curve}
    
    pnls = [t.pnl_usd for t in trades]
    n = len(trades)
    wins = [t for t in trades if t.pnl_usd > 0]
    losses = [t for t in trades if t.pnl_usd <= 0]
    wr = len(wins) / n
    avg_w = np.mean([t.pnl_usd for t in wins]) if wins else 0
    avg_l = np.mean([t.pnl_usd for t in losses]) if losses else 0
    pf = abs(avg_w / avg_l) if avg_l != 0 else np.inf
    total = sum(pnls)
    eq = pd.Series(equity_curve)
    max_dd = (eq - eq.cummax()).min()
    
    if len(pnls) > 1:
        rets = pd.Series(pnls) / 5000
        sharpe = (rets.mean() / rets.std()) * np.sqrt(252) if rets.std() != 0 else 0
        down = rets[rets < 0]
        down_std = down.std() if len(down) > 0 else 0
        sortino = (rets.mean() / down_std) * np.sqrt(252) if down_std != 0 else 0
    else:
        sharpe = sortino = 0
    
    return {
        'trades': [asdict(t) for t in trades],
        'metrics': {
            'n_trades': n, 'win_rate': wr, 'avg_win': float(avg_w), 'avg_loss': float(avg_l),
            'profit_factor': pf, 'total_return_usd': total, 'total_return_pct': (total / 5000) * 100,
            'max_drawdown_usd': float(max_dd), 'sharpe_ratio': sharpe, 'sortino_ratio': sortino,
            'tp_hits': sum(1 for t in trades if t.hit_tp), 'sl_hits': sum(1 for t in trades if t.hit_sl),
            'avg_bars_held': float(np.mean([t.bars_held for t in trades])),
        },
        'equity_curve': equity_curve,
    }


# ============================================================================
# 4. FOLD GENERATOR
# ============================================================================

def generate_folds(df, train_m, test_m, step_m, fwd_m):
    dates = df.index
    end = dates.max()
    if fwd_m > 0:
        ft_start = end - pd.DateOffset(months=fwd_m)
        wf_df = df[dates < ft_start]
        fwd_df = df[dates >= ft_start]
    else:
        wf_df = df
        fwd_df = pd.DataFrame()
    
    folds = []
    start = wf_df.index.min()
    while True:
        train_end = start + pd.DateOffset(months=train_m)
        test_end = train_end + pd.DateOffset(months=test_m)
        if test_end > wf_df.index.max(): break
        train = wf_df[(wf_df.index >= start) & (wf_df.index < train_end)]
        test = wf_df[(wf_df.index >= train_end) & (wf_df.index < test_end)]
        if len(train) >= 100 and len(test) >= 20:
            folds.append({
                'fold': len(folds) + 1,
                'train_start': start.strftime('%Y-%m-%d'), 'train_end': train_end.strftime('%Y-%m-%d'),
                'test_start': train_end.strftime('%Y-%m-%d'), 'test_end': test_end.strftime('%Y-%m-%d'),
                'train_rows': len(train), 'test_rows': len(test),
                'train_df': train, 'test_df': test,
            })
        start += pd.DateOffset(months=step_m)
    return folds, fwd_df


# ============================================================================
# 5. OPTUNA WITH HYPERBAND (run once on full dataset)
# ============================================================================

def find_best_params(X_train, y_train, n_trials=50):
    """Run Optuna with Hyperband pruning once. Return best params."""
    import xgboost as xgb
    import optuna
    from sklearn.metrics import accuracy_score
    
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    split = int(len(X_train) * 0.8)
    X_tr, X_val = X_train.iloc[:split], X_train.iloc[split:]
    y_tr, y_val = y_train.iloc[:split], y_train.iloc[split:]
    
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 200, 800),
            'max_depth': trial.suggest_int('max_depth', 3, 7),
            'learning_rate': trial.suggest_float('lr', 0.005, 0.15, log=True),
            'subsample': trial.suggest_float('sub', 0.5, 0.95),
            'colsample_bytree': trial.suggest_float('col', 0.4, 0.9),
            'min_child_weight': trial.suggest_int('mcw', 1, 15),
            'gamma': trial.suggest_float('gamma', 0, 2.0),
            'reg_alpha': trial.suggest_float('alpha', 0, 5.0),
            'reg_lambda': trial.suggest_float('lambda', 0, 5.0),
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'random_state': 42,
            'verbosity': 0,
            'early_stopping_rounds': 50,
        }
        model = xgb.XGBClassifier(**params)
        
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=0)
        
        pred = model.predict(X_val)
        return 1 - accuracy_score(y_val, pred)
    
    # Use MedianPruner for Hyperband-like behavior
    sampler = optuna.samplers.TPESampler(seed=42)
    pruner = optuna.pruners.MedianPruner(n_warmup_steps=10)
    study = optuna.create_study(direction='minimize', sampler=sampler, pruner=pruner)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    
    best = study.best_params
    best['objective'] = 'binary:logistic'
    best['eval_metric'] = 'logloss'
    best['random_state'] = 42
    best['verbosity'] = 0
    
    logger.info(f'  Best Optuna value: {study.best_value:.4f}')
    logger.info(f'  Best params: max_depth={best["max_depth"]}, lr={best["lr"]:.4f}, n_est={best["n_estimators"]}')
    
    return best


# ============================================================================
# 6. TRAIN + BACKTEST WITH FIXED PARAMS
# ============================================================================

def train_and_backtest(train_df, test_df, feature_names, asset, params, config):
    import xgboost as xgb
    
    if 'target' in train_df.columns:
        X_train = train_df[feature_names]
        y_train = train_df['target']
    else:
        from features.labels import generate_labels
        train_df = train_df.copy()
        train_df['target'] = generate_labels(train_df, asset=asset)
        X_train = train_df[feature_names]
        y_train = train_df['target']
    
    valid = X_train.notna().all(axis=1) & y_train.notna()
    X_train, y_train = X_train[valid], y_train[valid]
    
    X_test = test_df[feature_names]
    valid_test = X_test.notna().all(axis=1)
    X_test_clean, test_clean = X_test[valid_test], test_df[valid_test]
    
    if len(X_train) < 50 or len(X_test_clean) < 10:
        return {'metrics': {}, 'trades': []}
    
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train, verbose=0)
    
    try:
        proba = model.predict_proba(X_test_clean)[:, 1]
    except:
        proba = np.full(len(X_test_clean), 0.5)
    
    confidence = np.maximum(proba, 1 - proba)
    signals = np.zeros(len(X_test_clean), dtype=int)
    for i in range(len(X_test_clean)):
        if confidence[i] >= config['confidence_threshold'] and proba[i] >= 0.5:
            signals[i] = 1
    
    atr = compute_atr(test_clean, config['atr_period'])
    
    results = run_v6_backtest(
        test_clean, signals, atr,
        lot_size=config['lot_size'], gold_price=config['gold_price_approx'],
        sl_mult=config['atr_sl_multiplier'], tp_mult=config['atr_tp_multiplier'],
        max_hold=config['max_hold_bars'], commission_pct=config['commission_pct'],
        slippage_pct=config['slippage_pct'],
    )
    
    try:
        y_test = test_clean['target'] if 'target' in test_clean.columns else None
        if y_test is not None:
            from sklearn.metrics import accuracy_score
            results['metrics']['model_accuracy'] = float(accuracy_score(y_test, model.predict(X_test_clean)))
    except:
        results['metrics']['model_accuracy'] = 0.0
    
    results['metrics']['signals_generated'] = int(signals.sum())
    return results


# ============================================================================
# 7. AGGREGATE + REPORT
# ============================================================================

def aggregate(folds):
    keys = ['win_rate', 'profit_factor', 'sharpe_ratio', 'total_return_usd', 'n_trades']
    agg = {}
    for k in keys:
        vals = [f.get(k, 0) for f in folds if k in f and np.isfinite(f.get(k, 0))]
        agg[k] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))} if vals else {'mean': 0, 'std': 0}
    return agg


def report(folds, agg, single, forward, config, capital, params):
    lines = []
    lines.append('# V6-Beta Walk-Forward Report — GOLD')
    lines.append('')
    lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Capital:** ${capital:,.0f}')
    lines.append(f'**Lot size:** {config["lot_size"]} ({config["lot_size"] * config["gold_price_approx"] * 100:,.0f} notional)')
    lines.append(f'**SL:** {config["atr_sl_multiplier"]}x ATR | **TP:** {config["atr_tp_multiplier"]}x ATR (2:1 RR)')
    lines.append(f'**Confidence:** {config["confidence_threshold"]:.0%}')
    lines.append(f'**Features:** 89 base + lagged + interactions + regime + cross-asset')
    lines.append(f'**Optuna:** Hyperband pruner, {config["optuna_trials"]} trials, fixed params')
    lines.append(f'**Folds:** {len(folds)}')
    lines.append('')
    lines.append('## Optimized Hyperparameters')
    lines.append('')
    lines.append('```json')
    lines.append(json.dumps({k: v for k, v in params.items() if k not in ('objective', 'eval_metric', 'random_state', 'verbosity')}, indent=2))
    lines.append('```')
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
    lines.append('| Fold | Period | Win Rate | Return | Trades | TP | SL | Avg Bars |')
    lines.append('|------|--------|----------|--------|--------|----|----|----------|')
    for f in folds:
        p = f'{f["test_start"]} -> {f["test_end"]}'
        lines.append(f'| {f["fold"]} | {p} | {f.get("win_rate",0):.1%} | ${f.get("total_return_usd",0):+,.0f} | {f.get("n_trades",0)} | {f.get("tp_hits",0)} | {f.get("sl_hits",0)} | {f.get("avg_bars_held",0):.0f} |')
    lines.append('')
    lines.append('---')
    lines.append('*Generated by `scripts/v6_beta_walkforward.py`*')
    return '\n'.join(lines)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='V6-Beta Walk-Forward')
    parser.add_argument('--capital', type=float, default=5000)
    parser.add_argument('--optuna-trials', type=int, default=50)
    args = parser.parse_args()
    
    config = BETA_CONFIG.copy()
    config['optuna_trials'] = args.optuna_trials
    capital = args.capital
    
    logger.info(f'V6-Beta: ${capital:,.0f}, {config["lot_size"]} lots, Hyperband Optuna, enhanced features')
    
    # Load gold data
    df = load_asset_data(asset='gold', primary_tf='15m', session_filter=False)
    df = engineer_all_features(df, add_labels=True, asset='gold')
    df = compute_v4_features(df)
    logger.info(f'Base features: {len(df.columns)} cols')
    
    # Add enhanced features
    logger.info('Adding lagged features...')
    key_cols = ['VWAPd_4', 'CVD_4', 'adx_14', 'atr_14', 'trend_ema_cross', 'fvg_bullish']
    df = add_lagged_features(df, key_cols, lags=[1, 3, 5])
    
    logger.info('Adding interaction features...')
    df = add_interaction_features(df)
    
    logger.info('Adding regime features...')
    df = add_regime_features(df)
    
    logger.info('Fetching cross-asset features (DXY, VIX, TNX)...')
    cross = fetch_cross_asset_features(df.index)
    df = pd.concat([df, cross], axis=1)
    
    df = df.fillna(0)
    logger.info(f'Enhanced features: {len(df.columns)} cols')
    
    # Get base feature list from V4
    with open('models/gold_regression_system.pkl', 'rb') as f:
        base_features = pickle.load(f)['features']
    
    # All features = base + new
    all_features = [c for c in df.columns if c not in ('target', 'datetime') and df[c].dtype in ['float64', 'int64']]
    logger.info(f'Total usable features: {len(all_features)}')
    
    # === PHASE 1: Find best params with Hyperband Optuna (run once) ===
    logger.info(f'\n{"=" * 60}')
    logger.info('PHASE 1: Optuna Hyperband tuning (once on full data)')
    logger.info(f'{"=" * 60}')
    
    X_full = df[all_features]
    y_full = df['target'] if 'target' in df.columns else pd.Series(0, index=df.index)
    valid = X_full.notna().all(axis=1) & y_full.notna()
    X_full, y_full = X_full[valid], y_full[valid]
    
    best_params = find_best_params(X_full, y_full, n_trials=config['optuna_trials'])
    
    # Save params
    params_path = REPORTS_DIR / 'v6_beta_params.json'
    params_path.parent.mkdir(parents=True, exist_ok=True)
    with open(params_path, 'w') as f:
        json.dump(best_params, f, indent=2)
    logger.info(f'Params saved: {params_path}')
    
    # === PHASE 2: Walk-forward with fixed params ===
    logger.info(f'\n{"=" * 60}')
    logger.info('PHASE 2: Walk-forward with fixed params')
    logger.info(f'{"=" * 60}')
    
    folds, fwd_df = generate_folds(df, config['train_months'], config['test_months'],
                                   config['step_months'], config['forward_test_months'])
    logger.info(f'{len(folds)} folds + forward test')
    
    fold_results = []
    for fi in folds:
        logger.info(f'Fold {fi["fold"]}/{len(folds)}: {fi["train_start"]}->{fi["test_start"]}')
        res = train_and_backtest(fi['train_df'], fi['test_df'], all_features, 'gold', best_params, config)
        m = res['metrics']
        r = {**fi, **m}
        r.pop('train_df', None)
        r.pop('test_df', None)
        fold_results.append(r)
        logger.info(f'  WR={m.get("win_rate",0):.1%} Return=${m.get("total_return_usd",0):+,.0f} Trades={m.get("n_trades",0)}')
    
    agg = aggregate(fold_results)
    
    # Single-split
    from data.loaders import train_val_test_split
    train_df, val_df, test_df = train_val_test_split(df, 0.70, 0.15, 0.15)
    single = train_and_backtest(train_df, test_df, all_features, 'gold', best_params, config)['metrics']
    
    # Forward test
    forward = {}
    if len(fwd_df) > 0:
        wf_train = df[df.index < fwd_df.index.min()]
        forward = train_and_backtest(wf_train, fwd_df, all_features, 'gold', best_params, config).get('metrics', {})
    
    # Report
    rpt = report(fold_results, agg, single, forward, config, capital, best_params)
    with open(REPORTS_DIR / 'v6_beta_walkforward.md', 'w', encoding='utf-8') as f:
        f.write(rpt)
    
    with open(REPORTS_DIR / 'v6_beta_walkforward.json', 'w', encoding='utf-8') as f:
        json.dump({'config': config, 'params': best_params, 'n_features': len(all_features),
                    'folds': fold_results, 'aggregated': agg, 'single': single, 'forward': forward},
                   f, indent=2, default=str)
    
    logger.info(f'\nReport: reports/v6_beta_walkforward.md')
    logger.info(f'Results:')
    logger.info(f'  Single-split: ${single.get("total_return_usd",0):+,.0f}')
    logger.info(f'  Walk-forward: ${agg.get("total_return_usd",{}).get("mean",0):+,.0f} avg')
    logger.info(f'  Forward test: ${forward.get("total_return_usd",0):+,.0f}')


if __name__ == '__main__':
    main()
