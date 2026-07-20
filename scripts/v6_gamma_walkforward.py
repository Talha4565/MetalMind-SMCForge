"""
V6-Gamma: Pruned Features (78) + Dual Confidence Threshold (65% vs 70%)

Based on V6-Alpha but removes 11 zero-importance SMC features.
Runs two scenarios: 65% and 70% confidence to find the sweet spot.

Pruned features: session_asia, fvg_bullish, fvg_bearish, fvg_size, bos_bearish,
liquidity_sweep_high, liquidity_sweep_low, order_block_bullish, order_block_bearish,
in_discount, higher_low

Standalone — does NOT touch the main project.

Usage:
    python scripts/v6_gamma_walkforward.py
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
from data.loaders import load_asset_data
from features.pipeline import engineer_all_features
from features.v4_features import compute_v4_features

logging.basicConfig(level=logging.INFO, format='%(asctime)s — %(levelname)s — %(message)s')
logger = logging.getLogger(__name__)

# Features to PRUNE (zero importance in V4 model)
PRUNED_FEATURES = [
    'session_asia', 'fvg_bullish', 'fvg_bearish', 'fvg_size', 'bos_bearish',
    'liquidity_sweep_high', 'liquidity_sweep_low', 'order_block_bullish', 'order_block_bearish',
    'in_discount', 'higher_low',
]


# ============================================================================
# ATR + BACKTEST (reuse from V6-Alpha)
# ============================================================================

def compute_atr(df, period=14):
    h, l, c = df['high'], df['low'], df['close']
    tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


@dataclass
class Trade:
    entry_time: pd.Timestamp; entry_price: float; exit_time: pd.Timestamp
    exit_price: float; sl_price: float; tp_price: float
    pnl_usd: float; hit_tp: bool; hit_sl: bool; bars_held: int


def backtest(df, signals, atr, lot_size=0.01, gold=3200, sl_m=1.5, tp_m=3.0,
             max_hold=24, comm=0.0001, slip=0.0002):
    trades, equity, eq_curve = [], 0.0, [0.0]
    for i in range(len(signals)):
        if signals[i] == 0:
            eq_curve.append(equity); continue
        if i + 1 >= len(df): break
        entry = df.iloc[i + 1]['open'] * (1 + slip)
        a = atr.iloc[i] if not np.isnan(atr.iloc[i]) else atr.dropna().mean()
        if np.isnan(a) or a <= 0:
            eq_curve.append(equity); continue
        sl_p, tp_p = entry - a * sl_m, entry + a * tp_m
        hit_tp = hit_sl = False; exit_p = entry; bars = 0
        for k in range(1, max_hold + 1):
            idx = i + 1 + k
            if idx >= len(df): break
            hi, lo = df.iloc[idx]['high'], df.iloc[idx]['low']
            bars = k
            if hi >= tp_p:
                exit_p = tp_p * (1 - slip); hit_tp = True; break
            elif lo <= sl_p:
                exit_p = sl_p * (1 - slip); hit_sl = True; break
        else:
            if i + 1 + max_hold < len(df):
                exit_p = df.iloc[i + 1 + max_hold]['close'] * (1 - slip)
        pnl = (exit_p - entry) * lot_size * 100 - entry * lot_size * 100 * comm * 2
        equity += pnl; eq_curve.append(equity)
        trades.append(Trade(df.index[i+1], entry, df.index[min(i+1+bars, len(df)-1)],
                           exit_p, sl_p, tp_p, pnl, hit_tp, hit_sl, bars))
    if not trades:
        return {}
    pnls = [t.pnl_usd for t in trades]
    n = len(trades)
    w = [t for t in trades if t.pnl_usd > 0]
    l = [t for t in trades if t.pnl_usd <= 0]
    wr = len(w) / n
    aw = np.mean([t.pnl_usd for t in w]) if w else 0
    al = np.mean([t.pnl_usd for t in l]) if l else 0
    pf = abs(aw / al) if al != 0 else 0
    total = sum(pnls)
    eq = pd.Series(eq_curve)
    dd = (eq - eq.cummax()).min()
    rets = pd.Series(pnls) / 5000 if len(pnls) > 1 else pd.Series([0])
    sh = (rets.mean() / rets.std()) * np.sqrt(252) if rets.std() != 0 else 0
    down = rets[rets < 0]
    ds = down.std() if len(down) > 0 else 0
    so = (rets.mean() / ds) * np.sqrt(252) if ds != 0 else 0
    return {
        'n_trades': n, 'win_rate': wr, 'avg_win': float(aw), 'avg_loss': float(al),
        'profit_factor': pf, 'total_return_usd': total, 'total_return_pct': (total/5000)*100,
        'max_drawdown_usd': float(dd), 'sharpe_ratio': sh, 'sortino_ratio': so,
        'tp_hits': sum(1 for t in trades if t.hit_tp), 'sl_hits': sum(1 for t in trades if t.hit_sl),
        'avg_bars_held': float(np.mean([t.bars_held for t in trades])),
    }


# ============================================================================
# FOLD GENERATOR
# ============================================================================

def folds(df, train_m, test_m, step_m, fwd_m):
    dates = df.index; end = dates.max()
    if fwd_m > 0:
        ft = end - pd.DateOffset(months=fwd_m)
        wf, fwd = df[dates < ft], df[dates >= ft]
    else:
        wf, fwd = df, pd.DataFrame()
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


# ============================================================================
# OPTUNA (run once)
# ============================================================================

def find_params(X, y, n=50):
    import xgboost as xgb, optuna
    from sklearn.metrics import accuracy_score
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sp = int(len(X) * 0.8)
    Xt, Xv = X.iloc[:sp], X.iloc[sp:]
    yt, yv = y.iloc[:sp], y.iloc[sp:]
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
        m = xgb.XGBClassifier(**p)
        m.fit(Xt, yt, eval_set=[(Xv, yv)], verbose=0)
        return 1 - accuracy_score(yv, m.predict(Xv))
    study = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=42),
                                pruner=optuna.pruners.MedianPruner(n_warmup_steps=10))
    study.optimize(obj, n_trials=n, show_progress_bar=False)
    best = study.best_params
    best.update({'objective': 'binary:logistic', 'eval_metric': 'logloss', 'random_state': 42, 'verbosity': 0})
    logger.info(f'  Best: val_loss={study.best_value:.4f}, depth={best["max_depth"]}, lr={best["lr"]:.4f}, n_est={best["n_estimators"]}')
    return best


# ============================================================================
# TRAIN + BACKTEST
# ============================================================================

def run_fold(train_df, test_df, feats, params, conf, cfg):
    import xgboost as xgb
    Xtr = train_df[feats]; ytr = train_df['target']
    v = Xtr.notna().all(axis=1) & ytr.notna()
    Xtr, ytr = Xtr[v], ytr[v]
    Xte = test_df[feats]; vt = Xte.notna().all(axis=1)
    Xtc, tc = Xte[vt], test_df[vt]
    if len(Xtr) < 50 or len(Xtc) < 10:
        return {}
    m = xgb.XGBClassifier(**params)
    m.fit(Xtr, ytr, verbose=0)
    try: proba = m.predict_proba(Xtc)[:, 1]
    except: proba = np.full(len(Xtc), 0.5)
    conf_arr = np.maximum(proba, 1 - proba)
    sigs = np.zeros(len(Xtc), dtype=int)
    for i in range(len(Xtc)):
        if conf_arr[i] >= conf and proba[i] >= 0.5: sigs[i] = 1
    atr = compute_atr(tc, cfg['atr_period'])
    return backtest(tc, sigs, atr, lot_size=cfg['lot_size'], gold=cfg['gold_price_approx'],
                    sl_m=cfg['atr_sl_multiplier'], tp_m=cfg['atr_tp_multiplier'],
                    max_hold=cfg['max_hold_bars'], comm=cfg['commission_pct'], slip=cfg['slippage_pct'])


# ============================================================================
# MAIN
# ============================================================================

def main():
    cfg = {
        'lot_size': 0.01, 'gold_price_approx': 3200,
        'atr_sl_multiplier': 1.5, 'atr_tp_multiplier': 3.0, 'atr_period': 14,
        'confidence_threshold': 0.65, 'max_hold_bars': 24,
        'commission_pct': 0.0001, 'slippage_pct': 0.0002,
        'train_months': 2, 'test_months': 1, 'step_months': 1, 'forward_test_months': 2,
        'optuna_trials': 50,
    }
    capital = 5000

    logger.info('V6-Gamma: Pruned features (78) + Dual confidence (65% vs 70%)')
    logger.info(f'Pruning {len(PRUNED_FEATURES)} zero-importance SMC features')

    # Load data
    df = load_asset_data(asset='gold', primary_tf='15m', session_filter=False)
    df = engineer_all_features(df, add_labels=True, asset='gold')
    df = compute_v4_features(df)

    # Get feature list and prune
    with open('models/gold_regression_system.pkl', 'rb') as f:
        base_feats = pickle.load(f)['features']
    pruned_feats = [f for f in base_feats if f not in PRUNED_FEATURES]
    logger.info(f'Features: {len(base_feats)} -> {len(pruned_feats)} (pruned {len(PRUNED_FEATURES)})')

    # Find best params (once)
    X = df[pruned_feats]; y = df['target']
    v = X.notna().all(axis=1) & y.notna()
    params = find_params(X[v], y[v], cfg['optuna_trials'])

    all_results = {}
    for conf in [0.65, 0.70]:
        tag = f'Gamma-{int(conf*100)}'
        logger.info(f'\n{"="*60}\n{tag}: confidence={conf:.0%}\n{"="*60}')

        fl, fwd = folds(df, cfg['train_months'], cfg['test_months'], cfg['step_months'], cfg['forward_test_months'])
        fold_res = []
        for fi in fl:
            res = run_fold(fi['train_df'], fi['test_df'], pruned_feats, params, conf, cfg)
            r = {**fi, **res}
            r.pop('train_df', None); r.pop('test_df', None)
            fold_res.append(r)
            logger.info(f'  Fold {fi["fold"]}: WR={res.get("win_rate",0):.1%} Return=${res.get("total_return_usd",0):+,.0f} Trades={res.get("n_trades",0)}')

        agg = {}
        for k in ['win_rate','profit_factor','sharpe_ratio','total_return_usd','n_trades']:
            vals = [f.get(k,0) for f in fold_res if k in f and np.isfinite(f.get(k,0))]
            agg[k] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))} if vals else {'mean':0,'std':0}

        from data.loaders import train_val_test_split
        tr, va, te = train_val_test_split(df, 0.70, 0.15, 0.15)
        ss = run_fold(tr, te, pruned_feats, params, conf, cfg)

        ft = {}
        if len(fwd) > 0:
            wtr = df[df.index < fwd.index.min()]
            ft = run_fold(wtr, fwd, pruned_feats, params, conf, cfg)

        all_results[tag] = {'folds': fold_res, 'aggregated': agg, 'single': ss, 'forward': ft}
        logger.info(f'  SS: ${ss.get("total_return_usd",0):+,.0f} | WF avg: ${agg.get("total_return_usd",{}).get("mean",0):+,.0f} | FT: ${ft.get("total_return_usd",0):+,.0f}')

    # Also run V6-Alpha baseline (89 features, 65%) for comparison
    logger.info(f'\n{"="*60}\nAlpha-Baseline: 89 features, 65%\n{"="*60}')
    fl2, fwd2 = folds(df, cfg['train_months'], cfg['test_months'], cfg['step_months'], cfg['forward_test_months'])
    params_alpha = find_params(X[v], y[v], cfg['optuna_trials'])
    fold_alpha = []
    for fi in fl2:
        res = run_fold(fi['train_df'], fi['test_df'], base_feats, params_alpha, 0.65, cfg)
        r = {**fi, **res}; r.pop('train_df', None); r.pop('test_df', None)
        fold_alpha.append(r)
    agg_a = {}
    for k in ['win_rate','profit_factor','sharpe_ratio','total_return_usd','n_trades']:
        vals = [f.get(k,0) for f in fold_alpha if k in f and np.isfinite(f.get(k,0))]
        agg_a[k] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))} if vals else {'mean':0,'std':0}
    ss_a = run_fold(tr, te, base_feats, params_alpha, 0.65, cfg)
    ft_a = run_fold(wtr, fwd, base_feats, params_alpha, 0.65, cfg) if len(fwd) > 0 else {}
    all_results['Alpha-65'] = {'folds': fold_alpha, 'aggregated': agg_a, 'single': ss_a, 'forward': ft_a}

    # Report
    lines = ['# V6-Gamma Comparison — Pruned Features (78)\n']
    lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Capital:** ${capital:,.0f} | **Lots:** 0.01 | **SL:** 1.5x ATR | **TP:** 3.0x ATR')
    lines.append(f'**Pruned:** {len(PRUNED_FEATURES)} features removed (zero importance in V4)\n')
    lines.append('| Scenario | Features | Conf | Single-Split | Walk-Forward | Forward Test |')
    lines.append('|----------|----------|------|-------------|-------------|-------------|')
    for tag, data in all_results.items():
        ss_r = data['single'].get('total_return_usd', 0)
        wf_r = data['aggregated'].get('total_return_usd', {}).get('mean', 0)
        ft_r = data['forward'].get('total_return_usd', 0)
        n_f = len(base_feats) if 'Alpha' in tag else len(pruned_feats)
        c = 0.65 if '65' in tag else 0.70
        lines.append(f'| {tag} | {n_f} | {c:.0%} | ${ss_r:+,.0f} | ${wf_r:+,.0f} | ${ft_r:+,.0f} |')

    lines.append('\n---\n*Generated by `scripts/v6_gamma_walkforward.py`*')
    report = '\n'.join(lines)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORTS_DIR / 'v6_gamma_comparison.md', 'w', encoding='utf-8') as f:
        f.write(report)
    with open(REPORTS_DIR / 'v6_gamma_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=str)

    logger.info(f'\nReport: reports/v6_gamma_comparison.md')
    for tag, data in all_results.items():
        ss = data['single'].get('total_return_usd', 0)
        wf = data['aggregated'].get('total_return_usd', {}).get('mean', 0)
        ft = data['forward'].get('total_return_usd', 0)
        logger.info(f'{tag}: SS=${ss:+,.0f} WF=${wf:+,.0f} FT=${ft:+,.0f}')


if __name__ == '__main__':
    main()
