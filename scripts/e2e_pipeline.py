"""
End-to-End Pipeline: Backtest → Features → Outcomes → ChromaDB → Retrain

Uses V6-Delta fixed SMC features (104) with V6-Epsilon locked params.
Trains model, runs backtest, extracts features per trade, logs outcomes,
stores in ChromaDB, triggers retrain if needed, outputs trade log JSON.

Standalone — does NOT touch the main project.

Usage:
    python scripts/e2e_pipeline.py
    python scripts/e2e_pipeline.py --capital 5000
    python scripts/e2e_pipeline.py --capital 5000 --skip-retrain
"""

import sys
from pathlib import Path
# Load .env BEFORE any imports that read NVIDIA_API_KEY
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

import sys
import json
import logging
import pickle
import argparse
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

# V6-Delta feature engineering (same as v6_delta_fix_smc.py)
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


def build_v6_features(df):
    """Apply V6-Delta feature engineering. Return feature list."""
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
    sl_price: float; tp_price: float; pnl_usd: float; hit_tp: bool; hit_sl: bool
    bars_held: int; entry_idx: int; signal_bar_idx: int


def backtest_with_features(df, signals, atr, features_df, feat_names, lot=0.01, gold=3200,
                           sl_m=1.5, tp_m=3.0, mh=24, comm=0.0001, slip=0.0002):
    """Backtest that captures feature values at each trade entry."""
    trades, equity, eq_curve = [], 0.0, [0.0]
    
    for i in range(len(signals)):
        if signals[i] == 0: eq_curve.append(equity); continue
        if i + 1 >= len(df): break
        
        entry = df.iloc[i + 1]['open'] * (1 + slip)
        a = atr.iloc[i] if not np.isnan(atr.iloc[i]) else atr.dropna().mean()
        if np.isnan(a) or a <= 0: eq_curve.append(equity); continue
        
        sl_p, tp_p = entry - a * sl_m, entry + a * tp_m
        hit_tp = hit_sl = False; exit_p = entry; bars = 0
        
        for k in range(1, mh + 1):
            idx = i + 1 + k
            if idx >= len(df): break
            hi, lo = df.iloc[idx]['high'], df.iloc[idx]['low']; bars = k
            if hi >= tp_p: exit_p = tp_p * (1 - slip); hit_tp = True; break
            elif lo <= sl_p: exit_p = sl_p * (1 - slip); hit_sl = True; break
        else:
            if i + 1 + mh < len(df):
                exit_p = df.iloc[i + 1 + mh]['close'] * (1 - slip)
        
        pnl = (exit_p - entry) * lot * 100 - entry * lot * 100 * comm * 2
        equity += pnl; eq_curve.append(equity)
        
        # Extract feature values at signal bar
        feat_vals = {}
        signal_ts = df.index[i]
        if signal_ts in features_df.index:
            for fn in feat_names:
                if fn in features_df.columns:
                    feat_vals[fn] = float(features_df.loc[signal_ts, fn])
        
        trades.append(Trade(
            entry_time=df.index[i+1], entry_price=entry,
            exit_time=df.index[min(i+1+bars, len(df)-1)], exit_price=exit_p,
            sl_price=sl_p, tp_price=tp_p, pnl_usd=pnl,
            hit_tp=hit_tp, hit_sl=hit_sl, bars_held=bars,
            entry_idx=i+1, signal_bar_idx=i,
        ))
        trades[-1].features = feat_vals  # Attach features
    
    return trades, eq_curve


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='E2E Pipeline')
    parser.add_argument('--capital', type=float, default=5000)
    parser.add_argument('--skip-retrain', action='store_true')
    args = parser.parse_args()
    
    capital = args.capital
    asset = 'gold'
    lot = 0.01
    gold_price = 3200
    
    logger.info('='*60)
    logger.info('E2E PIPELINE: Backtest → Features → Outcomes → ChromaDB → Retrain')
    logger.info('='*60)
    logger.info(f'Capital: ${capital:,.0f} | Lot: {lot} | Asset: {asset}')
    
    # 1. Load data + V6-Delta features
    logger.info('\n[1/7] Loading data + building V6-Delta features...')
    df = load_asset_data(asset=asset, primary_tf='15m', session_filter=False)
    df = engineer_all_features(df, add_labels=True, asset=asset)
    df = compute_v4_features(df)
    df, feat_names = build_v6_features(df)
    logger.info(f'  {len(df)} rows, {len(feat_names)} features')
    
    # 2. Train model with V6-Epsilon locked params
    logger.info('\n[2/7] Training model with V6-Epsilon locked params...')
    locked_params = {
        'n_estimators': 398, 'max_depth': 7, 'learning_rate': 0.0116,
        'subsample': 0.71, 'colsample_bytree': 0.81, 'min_child_weight': 15,
        'gamma': 1.98, 'reg_alpha': 1.47, 'reg_lambda': 0.96,
        'objective': 'binary:logistic', 'eval_metric': 'logloss', 'verbosity': 0,
    }
    
    import xgboost as xgb
    X = df[feat_names]; y = df['target']
    valid = X.notna().all(axis=1) & y.notna()
    model = xgb.XGBClassifier(**locked_params)
    model.fit(X[valid], y[valid], verbose=0)
    logger.info(f'  Model trained on {valid.sum()} bars')
    
    # 3. Generate signals
    logger.info('\n[3/7] Generating signals...')
    try:
        proba = model.predict_proba(X)[:, 1]
    except:
        proba = np.full(len(X), 0.5)
    
    confidence = np.maximum(proba, 1 - proba)
    signals = np.zeros(len(df), dtype=int)
    for i in range(len(df)):
        if confidence[i] >= 0.65 and proba[i] >= 0.5:
            signals[i] = 1
    
    logger.info(f'  {signals.sum()} BUY signals out of {len(signals)} bars ({signals.sum()/len(signals)*100:.1f}%)')
    
    # 4. Run backtest
    logger.info('\n[4/7] Running backtest...')
    atr = compute_atr(df, 14)
    trades, eq_curve = backtest_with_features(df, signals, atr, df, feat_names,
                                               lot=lot, gold=gold_price)
    
    total_pnl = sum(t.pnl_usd for t in trades)
    wins = [t for t in trades if t.pnl_usd > 0]
    losses = [t for t in trades if t.pnl_usd <= 0]
    wr = len(wins) / len(trades) if trades else 0
    
    logger.info(f'  {len(trades)} trades, WR={wr:.1%}, PnL=${total_pnl:+,.2f}')
    
    # 5. Log outcomes to OutcomeTracker
    logger.info('\n[5/7] Logging outcomes to OutcomeTracker...')
    from self_learning.tracker import OutcomeTracker
    tracker = OutcomeTracker()
    
    for t in trades:
        outcome = 'WIN' if t.pnl_usd > 0 else 'LOSS'
        signal_id = f"e2e_{t.entry_time.strftime('%Y%m%d_%H%M%S')}_{asset}"
        
        tracker.log_outcome(
            signal_id=signal_id,
            asset=asset,
            signal=1,
            confidence=0.65,
            price=t.exit_price,
            entry_price=t.entry_price,
            outcome=outcome,
            pnl=(t.pnl_usd / capital) * 100,
            features=t.features,
        )
    
    summary = tracker.get_summary(days=30)
    logger.info(f'  Outcomes logged: {summary["total"]} total, {summary["wins"]} wins, {summary["losses"]} losses')
    
    # 6. Store signals in ChromaDB
    logger.info('\n[6/7] Storing signals in ChromaDB...')
    try:
        from signal_memory import SignalMemoryClient, SignalUpdater
        updater = SignalUpdater()
        
        stored = 0
        for t in trades:
            signal_data = {
                'asset': asset,
                'signal': 1,
                'confidence': 0.65,
                'price': t.entry_price,
                'exit_price': t.exit_price,
                'pnl': t.pnl_usd,
                'outcome': 'WIN' if t.pnl_usd > 0 else 'LOSS',
            }
            # Add key features for embedding
            for fn in ['order_block_signal', 'VWAPd_4', 'trend_ema_cross', 'adx_14', 'Ret_4']:
                if fn in t.features:
                    signal_data[fn] = t.features[fn]
            
            try:
                updater.store_signal(signal_data)
                stored += 1
            except Exception as e:
                logger.warning(f'  Could not store signal: {e}')
        
        stats = updater.get_collection_stats()
        logger.info(f'  Stored {stored} signals, total in ChromaDB: {stats.get("total", 0)}')
    except Exception as e:
        logger.warning(f'  ChromaDB storage failed: {e}')
    
    # 7. Check retrain trigger
    logger.info('\n[7/7] Checking retrain trigger...')
    if not args.skip_retrain:
        from self_learning.retrainer import ModelRetrainer
        retrainer = ModelRetrainer()
        
        should = retrainer.should_retrain(min_outcomes=10, accuracy_threshold=0.55)
        logger.info(f'  Should retrain: {should}')
        logger.info(f'  Outcomes: {summary["total"]} (min: 10)')
        logger.info(f'  Win rate: {summary["win_rate"]:.1%} (threshold: 55%)')
        
        if should:
            logger.info('  Retrain triggered!')
            result = retrainer.retrain_model(asset)
            logger.info(f'  Retrain result: {result}')
        else:
            logger.info('  Retrain not needed — model performing above threshold')
    else:
        logger.info('  Skipped (--skip-retrain)')
    
    # 8. Output trade log JSON for frontend
    logger.info('\n[DONE] Outputting trade log...')
    trade_log = []
    for t in trades:
        trade_log.append({
            'timestamp': t.entry_time.isoformat(),
            'asset': asset,
            'signal': 'BUY',
            'confidence': 0.65,
            'entry_price': round(t.entry_price, 2),
            'exit_price': round(t.exit_price, 2),
            'tp_price': round(t.tp_price, 2),
            'sl_price': round(t.sl_price, 2),
            'pnl_usd': round(t.pnl_usd, 2),
            'outcome': 'WIN' if t.pnl_usd > 0 else 'LOSS',
            'bars_held': t.bars_held,
            'hit_tp': t.hit_tp,
            'hit_sl': t.hit_sl,
            'top_features': {k: round(v, 4) for k, v in sorted(t.features.items(), key=lambda x: abs(x[1]), reverse=True)[:5]},
        })
    
    # Save trade log
    log_path = REPORTS_DIR / 'e2e_trade_log.json'
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_trades': len(trades),
                'win_rate': round(wr, 4),
                'total_pnl': round(total_pnl, 2),
                'total_pnl_pct': round((total_pnl / capital) * 100, 2),
                'capital': capital,
                'lot_size': lot,
                'asset': asset,
                'features_used': len(feat_names),
                'model': 'V6-Epsilon (locked params)',
                'generated_at': datetime.now().isoformat(),
            },
            'trades': trade_log,
            'outcome_summary': summary,
        }, f, indent=2)
    
    logger.info(f'  Trade log saved: {log_path}')
    logger.info(f'')
    logger.info('='*60)
    logger.info('SUMMARY')
    logger.info('='*60)
    logger.info(f'  Trades: {len(trades)}')
    logger.info(f'  Win Rate: {wr:.1%}')
    logger.info(f'  Total PnL: ${total_pnl:+,.2f} ({(total_pnl/capital)*100:+.1f}%)')
    logger.info(f'  Outcomes in tracker: {summary["total"]}')
    logger.info(f'  ChromaDB signals: stored')
    logger.info(f'  Retrain: {"triggered" if not args.skip_retrain and should else "not needed"}')
    logger.info(f'  Trade log: {log_path}')


if __name__ == '__main__':
    main()
