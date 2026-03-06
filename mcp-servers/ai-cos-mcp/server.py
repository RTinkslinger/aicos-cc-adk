"""AI CoS MCP Server — exposes tools for remote Claude clients.

Deployed on DO droplet, accessible via Tailscale + Cloudflare Tunnel.
Remote clients (Claude.ai, Claude Code, digest.wiki) call these tools.
Agent SDK runners import lib/ directly — no MCP hop.
"""

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(
    "ai-cos-mcp",
    instructions="AI Chief of Staff MCP server. Provides context loading, action scoring, and preference tracking.",
)

DATABASE_URL = os.getenv("DATABASE_URL", "")


@mcp.tool()
def health_check() -> dict:
    """Check server and database connectivity."""
    import psycopg2

    result = {"server": "ok", "database": "unknown"}
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM action_outcomes")
        result["action_outcomes_count"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM thesis_threads")
        result["thesis_threads_count"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sync_queue WHERE attempts < 5")
        result["sync_queue_pending"] = cur.fetchone()[0]
        cur.close()
        conn.close()
        result["database"] = "ok"
    except Exception as e:
        result["database"] = f"error: {e}"
    return result


@mcp.tool()
def cos_load_context() -> dict:
    """Load AI CoS domain context — key sections from CONTEXT.md."""
    from pathlib import Path

    context_path = os.getenv("CONTEXT_MD_PATH", str(Path(__file__).parent / "CONTEXT.md"))
    path = Path(context_path)
    if not path.exists():
        return {"error": f"CONTEXT.md not found at {path}", "context": ""}

    text = path.read_text(encoding="utf-8")
    # Return a trimmed version for MCP clients (keep under 8K chars)
    return {"context": text[:8000], "path": str(path), "length": len(text)}


@mcp.tool()
def cos_score_action(
    bucket_impact: float,
    conviction_change: float,
    time_sensitivity: float,
    action_novelty: float,
    effort_vs_impact: float,
) -> dict:
    """Score an action using the AI CoS action scoring model.

    All inputs on 0-10 scale. Returns score (0-10) and classification.
    """
    from lib.scoring import ActionInput, classify_action, score_action

    action = ActionInput(
        bucket_impact=bucket_impact,
        conviction_change=conviction_change,
        time_sensitivity=time_sensitivity,
        action_novelty=action_novelty,
        effort_vs_impact=effort_vs_impact,
    )
    score = score_action(action)
    return {
        "score": round(score, 2),
        "classification": classify_action(score),
    }


@mcp.tool()
def cos_get_preferences(limit: int = 20) -> dict:
    """Get recent action outcome preferences for calibration."""
    from lib.preferences import get_preference_summary, get_preferences

    return {
        "recent_outcomes": get_preferences(limit=limit),
        "summary": get_preference_summary(),
    }


@mcp.tool()
def cos_create_thesis_thread(
    thread_name: str,
    core_thesis: str,
    key_questions: list[str] | None = None,
    connected_buckets: list[str] | None = None,
    discovery_source: str = "Claude",
    conviction: str = "New",
) -> dict:
    """Create a new thesis thread in the Thesis Tracker.

    Write-ahead: saves to Postgres first, then pushes to Notion.
    If Notion fails, the write is queued for retry — no data loss.

    Args:
        thread_name: Short, distinctive name for the thesis thread
        core_thesis: One-liner: what is the durable value insight?
        key_questions: 2-3 critical questions that would move conviction up or down
        connected_buckets: Priority buckets (New Cap Tables, Deepen Existing, New Founders, Thesis Evolution)
        discovery_source: Where this thesis originated (Claude, Content Pipeline, Meeting, Research)
        conviction: Initial conviction level (New, Evolving, Evolving Fast, Low, Medium, High)
    """
    from lib.thesis_db import create_thread, enqueue_sync, set_notion_page_id

    # 1. Write to Postgres first (always succeeds or raises)
    row = create_thread(
        thread_name=thread_name,
        core_thesis=core_thesis,
        conviction=conviction,
        discovery_source=discovery_source,
        connected_buckets=connected_buckets,
        key_questions=key_questions,
    )
    thread_id = row["id"]

    # 2. Push to Notion
    notion_page_id = None
    notion_synced = False
    try:
        from lib.notion_client import create_thesis_thread

        result = create_thesis_thread(
            thread_name=thread_name,
            core_thesis=core_thesis,
            key_questions=key_questions,
            connected_buckets=connected_buckets,
            discovery_source=discovery_source,
            conviction=conviction,
        )
        notion_page_id = result.get("id", "")
        set_notion_page_id(thread_id, notion_page_id)
        notion_synced = True
    except Exception as e:
        # Queue for retry — data is safe in Postgres
        enqueue_sync(
            table_name="thesis_threads",
            record_id=thread_id,
            operation="create",
            payload={
                "thread_name": thread_name,
                "core_thesis": core_thesis,
                "key_questions": key_questions,
                "connected_buckets": connected_buckets,
                "discovery_source": discovery_source,
                "conviction": conviction,
            },
        )
        print(f"Notion push failed for thesis '{thread_name}', queued for retry: {e}")

    return {
        "id": notion_page_id or str(thread_id),
        "pg_id": thread_id,
        "thread_name": thread_name,
        "conviction": conviction,
        "notion_synced": notion_synced,
    }


@mcp.tool()
def cos_update_thesis(
    thesis_name: str,
    new_evidence: str,
    evidence_direction: str = "for",
    source: str = "Claude",
    conviction: str | None = None,
    new_key_questions: list[str] | None = None,
    answered_questions: list[str] | None = None,
    investment_implications: str | None = None,
    key_companies: str | None = None,
) -> dict:
    """Update an existing thesis thread with new evidence.

    Write-ahead: updates Postgres first, then pushes to Notion.
    If Notion fails, the update is queued for retry — no data loss.

    Args:
        thesis_name: Name of the existing thesis thread (partial match supported)
        new_evidence: The evidence text to append
        evidence_direction: 'for', 'against', or 'mixed'
        source: Where this evidence came from (Claude, Content Pipeline, Meeting, Research)
        conviction: New conviction level if it should change (New, Evolving, Evolving Fast, Low, Medium, High)
        new_key_questions: New questions this evidence raises
        answered_questions: Existing open questions this evidence answers
        investment_implications: What Aakash should DO about this
        key_companies: Companies mentioned relevant to this thesis
    """
    from lib.thesis_db import enqueue_sync, find_thread_by_name, mark_synced, update_thread

    # 1. Find in Postgres first
    pg_thread = find_thread_by_name(thesis_name)

    if pg_thread is None:
        # Thread exists in Notion but not yet in Postgres — fall back to Notion-only
        # This handles the transition period before initial sync populates Postgres
        from lib.notion_client import update_thesis_tracker

        result = update_thesis_tracker(
            thesis_name=thesis_name,
            new_evidence=new_evidence,
            evidence_direction=evidence_direction,
            source=source,
            conviction=conviction,
            new_key_questions=new_key_questions,
            answered_questions=answered_questions,
            investment_implications=investment_implications,
            key_companies=key_companies,
        )
        if result is None:
            return {"error": f"Thesis '{thesis_name}' not found in tracker"}
        return {
            "id": result.get("id", ""),
            "thesis_name": thesis_name,
            "updated": True,
            "notion_synced": True,
            "pg_backed": False,
        }

    # 2. Write to Postgres first
    row = update_thread(
        thread_id=pg_thread["id"],
        new_evidence=new_evidence,
        evidence_direction=evidence_direction,
        source=source,
        conviction=conviction,
        new_key_questions=new_key_questions,
        answered_questions=answered_questions,
        investment_implications=investment_implications,
        key_companies=key_companies,
    )

    # 3. Push to Notion
    notion_synced = False
    try:
        from lib.notion_client import update_thesis_tracker

        result = update_thesis_tracker(
            thesis_name=thesis_name,
            new_evidence=new_evidence,
            evidence_direction=evidence_direction,
            source=source,
            conviction=conviction,
            new_key_questions=new_key_questions,
            answered_questions=answered_questions,
            investment_implications=investment_implications,
            key_companies=key_companies,
        )
        if result:
            mark_synced(pg_thread["id"])
            notion_synced = True
    except Exception as e:
        enqueue_sync(
            table_name="thesis_threads",
            record_id=pg_thread["id"],
            operation="update",
            payload={
                "thesis_name": thesis_name,
                "new_evidence": new_evidence,
                "evidence_direction": evidence_direction,
                "source": source,
                "conviction": conviction,
                "new_key_questions": new_key_questions,
                "answered_questions": answered_questions,
                "investment_implications": investment_implications,
                "key_companies": key_companies,
            },
        )
        print(f"Notion push failed for thesis update '{thesis_name}', queued: {e}")

    return {
        "id": pg_thread.get("notion_page_id", ""),
        "pg_id": pg_thread["id"],
        "thesis_name": thesis_name,
        "updated": True,
        "notion_synced": notion_synced,
        "pg_backed": True,
    }


@mcp.tool()
def cos_get_thesis_threads(include_key_questions: bool = False) -> dict:
    """Get all active thesis threads from the Thesis Tracker.

    Returns thread names, conviction levels, core theses, evidence,
    and key questions. Use this to understand current thesis state
    before creating or updating threads.

    Args:
        include_key_questions: If True, also fetches individual [OPEN]/[ANSWERED]
            questions from page blocks (slower — one API call per thread)
    """
    from lib.notion_client import fetch_thesis_threads

    threads = fetch_thesis_threads(include_key_questions=include_key_questions)
    return {"threads": threads, "count": len(threads)}


@mcp.tool()
def cos_get_recent_digests(limit: int = 10) -> dict:
    """Get recent content digests from the Content Digest DB.

    Returns analyzed content with titles, channels, relevance scores,
    net newness, summaries, and digest URLs.

    Args:
        limit: Max number of digests to return (default 10)
    """
    from lib.notion_client import fetch_recent_digests

    digests = fetch_recent_digests(limit=limit)
    return {"digests": digests, "count": len(digests)}


@mcp.tool()
def cos_get_actions(status: str | None = None, limit: int = 20) -> dict:
    """Get actions from the Actions Queue.

    Returns proposed, accepted, or in-progress actions with priorities,
    types, assignments, and thesis connections.

    Args:
        status: Filter by status (Proposed, Accepted, In Progress, Done, Dismissed).
            If None, returns all actions.
        limit: Max number of actions to return (default 20)
    """
    from lib.notion_client import fetch_actions

    actions = fetch_actions(status_filter=status, limit=limit)
    return {"actions": actions, "count": len(actions)}


@mcp.tool()
def cos_sync_thesis_status() -> dict:
    """Sync thesis Status field from Notion to Postgres.

    Status is the only human-owned field (Active/Exploring/Parked/Archived).
    Call this periodically or before scoring to ensure Postgres has the latest.
    """
    from lib.notion_client import sync_thesis_status_from_notion

    changes = sync_thesis_status_from_notion()
    return {"synced": len(changes), "changes": changes}


@mcp.tool()
def cos_seed_thesis_db() -> dict:
    """One-time seed: pull all thesis threads from Notion into Postgres.

    Run this once to populate Postgres with existing Notion data.
    Skips threads already in Postgres. Safe to run multiple times.
    """
    from lib.notion_client import seed_thesis_threads_to_postgres

    count = seed_thesis_threads_to_postgres()
    return {"inserted": count}


@mcp.tool()
def cos_retry_sync_queue() -> dict:
    """Process pending items in the sync queue.

    Retries failed Notion pushes with exponential backoff.
    Call this periodically or manually to drain the queue.
    """
    from lib.thesis_db import get_pending_syncs, mark_sync_done, mark_sync_failed

    pending = get_pending_syncs()
    results = []
    for item in pending:
        try:
            payload = item["payload"]
            if item["operation"] == "create":
                from lib.notion_client import create_thesis_thread
                from lib.thesis_db import set_notion_page_id

                result = create_thesis_thread(**payload)
                set_notion_page_id(item["record_id"], result.get("id", ""))
                mark_sync_done(item["id"])
                results.append({"id": item["id"], "status": "done"})
            elif item["operation"] == "update":
                from lib.notion_client import update_thesis_tracker
                from lib.thesis_db import mark_synced

                update_thesis_tracker(**payload)
                mark_synced(item["record_id"])
                mark_sync_done(item["id"])
                results.append({"id": item["id"], "status": "done"})
        except Exception as e:
            mark_sync_failed(item["id"], str(e))
            results.append({"id": item["id"], "status": "failed", "error": str(e)})

    return {"processed": len(results), "results": results}


@mcp.tool()
def cos_sync_actions() -> dict:
    """Bidirectional sync for Actions Queue.

    Pulls status changes from Notion (accept/dismiss), pushes locally-created
    actions to Notion. Detects field-level changes.
    """
    from runners.sync_agent import sync_actions

    return sync_actions()


@mcp.tool()
def cos_full_sync() -> dict:
    """Run full sync: thesis status + actions bidirectional + retry queue.

    Orchestrates all sync operations in one call. Returns results for each.
    """
    from runners.sync_agent import full_sync

    return full_sync()


@mcp.tool()
def cos_get_changes(limit: int = 20) -> dict:
    """Get recent change events detected during sync.

    Shows field-level changes between Notion and Postgres (status changes,
    conviction moves, priority updates). Useful for audit and debugging.
    """
    from lib.change_detection import get_unprocessed_changes

    changes = get_unprocessed_changes(limit=limit)
    return {"changes": changes, "count": len(changes)}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
