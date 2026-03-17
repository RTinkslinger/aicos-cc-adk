"""Postgres backing store for Thesis Tracker.

Write-ahead pattern: all thesis operations write here first, then push to Notion.
If the Notion push fails, the write is queued in sync_queue for retry.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL", "")


def _get_conn():
    return psycopg2.connect(DATABASE_URL)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def create_thread(
    thread_name: str,
    core_thesis: str,
    conviction: str = "New",
    status: str = "Exploring",
    discovery_source: str = "Claude",
    connected_buckets: list[str] | None = None,
    key_questions: list[str] | None = None,
    notion_page_id: str | None = None,
) -> dict[str, Any]:
    """Insert a new thesis thread into Postgres. Returns the row as a dict."""
    kq_json = json.dumps({
        "open": key_questions or [],
        "answered": [],
    })
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO thesis_threads
                    (thread_name, core_thesis, conviction, status, discovery_source,
                     connected_buckets, key_questions_json, key_question_summary,
                     notion_page_id, date_discovered)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, CURRENT_DATE)
                RETURNING *
                """,
                (
                    thread_name,
                    core_thesis,
                    conviction,
                    status,
                    discovery_source,
                    connected_buckets or [],
                    kq_json,
                    f"{len(key_questions or [])} open questions" if key_questions else "",
                    notion_page_id,
                ),
            )
            row = dict(cur.fetchone())
        conn.commit()
        return row
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Update (evidence append)
# ---------------------------------------------------------------------------


def update_thread(
    thread_id: int,
    new_evidence: str,
    evidence_direction: str = "for",
    source: str = "Claude",
    conviction: str | None = None,
    new_key_questions: list[str] | None = None,
    answered_questions: list[str] | None = None,
    investment_implications: str | None = None,
    key_companies: str | None = None,
    notion_page_id: str | None = None,
) -> dict[str, Any]:
    """Append evidence to an existing thread in Postgres. Returns updated row."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Fetch current state
            cur.execute("SELECT * FROM thesis_threads WHERE id = %s", (thread_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Thread {thread_id} not found")

            updates = []
            params = []

            # Evidence append
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            evidence_line = f"[{timestamp}] [{source}] ({evidence_direction}) {new_evidence}"

            if evidence_direction in ("for", "mixed"):
                existing = row["evidence_for"] or ""
                new_text = f"{existing}\n+ {new_evidence}" if existing else f"+ {new_evidence}"
                updates.append("evidence_for = %s")
                params.append(new_text)

            if evidence_direction in ("against", "mixed"):
                existing = row["evidence_against"] or ""
                new_text = f"{existing}\n? {new_evidence}" if existing else f"? {new_evidence}"
                updates.append("evidence_against = %s")
                params.append(new_text)

            # Conviction
            if conviction:
                updates.append("conviction = %s")
                params.append(conviction)

            # Key questions JSON update
            kq = row["key_questions_json"] or {"open": [], "answered": []}
            if isinstance(kq, str):
                kq = json.loads(kq)
            if new_key_questions:
                kq["open"].extend(new_key_questions)
            if answered_questions:
                for aq in answered_questions:
                    # Move matching open questions to answered
                    remaining = []
                    for oq in kq["open"]:
                        if aq.lower() in oq.lower() or oq.lower() in aq.lower():
                            kq["answered"].append(oq)
                        else:
                            remaining.append(oq)
                    kq["open"] = remaining
            if new_key_questions or answered_questions:
                updates.append("key_questions_json = %s::jsonb")
                params.append(json.dumps(kq))
                updates.append("key_question_summary = %s")
                params.append(f"{len(kq['open'])} open, {len(kq['answered'])} answered")

            # Investment implications
            if investment_implications:
                existing = row["investment_implications"] or ""
                new_text = f"{existing}\n{investment_implications}" if existing else investment_implications
                updates.append("investment_implications = %s")
                params.append(new_text)

            # Key companies
            if key_companies:
                existing = row["key_companies"] or ""
                if key_companies not in existing:
                    new_text = f"{existing}, {key_companies}" if existing else key_companies
                    updates.append("key_companies = %s")
                    params.append(new_text)

            # Notion page ID (set if we get it back from Notion create)
            if notion_page_id:
                updates.append("notion_page_id = %s")
                params.append(notion_page_id)

            # Always update timestamp
            updates.append("updated_at = NOW()")

            if updates:
                params.append(thread_id)
                cur.execute(
                    f"UPDATE thesis_threads SET {', '.join(updates)} WHERE id = %s RETURNING *",
                    params,
                )
                row = dict(cur.fetchone())

        conn.commit()
        return row
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def find_thread_by_name(name: str) -> Optional[dict[str, Any]]:
    """Find a thread by partial name match (case-insensitive)."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM thesis_threads WHERE LOWER(thread_name) LIKE %s ORDER BY updated_at DESC LIMIT 1",
                (f"%{name.lower()}%",),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def get_all_threads() -> list[dict[str, Any]]:
    """Get all non-archived thesis threads."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM thesis_threads WHERE status != 'Archived' ORDER BY updated_at DESC"
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Sync helpers
# ---------------------------------------------------------------------------


def set_notion_page_id(thread_id: int, notion_page_id: str) -> None:
    """Link a Postgres thread to its Notion page."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE thesis_threads SET notion_page_id = %s, last_synced_at = NOW() WHERE id = %s",
                (notion_page_id, thread_id),
            )
        conn.commit()
    finally:
        conn.close()


def mark_synced(thread_id: int) -> None:
    """Mark a thread as synced with Notion."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE thesis_threads SET last_synced_at = NOW() WHERE id = %s",
                (thread_id,),
            )
        conn.commit()
    finally:
        conn.close()


def update_status_from_notion(notion_page_id: str, status: str) -> None:
    """Update the Status field from Notion (human-owned field)."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE thesis_threads SET status = %s, last_synced_at = NOW() WHERE notion_page_id = %s",
                (status, notion_page_id),
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Sync queue
# ---------------------------------------------------------------------------


def enqueue_sync(table_name: str, record_id: int, operation: str, payload: dict) -> int:
    """Add a failed Notion write to the retry queue."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sync_queue (table_name, record_id, operation, payload)
                VALUES (%s, %s, %s, %s::jsonb)
                RETURNING id
                """,
                (table_name, record_id, operation, json.dumps(payload)),
            )
            queue_id = cur.fetchone()[0]
        conn.commit()
        return queue_id
    finally:
        conn.close()


def get_pending_syncs(limit: int = 10) -> list[dict[str, Any]]:
    """Get pending sync items ready for retry."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM sync_queue
                WHERE attempts < 5 AND next_retry_at <= NOW()
                ORDER BY created_at ASC
                LIMIT %s
                """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def mark_sync_done(queue_id: int) -> None:
    """Remove a completed sync item."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sync_queue WHERE id = %s", (queue_id,))
        conn.commit()
    finally:
        conn.close()


def mark_sync_failed(queue_id: int, error: str) -> None:
    """Increment attempt count and set backoff for next retry."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sync_queue
                SET attempts = attempts + 1,
                    last_error = %s,
                    next_retry_at = NOW() + (INTERVAL '1 minute' * POWER(2, attempts))
                WHERE id = %s
                """,
                (error, queue_id),
            )
        conn.commit()
    finally:
        conn.close()
