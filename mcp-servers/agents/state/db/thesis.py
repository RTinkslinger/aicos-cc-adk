"""Thesis threads DB operations — read/create/update against Postgres."""

from __future__ import annotations

from state.db.connection import get_pool


async def get_threads() -> list[dict]:
    """Fetch all thesis threads, ordered by most recently updated."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, name, core_thesis, conviction, status,
               evidence_for, evidence_against, key_questions,
               notion_page_id, notion_synced, created_at, updated_at
        FROM thesis_threads
        ORDER BY updated_at DESC
        """
    )
    return [dict(row) for row in rows]


async def create_thread(name: str, core_thesis: str) -> dict:
    """Create a new thesis thread with notion_synced=FALSE.

    Sync Agent will pick up the unsynced row and push to Notion.
    """
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO thesis_threads (name, core_thesis, notion_synced)
        VALUES ($1, $2, FALSE)
        RETURNING id, name, core_thesis, conviction, status,
                  evidence_for, evidence_against, key_questions,
                  notion_page_id, notion_synced, created_at, updated_at
        """,
        name,
        core_thesis,
    )
    return dict(row)


async def update_thread(thesis_name: str, evidence: str, direction: str = "for") -> dict:
    """Append evidence to a thesis thread.

    Args:
        thesis_name: Name of the thesis thread to update.
        evidence: New evidence text to append.
        direction: One of 'for', 'against', or 'mixed'.
            - 'for' appends to evidence_for
            - 'against' appends to evidence_against
            - 'mixed' appends to both evidence_for and evidence_against

    Sets notion_synced=FALSE so Sync Agent picks up the change.
    """
    pool = await get_pool()

    if direction == "for":
        row = await pool.fetchrow(
            """
            UPDATE thesis_threads
            SET evidence_for = CASE
                    WHEN evidence_for = '' THEN $2
                    ELSE evidence_for || E'\\n' || $2
                END,
                notion_synced = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = $1
            RETURNING id, name, core_thesis, conviction, status,
                      evidence_for, evidence_against, key_questions,
                      notion_page_id, notion_synced, created_at, updated_at
            """,
            thesis_name,
            evidence,
        )
    elif direction == "against":
        row = await pool.fetchrow(
            """
            UPDATE thesis_threads
            SET evidence_against = CASE
                    WHEN evidence_against = '' THEN $2
                    ELSE evidence_against || E'\\n' || $2
                END,
                notion_synced = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = $1
            RETURNING id, name, core_thesis, conviction, status,
                      evidence_for, evidence_against, key_questions,
                      notion_page_id, notion_synced, created_at, updated_at
            """,
            thesis_name,
            evidence,
        )
    elif direction == "mixed":
        row = await pool.fetchrow(
            """
            UPDATE thesis_threads
            SET evidence_for = CASE
                    WHEN evidence_for = '' THEN $2
                    ELSE evidence_for || E'\\n' || $2
                END,
                evidence_against = CASE
                    WHEN evidence_against = '' THEN $2
                    ELSE evidence_against || E'\\n' || $2
                END,
                notion_synced = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = $1
            RETURNING id, name, core_thesis, conviction, status,
                      evidence_for, evidence_against, key_questions,
                      notion_page_id, notion_synced, created_at, updated_at
            """,
            thesis_name,
            evidence,
        )
    else:
        raise ValueError(f"Invalid direction '{direction}'. Must be 'for', 'against', or 'mixed'.")

    if row is None:
        raise ValueError(f"Thesis thread '{thesis_name}' not found.")

    return dict(row)
