"""Web Agent tools — dual layer: 11 FastMCP tools (external callers) + 9 SDK @tool functions (agent reasoning).

FastMCP tools: registered by server.py, exposed to Content Agent, CC, CAI via proxy.
SDK @tool functions: registered via create_sdk_mcp_server(), used by ClaudeSDKClient during web_task.
"""

from __future__ import annotations

import json

from claude_agent_sdk import create_sdk_mcp_server, tool

# -----------------------------------------------------------------------
# Category 1: FastMCP tool functions (11 tools — NOT decorated here)
# server.py registers these with @mcp.tool()
# -----------------------------------------------------------------------


async def web_task(
    task: str,
    url: str = "",
    output_schema: dict | None = None,
    timeout_s: int = 120,
    effort: str = "high",
) -> dict:
    """Execute a web task with full agent intelligence.

    The agent reasons about what to do: which tool to use, how to handle
    errors, whether to retry, how to validate content. Use this for
    complex or ambiguous tasks. For simple scrape/browse/search, use
    the direct tools instead (cheaper, faster).

    Args:
        task: Natural language description of what to do
        url: Optional target URL
        output_schema: Optional JSON schema for structured output
        timeout_s: Wall-clock timeout in seconds (default 120)
        effort: Reasoning effort level — "high", "medium", "low" (default "high")
    """
    # agent.py will be implemented in a future iteration
    return {"status": "not_implemented", "message": "Agent mode requires agent.py"}


async def web_scrape(url: str, use_firecrawl: bool = False) -> dict:
    """Extract content from URL as markdown. No agent reasoning — direct extraction.
    Jina Reader (free) by default, Firecrawl as fallback.
    """
    from web.lib.scrape import scrape

    result = await scrape(url, use_firecrawl=use_firecrawl)
    return {
        "content": result.get("content", ""),
        "content_length": result.get("content_length", 0),
        "url": url,
        "source": result.get("source", ""),
        "status": result.get("status"),
        "error": result.get("error"),
    }


async def web_browse(
    url: str,
    action: str = "snapshot",
    readiness_mode: str = "auto",
) -> dict:
    """Navigate to URL with Playwright. No agent reasoning — direct browse.
    Includes readiness ladder for SPAs. Max 2 concurrent via semaphore.

    Args:
        url: Target URL
        action: "snapshot" (default), "screenshot", "click", "fill", "evaluate"
        readiness_mode: "auto", "selector:<css>", "time:<ms>", "none"
    """
    from web.lib.browser import browse

    return await browse(url=url, action=action, readiness=readiness_mode)


async def web_search(query: str, limit: int = 5) -> dict:
    """Search the web. No agent reasoning — direct Firecrawl search."""
    from web.lib.search import search

    return await search(query, limit=limit)


async def web_screenshot(url: str) -> dict:
    """Capture a screenshot of the URL using Playwright.

    Returns screenshot as base64-encoded PNG in the result dict.
    """
    from web.lib.browser import browse

    return await browse(url=url, action="screenshot")


async def extract_youtube(
    playlist_url: str | None = None,
    video_urls: list[str] | None = None,
    since_days: int = 3,
) -> dict:
    """Extract YouTube playlist metadata and transcripts.

    Uses yt-dlp + youtube-transcript-api. Saves output JSON to queue/.
    Returns the full extraction data dict.

    Args:
        playlist_url: YouTube playlist URL (uses default playlist if omitted)
        video_urls: List of individual video URLs (alternative to playlist)
        since_days: Only include videos from the last N days (default 3)
    """
    from web.lib.extraction import extract_and_save

    output_path = extract_and_save(
        playlist_url=playlist_url,
        video_urls=video_urls,
        since_days=since_days,
    )
    if output_path is None:
        return {"status": "no_videos", "videos": [], "total_videos": 0}

    with open(output_path, encoding="utf-8") as f:
        data = json.load(f)

    data["output_file"] = str(output_path)
    return data


