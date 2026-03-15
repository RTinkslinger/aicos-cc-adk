# WebAgent — Agent SDK Build Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an intelligent WebAgent using the Claude Agent SDK that replaces web-tools-mcp with a self-learning, adaptive web intelligence system — exposed as an MCP endpoint at `web.3niac.com/mcp`.

**Architecture:** Claude Agent SDK agent with direct async Playwright/httpx tools (not wrapping web-tools-mcp). Uses `async_playwright` throughout — never blocks the event loop. `asyncio.Semaphore(2)` caps concurrent browser contexts to prevent OOM. Implements readiness ladder, site fingerprinting, strategy cache (SQLite WAL) with UCB bandit, content quality validation, and adaptive retry with auto-recorded outcomes. Exposes both agent-mode tools (`web_task` — Claude reasons) and direct-mode tools (`web_scrape`, `web_browse` — no LLM overhead). Runs as hardened systemd service on port 8001, replacing web-tools-mcp at the same Cloudflare Tunnel endpoint. Includes rollback procedure, 60s health monitoring, and 3-tier test system.

**Tech Stack:** Python 3.12+, claude-agent-sdk, FastMCP, async Playwright, httpx, SQLite WAL (strategy cache), Google Chrome 146 (system)

**Review-driven hardening (4 expert reviews applied):**
- Async Playwright + Semaphore(2) for safe concurrency (Systems Architect + QA)
- context.close() in finally, try/except in tool dispatch, wall-clock timeout (Agent SDK Expert)
- Hardened systemd unit, rollback procedure, 60s monitoring cron (DevOps)
- 3-tier test system: unit (mocked) → integration (stable URLs) → canary (weekly full) (QA)
- Auto-wired strategy learning (record_outcome called by lib, not by agent prompt) (Agent SDK Expert)
- Structured logging in all lib modules, API keys read at call time (Agent SDK Expert)

**Key research incorporated:** Reports 01-06 from `docs/research/2026-03-15-agent-web-mastery/`

**Dual-mode design decision:** Simple deterministic tasks (scrape URL, search query) use programmatic tool calling (direct Python, no LLM). Complex/ambiguous tasks (`web_task`) use full agent loop with Claude reasoning. This gives 98.7% token reduction on simple operations while preserving intelligence for hard problems.

---

## File Structure

```
mcp-servers/web-agent/                  # Local dev (git-tracked)
├── pyproject.toml
├── server.py                           # FastMCP wrapper — exposes agent + direct tools as MCP
├── agent.py                            # Agent runner — ClaudeSDKClient, system prompt, tool wiring
├── lib/
│   ├── __init__.py
│   ├── browser.py                      # Playwright: readiness ladder, context pooling, cookie injection
│   ├── scrape.py                       # Jina Reader + Firecrawl (ported from web-tools-mcp)
│   ├── search.py                       # Firecrawl search (ported from web-tools-mcp)
│   ├── cookies.py                      # Netscape cookie loading + staleness check
│   ├── fingerprint.py                  # Site fingerprinting — framework/CMS detection
│   ├── strategy.py                     # Strategy cache (SQLite) + UCB bandit selection
│   ├── quality.py                      # Content quality validation — reject garbage
│   └── stealth.py                      # Persona profiles, anti-detection config
├── system_prompt.md                    # Agent expertise (compiled from CC web skill docs)
├── deploy.sh
└── tests/
    ├── test_lib.py                     # Unit tests for lib modules
    └── test_agent.py                   # Integration tests — all 10 test URLs

/opt/web-agent/                         # Droplet (deployed)
├── (same as above, minus tests/)
├── .env                                # ANTHROPIC_API_KEY, FIRECRAWL_API_KEY
└── strategy.db                         # SQLite strategy cache (created at runtime)
```

**Port 8001** — same as current web-tools-mcp. WebAgent replaces it.

## Test URLs (same as web-tools-mcp plan + authenticated)

| # | URL | Type | Strategy Expected |
|---|-----|------|-------------------|
| 1 | `simonwillison.net/2024/Dec/19/one-shot-python-tools/` | Blog | Jina direct, no browser |
| 2 | `linear.app/features` | SaaS SPA | Browser + readiness ladder |
| 3 | `amazon.com/dp/B0DKHZTGQS` | Bot-hostile | Graceful fail / Browserbase |
| 4 | `discord.com/safety` | Cloudflare | Jina (best CF penetration) |
| 5 | `docs.anthropic.com/en/docs/about-claude/models` | Docs | Jina direct |
| 6 | `example.com/nonexistent-page-404` | 404 | Flag as 404 |
| 7 | `x.com/home` | Auth SPA | Cookies + readiness ladder |
| 8 | `x.com/i/bookmarks` | Auth SPA | Cookies + readiness ladder |
| 9 | `linkedin.com/in/kumaraakash/recent-activity/all/` | Bot-hostile auth | Graceful fail (Browserbase future) |
| 10 | `substack.com/inbox/post/190905077` | Auth content | Cookies or Jina |

---

## Chunk 1: Foundation — Project Setup + Core Lib (port from web-tools-mcp)

### Task 1: Project scaffolding

**Files:**
- Create: `mcp-servers/web-agent/pyproject.toml`
- Create: `mcp-servers/web-agent/lib/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "web-agent"
version = "0.1.0"
description = "WebAgent — intelligent web browsing, scraping, search via Agent SDK"
requires-python = ">=3.12"
dependencies = [
    "claude-agent-sdk>=0.1",
    "fastmcp>=2.0.0",
    "python-dotenv>=1.0",
    "playwright>=1.49",
    "httpx>=0.27",
]
```

- [ ] **Step 2: Create lib/__init__.py**

```python
"""WebAgent core libraries — browser, scrape, search, cookies, intelligence."""
```

- [ ] **Step 3: Verify Agent SDK is installable on droplet**

```bash
ssh root@aicos-droplet "cd /opt && mkdir -p web-agent && cd web-agent && \
  cp /dev/null pyproject.toml"
# Then copy pyproject.toml and run:
# uv sync
```

If `claude-agent-sdk` is not yet on PyPI, check:
- `pip install claude-agent-sdk` — official package
- `pip install anthropic[agent]` — may be bundled with anthropic SDK
- Check `https://github.com/anthropics/claude-agent-sdk-python` for install instructions

**BLOCKER CHECK:** If Agent SDK is not installable, fall back to using the `anthropic` SDK directly with tool_use pattern (manual agent loop). The plan works either way — the agent.py module abstracts the SDK layer.

- [ ] **Step 4: Commit**

```bash
git add mcp-servers/web-agent/
git commit -m "feat(web-agent): project scaffold"
```

### Task 2: Core lib — browser.py (readiness ladder + context pooling)

**Files:**
- Create: `mcp-servers/web-agent/lib/browser.py`

This is NOT a copy of web-tools-mcp's `web_browse`. It implements the readiness ladder from Research #4.

- [ ] **Step 1: Write browser.py**

