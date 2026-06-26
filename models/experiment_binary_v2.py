"""
Binary BUY/SELL model v2 — XGBoost only, balanced labels.

Label approach: symmetric barrier (0.3% TP / 0.3% SL) for balanced labels.
At inference: high-confidence signals (prob > threshold) = BUY/SELL, else HOLD.
"""
import pandas as pd
import numpy as np
import pickle
import logging
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report, precision_score, recall_score
from sklearn.utils.class_weight import compute_class_weight
import xgboost as xgb
import optuna

from config.settings import MODEL_CONFIG, PROJECT_ROOT
from data.loaders import MultiTimeframeLoader
from features.pipeline import engineer_all_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_balanced_binary_labels(df, tp_pct=0.003, sl_pct=0.003, max_bars=6):
    """Symmetric triple-barrier: 1=BUY, 0=SELL, NaN=neither hit."""
    close = df["close"].to_numpy()
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    labels = np.full(len(close), np.nan)

    for i in range(len(close) - max_bars):
        entry = close[i]
        for k in range(1, max_bars + 1):
            ret_h = (high[i + k] - entry) / entry
            ret_l = (low[i + k] - entry) / entry
            hit_tp = ret_h >= tp_pct
            hit_sl = ret_l <= -sl_pct
            if hit_tp and hit_sl:
                labels[i] = 1.0 if close[i + k] >= entry else 0.0
                break
            elif hit_tp:
                labels[i] = 1.0
                break
            elif hit_sl:
                labels[i] = 0.0
                break
    return pd.Series(labels, index=df.index, name="target")


def compute_adx(df, period=14):
    h, l, c = df["high"], df["low"], df["close"]
    pdm = h.diff()
    mdm = -l.diff()
    pdm = pdm.where((pdm > mdm) & (pdm > 0), 0.0)
    mdm = mdm.where((mdm > pdm) & (mdm > 0), 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    pdi = 100 * pdm.rolling(period).mean() / atr
    mdi = 100 * mdm.rolling(period).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.rolling(period).mean()


def compute_cvd(df):
    delta = df["close"] - df["open"]
    return (np.sign(delta) * df["volume"]).cumsum()



def load_data():
    loader = MultiTimeframeLoader("gold")
    tf = loader.load_all_timeframes(["15m", "30m", "1h"])
    primary = loader.align_to_primary("15m")

    # Strict sessions: London 08:00-12:00, NY 13:00-17:00
    mask = ((primary.index.hour >= 8) & (primary.index.hour < 12)) | \
           ((primary.index.hour >= 13) & (primary.index.hour < 17))
    primary = primary.loc[mask]

    df = engineer_all_features(primary, add_labels=False, asset="gold")

    # Binary labels with SYMMETRIC barriers
    labels = generate_balanced_binary_labels(primary, tp_pct=0.003, sl_pct=0.003, max_bars=6)
    df["target"] = labels
    df.dropna(subset=["target"], inplace=True)
    df["target"] = df["target"].astype(int)

    # CVD
    df["cvd_15m"] = compute_cvd(tf.get("15m", primary))
    df["cvd_15m_slope"] = df["cvd_15m"].diff(5)
    df["cvd_30m"] = compute_cvd(tf.get("30m", primary))
    df["cvd_30m_slope"] = df["cvd_30m"].diff(5)

    # ADX
    df["adx_14"] = compute_adx(df, 14)
    df["adx_trending"] = (df["adx_14"] > 25).astype(int)

    # ATR + volatility regime
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"] - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    df["atr_percentile"] = df["atr_14"].rolling(100).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False
    )
    df["high_vol"] = (df["atr_percentile"] > 0.5).astype(int)
    df["vol_keep"] = (df["atr_14"] > df["atr_14"].rolling(20).median()).astype(int)

    df.dropna(inplace=True)
    n_buy = (df["target"] == 1).sum()
    n_sell = (df["target"] == 0).sum()
    logger.info(f"Dataset: {len(df)} rows, {len(df.columns)} cols")
    logger.info(f"  BUY: {n_buy} ({n_buy/len(df):.1%}) | SELL: {n_sell} ({n_sell/len(df):.1%})")
    return df


def split(df, train_end="2024-12-31", val_end="2025-09-30"):
    train = df[df.index <= train_end]
    val = df[(df.index > train_end) & (df.index <= val_end)]
    test = df[df.index > val_end]

    # Volatility filter on training only
    train = train[train["vol_keep"] == 1]

    feat_cols = [c for c in df.columns if c not in ("target", "vol_keep")]
    X_tr, y_tr = train[feat_cols], train["target"]
    X_v, y_v = val[feat_cols], val["target"]
    X_te, y_te = test[feat_cols], test["target"]

    logger.info(f"Train: {len(X_tr)} | Val: {len(X_v)} | Test: {len(X_te)}")
    logger.info(f"  Train BUY: {(y_tr==1).sum()} SELL: {(y_tr==0).sum()}")
    return X_tr, y_tr, X_v, y_v, X_te, y_te, feat_cols


