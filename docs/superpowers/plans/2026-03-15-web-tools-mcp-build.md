# Web Tools MCP Server — Build & Deploy Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy a standalone web-tools MCP server on the droplet, exposing browse/scrape/search tools to CC, CAI, and Agent SDK runners.

**Architecture:** FastMCP Python server (same pattern as ai-cos-mcp) running as a separate systemd service on port 8001. Uses system Google Chrome (already installed) via Playwright's `channel='chrome'`. Jina Reader (free, httpx) is the primary scraper; Firecrawl is the fallback. Exposed via Cloudflare Tunnel at `web.3niac.com/mcp`.

**Tech Stack:** Python 3.12+, FastMCP, Playwright (Python), httpx, Google Chrome 146 (system), uv

**Fault isolation decision (already made):** Separate server from ai-cos-mcp. Chrome crash must not kill Notion/calendar/thesis tools.

---

## File Structure

```
mcp-servers/web-tools-mcp/          # Local dev (git-tracked)
├── pyproject.toml                   # Dependencies
├── server.py                        # FastMCP server — all 4 tools
├── deploy.sh                        # rsync + systemd restart
└── tests/
    └── test_tools.py                # Integration tests against real URLs

/opt/web-tools-mcp/                  # Droplet (deployed)
├── (same as above, minus tests/)
├── .env                             # FIRECRAWL_API_KEY
└── cookies/                         # Cookie files (future)
```

**Server runs on port 8001** (ai-cos-mcp uses 8000).

## Test URLs

### Public URLs (from Phase 0 evaluation)

| # | Type | URL | Expected Behavior |
|---|------|-----|-------------------|
| 1 | Blog (text-heavy) | `https://simonwillison.net/2024/Dec/19/one-shot-python-tools/` | Clean markdown, full article |
| 2 | SaaS (image-heavy) | `https://linear.app/features` | Some text, lots of image URLs |
| 3 | E-commerce (bot-hostile) | `https://www.amazon.com/dp/B0DKHZTGQS` | Blocked/404 — graceful failure |
| 4 | Cloudflare-protected | `https://discord.com/safety` | Jina penetrates, returns content |
| 5 | Docs/reference | `https://docs.anthropic.com/en/docs/about-claude/models` | Clean markdown, model info |
| 6 | 404 page | `https://example.com/nonexistent-page-404` | Flagged as 404, no hallucination |

### Authenticated URLs (cookie-dependent — tested in Chunks 6-7)

| # | Type | URL | Auth Layer | Cookie Domain | Expected Behavior |
|---|------|-----|------------|---------------|-------------------|
| 7 | X/Twitter home | `https://x.com/home` | L2: Cookies | `.x.com` | Feed content visible with cookies; login wall without |
| 8 | X/Twitter bookmarks | `https://x.com/i/bookmarks` | L2: Cookies | `.x.com` | Saved bookmarks list; harder test — requires active session |
| 9 | LinkedIn activity | `https://www.linkedin.com/in/kumaraakash/recent-activity/all/` | **L4: Browserbase** | `.linkedin.com` | **DO NOT cookie-inject** — LinkedIn bans headless sessions. Test with Browserbase only (future). For now, test graceful failure without cookies. |
| 10 | Substack post | `https://substack.com/inbox/post/190905077` | L0/L2 | `.substack.com` | Public posts: Jina works. Paywalled: needs cookies. |

**LinkedIn warning:** Per auth service registry, LinkedIn is "extremely bot-hostile." Cookie injection from a headless Playwright session WILL trigger detection and risks account ban. This URL tests graceful degradation (login wall / redirect) without cookies, and is deferred to Browserbase integration for authenticated access.

---

## Chunk 1: Scaffolding + Health Check

### Task 1: Create project structure locally

**Files:**
- Create: `mcp-servers/web-tools-mcp/pyproject.toml`
- Create: `mcp-servers/web-tools-mcp/server.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "web-tools-mcp"
version = "0.1.0"
description = "Web Tools MCP Server — browse, scrape, search"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=2.0.0",
    "python-dotenv>=1.0",
    "playwright>=1.49",
    "httpx>=0.27",
]
```

- [ ] **Step 2: Create server.py with health_check tool**

