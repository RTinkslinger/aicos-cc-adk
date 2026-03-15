"""Sync Agent MCP tool definitions.

All tool functions are defined here as plain async functions.
server.py imports these and registers them with @mcp.tool().

4 categories:
  1. State Read Tools  (9) — migrate from ai-cos-mcp/server.py
  2. Write-Receiver Tools (5) — NEW, for Content Agent writes via MCP
  3. Sync Operation Tools (6) — migrate from ai-cos-mcp/server.py
  4. Proxy Tools (3) — forward to Web Agent via shared.mcp_client
"""

from __future__ import annotations

import os
from typing import Any

from shared.logging import get_trace_id, setup_logger

logger = setup_logger("sync-agent")

# ---------------------------------------------------------------------------
# 1. STATE READ TOOLS
# ---------------------------------------------------------------------------


async def health_check() -> dict[str, Any]:
    """Check server and database connectivity."""
    import psycopg2

    database_url = os.getenv("DATABASE_URL", "")
    result: dict[str, Any] = {"server": "ok", "database": "unknown"}
    try:
        conn = psycopg2.connect(database_url)
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


async def cos_load_context() -> dict[str, Any]:
    """Load AI CoS domain context — key sections from CONTEXT.md."""
    from pathlib import Path

    context_path = os.getenv("CONTEXT_MD_PATH", str(Path(__file__).parent.parent.parent / "CONTEXT.md"))
    path = Path(context_path)
    if not path.exists():
        return {"error": f"CONTEXT.md not found at {path}", "context": ""}

    text = path.read_text(encoding="utf-8")
    return {"context": text[:8000], "path": str(path), "length": len(text)}


async def cos_get_thesis_threads(include_key_questions: bool = False) -> dict[str, Any]:
    """Get all active thesis threads from the Thesis Tracker.

    Args:
        include_key_questions: If True, fetches individual [OPEN]/[ANSWERED]
            questions from page blocks (slower — one API call per thread).
    """
    from sync.lib.notion_client import fetch_thesis_threads

    threads = fetch_thesis_threads(include_key_questions=include_key_questions)
    return {"threads": threads, "count": len(threads)}


async def cos_get_recent_digests(limit: int = 10) -> dict[str, Any]:
    """Get recent content digests from the Content Digest DB.

    Args:
        limit: Max number of digests to return (default 10)
    """
    from sync.lib.notion_client import fetch_recent_digests

    digests = fetch_recent_digests(limit=limit)
    return {"digests": digests, "count": len(digests)}


