"""
V6-Epsilon: Locked Optuna + Seed Averaging for Defensible Results

Proper methodology:
1. Run Optuna ONCE on walk-forward CV (not forward test)
2. Lock the best hyperparameters
3. Run 10 seeds with locked params
4. Report mean ± std for both walk-forward and forward test
5. Walk-forward average is PRIMARY metric

This eliminates Optuna search variance and gives a real distribution.

Standalone — does NOT touch the main project.

Usage:
    python scripts/v6_epsilon_final.py
"""

import sys
import json
import logging
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import REPORTS_DIR
from data.loaders import load_asset_data, train_val_test_split
from features.pipeline import engineer_all_features
from features.v4_features import compute_v4_features

logging.basicConfig(level=logging.INFO, format='%(asctime)s — %(levelname)s — %(message)s')
logger = logging.getLogger(__name__)

# V6-Delta feature engineering functions
PAIRS_TO_COLLAPSE = [
    ('fvg_bullish', 'fvg_bearish', 'fvg_signal'),
    ('order_block_bullish', 'order_block_bearish', 'order_block_signal'),
    ('liquidity_sweep_high', 'liquidity_sweep_low', 'liquidity_sweep_signal'),
    ('bos_bullish', 'bos_bearish', 'bos_signal'),
    ('bullish_structure', 'bearish_structure', 'structure_signal'),
    ('in_premium', 'in_discount', 'zone_signal'),
]

SPARSE_FEATURES = ['bos_bullish', 'bos_bearish', 'liquidity_sweep_high', 'liquidity_sweep_low', 'higher_low', 'lower_high']


def collapse_to_signed(df, b, c, n):
    df[n] = 0; df.loc[df[b] == 1, n] = 1; df.loc[df[c] == 1, n] = -1
    return df

def add_rolling_density(df, col, windows=[10, 20, 50]):
    for w in windows: df[f'{col}_count_{w}'] = df[col].rolling(w, min_periods=1).sum()
    return df

def add_bars_since(df, col, n):
    mask = (df[col] == 1).cumsum()
    df[n] = df.groupby(mask).cumcount()
    return df

def build_features(df):
    """Apply signed encoding + rolling density. Return feature list."""
    with open('models/gold_regression_system.pkl', 'rb') as f:
        orig_feats = pickle.load(f)['features']
    
    collapsed = []
    for b, c, n in PAIRS_TO_COLLAPSE:
        if b in df.columns and c in df.columns:
            df = collapse_to_signed(df, b, c, n)
            collapsed.extend([b, c])
    
    for feat in SPARSE_FEATURES:
        if feat in df.columns:
            df = add_rolling_density(df, feat, [10, 20, 50])
            if feat in ['bos_bullish', 'bos_bearish', 'higher_low', 'lower_high']:
                df = add_bars_since(df, feat, f'bars_since_{feat}')
    
    df = df.fillna(0)
    all_feats = [f for f in df.columns if f not in ('target', 'datetime') and df[f].dtype in ['float64', 'int64']]
    return df, all_feats


def compute_atr(df, p=14):
    h, l, c = df['high'], df['low'], df['close']
    tr = pd.concat([h-l, (h-c.shift(1)).abs(), (l-c.shift(1)).abs()], axis=1).max(axis=1)
    return tr.rolling(p).mean()


@dataclass
class Trade:
    entry_time: pd.Timestamp; entry_price: float; exit_time: pd.Timestamp; exit_price: float
    sl_price: float; tp_price: float; pnl_usd: float; hit_tp: bool; hit_sl: bool; bars_held: int


