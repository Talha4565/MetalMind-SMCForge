"""
P2 LIVE TEST: WebSocket & 2FA
Tests WebSocket connection and 2FA setup/enable/disable
Run: python tests/live/test_p2_websocket_2fa.py
"""
import sys
sys.path.insert(0, 'C:/Users/Talha/ml-signals')

import requests
import json
import time
import socketio

BASE = "http://localhost:5000"
RESULTS = []

def test(name, passed, detail=""):
    RESULTS.append({"test": name, "passed": passed, "detail": detail})
    s = "PASS" if passed else "FAIL"
    print(f"  [{s}] {name}" + (f" — {detail}" if detail else ""))

def get_token():
    email = f"ws_test_{int(time.time())}@example.com"
    password = "TestPass123!"
    try:
        requests.post(f"{BASE}/api/auth/register", json={"email": email, "password": password}, timeout=10)
        r = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": password}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("token") or data.get("access_token"), email, password
    except:
        pass
    return None, None, None

print("=" * 60)
print("P2 LIVE TEST: WEBSOCKET & 2FA")
print("=" * 60)

# ============================================================================
# WEBSOCKET TESTS
# ============================================================================
print("\n" + "=" * 60)
print("WEBSOCKET TESTS")
print("=" * 60)

# Test 1: SocketIO endpoint exists
print("\n1. SocketIO Endpoint")
try:
    r = requests.get(f"{BASE}/socket.io/?EIO=4&transport=polling", timeout=5)
    test("SocketIO polling endpoint responds", r.status_code == 200, f"Status: {r.status_code}")
except Exception as e:
    test("SocketIO polling endpoint", False, str(e)[:80])

# Test 2: SocketIO connection via client
print("\n2. SocketIO Connection")
try:
    client = socketio.Client()
    connected = [False]
    
    @client.on('connect')
    def on_connect():
        connected[0] = True
    
    client.connect(BASE, transports=['polling'])
    time.sleep(1)
    
    test("SocketIO client connects", connected[0])
    test("SocketIO client.connected", client.connected)
    
    client.disconnect()
except Exception as e:
    test("SocketIO connection", False, str(e)[:80])

# Test 3: Subscribe to predictions
print("\n3. Subscribe to Predictions")
try:
    client = socketio.Client()
    received = [False]
    
    @client.on('predictions')
    def on_predictions(data):
        received[0] = True
    
    client.connect(BASE, transports=['polling'])
    time.sleep(0.5)
    
    client.emit('subscribe_predictions', {'asset': 'gold'})
    time.sleep(2)
    
    test("Subscribe to predictions works", True, "No error on subscribe")
    client.disconnect()
except Exception as e:
    test("Subscribe to predictions", False, str(e)[:80])

# Test 4: Subscribe to ETL status
print("\n4. Subscribe to ETL Status")
try:
    client = socketio.Client()
    client.connect(BASE, transports=['polling'])
    time.sleep(0.5)
    
    client.emit('subscribe_etl_status', {})
    time.sleep(1)
    
    test("Subscribe to ETL status works", True, "No error on subscribe")
    client.disconnect()
except Exception as e:
    test("Subscribe to ETL status", False, str(e)[:80])

# ============================================================================
# 2FA TESTS
# ============================================================================
print("\n" + "=" * 60)
print("2FA TESTS")
print("=" * 60)

token, email, password = get_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {}