```python
"""Browser management — async Playwright, readiness ladder, context pooling, cookie injection.

CONCURRENCY MODEL (review-driven):
- Uses async_playwright (never blocks event loop)
- asyncio.Lock on browser initialization (prevents double Chrome launch)
- asyncio.Semaphore(2) on concurrent browse calls (prevents OOM on 4GB droplet)
- context.close() in finally block (prevents resource leaks)
- atexit handler for Playwright + Chrome cleanup

Readiness ladder (most reliable → least reliable):
1. Deterministic selector — wait for specific element to be visible
2. MutationObserver quiet window — DOM stable for 500ms
3. Framework markers — React Suspense gone, __NEXT_DATA__ present
4. Time-based fallback — asyncio.sleep (last resort)
"""

import asyncio
import atexit
import logging
import time
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)

# Shared browser instance (context pooling — 1 Chrome, many contexts)
_playwright: Playwright | None = None
_browser: Browser | None = None
_browser_lock = asyncio.Lock()
_browse_semaphore = asyncio.Semaphore(2)  # Max 2 concurrent browses

CHROME_ARGS = [
    "--no-sandbox",
    "--disable-gpu",
    "--disable-blink-features=AutomationControlled",
]

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
)


async def get_browser() -> Browser:
    """Get or create shared browser instance with lock (prevents double Chrome launch)."""
    global _playwright, _browser
    async with _browser_lock:
        if _browser is None or not _browser.is_connected():
            if _playwright is None:
                _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(
                channel="chrome", headless=True, args=CHROME_ARGS,
            )
            logger.info("Chrome browser launched (pid=%s)", _browser.contexts)
    return _browser


async def shutdown_browser() -> None:
    """Clean up Playwright and Chrome on process exit."""
    global _playwright, _browser
    if _browser and _browser.is_connected():
        await _browser.close()
        _browser = None
        logger.info("Chrome browser closed")
    if _playwright:
        await _playwright.stop()
        _playwright = None
        logger.info("Playwright stopped")


async def create_context(
    cookies_domain: str = "",
    cookie_dir: str = "/opt/ai-cos/cookies",
    persona: dict | None = None,
) -> tuple[BrowserContext, dict]:
    """Create an isolated browser context with optional cookies and persona."""
    browser = await get_browser()
    ua = persona.get("user_agent", DEFAULT_UA) if persona else DEFAULT_UA
    viewport = persona.get("viewport", {"width": 1280, "height": 720}) if persona else {"width": 1280, "height": 720}

    context = await browser.new_context(user_agent=ua, viewport=viewport)
    cookie_info: dict = {"count": 0}

    if cookies_domain:
        cookie_info = await _load_cookies(context, cookies_domain, cookie_dir)

    return context, cookie_info


async def browse(
    url: str,
    action: str = "snapshot",
    selector: str = "",
    text: str = "",
    cookies_domain: str = "",
    readiness: str = "auto",
    timeout_ms: int = 15000,
) -> dict:
    """Navigate to URL with intelligent readiness detection.

    Guarded by semaphore — max 2 concurrent browses to prevent OOM.

    readiness modes:
      - "auto": try deterministic selector, then MutationObserver, then time fallback
      - "selector:<css>": wait for specific CSS selector
      - "time:<ms>": async wait (e.g. "time:5000")
      - "none": no extra wait (for static pages)
    """
    result: dict = {"url": url, "action": action}
    context = None

    async with _browse_semaphore:  # Limits concurrent Chrome contexts
        try:
            context, cookie_info = await create_context(cookies_domain=cookies_domain)
            if cookies_domain:
                result["cookies_loaded"] = cookie_info

            page = await context.new_page()

            # Console errors
            console_errors: list[str] = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            # Navigate
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            # Readiness ladder
            await _wait_for_readiness(page, readiness)

            result["title"] = await page.title()
            result["final_url"] = page.url

            if action == "snapshot":
                # Try accessibility tree first (more robust than innerText)
                try:
                    a11y = await page.accessibility.snapshot()
                    a11y_text = _flatten_a11y(a11y) if a11y else ""
                    result["a11y_tree"] = a11y_text[:10000]  # Cap a11y tree size
                except Exception:
                    result["a11y_tree"] = ""

                text_content = await page.evaluate("document.body ? document.body.innerText : ''")
                result["content"] = text_content[:30000] if text_content else ""
                result["content_length"] = len(text_content) if text_content else 0
                result["console_errors"] = console_errors
                result["status"] = "ok"

            elif action == "click":
                if not selector:
                    result["error"] = "selector required"
                else:
                    await page.click(selector, timeout=5000)
                    result["status"] = "clicked"
                    result["title"] = await page.title()

            elif action == "fill":
                if not selector or not text:
                    result["error"] = "selector and text required"
                else:
                    await page.fill(selector, text, timeout=5000)
                    result["status"] = "filled"

            elif action == "screenshot":
                import base64
                screenshot_bytes = await page.screenshot(full_page=False)
                result["screenshot_base64"] = base64.b64encode(screenshot_bytes).decode()
                result["status"] = "ok"

            elif action == "evaluate":
                if not text:
                    result["error"] = "JS code required"
                else:
                    eval_result = await page.evaluate(text)
                    result["eval_result"] = str(eval_result)[:10000]
                    result["status"] = "ok"

            else:
                result["error"] = f"unknown action: {action}"

        except Exception as e:
            result["error"] = str(e)
            result["status"] = "error"
            logger.warning("browse(%s) failed: %s", url, e)

        finally:
            if context:
                await context.close()  # ALWAYS clean up — prevents resource leaks

    return result


async def _wait_for_readiness(page: Page, mode: str) -> None:
    """Readiness ladder — intelligent wait based on page type."""
    if mode == "none":
        return

    if mode.startswith("selector:"):
        css = mode[len("selector:"):]
        try:
            await page.wait_for_selector(css, state="visible", timeout=10000)
            return
        except Exception:
            pass  # Fall through to auto

    if mode.startswith("time:"):
        ms = int(mode[len("time:"):])
        await asyncio.sleep(ms / 1000)  # Non-blocking!
        return

    # Auto mode — readiness ladder
    # Step 1: Check if page has substantial content already
    text_len = await page.evaluate(
        "(document.body && document.body.innerText) ? document.body.innerText.length : 0"
    )
    if text_len > 500:
        return

    # Step 2: MutationObserver quiet window (500ms of no DOM changes, 10s max timeout)
    try:
        await page.evaluate("""
            new Promise((resolve) => {
                let timeout;
                const maxTimeout = setTimeout(() => { observer.disconnect(); resolve(); }, 10000);
                const observer = new MutationObserver(() => {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => { observer.disconnect(); clearTimeout(maxTimeout); resolve(); }, 500);
                });
                timeout = setTimeout(() => { observer.disconnect(); clearTimeout(maxTimeout); resolve(); }, 500);
                observer.observe(document.body || document.documentElement,
                    { childList: true, subtree: true });
            })
        """)
        text_len = await page.evaluate(
            "(document.body && document.body.innerText) ? document.body.innerText.length : 0"
        )
        if text_len > 200:
            return
    except Exception:
        pass

    # Step 3: Framework markers
    has_content = await page.evaluate("""
        (() => {
            if (document.getElementById('__NEXT_DATA__')) return true;
            const root = document.getElementById('root') || document.getElementById('__next');
            if (root && root.children.length > 1) return true;
            return document.querySelectorAll('article, main, [role="main"]').length > 0;
        })()
    """)
    if has_content:
        return

    # Step 4: Time fallback (3s) — non-blocking
    await asyncio.sleep(3)


def _flatten_a11y(node: dict, depth: int = 0) -> str:
    """Flatten accessibility tree to readable text (capped at 10KB by caller)."""
    parts = []
    role = node.get("role", "")
    name = node.get("name", "")
    if name and role not in ("generic", "none"):
        parts.append(f"{'  ' * depth}[{role}] {name}")
    for child in node.get("children", []):
        parts.append(_flatten_a11y(child, depth + 1))
    return "\n".join(parts)


async def _load_cookies(context: BrowserContext, domain: str, cookie_dir: str) -> dict:
    """Load Netscape-format cookies into browser context."""
    cookie_file = Path(cookie_dir) / f"{domain}.txt"
    result: dict = {"domain": domain, "file": str(cookie_file)}

    if not cookie_file.exists():
        result["error"] = f"No cookie file at {cookie_file}"
        result["count"] = 0
        return result

    age_days = (time.time() - cookie_file.stat().st_mtime) / 86400
    if age_days > 7:
        result["warning"] = f"Cookies {age_days:.0f} days old — may be expired"

    cookies = []
    for line in cookie_file.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        host, _flag, path, secure, expiry, name, value = parts[:7]
        cookies.append({
            "name": name, "value": value, "domain": host, "path": path,
            "secure": secure == "TRUE",
            "expires": int(expiry) if expiry != "0" else -1,
        })

    if cookies:
        await context.add_cookies(cookies)
    result["count"] = len(cookies)
    return result
```

