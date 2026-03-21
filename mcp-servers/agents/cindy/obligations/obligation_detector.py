#!/usr/bin/env python3
"""
Obligation Detector for Cindy.

Takes an interaction (email, meeting transcript, WhatsApp chat) as input,
detects obligations using pattern matching, computes Cindy priority,
handles deduplication and auto-fulfillment, and writes to Supabase.

Implements the full obligation-detection.md skill specification:
- I_OWE_THEM / THEY_OWE_ME classification
- 10 obligation categories
- Cindy priority formula (5-factor weighted score)
- Deduplication against existing obligations
- Auto-fulfillment detection
- Megamind routing for high-priority obligations

Usage:
    python3 -m cindy.obligations.obligation_detector --interaction-id 123
    python3 -m cindy.obligations.obligation_detector --text "I'll send you the deck" --source email --person-id 42
    python3 -m cindy.obligations.obligation_detector --dry-run --text "..."
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
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cindy.obligations")

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Obligation Categories
# ---------------------------------------------------------------------------

CATEGORIES = {
    "send_document", "reply", "schedule", "follow_up",
    "introduce", "review", "deliver", "connect", "provide_info", "other",
}

# ---------------------------------------------------------------------------
# Detection Patterns
# ---------------------------------------------------------------------------

# I_OWE_THEM patterns (Aakash committed to do something)
I_OWE_PATTERNS: list[tuple[str, str]] = [
    (r"(?:i'?ll|let me|i will|i am going to)\s+(?:send|share|forward|email)", "send_document"),
    (r"(?:i'?ll|let me|i will)\s+(?:get back|circle back|revert|reply|respond)", "reply"),
    (r"(?:i'?ll|let me|i will)\s+(?:follow up|follow-up|circle back on)", "follow_up"),
    (r"(?:i'?ll|let me|i will)\s+(?:introduce|connect|loop in|put you in touch)", "introduce"),
    (r"(?:i'?ll|let me|i will)\s+(?:review|look at|go through|check)", "review"),
    (r"(?:i'?ll|let me|i will)\s+(?:schedule|set up|arrange|book|plan)", "schedule"),
    (r"(?:i'?ll|let me|i will)\s+(?:deliver|provide|prepare|create|write|draft|build)", "deliver"),
    (r"(?:i'?ll|let me|i will)\s+(?:check with|confirm with|verify)", "provide_info"),
    # First person future tense + action verb (general catch-all)
    (r"i will\s+\w+", "other"),
]

# THEY_OWE_ME patterns (someone committed to Aakash)
THEY_OWE_PATTERNS: list[tuple[str, str]] = [
    (r"(?:i'?ll|let me|i will|we'?ll)\s+(?:send|share|forward)", "send_document"),
    (r"(?:i'?ll|let me|i will)\s+(?:get back|circle back|revert)", "reply"),
    (r"(?:i'?ll|let me|i will)\s+(?:schedule|set up|arrange)", "schedule"),
    (r"(?:i'?ll|let me|i will)\s+(?:introduce|connect)", "introduce"),
    (r"(?:i'?ll|let me|i will)\s+(?:review|look at|check)", "review"),
    (r"(?:i'?ll|let me|i will)\s+(?:deliver|provide|prepare)", "deliver"),
]

# Request patterns (Aakash asking = THEY_OWE, someone asking Aakash = I_OWE)
REQUEST_PATTERNS: list[tuple[str, str]] = [
    (r"(?:could you|can you|would you|please)\s+(?:send|share|forward)", "send_document"),
    (r"(?:could you|can you|would you|please)\s+(?:review|check|look at)", "review"),
    (r"(?:could you|can you|would you|please)\s+(?:schedule|set up|arrange)", "schedule"),
    (r"(?:could you|can you|would you|please)\s+(?:introduce|connect)", "introduce"),
    (r"(?:could you|can you|would you|please)\s+(?:provide|prepare|send me)", "provide_info"),
]

# Due date extraction patterns
DUE_DATE_PATTERNS: list[tuple[str, int]] = [
    (r"by (?:end of day|eod|tonight)", 0),
    (r"by tomorrow", 1),
    (r"by (?:end of week|eow|friday)", 5),
    (r"(?:next week|early next week)", 7),
    (r"by (?:monday|tuesday|wednesday|thursday)", 5),  # approximate
    (r"within (\d+) days?", -1),  # special: extract number
    (r"(?:this week)", 4),
    (r"(?:next month|end of month)", 30),
]


# ---------------------------------------------------------------------------
# Obligation Data Model
# ---------------------------------------------------------------------------


@dataclass
class DetectedObligation:
    """A detected obligation before DB write."""

    obligation_type: str  # I_OWE_THEM or THEY_OWE_ME
    description: str
    category: str
    source_quote: str
    detection_method: str  # explicit, implied, manual
    person_id: Optional[int] = None
    person_name: str = ""
    person_role: str = ""
    source: str = ""  # email, whatsapp, granola, calendar
    source_interaction_id: Optional[int] = None
    due_date: Optional[datetime] = None
    due_date_source: Optional[str] = None
    confidence: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pattern-Based Detection
# ---------------------------------------------------------------------------


def detect_obligations_from_text(
    text: str,
    is_from_aakash: bool = False,
    source: str = "email",
) -> list[DetectedObligation]:
    """Detect obligations from a text block using pattern matching.

    Args:
        text: The text to analyze.
        is_from_aakash: True if Aakash is the speaker/sender.
        source: The surface (email, whatsapp, granola, calendar).

    Returns:
        List of detected obligations.
    """
    obligations: list[DetectedObligation] = []
    text_lower = text.lower()

    if is_from_aakash:
        # Aakash speaking/writing: commitment patterns = I_OWE_THEM
        for pattern, category in I_OWE_PATTERNS:
            matches = list(re.finditer(pattern, text_lower))
            for m in matches:
                # Extract context around the match
                start = max(0, m.start() - 20)
                end = min(len(text), m.end() + 100)
                quote = text[start:end].strip()

                obligations.append(DetectedObligation(
                    obligation_type="I_OWE_THEM",
                    description=_generate_description(quote, category, "I_OWE_THEM"),
                    category=category,
                    source_quote=quote[:300],
                    detection_method="explicit",
                    source=source,
                    confidence=0.85,
                ))

        # Aakash sending a request = THEY_OWE_ME
        for pattern, category in REQUEST_PATTERNS:
            matches = list(re.finditer(pattern, text_lower))
            for m in matches:
                start = max(0, m.start() - 20)
                end = min(len(text), m.end() + 100)
                quote = text[start:end].strip()

                obligations.append(DetectedObligation(
                    obligation_type="THEY_OWE_ME",
                    description=_generate_description(quote, category, "THEY_OWE_ME"),
                    category=category,
                    source_quote=quote[:300],
                    detection_method="explicit",
                    source=source,
                    confidence=0.80,
                ))
    else:
        # Other person speaking/writing: commitment patterns = THEY_OWE_ME
        for pattern, category in THEY_OWE_PATTERNS:
            matches = list(re.finditer(pattern, text_lower))
            for m in matches:
                start = max(0, m.start() - 20)
                end = min(len(text), m.end() + 100)
                quote = text[start:end].strip()

                obligations.append(DetectedObligation(
                    obligation_type="THEY_OWE_ME",
                    description=_generate_description(quote, category, "THEY_OWE_ME"),
                    category=category,
                    source_quote=quote[:300],
                    detection_method="explicit",
                    source=source,
                    confidence=0.85,
                ))

        # Other person making a request = I_OWE_THEM
        for pattern, category in REQUEST_PATTERNS:
            matches = list(re.finditer(pattern, text_lower))
            for m in matches:
                start = max(0, m.start() - 20)
                end = min(len(text), m.end() + 100)
                quote = text[start:end].strip()

                obligations.append(DetectedObligation(
                    obligation_type="I_OWE_THEM",
                    description=_generate_description(quote, category, "I_OWE_THEM"),
                    category=category,
                    source_quote=quote[:300],
                    detection_method="explicit",
                    source=source,
                    confidence=0.80,
                ))

    # Extract due dates for all detected obligations
    for obl in obligations:
        due_date, due_source = _extract_due_date(obl.source_quote)
        if due_date:
            obl.due_date = due_date
            obl.due_date_source = due_source

    # Filter by confidence threshold (>= 0.7)
    obligations = [o for o in obligations if o.confidence >= 0.7]

    # Filter out generic pleasantries
    obligations = [o for o in obligations if not _is_pleasantry(o.source_quote)]

    return obligations


def _generate_description(quote: str, category: str, obl_type: str) -> str:
    """Generate a human-readable obligation description."""
    prefix = "Aakash committed to" if obl_type == "I_OWE_THEM" else "They committed to"
    category_verbs = {
        "send_document": "send a document",
        "reply": "reply/get back",
        "schedule": "schedule a meeting",
        "follow_up": "follow up",
        "introduce": "make an introduction",
        "review": "review something",
        "deliver": "deliver/prepare something",
        "connect": "connect people",
        "provide_info": "provide information",
        "other": "take action",
    }
    verb = category_verbs.get(category, "take action")
    # Trim quote to first sentence
    first_sentence = quote.split(".")[0].split("\n")[0][:120]
    return f"{prefix} {verb}: \"{first_sentence}\""


def _extract_due_date(text: str) -> tuple[Optional[datetime], Optional[str]]:
    """Extract due date from text using pattern matching."""
    text_lower = text.lower()
    now = datetime.now(timezone.utc)

    for pattern, days_offset in DUE_DATE_PATTERNS:
        m = re.search(pattern, text_lower)
        if m:
            if days_offset == -1:
                # Extract number from match
                try:
                    days_offset = int(m.group(1))
                except (IndexError, ValueError):
                    continue
            due = now + timedelta(days=days_offset)
            return due, f"extracted from: \"{m.group(0)}\""

    return None, None


def _is_pleasantry(text: str) -> bool:
    """Filter out generic pleasantries that aren't real obligations."""
    pleasantry_patterns = [
        r"let'?s catch up sometime",
        r"we should do something together",
        r"let'?s stay in touch",
        r"hope to see you",
        r"let'?s grab (?:coffee|lunch|dinner) sometime",
        r"nice meeting you",
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in pleasantry_patterns)


