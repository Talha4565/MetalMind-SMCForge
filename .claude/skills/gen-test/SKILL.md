---
name: gen-test
description: Generate tests for API endpoints (pytest), dashboard components (Jest), and E2E flows (Playwright)
disable-model-invocation: true
---

# Generate Tests

Generate tests for the MetalMind SMCForge codebase. Pick the right framework based on what's being tested.

## Framework selection

| What to test | Framework | Config |
|-------------|-----------|--------|
| Flask API endpoint | pytest | `tests/` directory |
| Next.js page/component | Jest + React Testing Library | `frontend-next/` |
| User flow / E2E | Playwright | `frontend-next/` (`@playwright/test`) |

## pytest template (API endpoint)

```python
import pytest
from unittest.mock import patch, MagicMock

def test_<endpoint>_success(client, auth_headers):
    """Should return 200 with valid data."""
    response = client.get('/api/<route>', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert '<key>' in data

def test_<endpoint>_unauthorized(client):
    """Should return 401 without auth."""
    response = client.get('/api/<route>')
    assert response.status_code == 401

def test_<endpoint>_invalid_input(client, auth_headers):
    """Should return 400 for bad input."""
    response = client.post('/api/<route>', json={}, headers=auth_headers)
    assert response.status_code == 400
```

## Jest template (component)

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('<ComponentName>', () => {
  it('renders the expected content', () => {
    render(<ComponentName />);
    expect(screen.getByText('Expected text')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    render(<ComponentName />);
    await user.click(screen.getByRole('button', { name: /action/i }));
    // assert result
  });

  it('shows loading state', () => {
    render(<ComponentName isLoading />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(<ComponentName error="Something failed" />);
    expect(screen.getByText(/something failed/i)).toBeInTheDocument();
  });
});
```

## Playwright template (E2E flow)

```ts
import { test, expect } from '@playwright/test';

test.describe('<flow name>', () => {
  test('completes the primary flow', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Open dashboard');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Dashboard')).toBeVisible();
  });

  test('handles error gracefully', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=ERR')).toBeVisible();
  });
});
```

## Instructions

1. Ask what to test (endpoint path, component file, or user flow)
2. Read the relevant source file(s) to understand the interface
3. Generate tests covering: success path, error path, loading state, empty state, auth boundary
4. Write the test file to the correct location