def train(X_tr, y_tr, X_v, y_v, n_trials=50):
    w = compute_class_weight("balanced", classes=[0, 1], y=y_tr.values)
    sw = y_tr.map({0: w[0], 1: w[1]}).values
    logger.info(f"Class weights: SELL={w[0]:.2f} BUY={w[1]:.2f}")

    def obj(trial):
        p = {
            "max_depth": trial.suggest_int("d", 3, 12),
            "learning_rate": trial.suggest_float("lr", 0.005, 0.1, log=True),
            "subsample": trial.suggest_float("s", 0.5, 0.9),
            "colsample_bytree": trial.suggest_float("c", 0.3, 0.8),
            "min_child_weight": trial.suggest_int("mcw", 1, 10),
            "gamma": trial.suggest_float("g", 0, 5),
            "reg_alpha": trial.suggest_float("a", 1e-8, 10, log=True),
            "reg_lambda": trial.suggest_float("l", 1e-8, 10, log=True),
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "early_stopping_rounds": 50,
            "random_state": 42,
        }
        m = xgb.XGBClassifier(**p)
        m.fit(X_tr, y_tr, sample_weight=sw, eval_set=[(X_v, y_v)], verbose=0)
        pred = m.predict(X_v)
        return 1 - accuracy_score(y_v, pred)

    study = optuna.create_study(direction="minimize")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(obj, n_trials=n_trials)

    b = study.best_params
    logger.info(f"Best val accuracy: {1 - study.best_value:.2%}")
    logger.info(f"Best params: {b}")

    final = xgb.XGBClassifier(
        n_estimators=2000, max_depth=b["d"], learning_rate=b["lr"],
        colsample_bytree=b["c"], subsample=b["s"],
        min_child_weight=b["mcw"], gamma=b["g"],
        reg_alpha=b["a"], reg_lambda=b["l"],
        objective="binary:logistic", eval_metric="logloss",
        early_stopping_rounds=50, random_state=42,
    )
    final.fit(X_tr, y_tr, sample_weight=sw, eval_set=[(X_v, y_v)], verbose=0)
    return final


def evaluate(model, X_test, y_test, threshold=0.0, label="Model"):
    proba = model.predict_proba(X_test)[:, 1]  # P(BUY)
    preds_raw = (proba >= 0.5).astype(int)  # 0=SELL, 1=BUY

    if threshold > 0:
        # Apply confidence gate
        confident = np.abs(proba - 0.5) >= (threshold - 0.5)
        preds = np.where(confident, preds_raw, -1)
        n_signals = confident.sum()
        n_hold = (~confident).sum()
    else:
        preds = preds_raw
        n_signals = len(preds)
        n_hold = 0

    mask = preds >= 0
    if mask.sum() > 0:
        acc = accuracy_score(y_test.values[mask], preds[mask])
        prec_b = precision_score(y_test.values[mask], preds[mask], pos_label=1, zero_division=0)
        rec_b = recall_score(y_test.values[mask], preds[mask], pos_label=1, zero_division=0)
        prec_s = precision_score(y_test.values[mask], preds[mask], pos_label=0, zero_division=0)
        rec_s = recall_score(y_test.values[mask], preds[mask], pos_label=0, zero_division=0)
    else:
        acc = prec_b = rec_b = prec_s = rec_s = 0.0

    logger.info(f"{label}: acc={acc:.2%} BUY_prec={prec_b:.2%} BUY_rec={rec_b:.2%} "
                f"SELL_prec={prec_s:.2%} SELL_rec={rec_s:.2%} "
                f"signals={n_signals}/{len(y_test)} hold={n_hold}")

    # Classification report
    if mask.sum() > 0:
        print(classification_report(y_test.values[mask], preds[mask],
                                    target_names=["SELL", "BUY"], zero_division=0))
    return acc


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("BINARY MODEL v2 — XGBoost only, balanced labels, Optuna")
    logger.info("=" * 60)

    df = load_data()
    X_tr, y_tr, X_v, y_v, X_te, y_te, feats = split(df)

    model = train(X_tr, y_tr, X_v, y_v, n_trials=50)

    # No threshold
    evaluate(model, X_te, y_te, threshold=0.0, label="No threshold")

    # With thresholds
    for t in [0.55, 0.60, 0.65, 0.70]:
        evaluate(model, X_te, y_te, threshold=t, label=f"Threshold={t}")

    # Save
    out = MODEL_CONFIG["enhanced_model_path"].parent / "gold_binary_v2.pkl"
    with open(out, "wb") as f:
        pickle.dump({"model": model, "features": feats}, f)
    logger.info(f"Saved to {out}")
