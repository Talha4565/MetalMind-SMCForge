"""Backtest the binary v2 model on test set with $5,000 initial capital."""
import pickle
import pandas as pd
import numpy as np
import logging

from models.experiment_binary_v2 import load_data, split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INITIAL_CAPITAL = 5000.0
RISK_PER_TRADE = 0.02  # 2% risk per trade
TP_PCT = 0.003  # 0.3% take profit
SL_PCT = 0.003  # 0.3% stop loss
THRESHOLD = 0.65
COMMISSION_PCT = 0.0002  # 0.02% per trade (round trip)


def backtest():
    df = load_data()
    X_tr, y_tr, X_v, y_v, X_te, y_te, feats = split(df)

    with open("/app/models/gold_binary_v2.pkl", "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]

    proba = model.predict_proba(X_te)[:, 1]
    preds_raw = (proba >= 0.5).astype(int)
    confident = np.abs(proba - 0.5) >= 0.15
    preds = np.where(confident, preds_raw, -1)

    # Get actual prices from the original data
    loader_data = load_data.__wrapped__ if hasattr(load_data, '__wrapped__') else None
    # We need the close prices — reload from the aligned data
    from data.loaders import MultiTimeframeLoader
    from features.pipeline import engineer_all_features

    loader = MultiTimeframeLoader("gold")
    tf = loader.load_all_timeframes(["15m", "30m", "1h"])
    primary = loader.align_to_primary("15m")
    mask = ((primary.index.hour >= 8) & (primary.index.hour < 12)) | \
           ((primary.index.hour >= 13) & (primary.index.hour < 17))
    primary = primary.loc[mask]

    labels = load_data.__wrapped__(primary) if hasattr(load_data, '__wrapped__') else None
    # Simpler approach: just get close prices aligned to our test index
    close_prices = primary["close"].reindex(X_te.index)

    # Run simulation
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

        # Position sizing: risk 2% of capital
        risk_amount = capital * RISK_PER_TRADE
        sl_distance = price * SL_PCT
        tp_distance = price * TP_PCT

        # Calculate PnL based on what actually happened next
        if i + 1 < len(close_prices):
            next_price = close_prices.iloc[i + 1]
            if pd.isna(next_price):
                equity_curve.append(capital)
                continue

            if signal == 1:  # BUY
                pnl_pct = (next_price - price) / price
            else:  # SELL (signal == 0)
                pnl_pct = (price - next_price) / price

            # Check if TP or SL would have been hit
            if pnl_pct >= TP_PCT:
                trade_pnl = risk_amount * (TP_PCT / SL_PCT)  # R:R = 1:1
            elif pnl_pct <= -SL_PCT:
                trade_pnl = -risk_amount
            else:
                trade_pnl = risk_amount * pnl_pct / SL_PCT

            # Apply commission
            commission = capital * COMMISSION_PCT
            trade_pnl -= commission

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

        # Track drawdown
        max_equity = max(max_equity, capital)
        drawdown = (max_equity - capital) / max_equity
        max_drawdown = max(max_drawdown, drawdown)

        equity_curve.append(capital)

    # Results
    total_trades = wins + losses
    win_rate = wins / total_trades if total_trades > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    avg_win = gross_profit / wins if wins > 0 else 0
    avg_loss = gross_loss / losses if losses > 0 else 0
    expectancy = total_pnl / total_trades if total_trades > 0 else 0
    roi = (capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100

    print("=" * 60)
    print("BACKTEST REPORT — Binary v2 Model ($5,000 initial)")
    print("=" * 60)
    print(f"Period:        {X_te.index.min().date()} to {X_te.index.max().date()}")
    print(f"Threshold:     {THRESHOLD}")
    print(f"Risk/trade:    {RISK_PER_TRADE:.0%} of capital")
    print(f"TP/SL:         {TP_PCT:.1%} / {SL_PCT:.1%}")
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
    print(f"Avg win:       ${avg_win:,.2f}")
    print(f"Avg loss:      ${avg_loss:,.2f}")
    print(f"")
    print(f"--- Risk Metrics ---")
    print(f"Profit factor: {profit_factor:.2f}")
    print(f"Max drawdown:  {max_drawdown:.2%} (${max_equity * max_drawdown:,.2f})")
    print(f"Expectancy:    ${expectancy:,.2f} per trade")
    print(f"Gross profit:  ${gross_profit:,.2f}")
    print(f"Gross loss:    ${gross_loss:,.2f}")
    print(f"")

    # Monthly breakdown
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

    # Last 10 trades
    if trades:
        print("Last 10 trades:")
        print("-" * 60)
        for t in trades[-10:]:
            ts = t["time"].strftime("%Y-%m-%d %H:%M")
            print(f"  {ts} | {t['signal']:4s} | ${t['price']:.2f} | PnL: ${t['pnl']:+.2f} | Equity: ${t['capital']:,.2f}")


if __name__ == "__main__":
    backtest()