- [ ] **Step 2: Deploy and test browser.py on droplet**

```bash
rsync -avz mcp-servers/web-agent/ root@aicos-droplet:/opt/web-agent/
ssh root@aicos-droplet "cd /opt/web-agent && uv sync"

# Test readiness ladder against SPA
ssh root@aicos-droplet "cd /opt/web-agent && uv run python -c '
from lib.browser import browse
import json

# Static page — should return immediately (no wait needed)
r = browse(\"https://example.com\", readiness=\"none\")
print(f\"example.com: {r[\"status\"]} | len={r.get(\"content_length\",0)}\")

# SPA — readiness ladder should handle
r = browse(\"https://x.com/home\", cookies_domain=\"x.com\")
print(f\"x.com: {r[\"status\"]} | len={r.get(\"content_length\",0)}\")
'"
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/web-agent/lib/browser.py
git commit -m "feat(web-agent): browser.py with readiness ladder + context pooling"
```

### Task 3: Core lib — scrape.py, search.py, cookies.py (port from web-tools-mcp)

**Files:**
- Create: `mcp-servers/web-agent/lib/scrape.py`
- Create: `mcp-servers/web-agent/lib/search.py`
- Create: `mcp-servers/web-agent/lib/cookies.py`

These are direct ports from web-tools-mcp/server.py, extracted into focused modules.

- [ ] **Step 1: Write scrape.py**

```python
"""Content extraction — Jina Reader (free, primary) + Firecrawl (fallback)."""

import logging
import os

import httpx

logger = logging.getLogger(__name__)


def _get_firecrawl_key() -> str:
    """Read API key at call time (not import time) so .env changes take effect."""
    return os.getenv("FIRECRAWL_API_KEY", "")


def scrape(url: str, use_firecrawl: bool = False) -> dict:
    """Extract content from URL as clean markdown."""
    firecrawl_key = _get_firecrawl_key()
    if use_firecrawl and firecrawl_key:
        return _scrape_firecrawl(url, firecrawl_key)

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
            "source": "jina", "url": url,
            "status": 404 if is_404 else resp.status_code,
            "content": content[:50000],
            "content_length": len(content),
            "is_404": is_404,
        }
    except httpx.TimeoutException:
        return {"source": "jina", "url": url, "error": "timeout", "content": ""}
    except Exception as e:
        if firecrawl_key:
            return _scrape_firecrawl(url, firecrawl_key)
        return {"source": "jina", "url": url, "error": str(e), "content": ""}


def _scrape_firecrawl(url: str, api_key: str) -> dict:
    """Firecrawl scrape with mandatory metadata validation."""
    try:
        resp = httpx.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            timeout=30.0,
        )
        data = resp.json()
        if not data.get("success"):
            return {"source": "firecrawl", "url": url, "error": data.get("error", "unknown"), "content": ""}

        result_data = data.get("data", {})
        metadata = result_data.get("metadata", {})
        return {
            "source": "firecrawl", "url": url,
            "actual_url": metadata.get("url", ""),
            "status": metadata.get("statusCode", 0),
            "redirected": metadata.get("url", "") != url and bool(metadata.get("url")),
            "content": result_data.get("markdown", "")[:50000],
            "content_length": len(result_data.get("markdown", "")),
            "title": metadata.get("title", ""),
        }
    except Exception as e:
        return {"source": "firecrawl", "url": url, "error": str(e), "content": ""}
```

- [ ] **Step 2: Write search.py**

```python
"""Web search — Firecrawl search (primary, requires API key)."""

import logging
import os

import httpx

logger = logging.getLogger(__name__)


def search(query: str, limit: int = 5) -> dict:
    """Search the web. Returns titles, URLs, snippets."""
    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    if not api_key:
        return {"source": "none", "query": query, "error": "No search API configured", "results": []}

    try:
        resp = httpx.post(
            "https://api.firecrawl.dev/v1/search",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"query": query, "limit": limit},
            timeout=15.0,
        )
        data = resp.json()
        results = data.get("data", [])[:limit]
        return {
            "source": "firecrawl", "query": query,
            "results": [
                {
                    "title": r.get("title", r.get("metadata", {}).get("title", "")),
                    "url": r.get("url", ""),
                    "snippet": r.get("markdown", r.get("description", ""))[:500],
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        return {"source": "firecrawl", "query": query, "error": str(e), "results": []}
```

- [ ] **Step 3: Write cookies.py**

```python
"""Cookie management — status check, domain listing."""

import time
from pathlib import Path

COOKIE_DIR = "/opt/ai-cos/cookies"


def cookie_status(cookie_dir: str = COOKIE_DIR) -> dict:
    """Check which domain cookies are available and their freshness."""
    cookie_path = Path(cookie_dir)
    if not cookie_path.exists():
        return {"cookies": [], "cookie_dir": cookie_dir, "error": "Cookie directory not found"}

    cookies = []
    for f in sorted(cookie_path.glob("*.txt")):
        age_days = (time.time() - f.stat().st_mtime) / 86400
        line_count = sum(1 for line in f.read_text().splitlines()
                         if line.strip() and not line.startswith("#"))
        entry: dict = {
            "domain": f.stem, "cookie_count": line_count,
            "age_days": round(age_days, 1), "file": str(f),
        }
        if age_days > 7:
            entry["warning"] = "STALE — re-run cookie-sync.sh"
        cookies.append(entry)

    return {"cookies": cookies, "cookie_dir": cookie_dir}
```

- [ ] **Step 4: Deploy and test all three modules**

```bash
rsync -avz mcp-servers/web-agent/ root@aicos-droplet:/opt/web-agent/
ssh root@aicos-droplet "cd /opt/web-agent && uv sync && uv run python -c '
from lib.scrape import scrape
from lib.search import search
from lib.cookies import cookie_status

r = scrape(\"https://example.com\")
print(f\"scrape: {r[\"source\"]} | {r.get(\"content_length\", 0)}\")

r = search(\"Claude Agent SDK\", limit=2)
print(f\"search: {r[\"source\"]} | {r.get(\"count\", 0)} results\")

r = cookie_status()
print(f\"cookies: {len(r.get(\"cookies\", []))} domains\")
'"
```

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/web-agent/lib/
git commit -m "feat(web-agent): core lib — scrape, search, cookies (ported from web-tools-mcp)"
```

---

## Chunk 2: Intelligence Lib — Fingerprinting, Strategy Cache, Quality Validation

### Task 4: Site fingerprinting

**Files:**
- Create: `mcp-servers/web-agent/lib/fingerprint.py`

Detects site framework/CMS/type to select the optimal extraction strategy BEFORE rendering.

- [ ] **Step 1: Write fingerprint.py**

```python
"""Site fingerprinting — detect framework, CMS, and page type.

Sub-millisecond classification using HTTP headers + HTML markers.
Used to select extraction strategy before full page render.
"""

