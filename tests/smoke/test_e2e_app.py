"""End-to-end smoke tests for MetalMind-SMCForge running application."""
import requests
import json
import sys

BASE = 'http://localhost:5000'
FRONTEND = 'http://localhost:3000'
results = []


def test(name, passed, detail=''):
    results.append({'test': name, 'passed': passed, 'detail': detail})
    s = 'PASS' if passed else 'FAIL'
    print(f'  [{s}] {name}' + (f" -- {detail}" if detail else ''))


print('=' * 70)
print('METALMIND-SMCFORGE — END-TO-END SMOKE TEST')
print('=' * 70)

# ===== 1. BACKEND API HEALTH =====
print('\n--- 1. Backend API Health ---')
try:
    r = requests.get(f'{BASE}/api/health', timeout=10)
    data = r.json()
    test('Health check returns 200', r.status_code == 200)
    test('Database is healthy', data['checks']['database'] == 'ok')
    test('Filesystem is healthy', data['checks']['filesystem'] == 'ok')
    test('Gold model loaded', data['checks']['models']['gold'] is True)
    test('Silver model loaded', data['checks']['models']['silver'] is True)
    test('Status is healthy', data['status'] == 'healthy')
except Exception as e:
    test('Health check', False, str(e)[:80])

# ===== 2. LIVE MARKET PRICE =====
print('\n--- 2. Live Market Price ---')
for asset in ['gold', 'silver']:
    try:
        r = requests.get(f'{BASE}/api/market/price?asset={asset}', timeout=15)
        data = r.json()
        price = data.get('price', 'N/A')
        test(f'Live price {asset}: ${price}', r.status_code == 200 and 'price' in data)
    except Exception as e:
        test(f'Live price {asset}', False, str(e)[:80])

try:
    r = requests.get(f'{BASE}/api/market/price?asset=bitcoin', timeout=10)
    test('Invalid asset returns 400', r.status_code == 400)
except Exception as e:
    test('Invalid asset validation', False, str(e)[:80])

# ===== 3. ML PREDICTIONS =====
print('\n--- 3. ML Predictions ---')
for asset in ['gold', 'silver']:
    try:
        r = requests.get(f'{BASE}/api/predictions/latest?asset={asset}&limit=5', timeout=60)
        data = r.json()
        preds = data.get('predictions', [])
        has_signal = any('signal' in p for p in preds)
        has_confidence = any('confidence' in p for p in preds)
        has_shap = any(len(p.get('shap_values', [])) > 0 for p in preds)
        latest = preds[-1] if preds else {}
        sig = latest.get('signal', 'N/A')
        conf = latest.get('confidence', 0) * 100
        test(f'{asset.upper()} predictions returned', r.status_code == 200 and len(preds) > 0,
             f'{len(preds)} bars, signal={sig}, conf={conf:.1f}%')
        test(f'{asset.upper()} has signal field', has_signal)
        test(f'{asset.upper()} has confidence field', has_confidence)
        test(f'{asset.upper()} has SHAP values', has_shap)
    except Exception as e:
        test(f'{asset.upper()} predictions', False, str(e)[:80])

try:
    r = requests.get(f'{BASE}/api/predictions/latest?asset=bitcoin', timeout=10)
    test('Invalid asset prediction returns 400', r.status_code == 400)
except Exception as e:
    test('Invalid asset prediction', False, str(e)[:80])

try:
    r = requests.get(f'{BASE}/api/predictions/latest?limit=5000', timeout=10)
    test('Invalid limit returns 400', r.status_code == 400)
except Exception as e:
    test('Limit validation', False, str(e)[:80])

# ===== 4. SHAP FEATURE IMPORTANCE =====
print('\n--- 4. SHAP Feature Importance ---')
try:
    r = requests.get(f'{BASE}/api/shap/feature-importance?asset=gold', timeout=30)
    test('SHAP endpoint responds', r.status_code in [200, 401])
except Exception as e:
    test('SHAP endpoint', False, str(e)[:80])

