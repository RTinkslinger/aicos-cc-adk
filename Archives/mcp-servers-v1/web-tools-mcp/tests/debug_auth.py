"""Deep debug: authenticated browse failures on YouTube, X, X bookmarks."""

import json
import sys
import time

sys.path.insert(0, "/opt/web-tools-mcp")

from playwright.sync_api import sync_playwright

from server import _load_cookies


def debug_page(url, cookies_domain, label):
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"DEBUG: {label} -- {url}")
    print(sep)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720},
        )

        # Load cookies
        cookie_result = _load_cookies(context, cookies_domain)
        print(f"Cookies loaded: {cookie_result.get('count', 0)}")
        if cookie_result.get("error"):
            print(f"Cookie error: {cookie_result['error']}")

        # Check what cookies the context actually has
        ctx_cookies = context.cookies()
        print(f"Context cookies count: {len(ctx_cookies)}")
        for c in ctx_cookies[:5]:
            print(
                f"  {c['domain']:20} | {c['name']:20} | "
                f"expires={c.get('expires', '?')}"
            )
        if len(ctx_cookies) > 5:
            print(f"  ... and {len(ctx_cookies) - 5} more")

        page = context.new_page()

        # Navigate
        print("\nNavigating...")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Navigation error: {e}")

        print(f"Title after domcontentloaded: '{page.title()}'")
        print(f"URL: {page.url}")

        # Wait extra for JS rendering
        print("Waiting 5s for JS rendering...")
        time.sleep(5)

        # Check body content
        body_text = page.evaluate(
            "document.body ? document.body.innerText : 'NO BODY'"
        )
        body_len = len(body_text) if body_text else 0
        print(f"Body innerText length: {body_len}")
        if body_text and body_len > 0:
            print(f"First 500 chars:\n{body_text[:500]}")
        else:
            print("Body innerText is EMPTY")

        # Check full HTML size
        html_len = page.evaluate("document.documentElement.innerHTML.length")
        print(f"\nFull HTML length: {html_len}")

        # Sample the HTML for clues
        html_sample = page.evaluate(
            "document.documentElement.innerHTML.substring(0, 1000)"
        )
        print(f"HTML sample (first 1000):\n{html_sample}")

        # Check for login indicators
        has_login = page.evaluate(
            """(() => {
                const text = document.body ? document.body.innerHTML.toLowerCase() : '';
                return {
                    has_login_text: text.includes('log in') || text.includes('sign in'),
                    has_password_field: !!document.querySelector('input[type=password]'),
                    body_classes: document.body ? document.body.className : '',
                };
            })()"""
        )
        print(f"Login indicators: {json.dumps(has_login, indent=2)}")

        # Take screenshot
        screenshot_path = f"/tmp/debug_{label}.png"
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Screenshot saved: {screenshot_path}")

        browser.close()


if __name__ == "__main__":
    targets = [
        ("https://www.youtube.com", "youtube.com", "youtube"),
        ("https://x.com/home", "x.com", "x_home"),
        ("https://x.com/i/bookmarks", "x.com", "x_bookmarks"),
    ]

    # Allow running specific target
    if len(sys.argv) > 1:
        targets = [t for t in targets if t[2] in sys.argv[1:]]

    for url, domain, label in targets:
        debug_page(url, domain, label)
