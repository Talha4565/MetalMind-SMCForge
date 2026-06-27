"""
Walk-forward PnL analysis: 6 months, monthly breakdown.
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


def run_monthly(asset, threshold=0.7):
    model = load_model(asset)
    feature_names = list(model.feature_names_in_)

    df = load_asset_data(asset=asset, primary_tf='15m', session_filter=True)
    df = engineer_all_features(df, add_labels=False, asset=asset)

    X = df[feature_names]
    proba = model.predict_proba(X)[:, 1]
    df['signal_prob'] = proba
    df['atr'] = df['high'].rolling(14).max() - df['low'].rolling(14).min()
    df['atr'] = df['atr'].ffill().fillna(50)

    # Last 6 months
    cutoff = df.index.max() - pd.Timedelta(days=180)
    recent = df[df.index >= cutoff].copy()
    recent['month'] = recent.index.to_period('M')

    results = []
    cumulative_pnl = 0

    for month, group in recent.groupby('month'):
        trades = []
        equity = ACCOUNT_SIZE
        peak = ACCOUNT_SIZE
        max_dd = 0

        for i in range(len(group) - 1):
            row = group.iloc[i]
            prob = row['signal_prob']
            price = row['close']
            atr = row['atr']

            if atr <= 0 or pd.isna(atr):
                continue

            # Both directions at T=0.7
            if prob > threshold:
                signal = 1
            elif prob < (1 - threshold):
                signal = -1
            else:
                continue

            sl = atr * SL_ATR_MULT
            tp = atr * TP_ATR_MULT

            nxt = group.iloc[i + 1]

            if signal == 1:
                if nxt['low'] <= price - sl:
                    pnl = -sl
                elif nxt['high'] >= price + tp:
                    pnl = tp
                else:
                    pnl = nxt['close'] - price
            else:
                if nxt['high'] >= price + sl:
                    pnl = -sl
                elif nxt['low'] <= price - tp:
                    pnl = tp
                else:
                    pnl = price - nxt['close']

            risk = ACCOUNT_SIZE * RISK_PER_TRADE
            pos = risk / sl if sl > 0 else 0
            pnl_dollar = pnl * pos

            equity += pnl_dollar
            peak = max(peak, equity)
            dd = (peak - equity) / peak
            max_dd = max(max_dd, dd)

            trades.append({
                'signal': 'BUY' if signal == 1 else 'SELL',
                'prob': prob,
                'pnl': pnl_dollar,
            })

        if not trades:
            results.append({
                'month': str(month),
                'trades': 0, 'wins': 0, 'losses': 0,
                'win_rate': 0, 'pf': 0, 'pnl': 0,
                'max_dd': 0, 'avg_win': 0, 'avg_loss': 0,
            })
            continue

        tdf = pd.DataFrame(trades)
        wins = tdf[tdf['pnl'] > 0]
        losses = tdf[tdf['pnl'] < 0]

        gp = wins['pnl'].sum() if len(wins) > 0 else 0
        gl = abs(losses['pnl'].sum()) if len(losses) > 0 else 0.01
        pf = gp / gl

        cumulative_pnl += tdf['pnl'].sum()

        results.append({
            'month': str(month),
            'trades': len(tdf),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': round(len(wins) / len(tdf) * 100, 1),
            'pf': round(pf, 2),
            'pnl': round(tdf['pnl'].sum(), 2),
            'max_dd': round(max_dd * 100, 1),
            'avg_win': round(wins['pnl'].mean(), 2) if len(wins) > 0 else 0,
            'avg_loss': round(losses['pnl'].mean(), 2) if len(losses) > 0 else 0,
        })

    return results, cumulative_pnl


def main():
    print("=" * 90)
    print("WALK-FORWARD 6-MONTH ANALYSIS — Monthly Breakdown (Threshold=0.7)")
    print("=" * 90)

    for asset in ['gold', 'silver']:
        print(f"\n{'='*90}")
        print(f"  {asset.upper()}")
        print(f"{'='*90}")

        results, cum_pnl = run_monthly(asset, threshold=0.7)

        total_trades = sum(r['trades'] for r in results)
        total_wins = sum(r['wins'] for r in results)
        total_losses = sum(r['losses'] for r in results)
        overall_wr = round(total_wins / total_trades * 100, 1) if total_trades > 0 else 0
        avg_pf = round(sum(r['pf'] for r in results if r['pf'] > 0) / max(1, sum(1 for r in results if r['pf'] > 0)), 2)
        worst_dd = max(r['max_dd'] for r in results) if results else 0

        print(f"\n  {'Month':<10} {'Trades':>7} {'Wins':>6} {'Losses':>7} {'Win%':>7} {'PF':>7} {'PnL':>10} {'MaxDD':>7} {'AvgW':>8} {'AvgL':>8}")
        print(f"  {'-'*10} {'-'*7} {'-'*6} {'-'*7} {'-'*7} {'-'*7} {'-'*10} {'-'*7} {'-'*8} {'-'*8}")

        for r in results:
            pnl_str = f"${r['pnl']:>9.2f}"
            marker = ""
            if r['pf'] >= 3.0:
                marker = " *"
            elif r['pf'] < 1.0 and r['trades'] > 0:
                marker = " !"
            print(f"  {r['month']:<10} {r['trades']:>7} {r['wins']:>6} {r['losses']:>7} {r['win_rate']:>6.1f}% {r['pf']:>7.2f} {pnl_str} {r['max_dd']:>6.1f}% ${r['avg_win']:>7.2f} ${r['avg_loss']:>7.2f}{marker}")

        print(f"  {'-'*10} {'-'*7} {'-'*6} {'-'*7} {'-'*7} {'-'*7} {'-'*10} {'-'*7} {'-'*8} {'-'*8}")
        print(f"  {'TOTAL':<10} {total_trades:>7} {total_wins:>6} {total_losses:>7} {overall_wr:>6.1f}% {avg_pf:>7.2f} ${cum_pnl:>9.2f} {worst_dd:>6.1f}%")

        print(f"\n  SUMMARY: {total_trades} trades over 6 months | {overall_wr}% win rate | PF={avg_pf} | Total PnL=${cum_pnl:.2f} | Worst DD={worst_dd}%")
        if avg_pf >= 2.0 and worst_dd < 5:
            print(f"  VERDICT: PROFITABLE SYSTEM")
        elif avg_pf >= 1.0:
            print(f"  VERDICT: MARGINAL — needs optimization")
        else:
            print(f"  VERDICT: LOSING — do not trade")

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()
