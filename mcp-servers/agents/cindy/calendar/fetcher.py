#!/usr/bin/env python3
"""
Thin Calendar .ics Fetcher for Cindy — Plumbing Only.

Parses .ics files (from AgentMail attachments or local files) and stages
raw calendar event data in interaction_staging.
NO people resolution, NO pre-meeting context assembly, NO gap detection.

Datum Agent handles: attendee resolution, entity linking, writing to interactions.
Cindy Agent handles: LLM-based gap detection, pre-meeting context assembly, signal extraction.

Usage:
    python3 -m cindy.calendar.fetcher --file event.ics
    python3 -m cindy.calendar.fetcher --file event.ics --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cindy.calendar.fetcher")

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]

try:
    from icalendar import Calendar as ICalendar
except ImportError:
    ICalendar = None  # type: ignore[assignment,misc]
    logger.warning("icalendar not installed. Run: pip install icalendar")

AAKASH_EMAILS = {"ak@z47.com", "aakash@z47.com", "aakash@devc.fund"}


@dataclass
class CalendarEvent:
    """Parsed calendar event."""

    uid: str
    summary: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    organizer: Optional[str] = None
    attendees: list[dict[str, str]] = field(default_factory=list)
    conference_url: Optional[str] = None
    status: str = "confirmed"

    @property
    def source_id(self) -> str:
        return f"cal_{self.uid}"

    def to_raw_json(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "summary": self.summary,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "location": self.location,
            "description": self.description[:5000] if self.description else None,
            "organizer": self.organizer,
            "attendees": self.attendees,
            "conference_url": self.conference_url,
            "status": self.status,
        }


def parse_ics(ics_content: str) -> list[CalendarEvent]:
    """Parse .ics content into CalendarEvent objects."""
    if ICalendar is None:
        logger.error("icalendar not installed")
        return []

    try:
        cal = ICalendar.from_ical(ics_content)
    except Exception as e:
        logger.error("Failed to parse .ics: %s", e)
        return []

    events: list[CalendarEvent] = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        uid = str(component.get("UID", ""))
        if not uid:
            continue

        # Parse times
        start_time = None
        end_time = None
        dtstart = component.get("DTSTART")
        dtend = component.get("DTEND")

        if dtstart:
            dt = dtstart.dt
            if isinstance(dt, datetime):
                start_time = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            else:
                start_time = datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc)

        if dtend:
            dt = dtend.dt
            if isinstance(dt, datetime):
                end_time = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            else:
                end_time = datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc)

        # Parse attendees
        attendees: list[dict[str, str]] = []
        att_list = component.get("ATTENDEE")
        if att_list:
            if not isinstance(att_list, list):
                att_list = [att_list]
            for att in att_list:
                email = str(att).replace("MAILTO:", "").replace("mailto:", "").strip()
                name = str(att.params.get("CN", "")) if hasattr(att, "params") else ""
                status = str(att.params.get("PARTSTAT", "NEEDS-ACTION")) if hasattr(att, "params") else ""
                if email and email.lower() not in AAKASH_EMAILS:
                    attendees.append({"email": email, "name": name, "status": status})

        # Parse organizer
        organizer = None
        org = component.get("ORGANIZER")
        if org:
            organizer = str(org).replace("MAILTO:", "").replace("mailto:", "").strip()

        # Conference URL
        conference_url = None
        loc = str(component.get("LOCATION", ""))
        desc = str(component.get("DESCRIPTION", ""))
        for text in [loc, desc]:
            if "zoom.us" in text or "meet.google.com" in text or "teams.microsoft.com" in text:
                import re
                url_match = re.search(r"https?://[^\s<>\"]+", text)
                if url_match:
                    conference_url = url_match.group(0)
                    break

        events.append(CalendarEvent(
            uid=uid,
            summary=str(component.get("SUMMARY", "")),
            start_time=start_time,
            end_time=end_time,
            location=loc if loc else None,
            description=desc if desc else None,
            organizer=organizer,
            attendees=attendees,
            conference_url=conference_url,
            status=str(component.get("STATUS", "CONFIRMED")).lower(),
        ))

    return events


class StagingWriter:
    """Writes raw calendar data to interaction_staging."""

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

    async def stage(self, event: CalendarEvent) -> Optional[int]:
        if self.dry_run:
            logger.info("[DRY RUN] Would stage event: %s — %s", event.uid, event.summary)
            return None
        if self._pool is None:
            raise RuntimeError("Database not connected")

        row = await self._pool.fetchrow(
            """
            INSERT INTO interaction_staging (source, source_id, raw_data)
            VALUES ('calendar', $1, $2::jsonb)
            ON CONFLICT (source, source_id) DO NOTHING
            RETURNING id
            """,
            event.source_id,
            json.dumps(event.to_raw_json()),
        )
        return row["id"] if row else None


async def fetch_and_stage(file_path: str, dry_run: bool = False) -> list[dict[str, Any]]:
    """Parse .ics file and stage raw data."""
    ics_path = Path(file_path)
    if not ics_path.exists():
        logger.error("File not found: %s", file_path)
        return []

    ics_content = ics_path.read_text(encoding="utf-8", errors="replace")
    events = parse_ics(ics_content)
    logger.info("Parsed %d events from %s", len(events), file_path)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url and not dry_run:
        logger.error("DATABASE_URL not set")
        sys.exit(1)

    writer = StagingWriter(database_url or "", dry_run=dry_run)

    try:
        if not dry_run:
            await writer.connect()

        results: list[dict[str, Any]] = []
        for event in events:
            staging_id = await writer.stage(event)
            results.append({
                "uid": event.uid,
                "summary": event.summary,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "attendees": len(event.attendees),
                "staging_id": staging_id,
                "action": "staged",
            })

        logger.info("Calendar fetch complete: %d events staged", len(results))
        if dry_run:
            print(json.dumps(results, indent=2, default=str))
        return results

    finally:
        await writer.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cindy Calendar Fetcher — stages raw data only")
    parser.add_argument("--file", type=str, required=True, help="Path to .ics file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    args = parser.parse_args()

    asyncio.run(fetch_and_stage(file_path=args.file, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