```python
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


@mcp.tool()
def health_check() -> dict:
    """Check server, Chrome, and Playwright connectivity."""
    import shutil

    result = {"server": "ok", "chrome": "unknown", "playwright": "unknown"}

    # Check Chrome binary
    chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable") or CHROME_PATH
    result["chrome"] = chrome if chrome else "not found"

    # Check Playwright can launch Chrome
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome", headless=True,
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


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
```

- [ ] **Step 3: Deploy to droplet and test health_check**

```bash
# From mcp-servers/web-tools-mcp/
rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='.venv' --exclude='tests' \
  ./ root@aicos-droplet:/opt/web-tools-mcp/

# SSH and test
ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv sync && \
  /root/.local/bin/uv run python -c \"
from server import mcp
import json
from server import health_check
print(json.dumps(health_check(), indent=2))
\""
```

**Expected:** `{"server": "ok", "chrome": "/usr/bin/google-chrome", "playwright": "ok (loaded: Example Domain)", "firecrawl_configured": false}`

- [ ] **Step 4: Commit**

```bash
git add mcp-servers/web-tools-mcp/
git commit -m "feat: web-tools-mcp scaffold with health_check"
```

---

## Chunk 2: web_scrape Tool

### Task 2: Implement web_scrape (Jina Reader primary, Firecrawl fallback)

**Files:**
- Modify: `mcp-servers/web-tools-mcp/server.py`

The scrape tool follows the tiered extraction pattern:
1. **Jina Reader** (free, fastest, best CF penetration) — default
2. **Firecrawl** (1 credit, more detailed) — fallback if Jina fails
3. Returns clean markdown + metadata

- [ ] **Step 1: Add web_scrape tool to server.py**

```python
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
            "content": content[:50000],  # Cap at 50KB
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
            return {"source": "firecrawl", "url": url, "error": data.get("error", "unknown"), "content": ""}

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
```

- [ ] **Step 2: Deploy and test web_scrape against all 6 test URLs**

```bash
# Deploy
rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='.venv' --exclude='tests' \
  ./ root@aicos-droplet:/opt/web-tools-mcp/

# Test each URL via direct Python call on droplet
ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv run python -c \"
from server import web_scrape
import json

urls = [
    'https://simonwillison.net/2024/Dec/19/one-shot-python-tools/',
    'https://linear.app/features',
    'https://www.amazon.com/dp/B0DKHZTGQS',
    'https://discord.com/safety',
    'https://docs.anthropic.com/en/docs/about-claude/models',
    'https://example.com/nonexistent-page-404',
]

for url in urls:
    r = web_scrape(url)
    print(f'{r[\"status\"]} | {r[\"source\"]} | {r.get(\"content_length\",0):>6} | {r.get(\"is_404\",False)} | {url[:50]}')
    print()
\""
```

**Expected results:**

