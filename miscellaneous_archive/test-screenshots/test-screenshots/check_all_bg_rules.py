from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=15000)
    page.reload(wait_until="networkidle")
    
    # Get ALL CSS rules that set --background
    result = page.evaluate("""() => {
        const sheets = document.styleSheets;
        let bgRules = [];
        for (let s of sheets) {
            try {
                for (let r of s.cssRules) {
                    if (r.cssText && r.cssText.includes("--background")) {
                        bgRules.push(r.cssText.substring(0, 400));
                    }
                }
            } catch(e) {}
        }
        return bgRules;
    }""")
    
    print(f"Found {len(result)} rules with --background:")
    for i, rule in enumerate(result):
        print(f"\n--- Rule {i+1} ---")
        print(rule)
    
    browser.close()
