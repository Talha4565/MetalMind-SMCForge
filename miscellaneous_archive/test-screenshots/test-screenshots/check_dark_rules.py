from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=15000)
    page.reload(wait_until="networkidle")
    
    # Find all stylesheets and check their content
    result = page.evaluate("""() => {
        const sheets = document.styleSheets;
        let allDark = [];
        for (let s of sheets) {
            try {
                for (let r of s.cssRules) {
                    if (r.selectorText && r.selectorText.includes(".dark")) {
                        allDark.push({
                            selector: r.selectorText,
                            css: r.cssText.substring(0, 300)
                        });
                    }
                }
            } catch(e) {}
        }
        return allDark;
    }""")
    
    print("All .dark CSS rules:")
    for rule in result:
        print(f"\n  Selector: {rule['selector']}")
        print(f"  CSS: {rule['css']}")
    
    browser.close()