async def cos_get_actions(status: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Get actions from the Actions Queue.

    Args:
        status: Filter by status (Proposed, Accepted, In Progress, Done, Dismissed).
            If None, returns all actions.
        limit: Max number of actions to return (default 20)
    """
    from sync.lib.notion_client import fetch_actions

    actions = fetch_actions(status_filter=status, limit=limit)
    return {"actions": actions, "count": len(actions)}


async def cos_get_preferences(limit: int = 20) -> dict[str, Any]:
    """Get recent action outcome preferences for calibration."""
    from sync.lib.preferences import get_preference_summary, get_preferences

    return {
        "recent_outcomes": get_preferences(limit=limit),
        "summary": get_preference_summary(),
    }


async def cos_score_action(
    bucket_impact: float,
    conviction_change: float,
    time_sensitivity: float,
    action_novelty: float,
    effort_vs_impact: float,
) -> dict[str, Any]:
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


async def cos_sync_status() -> dict[str, Any]:
    """Get unified sync status dashboard.

    Shows: thesis/actions sync state, last sync times, queue depth,
    unsynced items, and recent change events.
    """
    from sync.lib.change_detection import get_sync_status

    return get_sync_status()


async def cos_get_changes(limit: int = 20) -> dict[str, Any]:
    """Get recent change events detected during sync.

    Args:
        limit: Max number of changes to return (default 20)
    """
    from sync.lib.change_detection import get_unprocessed_changes

    changes = get_unprocessed_changes(limit=limit)
    return {"changes": changes, "count": len(changes)}


# ---------------------------------------------------------------------------
# 2. WRITE-RECEIVER TOOLS
# ---------------------------------------------------------------------------


async def write_digest(digest_data: dict[str, Any], request_id: str) -> dict[str, Any]:
    """Create a Content Digest entry in Notion (idempotent).

    Idempotency: if request_id was already processed, returns the cached result
    without writing again. Notion write is rate-limited.

    Args:
        digest_data: Dict matching create_digest_entry() signature fields
        request_id: Unique key for idempotency (e.g., "{slug}:{processing_date}")
    """
    import psycopg2

    database_url = os.getenv("DATABASE_URL", "")
    trace_id = get_trace_id()

    # Idempotency check — look for prior write in Postgres idempotency log
    if request_id:
        try:
            conn = psycopg2.connect(database_url)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT result_id FROM idempotency_log WHERE request_id = %s AND tool_name = 'write_digest'",
                        (request_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        logger.info(
                            "idempotent_skip",
                            extra={"tool": "write_digest", "request_id": request_id, "trace_id": trace_id},
                        )
                        return {"notion_page_id": row[0], "idempotent": True, "request_id": request_id}
            finally:
                conn.close()
        except Exception:
            # If idempotency table doesn't exist yet, proceed with write
            pass

    # Rate-limit before hitting Notion
    from sync.lib.rate_limiter import notion_limiter

    await notion_limiter.acquire()

    from sync.lib.notion_client import create_digest_entry

    page = create_digest_entry(**digest_data, request_id=request_id)
    notion_page_id = page.get("id", "")

    # Record in idempotency log
    if request_id and notion_page_id:
        try:
            conn = psycopg2.connect(database_url)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO idempotency_log (request_id, tool_name, result_id)
                        VALUES (%s, 'write_digest', %s)
                        ON CONFLICT (request_id, tool_name) DO NOTHING
                        """,
                        (request_id, notion_page_id),
                    )
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass  # Non-blocking — idempotency log is best-effort

    logger.info(
        "write_digest",
        extra={"notion_page_id": notion_page_id, "request_id": request_id, "trace_id": trace_id},
    )
    return {"notion_page_id": notion_page_id, "idempotent": False, "request_id": request_id}


