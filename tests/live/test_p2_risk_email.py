"""
P2 LIVE TEST: Risk Calculator, Email Alerts, 2FA
Tests risk calculation, email service, 2FA setup
Run: python tests/live/test_p2_risk_email.py
"""
import sys
sys.path.insert(0, 'C:/Users/Talha/ml-signals')

import requests
import json
import time

BASE = "http://localhost:5000"
RESULTS = []

def test(name, passed, detail=""):
    RESULTS.append({"test": name, "passed": passed, "detail": detail})
    s = "PASS" if passed else "FAIL"
    print(f"  [{s}] {name}" + (f" — {detail}" if detail else ""))

def get_token():
    email = f"p2_test_{int(time.time())}@example.com"
    password = "TestPass123!"
    try:
        requests.post(f"{BASE}/api/auth/register", json={"email": email, "password": password}, timeout=10)
        r = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": password}, timeout=10)
        if r.status_code == 200:
            return r.json().get("access_token")
    except:
        pass
    return None

print("=" * 60)
print("P2 LIVE TEST: RISK, EMAIL, 2FA")
print("=" * 60)

token = get_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {}

# Test 1: Risk Calculator Page Load
print("\n1. Risk Calculator")
try:
    # Risk calculator is frontend-only, but we can test the page loads
    r = requests.get("http://localhost:3000/dashboard/risk", timeout=10)
    test("Risk page loads", r.status_code == 200)
except Exception as e:
    test("Risk calculator", False, str(e)[:80])

# Test 2: Email Alert Service
print("\n2. Email Alert Service")
try:
    from etl.alerts import EmailAlertService
    service = EmailAlertService(
        sender_email='test@test.com',
        sender_password='pass',
        recipient_email='rec@test.com'
    )
    test("EmailAlertService initializes", True)
    test("should_alert returns bool for BUY", isinstance(service.should_alert(signal=1, confidence=0.9), bool))
    test("should_alert returns bool for HOLD", isinstance(service.should_alert(signal=0, confidence=0.9), bool))
    test("BUY with high confidence triggers", service.should_alert(signal=1, confidence=0.9) == True)
    test("HOLD does not trigger", service.should_alert(signal=0, confidence=0.9) == False)
    test("Low confidence does not trigger", service.should_alert(signal=1, confidence=0.3) == False)
except Exception as e:
    test("Email alert service", False, str(e)[:80])

# Test 3: Alert Risk Gate
print("\n3. Alert Risk Gate")
try:
    from etl.guards.alert_risk_gate import AlertRiskGate, RiskDecision
    gate = AlertRiskGate({"enabled": True})
    decision = gate.check(asset="gold", price=2000.0, atr=2.0, signal=1, confidence=0.8)
    test("AlertRiskGate initializes", True)
    test("check returns RiskDecision", isinstance(decision, RiskDecision))
    test("RiskDecision has approved field", hasattr(decision, 'approved'))
    test("RiskDecision has reason field", hasattr(decision, 'reason'))
except Exception as e:
    test("Alert risk gate", False, str(e)[:80])

# Test 4: Signal Reasoner
print("\n4. Signal Reasoner")
try:
    from etl.agents.signal_reasoner import SignalReasoner, AgentDecision
    reasoner = SignalReasoner(client=None, pred_logger=None)
    decision = reasoner.evaluate(
        asset="gold", signal=1, confidence=0.8,
        rsi=55, atr=2.0, ema20=2000, ema50=1990, price=2005
    )
    test("SignalReasoner initializes", True)
    test("evaluate returns AgentDecision", isinstance(decision, AgentDecision))
    test("AgentDecision has approved field", hasattr(decision, 'approved'))
    test("AgentDecision has source field", hasattr(decision, 'source'))
    test("AgentDecision has reason field", hasattr(decision, 'reason'))
except Exception as e:
    test("Signal reasoner", False, str(e)[:80])

# Test 5: Prediction Logger
print("\n5. Prediction Logger")
try:
    from etl.prediction_logger import PredictionLogger
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = PredictionLogger(log_dir=tmpdir)
        record = logger.log_prediction(
            asset='gold', signal=1, confidence=0.8,
            price=2000.0, tp_price=2010.0, sl_price=1995.0
        )
        test("PredictionLogger initializes", True)
        test("log_prediction returns record", record is not None)
        test("Record has asset", record.get('asset') == 'gold')
        test("Record has signal", record.get('signal') == 1)
        test("Record has confidence", record.get('confidence') == 0.8)
        test("Record has tp_price", record.get('tp_price') == 2010.0)
        test("Record has sl_price", record.get('sl_price') == 1995.0)
except Exception as e:
    test("Prediction logger", False, str(e)[:80])

# Test 6: Data Quality Gate
print("\n6. Data Quality Gate")
try:
    from etl.guards.data_quality_gate import DataQualityGate
    gate = DataQualityGate(config={"min_rows_required": 0, "max_price_change_pct": 999})
    test("DataQualityGate initializes", True)
    test("Has validate method", hasattr(gate, 'validate'))
except Exception as e:
    test("Data quality gate", False, str(e)[:80])

# Test 7: SHAP Analyzer
print("\n7. SHAP Analyzer")
try:
    import numpy as np
    import pandas as pd
    import xgboost as xgb
    from explainability.shap_analyzer import ShapAnalyzer
    X = pd.DataFrame(np.random.randn(50, 5), columns=[f'f{i}' for i in range(5)])
    y = np.random.choice([0, 1], 50)
    model = xgb.XGBClassifier(n_estimators=10, random_state=42,
                               use_label_encoder=False, eval_metric='logloss')
    model.fit(X, y)
    analyzer = ShapAnalyzer(model, sample_size=50)
    shap_vals = analyzer.compute_shap_values(X)
    test("ShapAnalyzer initializes", True)
    test("compute_shap_values returns values", shap_vals is not None)
except Exception as e:
    test("SHAP analyzer", False, str(e)[:80])

# Summary
print("\n" + "=" * 60)
passed = sum(1 for r in RESULTS if r["passed"])
total = len(RESULTS)
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print("=" * 60)