# ---------------------------------------------------------------------------
# Cindy Priority Formula
# ---------------------------------------------------------------------------

# Factor 1: Relationship Tier (30%)
RELATIONSHIP_TIER_WEIGHTS: dict[str, float] = {
    "portfolio_founder": 1.0,
    "active_deal": 0.9,
    "gp_partner": 0.85,
    "thesis_connected": 0.75,
    "devc_collective": 0.7,
    "network_known": 0.5,
    "cold_new": 0.3,
}

# Factor 3: Obligation Type (20%)
OBLIGATION_TYPE_WEIGHTS: dict[str, float] = {
    "I_OWE_THEM": 0.8,
    "THEY_OWE_ME": 0.5,
}

CATEGORY_WEIGHTS: dict[str, float] = {
    "send_document": 0.9,
    "reply": 0.85,
    "introduce": 0.8,
    "schedule": 0.75,
    "review": 0.7,
    "follow_up": 0.65,
    "deliver": 0.8,
    "connect": 0.75,
    "provide_info": 0.7,
    "other": 0.5,
}

# Factor 4: Source Reliability (15%)
SOURCE_RELIABILITY_WEIGHTS: dict[str, float] = {
    "explicit": 1.0,
    "manual": 0.9,
    "implied": 0.5,
}


def compute_cindy_priority(
    obligation: DetectedObligation,
    relationship_tier: str = "network_known",
    days_outstanding: int = 0,
) -> tuple[float, dict[str, Any]]:
    """Compute Cindy priority score (0.0 - 1.0) with factor breakdown.

    Formula:
        cindy_priority =
            relationship_tier_weight * 0.30 +
            staleness_weight         * 0.25 +
            obligation_type_weight   * 0.20 +
            source_reliability_weight * 0.15 +
            recency_weight           * 0.10
    """
    # Factor 1: Relationship Tier (30%)
    tier_weight = RELATIONSHIP_TIER_WEIGHTS.get(relationship_tier, 0.5)
    f1 = tier_weight * 0.30

    # Factor 2: Staleness (25%)
    if days_outstanding <= 2:
        staleness = 0.2
    elif days_outstanding <= 5:
        staleness = 0.5
    elif days_outstanding <= 7:
        staleness = 0.7
    elif days_outstanding <= 10:
        staleness = 0.85
    elif days_outstanding <= 14:
        staleness = 0.95
    else:
        staleness = 1.0
    f2 = staleness * 0.25

    # Factor 3: Obligation Type (20%)
    type_base = OBLIGATION_TYPE_WEIGHTS.get(obligation.obligation_type, 0.5)
    cat_weight = CATEGORY_WEIGHTS.get(obligation.category, 0.5)
    f3 = type_base * cat_weight * 0.20

    # Factor 4: Source Reliability (15%)
    reliability = SOURCE_RELIABILITY_WEIGHTS.get(obligation.detection_method, 0.5)
    f4 = reliability * 0.15

    # Factor 5: Recency (10%)
    if days_outstanding == 0:
        recency = 1.0
    elif days_outstanding <= 3:
        recency = 0.8
    elif days_outstanding <= 7:
        recency = 0.6
    else:
        recency = 0.4
    f5 = recency * 0.10

    total = f1 + f2 + f3 + f4 + f5

    factors = {
        "relationship_tier": relationship_tier,
        "relationship_tier_weight": round(f1, 4),
        "staleness_weight": round(f2, 4),
        "obligation_type_weight": round(f3, 4),
        "source_reliability_weight": round(f4, 4),
        "recency_weight": round(f5, 4),
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    return round(total, 4), factors


# ---------------------------------------------------------------------------
# Database Operations
# ---------------------------------------------------------------------------


class ObligationDBWriter:
    """Database operations for obligation detection pipeline."""

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

    async def get_interaction(self, interaction_id: int) -> Optional[dict[str, Any]]:
        """Fetch an interaction by ID."""
        if self._pool is None:
            return None
        row = await self._pool.fetchrow(
            "SELECT * FROM interactions WHERE id = $1", interaction_id,
        )
        return dict(row) if row else None

    async def get_person(self, person_id: int) -> Optional[dict[str, Any]]:
        """Fetch person from network DB."""
        if self._pool is None:
            return None
        row = await self._pool.fetchrow(
            "SELECT id, person_name, current_role, archetype FROM network WHERE id = $1",
            person_id,
        )
        return dict(row) if row else None

    async def check_dedup(
        self, person_id: int, interaction_id: Optional[int], key_phrase: str
    ) -> Optional[dict[str, Any]]:
        """Check for existing obligations with same person (dedup)."""
        if self._pool is None:
            return None

        row = await self._pool.fetchrow(
            """
            SELECT id, description, status, detected_at
            FROM obligations
            WHERE person_id = $1
              AND status IN ('pending', 'overdue', 'snoozed', 'escalated')
              AND (
                source_interaction_id = $2
                OR description ILIKE '%' || $3 || '%'
              )
            LIMIT 1
            """,
            person_id,
            interaction_id,
            key_phrase[:50],
        )
        return dict(row) if row else None

    async def write_obligation(self, obl: DetectedObligation, priority: float, factors: dict[str, Any]) -> Optional[int]:
        """Write obligation to Supabase."""
        if self.dry_run:
            logger.info(
                "[DRY RUN] Would write obligation: %s [%s] priority=%.3f",
                obl.obligation_type, obl.category, priority,
            )
            return None

        if self._pool is None:
            raise RuntimeError("Database not connected")

        row = await self._pool.fetchrow(
            """
            INSERT INTO obligations (
                person_id, person_name, person_role,
                obligation_type, description, category,
                source, source_interaction_id, source_quote, detection_method,
                detected_at, due_date, due_date_source,
                cindy_priority, cindy_priority_factors,
                context
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                NOW(), $11, $12, $13, $14::jsonb, $15::jsonb
            )
            RETURNING id
            """,
            obl.person_id or 0,
            obl.person_name,
            obl.person_role,
            obl.obligation_type,
            obl.description,
            obl.category,
            obl.source,
            obl.source_interaction_id,
            obl.source_quote,
            obl.detection_method,
            obl.due_date,
            obl.due_date_source,
            priority,
            json.dumps(factors),
            json.dumps(obl.context) if obl.context else None,
        )
        return row["id"] if row else None

    async def check_auto_fulfillment(
        self, person_id: int, interaction_id: int, source: str
    ) -> list[dict[str, Any]]:
        """Check if a new interaction resolves existing obligations."""
        if self._pool is None:
            return []

        rows = await self._pool.fetch(
            """
            SELECT id, obligation_type, category, description
            FROM obligations
            WHERE person_id = $1
              AND status IN ('pending', 'overdue')
            LIMIT 10
            """,
            person_id,
        )
        return [dict(r) for r in rows]

    async def fulfill_obligation(
        self, obligation_id: int, interaction_id: int, evidence: str
    ) -> None:
        """Mark an obligation as fulfilled."""
        if self.dry_run:
            logger.info("[DRY RUN] Would fulfill obligation #%d", obligation_id)
            return
        if self._pool is None:
            return

        await self._pool.execute(
            """
            UPDATE obligations SET
                status = 'fulfilled',
                fulfilled_at = NOW(),
                fulfilled_method = 'auto_detected',
                fulfilled_evidence = $1,
                status_changed_at = NOW(),
                updated_at = NOW()
            WHERE id = $2
            """,
            f"Resolved by interaction #{interaction_id} - {evidence}",
            obligation_id,
        )

    async def route_to_megamind(self, obligation_id: int, obl: DetectedObligation, priority: float) -> None:
        """Route high-priority obligations to Megamind via cai_inbox."""
        if self.dry_run:
            logger.info("[DRY RUN] Would route obligation #%d to Megamind (priority=%.3f)", obligation_id, priority)
            return
        if self._pool is None:
            return

        metadata = json.dumps({
            "signal_type": "obligation_priority",
            "obligation_id": obligation_id,
            "person_id": obl.person_id,
            "obligation_type": obl.obligation_type,
            "cindy_priority": priority,
            "description": obl.description,
        })
        await self._pool.execute(
            """
            INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
            VALUES ('cindy_signal', 'Obligation priority assessment request', $1::jsonb, FALSE, NOW())
            """,
            metadata,
        )
        logger.info("Routed obligation #%d to Megamind (priority=%.3f)", obligation_id, priority)

    def determine_relationship_tier(self, person: Optional[dict[str, Any]]) -> str:
        """Determine relationship tier from person data."""
        if not person:
            return "cold_new"

        archetype = (person.get("archetype") or "").lower()
        role = (person.get("current_role") or "").lower()

        if "founder" in archetype and "portfolio" in archetype:
            return "portfolio_founder"
        if "founder" in archetype:
            return "active_deal"
        if any(t in archetype for t in ["gp", "partner", "investor"]):
            return "gp_partner"
        if "collective" in role or "devc" in role:
            return "devc_collective"
        if person.get("id"):
            return "network_known"
        return "cold_new"


# ---------------------------------------------------------------------------
# Auto-Fulfillment Logic
# ---------------------------------------------------------------------------

# Maps: (existing_obligation_type, existing_category) -> what resolves it
FULFILLMENT_SIGNALS: dict[tuple[str, str], list[str]] = {
    ("I_OWE_THEM", "send_document"): ["email_with_attachment", "email_sent"],
    ("I_OWE_THEM", "reply"): ["email_sent", "whatsapp_sent"],
    ("I_OWE_THEM", "schedule"): ["calendar_event_created"],
    ("I_OWE_THEM", "introduce"): ["email_with_multiple_recipients"],
    ("THEY_OWE_ME", "send_document"): ["email_with_attachment_received"],
    ("THEY_OWE_ME", "reply"): ["email_received", "whatsapp_received"],
    ("THEY_OWE_ME", "deliver"): ["email_with_attachment_received"],
}


async def check_fulfillment(
    db: ObligationDBWriter,
    person_id: int,
    interaction_id: int,
    source: str,
    has_attachment: bool = False,
    is_from_aakash: bool = False,
) -> int:
    """Check if a new interaction fulfills existing obligations."""
    pending = await db.check_auto_fulfillment(person_id, interaction_id, source)
    fulfilled_count = 0

    for obl in pending:
        obl_type = obl["obligation_type"]
        category = obl["category"]

        should_fulfill = False
        evidence = ""

        if obl_type == "I_OWE_THEM" and is_from_aakash:
            if category == "send_document" and has_attachment and source == "email":
                should_fulfill = True
                evidence = "Aakash sent email with attachment"
            elif category == "reply" and source in ("email", "whatsapp"):
                should_fulfill = True
                evidence = f"Aakash sent {source} message"
            elif category == "schedule" and source == "calendar":
                should_fulfill = True
                evidence = "Calendar event created"
            elif category == "introduce" and source == "email":
                should_fulfill = True
                evidence = "Email sent (potential intro)"

        elif obl_type == "THEY_OWE_ME" and not is_from_aakash:
            if category == "send_document" and has_attachment and source == "email":
                should_fulfill = True
                evidence = "Person sent email with attachment"
            elif category == "reply" and source in ("email", "whatsapp"):
                should_fulfill = True
                evidence = f"Person replied via {source}"
            elif category == "deliver" and source == "email":
                should_fulfill = True
                evidence = "Received content from person"

        if should_fulfill:
            await db.fulfill_obligation(obl["id"], interaction_id, evidence)
            fulfilled_count += 1
            logger.info("Auto-fulfilled obligation #%d: %s", obl["id"], evidence)

    return fulfilled_count


# ---------------------------------------------------------------------------
# Main Processing
# ---------------------------------------------------------------------------


async def process_interaction(
    interaction_id: int,
    db: ObligationDBWriter,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Process a full interaction from the DB for obligation detection."""
    result: dict[str, Any] = {
        "interaction_id": interaction_id,
        "obligations_detected": 0,
        "obligations_fulfilled": 0,
        "i_owe": 0,
        "they_owe": 0,
    }

    interaction = await db.get_interaction(interaction_id)
    if not interaction:
        logger.error("Interaction #%d not found", interaction_id)
        return result

    source = interaction.get("source", "")
    raw_data = interaction.get("raw_data") or {}
    if isinstance(raw_data, str):
        raw_data = json.loads(raw_data)

    # Extract text content based on source
    text = interaction.get("summary", "")
    # For email, use extracted_text from raw_data if available
    if source == "email":
        text = raw_data.get("extracted_text", raw_data.get("text_body", text))

    # Get linked people
    linked_people = interaction.get("linked_people") or []

    for person_id in linked_people:
        person = await db.get_person(person_id)
        if not person:
            continue

        relationship_tier = db.determine_relationship_tier(person)

        # Detect obligations — for email, we know direction from raw_data
        is_from_aakash = raw_data.get("from_email", "").lower() in {
            "ak@z47.com", "aakash@z47.com", "aakash@devc.fund"
        }

        obligations = detect_obligations_from_text(text, is_from_aakash=is_from_aakash, source=source)

        for obl in obligations:
            obl.person_id = person_id
            obl.person_name = person.get("person_name", "")
            obl.person_role = person.get("current_role", "")
            obl.source_interaction_id = interaction_id

            # Dedup check
            key_phrase = obl.description.split('"')[1] if '"' in obl.description else obl.category
            existing = await db.check_dedup(person_id, interaction_id, key_phrase)
            if existing:
                logger.info("Dedup: obligation already exists (#%d) for person %d", existing["id"], person_id)
                continue

            # Compute priority
            priority, factors = compute_cindy_priority(obl, relationship_tier, days_outstanding=0)

            # Write obligation
            obl_id = await db.write_obligation(obl, priority, factors)

            if obl.obligation_type == "I_OWE_THEM":
                result["i_owe"] += 1
            else:
                result["they_owe"] += 1
            result["obligations_detected"] += 1

            logger.info(
                "Detected obligation: %s [%s] person=%s priority=%.3f",
                obl.obligation_type, obl.category, obl.person_name, priority,
            )

            # Route to Megamind if high priority
            if obl_id and priority > 0.7:
                await db.route_to_megamind(obl_id, obl, priority)

        # Auto-fulfillment check
        has_attachment = bool(raw_data.get("attachments"))
        fulfilled = await check_fulfillment(
            db, person_id, interaction_id, source,
            has_attachment=has_attachment, is_from_aakash=is_from_aakash,
        )
        result["obligations_fulfilled"] += fulfilled

    return result


async def process_text(
    text: str,
    source: str,
    person_id: Optional[int],
    is_from_aakash: bool,
    db: ObligationDBWriter,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Process raw text for obligation detection (standalone mode)."""
    result: dict[str, Any] = {
        "obligations_detected": 0,
        "i_owe": 0,
        "they_owe": 0,
        "obligations": [],
    }

    obligations = detect_obligations_from_text(text, is_from_aakash=is_from_aakash, source=source)

    person = None
    relationship_tier = "network_known"
    if person_id:
        person = await db.get_person(person_id)
        if person:
            relationship_tier = db.determine_relationship_tier(person)

    for obl in obligations:
        if person:
            obl.person_id = person_id
            obl.person_name = person.get("person_name", "")
            obl.person_role = person.get("current_role", "")

        priority, factors = compute_cindy_priority(obl, relationship_tier, days_outstanding=0)

        obl_id = await db.write_obligation(obl, priority, factors)

        obl_dict = {
            "type": obl.obligation_type,
            "category": obl.category,
            "description": obl.description,
            "quote": obl.source_quote,
            "priority": priority,
            "due_date": obl.due_date.isoformat() if obl.due_date else None,
        }
        result["obligations"].append(obl_dict)
        result["obligations_detected"] += 1
        if obl.obligation_type == "I_OWE_THEM":
            result["i_owe"] += 1
        else:
            result["they_owe"] += 1

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


async def run(
    interaction_id: Optional[int] = None,
    text: Optional[str] = None,
    source: str = "email",
    person_id: Optional[int] = None,
    is_from_aakash: bool = False,
    dry_run: bool = False,
) -> None:
    """Main entry point."""
    database_url = os.environ.get("DATABASE_URL", "")
    db = ObligationDBWriter(database_url, dry_run=dry_run)

    try:
        if not dry_run:
            await db.connect()

        if interaction_id:
            result = await process_interaction(interaction_id, db, dry_run)
        elif text:
            result = await process_text(text, source, person_id, is_from_aakash, db, dry_run)
        else:
            logger.error("Provide --interaction-id or --text")
            return

        logger.info(
            "Obligation detection complete: %d detected (%d I-owe, %d they-owe), %d auto-fulfilled",
            result.get("obligations_detected", 0),
            result.get("i_owe", 0),
            result.get("they_owe", 0),
            result.get("obligations_fulfilled", 0),
        )

        if dry_run:
            print(json.dumps(result, indent=2, default=str))

    finally:
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cindy Obligation Detector")
    parser.add_argument("--interaction-id", type=int, help="Process a specific interaction by ID")
    parser.add_argument("--text", type=str, help="Raw text to analyze for obligations")
    parser.add_argument("--source", type=str, default="email", help="Source surface: email, whatsapp, granola, calendar")
    parser.add_argument("--person-id", type=int, help="Network DB person ID")
    parser.add_argument("--from-aakash", action="store_true", help="Text is from Aakash")
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    args = parser.parse_args()

    asyncio.run(run(
        interaction_id=args.interaction_id,
        text=args.text,
        source=args.source,
        person_id=args.person_id,
        is_from_aakash=args.from_aakash,
        dry_run=args.dry_run,
    ))


if __name__ == "__main__":
    main()
