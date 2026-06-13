# 🔍 Frontend Audit Report — ml-signals

> **Audited By:** Rovo Dev (Senior Software Engineer)
> **Date:** February 2026
> **Project:** MetalMind SMC — AI-Powered Trading Signals (Gold & Silver)

---

## Verdict: Two Contradicting Frontends Detected

The project has **two separate frontend implementations** that conflict with each other, plus a third inline HTML dashboard. Neither of the two main frontends is fully functional.

---

## Frontend Inventory

### 1. 🔴 Frontend 1 — V4 Vanilla HTML (Referenced, Missing)

| Property | Detail |
|----------|--------|
| **Expected Location** | `ml-signals/frontend/public/index_v4.html` |
| **Actual Status** | ❌ File does not exist |
| **Served By** | Flask (`main.py` line 690) on port `5000` |
| **Tech** | Vanilla HTML + CSS + JS (assumed) |

**The Problem:**

Flask's `main.py` explicitly tries to serve this file as the default landing page:

```python
# main.py — line 684–691
@app.route('/')
@app.route('/v4')
def serve_v4_frontend():
    """Serve the V4 HTML frontend as the default landing page."""
    frontend_path = Path(__file__).parent.parent.parent / 'frontend' / 'public' / 'index_v4.html'
    return send_file(frontend_path)
```

The `frontend/public/` directory is **completely empty**. This means:

- Hitting `http://localhost:5000/` → **500 Internal Server Error** (FileNotFoundError)
- Hitting `http://localhost:5000/styles/<file>` → **404 / crash**
- Hitting `http://localhost:5000/js/<file>` → **404 / crash**

This is why the app was previously showing a **generic/broken frontend** — Flask was crashing trying to find a file that was never created.

---

### 2. ⚠️ Frontend 2 — React + TypeScript (Exists, Incomplete)

| Property | Detail |
|----------|--------|
| **Location** | `ml-signals/frontend/src/` |
| **Status** | ⚠️ Skeleton — partially built, mock data only |
| **Served By** | Vite dev server on port `3000` |
| **Tech** | React 18 + TypeScript + Vite + MUI + Zustand + React Query |
| **API Target** | `http://localhost:5000/api` (via Vite proxy) |

**What exists:**

| File/Folder | Status |
|-------------|--------|
| `App.tsx`, `router.tsx`, `main.tsx` | ✅ Complete |
| `pages/Login.tsx`, `Register.tsx`, `ForgotPassword.tsx` | ✅ Present |
| `pages/Dashboard.tsx` | ⚠️ Works but uses **mock data only** |
| `components/trading/` | ✅ Components exist (PredictionCard, CandlestickChart, etc.) |
| `components/auth/` | ❌ Folder empty — no files |
| `components/layout/` | ❌ Folder empty — no files |
| `features/auth/hooks/` | ❌ Folder empty |
| `features/backtest/` | ❌ Entire folder empty |
| `features/trading/hooks/` | ❌ Folder empty |
| `utils/` | ❌ Folder empty |
| `hooks/useAuth.ts`, `useWebSocket.ts` | ✅ Present |
| `guards/AuthGuard.tsx` | ✅ Present |

**Mock data in Dashboard.tsx:**
```tsx
// Dashboard.tsx — line 31
// Mock data for demonstration (will be replaced with real data from backend)
const mockPrediction = {
  asset: 'XAUUSD',
  signal: 'BUY',
  confidence: 85,
  price: 2050.32,
  timestamp: new Date().toISOString(),
};
```

The React frontend was **the intended final frontend** but was abandoned midway. It was replaced by the V4 HTML approach (which was also never completed).

---

### 3. ✅ Frontend 3 — ETL Dashboard (Inline HTML, Works)

| Property | Detail |
|----------|--------|
| **Location** | `ml-signals/api/app/etl_dashboard.py` |
| **Status** | ✅ Functional |
| **Served By** | Flask Blueprint on port `5000` at `/dashboard/` |
| **Tech** | Inline HTML string rendered from Python |

This is a monitoring page for the ETL pipeline, created for the exam committee demo. It is self-contained and works because it has no external file dependencies.

---

## Conflict Map

```
http://localhost:5000/           → Flask serves index_v4.html  ← FILE MISSING ❌
http://localhost:5000/api/*      → Flask REST API              ← Works ✅
http://localhost:5000/dashboard/ → ETL inline HTML dashboard   ← Works ✅
http://localhost:5000/styles/*   → Static CSS files            ← FILES MISSING ❌
http://localhost:5000/js/*       → Static JS files             ← FILES MISSING ❌

http://localhost:3000/           → React Vite dev server       ← Works (mock data) ⚠️
http://localhost:3000/dashboard  → React Dashboard             ← Mock data only ⚠️
http://localhost:3000/login      → React Login page            ← Works ✅
```

---

## Root Cause

The project went through at least **two frontend strategy changes**:

```
Phase 1: React + TypeScript (port 3000)
    ↓ Decision to switch to simpler HTML
Phase 2: V4 Vanilla HTML (port 5000, served by Flask)
    ↓ V4 HTML was never actually built
Phase 3: Stuck — neither frontend is complete
```

The comment in `main.py` line 44 confirms this history:
```python
# New UI is served from same origin (port 5000), but keep localhost:3000 for backward compatibility
```

This means at some point the plan was to **ditch the React app** and serve a simpler HTML frontend directly from Flask — but that HTML was never delivered.

---

## Impact Assessment

| Impact | Severity |
|--------|----------|
| `http://localhost:5000/` crashes with 500 | 🔴 Critical |
| No working UI accessible to end users out of the box | 🔴 Critical |
| React frontend exists but shows mock data | 🟡 Medium |
| Duplicate routing logic (Flask static + Vite proxy) | 🟡 Medium |
| Empty feature folders suggest incomplete implementation | 🟡 Medium |
| ETL dashboard works but is isolated from main app | 🟢 Low |

---

## Recommended Fix

### Option A — Recommended: Use React as the Single Frontend ✅

Remove the broken V4 references from Flask. Build the React app and serve it from Flask as static files. This is the cleanest long-term solution.

**Steps:**
1. Remove `serve_v4_frontend()`, `serve_styles()`, `serve_js()`, `serve_static()` routes from `main.py`
2. Add a single catch-all route that serves the React build output (`frontend/dist/index.html`)
3. Run `npm run build` in `frontend/` → outputs to `frontend/dist/`
4. Flask serves `frontend/dist/` as static files
5. React routes handle all UI navigation; Flask handles `/api/*` only

**Result:** Single port (`5000`), no Vite proxy needed in production, clean separation of concerns.

---

### Option B — Quick Fix: Create a Minimal index_v4.html

Create a simple working `frontend/public/index_v4.html` that connects to the Flask API. Fastest path to something running.

**Pros:** Quick, no build step needed
**Cons:** Technical debt, two codebases to maintain

---

### Option C — Dockerize As-Is, Fix Inside Docker

Containerize the project now and fix the frontend contradiction as part of the Docker setup.

**Pros:** Keeps momentum on deployment
**Cons:** Docker build will fail or produce a broken app at `/`

---

## Conclusion

The project is in a **frontend limbo** — the React app was the right choice architecturally but was abandoned before completion. The V4 HTML replacement was planned but never built. The result is a working backend API with no accessible UI.

**Recommended path forward:**

```
1. Fix Flask main.py → remove broken V4 routes
2. Complete the React frontend → replace mock data with real API calls
3. Build React → npm run build
4. Serve React dist from Flask (or Nginx in Docker)
5. Dockerize the complete working stack
```

This gives you one clean frontend, one port, and a Dockerizable stack.
