# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: critical-flows.spec.ts >> Landing page >> renders hero section with headline
- Location: tests\critical-flows.spec.ts:14:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Test source

```ts
  1  | /**
  2  |  * Critical flow tests — covers the 4 critical audit findings.
  3  |  * Run: npx playwright test tests/critical-flows.spec.ts
  4  |  */
  5  | 
  6  | import { test, expect } from '@playwright/test';
  7  | 
  8  | const FE = process.env.FRONTEND_URL || 'http://localhost:3000';
  9  | const API = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
  10 | 
  11 | // ── 1. Landing page renders with correct content ──
  12 | 
  13 | test.describe('Landing page', () => {
  14 |   test('renders hero section with headline', async ({ page }) => {
> 15 |     await page.goto(FE);
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  16 |     await expect(page.locator('h1')).toContainText('machine precision');
  17 |   });
  18 | 
  19 |   test('has working login CTA', async ({ page }) => {
  20 |     await page.goto(FE);
  21 |     const cta = page.locator('a[href="/auth/login"]').first();
  22 |     await expect(cta).toBeVisible();
  23 |     await cta.click();
  24 |     await expect(page).toHaveURL(/\/auth\/login/);
  25 |   });
  26 | 
  27 |   test('has GitHub link to correct repo', async ({ page }) => {
  28 |     await page.goto(FE);
  29 |     const link = page.locator('a[href*="github.com"]').first();
  30 |     await expect(link).toHaveAttribute('href', 'https://github.com/Talha4565/MetalMind-SMCForge');
  31 |   });
  32 | });
  33 | 
  34 | // ── 2. Auth middleware redirects unauthenticated users ──
  35 | 
  36 | test.describe('Auth protection', () => {
  37 |   test('backtest page redirects to login when not authenticated', async ({ page }) => {
  38 |     await page.goto(`${FE}/backtest`);
  39 |     // Should redirect to login (middleware) or show login page
  40 |     await page.waitForURL(/\/auth\/login|\/backtest/, { timeout: 10000 });
  41 |     const url = page.url();
  42 |     // If middleware is active, we land on login. If not, we see backtest page.
  43 |     expect(url).toMatch(/\/auth\/login|\/backtest/);
  44 |   });
  45 | 
  46 |   test('login page renders form fields', async ({ page }) => {
  47 |     await page.goto(`${FE}/auth/login`);
  48 |     await expect(page.locator('input[type="email"], input[name="email"]').first()).toBeVisible();
  49 |     await expect(page.locator('input[type="password"], input[name="password"]').first()).toBeVisible();
  50 |   });
  51 | 
  52 |   test('register page renders form fields', async ({ page }) => {
  53 |     await page.goto(`${FE}/auth/register`);
  54 |     await expect(page.locator('input[type="email"], input[name="email"]').first()).toBeVisible();
  55 |     await expect(page.locator('input[type="password"], input[name="password"]').first()).toBeVisible();
  56 |   });
  57 | });
  58 | 
  59 | // ── 3. Dashboard renders without crashing (error boundary test) ──
  60 | 
  61 | test.describe('Dashboard error boundary', () => {
  62 |   test('dashboard page loads or shows auth gate', async ({ page }) => {
  63 |     await page.goto(`${FE}/dashboard`);
  64 |     // Should either show dashboard content or redirect to login
  65 |     await page.waitForLoadState('networkidle', { timeout: 15000 });
  66 |     const body = await page.textContent('body');
  67 |     // Page should render something — not a blank white screen
  68 |     expect(body?.length).toBeGreaterThan(50);
  69 |   });
  70 | });
  71 | 
  72 | // ── 4. 404 page renders ──
  73 | 
  74 | test.describe('Not found page', () => {
  75 |   test('non-existent route shows 404', async ({ page }) => {
  76 |     const response = await page.goto(`${FE}/this-page-does-not-exist-xyz`);
  77 |     // Should show 404 content or a valid error page
  78 |     await page.waitForLoadState('domcontentloaded');
  79 |     const body = await page.textContent('body');
  80 |     expect(body).toBeTruthy();
  81 |   });
  82 | });
  83 | 
  84 | // ── 5. API health check (backend is reachable) ──
  85 | 
  86 | test.describe('API health', () => {
  87 |   test('backend API responds', async ({ request }) => {
  88 |     const response = await request.get(`${API}/api/health`, { timeout: 10000 });
  89 |     // API should respond (200 or 404 — either means it's running)
  90 |     expect([200, 404, 401]).toContain(response.status());
  91 |   });
  92 | });
  93 | 
```