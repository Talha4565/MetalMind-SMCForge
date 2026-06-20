/**
 * Tests for GitHub link and profile update fixes.
 * Run: npx playwright test tests/fixes.spec.ts
 */

import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';

test.describe('GitHub link', () => {
  test('landing page GitHub link points to correct repo', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    const githubLink = page.locator('a[href*="github.com"]').first();
    await expect(githubLink).toHaveAttribute('href', 'https://github.com/Talha4565/MetalMind-SMCForge');
  });

  test('footer GitHub link points to correct repo', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);
    const githubLink = page.locator('footer a[href*="github.com"]');
    await expect(githubLink).toHaveAttribute('href', 'https://github.com/Talha4565/MetalMind-SMCForge');
  });
});

test.describe('Profile update', () => {
  test('profile form has name and email fields', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard/profile`);
    const nameInput = page.locator('input[name="name"]');
    const emailInput = page.locator('input[name="email"]');
    await expect(nameInput).toBeVisible();
    await expect(emailInput).toBeVisible();
  });
});