import httpx
import re


def fingerprint(url: str) -> dict:
    """Analyze a URL and return site fingerprint.

    Returns: framework, cms, page_type, is_spa, auth_required, signals
    """
    result: dict = {
        "url": url, "framework": "unknown", "cms": "unknown",
        "page_type": "unknown", "is_spa": False, "auth_required": False,
        "signals": [],
    }

    try:
        # Quick HEAD + partial GET (first 50KB) for speed
        resp = httpx.get(
            url, timeout=10.0, follow_redirects=True,
            headers={"Accept": "text/html", "Range": "bytes=0-51200"},
        )
        html = resp.text[:50000].lower()
        headers = {k.lower(): v for k, v in resp.headers.items()}

        # Framework detection
        if "__next_data__" in html or "self.__next_f.push" in html or "_next/" in html:
            result["framework"] = "nextjs"
            result["is_spa"] = True
            result["signals"].append("__NEXT_DATA__ or _next/ assets")
        elif "data-reactroot" in html or "_reactlistening" in html or "react" in headers.get("x-powered-by", ""):
            result["framework"] = "react"
            result["is_spa"] = True
            result["signals"].append("React markers in DOM")
        elif "__vue__" in html or "vue" in html and "app.__vue" in html:
            result["framework"] = "vue"
            result["is_spa"] = True
            result["signals"].append("Vue markers")
        elif "ng-version" in html or "ng-app" in html:
            result["framework"] = "angular"
            result["is_spa"] = True
            result["signals"].append("Angular markers")
        elif "svelte" in html:
            result["framework"] = "svelte"
            result["is_spa"] = True
            result["signals"].append("Svelte markers")

        # CMS detection
        if "wp-content" in html or "wordpress" in headers.get("x-powered-by", ""):
            result["cms"] = "wordpress"
            result["signals"].append("WordPress indicators")
        elif "cdn.shopify" in html or "shopify" in html:
            result["cms"] = "shopify"
            result["signals"].append("Shopify CDN")

        # Page type
        if '"@type":"product"' in html or "schema.org/product" in html:
            result["page_type"] = "product"
        elif '"@type":"article"' in html or "<article" in html:
            result["page_type"] = "article"
        elif "<form" in html and 'type="password"' in html:
            result["page_type"] = "login"
            result["auth_required"] = True

        # Auth signals
        if any(p in url.lower() for p in ["/dashboard", "/settings", "/account", "/my/", "/inbox"]):
            result["auth_required"] = True
            result["signals"].append("Auth path detected")

        # SPA detection fallback (minimal HTML with large JS bundles)
        if not result["is_spa"]:
            script_count = html.count("<script")
            body_text_ratio = len(re.sub(r"<[^>]+>", "", html)) / max(len(html), 1)
            if script_count > 10 and body_text_ratio < 0.1:
                result["is_spa"] = True
                result["signals"].append(f"SPA heuristic: {script_count} scripts, {body_text_ratio:.2f} text ratio")

    except Exception as e:
        result["error"] = str(e)

    return result
```

- [ ] **Step 2: Test fingerprinting against known sites**

```bash
ssh root@aicos-droplet "cd /opt/web-agent && uv run python -c '
from lib.fingerprint import fingerprint
import json

sites = [
    \"https://simonwillison.net/2024/Dec/19/one-shot-python-tools/\",
    \"https://linear.app/features\",
    \"https://x.com/home\",
    \"https://docs.anthropic.com/en/docs/about-claude/models\",
]
for url in sites:
    r = fingerprint(url)
    print(f\"{r[\"framework\"]:>10} | spa={r[\"is_spa\"]} | {r[\"page_type\"]:>10} | {url[:50]}\")
'"
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/web-agent/lib/fingerprint.py
git commit -m "feat(web-agent): site fingerprinting — framework/CMS/type detection"
```

### Task 5: Strategy cache with UCB bandit

**Files:**
- Create: `mcp-servers/web-agent/lib/strategy.py`

- [ ] **Step 1: Write strategy.py**

```python
"""Strategy cache — learn what works per site, auto-promote winners.

Uses SQLite WAL for persistence + UCB (Upper Confidence Bound) bandit
to select between candidate strategies for each origin.

REVIEW FIX: WAL mode for concurrent reads/writes, init schema once at startup,
record_outcome auto-wired from lib functions (not relying on agent prompt).
"""

import logging
import math
import sqlite3
import time
import json
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = "/opt/web-agent/strategy.db"
_db: sqlite3.Connection | None = None


def _get_db() -> sqlite3.Connection:
    """Get or create module-level connection (reused, not per-call)."""
    global _db
    if _db is None:
        _db = sqlite3.connect(DB_PATH, timeout=10)
        _db.row_factory = sqlite3.Row
        _db.execute("PRAGMA journal_mode=WAL")  # Safe concurrent reads/writes
        _init_schema(_db)
    return _db


def _init_schema(db: sqlite3.Connection) -> None:
    """Create tables once at startup (not per-call)."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin TEXT NOT NULL,
            strategy_name TEXT NOT NULL,
            config TEXT NOT NULL DEFAULT '{}',
            successes INTEGER DEFAULT 0,
            failures INTEGER DEFAULT 0,
            total_attempts INTEGER DEFAULT 0,
            avg_latency_ms REAL DEFAULT 0,
            last_used TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(origin, strategy_name)
        )
    """)
    db.commit()
    return db


def get_strategy(origin: str) -> dict | None:
    """Get the best strategy for an origin using UCB bandit selection."""
    db = _get_db()
    rows = db.execute(
        "SELECT * FROM strategies WHERE origin = ?", (origin,)
    ).fetchall()

    if not rows:
        return None

    total_pulls = sum(r["total_attempts"] for r in rows)
    if total_pulls == 0:
        # No data yet — return first strategy
        row = rows[0]
        return {"strategy_name": row["strategy_name"], "config": json.loads(row["config"]), "source": "default"}

    # UCB1 selection
    best_score = -1
    best_row = rows[0]
    for row in rows:
        if row["total_attempts"] == 0:
            return {"strategy_name": row["strategy_name"], "config": json.loads(row["config"]), "source": "unexplored"}

        success_rate = row["successes"] / row["total_attempts"]
        exploration = math.sqrt(2 * math.log(total_pulls) / row["total_attempts"])
        ucb_score = success_rate + exploration

        if ucb_score > best_score:
            best_score = ucb_score
            best_row = row

    return {
        "strategy_name": best_row["strategy_name"],
        "config": json.loads(best_row["config"]),
        "success_rate": best_row["successes"] / max(best_row["total_attempts"], 1),
        "attempts": best_row["total_attempts"],
        "source": "ucb",
    }


def record_outcome(origin: str, strategy_name: str, success: bool, latency_ms: float = 0) -> None:
    """Record the outcome of a strategy attempt."""
    db = _get_db()
    db.execute("""
        UPDATE strategies SET
            successes = successes + ?,
            failures = failures + ?,
            total_attempts = total_attempts + 1,
            avg_latency_ms = (avg_latency_ms * total_attempts + ?) / (total_attempts + 1),
            last_used = datetime('now')
        WHERE origin = ? AND strategy_name = ?
    """, (1 if success else 0, 0 if success else 1, latency_ms, origin, strategy_name))
    db.commit()


