"""Web Tools MCP Server — browse, scrape, search for any Claude surface.

Deployed on DO droplet alongside (but separate from) ai-cos-mcp.
Uses system Google Chrome via Playwright channel='chrome'.
"""

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(
    "web-tools-mcp",
    instructions="Web tools MCP server. Provides browsing, scraping, and search capabilities.",
)

CHROME_PATH = os.getenv("CHROME_PATH", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
COOKIE_DIR = os.getenv("COOKIE_DIR", "/opt/ai-cos/cookies")


@mcp.tool()
def health_check() -> dict:
    """Check server, Chrome, and Playwright connectivity."""
    import shutil

    result = {"server": "ok", "chrome": "unknown", "playwright": "unknown"}

    # Check Chrome binary
    chrome = (
        shutil.which("google-chrome")
        or shutil.which("google-chrome-stable")
        or CHROME_PATH
    )
    result["chrome"] = chrome if chrome else "not found"

    # Check Playwright can launch Chrome
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome",
                headless=True,
                args=["--no-sandbox", "--disable-gpu"],
            )
            page = browser.new_page()
            page.goto("https://example.com", timeout=10000)
            title = page.title()
            browser.close()
        result["playwright"] = f"ok (loaded: {title})"
    except Exception as e:
        result["playwright"] = f"error: {e}"

    result["firecrawl_configured"] = bool(FIRECRAWL_API_KEY)
    return result


# ---------------------------------------------------------------------------
# web_scrape — Jina Reader (free) primary, Firecrawl fallback
# ---------------------------------------------------------------------------


@mcp.tool()
def web_scrape(url: str, use_firecrawl: bool = False) -> dict:
    """Extract content from a URL as clean markdown.

    Uses Jina Reader (free) by default. Set use_firecrawl=True for
    Firecrawl extraction (1 credit, sometimes more detailed).

    Args:
        url: The URL to extract content from
        use_firecrawl: Force Firecrawl instead of Jina (costs 1 credit)
    """
    import httpx

    if use_firecrawl and FIRECRAWL_API_KEY:
        return _scrape_firecrawl(url)

    # Jina Reader: prepend r.jina.ai/ to any URL
    jina_url = f"https://r.jina.ai/{url}"
    try:
        resp = httpx.get(
            jina_url,
            headers={"Accept": "text/plain"},
            timeout=15.0,
            follow_redirects=True,
        )
        content = resp.text
        is_404 = "Warning: Target URL returned error 404" in content

        return {
            "source": "jina",
            "url": url,
            "status": 404 if is_404 else resp.status_code,
            "content": content[:50000],
            "content_length": len(content),
            "is_404": is_404,
        }
    except httpx.TimeoutException:
        return {"source": "jina", "url": url, "error": "timeout (15s)", "content": ""}
    except Exception as e:
        # Jina failed — try Firecrawl if configured
        if FIRECRAWL_API_KEY:
            return _scrape_firecrawl(url)
        return {"source": "jina", "url": url, "error": str(e), "content": ""}


def _scrape_firecrawl(url: str) -> dict:
    """Firecrawl scrape with mandatory metadata validation."""
    import httpx

    try:
        resp = httpx.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            timeout=30.0,
        )
        data = resp.json()

        if not data.get("success"):
            return {
                "source": "firecrawl",
                "url": url,
                "error": data.get("error", "unknown"),
                "content": "",
            }

        result_data = data.get("data", {})
        metadata = result_data.get("metadata", {})

        # MANDATORY: validate metadata (Firecrawl hallucinates on blocked pages)
        status_code = metadata.get("statusCode", 0)
        actual_url = metadata.get("url", "")

        return {
            "source": "firecrawl",
            "url": url,
            "actual_url": actual_url,
            "status": status_code,
            "redirected": actual_url != url and bool(actual_url),
            "content": result_data.get("markdown", "")[:50000],
            "content_length": len(result_data.get("markdown", "")),
            "title": metadata.get("title", ""),
        }
    except Exception as e:
        return {"source": "firecrawl", "url": url, "error": str(e), "content": ""}


