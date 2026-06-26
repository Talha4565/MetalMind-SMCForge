"""Generate forward trading report using the binary v2 model."""
import pickle
import pandas as pd
import numpy as np
import logging

from models.experiment_binary_v2 import load_data, split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    df = load_data()
    X_tr, y_tr, X_v, y_v, X_te, y_te, feats = split(df)

    with open("/app/models/gold_binary_v2.pkl", "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]

    proba = model.predict_proba(X_te)[:, 1]
    preds_raw = (proba >= 0.5).astype(int)

    # 0.65 threshold
    confident = np.abs(proba - 0.5) >= 0.15
    preds = np.where(confident, preds_raw, -1)

    labels = {0: "SELL", 1: "BUY", -1: "HOLD"}

    results = pd.DataFrame({
        "timestamp": X_te.index,
        "signal": [labels[p] for p in preds],
        "confidence": [max(p, 1 - p) for p in proba],
    })

    total = len(results)
    buys = (results["signal"] == "BUY").sum()
    sells = (results["signal"] == "SELL").sum()
    holds = (results["signal"] == "HOLD").sum()

    # Accuracy of signals
    mask = preds >= 0
    correct = (preds[mask] == y_te.values[mask]).sum()
    total_signals = mask.sum()

    print("=" * 60)
    print("FORWARD TRADING REPORT — Binary v2 Model (0.65 threshold)")
    print("=" * 60)
    print(f"Period: {X_te.index.min().date()} to {X_te.index.max().date()}")
    print(f"Total bars: {total}")
    print(f"")
    print(f"Signal breakdown:")
    print(f"  BUY:   {buys:4d} ({buys/total:.1%})")
    print(f"  SELL:  {sells:4d} ({sells/total:.1%})")
    print(f"  HOLD:  {holds:4d} ({holds/total:.1%})")
    print(f"")
    print(f"Signal accuracy: {correct}/{total_signals} = {correct/total_signals:.1%}")
    print(f"")

    # Monthly breakdown
    results["month"] = results["timestamp"].dt.to_period("M")
    monthly = results.groupby("month")["signal"].value_counts().unstack(fill_value=0)
    print("Monthly signal distribution:")
    print(monthly.to_string())
    print("")

    # Last 10 signals
    print("Last 10 signals:")
    print("-" * 50)
    for _, row in results.tail(10).iterrows():
        ts = row["timestamp"].strftime("%Y-%m-%d %H:%M")
        print(f"  {ts} | {row['signal']:4s} | conf={row['confidence']:.1%}")

    # Last BUY and SELL
    print("")
    last_buy = results[results["signal"] == "BUY"].tail(1)
    last_sell = results[results["signal"] == "SELL"].tail(1)

    if not last_buy.empty:
        r = last_buy.iloc[0]
        print(f"Last BUY:  {r['timestamp'].strftime('%Y-%m-%d %H:%M')} | conf={r['confidence']:.1%}")
    if not last_sell.empty:
        r = last_sell.iloc[0]
        print(f"Last SELL: {r['timestamp'].strftime('%Y-%m-%d %H:%M')} | conf={r['confidence']:.1%}")

if __name__ == "__main__":
    main()
