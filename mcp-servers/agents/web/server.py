"""Web Tools MCP — Universal web capability server.
Handles browser automation, scraping, search, YouTube extraction, auth, strategy.
Port 8001, web.3niac.com via Cloudflare Tunnel.

External surface: 12 direct tools + 3 async task tools (submit/status/result).
Agent brain: 9 SDK @tool functions via web_sdk_server (used by web_task_submit).
"""
from __future__ import annotations

import asyncio
from datetime import datetime

from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from web.lib.logger import setup_logger
from web.task_store import complete_task, create_task, fail_task, get_task
from web.tools import (
    check_strategy,
    cookie_status,
    extract_transcript,
    extract_youtube,
    fingerprint,
    health_check,
    manage_session,
    validate,
    watch_url,
    web_browse,
    web_scrape,
    web_search,
)

load_dotenv()

logger = setup_logger("web-tools-mcp", "/opt/agents/logs/web.log")

mcp = FastMCP(
    "web-tools-mcp",
    instructions=(
        "Web Tools MCP server. Provides direct tools (web_scrape, web_browse, "
        "web_search, etc.) for simple single-step operations at zero LLM cost, "
        "plus async web_task_submit/status/result for complex multi-step tasks "
        "requiring agent reasoning. Also exposes check_strategy, manage_session, "
        "and validate for direct caller use."
    ),
)

# GET /health — ops liveness check
@mcp.custom_route("/health", methods=["GET"])
async def health_get(request: Request) -> JSONResponse:
    """Simple GET health check for ops tooling."""
    return JSONResponse({"status": "ok", "agent": "web-tools-mcp", "port": 8001})


# -----------------------------------------------------------------------
# Register direct FastMCP tools (no agent reasoning, zero LLM cost)
# -----------------------------------------------------------------------

# Core web operations (9 tools)
mcp.tool()(web_scrape)
mcp.tool()(web_browse)
mcp.tool()(web_search)
mcp.tool()(extract_youtube)
mcp.tool()(extract_transcript)
mcp.tool()(cookie_status)
mcp.tool()(fingerprint)
mcp.tool()(watch_url)
mcp.tool()(health_check)

# Exposed utility tools (previously SDK-only)
mcp.tool()(check_strategy)
mcp.tool()(manage_session)
mcp.tool()(validate)


# -----------------------------------------------------------------------
# Async task pattern — submit/poll/retrieve (CAI-facing)
# -----------------------------------------------------------------------

async def _run_web_task_background(
    task_id: str,
    task: str,
    url: str,
    output_schema: dict | None,
) -> None:
    """Background coroutine that runs the agent and updates the task store."""
    from web.agent import run_agent_task

    t = get_task(task_id)
    if t:
        t.status = "running"
    try:
        result = await run_agent_task(
            task=task, url=url, output_schema=output_schema, effort="high"
        )
        complete_task(task_id, result, cost_usd=result.get("cost_usd", 0))
    except Exception as e:
        logger.error("web_task %s failed: %s", task_id, e)
        fail_task(task_id, str(e))


@mcp.tool()
async def web_task_submit(
    task: str,
    url: str = "",
    output_schema: dict | None = None,
) -> dict:
    """Submit a complex web task for async agent execution.

    Returns immediately with a task_id. Poll with web_task_status,
    retrieve results with web_task_result.

    Args:
        task: Natural language description of what to do
        url: Optional target URL
        output_schema: Optional JSON schema for structured output
    """
    t = create_task(task=task, url=url)
    asyncio.create_task(_run_web_task_background(t.task_id, task, url, output_schema))
    logger.info("web_task_submit: %s (url=%s)", t.task_id, url)
    return {"task_id": t.task_id, "status": "started"}


@mcp.tool()
async def web_task_status(task_id: str) -> dict:
    """Check the status of an async web task.

    Args:
        task_id: The task ID returned by web_task_submit
    """
    t = get_task(task_id)
    if t is None:
        return {"error": f"Unknown task_id: {task_id}"}
    elapsed_s = (t.completed_at or datetime.utcnow()) - t.started_at
    result: dict = {
        "task_id": t.task_id,
        "status": t.status,
        "elapsed_s": round(elapsed_s.total_seconds(), 1),
    }
    if t.cost_usd is not None:
        result["cost_usd"] = t.cost_usd
    return result


@mcp.tool()
async def web_task_result(task_id: str) -> dict:
    """Retrieve the full result of a completed async web task.

    Returns the result if status is 'complete', error details if 'error',
    or a status message if still running.

    Args:
        task_id: The task ID returned by web_task_submit
    """
    t = get_task(task_id)
    if t is None:
        return {"error": f"Unknown task_id: {task_id}"}
    if t.status == "complete":
        return {
            "task_id": t.task_id,
            "status": "complete",
            "result": t.result,
            "cost_usd": t.cost_usd,
            "elapsed_s": round(
                ((t.completed_at or t.started_at) - t.started_at).total_seconds(), 1
            ),
        }
    if t.status == "error":
        return {
            "task_id": t.task_id,
            "status": "error",
            "error": t.error,
        }
    return {
        "task_id": t.task_id,
        "status": t.status,
        "message": "Task is still running. Poll again with web_task_status.",
    }


# -----------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