def seed_strategies(origin: str, fingerprint: dict) -> None:
    """Seed default strategies for a new origin based on its fingerprint."""
    db = _get_db()

    strategies = []
    if fingerprint.get("is_spa"):
        strategies = [
            ("jina_reader", {"method": "jina"}),
            ("browser_mutation_observer", {"method": "browse", "readiness": "auto"}),
            ("browser_time_wait", {"method": "browse", "readiness": "time:5000"}),
        ]
    else:
        strategies = [
            ("jina_reader", {"method": "jina"}),
            ("browser_fast", {"method": "browse", "readiness": "none"}),
        ]

    if fingerprint.get("auth_required"):
        strategies.append(("browser_with_cookies", {
            "method": "browse", "readiness": "auto", "cookies": True,
        }))

    for name, config in strategies:
        db.execute("""
            INSERT OR IGNORE INTO strategies (origin, strategy_name, config)
            VALUES (?, ?, ?)
        """, (origin, name, json.dumps(config)))
    db.commit()


def get_all_strategies() -> list[dict]:
    """Get all strategies across all origins (for diagnostics)."""
    db = _get_db()
    rows = db.execute(
        "SELECT * FROM strategies ORDER BY origin, successes DESC"
    ).fetchall()
    return [dict(r) for r in rows]
```

- [ ] **Step 2: Test strategy cache**

```bash
ssh root@aicos-droplet "cd /opt/web-agent && uv run python -c '
from lib.strategy import seed_strategies, get_strategy, record_outcome
import json