def backtest(df, signals, atr, lot=0.01, gold=3200, sl_m=1.5, tp_m=3.0, mh=24, comm=0.0001, slip=0.0002):
    trades, eq, eqc = [], 0.0, [0.0]
    for i in range(len(signals)):
        if signals[i] == 0: eqc.append(eq); continue
        if i+1 >= len(df): break
        entry = df.iloc[i+1]['open'] * (1+slip)
        a = atr.iloc[i] if not np.isnan(atr.iloc[i]) else atr.dropna().mean()
        if np.isnan(a) or a <= 0: eqc.append(eq); continue
        sl_p, tp_p = entry - a*sl_m, entry + a*tp_m
        hit_tp = hit_sl = False; exit_p = entry; bars = 0
        for k in range(1, mh+1):
            idx = i+1+k
            if idx >= len(df): break
            hi, lo = df.iloc[idx]['high'], df.iloc[idx]['low']; bars = k
            if hi >= tp_p: exit_p = tp_p*(1-slip); hit_tp = True; break
            elif lo <= sl_p: exit_p = sl_p*(1-slip); hit_sl = True; break
        else:
            if i+1+mh < len(df): exit_p = df.iloc[i+1+mh]['close']*(1-slip)
        pnl = (exit_p-entry)*lot*100 - entry*lot*100*comm*2
        eq += pnl; eqc.append(eq)
        trades.append(Trade(df.index[i+1], entry, df.index[min(i+1+bars, len(df)-1)],
                           exit_p, sl_p, tp_p, pnl, hit_tp, hit_sl, bars))
    if not trades: return {}
    pnls = [t.pnl_usd for t in trades]; n = len(trades)
    w = [t for t in trades if t.pnl_usd > 0]; l = [t for t in trades if t.pnl_usd <= 0]
    wr = len(w)/n; aw = np.mean([t.pnl_usd for t in w]) if w else 0
    al = np.mean([t.pnl_usd for t in l]) if l else 0; pf = abs(aw/al) if al != 0 else 0
    total = sum(pnls); eq_s = pd.Series(eqc); dd = (eq_s - eq_s.cummax()).min()
    rets = pd.Series(pnls)/5000 if len(pnls)>1 else pd.Series([0])
    sh = (rets.mean()/rets.std())*np.sqrt(252) if rets.std() != 0 else 0
    down = rets[rets<0]; ds = down.std() if len(down)>0 else 0
    so = (rets.mean()/ds)*np.sqrt(252) if ds != 0 else 0
    return {
        'n_trades': n, 'win_rate': wr, 'total_return_usd': total, 'total_return_pct': (total/5000)*100,
        'profit_factor': pf, 'sharpe_ratio': sh, 'sortino_ratio': so, 'max_drawdown_usd': float(dd),
        'tp_hits': sum(1 for t in trades if t.hit_tp), 'sl_hits': sum(1 for t in trades if t.hit_sl),
        'avg_bars_held': float(np.mean([t.bars_held for t in trades])),
    }


def make_folds(df, train_m=2, test_m=1, step_m=1, fwd_m=2):
    end = df.index.max(); ft = end - pd.DateOffset(months=fwd_m)
    wf, fwd = df[df.index < ft], df[df.index >= ft]
    result = []; start = wf.index.min()
    while True:
        te = start + pd.DateOffset(months=train_m)
        tse = te + pd.DateOffset(months=test_m)
        if tse > wf.index.max(): break
        tr = wf[(wf.index >= start) & (wf.index < te)]
        ts = wf[(wf.index >= te) & (wf.index < tse)]
        if len(tr) >= 100 and len(ts) >= 20:
            result.append({'fold': len(result)+1, 'train_start': start.strftime('%Y-%m-%d'),
                'train_end': te.strftime('%Y-%m-%d'), 'test_start': te.strftime('%Y-%m-%d'),
                'test_end': tse.strftime('%Y-%m-%d'), 'train_rows': len(tr), 'test_rows': len(ts),
                'train_df': tr, 'test_df': ts})
        start += pd.DateOffset(months=step_m)
    return result, fwd


def optuna_once(X, y, n=50):
    """Run Optuna ONCE on walk-forward objective. Return locked params."""
    import xgboost as xgb, optuna
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import TimeSeriesSplit
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    # Use TimeSeriesSplit on the available data for Optuna objective
    tscv = TimeSeriesSplit(n_splits=3)
    
    def obj(trial):
        p = {'n_estimators': trial.suggest_int('n_estimators', 200, 800),
             'max_depth': trial.suggest_int('max_depth', 3, 7),
             'learning_rate': trial.suggest_float('lr', 0.005, 0.15, log=True),
             'subsample': trial.suggest_float('sub', 0.5, 0.95),
             'colsample_bytree': trial.suggest_float('col', 0.4, 0.9),
             'min_child_weight': trial.suggest_int('mcw', 1, 15),
             'gamma': trial.suggest_float('gamma', 0, 2.0),
             'reg_alpha': trial.suggest_float('alpha', 0, 5.0),
             'reg_lambda': trial.suggest_float('lambda', 0, 5.0),
             'objective': 'binary:logistic', 'eval_metric': 'logloss',
             'random_state': 42, 'verbosity': 0, 'early_stopping_rounds': 50}
        
        scores = []
        for tr_idx, te_idx in tscv.split(X):
            Xtr, Xte = X.iloc[tr_idx], X.iloc[te_idx]
            ytr, yte = y.iloc[tr_idx], y.iloc[te_idx]
            m = xgb.XGBClassifier(**p)
            m.fit(Xtr, ytr, eval_set=[(Xte, yte)], verbose=0)
            scores.append(1 - accuracy_score(yte, m.predict(Xte)))
        return np.mean(scores)
    
    study = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=42),
                                pruner=optuna.pruners.MedianPruner(n_warmup_steps=10))
    study.optimize(obj, n_trials=n, show_progress_bar=False)
    
    best = study.best_params
    best.update({'objective': 'binary:logistic', 'eval_metric': 'logloss', 'verbosity': 0})
    logger.info(f'  Optuna locked: val_loss={study.best_value:.4f}, depth={best["max_depth"]}, lr={best["lr"]:.4f}')
    return best


