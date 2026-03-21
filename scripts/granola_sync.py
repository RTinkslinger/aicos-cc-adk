#!/usr/bin/env python3
"""
Granola → Postgres Sync Script for Cindy.

Reads meeting data from Granola's local cache on Mac and syncs to the
interactions table in Supabase Postgres. This is the CC-to-Postgres bridge
for Surface 2 (Granola Meetings).

Two modes:
  1. Cache mode (default): Reads ~/Library/Application Support/Granola/cache-v4.json
     - Contains meeting metadata, summaries, calendar events, people
     - Does NOT contain transcripts (those require the API)
  2. MCP mode: Takes JSON piped from Granola MCP tool output
     - Used when Cindy agent has MCP access

Usage:
    # Sync from local cache (run from Mac)
    python3 scripts/granola_sync.py

    # Sync specific meetings from MCP output
    echo '{"meetings": [...]}' | python3 scripts/granola_sync.py --stdin

    # Dry run
    python3 scripts/granola_sync.py --dry-run

    # Sync to custom DB
    DATABASE_URL=... python3 scripts/granola_sync.py

Requires:
    pip3 install asyncpg
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("granola_sync")

# Granola local cache path (macOS)
GRANOLA_CACHE = Path.home() / "Library" / "Application Support" / "Granola" / "cache-v4.json"

# State file for tracking last sync
STATE_FILE = Path(__file__).parent.parent / "mcp-servers" / "agents" / "state" / "granola_last_sync.json"


def load_granola_cache() -> dict[str, Any]:
    """Load Granola cache from local filesystem."""
    if not GRANOLA_CACHE.exists():
        logger.error(f"Granola cache not found at {GRANOLA_CACHE}")
        sys.exit(1)

    with open(GRANOLA_CACHE, "r") as f:
        data = json.load(f)

    state = data.get("cache", {}).get("state", {})
    return state


def extract_meetings_from_cache(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract meeting documents from Granola cache state."""
    documents = state.get("documents", {})
    events = state.get("events", [])
    meetings_meta = state.get("meetingsMetadata", {})

    meetings = []
    for doc_id, doc in documents.items():
        if not isinstance(doc, dict):
            continue
        meeting = {
            "id": doc_id,
            "title": doc.get("title", "Untitled"),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
            "summary": doc.get("summary", ""),
            "private_notes": doc.get("private_notes", ""),
            "attendees": doc.get("attendees", []),
            "calendar_event_id": doc.get("calendar_event_id"),
            "metadata": meetings_meta.get(doc_id, {}),
        }
        meetings.append(meeting)

    logger.info(f"Extracted {len(meetings)} meetings from cache ({len(events)} calendar events)")
    return meetings


def load_last_sync() -> str | None:
    """Load last sync timestamp."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
        return data.get("last_sync")
    return None


def save_last_sync(ts: str) -> None:
    """Save last sync timestamp."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"last_sync": ts, "updated_at": datetime.now(timezone.utc).isoformat()}, f)


async def sync_meetings_to_db(
    meetings: list[dict[str, Any]],
    db_url: str,
    dry_run: bool = False,
) -> dict[str, int]:
    """Sync meetings to interactions table."""
    try:
        import asyncpg
    except ImportError:
        logger.error("asyncpg not installed. Run: pip3 install asyncpg")
        sys.exit(1)

    stats = {"inserted": 0, "skipped": 0, "errors": 0}

    if dry_run:
        for m in meetings:
            logger.info(f"[DRY RUN] Would sync: {m['title']} ({m['id']})")
            stats["skipped"] += 1
        return stats

    conn = await asyncpg.connect(db_url)
    try:
        for m in meetings:
            source_id = f"granola_{m['id']}"
            try:
                # Check if already exists
                existing = await conn.fetchval(
                    "SELECT id FROM interactions WHERE source = 'granola' AND source_id = $1",
                    source_id,
                )
                if existing:
                    stats["skipped"] += 1
                    continue

                # Insert new interaction
                raw_data = json.dumps({
                    "granola_id": m["id"],
                    "title": m["title"],
                    "attendees": m.get("attendees", []),
                    "calendar_event_id": m.get("calendar_event_id"),
                    "private_notes": m.get("private_notes", ""),
                })

                await conn.execute(
                    """INSERT INTO interactions
                    (source, source_id, participants, summary, raw_data, timestamp, action_items, created_at, updated_at)
                    VALUES ('granola', $1, $2, $3, $4::jsonb, $5, $6, NOW(), NOW())""",
                    source_id,
                    ["Aakash Kumar"],  # Granola cache doesn't have attendee names reliably
                    m.get("summary", m["title"]),
                    raw_data,
                    m.get("created_at", datetime.now(timezone.utc).isoformat()),
                    [],
                )
                stats["inserted"] += 1
                logger.info(f"Inserted: {m['title']}")

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error syncing {m['title']}: {e}")

    finally:
        await conn.close()

    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Granola meetings to Postgres")
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    parser.add_argument("--stdin", action="store_true", help="Read MCP JSON from stdin")
    parser.add_argument("--all", action="store_true", help="Sync all meetings (not just new)")
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url and not args.dry_run:
        logger.error("DATABASE_URL not set. Use --dry-run or set DATABASE_URL.")
        sys.exit(1)

    if args.stdin:
        data = json.load(sys.stdin)
        meetings = data.get("meetings", [])
        logger.info(f"Read {len(meetings)} meetings from stdin")
    else:
        state = load_granola_cache()
        meetings = extract_meetings_from_cache(state)

    if not meetings:
        logger.info("No meetings to sync.")
        return

    stats = await sync_meetings_to_db(
        meetings,
        db_url or "",
        dry_run=args.dry_run,
    )

    logger.info(f"Sync complete: {stats['inserted']} inserted, {stats['skipped']} skipped, {stats['errors']} errors")

    if stats["inserted"] > 0 and not args.dry_run:
        save_last_sync(datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    asyncio.run(main())
