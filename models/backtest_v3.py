"""Backtest binary v3 model with trend filter — $5,000 initial."""
import pickle
import pandas as pd
import numpy as np
import logging

from models.experiment_binary_v3 import load_data, split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INITIAL_CAPITAL = 5000.0
RISK_PER_TRADE = 0.02
TP_PCT = 0.003
SL_PCT = 0.003
THRESHOLD = 0.65
COMMISSION_PCT = 0.0002
SPREAD_PCT = 0.0001  # 0.01% per side = $0.40 on $4,000 gold


def backtest():
    df = load_data()
    X_tr, y_tr, X_v, y_v, X_te, y_te, feats = split(df)

    with open("/app/models/gold_binary_v3_trend.pkl", "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]

    proba = model.predict_proba(X_te)[:, 1]
    preds_raw = (proba >= 0.5).astype(int)
    confident = np.abs(proba - 0.5) >= (THRESHOLD - 0.5)

    # Trend filter
    trend = X_te["trend_ema_cross"].values
    aligned = np.where(
        (preds_raw == 1) & (trend == 1), 1,
        np.where((preds_raw == 0) & (trend == 0), 0, -1)
    )
    preds = np.where(confident, aligned, -1)

    # Get close prices
    from data.loaders import MultiTimeframeLoader
    from features.pipeline import engineer_all_features
    loader = MultiTimeframeLoader("gold")
    loader.load_all_timeframes(["15m", "30m", "1h"])
    primary = loader.align_to_primary("15m")
    mask = ((primary.index.hour >= 8) & (primary.index.hour < 12)) | \
           ((primary.index.hour >= 13) & (primary.index.hour < 17))
    primary = primary.loc[mask]
    close_prices = primary["close"].reindex(X_te.index)

    capital = INITIAL_CAPITAL
    equity_curve = [capital]
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
            equity_curve.append(capital)
            continue

        price = close_prices.iloc[i]
        if pd.isna(price) or price <= 0:
            equity_curve.append(capital)
            continue

        risk_amount = capital * RISK_PER_TRADE

        if i + 1 < len(close_prices):
            next_price = close_prices.iloc[i + 1]
            if pd.isna(next_price):
                equity_curve.append(capital)
                continue

            if signal == 1:
                pnl_pct = (next_price - price) / price
            else:
                pnl_pct = (price - next_price) / price

            if pnl_pct >= TP_PCT:
                trade_pnl = risk_amount * (TP_PCT / SL_PCT)
            elif pnl_pct <= -SL_PCT:
                trade_pnl = -risk_amount
            else:
                trade_pnl = risk_amount * pnl_pct / SL_PCT

            # Costs: commission + spread (both sides)
            spread_cost = price * SPREAD_PCT * 2  # entry + exit spread
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
                "pnl": trade_pnl,
                "capital": capital,
            })

        max_equity = max(max_equity, capital)
        drawdown = (max_equity - capital) / max_equity
        max_drawdown = max(max_drawdown, drawdown)
        equity_curve.append(capital)

    total_trades = wins + losses
    win_rate = wins / total_trades if total_trades > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    expectancy = total_pnl / total_trades if total_trades > 0 else 0
    roi = (capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100

    print("=" * 60)
    print("BACKTEST — Binary v3 with TREND FILTER ($5,000)")
    print("=" * 60)
    print(f"Period:        {X_te.index.min().date()} to {X_te.index.max().date()}")
    print(f"Threshold:     {THRESHOLD}")
    print(f"Trend filter:  1h EMA-50/200 crossover")
    print(f"Spread:        $0.40/oz per side (0.01%)")
    print(f"Commission:    0.02% per trade")
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
        print("")

    if trades:
        print("Last 10 trades:")
        print("-" * 60)
        for t in trades[-10:]:
            ts = t["time"].strftime("%Y-%m-%d %H:%M")
            print(f"  {ts} | {t['signal']:4s} | ${t['price']:.2f} | PnL: ${t['pnl']:+.2f} | Equity: ${t['capital']:,.2f}")


if __name__ == "__main__":
    backtest()