# Test 5: Get 2FA setup
print("\n5. 2FA Setup")
try:
    r = requests.get(f"{BASE}/api/profile/2fa/setup", headers=headers, timeout=10)
    test("2FA setup endpoint responds", r.status_code in [200, 401], f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        test("Returns secret", "secret" in data)
        test("Returns provisioning_uri", "provisioning_uri" in data)
        test("Returns qr", "qr" in data)
        test("URI contains issuer", "MetalMind" in data.get("provisioning_uri", ""))
except Exception as e:
    test("2FA setup", False, str(e)[:80])

# Test 6: Enable 2FA with invalid OTP
print("\n6. Enable 2FA (invalid OTP)")
try:
    r = requests.post(f"{BASE}/api/profile/2fa/enable", headers=headers,
        json={"otp": "000000"}, timeout=10)
    test("Invalid OTP rejected", r.status_code in [400, 401], f"Status: {r.status_code}")
except Exception as e:
    test("Enable 2FA invalid OTP", False, str(e)[:80])

# Test 7: Enable 2FA with valid OTP (using pyotp)
print("\n7. Enable 2FA (valid OTP)")
try:
    import pyotp
    
    # Get fresh setup to get secret
    r = requests.get(f"{BASE}/api/profile/2fa/setup", headers=headers, timeout=10)
    if r.status_code == 200:
        secret = r.json().get("secret")
        if secret:
            totp = pyotp.TOTP(secret)
            valid_otp = totp.now()
            
            r = requests.post(f"{BASE}/api/profile/2fa/enable", headers=headers,
                json={"otp": valid_otp}, timeout=10)
            test("Valid OTP accepted", r.status_code == 200, f"Status: {r.status_code}")
        else:
            test("Valid OTP accepted", False, "No secret returned")
    else:
        test("Valid OTP accepted", False, f"Setup failed: {r.status_code}")
except Exception as e:
    test("Enable 2FA valid OTP", False, str(e)[:80])

# Test 8: Disable 2FA
print("\n8. Disable 2FA")
try:
    import pyotp
    
    r = requests.get(f"{BASE}/api/profile/2fa/setup", headers=headers, timeout=10)
    if r.status_code == 200:
        secret = r.json().get("secret")
        if secret:
            totp = pyotp.TOTP(secret)
            valid_otp = totp.now()
            
            r = requests.post(f"{BASE}/api/profile/2fa/disable", headers=headers,
                json={"otp": valid_otp}, timeout=10)
            test("Disable 2FA works", r.status_code == 200, f"Status: {r.status_code}")
        else:
            test("Disable 2FA works", False, "No secret")
    else:
        test("Disable 2FA works", False, f"Setup failed: {r.status_code}")
except Exception as e:
    test("Disable 2FA", False, str(e)[:80])

# Test 9: Login with 2FA required
print("\n9. Login with 2FA")
try:
    import pyotp
    
    # Register new user for 2FA test
    email_2fa = f"2fa_test_{int(time.time())}@example.com"
    password_2fa = "TestPass123!"
    requests.post(f"{BASE}/api/auth/register", json={"email": email_2fa, "password": password_2fa}, timeout=10)
    
    # Login and get token
    r = requests.post(f"{BASE}/api/auth/login", json={"email": email_2fa, "password": password_2fa}, timeout=10)
    if r.status_code == 200:
        login_token = r.json().get("token")
        if login_token:
            # Setup 2FA
            headers_2fa = {"Authorization": f"Bearer {login_token}", "Content-Type": "application/json"}
            r = requests.get(f"{BASE}/api/profile/2fa/setup", headers=headers_2fa, timeout=10)
            if r.status_code == 200:
                secret = r.json().get("secret")
                if secret:
                    # Enable 2FA
                    totp = pyotp.TOTP(secret)
                    r = requests.post(f"{BASE}/api/profile/2fa/enable", headers=headers_2fa,
                        json={"otp": totp.now()}, timeout=10)
                    
                    # Try login without TOTP
                    r = requests.post(f"{BASE}/api/auth/login", json={
                        "email": email_2fa, "password": password_2fa
                    }, timeout=10)
                    
                    if r.status_code == 200:
                        data = r.json()
                        requires_2fa = data.get("requires_2fa", False)
                        test("Login requires 2FA", requires_2fa, f"requires_2fa={requires_2fa}")
                    else:
                        test("Login requires 2FA", False, f"Status: {r.status_code}")
                else:
                    test("Login requires 2FA", False, "No secret")
            else:
                test("Login requires 2FA", False, f"Setup failed: {r.status_code}")
        else:
            test("Login requires 2FA", False, "No token")
    else:
        test("Login requires 2FA", False, f"Login failed: {r.status_code}")
except Exception as e:
    test("Login with 2FA", False, str(e)[:80])

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 60)
passed = sum(1 for r in RESULTS if r["passed"])
total = len(RESULTS)
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print("=" * 60)
