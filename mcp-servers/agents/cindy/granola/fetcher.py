#!/usr/bin/env python3
"""
Thin Granola Fetcher for Cindy — Plumbing Only.

Reads Granola meeting data (from MCP tool output or pre-fetched JSON files),
parses into structured format, and stages raw data in interaction_staging.
NO signal extraction, NO people resolution, NO obligation detection.

Datum Agent handles: attendee resolution, entity linking, writing to interactions.
Cindy Agent handles: LLM-based signal extraction, obligation reasoning, action creation.

Usage:
    echo '{"meetings": [...]}' | python3 -m cindy.granola.fetcher
    python3 -m cindy.granola.fetcher --file meetings.json
    python3 -m cindy.granola.fetcher --file meetings.json --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cindy.granola.fetcher")

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

STATE_DIR = Path(__file__).parent.parent / "state"
LAST_PROCESSED_FILE = STATE_DIR / "granola_last_processed.json"

AAKASH_EMAILS = {"ak@z47.com", "aakash@z47.com", "aakash@devc.fund"}
AAKASH_NAMES = {"aakash", "aakash kumar"}


# ---------------------------------------------------------------------------
# Data Models (pure data — no intelligence)
# ---------------------------------------------------------------------------


@dataclass
class GranolaMeeting:
    """Parsed Granola meeting data."""

    meeting_id: str
    title: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attendees: list[dict[str, str]] = field(default_factory=list)
    transcript: str = ""
    ai_summary: str = ""
    action_items: list[str] = field(default_factory=list)
    private_notes: str = ""
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_minutes(self) -> Optional[int]:
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None

    @property
    def attendee_names(self) -> list[str]:
        return [a.get("name", "") for a in self.attendees if a.get("name")]

    @property
    def attendee_emails(self) -> list[str]:
        return [a.get("email", "") for a in self.attendees if a.get("email")]

    @property
    def source_id(self) -> str:
        return f"granola_{self.meeting_id}"

    def to_raw_json(self) -> dict[str, Any]:
        """Convert to raw JSON for staging."""
        return {
            "meeting_id": self.meeting_id,
            "title": self.title,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "attendees": self.attendees,
            "attendee_names": self.attendee_names,
            "attendee_emails": self.attendee_emails,
            "transcript": self.transcript[:100000] if self.transcript else "",
            "ai_summary": self.ai_summary,
            "action_items": self.action_items,
            "private_notes": self.private_notes,
        }


# ---------------------------------------------------------------------------
# Parser (pure data transformation — no intelligence)
# ---------------------------------------------------------------------------


def parse_granola_meeting(raw: dict[str, Any]) -> GranolaMeeting:
    """Parse raw Granola meeting JSON."""
    start_time = None
    end_time = None

    start_str = raw.get("start_time") or raw.get("startTime") or raw.get("start")
    end_str = raw.get("end_time") or raw.get("endTime") or raw.get("end")

    if start_str:
        try:
            start_time = datetime.fromisoformat(str(start_str).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    if end_str:
        try:
            end_time = datetime.fromisoformat(str(end_str).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    attendees_raw = raw.get("attendees") or raw.get("participants") or []
    attendees: list[dict[str, str]] = []
    for att in attendees_raw:
        if isinstance(att, dict):
            attendees.append({
                "name": att.get("name", att.get("displayName", "")),
                "email": att.get("email", ""),
            })
        elif isinstance(att, str):
            attendees.append({"name": att, "email": ""})

    action_items_raw = raw.get("action_items") or raw.get("actionItems") or []
    action_items: list[str] = []
    for item in action_items_raw:
        if isinstance(item, dict):
            action_items.append(item.get("text", item.get("description", str(item))))
        elif isinstance(item, str):
            action_items.append(item)

    return GranolaMeeting(
        meeting_id=raw.get("id") or raw.get("meeting_id") or raw.get("uuid") or "",
        title=raw.get("title") or raw.get("name") or "",
        start_time=start_time,
        end_time=end_time,
        attendees=attendees,
        transcript=raw.get("transcript") or "",
        ai_summary=raw.get("summary") or raw.get("ai_summary") or raw.get("notes") or "",
        action_items=action_items,
        private_notes=raw.get("private_notes") or raw.get("privateNotes") or "",
        raw_data=raw,
    )


# ---------------------------------------------------------------------------
# Staging Writer
# ---------------------------------------------------------------------------


class StagingWriter:
    """Writes raw Granola data to interaction_staging table."""

    def __init__(self, database_url: str, dry_run: bool = False) -> None:
        self.database_url = database_url
        self.dry_run = dry_run
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg not installed")
        self._pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=3)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def already_staged(self, source_id: str) -> bool:
        if self._pool is None:
            return False
        row = await self._pool.fetchrow(
            "SELECT id FROM interaction_staging WHERE source = 'granola' AND source_id = $1",
            source_id,
        )
        return row is not None

    async def stage(self, meeting: GranolaMeeting) -> Optional[int]:
        if self.dry_run:
            logger.info("[DRY RUN] Would stage meeting: %s — %s", meeting.meeting_id, meeting.title)
            return None
        if self._pool is None:
            raise RuntimeError("Database not connected")

        row = await self._pool.fetchrow(
            """
            INSERT INTO interaction_staging (source, source_id, raw_data)
            VALUES ('granola', $1, $2::jsonb)
            ON CONFLICT (source, source_id) DO NOTHING
            RETURNING id
            """,
            meeting.source_id,
            json.dumps(meeting.to_raw_json()),
        )
        return row["id"] if row else None


# ---------------------------------------------------------------------------
# Main Fetcher
# ---------------------------------------------------------------------------


async def fetch_and_stage(
    file_path: Optional[str] = None,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Read Granola meetings from file/stdin and stage raw data."""

    # Read input
    if file_path:
        with open(file_path) as f:
            raw_input = json.load(f)
    else:
        if sys.stdin.isatty():
            logger.error("No input. Pipe JSON from Granola MCP or use --file.")
            return []
        raw_input = json.load(sys.stdin)

    # Normalize: accept {"meetings": [...]} or [...]
    if isinstance(raw_input, dict):
        meetings_raw = raw_input.get("meetings", raw_input.get("results", [raw_input]))
    elif isinstance(raw_input, list):
        meetings_raw = raw_input
    else:
        logger.error("Unexpected input format")
        return []

    logger.info("Parsed %d meetings from input", len(meetings_raw))

    database_url = os.environ.get("DATABASE_URL")
    if not database_url and not dry_run:
        logger.error("DATABASE_URL not set")
        sys.exit(1)

    writer = StagingWriter(database_url or "", dry_run=dry_run)

    try:
        if not dry_run:
            await writer.connect()

        results: list[dict[str, Any]] = []
        staged = 0
        skipped = 0

        for raw in meetings_raw:
            meeting = parse_granola_meeting(raw)
            if not meeting.meeting_id:
                logger.warning("Skipping meeting with no ID")
                continue

            if not dry_run and await writer.already_staged(meeting.source_id):
                skipped += 1
                continue

            staging_id = await writer.stage(meeting)
            results.append({
                "meeting_id": meeting.meeting_id,
                "title": meeting.title,
                "attendees": meeting.attendee_names,
                "duration_minutes": meeting.duration_minutes,
                "staging_id": staging_id,
                "action": "staged",
            })
            staged += 1

        logger.info("Granola fetch complete: %d staged, %d skipped", staged, skipped)

        # Update last processed timestamp
        if staged > 0 and not dry_run:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            with open(LAST_PROCESSED_FILE, "w") as f:
                json.dump({"last_processed": datetime.now(timezone.utc).isoformat()}, f)

        if dry_run:
            print(json.dumps(results, indent=2, default=str))
        return results

    finally:
        await writer.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cindy Granola Fetcher — stages raw data only")
    parser.add_argument("--file", type=str, help="Path to Granola JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    args = parser.parse_args()

    asyncio.run(fetch_and_stage(file_path=args.file, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
