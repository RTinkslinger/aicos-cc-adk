"""Browser management — async Playwright, readiness ladder, context pooling, cookie injection.

CONCURRENCY MODEL (review-driven):
- Uses async_playwright (never blocks event loop)
- asyncio.Lock on browser initialization (prevents double Chrome launch)
- asyncio.Semaphore(2) on concurrent browse calls (prevents OOM on 4GB droplet)
- context.close() in finally block (prevents resource leaks)
- shutdown_browser() for clean process exit

Readiness ladder (most reliable → least reliable):
1. Deterministic selector — wait for specific element to be visible
2. MutationObserver quiet window — DOM stable for 500ms
3. Framework markers — React Suspense gone, __NEXT_DATA__ present
4. Time-based fallback — asyncio.sleep (last resort)
"""

import asyncio
import logging
import time
from pathlib import Path

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

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
            # Reset Playwright on reconnect — stale handle causes launch failures
            if _playwright is not None:
                try:
                    await _playwright.stop()
                except Exception:
                    pass
                _playwright = None
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(
                channel="chrome",
                headless=True,
                args=CHROME_ARGS,
            )
            logger.info("Chrome browser launched")
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
    """Create an isolated browser context with optional cookies and persona.

    If no persona is provided, uses the default stealth persona (linux_us).
    """
    browser = await get_browser()

    # Use stealth persona by default for coherent fingerprint
    if persona is None:
        from lib.stealth import get_persona

        persona = get_persona()

    ua = persona.get("user_agent", DEFAULT_UA)
    viewport = persona.get("viewport", {"width": 1280, "height": 720})

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

    async with _browse_semaphore:
        try:
            context, cookie_info = await create_context(
                cookies_domain=cookies_domain
            )
            if cookies_domain:
                result["cookies_loaded"] = cookie_info

            page = await context.new_page()

            # Console errors
            console_errors: list[str] = []
            page.on(
                "console",
                lambda msg: (
                    console_errors.append(msg.text) if msg.type == "error" else None
                ),
            )

            # Navigate
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            # Readiness ladder
            await _wait_for_readiness(page, readiness)

            result["title"] = await page.title()
            result["final_url"] = page.url

            if action == "snapshot":
                text_content = await page.evaluate(
                    "document.body ? document.body.innerText : ''"
                )
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
                result["screenshot_base64"] = base64.b64encode(
                    screenshot_bytes
                ).decode()
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
        css = mode[len("selector:") :]
        try:
            await page.wait_for_selector(css, state="visible", timeout=10000)
            return
        except Exception:
            pass  # Fall through to auto

    if mode.startswith("time:"):
        try:
            ms = max(0, min(int(mode[len("time:") :]), 30000))  # Cap at 30s
        except ValueError:
            ms = 3000  # Fall back to 3s on parse error
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
        await page.evaluate(
            """
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
        """
        )
        text_len = await page.evaluate(
            "(document.body && document.body.innerText) ? document.body.innerText.length : 0"
        )
        if text_len > 200:
            return
    except Exception:
        pass

    # Step 3: Framework markers
    has_content = await page.evaluate(
        """
        (() => {
            if (document.getElementById('__NEXT_DATA__')) return true;
            const root = document.getElementById('root') || document.getElementById('__next');
            if (root && root.children.length > 1) return true;
            return document.querySelectorAll('article, main, [role="main"]').length > 0;
        })()
    """
    )
    if has_content:
        return

    # Step 4: Time fallback (3s) — non-blocking
    await asyncio.sleep(3)


def _flatten_a11y(node: dict, depth: int = 0, max_depth: int = 30) -> str:
    """Flatten accessibility tree to readable text."""
    if depth > max_depth:
        return ""
    parts = []
    role = node.get("role", "")
    name = node.get("name", "")
    if name and role not in ("generic", "none"):
        parts.append(f"{'  ' * depth}[{role}] {name}")
    for child in node.get("children", []):
        parts.append(_flatten_a11y(child, depth + 1, max_depth))
    return "\n".join(parts)


async def _load_cookies(
    context: BrowserContext, domain: str, cookie_dir: str
) -> dict:
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

    # Size guard — skip files > 1MB
    if cookie_file.stat().st_size > 1_000_000:
        result["error"] = "Cookie file unexpectedly large — skipping"
        result["count"] = 0
        return result

    cookies = []
    for line in cookie_file.read_text(encoding="utf-8", errors="replace").splitlines():
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
        await context.add_cookies(cookies)
    result["count"] = len(cookies)
    return result
