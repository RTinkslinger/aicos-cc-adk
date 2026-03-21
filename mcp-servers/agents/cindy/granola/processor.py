#!/usr/bin/env python3
"""
Granola Meeting Notes Processor for Cindy.

Polls for new Granola meeting transcripts, extracts intelligence (action items,
thesis signals, deal signals, relationship signals), cross-references attendees
with Network DB, links to calendar events, fills context gaps, and writes to
the interactions table.

Architecture: This module provides processing logic that can be called two ways:
  1. As a CLI tool that reads pre-fetched Granola JSON (from MCP tool output)
  2. As an importable module whose functions are called by the Cindy agent,
     which has access to Granola MCP tools (list_meetings, get_meetings,
     get_meeting_transcript, query_granola_meetings)

The Granola MCP is a Claude.ai plugin — not a standalone HTTP API — so direct
API calls are not possible from this script. The Cindy agent fetches meeting data
via MCP tools and passes it to this processor.

Usage:
    # Process meeting JSON from stdin (pipe from Granola MCP output)
    echo '{"meetings": [...]}' | python3 -m cindy.granola.processor

    # Process a pre-fetched JSON file
    python3 -m cindy.granola.processor --file meetings.json

    # Dry run
    python3 -m cindy.granola.processor --file meetings.json --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cindy.granola")

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# State file for tracking last processed meeting
STATE_DIR = Path(__file__).parent.parent / "state"
LAST_PROCESSED_FILE = STATE_DIR / "granola_last_processed.json"

# Aakash's known identifiers
AAKASH_EMAILS = {"ak@z47.com", "aakash@z47.com", "aakash@devc.fund"}
AAKASH_NAMES = {"aakash", "aakash kumar"}

# Calendar-Granola matching thresholds (from CLAUDE.md Section 4.3)
TIME_OVERLAP_WEIGHT = 0.50
ATTENDEE_OVERLAP_WEIGHT = 0.30
TITLE_SIMILARITY_WEIGHT = 0.20
MATCH_THRESHOLD = 0.50
TIME_WINDOW_MINUTES = 15  # +/- 15 min for time overlap


# ---------------------------------------------------------------------------
# Data Models
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
        """Unique source ID for dedup."""
        return f"granola_{self.meeting_id}"


@dataclass
class TranscriptSegment:
    """A segment of transcript with speaker attribution."""

    speaker: str
    text: str
    source: str  # "microphone" = Aakash, "system" = other participant
    timestamp: Optional[str] = None

    @property
    def is_aakash(self) -> bool:
        return self.source == "microphone"


# ---------------------------------------------------------------------------
# Granola Data Parser
# ---------------------------------------------------------------------------


def parse_granola_meeting(raw: dict[str, Any]) -> GranolaMeeting:
    """Parse raw Granola meeting JSON (from MCP get_meetings output)."""
    # Parse timestamps
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

    # Parse attendees
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

    # Parse action items
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


def parse_transcript_segments(transcript: str) -> list[TranscriptSegment]:
    """Parse transcript into speaker-attributed segments.

    Granola transcripts typically have speakers labeled, with
    source: "microphone" for Aakash and source: "system" for others.
    """
    segments: list[TranscriptSegment] = []

    if not transcript:
        return segments

    # Try JSON-structured transcript first
    try:
        parsed = json.loads(transcript)
        if isinstance(parsed, list):
            for entry in parsed:
                if isinstance(entry, dict):
                    segments.append(TranscriptSegment(
                        speaker=entry.get("speaker", "Unknown"),
                        text=entry.get("text", ""),
                        source=entry.get("source", "system"),
                        timestamp=entry.get("timestamp"),
                    ))
            return segments
    except (json.JSONDecodeError, TypeError):
        pass

    # Fall back to text-based parsing
    # Common patterns: "Speaker Name: text" or "[Speaker Name] text"
    speaker_pattern = re.compile(r"^(?:\[([^\]]+)\]|([^:]{2,30}):)\s*(.+)", re.MULTILINE)

    for match in speaker_pattern.finditer(transcript):
        speaker = match.group(1) or match.group(2) or "Unknown"
        text = match.group(3).strip()
        # Heuristic: if speaker name matches Aakash's known names, it's microphone
        source = "microphone" if speaker.lower().strip() in AAKASH_NAMES else "system"
        segments.append(TranscriptSegment(speaker=speaker.strip(), text=text, source=source))

    # If no structured segments found, treat entire transcript as one segment
    if not segments and transcript.strip():
        segments.append(TranscriptSegment(
            speaker="Unknown",
            text=transcript[:5000],  # Cap at 5KB for signal extraction
            source="system",
        ))

    return segments


# ---------------------------------------------------------------------------
# Signal Extraction
# ---------------------------------------------------------------------------


def extract_action_items_from_transcript(segments: list[TranscriptSegment]) -> list[str]:
    """Extract action items from transcript segments beyond Granola's AI items."""
    actions: list[str] = []
    patterns = [
        r"(?:let'?s|can we|should we|need to|let me|i'?ll)\s+(.{10,80})",
        r"(?:please|could you|can you|would you)\s+(.{10,80})",
        r"(?:action|todo|follow[- ]?up)[:;]\s*(.{10,80})",
        r"(?:will|going to)\s+(?:send|share|follow|schedule|set up|draft|prepare)\s+(.{10,60})",
        r"by (?:friday|monday|tuesday|wednesday|thursday|end of (?:day|week)|tomorrow|next week)(.{0,60})",
    ]

    for segment in segments:
        if not segment.text:
            continue
        for pattern in patterns:
            for match in re.finditer(pattern, segment.text, re.IGNORECASE):
                action = match.group(0).strip().rstrip(".,;:")
                if len(action) > 15 and action not in actions:
                    actions.append(action)

    return actions[:15]  # cap


