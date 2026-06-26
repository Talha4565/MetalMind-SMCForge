"""
Binary BUY/SELL model v3 — with trend filter.

Improvements over v2:
1. 1h trend filter (EMA-50 vs EMA-200, ADX)
2. Only signals aligned with higher-timeframe trend
3. Sideways market = HOLD (no signals)
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


def compute_1h_trend(tf_1h):
    """Compute 1h trend features: EMA crossover, ADX, price position."""
    if tf_1h is None or tf_1h.empty:
        return pd.DataFrame()

    df = tf_1h.copy()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["trend_ema_cross"] = (df["ema_50"] > df["ema_200"]).astype(int)  # 1=uptrend, 0=downtrend
    df["trend_price_vs_ema"] = ((df["close"] - df["ema_50"]) / df["ema_50"]).clip(-0.05, 0.05)
    df["trend_adx"] = compute_adx(df, 14)
    df["trend_strength"] = df["trend_adx"].clip(0, 50) / 50  # normalized 0-1

    # Resample to 15m and forward-fill
    cols = ["trend_ema_cross", "trend_price_vs_ema", "trend_adx", "trend_strength"]
    return df[cols]


def load_data():
    loader = MultiTimeframeLoader("gold")
    tf = loader.load_all_timeframes(["15m", "30m", "1h"])
    primary = loader.align_to_primary("15m")

    # Strict sessions
    mask = ((primary.index.hour >= 8) & (primary.index.hour < 12)) | \
           ((primary.index.hour >= 13) & (primary.index.hour < 17))
    primary = primary.loc[mask]

    df = engineer_all_features(primary, add_labels=False, asset="gold")

    # Binary labels
    labels = generate_balanced_binary_labels(primary, tp_pct=0.003, sl_pct=0.003, max_bars=6)
    df["target"] = labels
    df.dropna(subset=["target"], inplace=True)
    df["target"] = df["target"].astype(int)

    # CVD
    df["cvd_15m"] = compute_cvd(tf.get("15m", primary))
    df["cvd_15m_slope"] = df["cvd_15m"].diff(5)
    df["cvd_30m"] = compute_cvd(tf.get("30m", primary))
    df["cvd_30m_slope"] = df["cvd_30m"].diff(5)

    # 15m ADX
    df["adx_14"] = compute_adx(df, 14)
    df["adx_trending"] = (df["adx_14"] > 25).astype(int)

    # ATR + volatility
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"] - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    df["vol_keep"] = (df["atr_14"] > df["atr_14"].rolling(20).median()).astype(int)

    # 1h trend features
    trend_1h = compute_1h_trend(tf.get("1h"))
    if not trend_1h.empty:
        trend_1h_resampled = trend_1h.reindex(df.index, method="ffill")
        df = df.join(trend_1h_resampled, how="left")
        logger.info("Added 1h trend features")

    df.dropna(inplace=True)
    n_buy = (df["target"] == 1).sum()
    n_sell = (df["target"] == 0).sum()
    logger.info(f"Dataset: {len(df)} rows, {len(df.columns)} cols")
    logger.info(f"  BUY: {n_buy} ({n_buy/len(df):.1%}) | SELL: {n_sell} ({n_sell/len(df):.1%})")

    # Trend distribution
    if "trend_ema_cross" in df.columns:
        up = (df["trend_ema_cross"] == 1).sum()
        down = (df["trend_ema_cross"] == 0).sum()
        logger.info(f"  1h Uptrend: {up} ({up/len(df):.1%}) | Downtrend: {down} ({down/len(df):.1%})")

    return df


def split(df, train_end="2024-12-31", val_end="2025-09-30"):
    train = df[df.index <= train_end]
    val = df[(df.index > train_end) & (df.index <= val_end)]
    test = df[df.index > val_end]

    train = train[train["vol_keep"] == 1]

    feat_cols = [c for c in df.columns if c not in ("target", "vol_keep")]
    X_tr, y_tr = train[feat_cols], train["target"]
    X_v, y_v = val[feat_cols], val["target"]
    X_te, y_te = test[feat_cols], test["target"]

    logger.info(f"Train: {len(X_tr)} | Val: {len(X_v)} | Test: {len(X_te)}")
    return X_tr, y_tr, X_v, y_v, X_te, y_te, feat_cols


def train(X_tr, y_tr, X_v, y_v, n_trials=50):
    w = compute_class_weight("balanced", classes=[0, 1], y=y_tr.values)
    sw = y_tr.map({0: w[0], 1: w[1]}).values

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
        return 1 - accuracy_score(y_v, m.predict(X_v))

    study = optuna.create_study(direction="minimize")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(obj, n_trials=n_trials)

    b = study.best_params
    logger.info(f"Best val accuracy: {1 - study.best_value:.2%}")

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


def evaluate_with_trend_filter(model, X_test, y_test, threshold=0.65, label="Model"):
    """Evaluate with trend filter applied."""
    proba = model.predict_proba(X_test)[:, 1]
    preds_raw = (proba >= 0.5).astype(int)
    confident = np.abs(proba - 0.5) >= (threshold - 0.5)

    # Apply trend filter
    if "trend_ema_cross" in X_test.columns:
        trend = X_test["trend_ema_cross"].values  # 1=uptrend, 0=downtrend
        # BUY only in uptrend, SELL only in downtrend
        aligned = np.where(
            (preds_raw == 1) & (trend == 1), 1,  # BUY in uptrend
            np.where((preds_raw == 0) & (trend == 0), 0, -1)  # SELL in downtrend
        )
    else:
        aligned = preds_raw

    # Combine confidence + trend filter
    final = np.where(confident, aligned, -1)

    mask = final >= 0
    n_signals = mask.sum()
    n_hold = (~mask).sum()
    n_buy = (final == 1).sum()
    n_sell = (final == 0).sum()

    if mask.sum() > 0:
        acc = accuracy_score(y_test.values[mask], final[mask])
        prec_b = precision_score(y_test.values[mask], final[mask], pos_label=1, zero_division=0)
        rec_b = recall_score(y_test.values[mask], final[mask], pos_label=1, zero_division=0)
        prec_s = precision_score(y_test.values[mask], final[mask], pos_label=0, zero_division=0)
        rec_s = recall_score(y_test.values[mask], final[mask], pos_label=0, zero_division=0)
    else:
        acc = prec_b = rec_b = prec_s = rec_s = 0.0

    logger.info(f"{label}: acc={acc:.2%} BUY={n_buy} SELL={n_sell} HOLD={n_hold} "
                f"BUY_prec={prec_b:.2%} SELL_prec={prec_s:.2%}")

    if mask.sum() > 0:
        print(classification_report(y_test.values[mask], final[mask],
                                    target_names=["SELL", "BUY"], zero_division=0))
    return acc, final


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("BINARY MODEL v3 — with 1h trend filter")
    logger.info("=" * 60)

    df = load_data()
    X_tr, y_tr, X_v, y_v, X_te, y_te, feats = split(df)

    model = train(X_tr, y_tr, X_v, y_v, n_trials=50)

    # Evaluate WITHOUT trend filter (baseline)
    logger.info("\n--- Without trend filter ---")
    proba = model.predict_proba(X_te)[:, 1]
    preds_raw = (proba >= 0.5).astype(int)
    confident = np.abs(proba - 0.5) >= 0.15
    preds_no_filter = np.where(confident, preds_raw, -1)
    mask = preds_no_filter >= 0
    if mask.sum() > 0:
        acc_base = accuracy_score(y_te.values[mask], preds_no_filter[mask])
        logger.info(f"Baseline: acc={acc_base:.2%} signals={mask.sum()} "
                     f"BUY={(preds_no_filter==1).sum()} SELL={(preds_no_filter==0).sum()}")

    # Evaluate WITH trend filter
    for thresh in [0.55, 0.60, 0.65, 0.70]:
        logger.info(f"\n--- Trend filter + threshold={thresh} ---")
        evaluate_with_trend_filter(model, X_te, y_te, threshold=thresh)

    # Save
    out = MODEL_CONFIG["enhanced_model_path"].parent / "gold_binary_v3_trend.pkl"
    with open(out, "wb") as f:
        pickle.dump({"model": model, "features": feats}, f)
    logger.info(f"Saved to {out}")
