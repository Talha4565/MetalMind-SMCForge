# MetalMind SMCForge — Frontend-Next Comprehensive Audit Report

**Auditor:** Senior Frontend Auditor  
**Date:** 2026-06-29  
**Scope:** `frontend-next/` — All pages, components, hooks, tests, UI/UX, accessibility, animations, backtesting  
**Stack:** Next.js 16.2.6, React 19.2.4, TypeScript 5, Tailwind CSS 4, shadcn/ui, TanStack Query 5, NextAuth 4, Socket.IO, Playwright

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture & Tech Stack Audit](#2-architecture--tech-stack-audit)
3. [Page-by-Page Functional Review](#3-page-by-page-functional-review)
4. [Component Quality & Code Review](#4-component-quality--code-review)
5. [UI/UX Design & Animations](#5-uiux-design--animations)
6. [Accessibility (WCAG)](#6-accessibility-wcag)
7. [Backtesting Functionality Deep-Dive](#7-backtesting-functionality-deep-dive)
8. [Testing Coverage & Quality](#8-testing-coverage--quality)
9. [Security Audit](#9-security-audit)
10. [Findings Summary & Severity Matrix](#10-findings-summary--severity-matrix)

---

## 1. Executive Summary

The frontend-next application is a **Next.js 16 + React 19** Bloomberg-style trading terminal for ML-driven gold/silver signals. It demonstrates strong architectural foundations — clean separation of concerns, typed API layer, and real-time WebSocket integration. However, there are **critical gaps** in testing, accessibility, and several security concerns.

### Key Metrics

| Area | Score | Rating |
|------|-------|--------|
| Architecture | 8/10 | Good |
| Code Quality | 7/10 | Good |
| UI/UX Design | 8/10 | Very Good |
| Animations | 5/10 | Fair |
| Accessibility | 3/10 | Poor |
| Backtesting UI | 6/10 | Fair |
| Testing Coverage | 2/10 | Critical |
| Security | 5/10 | Fair |

**Overall: 5.5/10** — Solid foundation with significant gaps in testing and accessibility.

---

## 2. Architecture & Tech Stack Audit

### 2.1 Strengths

- **Modern stack:** Next.js 16, React 19, Tailwind CSS 4, TypeScript 5 — all latest major versions
- **Typed API layer:** `api-client.ts` is a well-structured singleton with interceptors, token refresh, and error normalization
- **Clean separation:** Pages → Components → Hooks → API Client → Types — proper layering
- **TanStack Query v5** for server state management with stale-time configuration
- **NextAuth v4** with JWT strategy, 2FA support, and custom credential provider
- **Socket.IO integration** with reconnection logic for real-time price/streaming
- **Dynamic imports** for heavy components (SHAPExplainer) to reduce initial bundle

### 2.2 Concerns

| # | Issue | Severity | Location |
|---|-------|----------|----------|
| A-1 | **No ESLint flat config** — `eslint.config.mjs` missing, relying on deprecated `.eslintrc` | Low | `package.json` |
| A-2 | **`suppressHydrationWarning`** on `<html>` — suppresses SSR mismatches, masks hydration bugs | Medium | `layout.tsx:30` |
| A-3 | **No error boundary** — no global React error boundary; unhandled render errors crash entire app | High | Missing |
| A-4 | **No loading.tsx / error.tsx** per-route — Next.js App Router error/loading conventions unused | Medium | `src/app/` |
| A-5 | **No `robots.ts` or `sitemap.ts`** — SEO basics missing for a public-facing app | Low | Missing |
| A-6 | **Agent orchestrator** (`lib/agents/`) is ~300 lines of dead code — no page or hook imports it | Medium | `lib/agents/` |
| A-7 | **ThemeToggle** manages theme via DOM class manipulation instead of `next-themes` provider | Medium | `ThemeToggle.tsx` |

---

## 3. Page-by-Page Functional Review

### 3.1 Landing Page (`/`) — `page.tsx`

**Status:** Functional but minimal  
**Issues:**
- Static landing page — no animations, no scroll effects, no mobile menu
- Hardcoded values: "89 Features", "XAU", "XAG" — not dynamic
- No `<head>` meta tags for social sharing (OG tags)
- CTA "Open dashboard" always links to `/auth/login` — no conditional redirect for logged-in users

### 3.2 Dashboard (`/dashboard`) — `page.tsx`

**Status:** Core feature, well-implemented  
**Issues:**
- **Good:** WebSocket live price streaming, asset switching, SHAP integration, terminal-style 3-column layout
- **Good:** Dynamic import for SHAPExplainer (code splitting)
- **Issue D-1:** `apiClient.getLivePrice()` call in useEffect has empty `.catch(() => {})` — silently swallows errors
- **Issue D-2:** No error state UI when predictions fail — just shows "..." forever
- **Issue D-3:** `TerminalPanelHeader` is defined inside page component — should be extracted to avoid re-creation on every render

### 3.3 Backtest (`/backtest`) — `page.tsx`

**Status:** Functional with significant gaps (see Section 7)  
**Issues:**
- Date inputs default to `2026-01-01` / `2026-05-01` — hardcoded dates
- "Capital ($)" input has `defaultValue={10000}` but uses native `<Input>` — no two-way binding
- Export button is non-functional (no onClick handler)
- History table hardcodes "XAUUSD" for all rows regardless of asset
- Progress bar uses `useCallback` + `setInterval` polling — should use SSE or WebSocket for real-time progress

### 3.4 Auth — Login (`/auth/login`)

**Status:** Well-implemented  
**Issues:**
- **Good:** 2FA flow, Zustand-free session management, toast notifications
- **Issue L-1:** Password regex requires special chars but login form doesn't hint at this — confusing UX
- **Issue L-2:** `setIsLoading(false)` missing in catch block at line 52 — loading state gets stuck on network errors

### 3.5 Auth — Register (`/auth/register`)

**Status:** Functional  
**Issues:**
- **Good:** Email verification flow, dev auto-verify check
- **Issue R-1:** Direct `fetch()` call instead of using `apiClient` — inconsistent with rest of codebase
- **Issue R-2:** No password strength indicator shown during registration

### 3.6 Auth — Verify Email (`/auth/verify-email`)

**Status:** Functional  
**Issues:**
- Uses `window.location.search` directly — SSR will fail (though `'use client'` protects this)
- Hardcoded 700ms `setTimeout` for redirect — no cancellation on unmount

### 3.7 Auth — Verify Success (`/auth/verify-success`)

**Status:** Simple, functional  
**Issue:** Uses `searchParams` as prop — Next.js 13+ App Router should use `useSearchParams()` hook

### 3.8 Profile (`/dashboard/profile`)

**Status:** Functional  
**Issues:**
- **Issue P-1:** `defaultValues` for name hardcoded to `'Talha'` — line 51. This is a personal default baked into production code
- **Issue P-2:** "Member Since" always shows today's date (`new Date()`) — not actual member creation date
- **Issue P-3:** Plan Type hardcoded to "Professional" — no backend integration
- **Issue P-4:** Show/Hide passwords button uses Eye/EyeOff but doesn't link to the actual password input via `id`

### 3.9 Pipeline (`/dashboard/pipeline`)

**Status:** Functional  
**Issues:**
- **Good:** Health status, data freshness, model info, auto-refresh every 30s
- **Issue PP-1:** 30-second `setInterval` without cleanup reference — potential memory leak pattern
- **Issue PP-2:** "Retrain Model" triggers but has no confirmation dialog — destructive action

### 3.10 Risk (`/dashboard/risk`)

**Status:** Excellent  
**Issues:**
- **Good:** Live price integration, risk profile selection, position sizing calculation, real-time updates
- **Issue RK-1:** Trading params are hardcoded (`tp_pct: 0.0045`) — should come from backend config
- **Issue RK-2:** Margin calculation uses hardcoded 5% — no user-configurable margin rate

### 3.11 Watchlist (`/dashboard/watchlist`)

**Status:** Functional but complex  
**Issues:**
- **Issue WL-1:** Hover preview uses hardcoded bar chart heights `[40, 60, 30, 70, 55, 85, 50]` — not real data
- **Issue WL-2:** `useEffect` at line 89 depends on `fetchSymbols`, `fetchWatchlist`, `refreshPrices` — causes re-fetch loop
- **Issue WL-3:** 20-second polling interval for watchlist refresh — should use WebSocket

---

## 4. Component Quality & Code Review

### 4.1 `api-client.ts` (317 lines)

**Rating: 8/10**

- Well-structured singleton with interceptors
- Token refresh queue pattern is correct
- **Issues:**
  - `any` type used at line 182: `(response.data as any).refreshToken`
  - `any` type at line 249: `getPipelineStatus(): Promise<any>`
  - No retry logic for network failures
  - Token stored in localStorage (XSS risk — see Security section)

### 4.2 `api-types.ts` (150 lines)

**Rating: 7/10**

- Clean type definitions for all API entities
- **Issues:**
  - `SignalAction` is `string | number` union — confusing, should be a discriminated union
  - `BacktestResponse.trades` missing from some API responses
  - No `zod` schemas for runtime validation (only used in forms)

### 4.3 `useWebSocket.ts` (66 lines)

**Rating: 6/10**

- **Issues:**
  - `error` state is declared but never set (line 11) — always `null`
  - No reconnection status feedback to user
  - Creates new socket on every `event` change — should cache by URL+event
  - No heartbeat/ping to detect stale connections

### 4.4 `usePredictions.ts` (34 lines)

**Rating: 5/10**

- **Critical Issue:** Calls `apiClient.setToken()` inside render body (line 22-24) — side effects during render
- `retry: 0` means any API failure shows nothing — should retry once

### 4.5 `Providers.tsx` (48 lines)

**Rating: 7/10**

- Good: Session sync with API client, React Query setup
- **Issue:** `SessionSync` calls `apiClient.setToken()` in useEffect — same token sync happens in `usePredictions`

### 4.6 `DashboardLayout.tsx` (40 lines)

**Rating: 9/10**

- Clean, minimal, well-typed
- No issues found

### 4.7 `Sidebar.tsx` (150 lines)

**Rating: 7/10**

- Good: Mobile drawer, active state, auth-gating per route
- **Issue:** Auth-gating logic (line 25-31) redirects to login for protected routes — but doesn't check session, only `isAuthenticated`

### 4.8 `Header.tsx` (177 lines)

**Rating: 8/10**

- Good: Live clock, market status, user dropdown
- **Issue:** Market hours calculation (line 50-60) uses UTC but doesn't account for DST or exchange holidays

### 4.9 `TradingViewChart.tsx` (107 lines)

**Rating: 7/10**

- Embeds TradingView widget via iframe
- **Issues:**
  - iframe `scrolling="no"` — prevents scroll on mobile
  - No fallback if TradingView CDN is blocked
  - `key={`${asset}-${interval}`}` causes full iframe reload on every interval change

### 4.10 `SHAPExplainer.tsx` (171 lines)

**Rating: 7/10**

- Good: Diverging bar chart for SHAP contributions
- **Issue:** `SHAP_LABELS` object is duplicated across 3 files (SHAPExplainer, SignalCard, TerminalSignalPanel)

### 4.11 `SignalCard.tsx` (196 lines)

**Rating: 6/10**

- Creates its own WebSocket connection — duplicating the one in `useWebSocket` used by the dashboard
- `SHAP_LABELS` duplicated again (3rd copy)

### 4.12 `TerminalSignalPanel.tsx` (182 lines)

**Rating: 7/10**

- Good terminal-style design
- **Issue:** Duplicates `SHAP_LABELS` (4th copy in the codebase — each component has its own version)

### 4.13 `agent-orchestrator.ts` (304 lines)

**Rating: 3/10**

- **Dead code** — not imported by any page or component
- References `http://localhost:3001` (Ruflo MCP server) that doesn't exist in the project
- Should be removed or moved to a separate package

---

## 5. UI/UX Design & Animations

### 5.1 Design System

**Rating: 8/10**

- Bloomberg Terminal aesthetic is well-executed
- Consistent use of `terminal-*` CSS variables
- Sharp corners (`radius: 0.25rem`) appropriate for terminal UI
- Custom scrollbars are well-implemented

### 5.2 Typography

**Rating: 7/10**

- Geist + Geist Mono fonts loaded via `next/font` — optimal
- Heavy use of `text-[8px]` to `text-[10px]` — may fail WCAG readability on small screens
- Monospace-first approach fits trading terminal aesthetic

### 5.3 Color System

**Rating: 8/10**

- Semantic color tokens: `terminal-buy`, `terminal-sell`, `terminal-hold`
- Dark theme only — no light theme defined in CSS (line 111-174 of globals.css only defines `:root, .dark`)
- ThemeToggle component exists but no light theme CSS variables

### 5.4 Animations

**Rating: 4/10**

| Animation | Status | Notes |
|-----------|--------|-------|
| Loading spinners | Present | `animate-spin` on Loader2 icons |
| Pulse indicators | Present | `animate-pulse` on status dots |
| Hover transitions | Present | Button/card hover effects |
| Page transitions | **Missing** | No route transition animations |
| Skeleton loading | **Missing** | Only one loading state (dashboard) uses skeleton-like pattern |
| Scroll animations | **Missing** | No scroll-triggered animations on landing page |
| Number counters | **Missing** | Stats don't animate on mount |
| Micro-interactions | **Minimal** | Only button hover translate-x on CTAs |
| Toast animations | Present | Via Sonner library |
| Chart animations | **N/A** | TradingView iframe handles its own |

**Key gaps:**
- No `framer-motion` or equivalent for page transitions
- No `IntersectionObserver`-based reveal animations on landing
- No skeleton loading states for data-heavy pages (risk, pipeline, watchlist)

### 5.5 Responsive Design

**Rating: 6/10**

- **Good:** Mobile sidebar drawer, responsive grid layouts
- **Issues:**
  - Dashboard 3-column layout (`grid-cols-1 lg:grid-cols-[300px_1fr_260px]`) may be cramped on 1024px screens
  - TradingView chart `minHeight: '480px'` is hardcoded inline — doesn't adapt
  - Landing page stats strip uses `grid-cols-2 md:grid-cols-5` — 5 columns may overflow on tablets

---

## 6. Accessibility (WCAG)

### Overall Rating: 3/10 — CRITICAL

### 6.1 Critical Issues

| # | Issue | Severity | WCAG |
|---|-------|----------|------|
| AC-1 | **No skip navigation link** — keyboard users must tab through entire sidebar | Critical | 2.4.1 |
| AC-2 | **Buttons without accessible names** — refresh button (dashboard:119), bell notification (Header:114) use only icons | High | 4.1.2 |
| AC-3 | **No focus management** — route changes don't move focus, modal/drawer open doesn't trap focus | High | 2.4.3 |
| AC-4 | **Missing `aria-label`** on most interactive elements | High | 1.1.1 |
| AC-5 | **Color-only signal indicators** — BUY/SELL/HOLD rely solely on color (green/red/amber) | High | 1.4.1 |
| AC-6 | **No `role` attributes** on custom UI patterns — sidebar nav, dropdown menus | Medium | 4.1.2 |
| AC-7 | **Table accessibility** — watchlist table uses `<table>` without `<caption>`, `<th scope>` | Medium | 1.3.1 |
| AC-8 | **Text too small** — `text-[8px]`, `text-[9px]`, `text-[10px]` throughout terminal UI | Medium | 1.4.4 |
| AC-9 | **No `aria-live` regions** — live price/signal updates not announced to screen readers | High | 4.1.3 |
| AC-10 | **No keyboard navigation** in backtest form — date inputs, select dropdowns | Medium | 2.1.1 |

### 6.2 Specific Component Issues

**Sidebar.tsx:**
- Mobile toggle button has no `aria-label`
- Mobile drawer overlay has no `role="dialog"` or `aria-modal`
- No `aria-expanded` on hamburger button

**Dashboard page:**
- Asset tabs (XAU/USD, XAG/USD) use `<button>` without `role="tab"` / `aria-selected`
- Signal badge has no accessible text beyond visual color

**Backtest page:**
- Progress bar has no `role="progressbar"`, no `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Export button is disabled (no handler) but not marked as `aria-disabled`

**Header:**
- Bell notification icon has no `aria-label` — screen reader says "button"
- Market status chip has no `aria-live` attribute

---

## 7. Backtesting Functionality Deep-Dive

### 7.1 Frontend Backtest Page Analysis

**Architecture:** Form → API mutation → Poll status → Display results

#### Issues Found

| # | Issue | Severity | Location |
|---|-------|----------|----------|
| BT-1 | **Capital input uncontrolled** — `defaultValue={10000}` but no `value`/`onChange` binding; `initial_capital` is always 10000 | High | `page.tsx:168-171` |
| BT-2 | **Export button non-functional** — `<Button>Export</Button>` has no `onClick` handler | Medium | `page.tsx:234-237` |
| BT-3 | **History table hardcoded asset** — all rows show "XAUUSD" regardless of actual `result.asset` | Medium | `page.tsx:257` |
| BT-4 | **No result detail view** — History row has `<History>` icon button with no handler | Medium | `page.tsx:263-265` |
| BT-5 | **No delete functionality** — Trash icon button has no `onClick` | Medium | `page.tsx:266-268` |
| BT-6 | **Progress polling every 1.5s** — should use WebSocket or SSE for efficiency | Low | `page.tsx:79-84` |
| BT-7 | **No backtest result visualization** — no equity curve chart, no trade list, no drawdown chart | High | Missing |
| BT-8 | **No date validation** — start date can be after end date | Medium | `page.tsx` |
| BT-9 | **Strategy hardcoded** — `strategy: 'SMC_FORGE_V1'` not configurable | Low | `page.tsx:99` |
| BT-10 | **No comparison mode** — can't compare multiple backtest runs | Low | Missing |

### 7.2 Backend Backtest Engine (from `tests/unit/test_backtesting.py`)

The backend `BacktestEngine` supports:
- Trade simulation with TP/SL
- Equity curve tracking
- Session performance (Asian/London/NY)
- Win rate, profit factor, max drawdown, Sharpe ratio

**Frontend doesn't expose most of these metrics.** The frontend only shows:
- Win rate
- Profit factor
- Net profit

**Missing from frontend:**
- Max drawdown
- Sharpe ratio
- Equity curve chart
- Individual trade list
- Session breakdown
- Trade duration analysis

### 7.3 Backend Test Coverage for Backtesting

`test_backtesting.py` covers:
- Trade creation
- Engine initialization (gold/silver/custom)
- Trade simulation (no signal, TP hit, end of data)
- Backtest execution (empty signals, with signals)
- Equity curve validation
- Metrics structure validation
- Session performance
- Stress test (many signals)

**Assessment:** Backend tests are solid; frontend has NO tests for backtesting.

---

## 8. Testing Coverage & Quality

### Overall Rating: 2/10 — CRITICAL

### 8.1 Playwright E2E Tests

| Test File | Tests | Coverage | Issues |
|-----------|-------|----------|--------|
| `tests/fixes.spec.ts` | 3 | GitHub link + profile form fields | Minimal — smoke tests only |
| `tests/2fa.spec.ts` | 1 | Full 2FA register→setup→enable→login flow | Good coverage for auth, API-only (no UI) |

**Total: 4 test cases across 2 files for an application with 11 pages, 30+ components**

### 8.2 Missing Test Coverage

| Area | Expected Tests | Actual | Gap |
|------|---------------|--------|-----|
| Dashboard page | 5-8 | 0 | CRITICAL |
| Backtest page | 8-12 | 0 | CRITICAL |
| Risk page | 5-8 | 0 | CRITICAL |
| Watchlist CRUD | 6-10 | 0 | CRITICAL |
| Pipeline page | 3-5 | 0 | HIGH |
| Profile page | 4-6 | 0 | HIGH |
| Auth flows | 6-8 | 1 (API only) | HIGH |
| Landing page | 3-4 | 2 | MODERATE |
| Components (unit) | 15-20 | 0 | CRITICAL |
| Hooks (unit) | 8-10 | 0 | CRITICAL |

### 8.3 Backend Test Coverage (referenced)

The `tests/` directory in `ml-signals/` has comprehensive Python tests:
- Unit tests for backtesting, features, alerts, SHAP, config, labels, etc.
- Integration tests for ETL and feature-model pipelines
- Smoke tests for E2E app

**Gap:** No frontend unit tests exist. No React Testing Library setup. No Vitest/Jest config.

### 8.4 Testing Recommendations

1. **Add Vitest + React Testing Library** for component/hook unit tests
2. **Add Playwright tests** for all critical user flows
3. **Target minimum 60% line coverage** for components
4. **Add snapshot tests** for key layout components
5. **Add integration tests** for API client + hooks

---

## 9. Security Audit

### 9.1 Critical Issues

| # | Issue | Severity | Location |
|---|-------|----------|----------|
| SEC-1 | **JWT tokens in localStorage** — vulnerable to XSS attacks. Tokens should use httpOnly cookies | Critical | `api-client.ts:101-103` |
| SEC-2 | **Hardcoded dev secret** — `'dev-preview-secret-do-not-use-in-prod'` used as NEXTAUTH_SECRET fallback in production | High | `auth-options.ts:116` |
| SEC-3 | **Auth bypass in dev** — middleware returns `NextResponse.next()` when no NEXTAUTH_SECRET, allowing unauthenticated access | High | `middleware.ts:17-18` |
| SEC-4 | **No CSRF protection** — API calls use Bearer token but no CSRF token for state-changing operations | Medium | `api-client.ts` |
| SEC-5 | **Refresh token in localStorage** — same XSS vulnerability as access token | High | `api-client.ts:122-125` |

### 9.2 Medium Issues

| # | Issue | Severity | Location |
|---|-------|----------|----------|
| SEC-6 | **No rate limiting on frontend** — no client-side throttle for API calls or login attempts | Medium | Multiple |
| SEC-7 | **API error messages leak internal details** — `error.response.data.error` shown directly to user | Medium | `api-client.ts:78` |
| SEC-8 | **No Content Security Policy** — no CSP headers configured | Medium | Missing |
| SEC-9 | **`any` type cast on middleware** — `(authMiddleware as any)(req)` bypasses type safety | Medium | `middleware.ts:21` |
| SEC-10 | **Email in URL params** — `verify-email?email=...` exposes email in browser history/URL | Low | `verify-email/page.tsx` |

### 9.3 Positive Security Practices

- Zod validation on auth forms
- Password complexity requirements (uppercase, lowercase, number, special char)
- Token refresh mechanism with queue deduplication
- `autoComplete` attributes on password fields for browser credential managers

---

## 10. Findings Summary & Severity Matrix

### By Severity

| Severity | Count | Key Items |
|----------|-------|-----------|
| **Critical** | 4 | No tests, no error boundaries, localStorage JWT, dev auth bypass |
| **High** | 8 | No accessibility, hardcoded secret fallback, no skip-nav, dead code, missing backtest features |
| **Medium** | 15 | Duplicate SHAP_LABELS, uncontrolled inputs, no light theme, no CSRF, no skeleton loading |
| **Low** | 8 | Missing SEO, unused landing components, minor type issues |

### Top 10 Recommendations (Priority Order)

1. **Add React Error Boundaries** — wrap routes in `error.tsx` files
2. **Implement accessibility** — skip-nav, aria-labels, focus management, screen reader support
3. **Add Playwright + Vitest tests** — cover all critical user flows
4. **Move tokens to httpOnly cookies** — eliminate localStorage JWT storage
5. **Remove hardcoded secret fallback** — require NEXTAUTH_SECRET in production
6. **Complete backtest UI** — equity curve chart, trade list, result detail view
7. **Extract shared constants** — deduplicate SHAP_LABELS across 4 files
8. **Add skeleton loading states** — improve perceived performance
9. **Add light theme CSS variables** — or remove ThemeToggle
10. **Remove dead code** — delete `lib/agents/` if not planned for use

### Files Touched in Audit

All files in `frontend-next/src/` were reviewed:
- 11 pages (`src/app/`)
- 25+ components (`src/components/`)
- 4 hooks (`src/lib/hooks/`)
- 3 agent files (`src/lib/agents/`) — dead code
- 2 API files (`src/lib/api-client.ts`, `src/lib/api-types.ts`)
- 1 utility (`src/lib/utils.ts`)
- 2 test files (`tests/`)
- Config files (`tsconfig.json`, `playwright.config.ts`, `package.json`)
- Styles (`globals.css`)
- Auth config (`auth-options.ts`, `route.ts`, `middleware.ts`)
- Type augmentation (`next-auth.d.ts`)

---

*End of Audit Report*
