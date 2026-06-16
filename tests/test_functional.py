"""Phase 1: Functional Testing — All Pages"""
from playwright.sync_api import sync_playwright
import time, json
from datetime import datetime

results = []
def test(name, passed, detail=""):
    results.append({"test": name, "passed": passed, "detail": detail, "time": datetime.now().isoformat()})
    s = "PASS" if passed else "FAIL"
    print(f"  [{s}] {name}" + (f" — {detail}" if detail else ""))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720})

    print("=" * 60)
    print("PHASE 1: FUNCTIONAL TESTING — ALL PAGES")
    print("=" * 60)

    # === AUTH TESTS ===
    print("\n--- Authentication ---")

    # Register page
    print("\n1. Register page")
    try:
        page.goto("http://localhost:3000/auth/register", wait_until="networkidle", timeout=15000)
        test("Register page loads", page.url.endswith("/auth/register"))
        test("Email field exists", page.locator('input[name="email"]').count() > 0)
        test("Password field exists", page.locator('input[name="password"]').count() > 0)
        test("Confirm password field exists", page.locator('input[name="confirmPassword"]').count() > 0)
        test("Theme toggle exists", page.locator('button[aria-label="Toggle theme"]').count() > 0)
        test("Brand panel visible", page.locator("text=smart traders").count() > 0)
    except Exception as e:
        test("Register page", False, str(e)[:80])

    # Login page
    print("\n2. Login page")
    try:
        page.goto("http://localhost:3000/auth/login", wait_until="networkidle", timeout=15000)
        test("Login page loads", page.url.endswith("/auth/login"))
        test("Email field exists", page.locator('input[name="email"]').count() > 0)
        test("Password field exists", page.locator('input[name="password"]').count() > 0)
        
        # Password toggle
        pwd = page.locator('input[name="password"]')
        test("Password starts hidden", pwd.get_attribute('type') == "password")
        eye = page.locator('button:has(svg):not([type="submit"])').first
        if eye.is_visible():
            eye.click()
            page.wait_for_timeout(300)
            test("Toggle shows password", pwd.get_attribute('type') == "text")
            eye.click()
            page.wait_for_timeout(300)
            test("Toggle hides password", pwd.get_attribute('type') == "password")
    except Exception as e:
        test("Login page", False, str(e)[:80])

    # Register + Login flow
    print("\n3. Register + Login flow")
    test_email = f"fyp_test_{int(time.time())}@test.com"
    test_password = "FypTest123!"
    try:
        page.goto("http://localhost:3000/auth/register", wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(1000)
        page.locator('input[name="email"]').fill(test_email)
        page.locator('input[name="password"]').fill(test_password)
        page.locator('input[name="confirmPassword"]').fill(test_password)
        page.locator('button[type="submit"]').click()
        page.wait_for_timeout(3000)
        test("Register redirects to login", "login" in page.url)
        
        page.wait_for_timeout(1000)
        page.locator('input[name="email"]').fill(test_email)
        page.locator('input[name="password"]').fill(test_password)
        page.locator('button[type="submit"]').click()
        page.wait_for_timeout(5000)
        test("Login redirects to dashboard", "dashboard" in page.url)
    except Exception as e:
        test("Register + Login flow", False, str(e)[:80])

    # Wrong password
    print("\n4. Wrong password rejection")
    try:
        page.goto("http://localhost:3000/auth/login", wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(1000)
        page.locator('input[name="email"]').fill(test_email)
        page.locator('input[name="password"]').fill("WrongPassword123!")
        page.locator('button[type="submit"]').click()
        page.wait_for_timeout(3000)
        test("Wrong password stays on login", "login" in page.url)
    except Exception as e:
        test("Wrong password", False, str(e)[:80])

    # === DASHBOARD TESTS ===
    print("\n--- Dashboard ---")
    try:
        page.goto("http://localhost:3000/dashboard", wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(3000)
        test("Dashboard loads", "dashboard" in page.url)
        test("Header exists", page.locator("header").count() > 0)
        test("Sidebar exists", page.locator("aside").count() > 0)
        test("Theme toggle exists", page.locator('button[aria-label="Toggle theme"]').count() > 0)
        test("Live price shows", page.locator("text=XAU").count() > 0 or page.locator("text=XAG").count() > 0)
        test("Signal card exists", page.locator("text=Signal").count() > 0)
        test("Confidence card exists", page.locator("text=Confidence").count() > 0)
        test("TradingView chart loads", page.locator("iframe").count() > 0)
    except Exception as e:
        test("Dashboard", False, str(e)[:80])

    # === RISK PAGE ===
    print("\n--- Risk Calculator ---")
    try:
        page.goto("http://localhost:3000/dashboard/risk", wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        test("Risk page loads", page.locator("text=Position sizing").count() > 0)
        test("Balance input exists", page.locator('input[type="number"]').count() > 0)
        test("Risk profiles exist", page.locator("text=Conservative").count() > 0)
        test("Risk parameters visible", page.locator("text=Take profit").count() > 0)
        test("Risk/Reward visible", page.locator("text=Risk / Reward").count() > 0)
        test("Price levels visible", page.locator("text=Stop loss").count() > 0)
    except Exception as e:
        test("Risk page", False, str(e)[:80])

    # === BACKTEST PAGE ===
    print("\n--- Backtest ---")
    try:
        page.goto("http://localhost:3000/backtest", wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        test("Backtest page loads", "backtest" in page.url)
        test("Has dashboard layout", page.locator("header").count() > 0)
    except Exception as e:
        test("Backtest page", False, str(e)[:80])

    # === WATCHLIST PAGE ===
    print("\n--- Watchlist ---")
    try:
        page.goto("http://localhost:3000/dashboard/watchlist", wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        test("Watchlist page loads", "watchlist" in page.url)
        test("Has dashboard layout", page.locator("header").count() > 0)
    except Exception as e:
        test("Watchlist page", False, str(e)[:80])

    # === PROFILE PAGE ===
    print("\n--- Profile ---")
    try:
        page.goto("http://localhost:3000/dashboard/profile", wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        test("Profile page loads", "profile" in page.url)
        test("Profile form visible", page.locator("text=Profile Information").count() > 0)
        test("Security section visible", page.locator("text=Security").count() > 0)
    except Exception as e:
        test("Profile page", False, str(e)[:80])

    # === THEME TOGGLE ===
    print("\n--- Theme Toggle ---")
    try:
        page.goto("http://localhost:3000/dashboard", wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        initial = "dark" in page.evaluate("() => document.documentElement.className")
        toggle = page.locator('button[aria-label="Toggle theme"]')
        if toggle.count() > 0 and toggle.first.is_visible():
            toggle.first.click()
            page.wait_for_timeout(1000)
            after = "dark" in page.evaluate("() => document.documentElement.className")
            test("Theme toggle switches", initial != after)
        else:
            test("Theme toggle exists", False, "Not visible")
    except Exception as e:
        test("Theme toggle", False, str(e)[:80])

    browser.close()

# Save results
passed = sum(1 for r in results if r["passed"])
total = len(results)

print(f"\n{'=' * 60}")
print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.0f}%)")
print(f"{'=' * 60}")

# Save to JSON
with open("reports/phase1_functional_results.json", "w") as f:
    json.dump({"summary": {"total": total, "passed": passed, "failed": total - passed}, "tests": results}, f, indent=2)

print(f"\nResults saved to reports/phase1_functional_results.json")
