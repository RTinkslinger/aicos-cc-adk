#!/usr/bin/env python3
"""
Calendar .ics Processor for Cindy.

Parses .ics files received as AgentMail attachments (or provided as local files),
extracts event details, cross-references attendees with Network DB, assembles
pre-meeting context, and writes to the interactions table.

Usage:
    python3 -m cindy.calendar.ics_processor --file event.ics           # parse a local .ics file
    python3 -m cindy.calendar.ics_processor --inbox-scan               # scan AgentMail for .ics
    python3 -m cindy.calendar.ics_processor --dry-run --file event.ics # preview
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
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cindy.calendar")

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]

try:
    from icalendar import Calendar as ICalendar
except ImportError:
    ICalendar = None  # type: ignore[assignment,misc]
    logger.warning("icalendar not installed. Run: pip install icalendar")

# Skip these email domains for attendee resolution (internal)
INTERNAL_DOMAINS = {"z47.com", "devc.fund"}
AAKASH_EMAILS = {"ak@z47.com", "aakash@z47.com", "aakash@devc.fund"}


@dataclass
class CalendarEvent:
    """Parsed calendar event."""

    uid: str
    summary: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    location: str = ""
    description: str = ""
    organizer: str = ""
    organizer_name: str = ""
    attendees: list[dict[str, str]] = field(default_factory=list)
    conference_uri: str = ""
    sequence: int = 0
    status: str = "confirmed"

    @property
    def duration_minutes(self) -> Optional[int]:
        if self.start and self.end:
            delta = self.end - self.start
            return int(delta.total_seconds() / 60)
        return None

    @property
    def attendee_emails(self) -> list[str]:
        return [a["email"] for a in self.attendees if a.get("email")]

    @property
    def is_internal(self) -> bool:
        """True if ALL attendees are from internal domains."""
        emails = self.attendee_emails
        if not emails:
            return False
        return all(
            e.split("@")[-1].lower() in INTERNAL_DOMAINS
            for e in emails
        )

    @property
    def is_short(self) -> bool:
        """True if meeting is < 15 minutes."""
        dur = self.duration_minutes
        return dur is not None and dur < 15


# ---------------------------------------------------------------------------
# .ics Parser
# ---------------------------------------------------------------------------


def parse_ics_content(ics_content: str | bytes) -> list[CalendarEvent]:
    """Parse .ics content and return list of CalendarEvent objects."""
    if ICalendar is None:
        raise RuntimeError("icalendar library not installed. Run: pip install icalendar")

    if isinstance(ics_content, str):
        ics_content = ics_content.encode("utf-8")

    cal = ICalendar.from_ical(ics_content)
    events: list[CalendarEvent] = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        # Parse attendees
        attendees_raw = component.get("ATTENDEE", [])
        if not isinstance(attendees_raw, list):
            attendees_raw = [attendees_raw] if attendees_raw else []

        attendees: list[dict[str, str]] = []
        for att in attendees_raw:
            email = str(att).replace("mailto:", "").replace("MAILTO:", "").strip()
            name = att.params.get("CN", "") if hasattr(att, "params") else ""
            response = att.params.get("PARTSTAT", "NEEDS-ACTION") if hasattr(att, "params") else ""
            if email:
                attendees.append({
                    "email": email,
                    "name": str(name),
                    "response": str(response).lower(),
                })

        # Parse organizer
        organizer_raw = component.get("ORGANIZER")
        organizer_email = ""
        organizer_name = ""
        if organizer_raw:
            organizer_email = str(organizer_raw).replace("mailto:", "").replace("MAILTO:", "").strip()
            if hasattr(organizer_raw, "params"):
                organizer_name = str(organizer_raw.params.get("CN", ""))

        # Parse dates
        dtstart = component.get("DTSTART")
        dtend = component.get("DTEND")

        def to_datetime(dt_prop: Any) -> Optional[datetime]:
            if dt_prop is None:
                return None
            dt = dt_prop.dt
            if isinstance(dt, datetime):
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            # It's a date, convert to datetime at midnight UTC
            return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)

        # Extract conference URI from description or X-properties
        conference_uri = ""
        description = str(component.get("DESCRIPTION", ""))
        # Look for meet/zoom/teams links
        import re
        uri_match = re.search(
            r"(https?://(?:meet\.google\.com|zoom\.us|teams\.microsoft\.com)[^\s<>\"]+)",
            description,
        )
        if uri_match:
            conference_uri = uri_match.group(1)

        event = CalendarEvent(
            uid=str(component.get("UID", "")),
            summary=str(component.get("SUMMARY", "")),
            start=to_datetime(dtstart),
            end=to_datetime(dtend),
            location=str(component.get("LOCATION", "")),
            description=description,
            organizer=organizer_email,
            organizer_name=organizer_name,
            attendees=attendees,
            conference_uri=conference_uri,
            sequence=int(component.get("SEQUENCE", 0)),
            status=str(component.get("STATUS", "CONFIRMED")).lower(),
        )
        events.append(event)

    return events


def parse_ics_file(file_path: str) -> list[CalendarEvent]:
    """Parse a .ics file from disk."""
    with open(file_path, "rb") as f:
        return parse_ics_content(f.read())


# ---------------------------------------------------------------------------
# Database Operations
# ---------------------------------------------------------------------------


class CalendarDBWriter:
    """Database writer for calendar interactions."""

    def __init__(self, database_url: str, dry_run: bool = False) -> None:
        self.database_url = database_url
        self.dry_run = dry_run
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg not installed")
        self._pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def resolve_person_by_email(self, email: str) -> Optional[dict[str, Any]]:
        """Tier 1 resolution: match by email."""
        if self._pool is None:
            return None
        row = await self._pool.fetchrow(
            "SELECT id, person_name, role_title FROM network WHERE email = $1",
            email,
        )
        return dict(row) if row else None

    async def resolve_attendees(
        self, event: CalendarEvent
    ) -> tuple[list[int], list[dict[str, Any]]]:
        """Resolve all attendees. Returns (linked_ids, unresolved_attendees)."""
        linked_ids: list[int] = []
        unresolved: list[dict[str, Any]] = []

        for att in event.attendees:
            email = att.get("email", "")
            if not email or email.lower() in AAKASH_EMAILS:
                continue

            person = await self.resolve_person_by_email(email)
            if person:
                linked_ids.append(person["id"])
                logger.info(
                    "Resolved attendee: %s -> %s (#%d)",
                    email, person["person_name"], person["id"],
                )
            else:
                unresolved.append(att)
                logger.info("Unresolved attendee: %s (%s)", att.get("name", ""), email)

        return linked_ids, unresolved

    async def write_interaction(
        self, event: CalendarEvent, linked_ids: list[int]
    ) -> Optional[int]:
        """Write calendar event as interaction."""
        if self.dry_run:
            logger.info("[DRY RUN] Would write calendar interaction: %s", event.summary)
            return None

        if self._pool is None:
            raise RuntimeError("Database not connected")

        raw_data = json.dumps({
            "title": event.summary,
            "location": event.location,
            "description": event.description[:500] if event.description else "",
            "organizer": event.organizer,
            "organizer_name": event.organizer_name,
            "attendees": event.attendees,
            "conference_uri": event.conference_uri,
            "sequence": event.sequence,
            "status": event.status,
            "end_time": event.end.isoformat() if event.end else None,
        })

        summary = f"{event.summary} — {event.duration_minutes or '?'} min"
        names = [a.get("name", a.get("email", "")) for a in event.attendees[:5]]
        if names:
            summary += f" with {', '.join(names)}"

        row = await self._pool.fetchrow(
            """
            INSERT INTO interactions (
                source, source_id, participants, linked_people,
                summary, raw_data, timestamp, duration_minutes
            ) VALUES (
                'calendar', $1, $2, $3, $4, $5::jsonb, $6::timestamptz, $7
            )
            ON CONFLICT (source, source_id) DO UPDATE SET
                participants = EXCLUDED.participants,
                linked_people = EXCLUDED.linked_people,
                summary = EXCLUDED.summary,
                raw_data = EXCLUDED.raw_data,
                duration_minutes = EXCLUDED.duration_minutes,
                updated_at = NOW()
            RETURNING id
            """,
            event.uid,                                    # $1
            event.attendee_emails,                         # $2
            linked_ids if linked_ids else None,            # $3
            summary,                                       # $4
            raw_data,                                      # $5
            event.start.isoformat() if event.start else datetime.now(timezone.utc).isoformat(),  # $6
            event.duration_minutes,                        # $7
        )
        return row["id"] if row else None

    async def write_people_interactions(
        self, linked_ids: list[int], interaction_id: int, event: CalendarEvent
    ) -> None:
        """Link resolved people to the calendar interaction."""
        if self.dry_run or self._pool is None:
            return

        for person_id in linked_ids:
            # Find the email for this person
            email = ""
            for att in event.attendees:
                person = await self.resolve_person_by_email(att.get("email", ""))
                if person and person["id"] == person_id:
                    email = att.get("email", "")
                    break

            role = "organizer" if email == event.organizer else "participant"
            await self._pool.execute(
                """
                INSERT INTO people_interactions (person_id, interaction_id, role, surface,
                                                  identifier_used, link_confidence)
                VALUES ($1, $2, $3, 'calendar', $4, 1.0)
                ON CONFLICT (person_id, interaction_id) DO NOTHING
                """,
                person_id, interaction_id, role, f"email:{email}",
            )

    async def write_datum_requests(
        self, unresolved: list[dict[str, Any]], interaction_id: Optional[int], event: CalendarEvent
    ) -> None:
        """Send unresolved attendees to Datum Agent."""
        if self.dry_run or self._pool is None:
            return

        for att in unresolved:
            metadata = json.dumps({
                "name": att.get("name", ""),
                "email": att.get("email", ""),
                "source": "cindy_calendar",
                "context": f"Attendee at: {event.summary}",
                "interaction_id": interaction_id,
            })
            await self._pool.execute(
                """
                INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
                VALUES ('datum_person', $1, $2::jsonb, FALSE, NOW())
                """,
                f"New person from calendar: {att.get('name', '')} <{att.get('email', '')}>",
                metadata,
            )

    async def get_recent_interactions_for_person(
        self, person_id: int, days: int = 30, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get recent interactions for pre-meeting context assembly."""
        if self._pool is None:
            return []
        rows = await self._pool.fetch(
            """
            SELECT i.source, i.summary, i.timestamp
            FROM interactions i
            JOIN people_interactions pi ON pi.interaction_id = i.id
            WHERE pi.person_id = $1 AND i.timestamp > NOW() - make_interval(days => $2)
            ORDER BY i.timestamp DESC
            LIMIT $3
            """,
            person_id, days, limit,
        )
        return [dict(r) for r in rows]

    async def get_open_actions_for_person(self, person_name: str) -> list[dict[str, Any]]:
        """Get open action items mentioning this person."""
        if self._pool is None:
            return []
        rows = await self._pool.fetch(
            """
            SELECT action_text, status FROM actions_queue
            WHERE action_text ILIKE $1
              AND status IN ('Proposed', 'Accepted')
            LIMIT 5
            """,
            f"%{person_name}%",
        )
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Pre-Meeting Context Assembly
# ---------------------------------------------------------------------------


