from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=15000)
    
    bg = page.evaluate("""() => {
        const html = document.documentElement;
        html.classList.add("dark");
        const style = getComputedStyle(document.documentElement);
        return {
            variable: style.getPropertyValue("--background"),
            bodyBg: getComputedStyle(document.body).backgroundColor,
            htmlBg: getComputedStyle(document.documentElement).backgroundColor
        };
    }""")
    print("CSS --background:", bg["variable"])
    print("Body bg:", bg["bodyBg"])
    print("HTML bg:", bg["htmlBg"])
    browser.close()
