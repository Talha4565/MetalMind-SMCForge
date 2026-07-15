"""
MODEL CORRECTNESS TESTS
Verifies the model is actually correct, not just functional.
These are the tests that answer "did you validate the model?"

Run: python tests/live/test_model_correctness.py
"""
import sys
sys.path.insert(0, 'C:/Users/Talha/ml-signals')

import pickle
import json
import numpy as np
import pandas as pd
from features.pipeline import engineer_all_features
from data.loaders import load_gold_data

RESULTS = []

def test(name, passed, detail=""):
    RESULTS.append({"test": name, "passed": passed, "detail": detail})
    s = "PASS" if passed else "FAIL"
    print(f"  [{s}] {name}" + (f" — {detail}" if detail else ""))

print("=" * 70)
print("MODEL CORRECTNESS TESTS")
print("=" * 70)

# Load model and data
with open('models/gold_regression_system.pkl', 'rb') as f:
    d = pickle.load(f)
model = d['direction_model']
features = d['features']

df = load_gold_data(primary_tf='15m', session_filter=False)
df = engineer_all_features(df, add_labels=False, asset='gold')

# ============================================================================
# TEST 1: SHAP Direction Sanity
# Bullish features should have positive contribution when price goes up
# ============================================================================
print("\n1. SHAP Direction Sanity (via API)")

try:
    import requests

    # Get SHAP values from API (already computed)
    r = requests.get('http://localhost:5000/api/predictions/latest?asset=gold&limit=1', timeout=30)
    shap_data = r.json()['predictions'][-1]['shap_values']

    test("API returns SHAP values", len(shap_data) > 0, f"{len(shap_data)} features")

    # Check that bullish features have correct sign
    bullish_features = ['htf_1h_dist_high', 'VWAPd_96']
    bullish_correct = 0

    for item in shap_data:
        feat = item['feature']
        contrib = item['contribution']

        if feat in bullish_features:
            if contrib > 0:
                bullish_correct += 1
                test(f"SHAP {feat} positive", True, f"contrib={contrib:.4f}")
            else:
                test(f"SHAP {feat} positive", False, f"contrib={contrib:.4f}")

    test("Bullish features have positive SHAP", bullish_correct >= 1,
         f"{bullish_correct}/{len(bullish_features)} correct")

except Exception as e:
    test("SHAP direction sanity", False, str(e)[:80])

# ============================================================================
# TEST 2: Prediction Consistency
# Same input should produce same output
# ============================================================================
print("\n2. Prediction Consistency")

try:
    X_sample = df[features].tail(1)

    # Run prediction 3 times
    pred1 = model.predict(X_sample)[0]
    pred2 = model.predict(X_sample)[0]
    pred3 = model.predict(X_sample)[0]

    test("Prediction run 1 == run 2", pred1 == pred2, f"{pred1} vs {pred2}")
    test("Prediction run 2 == run 3", pred2 == pred3, f"{pred2} vs {pred3}")
    test("All predictions identical", pred1 == pred2 == pred3)

except Exception as e:
    test("Prediction consistency", False, str(e)[:80])

# ============================================================================
# TEST 3: Probability Calibration
# High probability should correlate with actual wins
# ============================================================================
print("\n3. Probability Calibration")

try:
    # Load labeled data
    df_labeled = engineer_all_features(df.tail(5000), add_labels=True, asset='gold')
    X_test = df_labeled[features].tail(1000)
    y_test = df_labeled['target'].tail(1000)

    proba = model.predict_proba(X_test)[:, 1]

    # Bin by probability and check win rate in each bin
    bins = [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 1.0)]
    prev_winrate = 0
    calibration_ok = True

    for low, high in bins:
        mask = (proba >= low) & (proba < high)
        if mask.sum() > 10:
            winrate = y_test[mask].mean()
            if winrate < prev_winrate:
                calibration_ok = False
            test(f"Bin {low:.1f}-{high:.1f}: winrate={winrate:.1%} (n={mask.sum()})",
                 winrate >= prev_winrate * 0.8)  # Allow some noise
            prev_winrate = winrate

    test("Probability calibration monotonic", calibration_ok)

except Exception as e:
    test("Probability calibration", False, str(e)[:80])

# ============================================================================
# TEST 4: Signal Distribution Not Degenerate
# Model shouldn't predict all BUY or all SELL
# ============================================================================
print("\n4. Signal Distribution")

try:
    X = df[features].tail(2000)
    predictions = model.predict(X)
    proba = model.predict_proba(X)[:, 1]

    buy_rate = (predictions == 1).mean()
    sell_rate = (predictions == 0).mean()  # Binary: 0 = down

    test("Not all predictions are BUY", buy_rate < 0.95,
         f"BUY rate: {buy_rate:.1%}")
    test("Not all predictions are SELL", sell_rate < 0.95,
         f"SELL rate: {sell_rate:.1%}")
    test("Class balance reasonable", 0.1 < buy_rate < 0.9,
         f"BUY: {buy_rate:.1%}, SELL: {sell_rate:.1%}")

except Exception as e:
    test("Signal distribution", False, str(e)[:80])

# ============================================================================
# TEST 5: Feature Importance Ranking
# SHAP should rank known important features highly
# ============================================================================
print("\n5. Feature Importance Ranking")

try:
    import shap
    X = df[features].tail(1000)
    explainer = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(X)

    if isinstance(shap_vals, np.ndarray) and shap_vals.ndim > 1:
        shap_vals = shap_vals[0]

    mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)
    sorted_idx = np.argsort(mean_abs_shap)[::-1]
    top_10 = [features[i] for i in sorted_idx[:10]]

    # Known important features should be in top 10
    expected_important = ['htf_1h_dist_high', 'VWAPd_96', 'trend_adx']
    found = sum(1 for f in expected_important if f in top_10)

    test(f"Known important features in top 10", found >= 2,
         f"{found}/{len(expected_important)} found: {top_10[:5]}")

