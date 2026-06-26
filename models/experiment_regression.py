"""
Phase 2: Regression model for dynamic TP/SL prediction.

Three models:
1. Direction classifier (BUY/SELL) — from v3
2. TP distance regressor — predicts optimal take-profit % based on ATR
3. SL distance regressor — predicts optimal stop-loss % based on ATR

Labels:
- For each bar, look ahead to find actual TP/SL that would have worked
- TP distance = actual max favorable excursion before reversal
- SL distance = actual max adverse excursion before reversal
"""
import pandas as pd
import numpy as np
import pickle
import logging
from pathlib import Path
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb
import optuna

from config.settings import MODEL_CONFIG, PROJECT_ROOT
from data.loaders import MultiTimeframeLoader
from features.pipeline import engineer_all_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    if tf_1h is None or tf_1h.empty:
        return pd.DataFrame()
    df = tf_1h.copy()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["trend_ema_cross"] = (df["ema_50"] > df["ema_200"]).astype(int)
    df["trend_price_vs_ema"] = ((df["close"] - df["ema_50"]) / df["ema_50"]).clip(-0.05, 0.05)
    df["trend_adx"] = compute_adx(df, 14)
    df["trend_strength"] = df["trend_adx"].clip(0, 50) / 50
    cols = ["trend_ema_cross", "trend_price_vs_ema", "trend_adx", "trend_strength"]
    return df[cols]


def generate_regression_labels(df, max_bars=6):
    """
    Generate regression targets: actual TP and SL distances.

    For each bar, look ahead up to max_bars:
    - Find max favorable excursion (MFE) — best price move in signal direction
    - Find max adverse excursion (MAE) — worst price move against signal
    - TP distance = MFE (as % from entry)
    - SL distance = MAE (as % from entry, positive number)

    Also returns direction label (1=BUY, 0=SELL, NaN=neither hit).
    """
    close = df["close"].to_numpy()
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()

    directions = np.full(len(close), np.nan)
    tp_distances = np.full(len(close), np.nan)
    sl_distances = np.full(len(close), np.nan)

    for i in range(len(close) - max_bars):
        entry = close[i]

        # Track best and worst moves
        best_up = 0.0
        best_down = 0.0

        for k in range(1, max_bars + 1):
            if i + k >= len(close):
                break

            ret_h = (high[i + k] - entry) / entry
            ret_l = (low[i + k] - entry) / entry

            best_up = max(best_up, ret_h)
            best_down = min(best_down, ret_l)

            # Check if TP or SL hit
            hit_tp = ret_h >= 0.003  # 0.3% TP
            hit_sl = ret_l <= -0.003  # 0.3% SL

            if hit_tp and hit_sl:
                directions[i] = 1.0 if close[i + k] >= entry else 0.0
                break
            elif hit_tp:
                directions[i] = 1.0
                break
            elif hit_sl:
                directions[i] = 0.0
                break

        if not np.isnan(directions[i]):
            if directions[i] == 1.0:  # BUY
                tp_distances[i] = best_up
                sl_distances[i] = abs(best_down) if best_down < 0 else 0.001
            else:  # SELL
                tp_distances[i] = abs(best_down) if best_down < 0 else 0.001
                sl_distances[i] = best_up if best_up > 0 else 0.001

    return (
        pd.Series(directions, index=df.index, name="direction"),
        pd.Series(tp_distances, index=df.index, name="tp_distance"),
        pd.Series(sl_distances, index=df.index, name="sl_distance"),
    )


