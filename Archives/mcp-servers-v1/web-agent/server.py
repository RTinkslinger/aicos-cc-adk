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
async def web_scrape(url: str, use_firecrawl: bool = False) -> dict:
    """Extract content from URL as markdown. No agent reasoning — direct extraction.
    Jina Reader (free) by default, Firecrawl as fallback.
    """
    from lib.scrape import scrape

    return await scrape(url, use_firecrawl=use_firecrawl)


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
        url=url,
        action=action,
        selector=selector,
        text=text,
        cookies_domain=cookies_domain,
        readiness=readiness,
        timeout_ms=timeout_ms,
    )


@mcp.tool()
async def web_search(query: str, limit: int = 5) -> dict:
    """Search the web. No agent reasoning — direct Firecrawl search."""
    from lib.search import search

    return await search(query, limit=limit)


@mcp.tool()
def cookie_status() -> dict:
    """Check available cookies and freshness."""
    from lib.cookies import cookie_status as _cookie_status

    return _cookie_status()


@mcp.tool()
async def health_check() -> dict:
    """Check server, Chrome, Playwright, and agent connectivity."""
    import shutil

    result: dict = {
        "server": "ok",
        "chrome": "unknown",
        "playwright": "unknown",
    }

    chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    result["chrome"] = chrome if chrome else "not found"

    try:
        from lib.browser import get_browser

        browser = await get_browser()
        result["playwright"] = f"ok (connected={browser.is_connected()})"
    except Exception as e:
        result["playwright"] = f"error: {e}"

    result["anthropic_key_set"] = bool(os.getenv("ANTHROPIC_API_KEY"))
    result["firecrawl_key_set"] = bool(os.getenv("FIRECRAWL_API_KEY"))
    return result


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