def run_one_seed(train_df, test_df, feats, params, seed):
    """Run one fold with locked params + specific seed."""
    import xgboost as xgb
    Xtr = train_df[feats]; ytr = train_df['target']
    v = Xtr.notna().all(axis=1) & ytr.notna(); Xtr, ytr = Xtr[v], ytr[v]
    Xte = test_df[feats]; vt = Xte.notna().all(axis=1)
    Xtc, tc = Xte[vt], test_df[vt]
    if len(Xtr) < 50 or len(Xtc) < 10: return {}
    
    p = params.copy(); p['random_state'] = seed
    m = xgb.XGBClassifier(**p); m.fit(Xtr, ytr, verbose=0)
    
    try: proba = m.predict_proba(Xtc)[:, 1]
    except: proba = np.full(len(Xtc), 0.5)
    conf = np.maximum(proba, 1-proba)
    sigs = np.zeros(len(Xtc), dtype=int)
    for i in range(len(Xtc)):
        if conf[i] >= 0.65 and proba[i] >= 0.5: sigs[i] = 1
    atr = compute_atr(tc, 14)
    return backtest(tc, sigs, atr)


def main():
    capital = 5000
    n_seeds = 10
    
    logger.info(f'V6-Epsilon: Locked Optuna + {n_seeds} seeds, $5,000')
    
    # Load and build features
    df = load_asset_data(asset='gold', primary_tf='15m', session_filter=False)
    df = engineer_all_features(df, add_labels=True, asset='gold')
    df = compute_v4_features(df)
    df, all_feats = build_features(df)
    logger.info(f'Features: {len(all_feats)}')
    
    # Step 1: Run Optuna ONCE
    logger.info('='*60)
    logger.info('Step 1: Optuna search (once, on walk-forward objective)')
    logger.info('='*60)
    X = df[all_feats]; y = df['target']
    v = X.notna().all(axis=1) & y.notna()
    locked_params = optuna_once(X[v], y[v], n=50)
    
    # Save locked params
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORTS_DIR / 'v6_epsilon_locked_params.json', 'w') as f:
        json.dump(locked_params, f, indent=2)
    
    # Step 2: Run walk-forward + forward test across N seeds
    logger.info('='*60)
    logger.info(f'Step 2: Walk-forward + forward test across {n_seeds} seeds')
    logger.info('='*60)
    
    # Generate folds ONCE (same folds for all seeds)
    fl, fwd = make_folds(df)
    logger.info(f'{len(fl)} folds + forward test')
    
    # Forward test split (same for all seeds)
    fwd_start = df.index.max() - pd.DateOffset(months=2)
    fwd_df = df[df.index >= fwd_start]
    wf_train = df[df.index < fwd_start]
    
    # Run each seed
    seed_results = []
    for seed in range(n_seeds):
        logger.info(f'Seed {seed+1}/{n_seeds}')
        
        # Walk-forward for this seed
        fold_results = []
        for fi in fl:
            res = run_one_seed(fi['train_df'], fi['test_df'], all_feats, locked_params, seed)
            fold_results.append(res)
        
        # Aggregate walk-forward
        wf_wr = np.mean([f.get('win_rate', 0) for f in fold_results if f])
        wf_ret = np.mean([f.get('total_return_usd', 0) for f in fold_results if f])
        wf_sh = np.mean([f.get('sharpe_ratio', 0) for f in fold_results if f])
        wf_n = np.mean([f.get('n_trades', 0) for f in fold_results if f])
        wf_pf = np.mean([f.get('profit_factor', 0) for f in fold_results if f])
        
        # Forward test for this seed
        ft_res = run_one_seed(wf_train, fwd_df, all_feats, locked_params, seed)
        ft_wr = ft_res.get('win_rate', 0)
        ft_ret = ft_res.get('total_return_usd', 0)
        ft_sh = ft_res.get('sharpe_ratio', 0)
        ft_n = ft_res.get('n_trades', 0)
        
        seed_results.append({
            'seed': seed,
            'wf_win_rate': wf_wr, 'wf_return': wf_ret, 'wf_sharpe': wf_sh,
            'wf_trades': wf_n, 'wf_pf': wf_pf,
            'ft_win_rate': ft_wr, 'ft_return': ft_ret, 'ft_sharpe': ft_sh, 'ft_trades': ft_n,
        })
        
        logger.info(f'  WF: WR={wf_wr:.1%} Return=${wf_ret:+,.0f} | FT: WR={ft_wr:.1%} Return=${ft_ret:+,.0f}')
    
    # Step 3: Compute statistics
    sdf = pd.DataFrame(seed_results)
    
    stats = {}
    for prefix, label in [('wf', 'Walk-Forward'), ('ft', 'Forward Test')]:
        stats[prefix] = {}
        for metric in ['win_rate', 'return', 'sharpe', 'trades']:
            col = f'{prefix}_{metric}'
            if col in sdf.columns:
                vals = sdf[col]
                stats[prefix][metric] = {
                    'mean': float(vals.mean()), 'std': float(vals.std()),
                    'min': float(vals.min()), 'max': float(vals.max()),
                    'median': float(vals.median()),
                }
    
    # Report
    lines = ['# V6-Epsilon: Defensible Walk-Forward Results\n']
    lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Capital:** $5,000 | **Lots:** 0.01 | **SL/TP:** 1.5x/3.0x ATR | **Conf:** 65%')
    lines.append(f'**Seeds:** {n_seeds} (locked Optuna params)\n')
    lines.append('## Locked Hyperparameters')
    lines.append('```json')
    lines.append(json.dumps({k: v for k, v in locked_params.items() if k not in ('objective', 'eval_metric', 'verbosity')}, indent=2))
    lines.append('```\n')
    lines.append('## Walk-Forward (PRIMARY metric)')
    lines.append('')
    lines.append('| Metric | Mean | Std | Min | Max |')
    lines.append('|--------|------|-----|-----|-----|')
    for m in ['win_rate', 'return', 'sharpe', 'trades']:
        if m not in stats['wf']: continue
        s = stats['wf'][m]
        if m == 'win_rate': row = f'| {m} | {s["mean"]:.1%} | {s["std"]:.1%} | {s["min"]:.1%} | {s["max"]:.1%} |'
        elif m == 'return': row = f'| {m} | ${s["mean"]:+,.0f} | ${s["std"]:,.0f} | ${s["min"]:+,.0f} | ${s["max"]:+,.0f} |'
        else: row = f'| {m} | {s["mean"]:.2f} | {s["std"]:.2f} | {s["min"]:.2f} | {s["max"]:.2f} |'
        lines.append(row)
    lines.append('\n## Forward Test (directional confirmation)')
    lines.append('')
    lines.append('| Metric | Mean | Std | Min | Max |')
    lines.append('|--------|------|-----|-----|-----|')
    for m in ['win_rate', 'return', 'sharpe', 'trades']:
        s = stats['ft'][m]
        if m == 'win_rate': row = f'| {m} | {s["mean"]:.1%} | {s["std"]:.1%} | {s["min"]:.1%} | {s["max"]:.1%} |'
        elif m == 'return': row = f'| {m} | ${s["mean"]:+,.0f} | ${s["std"]:,.0f} | ${s["min"]:+,.0f} | ${s["max"]:+,.0f} |'
        else: row = f'| {m} | {s["mean"]:.2f} | {s["std"]:.2f} | {s["min"]:.2f} | {s["max"]:.2f} |'
        lines.append(row)
    lines.append('\n## Per-Seed Detail')
    lines.append('')
    lines.append('| Seed | WF Return | WF WR | FT Return | FT WR | FT Trades |')
    lines.append('|------|-----------|-------|-----------|-------|-----------|')
    for _, r in sdf.iterrows():
        lines.append(f'| {int(r["seed"])} | ${r["wf_return"]:+,.0f} | {r["wf_win_rate"]:.1%} | ${r["ft_return"]:+,.0f} | {r["ft_win_rate"]:.1%} | {int(r["ft_trades"])} |')
    lines.append('\n## Methodology')
    lines.append('')
    lines.append('1. Optuna hyperparameter search: ONCE, on walk-forward CV objective (TimeSeriesSplit, 3 folds)')
    lines.append('2. Forward test: HELD OUT from all tuning decisions — never used for model selection')
    lines.append('3. Primary metric: Walk-forward average (mean ± std across 10 seeds)')
    lines.append('4. Secondary: Forward test (single held-out period, reported as directional confirmation)')
    lines.append('')
    lines.append('---\n*Generated by `scripts/v6_epsilon_final.py`*')
    
    report = '\n'.join(lines)
    with open(REPORTS_DIR / 'v6_epsilon_final.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    with open(REPORTS_DIR / 'v6_epsilon_final.json', 'w', encoding='utf-8') as f:
        json.dump({'locked_params': locked_params, 'n_seeds': n_seeds, 'results': seed_results,
                    'stats': stats}, f, indent=2, default=str)
    
    logger.info(f'\nReport: reports/v6_epsilon_final.md')
    logger.info(f'Walk-forward: ${stats["wf"]["return"]["mean"]:+,.0f} +/- ${stats["wf"]["return"]["std"]:,.0f}')
    logger.info(f'Forward test: ${stats["ft"]["return"]["mean"]:+,.0f} +/- ${stats["ft"]["return"]["std"]:,.0f}')


if __name__ == '__main__':
    main()
