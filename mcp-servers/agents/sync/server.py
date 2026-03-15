"""Sync Agent — Gateway MCP server.
THE ONLY agent that reads/writes Notion + Postgres.
Port 8000, mcp.3niac.com via Cloudflare Tunnel.

Exposes 23 tools across 4 categories:
  1. State Read Tools (9)
  2. Write-Receiver Tools (5)
  3. Sync Operation Tools (6)
  4. Proxy Tools (3)

Internal 10-min sync loop: thesis status → actions sync → change detection
→ queue drain → process changes.
"""

from __future__ import annotations

import asyncio
import logging

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from shared.logging import setup_logger

load_dotenv()

logger = setup_logger("sync-agent", "/opt/agents/logs/sync.log")

mcp = FastMCP(
    "sync-agent",
    instructions=(
        "AI CoS Sync Agent — the system state keeper and gateway. "
        "THE ONLY agent that reads/writes Notion and Postgres. "
        "Serves all state reads, write-receives from Content Agent, "
        "bidirectional sync, and proxies web tools to Web Agent."
    ),
)

# ---------------------------------------------------------------------------
# Register tools from tools.py by wrapping each plain async function
# ---------------------------------------------------------------------------

import sync.tools as _tools


# 1. STATE READ TOOLS


@mcp.tool()
async def health_check() -> dict:
    """Check server and database connectivity."""
    return await _tools.health_check()


@mcp.tool()
async def cos_load_context() -> dict:
    """Load AI CoS domain context — key sections from CONTEXT.md."""
    return await _tools.cos_load_context()


@mcp.tool()
async def cos_get_thesis_threads(include_key_questions: bool = False) -> dict:
    """Get all active thesis threads from the Thesis Tracker.

    Args:
        include_key_questions: If True, fetches individual [OPEN]/[ANSWERED]
            questions from page blocks (slower — one API call per thread).
    """
    return await _tools.cos_get_thesis_threads(
        include_key_questions=include_key_questions
    )


@mcp.tool()
async def cos_get_recent_digests(limit: int = 10) -> dict:
    """Get recent content digests from the Content Digest DB.

    Args:
        limit: Max number of digests to return (default 10)
    """
    return await _tools.cos_get_recent_digests(limit=limit)


@mcp.tool()
async def cos_get_actions(status: str | None = None, limit: int = 20) -> dict:
    """Get actions from the Actions Queue.

    Args:
        status: Filter by status (Proposed, Accepted, In Progress, Done, Dismissed).
            If None, returns all actions.
        limit: Max number of actions to return (default 20)
    """
    return await _tools.cos_get_actions(status=status, limit=limit)


@mcp.tool()
async def cos_get_preferences(limit: int = 20) -> dict:
    """Get recent action outcome preferences for calibration."""
    return await _tools.cos_get_preferences(limit=limit)


@mcp.tool()
async def cos_score_action(
    bucket_impact: float,
    conviction_change: float,
    time_sensitivity: float,
    action_novelty: float,
    effort_vs_impact: float,
) -> dict:
    """Score an action using the AI CoS action scoring model.

    All inputs on 0-10 scale. Returns score (0-10) and classification.
    """
    return await _tools.cos_score_action(
        bucket_impact=bucket_impact,
        conviction_change=conviction_change,
        time_sensitivity=time_sensitivity,
        action_novelty=action_novelty,
        effort_vs_impact=effort_vs_impact,
    )


@mcp.tool()
async def cos_sync_status() -> dict:
    """Get unified sync status dashboard.

    Shows: thesis/actions sync state, last sync times, queue depth,
    unsynced items, and recent change events.
    """
    return await _tools.cos_sync_status()


@mcp.tool()
async def cos_get_changes(limit: int = 20) -> dict:
    """Get recent change events detected during sync.

    Args:
        limit: Max number of changes to return (default 20)
    """
    return await _tools.cos_get_changes(limit=limit)


# 2. WRITE-RECEIVER TOOLS


@mcp.tool()
async def write_digest(digest_data: dict, request_id: str) -> dict:
    """Create a Content Digest entry in Notion (idempotent).

    Args:
        digest_data: Dict matching create_digest_entry() signature fields
        request_id: Unique key for idempotency (e.g., "{slug}:{processing_date}")
    """
    return await _tools.write_digest(digest_data=digest_data, request_id=request_id)


@mcp.tool()
async def write_actions(actions: list, request_id: str) -> dict:
    """Create action entries in Notion and Postgres (idempotent per request_id).

    Args:
        actions: List of dicts, each matching create_action_entry() signature
        request_id: Unique key for idempotency (e.g., "{digest_slug}:actions:{date}")
    """
    return await _tools.write_actions(actions=actions, request_id=request_id)


@mcp.tool()
async def update_thesis(
    thesis_name: str,
    evidence: str,
    direction: str = "for",
    request_id: str = "",
) -> dict:
    """Update an existing thesis thread with new evidence.

    Args:
        thesis_name: Name of the existing thesis thread (partial match supported)
        evidence: The evidence text to append
        direction: 'for', 'against', or 'mixed'
        request_id: Idempotency key
    """
    return await _tools.update_thesis(
        thesis_name=thesis_name,
        evidence=evidence,
        direction=direction,
        request_id=request_id,
    )


