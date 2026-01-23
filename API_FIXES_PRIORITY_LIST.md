# 🔧 API FIXES - PRIORITY ORDER

## 🔴 CRITICAL FIXES (Do First)

### **Priority 1: Security - CORS Configuration**
- **File:** `api/app/main.py:33`
- **Issue:** Allows all origins
- **Time:** 2 minutes
- **Impact:** HIGH - Prevents CSRF attacks

### **Priority 2: Security - Input Validation**
- **File:** `api/app/main.py:135`
- **Issue:** No bounds on limit parameter
- **Time:** 5 minutes
- **Impact:** HIGH - Prevents DoS

### **Priority 3: Security - Rate Limiting**
- **File:** All protected routes
- **Issue:** No rate limits
- **Time:** 15 minutes
- **Impact:** HIGH - Prevents API abuse

### **Priority 4: Performance - Predictions Caching**
- **File:** `api/app/main.py:148-153`
- **Issue:** Loads entire dataset per request
- **Time:** 30 minutes
- **Impact:** EXTREME - 10x performance improvement

### **Priority 5: Logic - Transaction Rollbacks**
- **File:** `watchlist.py`, `profile.py`
- **Issue:** Missing error handling
- **Time:** 20 minutes
- **Impact:** HIGH - Prevents data corruption

### **Priority 6: Maintainability - Centralize Token Decorator**
- **Files:** `auth.py`, `watchlist.py`, `profile.py`
- **Issue:** Duplicate code (120 lines)
- **Time:** 15 minutes
- **Impact:** HIGH - Single source of truth

### **Priority 7: Performance - N+1 Query Fix**
- **File:** `watchlist.py:226-239`
- **Issue:** Loop with queries
- **Time:** 10 minutes
- **Impact:** MEDIUM - Better for large watchlists

### **Priority 8: Logic - Backtest Race Condition**
- **File:** `main.py:236-270`
- **Issue:** Untracked threads
- **Time:** 25 minutes
- **Impact:** MEDIUM - Prevents crashes

### **Priority 9: Security - Path Traversal**
- **File:** `main.py:208-217`
- **Issue:** Unsafe file paths
- **Time:** 5 minutes
- **Impact:** HIGH - Prevents file access

### **Priority 10: Maintainability - API Versioning**
- **File:** All routes
- **Issue:** No /v1/ prefix
- **Time:** 10 minutes
- **Impact:** MEDIUM - Future-proofing

### **Priority 11: Maintainability - Global State**
- **File:** `main.py:56-57`
- **Issue:** Global models dict
- **Time:** 20 minutes
- **Impact:** MEDIUM - Better testing

### **Priority 12: Performance - Model Loading**
- **File:** `main.py:102-107`
- **Issue:** Blocking startup
- **Time:** 20 minutes
- **Impact:** MEDIUM - Faster startup

---

## ⏱️ TOTAL ESTIMATED TIME: **3 hours**

---

## 🎯 EXECUTION PLAN

**Session 1 (30 min):** Priorities 1-3 (Security)
**Session 2 (45 min):** Priority 4 (Caching)
**Session 3 (45 min):** Priorities 5-7
**Session 4 (60 min):** Priorities 8-12

---

## ✅ READY TO START?

Say **"start fixing"** and I'll begin with Priority 1!