def extract_deal_signals(segments: list[TranscriptSegment]) -> list[dict[str, str]]:
    """Extract deal signals from transcript."""
    all_text = " ".join(s.text for s in segments if s.text)
    signals: list[dict[str, str]] = []

    deal_types = {
        "term_sheet": r"term\s*sheet",
        "valuation": r"(?:valuation|pre-?money|post-?money|\$\d+[MmBb]\s+(?:pre|post))",
        "fundraise": r"(?:series\s+[a-e]|seed|bridge|extension|follow[- ]?on|fundrais)",
        "financials": r"(?:cap\s*table|burn\s*rate|runway|revenue|arr|mrr|gmv)",
        "diligence": r"(?:due\s*diligence|dd\s+process|data\s*room|ic\s+(?:meeting|review|deck))",
    }
    for signal_type, pattern in deal_types.items():
        if re.search(pattern, all_text, re.IGNORECASE):
            signals.append({"type": signal_type, "strength": "detected"})

    return signals


def extract_thesis_signals(segments: list[TranscriptSegment]) -> list[dict[str, str]]:
    """Extract thesis signals from transcript."""
    all_text = " ".join(s.text for s in segments if s.text)
    signals: list[dict[str, str]] = []

    thesis_keywords = {
        "agentic_ai": r"(?:agentic|ai\s+agent|autonomous\s+agent|agent\s+(?:framework|infra))",
        "developer_tools": r"(?:dev\s*tools?|developer\s+(?:experience|platform)|devops|ci/?cd)",
        "fintech": r"(?:fintech|digital\s+(?:payments?|banking|lending)|neobank)",
        "climate": r"(?:climate\s*tech|carbon|sustainability|clean\s*energy|ev\s)",
        "cybersecurity": r"(?:cyber\s*security|infosec|zero\s*trust|siem|soc\s)",
    }
    for thesis_name, pattern in thesis_keywords.items():
        if re.search(pattern, all_text, re.IGNORECASE):
            signals.append({"thesis": thesis_name, "signal": "mention", "strength": "moderate"})

    return signals


