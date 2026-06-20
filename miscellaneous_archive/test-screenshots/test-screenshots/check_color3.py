from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=15000)
    page.reload(wait_until="networkidle")
    
    # Check multiple elements
    result = page.evaluate("""() => {
        const body = document.body;
        const html = document.documentElement;
        const root = document.getElementById("__next") || document.body.firstElementChild;
        
        return {
            htmlBg: getComputedStyle(html).backgroundColor,
            bodyBg: getComputedStyle(body).backgroundColor,
            rootBg: root ? getComputedStyle(root).backgroundColor : "no root",
            cssVar: getComputedStyle(html).getPropertyValue("--background"),
            bodyClasses: body.className,
            htmlClasses: html.className,
        };
    }""")
    
    for k, v in result.items():
        print(f"{k}: {v}")
    
    # Check if there's a style tag overriding things
    styles = page.evaluate("""() => {
        const sheets = document.styleSheets;
        let bgRules = [];
        for (let s of sheets) {
            try {
                for (let r of s.cssRules) {
                    if (r.cssText && r.cssText.includes("background")) {
                        bgRules.push(r.cssText.substring(0, 200));
                    }
                }
            } catch(e) {}
        }
        return bgRules.slice(0, 10);
    }""")
    
    print("\nCSS rules with 'background':")
    for s in styles:
        print(f"  {s}")
    
    browser.close()
