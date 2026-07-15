"""
P0 LIVE TEST: Authentication Flow
Tests register → login → token → protected routes
Run: python -m pytest tests/live/test_auth.py -v
"""
import requests
import json
import time

BASE = "http://localhost:5000"
RESULTS = []

def test(name, passed, detail=""):
    RESULTS.append({"test": name, "passed": passed, "detail": detail})
    s = "PASS" if passed else "FAIL"
    print(f"  [{s}] {name}" + (f" — {detail}" if detail else ""))

print("=" * 60)
print("P0 LIVE TEST: AUTHENTICATION")
print("=" * 60)

# Test 1: Health check
print("\n1. API Health")
try:
    r = requests.get(f"{BASE}/api/health", timeout=10)
    test("Health endpoint", r.status_code == 200, f"Status: {r.status_code}")
except Exception as e:
    test("Health endpoint", False, str(e)[:80])

# Test 2: Register new user
print("\n2. Register")
test_email = f"test_{int(time.time())}@example.com"
test_password = "TestPass123!"
try:
    r = requests.post(f"{BASE}/api/auth/register", json={
        "email": test_email,
        "password": test_password
    }, timeout=10)
    test("Register returns 200/201", r.status_code in [200, 201], f"Status: {r.status_code}")
except Exception as e:
    test("Register endpoint", False, str(e)[:80])

# Test 3: Login
print("\n3. Login")
token = None
try:
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": test_email,
        "password": test_password
    }, timeout=10)
    test("Login returns 200", r.status_code == 200, f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token") or data.get("token")
        test("Token returned", token is not None, f"Token: {token[:20]}..." if token else "None")
except Exception as e:
    test("Login endpoint", False, str(e)[:80])

# Test 4: Wrong password
print("\n4. Wrong Password")
try:
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": test_email,
        "password": "WrongPassword!"
    }, timeout=10)
    test("Wrong password rejected", r.status_code in [400, 401], f"Status: {r.status_code}")
except Exception as e:
    test("Wrong password", False, str(e)[:80])

# Test 5: Protected route without token
print("\n5. Protected Route (no token)")
try:
    r = requests.get(f"{BASE}/api/shap/feature-importance", timeout=10)
    test("No token returns 401", r.status_code == 401, f"Status: {r.status_code}")
except Exception as e:
    test("Protected route (no token)", False, str(e)[:80])

# Test 6: Protected route with token
print("\n6. Protected Route (with token)")
if token:
    try:
        r = requests.get(f"{BASE}/api/shap/feature-importance",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10)
        test("Valid token returns 200", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        test("Protected route (with token)", False, str(e)[:80])
else:
    test("Protected route (with token)", False, "No token available")

# Test 7: Invalid token
print("\n7. Invalid Token")
try:
    r = requests.get(f"{BASE}/api/shap/feature-importance",
        headers={"Authorization": "Bearer invalid_token_12345"},
        timeout=10)
    test("Invalid token rejected", r.status_code == 401, f"Status: {r.status_code}")
except Exception as e:
    test("Invalid token", False, str(e)[:80])

# Summary
print("\n" + "=" * 60)
passed = sum(1 for r in RESULTS if r["passed"])
total = len(RESULTS)
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print("=" * 60)
