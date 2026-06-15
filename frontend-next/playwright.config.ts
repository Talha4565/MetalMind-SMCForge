import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  use: {
    actionTimeout: 10_000,
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
    trace: 'on-first-retry'
  }
});
