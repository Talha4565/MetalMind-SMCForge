"""
Walk-forward PnL analysis and threshold tuning.
Runs models on the last 2 months of data and calculates real trading metrics.
"""

import sys
sys.path.insert(0, r'C:\Users\Talha\ml-signals')

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from data.loaders import load_asset_data
from features.pipeline import engineer_all_features

MODELS_DIR = Path(r'C:\Users\Talha\ml-signals\models')

RISK_PER_TRADE = 0.01
ACCOUNT_SIZE = 10000
SL_ATR_MULT = 1.5
TP_ATR_MULT = 3.0


def load_model(asset):
    path = MODELS_DIR / f'{asset}_enhanced_15m.pkl'
    with open(path, 'rb') as f:
        return pickle.load(f)


def run_backtest(asset, threshold=0.5, direction='both'):
    model = load_model(asset)
    feature_names = list(model.feature_names_in_)

    df = load_asset_data(asset=asset, primary_tf='15m', session_filter=True)
    df = engineer_all_features(df, add_labels=False, asset=df.columns[0] if False else asset)

    # Use only the features the model was trained on
    X = df[feature_names]

    proba = model.predict_proba(X)[:, 1]

    df['signal_prob'] = proba

    # Need ATR for SL/TP — compute from raw OHLC
    df['atr'] = df['high'].rolling(14).max() - df['low'].rolling(14).min()
    df['atr'] = df['atr'].fillna(method='ffill').fillna(50)

    # Last 2 months
    cutoff = df.index.max() - pd.Timedelta(days=60)
    recent = df[df.index >= cutoff].copy()

    trades = []
    equity = ACCOUNT_SIZE
    peak_equity = ACCOUNT_SIZE
    max_dd = 0

    for i in range(len(recent) - 1):
        row = recent.iloc[i]
        prob = row['signal_prob']
        price = row['close']
        atr = row['atr']

        if atr <= 0 or pd.isna(atr):
            continue

        if direction == 'both':
            if prob > threshold:
                signal = 1
            elif prob < (1 - threshold):
                signal = -1
            else:
                continue
        elif direction == 'long':
            signal = 1 if prob > threshold else 0
            if signal == 0:
                continue
        elif direction == 'short':
            signal = -1 if prob < (1 - threshold) else 0
            if signal == 0:
                continue
        else:
            continue

        sl = atr * SL_ATR_MULT
        tp = atr * TP_ATR_MULT

        next_row = recent.iloc[i + 1]
        next_high = next_row['high']
        next_low = next_row['low']

        if signal == 1:
            if next_low <= price - sl:
                pnl = -sl
            elif next_high >= price + tp:
                pnl = tp
            else:
                pnl = next_row['close'] - price
        else:
            if next_high >= price + sl:
                pnl = -sl
            elif next_low <= price - tp:
                pnl = tp
            else:
                pnl = price - next_row['close']

        risk_amount = ACCOUNT_SIZE * RISK_PER_TRADE
        position_size = risk_amount / sl if sl > 0 else 0
        pnl_dollar = pnl * position_size

        equity += pnl_dollar
        peak_equity = max(peak_equity, equity)
        dd = (peak_equity - equity) / peak_equity
        max_dd = max(max_dd, dd)

        trades.append({
            'time': recent.index[i],
            'signal': 'BUY' if signal == 1 else 'SELL',
            'prob': prob,
            'entry': price,
            'pnl': pnl_dollar,
            'equity': equity,
        })

    if not trades:
        return None

    trades_df = pd.DataFrame(trades)
    winners = trades_df[trades_df['pnl'] > 0]
    losers = trades_df[trades_df['pnl'] < 0]

    gross_profit = winners['pnl'].sum() if len(winners) > 0 else 0
    gross_loss = abs(losers['pnl'].sum()) if len(losers) > 0 else 0.01
    profit_factor = gross_profit / gross_loss

    win_rate = len(winners) / len(trades_df) * 100
    avg_win = winners['pnl'].mean() if len(winners) > 0 else 0
    avg_loss = losers['pnl'].mean() if len(losers) > 0 else 0

    return {
        'trades': len(trades_df),
        'win_rate': round(win_rate, 1),
        'pf': round(profit_factor, 2),
        'max_dd': round(max_dd * 100, 1),
        'pnl': round(trades_df['pnl'].sum(), 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'expectancy': round(trades_df['pnl'].mean(), 2),
        'final': round(equity, 2),
    }


def main():
    print("=" * 70)
    print("WALK-FORWARD PNL ANALYSIS (Last 2 Months)")
    print("=" * 70)

    for asset in ['gold', 'silver']:
        print(f"\n{'='*30} {asset.upper()} {'='*30}")

        for threshold in [0.5, 0.6, 0.7]:
            for direction in ['both', 'long', 'short']:
                try:
                    r = run_backtest(asset, threshold=threshold, direction=direction)
                    if r:
                        tag = ""
                        if r['pf'] >= 1.5 and r['max_dd'] < 15:
                            tag = " *** GOOD ***"
                        elif r['pf'] < 1.0:
                            tag = " ** LOSING **"
                        print(f"  T={threshold} {direction:5s} | Trades={r['trades']:3d} | Win%={r['win_rate']:5.1f} | PF={r['pf']:5.2f} | DD={r['max_dd']:5.1f}% | PnL=${r['pnl']:>8.2f} | AvgW=${r['avg_win']:>7.2f} | AvgL=${r['avg_loss']:>7.2f} | Exp=${r['expectancy']:>6.2f}{tag}")
                except Exception as e:
                    print(f"  T={threshold} {direction:5s} | ERROR: {e}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
