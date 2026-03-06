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

    Detects: Outcome changes (human feedback: Unknown→Helpful→Gold).
    Status is NOT synced from Notion — it's managed by MCP tools / Action Frontend.
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

                # Outcome change (human-owned field, synced FROM Notion)
                notion_outcome = action.get("outcome", "")
                if notion_outcome and notion_outcome != (pg_row["outcome"] or ""):
                    _log_change(
                        cur, "actions_queue", pg_row["id"], notion_page_id,
                        "outcome", pg_row["outcome"] or "", notion_outcome,
                    )
                    changes.append({
                        "table": "actions_queue",
                        "action": action.get("action", ""),
                        "field": "outcome",
                        "old": pg_row["outcome"] or "",
                        "new": notion_outcome,
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


def generate_actions_from_changes(changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate proposed actions from unprocessed change events.

    Rules:
    - Thesis conviction → High: propose "Review portfolio for thesis X investment opportunities"
    - Thesis status Active → Parked: propose "Archive actions connected to thesis X"
    - Thesis status Parked/Archived → Active: propose "Resurface actions for reactivated thesis X"
    - Action outcome → Gold: propose "Find similar actions to the Gold-rated one"
    """
    from lib.actions_db import create_action

    generated = []
    for change in changes:
        table = change.get("table_name", "")
        field = change.get("field_name", "")
        new_val = change.get("new_value", "")
        old_val = change.get("old_value", "")
        record_id = change.get("record_id", 0)

        action_text = None
        action_type = ""
        priority = ""
        reasoning = ""

        if table == "thesis_threads" and field == "conviction" and new_val == "High":
            # Look up thread name
            thread_name = _get_thread_name(record_id)
            action_text = f"Review portfolio and pipeline for '{thread_name}' investment opportunities — conviction just reached High"
            action_type = "Research"
            priority = "P1 - Next"
            reasoning = f"Thesis '{thread_name}' conviction moved from {old_val} to High. High-conviction thesis should trigger active deal sourcing."

        elif table == "thesis_threads" and field == "status":
            thread_name = _get_thread_name(record_id)
            if new_val in ("Parked", "Archived") and old_val in ("Active", "Exploring"):
                action_text = f"Review and deprioritize pending actions connected to '{thread_name}' (now {new_val})"
                action_type = "Thesis Update"
                priority = "P2 - Later"
                reasoning = f"Thesis '{thread_name}' moved from {old_val} to {new_val}. Connected actions may no longer be relevant."
            elif new_val in ("Active", "Exploring") and old_val in ("Parked", "Archived"):
                action_text = f"Resurface and review actions for reactivated thesis '{thread_name}'"
                action_type = "Thesis Update"
                priority = "P1 - Next"
                reasoning = f"Thesis '{thread_name}' reactivated from {old_val} to {new_val}. Check for new signals and pending actions."

        elif table == "actions_queue" and field == "outcome" and new_val == "Gold":
            action_text = f"Analyze what made action #{record_id} Gold-rated — find similar high-value patterns"
            action_type = "Research"
            priority = "P2 - Later"
            reasoning = f"Action outcome rated Gold. Understanding what makes actions valuable improves future scoring."

        if action_text:
            try:
                row = create_action(
                    action=action_text,
                    action_type=action_type,
                    priority=priority,
                    source="SyncAgent",
                    created_by="AI CoS",
                    assigned_to="Aakash",
                    reasoning=reasoning,
                )
                generated.append({
                    "action": action_text,
                    "priority": priority,
                    "trigger": f"{table}.{field}: {old_val} → {new_val}",
                    "pg_id": row["id"],
                })
            except Exception as e:
                print(f"[ChangeDetection] Failed to generate action: {e}")

    return generated


def _get_thread_name(record_id: int) -> str:
    """Look up thesis thread name by Postgres ID."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT thread_name FROM thesis_threads WHERE id = %s", (record_id,))
            row = cur.fetchone()
            return row[0] if row else f"Thread #{record_id}"
    finally:
        conn.close()


def get_sync_status() -> dict[str, Any]:
    """Get unified sync status dashboard."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Thesis sync status
            cur.execute("SELECT COUNT(*) as total, MAX(last_synced_at) as last_sync FROM thesis_threads")
            thesis = dict(cur.fetchone())

            # Actions sync status
            cur.execute("SELECT COUNT(*) as total, MAX(last_synced_at) as last_sync FROM actions_queue")
            actions = dict(cur.fetchone())

            # Unsynced actions (no Notion page ID)
            cur.execute("SELECT COUNT(*) as count FROM actions_queue WHERE notion_page_id IS NULL")
            unsynced_actions = cur.fetchone()["count"]

            # Sync queue depth
            cur.execute("SELECT COUNT(*) as pending FROM sync_queue WHERE status = 'pending'")
            queue_pending = cur.fetchone()["pending"]

            cur.execute("SELECT COUNT(*) as failed FROM sync_queue WHERE status = 'failed'")
            queue_failed = cur.fetchone()["failed"]

            # Recent changes
            cur.execute("SELECT COUNT(*) as unprocessed FROM change_events WHERE NOT processed")
            unprocessed_changes = cur.fetchone()["unprocessed"]

            cur.execute("""
                SELECT table_name, field_name, old_value, new_value, detected_at
                FROM change_events ORDER BY detected_at DESC LIMIT 5
            """)
            recent_changes = [dict(r) for r in cur.fetchall()]

            return {
                "thesis": {
                    "total_threads": thesis["total"],
                    "last_sync": str(thesis["last_sync"]) if thesis["last_sync"] else None,
                },
                "actions": {
                    "total_actions": actions["total"],
                    "last_sync": str(actions["last_sync"]) if actions["last_sync"] else None,
                    "unsynced_to_notion": unsynced_actions,
                },
                "sync_queue": {
                    "pending": queue_pending,
                    "failed": queue_failed,
                },
                "changes": {
                    "unprocessed": unprocessed_changes,
                    "recent": recent_changes,
                },
            }
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
