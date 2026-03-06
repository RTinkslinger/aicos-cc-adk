"""Change detection engine for Data Sovereignty sync.

Compares Notion state vs Postgres state and logs diffs to change_events table.
Changes can trigger action generation (Phase 5).
"""

from __future__ import annotations

import os
from typing import Any

import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL", "")


def _get_conn():
    return psycopg2.connect(DATABASE_URL)


def detect_thesis_changes(notion_threads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare Notion thesis state against Postgres and log changes.

    Detects: Status changes, Conviction changes (from other surfaces).
    Returns list of detected changes.
    """
    conn = _get_conn()
    changes = []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            for thread in notion_threads:
                notion_page_id = thread.get("id", "")
                if not notion_page_id:
                    continue

                cur.execute(
                    "SELECT * FROM thesis_threads WHERE notion_page_id = %s",
                    (notion_page_id,),
                )
                pg_row = cur.fetchone()
                if not pg_row:
                    continue

                # Check status (human-owned field)
                notion_status = thread.get("status", "")
                if notion_status and notion_status != pg_row["status"]:
                    _log_change(
                        cur, "thesis_threads", pg_row["id"], notion_page_id,
                        "status", pg_row["status"], notion_status,
                    )
                    changes.append({
                        "table": "thesis_threads",
                        "name": thread.get("name", ""),
                        "field": "status",
                        "old": pg_row["status"],
                        "new": notion_status,
                    })

                # Check conviction (could change from ContentAgent or other surface)
                notion_conviction = thread.get("conviction", "")
                if notion_conviction and notion_conviction != pg_row["conviction"]:
                    _log_change(
                        cur, "thesis_threads", pg_row["id"], notion_page_id,
                        "conviction", pg_row["conviction"], notion_conviction,
                    )
                    changes.append({
                        "table": "thesis_threads",
                        "name": thread.get("name", ""),
                        "field": "conviction",
                        "old": pg_row["conviction"],
                        "new": notion_conviction,
                    })

        conn.commit()
    finally:
        conn.close()

    return changes


def detect_action_changes(notion_actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare Notion actions state against Postgres and log changes.

    Detects: Status changes (Proposed→Accepted, etc.), Priority changes.
    """
    conn = _get_conn()
    changes = []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            for action in notion_actions:
                notion_page_id = action.get("id", "")
                if not notion_page_id:
                    continue

                cur.execute(
                    "SELECT * FROM actions_queue WHERE notion_page_id = %s",
                    (notion_page_id,),
                )
                pg_row = cur.fetchone()
                if not pg_row:
                    continue

                # Status change
                notion_status = action.get("status", "")
                if notion_status and notion_status != pg_row["status"]:
                    _log_change(
                        cur, "actions_queue", pg_row["id"], notion_page_id,
                        "status", pg_row["status"], notion_status,
                    )
                    changes.append({
                        "table": "actions_queue",
                        "action": action.get("action", ""),
                        "field": "status",
                        "old": pg_row["status"],
                        "new": notion_status,
                    })

                # Priority change
                notion_priority = action.get("priority", "")
                if notion_priority and notion_priority != pg_row["priority"]:
                    _log_change(
                        cur, "actions_queue", pg_row["id"], notion_page_id,
                        "priority", pg_row["priority"], notion_priority,
                    )
                    changes.append({
                        "table": "actions_queue",
                        "action": action.get("action", ""),
                        "field": "priority",
                        "old": pg_row["priority"],
                        "new": notion_priority,
                    })

        conn.commit()
    finally:
        conn.close()

    return changes


def get_unprocessed_changes(limit: int = 50) -> list[dict[str, Any]]:
    """Get unprocessed change events for action generation."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM change_events WHERE NOT processed ORDER BY detected_at ASC LIMIT %s",
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def mark_changes_processed(change_ids: list[int]) -> None:
    """Mark change events as processed."""
    if not change_ids:
        return
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE change_events SET processed = TRUE WHERE id = ANY(%s)",
                (change_ids,),
            )
        conn.commit()
    finally:
        conn.close()


def _log_change(
    cur, table_name: str, record_id: int, notion_page_id: str,
    field_name: str, old_value: str, new_value: str,
) -> None:
    """Insert a change event into the log."""
    cur.execute(
        """
        INSERT INTO change_events (table_name, record_id, notion_page_id, field_name, old_value, new_value)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (table_name, record_id, notion_page_id, field_name, old_value, new_value),
    )
