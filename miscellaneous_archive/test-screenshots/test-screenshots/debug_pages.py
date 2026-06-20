from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})

    # Check dashboard
    page.goto("http://localhost:3000/dashboard", wait_until="networkidle", timeout=15000)
    page.screenshot(path="test-screenshots/debug_dashboard.png", full_page=True)
    url = page.url
    title = page.title()
    content = page.inner_text("body")[:500]
    print(f"Dashboard URL: {url}")
    print(f"Dashboard title: {title}")
    print(f"Dashboard content (first 500 chars):\n{content}")

    # Check backtest
    page.goto("http://localhost:3000/backtest", wait_until="networkidle", timeout=10000)
    page.screenshot(path="test-screenshots/debug_backtest.png", full_page=True)
    url2 = page.url
    content2 = page.inner_text("body")[:500]
    print(f"\nBacktest URL: {url2}")
    print(f"Backtest content (first 500 chars):\n{content2}")

    browser.close()