async def assemble_pre_meeting_context(
    event: CalendarEvent,
    linked_ids: list[int],
    db: CalendarDBWriter,
) -> dict[str, Any]:
    """Build pre-meeting context for an upcoming meeting."""
    context: dict[str, Any] = {
        "meeting_title": event.summary,
        "meeting_time": event.start.isoformat() if event.start else None,
        "duration_minutes": event.duration_minutes,
        "location": event.location,
        "attendees": [],
    }

    for person_id in linked_ids:
        person = None
        for att in event.attendees:
            p = await db.resolve_person_by_email(att.get("email", ""))
            if p and p["id"] == person_id:
                person = p
                break

        if not person:
            continue

        recent = await db.get_recent_interactions_for_person(person_id)
        actions = await db.get_open_actions_for_person(person["person_name"])

        attendee_context = {
            "name": person["person_name"],
            "role": person.get("role_title", ""),
            "person_id": person_id,
            "recent_interactions": [
                {
                    "date": r["timestamp"].isoformat() if r.get("timestamp") else "",
                    "surface": r.get("source", ""),
                    "summary": r.get("summary", ""),
                }
                for r in recent
            ],
            "open_actions": [a.get("action_text", "") for a in actions],
            "interaction_count_30d": len(recent),
        }
        context["attendees"].append(attendee_context)

    return context