def load_data():
    loader = MultiTimeframeLoader("gold")
    tf = loader.load_all_timeframes(["15m", "30m", "1h"])
    primary = loader.align_to_primary("15m")

    mask = ((primary.index.hour >= 8) & (primary.index.hour < 12)) | \
           ((primary.index.hour >= 13) & (primary.index.hour < 17))
    primary = primary.loc[mask]

    df = engineer_all_features(primary, add_labels=False, asset="gold")

    # Regression labels
    directions, tp_dist, sl_dist = generate_regression_labels(primary)
    df["target"] = directions
    df["tp_target"] = tp_dist
    df["sl_target"] = sl_dist

    # Drop rows where direction is NaN
    df.dropna(subset=["target"], inplace=True)
    df["target"] = df["target"].astype(int)

    # Drop rows where TP/SL are NaN or zero
    df = df[(df["tp_target"] > 0) & (df["sl_target"] > 0)]

    # CVD
    df["cvd_15m"] = compute_cvd(tf.get("15m", primary))
    df["cvd_15m_slope"] = df["cvd_15m"].diff(5)
    df["cvd_30m"] = compute_cvd(tf.get("30m", primary))
    df["cvd_30m_slope"] = df["cvd_30m"].diff(5)

    # ADX
    df["adx_14"] = compute_adx(df, 14)
    df["adx_trending"] = (df["adx_14"] > 25).astype(int)

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"] - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    df["vol_keep"] = (df["atr_14"] > df["atr_14"].rolling(20).median()).astype(int)

    # 1h trend
    trend_1h = compute_1h_trend(tf.get("1h"))
    if not trend_1h.empty:
        trend_1h_resampled = trend_1h.reindex(df.index, method="ffill")
        df = df.join(trend_1h_resampled, how="left")

    df.dropna(inplace=True)

    logger.info(f"Dataset: {len(df)} rows, {len(df.columns)} cols")
    logger.info(f"  BUY: {(df['target']==1).sum()} | SELL: {(df['target']==0).sum()}")
    logger.info(f"  TP range: {df['tp_target'].min():.4f} - {df['tp_target'].max():.4f} ({df['tp_target'].mean():.4f} avg)")
    logger.info(f"  SL range: {df['sl_target'].min():.4f} - {df['sl_target'].max():.4f} ({df['sl_target'].mean():.4f} avg)")

    return df


def split(df, train_end="2024-12-31", val_end="2025-09-30"):
    train = df[df.index <= train_end]
    val = df[(df.index > train_end) & (df.index <= val_end)]
    test = df[df.index > val_end]

    train = train[train["vol_keep"] == 1]

    feat_cols = [c for c in df.columns if c not in ("target", "vol_keep", "tp_target", "sl_target")]

    def xy(sub):
        return sub[feat_cols], sub["target"], sub["tp_target"], sub["sl_target"]

    X_tr, y_tr, tp_tr, sl_tr = xy(train)
    X_v, y_v, tp_v, sl_v = xy(val)
    X_te, y_te, tp_te, sl_te = xy(test)

    logger.info(f"Train: {len(X_tr)} | Val: {len(X_v)} | Test: {len(X_te)}")
    return X_tr, y_tr, tp_tr, sl_tr, X_v, y_v, tp_v, sl_v, X_te, y_te, tp_te, sl_te, feat_cols


def train_direction(X_tr, y_tr, X_v, y_v, n_trials=40):
    """Train direction classifier."""
    from sklearn.utils.class_weight import compute_class_weight
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
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "early_stopping_rounds": 50,
            "random_state": 42,
        }
        m = xgb.XGBClassifier(**p)
        m.fit(X_tr, y_tr, sample_weight=sw, eval_set=[(X_v, y_v)], verbose=0)
        from sklearn.metrics import accuracy_score
        return 1 - accuracy_score(y_v, m.predict(X_v))

    study = optuna.create_study(direction="minimize")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(obj, n_trials=n_trials)

    b = study.best_params
    logger.info(f"Direction val accuracy: {1 - study.best_value:.2%}")

    final = xgb.XGBClassifier(
        n_estimators=2000, max_depth=b["d"], learning_rate=b["lr"],
        colsample_bytree=b["c"], subsample=b["s"],
        min_child_weight=b["mcw"], gamma=b["g"],
        objective="binary:logistic", eval_metric="logloss",
        early_stopping_rounds=50, random_state=42,
    )
    final.fit(X_tr, y_tr, sample_weight=sw, eval_set=[(X_v, y_v)], verbose=0)
    return final


def train_regression(X_tr, y_tr, X_v, y_v, target_name, n_trials=30):
    """Train TP or SL distance regressor."""
    def obj(trial):
        p = {
            "max_depth": trial.suggest_int("d", 3, 10),
            "learning_rate": trial.suggest_float("lr", 0.005, 0.1, log=True),
            "subsample": trial.suggest_float("s", 0.5, 0.9),
            "colsample_bytree": trial.suggest_float("c", 0.3, 0.8),
            "min_child_weight": trial.suggest_int("mcw", 1, 10),
            "objective": "reg:squarederror",
            "eval_metric": "rmse",
            "early_stopping_rounds": 50,
            "random_state": 42,
        }
        m = xgb.XGBRegressor(**p)
        m.fit(X_tr, y_tr, eval_set=[(X_v, y_v)], verbose=0)
        pred = m.predict(X_v)
        return mean_absolute_error(y_v, pred)

    study = optuna.create_study(direction="minimize")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(obj, n_trials=n_trials)

    b = study.best_params
    logger.info(f"{target_name} val MAE: {study.best_value:.6f}")

    final = xgb.XGBRegressor(
        n_estimators=2000, max_depth=b["d"], learning_rate=b["lr"],
        colsample_bytree=b["c"], subsample=b["s"],
        min_child_weight=b["mcw"],
        objective="reg:squarederror", eval_metric="rmse",
        early_stopping_rounds=50, random_state=42,
    )
    final.fit(X_tr, y_tr, eval_set=[(X_v, y_v)], verbose=0)
    return final


