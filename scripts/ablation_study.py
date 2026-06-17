"""Ablation study: quantify SMC feature contribution to model performance."""

import sys
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.loaders import load_gold_data, load_silver_data
from features.pipeline import engineer_all_features
from models.train_enhanced import EnhancedModelTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_ablation(asset: str = "gold"):
    """Run ablation study: full model vs model without SMC features."""
    logger.info(f"=" * 60)
    logger.info(f"ABLATION STUDY: {asset.upper()}")
    logger.info(f"=" * 60)

    # Load and engineer features
    logger.info("Loading data...")
    df = load_asset_data(asset=asset, primary_tf="15m", session_filter=True)
    df = engineer_all_features(df, add_labels=True)

    label_col = "target" if "target" in df.columns else "label"
    if label_col not in df.columns:
        logger.error(f"No label column found. Available: {[c for c in df.columns if 'label' in c.lower() or 'target' in c.lower()]}")
        return

    # Drop rows with NaN labels
    df = df.dropna(subset=[label_col])
    logger.info(f"Dataset: {len(df)} rows, {len(df.columns)} columns")

    # Identify SMC feature columns
    smc_cols = [c for c in df.columns if any(x in c.lower() for x in
        ["fvg", "bos", "liquidity", "sweep", "order_block", "premium", "discount", "market_structure"])]
    logger.info(f"SMC features ({len(smc_cols)}): {smc_cols[:10]}...")

    # Identify non-SMC feature columns (for the ablated model)
    exclude_cols = [label_col, "open", "high", "low", "close", "volume"] + smc_cols
    non_smc_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ["float64", "int64"]]
    logger.info(f"Non-SMC features ({len(non_smc_cols)}): {non_smc_cols[:10]}...")

    # Prepare data
    from config.settings import get_label_params
    label_params = get_label_params(asset)

    # Train/test split (last 20% for test)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    results = {}

    # === FULL MODEL (all features) ===
    logger.info("\n--- Full Model (all features) ---")
    base_exclude = [label_col, "open", "high", "low", "close", "volume"]
    all_feature_cols = [c for c in df.columns if c not in base_exclude and df[c].dtype in ["float64", "int64"]]
    
    # Ensure alignment: drop any rows where features or label are NaN
    train_full = train_df[all_feature_cols + [label_col]].dropna()
    test_full = test_df[all_feature_cols + [label_col]].dropna()
    
    logger.info(f"Train: {len(train_full)} rows, Test: {len(test_full)} rows")
    logger.info(f"Train label distribution: {train_full[label_col].value_counts().to_dict()}")
    
    X_train_full = train_full[all_feature_cols].values
    X_test_full = test_full[all_feature_cols].values
    y_train = train_full[label_col].astype(int).values
    y_test = test_full[label_col].astype(int).values
    
    logger.info(f"X_train: {X_train_full.shape}, y_train: {y_train.shape}")
    logger.info(f"X_test: {X_test_full.shape}, y_test: {y_test.shape}")

    from xgboost import XGBClassifier
    full_model = XGBClassifier(
        n_estimators=500, max_depth=6, learning_rate=0.05,
        eval_metric="logloss", random_state=42, use_label_encoder=False
    )
    full_model.fit(X_train_full, y_train, eval_set=[(X_test_full, y_test)], verbose=False)

    y_pred_full = full_model.predict(X_test_full)
    y_prob_full = full_model.predict_proba(X_test_full)[:, 1]

    full_acc = accuracy_score(y_test, y_pred_full)
    full_auc = roc_auc_score(y_test, y_prob_full) if len(np.unique(y_test)) > 1 else 0
    logger.info(f"Full Model — Accuracy: {full_acc:.4f}, AUC-ROC: {full_auc:.4f}")

    results["full_model"] = {
        "features": len(all_feature_cols),
        "accuracy": round(full_acc, 4),
        "auc_roc": round(full_auc, 4),
        "feature_names": all_feature_cols,
    }

    # === ABLATED MODEL (no SMC features) ===
    logger.info("\n--- Ablated Model (no SMC features) ---")
    train_abl = train_df[non_smc_cols + [label_col]].dropna()
    test_abl = test_df[non_smc_cols + [label_col]].dropna()
    
    X_train_ablated = train_abl[non_smc_cols].values
    X_test_ablated = test_abl[non_smc_cols].values
    y_train_abl = train_abl[label_col].astype(int).values
    y_test_abl = test_abl[label_col].astype(int).values

    ablated_model = XGBClassifier(
        n_estimators=500, max_depth=6, learning_rate=0.05,
        eval_metric="logloss", random_state=42, use_label_encoder=False
    )
    ablated_model.fit(X_train_ablated, y_train_abl, eval_set=[(X_test_ablated, y_test_abl)], verbose=False)

    y_pred_ablated = ablated_model.predict(X_test_ablated)
    y_prob_ablated = ablated_model.predict_proba(X_test_ablated)[:, 1]

    ablated_acc = accuracy_score(y_test_abl, y_pred_ablated)
    ablated_auc = roc_auc_score(y_test_abl, y_prob_ablated) if len(np.unique(y_test_abl)) > 1 else 0
    logger.info(f"Ablated Model — Accuracy: {ablated_acc:.4f}, AUC-ROC: {ablated_auc:.4f}")

    results["ablated_model"] = {
        "features": len(non_smc_cols),
        "accuracy": round(ablated_acc, 4),
        "auc_roc": round(ablated_auc, 4),
        "feature_names": non_smc_cols,
    }

    # === DELTA ===
    acc_delta = full_acc - ablated_acc
    auc_delta = full_auc - ablated_auc

    results["delta"] = {
        "accuracy_improvement": round(acc_delta, 4),
        "accuracy_improvement_pct": round(acc_delta * 100, 2),
        "auc_improvement": round(auc_delta, 4),
        "smc_features_count": len(smc_cols),
    }

    logger.info(f"\n{'=' * 60}")
    logger.info(f"ABLATION RESULTS")
    logger.info(f"{'=' * 60}")
    logger.info(f"Full Model:    {full_acc:.4f} accuracy, {full_auc:.4f} AUC ({len(all_feature_cols)} features)")
    logger.info(f"Ablated Model: {ablated_acc:.4f} accuracy, {ablated_auc:.4f} AUC ({len(non_smc_cols)} features)")
    logger.info(f"SMC Impact:    +{acc_delta*100:.2f}% accuracy, +{auc_delta:.4f} AUC")
    logger.info(f"SMC Features:  {len(smc_cols)} features removed")
    logger.info(f"{'=' * 60}")

    # Save results
    output_path = Path(__file__).parent.parent / "reports" / f"ablation_{asset}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

    return results


if __name__ == "__main__":
    from data.loaders import load_asset_data
    for asset in ["gold", "silver"]:
        try:
            run_ablation(asset)
        except Exception as e:
            logger.error(f"Ablation failed for {asset}: {e}")