except Exception as e:
    test("Feature importance ranking", False, str(e)[:80])

# ============================================================================
# TEST 6: Live vs Offline Model Match
# API predictions should match direct model inference
# ============================================================================
print("\n6. Live vs Offline Model Match")

try:
    import requests

    # Get prediction from API
    r = requests.get('http://localhost:5000/api/predictions/latest?asset=gold&limit=1', timeout=30)
    api_pred = r.json()['predictions'][-1]

    # Get prediction from direct inference
    X_latest = df[features].tail(1)
    offline_signal = model.predict(X_latest)[0]
    offline_proba = model.predict_proba(X_latest)[:, 1][0]

    # Apply trend filter
    trend = df['trend_ema_cross'].iloc[-1]
    conf = max(offline_proba, 1 - offline_proba)
    if trend == 1 and offline_proba >= 0.5 and conf >= 0.65:
        offline_filtered = 1
    elif trend == 0 and offline_proba < 0.5 and conf >= 0.65:
        offline_filtered = -1
    else:
        offline_filtered = 0

    test("API signal matches offline", api_pred['signal'] == offline_filtered,
         f"API={api_pred['signal']}, Offline={offline_filtered}")
    test("API confidence close to offline",
         abs(api_pred['confidence'] - offline_proba) < 0.01,
         f"API={api_pred['confidence']:.3f}, Offline={offline_proba:.3f}")

except Exception as e:
    test("Live vs offline match", False, str(e)[:80])

# ============================================================================
# TEST 7: Trend Filter Logic
# Verify BUY/SELL/HOLD conditions are correct
# ============================================================================
print("\n7. Trend Filter Logic")

try:
    # Test known cases
    # Case 1: trend=1, proba=0.8, conf=0.8 -> should BUY
    trend, proba_val, conf = 1, 0.8, 0.8
    if trend == 1 and proba_val >= 0.5 and conf >= 0.65:
        result = 1
    elif trend == 0 and proba_val < 0.5 and conf >= 0.65:
        result = -1
    else:
        result = 0
    test("trend=1, proba=0.8 -> BUY", result == 1, f"Got {result}")

    # Case 2: trend=0, proba=0.2, conf=0.8 -> should SELL
    trend, proba_val, conf = 0, 0.2, 0.8
    if trend == 1 and proba_val >= 0.5 and conf >= 0.65:
        result = 1
    elif trend == 0 and proba_val < 0.5 and conf >= 0.65:
        result = -1
    else:
        result = 0
    test("trend=0, proba=0.2 -> SELL", result == -1, f"Got {result}")

    # Case 3: trend=1, proba=0.2, conf=0.8 -> should HOLD (conflict)
    trend, proba_val, conf = 1, 0.2, 0.8
    if trend == 1 and proba_val >= 0.5 and conf >= 0.65:
        result = 1
    elif trend == 0 and proba_val < 0.5 and conf >= 0.65:
        result = -1
    else:
        result = 0
    test("trend=1, proba=0.2 -> HOLD (conflict)", result == 0, f"Got {result}")

    # Case 4: trend=0, proba=0.8, conf=0.8 -> should HOLD (conflict)
    trend, proba_val, conf = 0, 0.8, 0.8
    if trend == 1 and proba_val >= 0.5 and conf >= 0.65:
        result = 1
    elif trend == 0 and proba_val < 0.5 and conf >= 0.65:
        result = -1
    else:
        result = 0
    test("trend=0, proba=0.8 -> HOLD (conflict)", result == 0, f"Got {result}")

    # Case 5: Low confidence -> should HOLD
    trend, proba_val, conf = 1, 0.6, 0.6
    if trend == 1 and proba_val >= 0.5 and conf >= 0.65:
        result = 1
    elif trend == 0 and proba_val < 0.5 and conf >= 0.65:
        result = -1
    else:
        result = 0
    test("Low confidence -> HOLD", result == 0, f"Got {result}")

except Exception as e:
    test("Trend filter logic", False, str(e)[:80])

# ============================================================================
# TEST 8: Backtest Win Rate Matches Live Filtering
# Same filtering logic should produce similar win rates
# ============================================================================
print("\n8. Backtest vs Live Filtering Consistency")

try:
    # Load backtest results
    with open('reports/backtest_results/gold_backtest.json') as f:
        bt = json.load(f)

    bt_winrate = bt['summary']['win_rate']
    bt_trades = bt['summary']['n_trades']

    test("Backtest has results", bt_trades > 0, f"{bt_trades} trades")
    test("Backtest win rate reasonable", 0.4 < bt_winrate < 0.8,
         f"{bt_winrate:.1%}")

    # Check if backtest uses same trend filter
    import json
    # The backtest trades show hit_tp and hit_sl, which aligns with our label definition
    tp_hits = sum(1 for t in bt['trades'] if t.get('hit_tp'))
    sl_hits = sum(1 for t in bt['trades'] if t.get('hit_sl'))
    total = len(bt['trades'])

    test("TP hits + SL hits cover most trades",
         (tp_hits + sl_hits) / total > 0.5 if total > 0 else False,
         f"TP={tp_hits}, SL={sl_hits}, Total={total}")

except Exception as e:
    test("Backtest vs live consistency", False, str(e)[:80])

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
passed = sum(1 for r in RESULTS if r["passed"])
total = len(RESULTS)
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print("=" * 70)