async def write_actions(actions: list[dict[str, Any]], request_id: str) -> dict[str, Any]:
    """Create action entries in Notion and Postgres (idempotent per request_id).

    Idempotency: if request_id was already processed, returns the cached result.
    Each action is rate-limited individually before the Notion write.

    Args:
        actions: List of dicts, each matching create_action_entry() signature
        request_id: Unique key for idempotency (e.g., "{digest_slug}:actions:{date}")
    """
    import psycopg2

    database_url = os.getenv("DATABASE_URL", "")
    trace_id = get_trace_id()

    # Idempotency check
    if request_id:
        try:
            conn = psycopg2.connect(database_url)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT result_id FROM idempotency_log WHERE request_id = %s AND tool_name = 'write_actions'",
                        (request_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        logger.info(
                            "idempotent_skip",
                            extra={"tool": "write_actions", "request_id": request_id, "trace_id": trace_id},
                        )
                        return {"idempotent": True, "request_id": request_id, "written": 0}
            finally:
                conn.close()
        except Exception:
            pass

    from sync.lib.actions_db import create_action
    from sync.lib.notion_client import create_action_entry
    from sync.lib.rate_limiter import notion_limiter

    written = []
    errors = []

    for action_data in actions:
        try:
            # Write to Postgres first (write-ahead)
            pg_row = create_action(
                action=action_data.get("action_text", action_data.get("action", "")),
                action_type=action_data.get("action_type", ""),
                priority=action_data.get("priority", ""),
                source=action_data.get("source", "SyncAgent"),
                assigned_to=action_data.get("assigned_to", "Aakash"),
                created_by=action_data.get("created_by", "AI CoS"),
                reasoning=action_data.get("reasoning", ""),
                source_content=action_data.get("source_content", ""),
                thesis_connection=action_data.get("thesis_connection", ""),
                relevance_score=action_data.get("relevance_score"),
                request_id=None,  # Per-action idempotency not used here; request_id covers the batch
            )

            # Rate-limit before Notion write
            await notion_limiter.acquire()

            page = create_action_entry(
                action_text=action_data.get("action_text", action_data.get("action", "")),
                priority=action_data.get("priority", "P3"),
                action_type=action_data.get("action_type", "Research"),
                assigned_to=action_data.get("assigned_to", "Aakash"),
                company_name=action_data.get("company_name"),
                thesis_connection=action_data.get("thesis_connection"),
                source_digest_page_id=action_data.get("source_digest_page_id"),
                relevance_score=action_data.get("relevance_score"),
                reasoning=action_data.get("reasoning", ""),
                source_content=action_data.get("source_content", ""),
            )
            notion_page_id = page.get("id", "")

            # Link Postgres row to Notion page
            if notion_page_id and pg_row.get("id"):
                from sync.lib.actions_db import set_notion_page_id as set_action_notion_id
                set_action_notion_id(pg_row["id"], notion_page_id)

            written.append({"pg_id": pg_row.get("id"), "notion_page_id": notion_page_id})
        except Exception as e:
            errors.append({"action": action_data.get("action_text", "?")[:50], "error": str(e)})
            logger.error(
                "write_actions_error",
                extra={"error": str(e), "trace_id": trace_id},
            )

    # Record idempotency key only if at least one action was written
    if request_id and written:
        try:
            conn = psycopg2.connect(database_url)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO idempotency_log (request_id, tool_name, result_id)
                        VALUES (%s, 'write_actions', %s)
                        ON CONFLICT (request_id, tool_name) DO NOTHING
                        """,
                        (request_id, str(len(written))),
                    )
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

    logger.info(
        "write_actions",
        extra={"written": len(written), "errors": len(errors), "request_id": request_id, "trace_id": trace_id},
    )
    return {
        "written": len(written),
        "errors": errors,
        "results": written,
        "idempotent": False,
        "request_id": request_id,
    }


async def update_thesis(
    thesis_name: str,
    evidence: str,
    direction: str = "for",
    request_id: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Update an existing thesis thread with new evidence.

    Write-ahead: Postgres first, then Notion. If Notion fails, queued for retry.
    Idempotent: if request_id was already processed, returns without writing.

    Args:
        thesis_name: Name of the existing thesis thread (partial match supported)
        evidence: The evidence text to append
        direction: 'for', 'against', or 'mixed'
        request_id: Idempotency key
        **kwargs: Additional fields: source, conviction, new_key_questions,
            answered_questions, investment_implications, key_companies
    """
    from sync.lib.thesis_db import (
        enqueue_sync,
        find_thread_by_name,
        mark_synced,
        update_thread,
    )

    trace_id = get_trace_id()

    # 1. Find in Postgres
    pg_thread = find_thread_by_name(thesis_name)

    if pg_thread is None:
        # Fallback to Notion-only (transition period before seeding)
        from sync.lib.rate_limiter import notion_limiter

        await notion_limiter.acquire()
        from sync.lib.notion_client import update_thesis_tracker

        result = update_thesis_tracker(
            thesis_name=thesis_name,
            new_evidence=evidence,
            evidence_direction=direction,
            source=kwargs.get("source", "SyncAgent"),
            conviction=kwargs.get("conviction"),
            new_key_questions=kwargs.get("new_key_questions"),
            answered_questions=kwargs.get("answered_questions"),
            investment_implications=kwargs.get("investment_implications"),
            key_companies=kwargs.get("key_companies"),
            request_id=request_id or None,
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

    # 2. Write to Postgres first (write-ahead)
    row = update_thread(
        thread_id=pg_thread["id"],
        new_evidence=evidence,
        evidence_direction=direction,
        source=kwargs.get("source", "SyncAgent"),
        conviction=kwargs.get("conviction"),
        new_key_questions=kwargs.get("new_key_questions"),
        answered_questions=kwargs.get("answered_questions"),
        investment_implications=kwargs.get("investment_implications"),
        key_companies=kwargs.get("key_companies"),
        request_id=request_id or None,
    )

    # 3. Push to Notion (rate-limited)
    notion_synced = False
    try:
        from sync.lib.rate_limiter import notion_limiter

        await notion_limiter.acquire()
        from sync.lib.notion_client import update_thesis_tracker

        result = update_thesis_tracker(
            thesis_name=thesis_name,
            new_evidence=evidence,
            evidence_direction=direction,
            source=kwargs.get("source", "SyncAgent"),
            conviction=kwargs.get("conviction"),
            new_key_questions=kwargs.get("new_key_questions"),
            answered_questions=kwargs.get("answered_questions"),
            investment_implications=kwargs.get("investment_implications"),
            key_companies=kwargs.get("key_companies"),
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
                "new_evidence": evidence,
                "evidence_direction": direction,
                "source": kwargs.get("source", "SyncAgent"),
                "conviction": kwargs.get("conviction"),
                "new_key_questions": kwargs.get("new_key_questions"),
                "answered_questions": kwargs.get("answered_questions"),
                "investment_implications": kwargs.get("investment_implications"),
                "key_companies": kwargs.get("key_companies"),
            },
            request_id=request_id or None,
        )
        logger.warning(
            "notion_push_queued",
            extra={"thesis": thesis_name, "error": str(e), "trace_id": trace_id},
        )

    return {
        "id": pg_thread.get("notion_page_id", ""),
        "pg_id": pg_thread["id"],
        "thesis_name": thesis_name,
        "updated": True,
        "notion_synced": notion_synced,
        "pg_backed": True,
    }


async def create_thesis_thread(
    name: str,
    core_thesis: str,
    request_id: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a new thesis thread.

    Write-ahead: Postgres first, then Notion. If Notion fails, queued for retry.
    Idempotent: if request_id was already processed, returns the existing row.

    Args:
        name: Short, distinctive thread name
        core_thesis: One-liner value insight
        request_id: Idempotency key
        **kwargs: key_questions, connected_buckets, discovery_source, conviction
    """
    from sync.lib.thesis_db import (
        create_thread as pg_create_thread,
        enqueue_sync,
        set_notion_page_id,
    )

    trace_id = get_trace_id()

    # 1. Write to Postgres first
    row = pg_create_thread(
        thread_name=name,
        core_thesis=core_thesis,
        conviction=kwargs.get("conviction", "New"),
        discovery_source=kwargs.get("discovery_source", "SyncAgent"),
        connected_buckets=kwargs.get("connected_buckets"),
        key_questions=kwargs.get("key_questions"),
        request_id=request_id or None,
    )
    thread_id = row["id"]

    # 2. Push to Notion (rate-limited)
    notion_page_id = None
    notion_synced = False
    try:
        from sync.lib.rate_limiter import notion_limiter

        await notion_limiter.acquire()
        from sync.lib.notion_client import create_thesis_thread as notion_create

        result = notion_create(
            thread_name=name,
            core_thesis=core_thesis,
            key_questions=kwargs.get("key_questions"),
            connected_buckets=kwargs.get("connected_buckets"),
            discovery_source=kwargs.get("discovery_source", "SyncAgent"),
            conviction=kwargs.get("conviction", "New"),
        )
        notion_page_id = result.get("id", "")
        set_notion_page_id(thread_id, notion_page_id)
        notion_synced = True
    except Exception as e:
        enqueue_sync(
            table_name="thesis_threads",
            record_id=thread_id,
            operation="create",
            payload={
                "thread_name": name,
                "core_thesis": core_thesis,
                "key_questions": kwargs.get("key_questions"),
                "connected_buckets": kwargs.get("connected_buckets"),
                "discovery_source": kwargs.get("discovery_source", "SyncAgent"),
                "conviction": kwargs.get("conviction", "New"),
            },
            request_id=request_id or None,
        )
        logger.warning(
            "notion_push_queued",
            extra={"thesis": name, "error": str(e), "trace_id": trace_id},
        )

    return {
        "id": notion_page_id or str(thread_id),
        "pg_id": thread_id,
        "thread_name": name,
        "conviction": kwargs.get("conviction", "New"),
        "notion_synced": notion_synced,
    }


async def log_preference(
    action_text: str,
    action_type: str,
    outcome: str,
    score: float,
    scoring_factors: dict[str, float],
    request_id: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Log an action outcome to the preference store.

    Args:
        action_text: The action description
        action_type: e.g. 'research', 'meeting', 'follow-up', 'content'
        outcome: 'proposed', 'accepted', 'dismissed', 'completed'
        score: Computed action score (0-10)
        scoring_factors: Dict of factor_name -> value used in scoring
        request_id: Idempotency key
        **kwargs: source_digest_slug, company, thesis_thread
    """
    from sync.lib.preferences import log_outcome

    trace_id = get_trace_id()

    row_id = log_outcome(
        action_text=action_text,
        action_type=action_type,
        outcome=outcome,
        score=score,
        scoring_factors=scoring_factors,
        source_digest_slug=kwargs.get("source_digest_slug"),
        company=kwargs.get("company"),
        thesis_thread=kwargs.get("thesis_thread"),
        request_id=request_id or None,
    )

    logger.info(
        "log_preference",
        extra={"outcome": outcome, "score": score, "row_id": row_id, "trace_id": trace_id},
    )
    return {"id": row_id, "logged": True, "request_id": request_id}


# ---------------------------------------------------------------------------
# 3. SYNC OPERATION TOOLS
# ---------------------------------------------------------------------------


async def cos_sync_thesis_status() -> dict[str, Any]:
    """Sync thesis Status field from Notion to Postgres.

    Status is the only human-owned field (Active/Exploring/Parked/Archived).
    """
    from sync.lib.notion_client import sync_thesis_status_from_notion

    changes = sync_thesis_status_from_notion()
    return {"synced": len(changes), "changes": changes}


async def cos_sync_actions() -> dict[str, Any]:
    """Bidirectional sync for Actions Queue.

    Pulls status changes from Notion (accept/dismiss), pushes locally-created
    actions to Notion. Detects field-level changes.
    """
    from runners.sync_agent import sync_actions

    return sync_actions()


async def cos_full_sync() -> dict[str, Any]:
    """Run full sync: thesis status + actions bidirectional + retry queue.

    Orchestrates all sync operations in one call.
    """
    from runners.sync_agent import full_sync

    return full_sync()


async def cos_retry_sync_queue() -> dict[str, Any]:
    """Process pending items in the sync queue.

    Retries failed Notion pushes with exponential backoff.
    """
    from sync.lib.thesis_db import get_pending_syncs, mark_sync_done, mark_sync_failed

    pending = get_pending_syncs()
    results = []
    for item in pending:
        try:
            payload = item["payload"]
            if item["operation"] == "create":
                from sync.lib.notion_client import create_thesis_thread as notion_create
                from sync.lib.thesis_db import set_notion_page_id

                result = notion_create(**payload)
                set_notion_page_id(item["record_id"], result.get("id", ""))
                mark_sync_done(item["id"])
                results.append({"id": item["id"], "status": "done"})
            elif item["operation"] == "update":
                from sync.lib.notion_client import update_thesis_tracker
                from sync.lib.thesis_db import mark_synced

                update_thesis_tracker(**payload)
                mark_synced(item["record_id"])
                mark_sync_done(item["id"])
                results.append({"id": item["id"], "status": "done"})
        except Exception as e:
            mark_sync_failed(item["id"], str(e))
            results.append({"id": item["id"], "status": "failed", "error": str(e)})

    return {"processed": len(results), "results": results}


async def cos_process_changes() -> dict[str, Any]:
    """Process unprocessed change events and generate actions from them.

    Turns field-level changes (conviction moves, status changes, outcome ratings)
    into proposed actions.
    """
    from runners.sync_agent import process_changes

    return process_changes()


async def cos_seed_thesis_db() -> dict[str, Any]:
    """One-time seed: pull all thesis threads from Notion into Postgres.

    Skips threads already in Postgres. Safe to run multiple times.
    """
    from sync.lib.notion_client import seed_thesis_threads_to_postgres

    count = seed_thesis_threads_to_postgres()
    return {"inserted": count}


# ---------------------------------------------------------------------------
# 4. PROXY TOOLS (forward to Web Agent)
# ---------------------------------------------------------------------------

WEB_AGENT_URL = os.getenv("WEB_AGENT_URL", "http://localhost:8001/mcp")


async def web_task(
    task: str,
    url: str = "",
    output_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Delegate a web task to the Web Agent.

    Args:
        task: Natural language description of the task
        url: Optional starting URL
        output_schema: Optional JSON schema for structured output
    """
    import pybreaker

    from shared.mcp_client import AgentCallError, call_agent_tool

    trace_id = get_trace_id()
    arguments: dict[str, Any] = {"task": task}
    if url:
        arguments["url"] = url
    if output_schema is not None:
        arguments["output_schema"] = output_schema

    try:
        result = await call_agent_tool(
            agent_url=WEB_AGENT_URL,
            tool_name="web_task",
            arguments=arguments,
            timeout_s=120.0,
            agent_name="web-agent",
        )
        logger.info("web_task_ok", extra={"url": url, "trace_id": trace_id})
        return result
    except pybreaker.CircuitBreakerError:
        logger.error("web_agent_circuit_open", extra={"trace_id": trace_id})
        return {"error": "Web Agent unavailable (circuit open)", "circuit_open": True}
    except AgentCallError as e:
        logger.error("web_task_error", extra={"error": str(e), "trace_id": trace_id})
        return {"error": str(e)}


async def web_scrape(url: str, use_firecrawl: bool = False) -> dict[str, Any]:
    """Scrape a URL via the Web Agent.

    Args:
        url: URL to scrape
        use_firecrawl: If True, use Firecrawl for JS-heavy pages
    """
    import pybreaker

    from shared.mcp_client import AgentCallError, call_agent_tool

    trace_id = get_trace_id()

    try:
        result = await call_agent_tool(
            agent_url=WEB_AGENT_URL,
            tool_name="web_scrape",
            arguments={"url": url, "use_firecrawl": use_firecrawl},
            timeout_s=60.0,
            agent_name="web-agent",
        )
        logger.info("web_scrape_ok", extra={"url": url, "trace_id": trace_id})
        return result
    except pybreaker.CircuitBreakerError:
        logger.error("web_agent_circuit_open", extra={"trace_id": trace_id})
        return {"error": "Web Agent unavailable (circuit open)", "circuit_open": True}
    except AgentCallError as e:
        logger.error("web_scrape_error", extra={"error": str(e), "trace_id": trace_id})
        return {"error": str(e)}


async def web_search(query: str, limit: int = 5) -> dict[str, Any]:
    """Search the web via the Web Agent.

    Args:
        query: Search query string
        limit: Max results to return (default 5)
    """
    import pybreaker

    from shared.mcp_client import AgentCallError, call_agent_tool

    trace_id = get_trace_id()

    try:
        result = await call_agent_tool(
            agent_url=WEB_AGENT_URL,
            tool_name="web_search",
            arguments={"query": query, "limit": limit},
            timeout_s=30.0,
            agent_name="web-agent",
        )
        logger.info("web_search_ok", extra={"query": query[:50], "trace_id": trace_id})
        return result
    except pybreaker.CircuitBreakerError:
        logger.error("web_agent_circuit_open", extra={"trace_id": trace_id})
        return {"error": "Web Agent unavailable (circuit open)", "circuit_open": True}
    except AgentCallError as e:
        logger.error("web_search_error", extra={"error": str(e), "trace_id": trace_id})
        return {"error": str(e)}
