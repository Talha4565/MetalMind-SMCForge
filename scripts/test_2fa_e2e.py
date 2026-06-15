#!/usr/bin/env python3
import requests, time, hmac, hashlib, struct, base64, os, sys

API_URL = os.environ.get('API_URL', 'http://localhost:5000')


def totp_code(secret, digits=6, interval=30):
    # Base32 decode the secret (allow lower/upper case)
    key = base64.b32decode(secret, casefold=True)
    t = int(time.time()) // interval
    msg = struct.pack('>Q', t)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = struct.unpack('>I', h[offset:offset+4])[0] & 0x7FFFFFFF
    return str(code % (10 ** digits)).zfill(digits)


email = f"e2e+{int(time.time())}@example.com"
password = 'Testpass123!'
print('Using API_URL=', API_URL)
print('Registering user:', email)

try:
    r = requests.post(f"{API_URL}/api/auth/register", json={'email': email, 'password': password}, timeout=10)
    print('register', r.status_code, r.text)
except Exception as e:
    print('Register request failed:', e)
    sys.exit(1)

# Login
try:
    r = requests.post(f"{API_URL}/api/auth/login", json={'email': email, 'password': password}, timeout=10)
    print('login (initial)', r.status_code, r.text)
    data = r.json()
    token = data.get('token') or (data.get('data', {}).get('tokens', {}).get('accessToken'))
    if not token:
        print('No token returned; aborting')
        sys.exit(1)
except Exception as e:
    print('Login request failed:', e)
    sys.exit(1)

headers = {'Authorization': f'Bearer {token}'}

# Get 2FA setup
try:
    r = requests.get(f"{API_URL}/api/profile/2fa/setup", headers=headers, timeout=10)
    print('2fa setup', r.status_code)
    setup = r.json()
    print(setup)
    secret = setup.get('secret')
    if not secret:
        print('No secret returned; aborting')
        sys.exit(1)
except Exception as e:
    print('2FA setup request failed:', e)
    sys.exit(1)

# Compute TOTP and enable
code = totp_code(secret)
print('Computed TOTP code:', code)

try:
    r = requests.post(f"{API_URL}/api/profile/2fa/enable", headers=headers, json={'otp': code}, timeout=10)
    print('enable 2fa', r.status_code, r.text)
except Exception as e:
    print('Enable request failed:', e)
    sys.exit(1)

# Attempt login without 2FA code (should prompt requires_2fa or similar)
try:
    r = requests.post(f"{API_URL}/api/auth/login", json={'email': email, 'password': password}, timeout=10)
    print('login after enable (no totp)', r.status_code, r.text)
    print('Response JSON:', r.json())
except Exception as e:
    print('Login check failed:', e)

# Attempt login with TOTP code
code2 = totp_code(secret)
try:
    r = requests.post(f"{API_URL}/api/auth/login", json={'email': email, 'password': password, 'totp_code': code2}, timeout=10)
    print('login with totp', r.status_code, r.text)
except Exception as e:
    print('Login with totp failed:', e)

print('E2E script finished')