async def extract_transcript(video_id: str) -> dict:
    """Fetch transcript for a single YouTube video.

    Tries youtube-transcript-api first, falls back to yt-dlp subtitles.

    Args:
        video_id: YouTube video ID (11-char ID or full URL)
    """
    from web.lib.extraction import extract_video_id, get_transcript

    clean_id = extract_video_id(video_id)
    return get_transcript(clean_id)


async def cookie_status() -> dict:
    """Check available domain cookies and their freshness.

    Returns list of cookie files with age, count, and stale warnings.
    """
    from web.lib.sessions import cookie_status as _cookie_status

    return _cookie_status()


async def fingerprint(url: str) -> dict:
    """Classify a site: detect framework, CMS, page type, SPA, auth required.

    Uses partial HTML fetch for bandwidth efficiency.

    Args:
        url: Target URL to fingerprint
    """
    from web.lib.fingerprint import fingerprint as _fingerprint

    return await _fingerprint(url)


async def watch_url(
    url: str,
    interval_minutes: int = 60,
    notify_method: str = "log",
) -> dict:
    """Register a URL for periodic monitoring.

    Checks for content changes at the given interval and notifies via the
    specified method. Phase 2 stub — monitoring loop runs separately.

    Args:
        url: URL to monitor
        interval_minutes: Check interval in minutes (default 60)
        notify_method: Notification method — "log", "webhook", "mcp" (default "log")
    """
    from web.lib.monitor import register_watch

    return await register_watch(url, interval_minutes=interval_minutes, notify_method=notify_method)


async def health_check() -> dict:
    """Check web agent health."""
    return {"status": "ok", "agent": "web-agent"}


# -----------------------------------------------------------------------
# Category 2: Internal @tool functions (9 tools for Agent SDK reasoning)
# Registered via create_sdk_mcp_server() — used by ClaudeSDKClient in web_task
# -----------------------------------------------------------------------


@tool("browse", "Navigate to URL with Playwright and get page content", {"url": str, "readiness_mode": str})
async def browse_tool(args: dict) -> dict:
    """Navigate to URL with intelligent readiness detection (SPA-aware)."""
    from web.lib.browser import browse

    result = await browse(
        url=args["url"],
        action="snapshot",
        readiness=args.get("readiness_mode", "auto"),
    )
    text = result.get("content") or result.get("error") or str(result)
    return {"content": [{"type": "text", "text": text[:30000]}]}


@tool("scrape", "Extract clean markdown content from a URL using Jina Reader or Firecrawl", {"url": str, "use_firecrawl": bool})
async def scrape_tool(args: dict) -> dict:
    """Extract content from URL as clean markdown."""
    from web.lib.scrape import scrape

    result = await scrape(args["url"], use_firecrawl=args.get("use_firecrawl", False))
    content = result.get("content") or result.get("error") or ""
    return {"content": [{"type": "text", "text": content[:50000]}]}


@tool("search", "Search the web and return titles, URLs, and snippets", {"query": str, "limit": int})
async def search_tool(args: dict) -> dict:
    """Search the web via Firecrawl."""
    from web.lib.search import search

    result = await search(args["query"], limit=args.get("limit", 5))
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


@tool("screenshot", "Capture a screenshot of a URL as base64 PNG", {"url": str})
async def screenshot_tool(args: dict) -> dict:
    """Capture a full-page screenshot via Playwright."""
    from web.lib.browser import browse

    result = await browse(url=args["url"], action="screenshot")
    if "screenshot_base64" in result:
        # Return as image content block if possible, else base64 text
        return {
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result["screenshot_base64"],
                    },
                }
            ]
        }
    error = result.get("error", "Screenshot failed")
    return {"content": [{"type": "text", "text": f"Error: {error}"}], "is_error": True}