# ---------------------------------------------------------------------------
# web_browse — Playwright + system Chrome + cookie injection
# ---------------------------------------------------------------------------


def _load_cookies(context, domain: str) -> dict:
    """Load Netscape-format cookies into a Playwright browser context.

    Reads from COOKIE_DIR/<domain>.txt (synced from Mac via cookie-sync.sh).
    Returns dict with count loaded, file path, and staleness warning.
    """
    import time
    from pathlib import Path

    cookie_file = Path(COOKIE_DIR) / f"{domain}.txt"
    result: dict = {"domain": domain, "file": str(cookie_file)}

    if not cookie_file.exists():
        result["error"] = f"No cookie file found at {cookie_file}"
        result["count"] = 0
        return result

    # Check staleness (warn if > 7 days old)
    age_days = (time.time() - cookie_file.stat().st_mtime) / 86400
    if age_days > 7:
        result["warning"] = (
            f"Cookies are {age_days:.0f} days old — may be expired. "
            "Re-run cookie-sync.sh."
        )

    cookies = []
    for line in cookie_file.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        host, _flag, path, secure, expiry, name, value = parts[:7]
        cookies.append(
            {
                "name": name,
                "value": value,
                "domain": host,
                "path": path,
                "secure": secure == "TRUE",
                "expires": int(expiry) if expiry != "0" else -1,
            }
        )

    if cookies:
        context.add_cookies(cookies)

    result["count"] = len(cookies)
    return result


@mcp.tool()
def web_browse(
    url: str,
    action: str = "snapshot",
    selector: str = "",
    text: str = "",
    cookies_domain: str = "",
    wait_for: str = "networkidle",
    wait_after_ms: int = 3000,
    timeout_ms: int = 15000,
) -> dict:
    """Navigate to a URL and interact with it via Playwright + system Chrome.

    Actions:
      - snapshot: Navigate and return page title + text content summary
      - click: Click an element matching selector
      - fill: Fill a form field matching selector with text
      - screenshot: Take a screenshot (returned as base64)
      - evaluate: Run JavaScript and return result

    Args:
        url: Target URL
        action: What to do — snapshot, click, fill, screenshot, evaluate
        selector: CSS selector for click/fill/evaluate actions
        text: Text to fill (for fill action) or JS code (for evaluate)
        cookies_domain: Load cookies for this domain from /opt/ai-cos/cookies/<domain>.txt
            (e.g. "youtube.com"). Enables authenticated browsing.
        wait_for: Wait strategy — networkidle, domcontentloaded, load
        wait_after_ms: Extra wait after navigation for JS rendering (default 3000ms).
            Needed for SPAs like YouTube, X, etc. Set to 0 for static pages.
        timeout_ms: Navigation timeout in milliseconds
    """
    import time

    from playwright.sync_api import sync_playwright

    result: dict = {"url": url, "action": action}

    try:
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

            # Load cookies from Netscape file if domain specified
            if cookies_domain:
                cookies_loaded = _load_cookies(context, cookies_domain)
                result["cookies_loaded"] = cookies_loaded

            page = context.new_page()

            # Register console listener BEFORE navigation
            console_errors: list[str] = []
            page.on(
                "console",
                lambda msg: (
                    console_errors.append(msg.text) if msg.type == "error" else None
                ),
            )

            page.goto(url, wait_until=wait_for, timeout=timeout_ms)

            # Extra wait for JS-heavy SPAs (YouTube, X, etc.)
            if wait_after_ms > 0:
                time.sleep(wait_after_ms / 1000)

            result["title"] = page.title()
            result["final_url"] = page.url

            if action == "snapshot":
                text_content = page.evaluate("document.body.innerText")
                result["content"] = text_content[:30000] if text_content else ""
                result["content_length"] = len(text_content) if text_content else 0
                result["console_errors"] = console_errors
                result["status"] = "ok"

            elif action == "click":
                if not selector:
                    result["error"] = "selector required for click action"
                else:
                    page.click(selector, timeout=5000)
                    result["status"] = "clicked"
                    result["title"] = page.title()

            elif action == "fill":
                if not selector or not text:
                    result["error"] = "selector and text required for fill action"
                else:
                    page.fill(selector, text, timeout=5000)
                    result["status"] = "filled"

            elif action == "screenshot":
                import base64

                screenshot_bytes = page.screenshot(full_page=False)
                result["screenshot_base64"] = base64.b64encode(
                    screenshot_bytes
                ).decode()
                result["status"] = "ok"

            elif action == "evaluate":
                if not text:
                    result["error"] = "text (JS code) required for evaluate action"
                else:
                    eval_result = page.evaluate(text)
                    result["eval_result"] = str(eval_result)[:10000]
                    result["status"] = "ok"

            else:
                result["error"] = f"unknown action: {action}"

            browser.close()

    except Exception as e:
        result["error"] = str(e)
        result["status"] = "error"

    return result


