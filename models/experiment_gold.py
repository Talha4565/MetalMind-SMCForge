"""
Experimental gold model — separate from production.
Tests accuracy improvements without touching the existing model.

Step 1: Class weighting + walk-forward validation
"""
import pandas as pd
import numpy as np
import pickle
import logging
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils.class_weight import compute_class_weight
import xgboost as xgb
import optuna

from config.settings import MODEL_CONFIG, PROJECT_ROOT
from data.loaders import load_gold_data
from features.pipeline import engineer_all_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Label remap: {-1,0,1} -> {0,1,2} for XGBoost
LABEL_MAP = {-1: 0, 0: 1, 1: 2}
LABEL_REVERSE = {0: -1, 1: 0, 2: 1}


def prepare_data():
    df = load_gold_data(primary_tf="15m", session_filter=True)
    df = engineer_all_features(df, add_labels=True, asset="gold")
    df.dropna(inplace=True)
    logger.info(f"Dataset: {len(df)} rows, {len(df.columns)} columns")
    return df


def walk_forward_split(df, train_end="2024-12-31", val_end="2025-09-30"):
    """Time-series split: train -> validate -> test (no look-ahead)."""
    train = df[df.index <= train_end]
    val = df[(df.index > train_end) & (df.index <= val_end)]
    test = df[df.index > val_end]

    feature_cols = [c for c in df.columns if c != "target"]

    X_train, y_train = train[feature_cols], train["target"].map(LABEL_MAP)
    X_val, y_val = val[feature_cols], val["target"].map(LABEL_MAP)
    X_test, y_test = test[feature_cols], test["target"].map(LABEL_MAP)

    logger.info(f"Train: {len(train)} ({train.index.min()} → {train.index.max()})")
    logger.info(f"Val:   {len(val)} ({val.index.min()} → {val.index.max()})")
    logger.info(f"Test:  {len(test)} ({test.index.min()} → {test.index.max()})")

    for split_name, ys in [("train", y_train), ("val", y_val), ("test", y_test)]:
        dist = ys.value_counts().sort_index()
        dist_str = ", ".join(f"{LABEL_REVERSE[k]}:{v}" for k, v in dist.items())
        logger.info(f"  {split_name} dist: {dist_str}")

    return X_train, y_train, X_val, y_val, X_test, y_test, feature_cols


def tune_and_train(X_train, y_train, X_val, y_val, n_trials=30):
    """Optuna tune + final train with class weights."""
    classes = np.array([0, 1, 2])
    weights = compute_class_weight("balanced", classes=classes, y=y_train.values)
    weight_dict = {c: w for c, w in zip(classes, weights)}
    sample_weights = y_train.map(weight_dict).values

    logger.info(f"Class weights: SELL={weight_dict[0]:.2f}, HOLD={weight_dict[1]:.2f}, BUY={weight_dict[2]:.2f}")

    def objective(trial):
        params = {
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "learning_rate": trial.suggest_float("lr", 0.01, 0.1, log=True),
            "subsample": trial.suggest_float("sub", 0.5, 0.9),
            "colsample_bytree": trial.suggest_float("col", 0.4, 0.8),
            "objective": "multi:softmax",
            "num_class": 3,
            "eval_metric": "mlogloss",
            "early_stopping_rounds": 50,
            "random_state": 42,
        }
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train, sample_weight=sample_weights,
                  eval_set=[(X_val, y_val)], verbose=0)
        pred = model.predict(X_val)
        return 1 - accuracy_score(y_val, pred)

    study = optuna.create_study(direction="minimize")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(objective, n_trials=n_trials)

    best = study.best_params
    best_acc = 1 - study.best_value
    logger.info(f"Best params: {best}")
    logger.info(f"Best val accuracy: {best_acc:.2%}")

    # Final model
    final_model = xgb.XGBClassifier(
        n_estimators=2000,
        max_depth=best["max_depth"],
        learning_rate=best["lr"],
        colsample_bytree=best["col"],
        subsample=best["sub"],
        objective="multi:softmax",
        num_class=3,
        eval_metric="mlogloss",
        early_stopping_rounds=50,
        random_state=42,
    )
    final_model.fit(X_train, y_train, sample_weight=sample_weights,
                    eval_set=[(X_val, y_val)], verbose=0)
    return final_model


def evaluate(model, X_test, y_test):
    pred_mapped = model.predict(X_test)
    pred = pd.Series(pred_mapped).map(LABEL_REVERSE).values
    y_original = y_test.map(LABEL_REVERSE).values
    acc = accuracy_score(y_original, pred)
    logger.info(f"Test accuracy: {acc:.2%}")
    print(classification_report(y_original, pred, target_names=["SELL", "HOLD", "BUY"]))
    return acc, pred


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("EXPERIMENTAL GOLD MODEL — Step 1: Class weights + walk-forward")
    logger.info("=" * 60)

    df = prepare_data()
    X_train, y_train, X_val, y_val, X_test, y_test, features = walk_forward_split(df)
    model = tune_and_train(X_train, y_train, X_val, y_val, n_trials=30)
    acc, preds = evaluate(model, X_test, y_test)

    # Save as experimental (not production)
    out_path = MODEL_CONFIG["enhanced_model_path"].parent / "gold_experiment_15m.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Saved experimental model to {out_path}")
    logger.info(f"Result: {acc:.2%} test accuracy")