# ---------------------------------------------------------------------------
# Main Processing
# ---------------------------------------------------------------------------


async def process_event(
    event: CalendarEvent,
    db: CalendarDBWriter,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Process a single calendar event."""
    result: dict[str, Any] = {
        "uid": event.uid,
        "summary": event.summary,
        "start": event.start.isoformat() if event.start else None,
        "action": "skipped",
    }

    # Skip internal meetings and short meetings
    if event.is_internal:
        logger.info("Skipping internal meeting: %s", event.summary)
        result["action"] = "skipped_internal"
        return result

    if event.is_short:
        logger.info("Skipping short meeting (<15 min): %s", event.summary)
        result["action"] = "skipped_short"
        return result

    # Skip cancelled events
    if event.status == "cancelled":
        logger.info("Skipping cancelled event: %s", event.summary)
        result["action"] = "skipped_cancelled"
        return result

    # Resolve attendees
    linked_ids, unresolved = await db.resolve_attendees(event)
    result["people_linked"] = len(linked_ids)
    result["people_unresolved"] = len(unresolved)

    # Write interaction
    interaction_id = await db.write_interaction(event, linked_ids)
    result["action"] = "processed"
    result["interaction_id"] = interaction_id

    # Write people links
    if interaction_id and linked_ids:
        await db.write_people_interactions(linked_ids, interaction_id, event)

    # Send unresolved to Datum
    if unresolved:
        await db.write_datum_requests(unresolved, interaction_id, event)

    # Pre-meeting context for future events
    if event.start and event.start > datetime.now(timezone.utc):
        context = await assemble_pre_meeting_context(event, linked_ids, db)
        result["context_assembled"] = True
        if not dry_run and interaction_id:
            # Store context_assembly on the interaction
            if db._pool:
                await db._pool.execute(
                    "UPDATE interactions SET context_assembly = $1::jsonb WHERE id = $2",
                    json.dumps(context, default=str),
                    interaction_id,
                )
        logger.info("Pre-meeting context assembled for: %s", event.summary)

    return result


async def run(
    file_path: Optional[str] = None,
    ics_content: Optional[str | bytes] = None,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Parse .ics and process all events."""
    database_url = os.environ.get("DATABASE_URL", "")
    db = CalendarDBWriter(database_url, dry_run=dry_run)

    try:
        if not dry_run:
            await db.connect()

        # Parse .ics
        if file_path:
            events = parse_ics_file(file_path)
        elif ics_content:
            events = parse_ics_content(ics_content)
        else:
            logger.error("No .ics file or content provided")
            return []

        logger.info("Parsed %d events from .ics", len(events))

        results: list[dict[str, Any]] = []
        for event in events:
            result = await process_event(event, db, dry_run=dry_run)
            results.append(result)

        processed = [r for r in results if r["action"] == "processed"]
        logger.info(
            "Calendar processing complete: %d events processed out of %d total",
            len(processed), len(events),
        )

        if dry_run:
            print(json.dumps(results, indent=2, default=str))

        return results

    finally:
        await db.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Cindy Calendar .ics Processor")
    parser.add_argument("--file", type=str, help="Path to .ics file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    args = parser.parse_args()

    if not args.file:
        logger.error("Provide --file path to a .ics file")
        sys.exit(1)

    asyncio.run(run(file_path=args.file, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
