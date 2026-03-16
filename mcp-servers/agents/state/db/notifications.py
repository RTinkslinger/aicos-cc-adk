"""Notifications DB operations — unread retrieval, posting, and mark-read."""

from __future__ import annotations

import json

from state.db.connection import get_pool


async def get_unread() -> list[dict]:
    """Fetch up to 50 unread notifications, newest first."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, source, type, content, metadata, read, created_at
        FROM notifications
        WHERE read = FALSE
        ORDER BY created_at DESC
        LIMIT 50
        """
    )
    return [dict(row) for row in rows]


async def post_notification(
    source: str, type: str, content: str, metadata: dict | None = None
) -> dict:
    """Create a new notification.

    Args:
        source: Origin system (e.g. content_agent, sync_agent, pipeline).
        type: Notification category (e.g. digest_ready, thesis_update, error).
        content: Human-readable notification body.
        metadata: Optional JSON-serializable metadata dict.

    Returns:
        The newly created notification row as a dict.
    """
    pool = await get_pool()
    meta_json = json.dumps(metadata) if metadata else "{}"
    row = await pool.fetchrow(
        """
        INSERT INTO notifications (source, type, content, metadata)
        VALUES ($1, $2, $3, $4::jsonb)
        RETURNING id, source, type, content, metadata, read, created_at
        """,
        source,
        type,
        content,
        meta_json,
    )
    return dict(row)


async def mark_read(notification_ids: list[int]) -> int:
    """Mark one or more notifications as read.

    Args:
        notification_ids: List of notification IDs to mark as read.

    Returns:
        Count of rows updated.
    """
    if not notification_ids:
        return 0

    pool = await get_pool()
    result = await pool.execute(
        """
        UPDATE notifications
        SET read = TRUE
        WHERE id = ANY($1::int[])
        """,
        notification_ids,
    )
    # asyncpg returns 'UPDATE N' — extract the count
    return int(result.split()[-1])
