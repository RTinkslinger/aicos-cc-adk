"""Integration tests for web-tools-mcp — run via direct import on droplet."""

import json
import sys

sys.path.insert(0, "/opt/web-tools-mcp")

from server import cookie_status, health_check, web_browse, web_scrape, web_search

TEST_URLS = [
    ("blog", "https://simonwillison.net/2024/Dec/19/one-shot-python-tools/"),
    ("saas", "https://linear.app/features"),
    ("ecommerce", "https://www.amazon.com/dp/B0DKHZTGQS"),
    ("cloudflare", "https://discord.com/safety"),
    ("docs", "https://docs.anthropic.com/en/docs/about-claude/models"),
    ("404", "https://example.com/nonexistent-page-404"),
]


def test_health():
    print("=== health_check ===")
    r = health_check()
    print(json.dumps(r, indent=2))
    assert r["server"] == "ok", f"Server not ok: {r}"
    assert "ok" in r["playwright"], f"Playwright not ok: {r}"
    print("PASS\n")


def test_scrape():
    print("=== web_scrape (6 URLs) ===")
    for label, url in TEST_URLS:
        r = web_scrape(url)
        status = r.get("status", "?")
        length = r.get("content_length", 0)
        is_404 = r.get("is_404", False)
        error = r.get("error", "")
        print(
            f"  {label:12} | status={status} | len={length:>6} "
            f"| 404={is_404} | err={error[:40]}"
        )
    print("PASS\n")


def test_browse():
    print("=== web_browse (5 URLs) ===")
    browse_urls = [u for u in TEST_URLS if u[0] != "ecommerce"]
    for label, url in browse_urls:
        r = web_browse(url)
        status = r.get("status", "unknown")
        title = r.get("title", "?")[:40]
        length = r.get("content_length", 0)
        err = r.get("error", "")[:50]
        print(f"  {label:12} | {status:>5} | {length:>6} | {title:40} | {err}")

    # Test evaluate action
    print("\n  --- evaluate test ---")
    r = web_browse(
        "https://example.com",
        action="evaluate",
        text='JSON.stringify({title: document.title, links: document.querySelectorAll("a").length})',
    )
    print(f"  eval result: {r.get('eval_result', r.get('error', '?'))}")
    print("PASS\n")


def test_search():
    print("=== web_search (2 queries) ===")
    for q in ["Claude API pricing 2025", "best Python web scraping tools"]:
        r = web_search(q, limit=3)
        count = r.get("count", 0)
        source = r.get("source", "?")
        print(f"  query='{q[:30]}' | source={source} | results={count}")
    print("PASS\n")


def test_cookies():
    print("=== cookie_status ===")
    r = cookie_status()
    for c in r.get("cookies", []):
        warning = c.get("warning", "fresh")
        print(
            f"  {c['domain']:20} | {c['cookie_count']:>4} cookies "
            f"| {c['age_days']} days | {warning}"
        )
    print(f"  Cookie dir: {r.get('cookie_dir')}")
    print("PASS\n")


def test_authenticated_browse():
    print("=== web_browse with cookies ===")
    auth_urls = [
        ("youtube", "https://www.youtube.com", "youtube.com"),
        ("x-home", "https://x.com/home", "x.com"),
        ("x-bookmarks", "https://x.com/i/bookmarks", "x.com"),
        ("substack", "https://substack.com/inbox/post/190905077", "substack.com"),
    ]
    for label, url, domain in auth_urls:
        r = web_browse(url, cookies_domain=domain)
        status = r.get("status", "unknown")
        cookies_info = r.get("cookies_loaded", {})
        title = r.get("title", "?")[:30]
        content_len = r.get("content_length", 0)
        warn = cookies_info.get("warning", "")[:30]
        err = cookies_info.get("error", "")[:30]
        print(
            f"  {label:14} | {status:>5} | cookies={cookies_info.get('count', 0):>3} "
            f"| {title:30} | len={content_len} | {warn}{err}"
        )

    # LinkedIn WITHOUT cookies — expect login wall (Layer 4 only)
    print("  --- LinkedIn (no cookies, expect login wall) ---")
    r = web_browse(
        "https://www.linkedin.com/in/kumaraakash/recent-activity/all/"
    )
    title = r.get("title", "?")[:30]
    content = r.get("content", "")[:200].lower()
    has_login_wall = (
        "sign in" in content or "log in" in content or "join" in content
    )
    print(
        f"  linkedin      | {r.get('status', '?'):>5} | cookies=  0 "
        f"| {title:30} | login_wall={has_login_wall}"
    )
    print("PASS\n")


if __name__ == "__main__":
    import sys

    # Allow running specific tests
    tests = {
        "health": test_health,
        "scrape": test_scrape,
        "browse": test_browse,
        "search": test_search,
        "cookies": test_cookies,
        "auth": test_authenticated_browse,
    }

    if len(sys.argv) > 1:
        for name in sys.argv[1:]:
            if name in tests:
                tests[name]()
            else:
                print(f"Unknown test: {name}. Available: {list(tests.keys())}")
    else:
        test_health()
        test_scrape()
        test_browse()
        test_search()
        test_cookies()
        test_authenticated_browse()
        print("All tests complete.")