# ---------------------------------------------------------------------------
# web_search — Jina search (free) primary, Firecrawl fallback
# ---------------------------------------------------------------------------


@mcp.tool()
def web_search(query: str, limit: int = 5) -> dict:
    """Search the web and return results with titles, URLs, and snippets.

    Uses Jina Reader search (free) by default. Falls back to Firecrawl
    search if Jina returns no results and Firecrawl is configured.

    Args:
        query: Search query
        limit: Max results to return (default 5)
    """
    import httpx

    # Jina search (s.jina.ai) requires an API key — not free like Jina Reader.
    # Use Firecrawl search as primary engine.
    if FIRECRAWL_API_KEY:
        try:
            resp = httpx.post(
                "https://api.firecrawl.dev/v1/search",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"query": query, "limit": limit},
                timeout=15.0,
            )
            data = resp.json()
            results = data.get("data", [])[:limit]
            return {
                "source": "firecrawl",
                "query": query,
                "results": [
                    {
                        "title": r.get(
                            "title", r.get("metadata", {}).get("title", "")
                        ),
                        "url": r.get("url", ""),
                        "snippet": r.get("markdown", r.get("description", ""))[:500],
                    }
                    for r in results
                ],
                "count": len(results),
            }
        except Exception as e:
            return {
                "source": "firecrawl",
                "query": query,
                "error": str(e),
                "results": [],
            }

    return {
        "source": "none",
        "query": query,
        "error": "No search engines available",
        "results": [],
    }


# ---------------------------------------------------------------------------
# cookie_status — check cookie freshness
# ---------------------------------------------------------------------------


@mcp.tool()
def cookie_status() -> dict:
    """Check which domain cookies are available and their freshness.

    Returns list of cookie files with domain, cookie count, age in days,
    and staleness warning if older than 7 days.
    """
    import time
    from pathlib import Path

    cookie_dir = Path(COOKIE_DIR)
    if not cookie_dir.exists():
        return {
            "cookies": [],
            "cookie_dir": str(cookie_dir),
            "error": "Cookie directory not found",
        }

    cookies = []
    for f in sorted(cookie_dir.glob("*.txt")):
        age_days = (time.time() - f.stat().st_mtime) / 86400
        line_count = sum(
            1
            for line in f.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        )
        entry: dict = {
            "domain": f.stem,
            "cookie_count": line_count,
            "age_days": round(age_days, 1),
            "file": str(f),
        }
        if age_days > 7:
            entry["warning"] = "STALE — re-run cookie-sync.sh on Mac"
        cookies.append(entry)

    return {"cookies": cookies, "cookie_dir": str(cookie_dir)}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
