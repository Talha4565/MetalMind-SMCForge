import requests
import json

BASE = "http://localhost:5000"

# Step 1: Register a test user
print("1. Register test user...")
r = requests.post(f"{BASE}/api/auth/register", json={
    "email": "test_refresh@example.com",
    "password": "TestPass123!",
    "name": "Refresh Test"
})
print(f"   Register: {r.status_code} - {r.json().get('message', r.json().get('error', ''))}")

# Step 2: Login to get tokens
print("2. Login...")
r = requests.post(f"{BASE}/api/auth/login", json={
    "email": "test_refresh@example.com",
    "password": "TestPass123!"
})
login_data = r.json()
print(f"   Login: {r.status_code}")
access_token = login_data.get('token') or login_data.get('access_token')
refresh_token = login_data.get('refreshToken') or login_data.get('refresh_token')
print(f"   Access token: {access_token[:30]}..." if access_token else "   No access token")
print(f"   Refresh token: {refresh_token[:30]}..." if refresh_token else "   No refresh token")

if not access_token or not refresh_token:
    print("   FAILED: Missing tokens")
    exit(1)

# Step 3: Test backtest endpoint with valid token
print("3. Test backtest/results with valid token...")
r = requests.get(f"{BASE}/api/backtest/results", headers={"Authorization": f"Bearer {access_token}"})
print(f"   Results: {r.status_code}")

# Step 4: Test refresh endpoint
print("4. Test /api/auth/refresh...")
r = requests.post(f"{BASE}/api/auth/refresh", json={"refresh_token": refresh_token})
print(f"   Refresh: {r.status_code}")
if r.status_code == 200:
    new_access = r.json().get('access_token')
    print(f"   New access token: {new_access[:30]}..." if new_access else "   No new token")
    
    # Step 5: Test backtest with new token
    print("5. Test backtest/results with refreshed token...")
    r = requests.get(f"{BASE}/api/backtest/results", headers={"Authorization": f"Bearer {new_access}"})
    print(f"   Results: {r.status_code}")
else:
    print(f"   Error: {r.json()}")

# Step 6: Test refresh with invalid token
print("6. Test refresh with invalid token...")
r = requests.post(f"{BASE}/api/auth/refresh", json={"refresh_token": "invalid_token"})
print(f"   Invalid refresh: {r.status_code} (expected 401)")

# Step 7: Test refresh with no token
print("7. Test refresh with no token...")
r = requests.post(f"{BASE}/api/auth/refresh", json={})
print(f"   No token: {r.status_code} (expected 400)")

print("\n=== ALL TESTS COMPLETE ===")
