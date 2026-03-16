"""CAI inbox DB operations — message posting and retrieval."""

from __future__ import annotations

import json

from state.db.connection import get_pool


async def post_message(type: str, content: str, metadata: dict | None = None) -> dict:
    """Post a message to the CAI inbox.

    Args:
        type: Message type (e.g. track_source, research_request, thesis_update,
              watch_list_add, watch_list_remove, general).
        content: Message body text.
        metadata: Optional JSON-serializable metadata dict.

    Returns:
        The newly created inbox row as a dict.
    """
    pool = await get_pool()
    meta_json = json.dumps(metadata) if metadata else "{}"
    row = await pool.fetchrow(
        """
        INSERT INTO cai_inbox (type, content, metadata)
        VALUES ($1, $2, $3::jsonb)
        RETURNING id, type, content, metadata, processed, processed_at, created_at
        """,
        type,
        content,
        meta_json,
    )
    return dict(row)


async def get_pending() -> list[dict]:
    """Fetch all unprocessed inbox messages, oldest first."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, type, content, metadata, processed, processed_at, created_at
        FROM cai_inbox
        WHERE processed = FALSE
        ORDER BY created_at
        """
    )
    return [dict(row) for row in rows]


async def mark_processed(message_id: int) -> dict | None:
    """Mark an inbox message as processed.

    Returns:
        The updated row as a dict, or None if the message_id was not found.
    """
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        UPDATE cai_inbox
        SET processed = TRUE, processed_at = CURRENT_TIMESTAMP
        WHERE id = $1
        RETURNING id, type, content, metadata, processed, processed_at, created_at
        """,
        message_id,
    )
    return dict(row) if row else None
