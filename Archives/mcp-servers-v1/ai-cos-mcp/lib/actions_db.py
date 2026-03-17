"""Postgres backing store for Actions Queue.

Bidirectional sync: droplet creates proposals (write-ahead to Postgres, push to Notion).
Notion status changes (accept/dismiss) pull back to Postgres.
Conflict resolution: field-level last-writer-wins using timestamps.
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


def create_action(
    action: str,
    action_type: str = "",
    priority: str = "",
    source: str = "",
    assigned_to: str = "",
    created_by: str = "",
    reasoning: str = "",
    source_content: str = "",
    thesis_connection: str = "",
    relevance_score: float | None = None,
    company_notion_id: str | None = None,
    source_digest_notion_id: str | None = None,
    notion_page_id: str | None = None,
    scoring_factors: dict | None = None,
) -> dict[str, Any]:
    """Insert a new action into Postgres. Returns the row as a dict."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO actions_queue
                    (action, action_type, status, priority, source, assigned_to,
                     created_by, reasoning, source_content, thesis_connection,
                     relevance_score, company_notion_id, source_digest_notion_id,
                     notion_page_id, scoring_factors, last_local_edit)
                VALUES (%s, %s, 'Proposed', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
                RETURNING *
                """,
                (
                    action,
                    action_type,
                    priority,
                    source,
                    assigned_to,
                    created_by,
                    reasoning,
                    source_content,
                    thesis_connection,
                    relevance_score,
                    company_notion_id,
                    source_digest_notion_id,
                    notion_page_id,
                    json.dumps(scoring_factors or {}),
                ),
            )
            row = dict(cur.fetchone())
        conn.commit()
        return row
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def update_action_status(
    action_id: int,
    status: str,
    outcome: str | None = None,
    source: str = "local",
) -> dict[str, Any]:
    """Update action status (and optionally outcome). Returns updated row."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            updates = ["status = %s", "updated_at = NOW()"]
            params: list[Any] = [status]

            if source == "local":
                updates.append("last_local_edit = NOW()")
            else:
                updates.append("last_notion_edit = NOW()")
                updates.append("last_synced_at = NOW()")

            if outcome:
                updates.append("outcome = %s")
                params.append(outcome)

            params.append(action_id)
            cur.execute(
                f"UPDATE actions_queue SET {', '.join(updates)} WHERE id = %s RETURNING *",
                params,
            )
            row = cur.fetchone()
        conn.commit()
        return dict(row) if row else {}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def find_action_by_notion_id(notion_page_id: str) -> Optional[dict[str, Any]]:
    """Find an action by its Notion page ID."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM actions_queue WHERE notion_page_id = %s",
                (notion_page_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def get_actions(status: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Get actions, optionally filtered by status."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if status:
                cur.execute(
                    "SELECT * FROM actions_queue WHERE status = %s ORDER BY created_at DESC LIMIT %s",
                    (status, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM actions_queue ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_unsynced_actions() -> list[dict[str, Any]]:
    """Get actions that were created locally but not yet pushed to Notion."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM actions_queue WHERE notion_page_id IS NULL ORDER BY created_at ASC"
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Sync helpers
# ---------------------------------------------------------------------------


def set_notion_page_id(action_id: int, notion_page_id: str) -> None:
    """Link a Postgres action to its Notion page."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE actions_queue SET notion_page_id = %s, last_synced_at = NOW() WHERE id = %s",
                (notion_page_id, action_id),
            )
        conn.commit()
    finally:
        conn.close()


def upsert_from_notion(
    notion_page_id: str,
    action: str,
    action_type: str,
    status: str,
    priority: str,
    source: str,
    assigned_to: str,
    created_by: str,
    reasoning: str,
    source_content: str,
    thesis_connection: str,
    relevance_score: float | None,
    outcome: str,
) -> dict[str, Any]:
    """Upsert an action from Notion data. Used during sync pull.

    For existing rows: only updates Outcome (human-owned field from Notion).
    Status is NOT synced from Notion — it's managed by MCP tools / Action Frontend.
    For new rows (initial seed): inserts all fields.
    """
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Check if exists
            cur.execute(
                "SELECT * FROM actions_queue WHERE notion_page_id = %s",
                (notion_page_id,),
            )
            existing = cur.fetchone()

            if existing:
                # Only sync Outcome from Notion (human-owned feedback field)
                # Status, Priority, etc. are managed locally — not overwritten
                if outcome and outcome != (existing["outcome"] or ""):
                    cur.execute(
                        """
                        UPDATE actions_queue SET
                            outcome = %s, last_notion_edit = NOW(), last_synced_at = NOW(),
                            updated_at = NOW()
                        WHERE notion_page_id = %s RETURNING *
                        """,
                        (outcome, notion_page_id),
                    )
                    row = dict(cur.fetchone())
                else:
                    # Nothing changed — just mark synced
                    cur.execute(
                        "UPDATE actions_queue SET last_synced_at = NOW() WHERE notion_page_id = %s RETURNING *",
                        (notion_page_id,),
                    )
                    row = dict(cur.fetchone())
            else:
                # New action from Notion (manual creation or initial seed) — take all fields
                cur.execute(
                    """
                    INSERT INTO actions_queue
                        (notion_page_id, action, action_type, status, priority, source,
                         assigned_to, created_by, reasoning, source_content,
                         thesis_connection, relevance_score, outcome,
                         last_notion_edit, last_synced_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING *
                    """,
                    (
                        notion_page_id, action, action_type, status, priority, source,
                        assigned_to, created_by, reasoning, source_content,
                        thesis_connection, relevance_score, outcome,
                    ),
                )
                row = dict(cur.fetchone())

        conn.commit()
        return row
    finally:
        conn.close()
