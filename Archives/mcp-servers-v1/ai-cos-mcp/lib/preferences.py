from __future__ import annotations

"""Preference Store — queries and writes to Postgres action_outcomes table.

The action_outcomes table tracks every accept/reject decision with scoring
factor snapshots, enabling preference learning over time.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")


def _get_conn():
    return psycopg2.connect(DATABASE_URL)


def log_outcome(
    action_text: str,
    action_type: str,
    outcome: str,
    score: float,
    scoring_factors: dict[str, float],
    source_digest_slug: Optional[str] = None,
    company: Optional[str] = None,
    thesis_thread: Optional[str] = None,
) -> int:
    """Log an action outcome to the preference store.

    Args:
        action_text: The action description
        action_type: e.g. "research", "meeting", "follow-up", "content"
        outcome: "proposed", "accepted", "dismissed", "completed"
        score: The computed action score (0-10)
        scoring_factors: Dict of factor_name -> value used in scoring
        source_digest_slug: Optional slug of the source content digest
        company: Optional company name
        thesis_thread: Optional thesis thread name

    Returns:
        The inserted row ID.
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO action_outcomes
                (action_text, action_type, outcome, score, scoring_factors,
                 source_digest_slug, company, thesis_thread, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                action_text,
                action_type,
                outcome,
                score,
                json.dumps(scoring_factors),
                source_digest_slug,
                company,
                thesis_thread,
                datetime.now(timezone.utc),
            ),
        )
        row_id = cur.fetchone()[0]
        conn.commit()
        return row_id
    finally:
        conn.close()


def get_preferences(
    limit: int = 50,
    action_type: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Get recent action outcomes for preference learning injection.

    Returns recent accepted/dismissed actions with their scoring factors,
    enabling calibration of future scoring.
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        query = """
            SELECT action_text, action_type, outcome, score, scoring_factors,
                   company, thesis_thread, created_at
            FROM action_outcomes
            WHERE outcome IN ('accepted', 'dismissed')
        """
        params: list[Any] = []
        if action_type:
            query += " AND action_type = %s"
            params.append(action_type)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        rows = []
        for row in cur.fetchall():
            row_dict = dict(zip(columns, row))
            if isinstance(row_dict.get("scoring_factors"), str):
                row_dict["scoring_factors"] = json.loads(row_dict["scoring_factors"])
            if row_dict.get("created_at"):
                row_dict["created_at"] = row_dict["created_at"].isoformat()
            rows.append(row_dict)
        return rows
    finally:
        conn.close()


def get_preference_summary() -> dict[str, Any]:
    """Get aggregate stats for preference injection into prompts.

    Returns acceptance rates by action type and thesis thread.
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT action_type,
                   COUNT(*) FILTER (WHERE outcome = 'accepted') as accepted,
                   COUNT(*) FILTER (WHERE outcome = 'dismissed') as dismissed,
                   AVG(score) FILTER (WHERE outcome = 'accepted') as avg_accepted_score,
                   AVG(score) FILTER (WHERE outcome = 'dismissed') as avg_dismissed_score
            FROM action_outcomes
            GROUP BY action_type
            """
        )
        by_type = {}
        for row in cur.fetchall():
            by_type[row[0]] = {
                "accepted": row[1],
                "dismissed": row[2],
                "avg_accepted_score": round(row[3], 2) if row[3] else None,
                "avg_dismissed_score": round(row[4], 2) if row[4] else None,
            }
        return {"by_action_type": by_type}
    finally:
        conn.close()
