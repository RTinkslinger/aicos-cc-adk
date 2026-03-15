"""Web Agent — Universal web master.
Handles browser automation, scraping, search, YouTube extraction, auth, strategy.
Port 8001, web.3niac.com via Cloudflare Tunnel.
Leaf agent — does not call other agents.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from shared.logging import setup_logger
from web.tools import (
    cookie_status,
    extract_transcript,
    extract_youtube,
    fingerprint,
    health_check,
    watch_url,
    web_browse,
    web_screenshot,
    web_scrape,
    web_search,
)

load_dotenv()

logger = setup_logger("web-agent", "/opt/agents/logs/web.log")

mcp = FastMCP(
    "web-agent",
    instructions=(
        "Universal web master agent. Handles browser automation, scraping, search, "
        "YouTube extraction, authentication, strategy learning, and URL monitoring. "
        "Use web_task for complex multi-step tasks requiring agent reasoning. "
        "Use direct tools (web_scrape, web_browse, web_search, etc.) for simple "
        "single-step operations — zero LLM cost."
    ),
)

# GET /health — ops liveness check (C2 audit fix)
from starlette.requests import Request
from starlette.responses import JSONResponse


@mcp.custom_route("/health", methods=["GET"])
async def health_get(request: Request) -> JSONResponse:
    """Simple GET health check for ops tooling."""
    return JSONResponse({"status": "ok", "agent": "web-agent", "port": 8001})


# -----------------------------------------------------------------------
# Register the 10 direct FastMCP tools (no agent reasoning)
# -----------------------------------------------------------------------

mcp.tool()(web_scrape)
mcp.tool()(web_browse)
mcp.tool()(web_search)
mcp.tool()(web_screenshot)
mcp.tool()(extract_youtube)
mcp.tool()(extract_transcript)
mcp.tool()(cookie_status)
mcp.tool()(fingerprint)
mcp.tool()(watch_url)
mcp.tool()(health_check)


# -----------------------------------------------------------------------
# web_task — registered separately to override placeholder with agent.py
# -----------------------------------------------------------------------


@mcp.tool()
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
    from web.agent import run_agent_task

    return await run_agent_task(
        task=task,
        url=url,
        output_schema=output_schema,
        effort=effort,
    )


# -----------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