@mcp.tool()
async def create_thesis_thread(
    name: str,
    core_thesis: str,
    request_id: str = "",
) -> dict:
    """Create a new thesis thread.

    Args:
        name: Short, distinctive thread name
        core_thesis: One-liner value insight
        request_id: Idempotency key
    """
    return await _tools.create_thesis_thread(
        name=name,
        core_thesis=core_thesis,
        request_id=request_id,
    )


@mcp.tool()
async def log_preference(
    action_text: str,
    action_type: str,
    outcome: str,
    score: float,
    scoring_factors: dict,
    request_id: str = "",
) -> dict:
    """Log an action outcome to the preference store.

    Args:
        action_text: The action description
        action_type: e.g. 'research', 'meeting', 'follow-up', 'content'
        outcome: 'proposed', 'accepted', 'dismissed', 'completed'
        score: Computed action score (0-10)
        scoring_factors: Dict of factor_name -> value used in scoring
        request_id: Idempotency key
    """
    return await _tools.log_preference(
        action_text=action_text,
        action_type=action_type,
        outcome=outcome,
        score=score,
        scoring_factors=scoring_factors,
        request_id=request_id,
    )


# 3. SYNC OPERATION TOOLS


@mcp.tool()
async def cos_sync_thesis_status() -> dict:
    """Sync thesis Status field from Notion to Postgres.

    Status is the only human-owned field (Active/Exploring/Parked/Archived).
    """
    return await _tools.cos_sync_thesis_status()


@mcp.tool()
async def cos_sync_actions() -> dict:
    """Bidirectional sync for Actions Queue.

    Pulls status changes from Notion (accept/dismiss), pushes locally-created
    actions to Notion. Detects field-level changes.
    """
    return await _tools.cos_sync_actions()


@mcp.tool()
async def cos_full_sync() -> dict:
    """Run full sync: thesis status + actions bidirectional + retry queue.

    Orchestrates all sync operations in one call.
    """
    return await _tools.cos_full_sync()


@mcp.tool()
async def cos_retry_sync_queue() -> dict:
    """Process pending items in the sync queue.

    Retries failed Notion pushes with exponential backoff.
    """
    return await _tools.cos_retry_sync_queue()


@mcp.tool()
async def cos_process_changes() -> dict:
    """Process unprocessed change events and generate actions from them.

    Turns field-level changes (conviction moves, status changes, outcome ratings)
    into proposed actions.
    """
    return await _tools.cos_process_changes()


@mcp.tool()
async def cos_seed_thesis_db() -> dict:
    """One-time seed: pull all thesis threads from Notion into Postgres.

    Skips threads already in Postgres. Safe to run multiple times.
    """
    return await _tools.cos_seed_thesis_db()


# 4. PROXY TOOLS


@mcp.tool()
async def web_task(
    task: str,
    url: str = "",
    output_schema: dict | None = None,
) -> dict:
    """Delegate a web task to the Web Agent.

    Args:
        task: Natural language description of the task
        url: Optional starting URL
        output_schema: Optional JSON schema for structured output
    """
    return await _tools.web_task(task=task, url=url, output_schema=output_schema)


@mcp.tool()
async def web_scrape(url: str, use_firecrawl: bool = False) -> dict:
    """Scrape a URL via the Web Agent.

    Args:
        url: URL to scrape
        use_firecrawl: If True, use Firecrawl for JS-heavy pages
    """
    return await _tools.web_scrape(url=url, use_firecrawl=use_firecrawl)


@mcp.tool()
async def web_search(query: str, limit: int = 5) -> dict:
    """Search the web via the Web Agent.

    Args:
        query: Search query string
        limit: Max results to return (default 5)
    """
    return await _tools.web_search(query=query, limit=limit)


# ---------------------------------------------------------------------------
# Internal 10-minute sync loop
# ---------------------------------------------------------------------------


async def _sync_loop() -> None:
    """Periodic sync cycle: runs every 10 minutes indefinitely."""
    logger.info("sync_loop_start", extra={"interval_seconds": 600})
    while True:
        await asyncio.sleep(600)
        try:
            logger.info("sync_cycle_begin")

            # Step 1: Thesis status sync (Notion → Postgres, human-owned Status)
            thesis_result = await _tools.cos_sync_thesis_status()
            logger.info(
                "sync_thesis_status",
                extra={"synced": thesis_result.get("synced", 0)},
            )

            # Step 2: Actions bidirectional sync
            actions_result = await _tools.cos_sync_actions()
            logger.info(
                "sync_actions",
                extra={"result": str(actions_result)[:200]},
            )

            # Step 3: Drain sync retry queue (failed Notion pushes)
            queue_result = await _tools.cos_retry_sync_queue()
            logger.info(
                "sync_queue_drain",
                extra={"processed": queue_result.get("processed", 0)},
            )

            # Step 4: Process change events → generate actions
            changes_result = await _tools.cos_process_changes()
            logger.info(
                "sync_process_changes",
                extra={"result": str(changes_result)[:200]},
            )

            logger.info("sync_cycle_complete")

        except Exception as exc:
            logger.error(
                "sync_cycle_error",
                extra={"error": str(exc)},
                exc_info=True,
            )


# ---------------------------------------------------------------------------
# Startup: launch sync loop as background task
# ---------------------------------------------------------------------------


@mcp.on_startup()
async def _on_startup() -> None:
    """Start the background sync loop when the server starts."""
    asyncio.create_task(_sync_loop())
    logger.info("server_started", extra={"port": 8000})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
