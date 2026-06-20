from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=15000)
    page.reload(wait_until="networkidle")
    
    bg = page.evaluate("""() => {
        return getComputedStyle(document.documentElement).getPropertyValue("--background");
    }""")
    print("After reload:", bg)
    
    # Also check if the dark class is present
    has_dark = page.evaluate("""() => {
        return document.documentElement.classList.contains("dark");
    }""")
    print("Has dark class:", has_dark)
    
    # Take a fresh screenshot
    page.screenshot(path="test-screenshots/dark_theme_v2.png", full_page=True)
    print("Screenshot saved")
    
    browser.close()