| URL | Source | Status | Content? | 404? |
|-----|--------|--------|----------|------|
| simonwillison.net | jina | 200 | ~7KB+ | No |
| linear.app/features | jina | 200 | Some content | No |
| amazon.com | jina | 200 or blocked | Minimal | Possibly |
| discord.com/safety | jina | 200 | ~14KB (CF penetrated) | No |
| docs.anthropic.com | jina | 200 | ~5KB+ | No |
| example.com/nonexistent | jina | 404 | Warning text | Yes |

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/web-tools-mcp/server.py
git commit -m "feat(web-tools-mcp): add web_scrape tool with Jina/Firecrawl cascade"
```

---

## Chunk 3: web_browse Tool

### Task 3: Implement web_browse (Playwright + system Chrome)

**Files:**
- Modify: `mcp-servers/web-tools-mcp/server.py`

Browse tool wraps Playwright to navigate, take snapshots, and interact with pages. Uses system Chrome (`channel='chrome'`, `headless=True` with new headless mode for better anti-detection).

- [ ] **Step 1: Add web_browse tool to server.py**

```python
@mcp.tool()
def web_browse(
    url: str,
    action: str = "snapshot",
    selector: str = "",
    text: str = "",
    cookies_domain: str = "",
    wait_for: str = "networkidle",
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
            (e.g. "youtube.com"). Enables authenticated browsing. Cookies are
            synced from the Mac via cookie-sync.sh.
        wait_for: Wait strategy — networkidle, domcontentloaded, load
        timeout_ms: Navigation timeout in milliseconds
    """
    from playwright.sync_api import sync_playwright

    result = {"url": url, "action": action}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome",
                headless=True,
                args=["--no-sandbox", "--disable-gpu", "--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
            )

            # Load cookies from Netscape file if domain specified
            if cookies_domain:
                cookies_loaded = _load_cookies(context, cookies_domain)
                result["cookies_loaded"] = cookies_loaded

            page = context.new_page()

            # Register console listener BEFORE navigation to capture load-time errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            page.goto(url, wait_until=wait_for, timeout=timeout_ms)

            result["title"] = page.title()
            result["final_url"] = page.url

            if action == "snapshot":
                # Get text content (trimmed)
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
                result["screenshot_base64"] = base64.b64encode(screenshot_bytes).decode()
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


COOKIE_DIR = os.getenv("COOKIE_DIR", "/opt/ai-cos/cookies")


def _load_cookies(context, domain: str) -> dict:
    """Load Netscape-format cookies into a Playwright browser context.

    Reads from COOKIE_DIR/<domain>.txt (synced from Mac via cookie-sync.sh).
    Returns dict with count loaded, file path, and staleness warning.
    """
    from pathlib import Path
    import time

    cookie_file = Path(COOKIE_DIR) / f"{domain}.txt"
    result = {"domain": domain, "file": str(cookie_file)}

    if not cookie_file.exists():
        result["error"] = f"No cookie file found at {cookie_file}"
        result["count"] = 0
        return result

    # Check staleness (warn if > 7 days old)
    age_days = (time.time() - cookie_file.stat().st_mtime) / 86400
    if age_days > 7:
        result["warning"] = f"Cookies are {age_days:.0f} days old — may be expired. Re-run cookie-sync.sh."

    cookies = []
    for line in cookie_file.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        host, _flag, path, secure, expiry, name, value = parts[:7]
        cookies.append({
            "name": name,
            "value": value,
            "domain": host,
            "path": path,
            "secure": secure == "TRUE",
            "expires": int(expiry) if expiry != "0" else -1,
        })

    if cookies:
        context.add_cookies(cookies)

    result["count"] = len(cookies)
    return result
```

- [ ] **Step 2: Deploy and test web_browse against test URLs**

```bash
rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='.venv' --exclude='tests' \
  ./ root@aicos-droplet:/opt/web-tools-mcp/

ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv run python -c \"
from server import web_browse
import json

urls = [
    'https://simonwillison.net/2024/Dec/19/one-shot-python-tools/',
    'https://linear.app/features',
    'https://discord.com/safety',
    'https://docs.anthropic.com/en/docs/about-claude/models',
    'https://example.com/nonexistent-page-404',
]

for url in urls:
    r = web_browse(url)
    status = r.get('status', 'unknown')
    title = r.get('title', '')[:40]
    length = r.get('content_length', 0)
    err = r.get('error', '')[:50]
    print(f'{status:>5} | {length:>6} | {title:40} | {err}')
\""
```

**Expected:** Each URL loads, returns title + text content. Discord/Linear may have less content due to JS rendering.

- [ ] **Step 3: Test browse interaction (fill + evaluate)**

```bash
ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv run python -c \"
from server import web_browse
import json

# Test evaluate — get performance timing from example.com
r = web_browse('https://example.com', action='evaluate', text='JSON.stringify({title: document.title, links: document.querySelectorAll(\"a\").length})')
print(json.dumps(r, indent=2))
\""
```

- [ ] **Step 4: Commit**

```bash
git add mcp-servers/web-tools-mcp/server.py
git commit -m "feat(web-tools-mcp): add web_browse tool with Playwright + system Chrome"
```

---

## Chunk 4: web_search Tool

### Task 4: Implement web_search

**Files:**
- Modify: `mcp-servers/web-tools-mcp/server.py`

Search tool routes queries. On the droplet (Agent SDK), the available engines are:
- Jina Reader with search prefix (free)
- Firecrawl search (if API key configured)

- [ ] **Step 1: Add web_search tool to server.py**

```python
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

    # Jina Search: https://s.jina.ai/<query>
    from urllib.parse import quote

    try:
        resp = httpx.get(
            f"https://s.jina.ai/{quote(query)}",
            headers={"Accept": "application/json", "X-Retain-Images": "none"},
            timeout=15.0,
            follow_redirects=True,
        )
        if resp.status_code == 200:
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            results = data.get("data", [])[:limit] if isinstance(data.get("data"), list) else []

            if results:
                return {
                    "source": "jina",
                    "query": query,
                    "results": [
                        {
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "snippet": r.get("description", r.get("content", ""))[:500],
                        }
                        for r in results
                    ],
                    "count": len(results),
                }

            # Jina returned no structured results — try plain text
            if resp.text.strip():
                return {
                    "source": "jina",
                    "query": query,
                    "results": [],
                    "raw_content": resp.text[:10000],
                    "count": 0,
                    "note": "Jina returned text, not structured results",
                }
    except Exception as e:
        pass  # Fall through to Firecrawl

    # Firecrawl search fallback
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

    return {"source": "none", "query": query, "error": "No search engines available", "results": []}
```

- [ ] **Step 2: Deploy and test web_search**

```bash
rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='.venv' --exclude='tests' \
  ./ root@aicos-droplet:/opt/web-tools-mcp/

ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv run python -c \"
from server import web_search
import json

queries = [
    'Claude Code MCP server setup',
    'best VC fund frameworks 2025',
    'Playwright headless detection bypass',
]

for q in queries:
    r = web_search(q, limit=3)
    print(f'Source: {r[\"source\"]} | Results: {r[\"count\"]} | Query: {q}')
    for res in r.get('results', [])[:2]:
        print(f'  - {res[\"title\"][:60]}')
    print()
\""
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/web-tools-mcp/server.py
git commit -m "feat(web-tools-mcp): add web_search tool with Jina/Firecrawl routing"
```

---

## Chunk 5: Infrastructure — systemd + Cloudflare Tunnel

### Task 5: Create deploy.sh and systemd service

**Files:**
- Create: `mcp-servers/web-tools-mcp/deploy.sh`

- [ ] **Step 1: Create deploy.sh**

```bash
#!/bin/bash
# Deploy web-tools-mcp to the DO droplet
set -e

DROPLET="aicos-droplet"
REMOTE_DIR="/opt/web-tools-mcp"

echo "Deploying web-tools-mcp to $DROPLET:$REMOTE_DIR..."

rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='.venv' --exclude='tests' \
  ./ root@${DROPLET}:${REMOTE_DIR}/

ssh root@${DROPLET} "cd ${REMOTE_DIR} && /root/.local/bin/uv sync && systemctl restart web-tools-mcp"

echo ""
echo "Deployed. Checking status..."
ssh root@${DROPLET} "systemctl status web-tools-mcp --no-pager | head -10"
```

- [ ] **Step 2: Create systemd service on droplet**

```bash
ssh root@aicos-droplet "cat > /etc/systemd/system/web-tools-mcp.service << 'EOF'
[Unit]
Description=Web Tools MCP Server
After=network.target tailscaled.service

[Service]
Type=simple
WorkingDirectory=/opt/web-tools-mcp
ExecStart=/root/.local/bin/uv run server.py
Restart=always
RestartSec=5
EnvironmentFile=/opt/web-tools-mcp/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable web-tools-mcp
systemctl start web-tools-mcp
systemctl status web-tools-mcp --no-pager | head -10"
```

- [ ] **Step 3: Create .env on droplet (paste key interactively — never commit)**

```bash
# SSH in and create .env manually — do NOT put the real key in any git-tracked file
ssh root@aicos-droplet
echo 'FIRECRAWL_API_KEY=<paste-key-here>' > /opt/web-tools-mcp/.env
chmod 600 /opt/web-tools-mcp/.env
exit
```

The Firecrawl API key is in the handoff doc (`web-tools-mcp-handoff.md`). Paste it directly on the droplet.

- [ ] **Step 4: Verify MCP server responds on port 8001**

```bash
ssh root@aicos-droplet "curl -s http://localhost:8001/mcp 2>&1 | head -5"
```

- [ ] **Step 5: Add web.3niac.com route to Cloudflare Tunnel**

**IMPORTANT:** Read the existing config first, then add the new ingress entry. Do NOT blindly overwrite.

```bash
# 1. Read current config
ssh root@aicos-droplet "cat /root/.cloudflared/config.yml"

# 2. Add the web.3niac.com entry BEFORE the catch-all 404 rule.
#    The catch-all (- service: http_status:404) must remain last.
#    Insert this new entry just above it:
#
#      - hostname: web.3niac.com
#        service: http://localhost:8001
#
#    Use a text editor on the droplet:
ssh root@aicos-droplet "micro /root/.cloudflared/config.yml"

# 3. Add DNS record for web.3niac.com (CNAME to tunnel)
ssh root@aicos-droplet "cloudflared tunnel route dns a381fcd4-b7fa-4226-8615-a77cfa498d09 web.3niac.com"

# 4. Restart tunnel
ssh root@aicos-droplet "systemctl restart cloudflared && sleep 3 && systemctl status cloudflared --no-pager | head -5"
```

**If `cloudflared tunnel route dns` fails:** create the DNS record manually in Cloudflare dashboard: `web.3niac.com` → CNAME → `a381fcd4-b7fa-4226-8615-a77cfa498d09.cfargotunnel.com` (proxied).

- [ ] **Step 6: Test external access**

```bash
# From Mac (not droplet)
curl -s https://web.3niac.com/mcp | head -5
```

- [ ] **Step 7: Add web-tools-mcp to .mcp.json in this project**

Add to `/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/.mcp.json`:

```json
{
  "mcpServers": {
    "ai-cos-mcp": {
      "type": "http",
      "url": "https://mcp.3niac.com/mcp"
    },
    "web-tools-mcp": {
      "type": "http",
      "url": "https://web.3niac.com/mcp"
    }
  }
}
```

- [ ] **Step 8: Commit**

```bash
git add mcp-servers/web-tools-mcp/deploy.sh .mcp.json
git commit -m "feat(web-tools-mcp): deploy pipeline, systemd, Cloudflare Tunnel"
```

---

## Chunk 6: Cookie Sync Infrastructure

### Task 6: Deploy cookie-sync.sh and set up cookie pipeline

The cookie-sync script already exists at `~/Claude Projects/Skills Factory/Web & Browsers/auth/scripts/cookie-sync.sh`. It extracts domain-filtered cookies from Safari/Chrome via browser_cookie3, converts to Netscape format, and pushes to the droplet via rsync.

**Files:**
- Source: `~/Claude Projects/Skills Factory/Web & Browsers/auth/scripts/cookie-sync.sh`
- Deploy to: `~/.ai-cos/scripts/cookie-sync.sh` (Mac)
- Auth registry: `~/Claude Projects/Skills Factory/Web & Browsers/auth/auth-service-registry.md`

**Flow:**
```
Mac (cron daily) → browser_cookie3 extracts from Safari/Chrome
  → ~/.ai-cos/cookies/<domain>.txt (Netscape format, chmod 600)
  → rsync over Tailscale → /opt/ai-cos/cookies/<domain>.txt (droplet)
  → web_browse loads cookies via context.add_cookies()
```

- [ ] **Step 1: Install browser_cookie3 on Mac**

```bash
pip3 install browser_cookie3
# Verify it works
python3 -c "import browser_cookie3; cj = browser_cookie3.safari(domain_name='.youtube.com'); print(f'{len(list(cj))} YouTube cookies')"
```

- [ ] **Step 2: Deploy cookie-sync.sh to Mac**

```bash
mkdir -p ~/.ai-cos/scripts ~/.ai-cos/cookies ~/.ai-cos/logs
cp ~/Claude\ Projects/Skills\ Factory/Web\ \&\ Browsers/auth/scripts/cookie-sync.sh ~/.ai-cos/scripts/
chmod +x ~/.ai-cos/scripts/cookie-sync.sh
```

- [ ] **Step 3: Fix DROPLET_HOST in cookie-sync.sh**

The script defaults to `droplet` but our Tailscale hostname is `aicos-droplet`:

```bash
sed -i '' 's/DROPLET_HOST:-droplet/DROPLET_HOST:-aicos-droplet/' ~/.ai-cos/scripts/cookie-sync.sh
```

- [ ] **Step 4: Create receiving directory on droplet**

```bash
ssh root@aicos-droplet "mkdir -p /opt/ai-cos/cookies && chmod 700 /opt/ai-cos/cookies"
```

- [ ] **Step 5: Add new domains to REGISTERED_DOMAINS in cookie-sync.sh**

```bash
# Edit the script to add X and Substack to registered domains
# The REGISTERED_DOMAINS array should be:
#   ".youtube.com"
#   ".google.com"
#   ".github.com"
#   ".x.com"
#   ".substack.com"
```

Open `~/.ai-cos/scripts/cookie-sync.sh` and update the `REGISTERED_DOMAINS` array:

```bash
REGISTERED_DOMAINS=(
    ".youtube.com"
    ".google.com"
    ".github.com"
    ".x.com"
    ".substack.com"
)
```

**Do NOT add `.linkedin.com`** — LinkedIn detects headless browsers and bans accounts. Use Browserbase (Layer 4) only.

- [ ] **Step 6: Test cookie-sync manually for all domains**

```bash
# Sync all registered domains
~/.ai-cos/scripts/cookie-sync.sh --all

# Verify cookies arrived on droplet
ssh root@aicos-droplet "ls -la /opt/ai-cos/cookies/ && wc -l /opt/ai-cos/cookies/*.txt"
```

- [ ] **Step 7: Test authenticated browse — YouTube (baseline)**

```bash
ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv run python -c \"
from server import web_browse
import json

# Browse YouTube with cookies — should show personalized/logged-in state
r = web_browse('https://www.youtube.com', cookies_domain='youtube.com')
print(json.dumps({k: v for k, v in r.items() if k != 'content'}, indent=2))
content = r.get('content', '')
print(f'Content length: {len(content)}')
print(f'First 500 chars: {content[:500]}')
\""
```

- [ ] **Step 8: Test authenticated browse — X/Twitter (home + bookmarks)**

```bash
ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv run python -c \"
from server import web_browse
import json

# X home feed — needs .x.com cookies
for url in ['https://x.com/home', 'https://x.com/i/bookmarks']:
    r = web_browse(url, cookies_domain='x.com')
    cookies_info = r.get('cookies_loaded', {})
    status = r.get('status', '?')
    title = r.get('title', '?')[:40]
    content_len = r.get('content_length', 0)
    print(f'{status:>5} | cookies={cookies_info.get(\"count\",0):>3} | {title:40} | len={content_len} | {url}')
    # Check for login wall vs feed content
    content = r.get('content', '')[:200]
    if 'log in' in content.lower() or 'sign in' in content.lower():
        print('  >> LOGIN WALL detected — cookies may be expired')
    else:
        print(f'  >> Content preview: {content[:100]}')
    print()
\""
```

- [ ] **Step 9: Test authenticated browse — Substack post**

```bash
ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv run python -c \"
from server import web_browse, web_scrape
import json

# Try Jina first (works for public posts without auth)
print('=== Jina Reader (no auth) ===')
r = web_scrape('https://substack.com/inbox/post/190905077')
print(f'Source: {r.get(\"source\")} | Status: {r.get(\"status\")} | Len: {r.get(\"content_length\",0)}')
print(f'Preview: {r.get(\"content\",\"\")[:200]}')
print()

# Try with cookies (for paywalled content)
print('=== Playwright + cookies ===')
r = web_browse('https://substack.com/inbox/post/190905077', cookies_domain='substack.com')
print(f'Status: {r.get(\"status\")} | Cookies: {r.get(\"cookies_loaded\",{}).get(\"count\",0)} | Len: {r.get(\"content_length\",0)}')
print(f'Preview: {r.get(\"content\",\"\")[:200]}')
\""
```

- [ ] **Step 10: Test graceful degradation — LinkedIn (NO cookies)**

```bash
ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv run python -c \"
from server import web_browse
import json

# LinkedIn WITHOUT cookies — expect login wall / redirect. This is correct behavior.
# DO NOT pass cookies_domain='linkedin.com' — account ban risk.
r = web_browse('https://www.linkedin.com/in/kumaraakash/recent-activity/all/')
print(json.dumps({k: v for k, v in r.items() if k != 'content'}, indent=2))
content = r.get('content', '')[:300]
print(f'Content preview: {content}')
print()
print('Expected: Login wall or redirect to linkedin.com/login')
print('LinkedIn auth requires Browserbase (Layer 4) — not implemented yet')
\""
```

- [ ] **Step 11: Set up daily cron on Mac**

```bash
# Add cron job — runs daily at 6am, syncs all registered domains
(crontab -l 2>/dev/null; echo '# cookie-sync: daily extraction for web-tools-mcp') | crontab -
(crontab -l 2>/dev/null; echo '0 6 * * * ~/.ai-cos/scripts/cookie-sync.sh --all >> ~/.ai-cos/logs/cookie-sync.log 2>&1') | crontab -

# Verify
crontab -l | grep cookie
```

- [ ] **Step 12: Add cookie_status tool to web-tools-mcp server**

Add to `server.py` — lets any surface check cookie freshness:

```python
@mcp.tool()
def cookie_status() -> dict:
    """Check which domain cookies are available and their freshness.

    Returns list of cookie files with domain, cookie count, age in days,
    and staleness warning if older than 7 days.
    """
    from pathlib import Path
    import time

    cookie_dir = Path(COOKIE_DIR)
    if not cookie_dir.exists():
        return {"cookies": [], "cookie_dir": str(cookie_dir), "error": "Cookie directory not found"}

    cookies = []
    for f in sorted(cookie_dir.glob("*.txt")):
        age_days = (time.time() - f.stat().st_mtime) / 86400
        line_count = sum(1 for line in f.read_text().splitlines()
                        if line.strip() and not line.startswith("#"))
        entry = {
            "domain": f.stem,
            "cookie_count": line_count,
            "age_days": round(age_days, 1),
            "file": str(f),
        }
        if age_days > 7:
            entry["warning"] = "STALE — re-run cookie-sync.sh on Mac"
        cookies.append(entry)

    return {"cookies": cookies, "cookie_dir": str(cookie_dir)}
```

- [ ] **Step 13: Deploy and test cookie_status**

```bash
rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='.venv' --exclude='tests' \
  mcp-servers/web-tools-mcp/ root@aicos-droplet:/opt/web-tools-mcp/

ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv run python -c \"
from server import cookie_status
import json
print(json.dumps(cookie_status(), indent=2))
\""
```

- [ ] **Step 14: Commit**

```bash
git add mcp-servers/web-tools-mcp/server.py
git commit -m "feat(web-tools-mcp): cookie loading in web_browse + cookie_status tool"
```

---

## Chunk 7: End-to-End Integration Test

### Task 7: Full integration test via MCP endpoint

**Files:**
- Create: `mcp-servers/web-tools-mcp/tests/test_tools.py`

- [ ] **Step 1: Write integration test script (direct Python calls on droplet)**

FastMCP streamable-http uses SSE, so raw httpx JSONRPC calls won't work.
Instead, test by importing the tool functions directly on the droplet (same
pattern as Chunks 1–4). This also tests the actual server code, not just the
transport layer.

```python
"""Integration tests for web-tools-mcp — run via direct import on droplet."""

import json
import sys

# Import tools directly from server module
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
        print(f"  {label:12} | status={status} | len={length:>6} | 404={is_404} | err={error[:40]}")
    print("PASS\n")

def test_browse():
    print("=== web_browse (3 URLs) ===")
    for label, url in [TEST_URLS[0], TEST_URLS[3], TEST_URLS[4]]:
        r = web_browse(url)
        status = r.get("status", "unknown")
        title = r.get("title", "?")[:40]
        length = r.get("content_length", 0)
        err = r.get("error", "")[:50]
        print(f"  {label:12} | {status:>5} | {length:>6} | {title:40} | {err}")
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
        print(f"  {c['domain']:20} | {c['cookie_count']:>4} cookies | {c['age_days']} days | {warning}")
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
        print(f"  {label:14} | {status:>5} | cookies={cookies_info.get('count', 0):>3} | {title:30} | len={content_len} | {warn}{err}")

    # LinkedIn WITHOUT cookies — expect login wall (Layer 4 only)
    print("  --- LinkedIn (no cookies, expect login wall) ---")
    r = web_browse("https://www.linkedin.com/in/kumaraakash/recent-activity/all/")
    title = r.get("title", "?")[:30]
    content = r.get("content", "")[:100].lower()
    has_login_wall = "sign in" in content or "log in" in content or "join" in content
    print(f"  linkedin      | {r.get('status',  '?'):>5} | cookies=  0 | {title:30} | login_wall={has_login_wall}")
    print("PASS\n")

if __name__ == "__main__":
    test_health()
    test_scrape()
    test_browse()
    test_search()
    test_cookies()
    test_authenticated_browse()
    print("All tests complete.")
```

- [ ] **Step 2: Deploy tests and run on droplet**

```bash
rsync -avz tests/ root@aicos-droplet:/opt/web-tools-mcp/tests/
ssh root@aicos-droplet "cd /opt/web-tools-mcp && /root/.local/bin/uv run python tests/test_tools.py"
```

Also verify the MCP endpoint is reachable externally (smoke test):

```bash
# From Mac — just check HTTP 200
curl -sI https://web.3niac.com/mcp | head -3
```

- [ ] **Step 3: Verify memory usage on droplet after all tests**

```bash
ssh root@aicos-droplet "free -h && echo '---' && systemctl status web-tools-mcp --no-pager | head -5 && echo '---' && systemctl status ai-cos-mcp --no-pager | head -5"
```

**Expected:** Both services running, memory usage reasonable (< 2GB used).

- [ ] **Step 4: Commit tests**

```bash
git add mcp-servers/web-tools-mcp/tests/
git commit -m "test(web-tools-mcp): integration tests against 6 test URLs"
```

---

## Chunk 8: Reference Docs Deployment + Deploy.sh Update

### Task 8: Deploy reference docs to droplet and update ai-cos-mcp deploy.sh

**Files:**
- Modify: `mcp-servers/ai-cos-mcp/deploy.sh`

- [ ] **Step 1: Add reference docs rsync to ai-cos-mcp deploy.sh**

Add to `mcp-servers/ai-cos-mcp/deploy.sh` before the final echo:

```bash
# Sync web-tools reference docs for Agent SDK runners
if [ -d "$HOME/.claude/skills/web-router/references/" ]; then
  echo "Syncing web-router reference docs..."
  ssh root@${DROPLET} "mkdir -p /opt/ai-cos-mcp/skills/web-router/references"
  rsync -avz "$HOME/.claude/skills/web-router/references/" \
    root@${DROPLET}:/opt/ai-cos-mcp/skills/web-router/references/
fi
```

- [ ] **Step 2: Run the sync manually once**

```bash
ssh root@aicos-droplet "mkdir -p /opt/ai-cos-mcp/skills/web-router/references"
rsync -avz ~/.claude/skills/web-router/references/ \
  root@aicos-droplet:/opt/ai-cos-mcp/skills/web-router/references/
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/ai-cos-mcp/deploy.sh
git commit -m "feat: add web-router reference docs to deploy pipeline"
```

---

## Future Work (Not in This Plan)

These are documented for later implementation:

1. **web_qa tool** — Playwright page inspection, console errors, health scoring (composes web_browse)
2. **web_perf tool** — Lighthouse via Chrome DevTools or `performance.timing` via Playwright evaluate
3. **web_monitor_setup / web_monitor_check** — Baseline capture, diff detection, alerting
4. **CAI remote MCP connector** — Add web-tools-mcp as remote connector in Claude.ai settings
5. **Firecrawl structured extraction** — `web_extract` tool for schema-driven JSON extraction
6. **Browserbase integration** — Isolated sessions for bot-hostile sites (Amazon, LinkedIn)

---

## Success Criteria

1. `health_check` returns Chrome + Playwright OK on droplet
2. `web_scrape` extracts content from 5/6 test URLs (Amazon may be blocked)
3. `web_browse` loads and returns page content for 4/6 test URLs
4. `web_browse` with `cookies_domain` loads cookies and browses authenticated
5. `web_search` returns results for general queries
6. `cookie_status` reports cookie freshness for synced domains
7. `cookie-sync.sh` runs on Mac cron, pushes cookies to droplet
8. Both `ai-cos-mcp` and `web-tools-mcp` run simultaneously without memory issues
9. `https://web.3niac.com/mcp` responds from Mac
10. `.mcp.json` updated, tools callable from CC