@tool(
    "interact",
    "Click, fill, or evaluate JavaScript on a page via Playwright",
    {"url": str, "action": str, "selector": str, "text": str},
)
async def interact_tool(args: dict) -> dict:
    """Interact with page elements — click, fill form fields, or run JS."""
    from web.lib.browser import browse

    result = await browse(
        url=args["url"],
        action=args.get("action", "click"),
        selector=args.get("selector", ""),
        text=args.get("text", ""),
    )
    status = result.get("status") or result.get("error") or str(result)
    return {"content": [{"type": "text", "text": str(status)}]}


@tool("fingerprint", "Classify a site: detect framework, CMS, page type, SPA, auth required", {"url": str})
async def fingerprint_sdk_tool(args: dict) -> dict:
    """Fingerprint a site to determine the best extraction strategy."""
    from web.lib.fingerprint import fingerprint

    result = await fingerprint(args["url"])
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


@tool(
    "check_strategy",
    "Query the UCB bandit to get the best known strategy for a site origin",
    {"origin": str},
)
async def check_strategy_tool(args: dict) -> dict:
    """Get the highest-UCB strategy for an origin from the SQLite strategy cache."""
    from web.lib.strategy import get_strategy

    result = get_strategy(args["origin"])
    if result is None:
        return {"content": [{"type": "text", "text": json.dumps({"strategy": None, "note": "No strategies seeded for this origin"})}]}
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


@tool(
    "manage_session",
    "Save or load a Playwright storageState (cookies + localStorage) for a domain",
    {"action": str, "domain": str, "state_json": str},
)
async def manage_session_tool(args: dict) -> dict:
    """Persist or restore full browser session state for a domain.

    action: "save" | "load" | "check" | "list"
    domain: e.g. "linkedin.com"
    state_json: JSON string of storageState dict (required for action="save")
    """
    from web.lib.sessions import (
        check_storage_state_valid,
        list_storage_states,
        load_storage_state,
        save_storage_state,
    )

    action = args.get("action", "load")
    domain = args.get("domain", "")

    if action == "save":
        raw = args.get("state_json", "{}")
        try:
            state = json.loads(raw)
        except json.JSONDecodeError as e:
            return {"content": [{"type": "text", "text": f"Error: invalid state_json — {e}"}], "is_error": True}
        save_storage_state(domain, state)
        return {"content": [{"type": "text", "text": f"Saved storageState for {domain}"}]}

    elif action == "load":
        state = load_storage_state(domain)
        if state is None:
            return {"content": [{"type": "text", "text": f"No storageState found for {domain}"}]}
        return {"content": [{"type": "text", "text": json.dumps(state, indent=2)}]}

    elif action == "check":
        fresh = check_storage_state_valid(domain)
        return {"content": [{"type": "text", "text": json.dumps({"domain": domain, "fresh": fresh})}]}

    elif action == "list":
        states = list_storage_states()
        return {"content": [{"type": "text", "text": json.dumps(states, indent=2)}]}

    return {"content": [{"type": "text", "text": f"Unknown action: {action}"}], "is_error": True}


@tool(
    "validate",
    "Score content quality — detect login walls, cookie banners, error pages, short content",
    {"content": str, "url": str, "expected_type": str},
)
async def validate_tool(args: dict) -> dict:
    """Validate extracted content quality before returning to caller."""
    from web.lib.quality import validate_content

    result = validate_content(
        content=args.get("content", ""),
        url=args.get("url", ""),
        expected_type=args.get("expected_type", ""),
    )
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


# -----------------------------------------------------------------------
# SDK MCP server — bundles all 9 @tool functions for ClaudeSDKClient
# -----------------------------------------------------------------------

web_sdk_server = create_sdk_mcp_server(
    name="web",
    version="1.0.0",
    tools=[
        browse_tool,
        scrape_tool,
        search_tool,
        screenshot_tool,
        interact_tool,
        fingerprint_sdk_tool,
        check_strategy_tool,
        manage_session_tool,
        validate_tool,
    ],
)