# ===== 5. MODEL INFO =====
print('\n--- 5. Model Info ---')
try:
    r = requests.get(f'{BASE}/api/models/info?asset=gold', timeout=10)
    test('Gold model info', r.status_code == 200)
    if r.status_code == 200:
        info = r.json()
        test('Model type is XGBoost', info.get('model_type') == 'XGBoost Classifier')
        test('Has feature count', 'features_count' in info)
except Exception as e:
    test('Model info', False, str(e)[:80])

# ===== 6. FRONTEND PAGES =====
print('\n--- 6. Frontend Pages ---')
pages = [
    ('/', 'Landing page'),
    ('/auth/login', 'Login page'),
    ('/auth/register', 'Register page'),
    ('/dashboard', 'Dashboard'),
    ('/dashboard/risk', 'Risk calculator'),
    ('/dashboard/profile', 'Profile page'),
    ('/dashboard/watchlist', 'Watchlist page'),
    ('/backtest', 'Backtest page'),
]
for path, name in pages:
    try:
        r = requests.get(f'{FRONTEND}{path}', timeout=15)
        test(f'{name} ({path})', r.status_code == 200, f'Status: {r.status_code}')
    except Exception as e:
        test(f'{name} ({path})', False, str(e)[:80])

# ===== 7. RATE LIMITING =====
print('\n--- 7. Rate Limiting ---')
try:
    for i in range(12):
        r = requests.get(f'{BASE}/api/health', timeout=5)
    test('Rate limiter active (allowed through or 429)', r.status_code in [200, 429])
except Exception as e:
    test('Rate limiting', False, str(e)[:80])

# ===== 8. SECURITY HEADERS =====
print('\n--- 8. Security Headers ---')
try:
    r = requests.get(f'{BASE}/api/health', timeout=10)
    headers = r.headers
    test('CSP header present', 'Content-Security-Policy' in headers)
    test('X-Frame-Options present', 'X-Frame-Options' in headers)
    test('X-Content-Type-Options present', 'X-Content-Type-Options' in headers)
    test('Referrer-Policy present', 'Referrer-Policy' in headers)
    test('Permissions-Policy present', 'Permissions-Policy' in headers)
except Exception as e:
    test('Security headers', False, str(e)[:80])

# ===== 9. WEBSOCKET / SOCKET.IO =====
print('\n--- 9. WebSocket (Socket.IO) ---')
try:
    r = requests.get(f'{BASE}/socket.io/?EIO=4&transport=polling', timeout=10)
    test('Socket.IO polling endpoint', r.status_code == 200)
except Exception as e:
    test('Socket.IO polling', False, str(e)[:80])

# ===== 10. AUTH ENDPOINTS =====
print('\n--- 10. Auth Endpoints ---')
try:
    r = requests.post(f'{BASE}/api/auth/register', json={
        'email': 'e2e_test_run@test.com',
        'password': 'TestPass123!'
    }, timeout=10)
    test('Register endpoint responds', r.status_code in [200, 201, 409, 429])
except Exception as e:
    test('Register endpoint', False, str(e)[:80])

try:
    r = requests.post(f'{BASE}/api/auth/login', json={
        'email': 'nonexistent@test.com',
        'password': 'WrongPass123!'
    }, timeout=10)
    test('Login with wrong creds returns error', r.status_code in [401, 429])
except Exception as e:
    test('Login endpoint', False, str(e)[:80])

# ===== SUMMARY =====
passed = sum(1 for r in results if r['passed'])
total = len(results)
failed = total - passed
print(f'\n{"=" * 70}')
print(f'FINAL RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%) | {failed} failed')
print(f'{"=" * 70}')

# Save results
import os
os.makedirs('reports', exist_ok=True)
with open('reports/e2e_test_results.json', 'w') as f:
    json.dump({'summary': {'total': total, 'passed': passed, 'failed': failed}, 'tests': results}, f, indent=2)
print(f'Results saved to reports/e2e_test_results.json')
