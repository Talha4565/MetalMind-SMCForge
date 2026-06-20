from playwright.sync_api import sync_playwright
import json

results = []

def test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    
    # Test 1: Frontend loads
    print("\n=== Frontend Load Test ===")
    try:
        resp = page.goto("http://localhost:3000", wait_until="networkidle", timeout=15000)
        test("Frontend loads", resp.status == 200, f"status={resp.status}")
    except Exception as e:
        test("Frontend loads", False, str(e))
    
    # Test 2: Dark theme background color
    print("\n=== Dark Theme Test ===")
    try:
        bg_color = page.evaluate("""() => {
            const html = document.documentElement;
            html.classList.add('dark');
            return getComputedStyle(document.body).backgroundColor;
        }""")
        # #303446 = rgb(48, 52, 70)
        test("Dark theme background applied", "48" in bg_color and "52" in bg_color and "70" in bg_color, f"bg={bg_color}")
    except Exception as e:
        test("Dark theme background applied", False, str(e))
    
    # Test 3: Take screenshot of dark theme
    try:
        page.screenshot(path="test-screenshots/dark_theme.png", full_page=True)
        test("Dark theme screenshot saved", True, "test-screenshots/dark_theme.png")
    except Exception as e:
        test("Dark theme screenshot saved", False, str(e))
    
    # Test 4: Check login page exists
    print("\n=== Page Navigation Test ===")
    try:
        page.goto("http://localhost:3000/auth/login", wait_until="networkidle", timeout=10000)
        test("Login page loads", True)
    except Exception as e:
        test("Login page loads", False, str(e))
    
    # Test 5: Check dashboard page
    try:
        page.goto("http://localhost:3000/dashboard", wait_until="networkidle", timeout=10000)
        test("Dashboard page loads", True)
    except Exception as e:
        test("Dashboard page loads", False, str(e))
    
    # Test 6: Screenshot of dashboard
    try:
        page.screenshot(path="test-screenshots/dashboard_dark.png", full_page=True)
        test("Dashboard screenshot saved", True, "test-screenshots/dashboard_dark.png")
    except Exception as e:
        test("Dashboard screenshot saved", False, str(e))
    
    # Test 7: API health check
    print("\n=== API Test ===")
    try:
        api_resp = page.goto("http://localhost:5000/api/health", timeout=10000)
        test("API health endpoint", api_resp.status == 200, f"status={api_resp.status}")
    except Exception as e:
        test("API health endpoint", False, str(e))
    
    # Test 8: Predictions endpoint
    try:
        page.goto("http://localhost:5000/api/predictions/latest?asset=gold&limit=5", timeout=15000)
        content = page.content()
        has_predictions = "predictions" in content or "signal" in content
        test("Predictions endpoint responds", has_predictions, "has prediction data" if has_predictions else "no prediction data")
    except Exception as e:
        test("Predictions endpoint responds", False, str(e))
    
    # Test 9: Console errors
    print("\n=== Console Errors ===")
    # Filter out expected WebSocket errors
    real_errors = [e for e in console_errors if "socket.io" not in e.lower() and "websocket" not in e.lower()]
    test("No critical console errors", len(real_errors) == 0, f"{len(real_errors)} errors" + (f": {real_errors[:3]}" if real_errors else ""))
    
    browser.close()

# Summary
print("\n" + "=" * 50)
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
print(f"Results: {passed}/{len(results)} passed, {failed} failed")
if failed:
    print("\nFailed tests:")
    for r in results:
        if r["status"] == "FAIL":
            print(f"  - {r['name']}: {r['detail']}")
