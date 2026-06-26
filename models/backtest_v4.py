"""Backtest v4 — dynamic TP/SL from regression models."""
import pickle
import pandas as pd
import numpy as np
import logging

from models.experiment_regression import load_data, split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INITIAL_CAPITAL = 5000.0
RISK_PER_TRADE = 0.02
THRESHOLD = 0.65
COMMISSION_PCT = 0.0002
SPREAD_PCT = 0.0001


def backtest():
    df = load_data()
    X_tr, y_tr, tp_tr, sl_tr, X_v, y_v, tp_v, sl_v, X_te, y_te, tp_te, sl_te, feats = split(df)

    with open("/app/models/gold_regression_system.pkl", "rb") as f:
        saved = pickle.load(f)

    dir_model = saved["direction_model"]
    tp_model = saved["tp_model"]
    sl_model = saved["sl_model"]

    # Predictions
    proba = dir_model.predict_proba(X_te[feats])[:, 1]
    confident = np.abs(proba - 0.5) >= 0.15
    preds_raw = (proba >= 0.5).astype(int)

    # Trend filter
    if "trend_ema_cross" in X_te.columns:
        trend = X_te["trend_ema_cross"].values
        aligned = np.where(
            (preds_raw == 1) & (trend == 1), 1,
            np.where((preds_raw == 0) & (trend == 0), 0, -1)
        )
    else:
        aligned = preds_raw
    preds = np.where(confident, aligned, -1)

    # Dynamic TP/SL
    tp_pred = np.clip(tp_model.predict(X_te[feats]), 0.003, 0.02)   # 0.3% - 2% TP
    sl_pred = np.clip(sl_model.predict(X_te[feats]), 0.00375, 0.0075)  # 15-30 pips SL

    # Get close prices
    from data.loaders import MultiTimeframeLoader
    loader = MultiTimeframeLoader("gold")
    loader.load_all_timeframes(["15m", "30m", "1h"])
    primary = loader.align_to_primary("15m")
    mask = ((primary.index.hour >= 8) & (primary.index.hour < 12)) | \
           ((primary.index.hour >= 13) & (primary.index.hour < 17))
    primary = primary.loc[mask]
    close_prices = primary["close"].reindex(X_te.index)

    capital = INITIAL_CAPITAL
    trades = []
    wins = 0
    losses = 0
    total_pnl = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    max_equity = capital
    max_drawdown = 0.0

    for i in range(len(preds)):
        signal = preds[i]
        if signal == -1:
            continue

        price = close_prices.iloc[i]
        if pd.isna(price) or price <= 0:
            continue

        # Dynamic TP/SL
        tp_pct = tp_pred[i]
        sl_pct = sl_pred[i]
        risk_amount = capital * RISK_PER_TRADE

        if i + 1 < len(close_prices):
            next_price = close_prices.iloc[i + 1]
            if pd.isna(next_price):
                continue

            if signal == 1:
                pnl_pct = (next_price - price) / price
            else:
                pnl_pct = (price - next_price) / price

            # Check if TP or SL hit
            if pnl_pct >= tp_pct:
                trade_pnl = risk_amount * (tp_pct / sl_pct)
            elif pnl_pct <= -sl_pct:
                trade_pnl = -risk_amount
            else:
                trade_pnl = risk_amount * pnl_pct / sl_pct

            # Costs
            spread_cost = price * SPREAD_PCT * 2
            commission = capital * COMMISSION_PCT
            trade_pnl -= (commission + spread_cost)

            capital += trade_pnl
            total_pnl += trade_pnl

            if trade_pnl > 0:
                gross_profit += trade_pnl
                wins += 1
            else:
                gross_loss += abs(trade_pnl)
                losses += 1

            trades.append({
                "time": X_te.index[i],
                "signal": "BUY" if signal == 1 else "SELL",
                "price": price,
                "tp_pct": tp_pct,
                "sl_pct": sl_pct,
                "pnl": trade_pnl,
                "capital": capital,
            })

        max_equity = max(max_equity, capital)
        drawdown = (max_equity - capital) / max_equity
        max_drawdown = max(max_drawdown, drawdown)

    total_trades = wins + losses
    win_rate = wins / total_trades if total_trades > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    expectancy = total_pnl / total_trades if total_trades > 0 else 0
    roi = (capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100

    print("=" * 60)
    print("BACKTEST — v4 Dynamic TP/SL + Trend Filter ($5,000)")
    print("=" * 60)
    print(f"Period:        {X_te.index.min().date()} to {X_te.index.max().date()}")
    print(f"Threshold:     {THRESHOLD}")
    print(f"TP model:      dynamic (0.3%-2.0%)")
    print(f"SL model:      dynamic (15-30 pips = 0.375%-0.75%)")
    print(f"Spread:        $0.40/oz per side")
    print(f"")
    print(f"--- Performance ---")
    print(f"Initial:       ${INITIAL_CAPITAL:,.2f}")
    print(f"Final:         ${capital:,.2f}")
    print(f"Net PnL:       ${total_pnl:,.2f}")
    print(f"ROI:           {roi:+.2f}%")
    print(f"")
    print(f"--- Trade Stats ---")
    print(f"Total trades:  {total_trades}")
    print(f"  BUY taken:   {sum(1 for t in trades if t['signal'] == 'BUY')}")
    print(f"  SELL taken:  {sum(1 for t in trades if t['signal'] == 'SELL')}")
    print(f"Wins:          {wins} ({win_rate:.1%})")
    print(f"Losses:        {losses} ({1-win_rate:.1%})")
    print(f"Avg TP used:   {np.mean([t['tp_pct'] for t in trades]):.4f} ({np.mean([t['tp_pct'] for t in trades])*100:.2f}%)")
    print(f"Avg SL used:   {np.mean([t['sl_pct'] for t in trades]):.4f} ({np.mean([t['sl_pct'] for t in trades])*100:.2f}%)")
    print(f"")
    print(f"--- Risk Metrics ---")
    print(f"Profit factor: {profit_factor:.2f}")
    print(f"Max drawdown:  {max_drawdown:.2%}")
    print(f"Expectancy:    ${expectancy:,.2f} per trade")
    print(f"")

    if trades:
        tdf = pd.DataFrame(trades)
        tdf["month"] = tdf["time"].dt.to_period("M")
        monthly = tdf.groupby("month").agg(
            trades=("pnl", "count"),
            wins=("pnl", lambda x: (x > 0).sum()),
            pnl=("pnl", "sum"),
        )
        monthly["win_rate"] = monthly["wins"] / monthly["trades"]
        print("Monthly breakdown:")
        print(monthly.to_string())

    if trades:
        print("\nLast 10 trades:")
        print("-" * 70)
        for t in trades[-10:]:
            ts = t["time"].strftime("%Y-%m-%d %H:%M")
            print(f"  {ts} | {t['signal']:4s} | ${t['price']:.2f} | TP={t['tp_pct']*100:.2f}% SL={t['sl_pct']*100:.2f}% | PnL: ${t['pnl']:+.2f}")


if __name__ == "__main__":
    backtest()
