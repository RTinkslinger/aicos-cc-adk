"""State MCP Server — CAI's window into AI CoS system state.

FastMCP server with 5 tools + GET /health endpoint.
Backed by asyncpg connection pool against Postgres.

Tools:
  - get_state: Read thesis threads + unread notifications
  - create_thesis_thread: Create new thesis (notion_synced=false)
  - update_thesis: Append evidence to thesis thread
  - post_message: Write to CAI inbox for agent processing
  - health_check: Liveness + DB connectivity check

Run:
  python -m state.server
  # or: uv run state/server.py
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from state.db.connection import close_pool, get_pool
from state.db.inbox import post_message as db_post_message
from state.db.notifications import get_unread
from state.db.thesis import create_thread, get_threads, update_thread


@asynccontextmanager
async def lifespan(app: Any):
    """Initialize asyncpg pool on startup, close on shutdown."""
    await get_pool()
    yield
    await close_pool()


mcp = FastMCP("state-mcp", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Tool 1: get_state
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_state(include: list[str] | None = None) -> dict:
    """Get AI CoS system state for CAI context loading.

    Returns thesis threads and unread notifications.
    Use include=["thesis","notifications"] to filter sections.
    Default (None): returns both.
    """
    sections = set(include) if include else {"thesis", "notifications"}
    result: dict[str, Any] = {}

    if "thesis" in sections:
        threads = await get_threads()
        result["thesis_threads"] = [
            {
                "name": t["thread_name"],
                "core_thesis": t["core_thesis"],
                "conviction": t["conviction"],
                "status": t["status"],
                "evidence_for": t["evidence_for"],
                "evidence_against": t["evidence_against"],
                "key_questions": t["key_question_summary"],
            }
            for t in threads
        ]

    if "notifications" in sections:
        notifs = await get_unread()
        result["notifications"] = [
            {
                "id": n["id"],
                "source": n["source"],
                "type": n["type"],
                "content": n["content"],
                "metadata": n["metadata"],
                "created_at": str(n["created_at"]),
            }
            for n in notifs
        ]

    return result


# ---------------------------------------------------------------------------
# Tool 2: create_thesis_thread
# ---------------------------------------------------------------------------
@mcp.tool()
async def create_thesis_thread(name: str, core_thesis: str) -> dict:
    """Create a new thesis thread.

    Writes to Postgres with notion_synced=false.
    Sync Agent will push to Notion on next cycle.

    Args:
        name: Unique name for the thesis thread.
        core_thesis: The core thesis statement.

    Returns:
        The newly created thesis thread record.
    """
    row = await create_thread(name, core_thesis)
    return {
        "status": "created",
        "thread": {
            "id": row["id"],
            "name": row["thread_name"],
            "core_thesis": row["core_thesis"],
            "conviction": row["conviction"],
            "notion_synced": row["notion_synced"],
        },
    }


# ---------------------------------------------------------------------------
# Tool 3: update_thesis
# ---------------------------------------------------------------------------
@mcp.tool()
async def update_thesis(thesis_name: str, evidence: str, direction: str = "for") -> dict:
    """Add evidence to a thesis thread.

    Direction: 'for', 'against', or 'mixed'.
    Sets notion_synced=false for Sync Agent to pick up.

    Args:
        thesis_name: Name of the thesis thread to update.
        evidence: New evidence text to append.
        direction: One of 'for', 'against', or 'mixed'.

    Returns:
        The updated thesis thread record.
    """
    row = await update_thread(thesis_name, evidence, direction)
    return {
        "status": "updated",
        "thread": {
            "id": row["id"],
            "name": row["thread_name"],
            "evidence_for": row["evidence_for"],
            "evidence_against": row["evidence_against"],
            "notion_synced": row["notion_synced"],
        },
    }


# ---------------------------------------------------------------------------
# Tool 4: post_message
# ---------------------------------------------------------------------------
@mcp.tool()
async def post_message(content: str, metadata: dict | None = None) -> dict:
    """Post a message to the CAI inbox for agent processing.

    Orchestrator checks inbox every ~60 seconds and relays to Content Agent.
    Just describe what you need in plain text — the agent figures out what to do.

    Args:
        content: Message body text. Include URLs, questions, or instructions.
        metadata: Optional metadata dict for structured context.

    Returns:
        The newly created inbox message record.
    """
    row = await db_post_message("message", content, metadata)
    return {
        "status": "posted",
        "message": {
            "id": row["id"],
            "type": row["type"],
            "content": row["content"],
            "created_at": str(row["created_at"]),
        },
    }


# ---------------------------------------------------------------------------
# Tool 5: health_check
# ---------------------------------------------------------------------------
@mcp.tool()
async def health_check() -> dict:
    """Liveness + DB connectivity check.

    Tests that the asyncpg pool can execute a simple query.
    Returns status, service name, and DB connectivity result.
    """
    db_ok = False
    db_error = None
    try:
        pool = await get_pool()
        result = await pool.fetchval("SELECT 1")
        db_ok = result == 1
    except Exception as e:
        db_error = str(e)

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "state-mcp",
        "port": 8000,
        "db_connected": db_ok,
        **({"db_error": db_error} if db_error else {}),
    }


# ---------------------------------------------------------------------------
# GET /health — ops endpoint (non-MCP)
# ---------------------------------------------------------------------------
@mcp.custom_route("/health", methods=["GET"])
async def health_get(request):
    """HTTP GET /health for ops monitoring and load balancer probes."""
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok", "service": "state-mcp", "port": 8000})


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