def extract_relationship_signals(segments: list[TranscriptSegment]) -> dict[str, Any]:
    """Detect relationship warmth and engagement from conversation dynamics."""
    if not segments:
        return {}

    # Count turns by speaker
    aakash_turns = sum(1 for s in segments if s.is_aakash)
    other_turns = sum(1 for s in segments if not s.is_aakash)
    total_turns = aakash_turns + other_turns

    if total_turns == 0:
        return {}

    # Engagement: balanced turns = higher engagement
    balance = min(aakash_turns, other_turns) / max(aakash_turns, other_turns, 1)
    engagement = "active" if balance > 0.3 else "one-sided"

    # Follow-up signals
    all_text = " ".join(s.text for s in segments if s.text)
    follow_up_needed = bool(re.search(
        r"(?:follow[- ]?up|next\s+(?:step|meeting|call)|circle\s+back|touch\s+base|reconnect)",
        all_text, re.IGNORECASE,
    ))

    return {
        "engagement": engagement,
        "turn_balance": round(balance, 2),
        "follow_up_needed": follow_up_needed,
        "total_turns": total_turns,
    }


# ---------------------------------------------------------------------------
# Calendar-Granola Matching (Multi-Signal Scoring)
# ---------------------------------------------------------------------------


def compute_time_overlap(
    granola_start: Optional[datetime],
    calendar_start: Optional[datetime],
) -> float:
    """Score time overlap between Granola meeting and calendar event.

    Returns 1.0 if starts are within TIME_WINDOW_MINUTES, scaling to 0.0 outside.
    """
    if not granola_start or not calendar_start:
        return 0.0

    delta = abs((granola_start - calendar_start).total_seconds() / 60)
    if delta <= TIME_WINDOW_MINUTES:
        return 1.0 - (delta / TIME_WINDOW_MINUTES) * 0.5  # 1.0 at 0 min, 0.5 at threshold
    return 0.0


def compute_attendee_overlap(
    granola_names: list[str],
    calendar_emails: list[str],
    calendar_names: list[str],
) -> float:
    """Score attendee overlap using fuzzy name matching.

    Compares Granola attendee names against calendar attendee names and emails.
    """
    if not granola_names or (not calendar_emails and not calendar_names):
        return 0.0

    # Combine calendar identifiers into searchable names
    cal_names_lower = [n.lower() for n in calendar_names if n]
    # Extract name portion from emails (before @)
    email_names = [e.split("@")[0].replace(".", " ").lower() for e in calendar_emails if e]
    all_cal_names = cal_names_lower + email_names

    if not all_cal_names:
        return 0.0

    matches = 0
    for g_name in granola_names:
        g_lower = g_name.lower().strip()
        if not g_lower or g_lower in AAKASH_NAMES:
            continue
        for c_name in all_cal_names:
            if not c_name:
                continue
            # Fuzzy match
            ratio = SequenceMatcher(None, g_lower, c_name).ratio()
            if ratio > 0.6:
                matches += 1
                break

    total_granola = len([n for n in granola_names if n.lower().strip() not in AAKASH_NAMES])
    if total_granola == 0:
        return 0.0

    return min(matches / total_granola, 1.0)


def compute_title_similarity(granola_title: str, calendar_title: str) -> float:
    """Score title similarity between Granola meeting and calendar event."""
    if not granola_title or not calendar_title:
        return 0.0
    return SequenceMatcher(None, granola_title.lower(), calendar_title.lower()).ratio()


