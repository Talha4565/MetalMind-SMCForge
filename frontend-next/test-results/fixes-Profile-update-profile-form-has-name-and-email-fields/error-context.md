# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: fixes.spec.ts >> Profile update >> profile form has name and email fields
- Location: tests\fixes.spec.ts:25:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/dashboard/profile
Call log:
  - navigating to "http://localhost:3000/dashboard/profile", waiting until "load"

```

# Test source

```ts
  1  | /**
  2  |  * Tests for GitHub link and profile update fixes.
  3  |  * Run: npx playwright test tests/fixes.spec.ts
  4  |  */
  5  | 
  6  | import { test, expect } from '@playwright/test';
  7  | 
  8  | const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';
  9  | 
  10 | test.describe('GitHub link', () => {
  11 |   test('landing page GitHub link points to correct repo', async ({ page }) => {
  12 |     await page.goto(FRONTEND_URL);
  13 |     const githubLink = page.locator('a[href*="github.com"]').first();
  14 |     await expect(githubLink).toHaveAttribute('href', 'https://github.com/Talha4565/MetalMind-SMCForge');
  15 |   });
  16 | 
  17 |   test('footer GitHub link points to correct repo', async ({ page }) => {
  18 |     await page.goto(`${FRONTEND_URL}/dashboard`);
  19 |     const githubLink = page.locator('footer a[href*="github.com"]');
  20 |     await expect(githubLink).toHaveAttribute('href', 'https://github.com/Talha4565/MetalMind-SMCForge');
  21 |   });
  22 | });
  23 | 
  24 | test.describe('Profile update', () => {
  25 |   test('profile form has name and email fields', async ({ page }) => {
> 26 |     await page.goto(`${FRONTEND_URL}/dashboard/profile`);
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/dashboard/profile
  27 |     const nameInput = page.locator('input[name="name"]');
  28 |     const emailInput = page.locator('input[name="email"]');
  29 |     await expect(nameInput).toBeVisible();
  30 |     await expect(emailInput).toBeVisible();
  31 |   });
  32 | });
  33 | 
```