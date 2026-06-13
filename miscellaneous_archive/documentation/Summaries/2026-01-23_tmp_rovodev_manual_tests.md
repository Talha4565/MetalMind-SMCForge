# 🧪 MANUAL TESTING GUIDE

After running the automated test script, manually verify these items:

---

## 1️⃣ START THE SERVER

```bash
cd ml-signals
python run.py
```

**Check startup logs for:**
- ✅ "Server ready - models will be loaded on first request (lazy loading)"
- ✅ "ModelManager, PredictionCache, and BacktestManager initialized"
- ✅ No SECRET_KEY warnings (or warning about dev mode)

---

## 2️⃣ RUN AUTOMATED TESTS

```bash
cd ml-signals
python tmp_rovodev_test_all_fixes.py
```

**Expected output:**
- All tests should pass (green checkmarks)
- Some warnings OK (yellow) if optional features not installed
- No red failures

---

## 3️⃣ TEST WITH CURL

### Health Check
```bash
curl http://localhost:5000/api/health
```

**Expected JSON:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-23T...",
  "checks": {
    "database": "ok",
    "filesystem": "ok",
    "models": {"gold": false, "silver": false}
  },
  "version": "1.0.0"
}
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@metalmind.com","password":"Demo123!@#"}'
```

**Expected:** Token in response

### Test Rate Limiting
```bash
# Run this 15 times rapidly
for i in {1..15}; do curl http://localhost:5000/api/health; done
```

**Expected:** Some requests return 429 (Too Many Requests)

### Test Input Validation
```bash
TOKEN="your-token-here"

# Invalid limit (should fail)
curl "http://localhost:5000/api/predictions/latest?limit=999999" \
  -H "Authorization: Bearer $TOKEN"

# Expected: 400 error "Limit must be between 1 and 1000"

# Valid limit (should work)
curl "http://localhost:5000/api/predictions/latest?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Test Path Traversal Protection
```bash
TOKEN="your-token-here"

curl "http://localhost:5000/api/backtest/results?asset=../../etc/passwd" \
  -H "Authorization: Bearer $TOKEN"

# Expected: 400 error "Invalid asset"
```

---

## 4️⃣ TEST COMPRESSION

```bash
# Check if compressed
curl -I -H "Accept-Encoding: gzip" http://localhost:5000/api/health
```

**Look for:** `Content-Encoding: gzip`

**If NOT present:** Install Flask-Compress:
```bash
pip install flask-compress
```

---

## 5️⃣ TEST CACHING PERFORMANCE

```bash
TOKEN="your-token-here"

# First request (cache miss - slow)
time curl "http://localhost:5000/api/predictions/latest?limit=100" \
  -H "Authorization: Bearer $TOKEN" > /dev/null

# Second request (cache hit - fast!)
time curl "http://localhost:5000/api/predictions/latest?limit=100" \
  -H "Authorization: Bearer $TOKEN" > /dev/null
```

**Expected:** Second request significantly faster

---

## 6️⃣ CHECK DATABASE

```bash
cd ml-signals
python tmp_rovodev_check_db.py
```

**Verify:**
- Users exist
- demo@metalmind.com is verified and active

---

## 7️⃣ TEST PASSWORD VALIDATORS

```bash
# Weak password (should fail)
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"weak"}'

# Expected: 400 error with specific message

# Invalid email (should fail)
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid-email","password":"Strong123!@#"}'

# Expected: 400 error "Invalid email format"
```

---

## 8️⃣ TEST SECRET_KEY VALIDATION

**In development:**
```bash
unset SECRET_KEY
python run.py
```

**Expected:** Warning but server starts

**In production:**
```bash
export FLASK_ENV=production
unset SECRET_KEY
python run.py
```

**Expected:** Server exits with error message

---

## 9️⃣ CHECK CODE QUALITY

### No Unused Imports
```bash
cd ml-signals/api/app
grep -n "^import numpy" *.py
# Should return nothing (numpy removed from main.py)

grep -n "^import json" main.py | wc -l
# Should return 1 (duplicate removed)
```

### Validators Created
```bash
ls -la ml-signals/api/app/validators.py
# Should exist
```

### Connection Pool Configured
```bash
grep -A 5 "SQLALCHEMY_ENGINE_OPTIONS" ml-signals/api/app/database.py
# Should show pool_size, max_overflow, pool_timeout
```

---

## 🔟 TEST FRONTEND INTEGRATION

If you have the frontend running:

1. **Open:** http://localhost:3000
2. **Login:** demo@metalmind.com / Demo123!@#
3. **Navigate:** Check predictions page
4. **Verify:** Data loads quickly (cache working)
5. **Check Console:** No CORS errors

---

## ✅ CHECKLIST

Use this to track your testing:

### Automated Tests
- [ ] All automated tests pass (green)
- [ ] No red failures

### Manual Tests
- [ ] Health check returns enhanced data
- [ ] Login works with demo account
- [ ] Rate limiting triggers after ~10 requests
- [ ] Input validation rejects invalid limits
- [ ] Path traversal is blocked
- [ ] Second prediction request is faster (cache)
- [ ] Compression header present (or flask-compress installed)

### Code Verification
- [ ] Startup logs show lazy loading message
- [ ] No numpy import in main.py
- [ ] validators.py exists
- [ ] Connection pool configured in database.py
- [ ] All try/except blocks have db.session.rollback()

### Production Readiness
- [ ] SECRET_KEY validation works
- [ ] Auto-verification only in dev mode
- [ ] CORS configured with specific origins

---

## 🚨 TROUBLESHOOTING

### "Connection refused"
- Server not running: `python run.py`

### "Token is missing"
- Login first to get token
- Use token in Authorization header

### "Model not found"
- Models not trained yet (OK for testing)
- Endpoints should still respond with proper errors

### "Flask-Compress not found"
- Install: `pip install flask-compress`

### Tests fail with database errors
- Check database exists: `ml-signals/instance/metalmind_smc.db`
- Recreate if needed: Delete and restart server

---

## 📊 SUCCESS CRITERIA

**All fixes working if:**
1. ✅ Automated tests: 16+ passed
2. ✅ Health check returns enhanced data
3. ✅ Caching makes 2nd request faster
4. ✅ Rate limiting triggers
5. ✅ Input validation works
6. ✅ No security bypasses in production
7. ✅ Code is clean (no unused imports)

---

**Ready to test? Run the automated script first, then manually verify!**