def compute_calendar_match_score(
    meeting: GranolaMeeting,
    calendar_event: dict[str, Any],
) -> float:
    """Compute multi-signal matching score.

    Score = time_overlap * 0.50 + attendee_overlap * 0.30 + title_similarity * 0.20
    """
    # Parse calendar event timestamps
    cal_start = None
    cal_start_str = calendar_event.get("timestamp") or calendar_event.get("start_time")
    if cal_start_str:
        try:
            cal_start = datetime.fromisoformat(str(cal_start_str).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    time_score = compute_time_overlap(meeting.start_time, cal_start)

    # Calendar attendees
    cal_participants = calendar_event.get("participants") or []
    cal_names = []
    cal_emails = []
    if isinstance(cal_participants, list):
        for p in cal_participants:
            if isinstance(p, str):
                if "@" in p:
                    cal_emails.append(p)
                else:
                    cal_names.append(p)

    # Also check raw_data for attendee details
    raw_data = calendar_event.get("raw_data")
    if raw_data and isinstance(raw_data, str):
        try:
            raw_data = json.loads(raw_data)
        except json.JSONDecodeError:
            raw_data = {}
    if isinstance(raw_data, dict):
        for att in raw_data.get("attendees", []):
            if isinstance(att, dict):
                if att.get("email"):
                    cal_emails.append(att["email"])
                if att.get("name"):
                    cal_names.append(att["name"])

    attendee_score = compute_attendee_overlap(meeting.attendee_names, cal_emails, cal_names)

    # Calendar title
    cal_title = calendar_event.get("summary") or calendar_event.get("title") or ""
    title_score = compute_title_similarity(meeting.title, cal_title)

    total = (
        time_score * TIME_OVERLAP_WEIGHT
        + attendee_score * ATTENDEE_OVERLAP_WEIGHT
        + title_score * TITLE_SIMILARITY_WEIGHT
    )

    logger.debug(
        "Calendar match: time=%.2f(%.2f) attendee=%.2f(%.2f) title=%.2f(%.2f) => %.2f",
        time_score, time_score * TIME_OVERLAP_WEIGHT,
        attendee_score, attendee_score * ATTENDEE_OVERLAP_WEIGHT,
        title_score, title_score * TITLE_SIMILARITY_WEIGHT,
        total,
    )

    return total


# ---------------------------------------------------------------------------
# Database Operations
# ---------------------------------------------------------------------------


class GranolaDBWriter:
    """Async Postgres writer for Granola meeting interactions."""

    def __init__(self, database_url: str, dry_run: bool = False) -> None:
        self.database_url = database_url
        self.dry_run = dry_run
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg not installed. Run: pip install asyncpg")
        self._pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def interaction_exists(self, source_id: str) -> Optional[int]:
        """Check if meeting already processed (dedup)."""
        if self._pool is None:
            return None
        row = await self._pool.fetchrow(
            "SELECT id FROM interactions WHERE source = 'granola' AND source_id = $1",
            source_id,
        )
        return row["id"] if row else None

    async def resolve_person_by_email(self, email: str) -> Optional[dict[str, Any]]:
        """Tier 1 resolution: match by email."""
        if self._pool is None:
            return None
        row = await self._pool.fetchrow(
            "SELECT id, person_name, role_title FROM network WHERE email = $1",
            email,
        )
        return dict(row) if row else None

    async def resolve_person_by_name(self, name: str) -> list[dict[str, Any]]:
        """Tier 5 resolution: match by name."""
        if self._pool is None:
            return []
        rows = await self._pool.fetch(
            "SELECT id, person_name, role_title, email, phone FROM network WHERE LOWER(person_name) = LOWER($1)",
            name,
        )
        return [dict(r) for r in rows]

    async def find_calendar_events_near(
        self, start_time: datetime, window_minutes: int = TIME_WINDOW_MINUTES
    ) -> list[dict[str, Any]]:
        """Find calendar interactions near a given time for calendar-Granola matching."""
        if self._pool is None:
            return []
        rows = await self._pool.fetch(
            """
            SELECT id, source_id, summary, participants, linked_people,
                   raw_data, timestamp, duration_minutes
            FROM interactions
            WHERE source = 'calendar'
              AND timestamp BETWEEN $1::timestamptz - make_interval(mins => $2)
                                AND $1::timestamptz + make_interval(mins => $2)
            """,
            start_time, window_minutes,
        )
        return [dict(r) for r in rows]

    async def fill_context_gap(self, calendar_event_id: str, interaction_id: int) -> None:
        """Mark context gap as filled when Granola transcript arrives."""
        if self.dry_run or self._pool is None:
            return
        await self._pool.execute(
            """
            UPDATE context_gaps SET
                status = 'filled',
                filled_by = 'automatic',
                filled_sources = array_append(COALESCE(filled_sources, ARRAY[]::TEXT[]), 'granola'),
                filled_at = NOW()
            WHERE calendar_event_id = $1
              AND status IN ('pending', 'partial')
            """,
            calendar_event_id,
        )

    async def write_interaction(
        self,
        meeting: GranolaMeeting,
        linked_ids: list[int],
        linked_companies: list[int],
        signals: dict[str, Any],
        calendar_match: Optional[dict[str, Any]],
    ) -> Optional[int]:
        """Write Granola meeting as interaction. Full transcript stored in raw_data."""
        if self.dry_run:
            logger.info("[DRY RUN] Would write interaction: %s", meeting.source_id)
            return None

        if self._pool is None:
            raise RuntimeError("Database not connected")

        # raw_data stores full transcript (allowed for Granola per privacy rules)
        raw_data = json.dumps({
            "title": meeting.title,
            "ai_summary": meeting.ai_summary,
            "transcript": meeting.transcript[:100000] if meeting.transcript else "",
            "private_notes": meeting.private_notes,
            "attendees": meeting.attendees,
            "granola_action_items": meeting.action_items,
            "calendar_match_id": calendar_match.get("id") if calendar_match else None,
        }, default=str)

        summary = f"{meeting.title} — {meeting.duration_minutes or '?'} min"
        names = [a.get("name", "") for a in meeting.attendees[:5] if a.get("name")]
        if names:
            summary += f" with {', '.join(names)}"

        # Participants: attendee emails/names
        participants = meeting.attendee_emails or meeting.attendee_names

        # Context gap ID if we matched a calendar event
        context_gap_id = None

        row = await self._pool.fetchrow(
            """
            INSERT INTO interactions (
                source, source_id, thread_id, participants, linked_people,
                linked_companies, summary, raw_data, timestamp, duration_minutes,
                action_items, thesis_signals, relationship_signals, deal_signals,
                context_gap_id
            ) VALUES (
                'granola', $1, $2, $3, $4, $5, $6, $7::jsonb, $8::timestamptz, $9,
                $10, $11::jsonb, $12::jsonb, $13::jsonb, $14
            )
            ON CONFLICT (source, source_id) DO UPDATE SET
                summary = COALESCE(EXCLUDED.summary, interactions.summary),
                linked_people = COALESCE(EXCLUDED.linked_people, interactions.linked_people),
                action_items = COALESCE(EXCLUDED.action_items, interactions.action_items),
                thesis_signals = COALESCE(EXCLUDED.thesis_signals, interactions.thesis_signals),
                relationship_signals = COALESCE(EXCLUDED.relationship_signals, interactions.relationship_signals),
                deal_signals = COALESCE(EXCLUDED.deal_signals, interactions.deal_signals),
                updated_at = NOW()
            RETURNING id
            """,
            meeting.source_id,                                                # $1
            meeting.meeting_id,                                               # $2 thread_id
            participants,                                                      # $3
            linked_ids if linked_ids else None,                                # $4
            linked_companies if linked_companies else None,                    # $5
            summary,                                                           # $6
            raw_data,                                                          # $7
            meeting.start_time.isoformat() if meeting.start_time else datetime.now(timezone.utc).isoformat(),  # $8
            meeting.duration_minutes,                                          # $9
            signals.get("all_action_items", []),                               # $10
            json.dumps(signals.get("thesis_signals", [])),                     # $11
            json.dumps(signals.get("relationship_signals", {})),               # $12
            json.dumps(signals.get("deal_signals", [])),                       # $13
            context_gap_id,                                                    # $14
        )
        return row["id"] if row else None

    async def write_people_interaction(
        self,
        person_id: int,
        interaction_id: int,
        role: str,
        identifier: str,
        confidence: float,
    ) -> None:
        """Link a person to an interaction."""
        if self.dry_run or self._pool is None:
            return
        await self._pool.execute(
            """
            INSERT INTO people_interactions (person_id, interaction_id, role, surface,
                                              identifier_used, link_confidence)
            VALUES ($1, $2, $3, 'granola', $4, $5)
            ON CONFLICT (person_id, interaction_id) DO NOTHING
            """,
            person_id, interaction_id, role, identifier, confidence,
        )

    async def write_datum_request(
        self,
        name: str,
        email: str,
        context: str,
        interaction_id: Optional[int],
    ) -> None:
        """Send unresolved attendee to Datum Agent."""
        if self.dry_run or self._pool is None:
            return
        metadata = json.dumps({
            "name": name,
            "email": email,
            "source": "cindy_meeting",
            "context": context,
            "interaction_id": interaction_id,
        })
        await self._pool.execute(
            """
            INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
            VALUES ('datum_person', $1, $2::jsonb, FALSE, NOW())
            """,
            f"New person from Granola meeting: {name} <{email}>",
            metadata,
        )

    async def write_action_items(
        self,
        actions: list[str],
        meeting: GranolaMeeting,
    ) -> None:
        """Write action items to actions_queue."""
        if self.dry_run or self._pool is None:
            return
        for action_text in actions:
            await self._pool.execute(
                """
                INSERT INTO actions_queue (action, action_type, priority, status,
                                           assigned_to, source, reasoning, notion_synced,
                                           created_at, updated_at)
                VALUES ($1, 'Meeting/Outreach', 'P1 - This Week', 'Proposed',
                        'Aakash', 'Cindy-Meeting', $2, FALSE, NOW(), NOW())
                """,
                action_text,
                f"Extracted from Granola meeting: {meeting.title}",
            )

    async def write_thesis_signal(
        self,
        signals: list[dict[str, str]],
        meeting: GranolaMeeting,
        interaction_id: Optional[int],
    ) -> None:
        """Route thesis signals to Megamind via cai_inbox."""
        if self.dry_run or self._pool is None or not signals:
            return
        metadata = json.dumps({
            "signal_type": "thesis_conviction",
            "strength": "moderate",
            "summary": f"Thesis signals from meeting: {meeting.title}",
            "thesis_connections": [s.get("thesis", "") for s in signals],
            "interaction_id": interaction_id,
        })
        await self._pool.execute(
            """
            INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
            VALUES ('cindy_signal', $1, $2::jsonb, FALSE, NOW())
            """,
            f"Thesis signal from Granola meeting: {meeting.title}",
            metadata,
        )


# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------


def load_last_processed() -> Optional[str]:
    """Load last processed meeting ID from state file."""
    if not LAST_PROCESSED_FILE.exists():
        return None
    try:
        data = json.loads(LAST_PROCESSED_FILE.read_text())
        return data.get("last_meeting_id")
    except (json.JSONDecodeError, KeyError):
        return None


def save_last_processed(meeting_id: str, meeting_title: str) -> None:
    """Save last processed meeting ID to state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LAST_PROCESSED_FILE.write_text(json.dumps({
        "last_meeting_id": meeting_id,
        "last_meeting_title": meeting_title,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))


# ---------------------------------------------------------------------------
# Main Processing
# ---------------------------------------------------------------------------


async def process_meeting(
    meeting: GranolaMeeting,
    db: GranolaDBWriter,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Process a single Granola meeting: resolve people, extract signals, match calendar, write."""
    result: dict[str, Any] = {
        "meeting_id": meeting.meeting_id,
        "title": meeting.title,
        "action": "skipped",
        "people_linked": 0,
        "people_new": 0,
    }

    if not meeting.meeting_id:
        result["action"] = "skipped_no_id"
        return result

    # 1. Dedup
    existing_id = await db.interaction_exists(meeting.source_id)
    if existing_id:
        logger.info("Already processed: %s (interaction #%d)", meeting.source_id, existing_id)
        result["action"] = "already_processed"
        result["interaction_id"] = existing_id
        return result

    # 2. Parse transcript segments
    segments = parse_transcript_segments(meeting.transcript)
    logger.info("Parsed %d transcript segments for: %s", len(segments), meeting.title)

    # 3. Resolve attendees
    linked_ids: list[int] = []
    unresolved: list[dict[str, str]] = []

    for att in meeting.attendees:
        name = att.get("name", "")
        email = att.get("email", "")

        # Skip Aakash
        if email and email.lower() in AAKASH_EMAILS:
            continue
        if name and name.lower().strip() in AAKASH_NAMES:
            continue

        # Tier 1: Email match
        if email:
            person = await db.resolve_person_by_email(email)
            if person:
                linked_ids.append(person["id"])
                result["people_linked"] += 1
                logger.info("Linked by email: %s -> %s (#%d)", email, person["person_name"], person["id"])
                continue

        # Tier 5: Name match
        if name:
            matches = await db.resolve_person_by_name(name)
            if len(matches) == 1:
                linked_ids.append(matches[0]["id"])
                result["people_linked"] += 1
                logger.info(
                    "Linked by name: %s -> %s (#%d) [confidence=0.80]",
                    name, matches[0]["person_name"], matches[0]["id"],
                )
                continue
            elif len(matches) > 1:
                logger.info("Ambiguous name match for %s (%d candidates) — sending to Datum", name, len(matches))

        # Tier 6: Unresolved
        unresolved.append(att)
        result["people_new"] += 1

    # 4. Extract signals
    # Start with Granola's AI action items, then add transcript-extracted ones
    granola_actions = meeting.action_items or []
    transcript_actions = extract_action_items_from_transcript(segments)
    # Deduplicate
    all_action_items = list(granola_actions)
    for action in transcript_actions:
        if action not in all_action_items:
            all_action_items.append(action)

    signals: dict[str, Any] = {
        "granola_action_items": granola_actions,
        "transcript_action_items": transcript_actions,
        "all_action_items": all_action_items,
        "deal_signals": extract_deal_signals(segments),
        "thesis_signals": extract_thesis_signals(segments),
        "relationship_signals": extract_relationship_signals(segments),
    }
    result["signals"] = {k: len(v) if isinstance(v, list) else 1 for k, v in signals.items()}

    # 5. Calendar-Granola matching (per CLAUDE.md Section 4.3)
    calendar_match: Optional[dict[str, Any]] = None
    if meeting.start_time:
        nearby_events = await db.find_calendar_events_near(meeting.start_time)
        if nearby_events:
            best_score = 0.0
            best_event = None
            for event in nearby_events:
                score = compute_calendar_match_score(meeting, event)
                if score > best_score:
                    best_score = score
                    best_event = event

            if best_score >= MATCH_THRESHOLD and best_event:
                calendar_match = best_event
                result["calendar_match"] = {
                    "event_id": best_event.get("source_id"),
                    "score": round(best_score, 3),
                    "summary": best_event.get("summary", ""),
                }
                logger.info(
                    "Matched to calendar event (score=%.2f): %s",
                    best_score, best_event.get("summary", ""),
                )

                # Fill context gap if one exists
                if best_event.get("source_id"):
                    await db.fill_context_gap(best_event["source_id"], 0)  # ID updated after insert

    # 6. Write interaction
    interaction_id = await db.write_interaction(
        meeting, linked_ids, [], signals, calendar_match,
    )
    result["action"] = "processed"
    result["interaction_id"] = interaction_id

    # 7. Write people links
    if interaction_id:
        for att in meeting.attendees:
            email = att.get("email", "")
            name = att.get("name", "")

            if email and email.lower() in AAKASH_EMAILS:
                continue
            if name and name.lower().strip() in AAKASH_NAMES:
                continue

            # Find person_id for this attendee
            person_id = None
            if email:
                p = await db.resolve_person_by_email(email)
                if p:
                    person_id = p["id"]
            if not person_id and name:
                matches = await db.resolve_person_by_name(name)
                if len(matches) == 1:
                    person_id = matches[0]["id"]

            if person_id and person_id in linked_ids:
                identifier = f"email:{email}" if email else f"name:{name}"
                confidence = 1.0 if email else 0.80
                await db.write_people_interaction(
                    person_id, interaction_id, "participant",
                    identifier, confidence,
                )

    # 8. Write datum requests for unresolved
    for att in unresolved:
        await db.write_datum_request(
            att.get("name", ""),
            att.get("email", ""),
            f"Attendee at Granola meeting: {meeting.title}",
            interaction_id,
        )

    # 9. Write action items to actions_queue
    if all_action_items:
        await db.write_action_items(all_action_items, meeting)

    # 10. Route thesis signals
    if signals["thesis_signals"]:
        await db.write_thesis_signal(signals["thesis_signals"], meeting, interaction_id)

    # 11. Update context gap if calendar was matched
    if calendar_match and interaction_id and calendar_match.get("source_id"):
        await db.fill_context_gap(calendar_match["source_id"], interaction_id)

    return result


async def process_meetings_batch(
    meetings_data: list[dict[str, Any]],
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Process a batch of Granola meetings."""
    database_url = os.environ.get("DATABASE_URL", "")

    if not database_url and not dry_run:
        logger.error("DATABASE_URL not set (required when not in --dry-run mode)")
        return []

    # Parse meetings
    meetings = [parse_granola_meeting(m) for m in meetings_data]

    # Filter out already-processed (by meeting ID state)
    last_id = load_last_processed()
    if last_id:
        logger.info("Last processed meeting ID: %s", last_id)

    db = GranolaDBWriter(database_url, dry_run=dry_run)

    try:
        if not dry_run:
            await db.connect()

        results: list[dict[str, Any]] = []
        for meeting in meetings:
            if not meeting.meeting_id:
                logger.warning("Skipping meeting with no ID: %s", meeting.title)
                continue

            result = await process_meeting(meeting, db, dry_run=dry_run)
            results.append(result)

        # Summary
        processed = [r for r in results if r["action"] == "processed"]
        skipped = [r for r in results if r["action"] == "already_processed"]
        total_people = sum(r.get("people_linked", 0) for r in processed)
        total_new = sum(r.get("people_new", 0) for r in processed)
        total_actions = sum(
            r.get("signals", {}).get("all_action_items", 0) for r in processed
        )
        calendar_matches = sum(1 for r in processed if r.get("calendar_match"))

        logger.info(
            "Granola processing complete: %d processed, %d skipped, "
            "%d people linked, %d new, %d action items, %d calendar matches",
            len(processed), len(skipped),
            total_people, total_new, total_actions, calendar_matches,
        )

        # Save last processed meeting
        if not dry_run and processed:
            last = processed[-1]
            save_last_processed(last["meeting_id"], last["title"])

        if dry_run:
            print(json.dumps(results, indent=2, default=str))

        return results

    finally:
        await db.close()


async def run(
    file_path: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Main entry point: read meetings data, process all."""
    # Read meetings data from file or stdin
    meetings_data: list[dict[str, Any]] = []

    if file_path:
        with open(file_path) as f:
            data = json.load(f)
    else:
        # Read from stdin
        if sys.stdin.isatty():
            logger.error(
                "No input provided. Pipe Granola MCP output via stdin or use --file.\n"
                "Example: echo '{\"meetings\": [...]}' | python3 -m cindy.granola.processor"
            )
            sys.exit(1)
        data = json.load(sys.stdin)

    # Handle various data shapes from Granola MCP
    if isinstance(data, list):
        meetings_data = data
    elif isinstance(data, dict):
        meetings_data = data.get("meetings", data.get("items", [data]))
    else:
        logger.error("Unexpected data format: %s", type(data))
        sys.exit(1)

    logger.info("Loaded %d meetings to process", len(meetings_data))

    if not meetings_data:
        logger.info("No meetings to process")
        return

    await process_meetings_batch(meetings_data, dry_run=dry_run)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Cindy Granola Meeting Notes Processor")
    parser.add_argument("--file", type=str, help="Path to meetings JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    args = parser.parse_args()

    asyncio.run(run(file_path=args.file, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