def evaluate_all(direction_model, tp_model, sl_model, X_test, y_test, tp_test, sl_test):
    """Evaluate full system: direction + dynamic TP/SL."""
    from sklearn.metrics import accuracy_score

    # Direction predictions
    proba = direction_model.predict_proba(X_test)[:, 1]
    confident = np.abs(proba - 0.5) >= 0.15
    preds_raw = (proba >= 0.5).astype(int)

    # Trend filter
    if "trend_ema_cross" in X_test.columns:
        trend = X_test["trend_ema_cross"].values
        aligned = np.where(
            (preds_raw == 1) & (trend == 1), 1,
            np.where((preds_raw == 0) & (trend == 0), 0, -1)
        )
    else:
        aligned = preds_raw
    preds = np.where(confident, aligned, -1)

    # TP/SL predictions
    tp_pred = tp_model.predict(X_test)
    sl_pred = sl_model.predict(X_test)

    # Clamp TP/SL to reasonable ranges
    tp_pred = np.clip(tp_pred, 0.001, 0.02)  # 0.1% to 2%
    sl_pred = np.clip(sl_pred, 0.001, 0.015)  # 0.1% to 1.5%

    # Direction accuracy
    mask = preds >= 0
    if mask.sum() > 0:
        dir_acc = accuracy_score(y_test.values[mask], preds[mask])
    else:
        dir_acc = 0.0

    # TP/SL accuracy (how close to actual)
    tp_mae = mean_absolute_error(tp_test, tp_pred)
    sl_mae = mean_absolute_error(sl_test, sl_pred)
    tp_r2 = r2_score(tp_test, tp_pred)
    sl_r2 = r2_score(sl_test, sl_pred)

    n_buy = (preds == 1).sum()
    n_sell = (preds == 0).sum()
    n_hold = (preds == -1).sum()

    print(f"Direction accuracy: {dir_acc:.2%}")
    print(f"Signals: BUY={n_buy} SELL={n_sell} HOLD={n_hold}")
    print(f"")
    print(f"TP prediction — MAE: {tp_mae:.6f} ({tp_mae*100:.3f}%) | R2: {tp_r2:.4f}")
    print(f"SL prediction — MAE: {sl_mae:.6f} ({sl_mae*100:.3f}%) | R2: {sl_r2:.4f}")
    print(f"")
    print(f"Predicted TP range: {tp_pred.min():.4f} - {tp_pred.max():.4f} (avg {tp_pred.mean():.4f})")
    print(f"Predicted SL range: {sl_pred.min():.4f} - {sl_pred.max():.4f} (avg {sl_pred.mean():.4f})")
    print(f"Actual TP range:    {tp_test.min():.4f} - {tp_test.max():.4f} (avg {tp_test.mean():.4f})")
    print(f"Actual SL range:    {sl_test.min():.4f} - {sl_test.max():.4f} (avg {sl_test.mean():.4f})")

    return dir_acc, tp_mae, sl_mae, preds, tp_pred, sl_pred


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("PHASE 2 — Direction + TP/SL Regression")
    logger.info("=" * 60)

    df = load_data()
    X_tr, y_tr, tp_tr, sl_tr, X_v, y_v, tp_v, sl_v, X_te, y_te, tp_te, sl_te, feats = split(df)

    # Train all three models
    logger.info("\n--- Training direction classifier ---")
    dir_model = train_direction(X_tr, y_tr, X_v, y_v, n_trials=40)

    logger.info("\n--- Training TP regressor ---")
    tp_model = train_regression(X_tr[feats], tp_tr, X_v[feats], tp_v, "TP", n_trials=30)

    logger.info("\n--- Training SL regressor ---")
    sl_model = train_regression(X_tr[feats], sl_tr, X_v[feats], sl_v, "SL", n_trials=30)

    # Evaluate
    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)
    dir_acc, tp_mae, sl_mae, preds, tp_pred, sl_pred = evaluate_all(
        dir_model, tp_model, sl_model, X_te[feats], y_te, tp_te, sl_te
    )

    # Save
    out = MODEL_CONFIG["enhanced_model_path"].parent / "gold_regression_system.pkl"
    with open(out, "wb") as f:
        pickle.dump({
            "direction_model": dir_model,
            "tp_model": tp_model,
            "sl_model": sl_model,
            "features": feats,
        }, f)
    logger.info(f"Saved to {out}")