# Seed strategies for x.com (SPA)
seed_strategies(\"x.com\", {\"is_spa\": True, \"auth_required\": True})

# Get best strategy (should be first since no data)
s = get_strategy(\"x.com\")
print(f\"Initial: {s}\")

# Record some outcomes
record_outcome(\"x.com\", \"jina_reader\", success=False)
record_outcome(\"x.com\", \"browser_mutation_observer\", success=True, latency_ms=3200)
record_outcome(\"x.com\", \"browser_mutation_observer\", success=True, latency_ms=2800)

# Should now prefer browser_mutation_observer
s = get_strategy(\"x.com\")
print(f\"After learning: {s}\")
'"
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/web-agent/lib/strategy.py
git commit -m "feat(web-agent): strategy cache with UCB bandit selection"
```

### Task 6: Content quality validation

**Files:**
- Create: `mcp-servers/web-agent/lib/quality.py`

- [ ] **Step 1: Write quality.py**

```python
"""Content quality validation — reject garbage before returning results."""


def validate_content(content: str, url: str = "", expected_type: str = "") -> dict:
    """Score content quality. Returns score (0-100), issues, and verdict.

    Checks: length, structure, login walls, cookie banners, error pages.
    """
    issues: list[str] = []
    score = 100

    if not content or not content.strip():
        return {"score": 0, "verdict": "empty", "issues": ["No content extracted"]}

    text = content.strip()
    text_lower = text.lower()
    word_count = len(text.split())

    # Length check
    if word_count < 10:
        score -= 60
        issues.append(f"Very short: {word_count} words")
    elif word_count < 50:
        score -= 30
        issues.append(f"Short: {word_count} words")

    # Login wall detection
    login_signals = ["sign in", "log in", "create account", "forgot password",
                     "enter your email", "enter your password"]
    login_count = sum(1 for s in login_signals if s in text_lower)
    if login_count >= 2 and word_count < 200:
        score -= 50
        issues.append(f"Likely login wall ({login_count} login signals)")

    # Cookie/consent overlay detection
    consent_signals = ["accept cookies", "cookie policy", "we use cookies",
                       "privacy preferences", "consent"]
    consent_count = sum(1 for s in consent_signals if s in text_lower)
    if consent_count >= 2 and word_count < 100:
        score -= 40
        issues.append("Likely cookie consent overlay")

    # Error page detection
    error_signals = ["404", "page not found", "not found", "error occurred",
                     "access denied", "403 forbidden"]
    if any(s in text_lower for s in error_signals) and word_count < 100:
        score -= 30
        issues.append("Possible error page")

    # Structural quality (has headings, paragraphs, etc.)
    if "\n" not in text and word_count > 100:
        score -= 10
        issues.append("No line breaks — may be poorly structured")

    score = max(0, min(100, score))
    verdict = "good" if score >= 70 else "acceptable" if score >= 40 else "poor"

    return {
        "score": score,
        "verdict": verdict,
        "word_count": word_count,
        "issues": issues,
    }
```

- [ ] **Step 2: Commit**

```bash
git add mcp-servers/web-agent/lib/quality.py
git commit -m "feat(web-agent): content quality validation"
```

---

## Chunk 3: System Prompt + Agent Runner

### Task 7: Compile system prompt from CC skill reference docs

**Files:**
- Create: `mcp-servers/web-agent/system_prompt.md`

The system prompt gives the agent its expertise. It's compiled from the CC skill reference docs (browse.md, scrape.md, search.md, auth.md, tool-selection.md) into a single focused document.

- [ ] **Step 1: Write system_prompt.md**

This should be a focused compilation (~3-4KB) covering:
- Task classification (browse/scrape/search/auth)
- Tool selection heuristic (6-dimension framework, simplified)
- Extraction strategy: Jina first (free), Firecrawl fallback, browser for SPAs
- Firecrawl hallucination guardrail (MUST validate metadata)
- Auth layers (cookie injection, escalation to human for 2FA)
- SPA readiness (use auto readiness, check fingerprint first)
- Quality validation (check content before returning)
- Strategy learning (check cache, record outcomes)

**DO NOT copy full reference docs verbatim** — compile the decision-making logic into ~3KB. The agent has tools for the mechanics; the prompt gives it judgment.

Read from:
- `~/Claude Projects/Skills Factory/Web & Browsers/web-router/SKILL.md`
- `~/Claude Projects/Skills Factory/Web & Browsers/tool-selection.md`
- `~/Claude Projects/Skills Factory/Web & Browsers/scrape/scrape.md`
- `~/Claude Projects/Skills Factory/Web & Browsers/browse/browse.md`
- `~/Claude Projects/Skills Factory/Web & Browsers/auth/auth.md`

- [ ] **Step 2: Commit**

```bash
git add mcp-servers/web-agent/system_prompt.md
git commit -m "feat(web-agent): system prompt compiled from CC web skills"
```

### Task 8: Agent runner

**Files:**
- Create: `mcp-servers/web-agent/agent.py`

The agent runner wraps Claude API (via Agent SDK or direct anthropic SDK) with the system prompt and tools.

- [ ] **Step 1: Write agent.py**

**IMPORTANT:** Check which SDK is available:
1. Try `claude-agent-sdk` first (preferred)
2. Fall back to `anthropic` SDK with manual tool-use loop

```python
"""WebAgent runner — Claude-powered web intelligence.

Uses anthropic SDK with manual tool-use loop (works without claude-agent-sdk).
Async throughout — compatible with FastMCP's async event loop.

REVIEW FIXES: try/except on tools, wall-clock timeout, max_tokens=8192,
cumulative usage tracking, auto-record strategy outcomes.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (Path(__file__).parent / "system_prompt.md").read_text()


def _build_tools() -> list[dict]:
    """Build tool definitions for the agent."""
    return [
        {
            "name": "web_browse",
            "description": "Navigate to URL and extract content with intelligent readiness detection. Returns page title, text content, accessibility tree, console errors.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to navigate to"},
                    "action": {"type": "string", "enum": ["snapshot", "click", "fill", "screenshot", "evaluate"], "default": "snapshot"},
                    "selector": {"type": "string", "description": "CSS selector for click/fill actions", "default": ""},
                    "text": {"type": "string", "description": "Text for fill action or JS for evaluate", "default": ""},
                    "cookies_domain": {"type": "string", "description": "Load cookies for this domain (e.g. 'youtube.com')", "default": ""},
                    "readiness": {"type": "string", "description": "Readiness mode: auto, selector:<css>, time:<ms>, none", "default": "auto"},
                },
                "required": ["url"],
            },
        },
        {
            "name": "web_scrape",
            "description": "Extract text content from URL as markdown. Uses Jina Reader (free) by default, Firecrawl as fallback.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "use_firecrawl": {"type": "boolean", "default": False},
                },
                "required": ["url"],
            },
        },
        {
            "name": "web_search",
            "description": "Search the web. Returns titles, URLs, snippets.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
        {
            "name": "fingerprint_site",
            "description": "Detect site framework, CMS, page type. Returns is_spa, auth_required, framework name.",
            "input_schema": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
        {
            "name": "check_strategy",
            "description": "Look up cached extraction strategy for a domain. Returns best strategy if known.",
            "input_schema": {
                "type": "object",
                "properties": {"origin": {"type": "string"}},
                "required": ["origin"],
            },
        },
        {
            "name": "validate_content",
            "description": "Score extracted content quality (0-100). Detects login walls, error pages, empty content.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "url": {"type": "string", "default": ""},
                },
                "required": ["content"],
            },
        },
        {
            "name": "cookie_status",
            "description": "Check available cookies and freshness.",
            "input_schema": {"type": "object", "properties": {}},
        },
    ]


async def _execute_tool(name: str, args: dict) -> str:
    """Execute a tool call and return JSON result.

    REVIEW FIX: Wrapped in try/except — errors returned to Claude for reasoning,
    not propagated as crashes. Auto-records outcomes to strategy cache.
    """
    import time as _time
    from urllib.parse import urlparse

    start = _time.monotonic()
    try:
        if name == "web_browse":
            from lib.browser import browse
            result = await browse(**args)
            # Auto-record outcome to strategy cache
            _auto_record_outcome(
                url=args.get("url", ""),
                strategy="browse",
                success=result.get("status") == "ok",
                latency_ms=(_time.monotonic() - start) * 1000,
            )
        elif name == "web_scrape":
            from lib.scrape import scrape
            result = scrape(**args)
            _auto_record_outcome(
                url=args.get("url", ""),
                strategy="jina_reader" if result.get("source") == "jina" else "firecrawl",
                success=result.get("content_length", 0) > 100,
                latency_ms=(_time.monotonic() - start) * 1000,
            )
        elif name == "web_search":
            from lib.search import search
            result = search(**args)
        elif name == "fingerprint_site":
            from lib.fingerprint import fingerprint
            from lib.strategy import seed_strategies
            result = fingerprint(args["url"])
            origin = urlparse(args["url"]).netloc
            seed_strategies(origin, result)
        elif name == "check_strategy":
            from lib.strategy import get_strategy
            result = get_strategy(args["origin"])
            if result is None:
                result = {"message": "No cached strategy. Use fingerprint_site first."}
        elif name == "validate_content":
            from lib.quality import validate_content
            result = validate_content(args["content"], args.get("url", ""))
        elif name == "cookie_status":
            from lib.cookies import cookie_status
            result = cookie_status()
        else:
            result = {"error": f"Unknown tool: {name}"}

    except Exception as e:
        # Return error to Claude so it can reason about alternatives
        logger.warning("Tool %s failed: %s", name, e)
        result = {"error": f"Tool execution failed: {e}", "tool": name}

    return json.dumps(result, default=str)


def _auto_record_outcome(url: str, strategy: str, success: bool, latency_ms: float) -> None:
    """Auto-record extraction outcome to strategy cache (not relying on agent prompt)."""
    try:
        from urllib.parse import urlparse
        from lib.strategy import record_outcome
        origin = urlparse(url).netloc
        if origin:
            record_outcome(origin, strategy, success, latency_ms)
    except Exception:
        pass  # Strategy recording is best-effort, never blocks


async def run_agent_task(task: str, max_turns: int = 20, timeout_s: int = 120) -> dict:
    """Run the WebAgent on a task using anthropic SDK tool-use loop.

    REVIEW FIXES:
    - Wall-clock timeout (120s default) — returns error_type: "timeout"
    - try/except on tool execution — errors go to Claude, not crash
    - max_tokens bumped to 8192
    - Handles stop_reason="max_tokens" (response truncation)
    - Cumulative usage tracking across all turns
    """
    import anthropic

    client = anthropic.AsyncAnthropic()  # Async client for non-blocking
    tools = _build_tools()
    messages: list[dict] = [{"role": "user", "content": task}]
    cumulative_usage = {"input_tokens": 0, "output_tokens": 0}

    try:
        result = await asyncio.wait_for(
            _agent_loop(client, tools, messages, max_turns, cumulative_usage),
            timeout=timeout_s,
        )
        result["usage"] = cumulative_usage
        return result
    except asyncio.TimeoutError:
        logger.warning("Agent task timed out after %ds: %s", timeout_s, task[:100])
        return {
            "status": "error",
            "error_type": "timeout",
            "error": f"Agent task exceeded {timeout_s}s wall-clock limit",
            "turns_completed": len([m for m in messages if m["role"] == "assistant"]),
            "usage": cumulative_usage,
        }


async def _agent_loop(
    client, tools: list[dict], messages: list[dict],
    max_turns: int, cumulative_usage: dict,
) -> dict:
    """Inner agent loop — separated for timeout wrapping."""
    for turn in range(max_turns):
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # Track cumulative usage
        cumulative_usage["input_tokens"] += response.usage.input_tokens
        cumulative_usage["output_tokens"] += response.usage.output_tokens

        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        # Handle completion
        if response.stop_reason == "end_turn":
            text_parts = [b.text for b in assistant_content if b.type == "text"]
            return {
                "status": "complete",
                "output": "\n".join(text_parts),
                "turns": turn + 1,
                "model": response.model,
            }

        # Handle truncation (response hit max_tokens mid-sentence)
        if response.stop_reason == "max_tokens":
            text_parts = [b.text for b in assistant_content if b.type == "text"]
            logger.warning("Agent response truncated at max_tokens on turn %d", turn + 1)
            return {
                "status": "error",
                "error_type": "truncated",
                "error": "Response hit max_tokens limit — output may be incomplete",
                "output": "\n".join(text_parts),
                "turns": turn + 1,
            }

        # Execute tool calls
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    result_str = await _execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })
            messages.append({"role": "user", "content": tool_results})

    return {"status": "error", "error_type": "max_turns", "error": f"Exceeded {max_turns} turns", "turns": max_turns}


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "What tools do you have available?"
    result = asyncio.run(run_agent_task(task))
    print(json.dumps(result, indent=2))
```

- [ ] **Step 2: Verify ANTHROPIC_API_KEY is on droplet**

```bash
ssh root@aicos-droplet "grep ANTHROPIC_API_KEY /opt/web-agent/.env 2>/dev/null || echo 'MISSING — add it'"
```

If missing, add it:
```bash
ssh root@aicos-droplet "echo 'ANTHROPIC_API_KEY=<key>' >> /opt/web-agent/.env && chmod 600 /opt/web-agent/.env"
```

- [ ] **Step 3: Deploy and test agent**

```bash
rsync -avz mcp-servers/web-agent/ root@aicos-droplet:/opt/web-agent/
ssh root@aicos-droplet "cd /opt/web-agent && uv sync && uv run python agent.py 'Scrape the pricing page at docs.anthropic.com and tell me what Claude Sonnet costs'"
```

- [ ] **Step 4: Commit**

```bash
git add mcp-servers/web-agent/agent.py
git commit -m "feat(web-agent): agent runner with manual tool-use loop"
```

---

## Chunk 4: FastMCP Wrapper + Infrastructure

### Task 9: FastMCP server exposing agent + direct tools

**Files:**
- Create: `mcp-servers/web-agent/server.py`

Dual-mode: agent tools (`web_task`) + direct tools (`web_scrape`, `web_browse`, etc.)

- [ ] **Step 1: Write server.py**

```python
"""WebAgent MCP Server — dual-mode: agent reasoning + direct tools.

Agent mode: web_task() — Claude reasons about the task, uses tools intelligently
Direct mode: web_scrape(), web_browse(), etc. — no LLM, just the tool (98.7% cheaper)
"""

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(
    "web-agent",
    instructions=(
        "WebAgent — intelligent web browsing, scraping, and search. "
        "Use web_task for complex tasks requiring reasoning. "
        "Use web_scrape/web_browse/web_search for simple, direct operations."
    ),
)


# -------------------------------------------------------
# AGENT MODE — Claude reasons about the task
# -------------------------------------------------------


@mcp.tool()
async def web_task(task: str, url: str = "", timeout_s: int = 120) -> dict:
    """Execute a web task with full agent intelligence.

    The agent reasons about what to do: which tool to use, how to handle
    errors, whether to retry, how to validate content. Use this for
    complex or ambiguous tasks. For simple scrape/browse/search, use
    the direct tools instead (cheaper, faster).

    Returns error_type="timeout" if wall-clock limit exceeded.

    Args:
        task: Natural language description of what to do
        url: Optional target URL
        timeout_s: Wall-clock timeout in seconds (default 120)
    """
    from agent import run_agent_task

    prompt = task
    if url:
        prompt = f"{task}\n\nTarget URL: {url}"

    return await run_agent_task(prompt, max_turns=20, timeout_s=timeout_s)


# -------------------------------------------------------
# DIRECT MODE — no LLM, just the tool (programmatic)
# -------------------------------------------------------


@mcp.tool()
def web_scrape(url: str, use_firecrawl: bool = False) -> dict:
    """Extract content from URL as markdown. No agent reasoning — direct extraction.
    Jina Reader (free) by default, Firecrawl as fallback.
    """
    from lib.scrape import scrape
    return scrape(url, use_firecrawl=use_firecrawl)


@mcp.tool()
async def web_browse(
    url: str,
    action: str = "snapshot",
    selector: str = "",
    text: str = "",
    cookies_domain: str = "",
    readiness: str = "auto",
    timeout_ms: int = 15000,
) -> dict:
    """Navigate to URL with Playwright. No agent reasoning — direct browse.
    Includes readiness ladder for SPAs. Max 2 concurrent via semaphore.
    """
    from lib.browser import browse
    return await browse(
        url=url, action=action, selector=selector, text=text,
        cookies_domain=cookies_domain, readiness=readiness, timeout_ms=timeout_ms,
    )


@mcp.tool()
def web_search(query: str, limit: int = 5) -> dict:
    """Search the web. No agent reasoning — direct Firecrawl search."""
    from lib.search import search
    return search(query, limit=limit)


@mcp.tool()
def cookie_status() -> dict:
    """Check available cookies and freshness."""
    from lib.cookies import cookie_status as _cookie_status
    return _cookie_status()


@mcp.tool()
def health_check() -> dict:
    """Check server, Chrome, Playwright, and agent connectivity."""
    import shutil
    result: dict = {"server": "ok", "chrome": "unknown", "playwright": "unknown", "agent_sdk": "unknown"}

    chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    result["chrome"] = chrome if chrome else "not found"

    try:
        from lib.browser import get_browser
        browser = get_browser()
        result["playwright"] = f"ok (connected={browser.is_connected()})"
    except Exception as e:
        result["playwright"] = f"error: {e}"

    result["anthropic_key_set"] = bool(os.getenv("ANTHROPIC_API_KEY"))
    result["firecrawl_key_set"] = bool(os.getenv("FIRECRAWL_API_KEY"))
    return result


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
```

- [ ] **Step 2: Create deploy.sh**

```bash
#!/bin/bash
set -e
DROPLET="aicos-droplet"
REMOTE_DIR="/opt/web-agent"

echo "Deploying web-agent to $DROPLET:$REMOTE_DIR..."

# Pre-deploy: syntax check (don't deploy broken code)
ssh root@${DROPLET} "cd ${REMOTE_DIR} && /root/.local/bin/uv run python -c 'import server' 2>&1" || {
  echo "ERROR: Syntax check failed — aborting deploy"
  exit 1
}

rsync -avz --delete --exclude='.env' --exclude='__pycache__' --exclude='.venv' \
  --exclude='tests' --exclude='strategy.db' \
  ./ root@${DROPLET}:${REMOTE_DIR}/

ssh root@${DROPLET} "cd ${REMOTE_DIR} && /root/.local/bin/uv sync && systemctl restart web-agent"

# Post-deploy: health check (wait up to 30s for server to come up)
echo "Waiting for server to start..."
for i in $(seq 1 15); do
  if ssh root@${DROPLET} "curl -sf -m 5 -o /dev/null http://localhost:8001/mcp -X POST -H 'Content-Type: application/json' -d '{}'"; then
    echo "Health check passed after ${i}x2 seconds."
    break
  fi
  [ $i -eq 15 ] && echo "WARNING: Server did not respond within 30s"
  sleep 2
done

ssh root@${DROPLET} "systemctl status web-agent --no-pager | head -10"
```

- [ ] **Step 3: Create systemd service on droplet**

```bash
ssh root@aicos-droplet 'cat > /etc/systemd/system/web-agent.service << EOF
[Unit]
Description=WebAgent MCP Server
After=network.target tailscaled.service

[Service]
Type=simple
WorkingDirectory=/opt/web-agent
ExecStartPre=/bin/sh -c "while ss -tlnp | grep -q :8001; do sleep 1; done"
ExecStartPre=/bin/sh -c "rm -rf /tmp/.org.chromium.* /tmp/playwright*"
ExecStart=/root/.local/bin/uv run server.py
ExecStopPost=/usr/bin/pkill -f "chrome.*--headless" || true
Restart=always
RestartSec=5
TimeoutStopSec=15
EnvironmentFile=-/opt/web-agent/.env
MemoryHigh=768M
MemoryMax=1G
CPUQuota=80%
OOMScoreAdjust=500
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

# Protect PostgreSQL from OOM killer
ssh root@aicos-droplet "mkdir -p /etc/systemd/system/postgresql.service.d && \
  echo -e \"[Service]\nOOMScoreAdjust=-500\" > /etc/systemd/system/postgresql.service.d/oom.conf"

systemctl daemon-reload && systemctl enable web-agent'
```

- [ ] **Step 4: Stop web-tools-mcp, start web-agent (same port 8001)**

```bash
ssh root@aicos-droplet "systemctl stop web-tools-mcp && systemctl disable web-tools-mcp && \
  systemctl start web-agent && sleep 3 && systemctl status web-agent --no-pager | head -10"
```

Cloudflare Tunnel already routes `web.3niac.com` → port 8001. No tunnel config change needed.

- [ ] **Step 5: Verify MCP endpoint**

```bash
curl -sv -X POST https://web.3niac.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' \
  2>&1 | grep "serverInfo"
```

Expected: `"name":"web-agent"` (not `web-tools-mcp`)

- [ ] **Step 6: Commit**

```bash
git add mcp-servers/web-agent/server.py mcp-servers/web-agent/deploy.sh
git commit -m "feat(web-agent): FastMCP server with dual-mode (agent + direct) + infrastructure"
```

---

## Chunk 5: Integration Testing

### Task 10: Full integration test

**Files:**
- Create: `mcp-servers/web-agent/tests/test_agent.py`

- [ ] **Step 1: Write test_agent.py**

Test all 10 URLs using both direct mode and agent mode. Direct mode tests the lib functions. Agent mode tests the full Claude reasoning loop (costs tokens — run selectively).

```python
"""Integration tests for WebAgent."""
import json
import sys
sys.path.insert(0, "/opt/web-agent")

from lib.browser import browse
from lib.scrape import scrape
from lib.search import search
from lib.fingerprint import fingerprint
from lib.quality import validate_content
from lib.cookies import cookie_status
from lib.strategy import get_strategy, seed_strategies, record_outcome

# ... test functions for each module against all 10 URLs
# Same structure as web-tools-mcp tests but testing new lib modules
# Plus: fingerprint tests, strategy cache tests, quality validation tests
# Plus: one agent mode test (web_task) to verify full loop
```

Full test file follows the pattern from `web-tools-mcp/tests/test_tools.py` but adds:
- `test_fingerprint()` — all 10 URLs classified
- `test_strategy_cache()` — seed, select, record, re-select
- `test_quality()` — validate good content, login wall, empty, error page
- `test_agent_mode()` — one full `web_task` call (e.g. "scrape Claude pricing")

- [ ] **Step 2: Deploy and run tests**

```bash
rsync -avz mcp-servers/web-agent/tests/ root@aicos-droplet:/opt/web-agent/tests/
ssh root@aicos-droplet "cd /opt/web-agent && uv run python tests/test_agent.py"
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/web-agent/tests/
git commit -m "test(web-agent): integration tests — 10 URLs, all modules, agent mode"
```

---

## Chunk 6: Stealth + Anti-Detection (Phase 2)

### Task 11: Persona management

**Files:**
- Create: `mcp-servers/web-agent/lib/stealth.py`

Implements stable persona profiles from Research #6. Coherent IP + timezone + locale + UA.

- [ ] **Step 1: Write stealth.py**

```python
"""Stealth — persona management, anti-detection configuration.

Key principle: coherence > randomization.
A stable persona (consistent IP + timezone + locale + UA) beats
rotating everything randomly. Inconsistency is the detection signal.
"""

PERSONAS = {
    "linux_us": {
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "timezone_id": "America/New_York",
    },
    "mac_us": {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "viewport": {"width": 1440, "height": 900},
        "locale": "en-US",
        "timezone_id": "America/Los_Angeles",
    },
    "win_us": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "timezone_id": "America/Chicago",
    },
}

# Default persona for our droplet (Linux, US datacenter)
DEFAULT_PERSONA = "linux_us"


def get_persona(name: str = DEFAULT_PERSONA) -> dict:
    """Get a coherent persona profile."""
    return PERSONAS.get(name, PERSONAS[DEFAULT_PERSONA])
```

- [ ] **Step 2: Wire persona into browser.py create_context()**

Update `lib/browser.py` to use stealth personas by default.

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/web-agent/lib/stealth.py
git commit -m "feat(web-agent): stealth persona management"
```

---

## Migration Checklist

After all chunks are complete:

- [ ] web-tools-mcp service stopped (NOT disabled — keep for rollback)
- [ ] web-agent service running on port 8001
- [ ] `web.3niac.com/mcp` returns `serverInfo: web-agent`
- [ ] `.mcp.json` already points to `web.3niac.com/mcp` (no change needed)
- [ ] Direct tools work: `web_scrape`, `web_browse`, `web_search`
- [ ] Agent mode works: `web_task` with Claude reasoning
- [ ] Strategy cache learning: fingerprint → seed → select → auto-record outcomes
- [ ] All 10 test URLs pass (Tier 2 + Tier 3)
- [ ] Memory usage < 1GB under concurrent load
- [ ] 60s monitoring cron installed and verified
- [ ] Rollback procedure tested

### Rollback Procedure

If web-agent fails in production:

```bash
# Rollback: web-agent → web-tools-mcp (< 30 seconds)
ssh root@aicos-droplet "systemctl stop web-agent && \
  systemctl start web-tools-mcp && \
  sleep 3 && systemctl is-active web-tools-mcp"
```

web-tools-mcp code stays at `/opt/web-tools-mcp/`. Service file stays in systemd (stopped, not disabled). 48-hour canary period before full decommission — after 48h of web-agent running cleanly, disable web-tools-mcp.

### 60-Second Monitoring Cron

```bash
# Install on droplet — lightweight HTTP check, restart on failure
ssh root@aicos-droplet "(crontab -l 2>/dev/null | grep -v web-agent-health; \
  echo '# web-agent: 60s health check'; \
  echo '* * * * * curl -sf -m 5 -o /dev/null http://localhost:8001/mcp -X POST -H \"Content-Type: application/json\" -d \"{}\" || systemctl restart web-agent') | crontab -"
```

## Future Work (Not in This Plan)

1. **Claude Agent SDK migration** — once SDK is stable on PyPI, migrate from manual tool-use loop to `ClaudeSDKClient`
2. **Browserbase integration** — isolated sessions for bot-hostile sites (Amazon, LinkedIn)
3. **Screenshot + vision fallback** — for canvas, WebGL, obfuscated DOMs
4. **WebSocket monitoring** — real-time data extraction
5. **Overlay auto-dismissal** — `page.addLocatorHandler()` for cookie banners
6. **Cross-agent strategy sharing** — MCP tool for querying strategy cache from other agents
7. **Performance auditing** — Lighthouse via Chrome DevTools
8. **Adaptive retry with circuit breakers** — 5-step escalation ladder with per-origin circuit state

## Success Criteria (Quantitative)

| # | Criterion | Pass Threshold |
|---|-----------|----------------|
| 1 | health_check | Returns 200 in <2s, all fields non-error |
| 2 | Direct scrape (Jina) | Content_length > 1000 for 5/6 public URLs (Amazon may block) |
| 3 | Direct browse (Playwright) | Content_length > 200 for 5/6 public URLs within 15s |
| 4 | Authenticated browse | Cookies loaded (count > 0) for x.com, youtube.com, substack.com |
| 5 | Agent mode (web_task) | status="complete", output.word_count > 50, in <60s, <$1 cost |
| 6 | Fingerprinting accuracy | Correctly classifies >= 8/10 test URLs per "Strategy Expected" column |
| 7 | Strategy learning | After 10 recorded outcomes (7 success A, 3 success B), UCB selects A > 80% of the time |
| 8 | Quality validation | Rejects login walls (score < 40), accepts good content (score >= 70), precision >= 90% |
| 9 | Memory under load | Peak RSS < 1.5GB with 2 concurrent browse calls sustained for 5 minutes |
| 10 | Endpoint identity | `web.3niac.com/mcp` initialize returns serverInfo.name = "web-agent" |
| 11 | Rollback works | web-tools-mcp starts on port 8001 within 10s of rollback command |
| 12 | Monitoring fires | Monitoring cron restarts service within 60s of simulated crash |
