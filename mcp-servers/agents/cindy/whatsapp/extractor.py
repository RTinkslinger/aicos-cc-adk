#!/usr/bin/env python3
"""
WhatsApp iCloud Backup Extractor for Cindy.

Reads ChatStorage.sqlite from iCloud backup, parses conversations,
resolves participants against Network DB, classifies conversations,
extracts signals, and writes structured interaction records to Postgres.

Runs on Mac as a daily cron job. Only structured summaries travel to the DB —
raw message text is NEVER stored (privacy-critical).

Usage:
    python3 -m cindy.whatsapp.extractor                      # last 24h
    python3 -m cindy.whatsapp.extractor --since 48h          # last 48 hours
    python3 -m cindy.whatsapp.extractor --since 7d           # last 7 days
    python3 -m cindy.whatsapp.extractor --dry-run             # preview without DB writes
    python3 -m cindy.whatsapp.extractor --dry-run --since 2h  # preview last 2 hours
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cindy.whatsapp")

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# WhatsApp Mac app path (primary — unencrypted sqlite)
WHATSAPP_MAC_APP_DB = Path.home() / "Library" / "Group Containers" / "group.net.whatsapp.WhatsApp.shared" / "ChatStorage.sqlite"

# iCloud WhatsApp backup path (fallback — .enc files, usually encrypted)
ICLOUD_WHATSAPP_BASE = Path.home() / "Library" / "Mobile Documents" / "57T9237FN3~net~whatsapp~WhatsApp"

# State file for incremental extraction
STATE_DIR = Path(__file__).parent.parent / "state"
LAST_EXTRACTION_FILE = STATE_DIR / "whatsapp_last_extraction.json"

# Aakash's known phone identifiers (skip during people resolution)
AAKASH_JIDS = {
    "919820820663@s.whatsapp.net",
}

# Internal group keywords (skip gap detection)
INTERNAL_GROUP_KEYWORDS = {"z47", "devc", "internal", "team"}

# Batch limit per CLAUDE.md anti-pattern #20
MAX_CONVERSATIONS_PER_RUN = 20

# Apple Core Foundation epoch (2001-01-01 00:00:00 UTC)
CF_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class WhatsAppMessage:
    """Single WhatsApp message (in-memory only, never persisted raw)."""

    pk: int
    sender_jid: str
    is_from_me: bool
    text: Optional[str]
    timestamp: datetime
    message_type: int  # 0=text, 1=image, 2=video, 3=voice, 5=location, 7=doc
    reply_to_pk: Optional[int] = None

    @property
    def is_text(self) -> bool:
        return self.message_type == 0

    @property
    def is_media(self) -> bool:
        return self.message_type in (1, 2, 3, 5, 7, 8)

    @property
    def media_type_name(self) -> str:
        names = {1: "image", 2: "video", 3: "voice_note", 5: "location", 7: "document", 8: "sticker"}
        return names.get(self.message_type, "unknown")


@dataclass
class WhatsAppConversation:
    """Parsed WhatsApp conversation with messages."""

    chat_pk: int
    chat_jid: str
    chat_name: str
    session_type: int  # 0 = 1:1, 1 = group
    messages: list[WhatsAppMessage] = field(default_factory=list)
    participant_jids: list[str] = field(default_factory=list)

    @property
    def is_group(self) -> bool:
        return self.session_type == 1

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def text_messages(self) -> list[WhatsAppMessage]:
        return [m for m in self.messages if m.is_text and m.text]

    @property
    def media_types(self) -> list[str]:
        return list({m.media_type_name for m in self.messages if m.is_media})

    @property
    def has_voice_notes(self) -> bool:
        return any(m.message_type == 3 for m in self.messages)

    @property
    def time_span(self) -> dict[str, Optional[str]]:
        if not self.messages:
            return {"first": None, "last": None}
        timestamps = sorted(m.timestamp for m in self.messages)
        return {
            "first": timestamps[0].isoformat(),
            "last": timestamps[-1].isoformat(),
        }

    @property
    def source_id(self) -> str:
        """Unique source ID for dedup: wa_{jid}_{date}."""
        if self.messages:
            date_str = self.messages[-1].timestamp.strftime("%Y%m%d")
        else:
            date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        clean_jid = self.chat_jid.replace("@s.whatsapp.net", "").replace("@g.us", "_g")
        return f"wa_{clean_jid}_{date_str}"


# ---------------------------------------------------------------------------
# Timestamp Conversion
# ---------------------------------------------------------------------------


def cf_to_datetime(cf_timestamp: float) -> datetime:
    """Convert Apple Core Foundation timestamp to UTC datetime."""
    return CF_EPOCH + timedelta(seconds=cf_timestamp)


def datetime_to_cf(dt: datetime) -> float:
    """Convert UTC datetime to Apple Core Foundation timestamp."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt - CF_EPOCH).total_seconds()


# ---------------------------------------------------------------------------
# SQLite Reader (ChatStorage.sqlite)
# ---------------------------------------------------------------------------


def find_chat_storage() -> Optional[Path]:
    """Locate ChatStorage.sqlite — prefer Mac app (unencrypted), fall back to iCloud backup."""
    # Primary: WhatsApp Mac native app (unencrypted sqlite, syncs from phone)
    if WHATSAPP_MAC_APP_DB.exists():
        logger.info("Found WhatsApp Mac app database: %s", WHATSAPP_MAC_APP_DB)
        return WHATSAPP_MAC_APP_DB

    # Fallback: iCloud backup directory
    if not ICLOUD_WHATSAPP_BASE.exists():
        logger.error(
            "WhatsApp database not found. Install WhatsApp for Mac from the App Store, "
            "or check iCloud backup at: %s", ICLOUD_WHATSAPP_BASE
        )
        return None

    accounts_dir = ICLOUD_WHATSAPP_BASE / "Accounts"
    if not accounts_dir.exists():
        logger.error("Accounts directory not found: %s", accounts_dir)
        return None

    for account_dir in accounts_dir.iterdir():
        if not account_dir.is_dir():
            continue

        backup_dir = account_dir / "backup"
        if not backup_dir.exists():
            continue

        plain_db = backup_dir / "ChatStorage.sqlite"
        if plain_db.exists():
            logger.info("Found decrypted ChatStorage.sqlite: %s", plain_db)
            return plain_db

        enc_db = backup_dir / "ChatStorage.sqlite.enc"
        if enc_db.exists():
            logger.error(
                "Found ENCRYPTED ChatStorage.sqlite.enc at %s. "
                "Use WhatsApp Mac app instead (primary path).",
                enc_db,
            )
            return None

    logger.error("No ChatStorage.sqlite found")
    return None


def read_conversations(
    db_path: Path,
    since_cf: float,
) -> list[WhatsAppConversation]:
    """Read conversations with messages since the given CF timestamp."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conversations: list[WhatsAppConversation] = []

    try:
        # 1. Find conversations with recent messages
        cursor = conn.execute(
            """
            SELECT cs.Z_PK, cs.ZCONTACTJID, cs.ZPARTNERNAME, cs.ZSESSIONTYPE,
                   MAX(m.ZMESSAGEDATE) as last_msg_date
            FROM ZWACHATSESSION cs
            JOIN ZWAMESSAGE m ON m.ZCHATSESSION = cs.Z_PK
            WHERE m.ZMESSAGEDATE > ?
              AND cs.ZCONTACTJID IS NOT NULL
              AND cs.ZCONTACTJID != 'status@broadcast'
            GROUP BY cs.Z_PK, cs.ZCONTACTJID, cs.ZPARTNERNAME, cs.ZSESSIONTYPE
            ORDER BY last_msg_date DESC
            LIMIT ?
            """,
            (since_cf, MAX_CONVERSATIONS_PER_RUN),
        )

        chat_rows = cursor.fetchall()
        logger.info("Found %d conversations with recent activity", len(chat_rows))

        for chat_row in chat_rows:
            chat_pk = chat_row["Z_PK"]
            chat_jid = chat_row["ZCONTACTJID"] or ""
            chat_name = chat_row["ZPARTNERNAME"] or ""
            session_type = chat_row["ZSESSIONTYPE"] or 0

            # 2. Fetch messages for this conversation
            msg_cursor = conn.execute(
                """
                SELECT Z_PK, ZFROMJID, ZISFROMME, ZTEXT, ZMESSAGEDATE,
                       ZMESSAGETYPE, ZPARENTMESSAGE
                FROM ZWAMESSAGE
                WHERE ZCHATSESSION = ? AND ZMESSAGEDATE > ?
                ORDER BY ZMESSAGEDATE ASC
                """,
                (chat_pk, since_cf),
            )

            messages: list[WhatsAppMessage] = []
            for msg_row in msg_cursor:
                msg_date = msg_row["ZMESSAGEDATE"]
                if msg_date is None:
                    continue

                messages.append(WhatsAppMessage(
                    pk=msg_row["Z_PK"],
                    sender_jid=msg_row["ZFROMJID"] or "",
                    is_from_me=bool(msg_row["ZISFROMME"]),
                    text=msg_row["ZTEXT"],
                    timestamp=cf_to_datetime(msg_date),
                    message_type=msg_row["ZMESSAGETYPE"] or 0,
                    reply_to_pk=msg_row["ZPARENTMESSAGE"],
                ))

            if not messages:
                continue

            # 3. For group chats, collect participant JIDs
            participant_jids: list[str] = []
            if session_type == 1:
                # Collect unique sender JIDs from messages
                participant_jids = list({
                    m.sender_jid for m in messages
                    if m.sender_jid and m.sender_jid not in AAKASH_JIDS
                })

            # 4. Try to get display name from push names if chat_name is empty
            if not chat_name and chat_jid:
                name_cursor = conn.execute(
                    "SELECT ZPUSHNAME FROM ZWAPROFILEPUSHNAME WHERE ZJID = ?",
                    (chat_jid,),
                )
                name_row = name_cursor.fetchone()
                if name_row:
                    chat_name = name_row["ZPUSHNAME"] or ""

            conversations.append(WhatsAppConversation(
                chat_pk=chat_pk,
                chat_jid=chat_jid,
                chat_name=chat_name,
                session_type=session_type,
                messages=messages,
                participant_jids=participant_jids,
            ))

    finally:
        conn.close()

    return conversations


# ---------------------------------------------------------------------------
# Conversation Classification
# ---------------------------------------------------------------------------

# Patterns for classification (applied to concatenated text of conversation)
DEAL_PATTERNS = re.compile(
    r"term\s*sheet|valuation|pre[-\s]?money|post[-\s]?money|series\s+[a-e]|"
    r"seed\s+round|bridge|fundrais|cap\s*table|runway|diligence|data\s*room|"
    r"ic\s+(?:meeting|review|deck)|\$\d+[MmBb]",
    re.IGNORECASE,
)

PORTFOLIO_PATTERNS = re.compile(
    r"portfolio|burn\s*rate|arr\s|mrr\s|revenue|growth\s+rate|churn|"
    r"customer\s+acquisition|unit\s+economics|board\s+meeting|quarterly",
    re.IGNORECASE,
)

THESIS_PATTERNS = re.compile(
    r"agentic|ai\s+agent|developer\s+tools?|fintech|climate\s*tech|"
    r"cybersecurity|market\s+(?:trend|shift|signal)|competitive\s+landscape|"
    r"emerging\s+(?:space|sector|trend)",
    re.IGNORECASE,
)

OPERATIONAL_PATTERNS = re.compile(
    r"(?:meeting|call|sync)\s+(?:at|on|tomorrow|today)|schedule|"
    r"running\s+late|on\s+my\s+way|office|logistics|travel",
    re.IGNORECASE,
)


def classify_conversation(conv: WhatsAppConversation) -> str:
    """Classify a conversation: deal, portfolio, thesis, operational, or social.

    Only deal, portfolio, and thesis conversations get signal extraction.
    """
    # Concatenate text messages for pattern matching (in-memory only)
    all_text = " ".join(m.text for m in conv.text_messages if m.text)

    if not all_text:
        return "social"

    if DEAL_PATTERNS.search(all_text):
        return "deal"
    if PORTFOLIO_PATTERNS.search(all_text):
        return "portfolio"
    if THESIS_PATTERNS.search(all_text):
        return "thesis"
    if OPERATIONAL_PATTERNS.search(all_text):
        return "operational"

    return "social"


# ---------------------------------------------------------------------------
# Signal Extraction (in-memory, raw text never stored)
# ---------------------------------------------------------------------------


def extract_action_items(conv: WhatsAppConversation) -> list[str]:
    """Extract action items from conversation text."""
    actions: list[str] = []
    patterns = [
        r"(?:let'?s|can we|should we|need to|let me|i'?ll)\s+(.{10,80})",
        r"(?:please|could you|can you|would you)\s+(.{10,80})",
        r"(?:action|todo|follow[- ]?up)[:;]\s*(.{10,80})",
        r"by (?:friday|monday|tuesday|wednesday|thursday|saturday|sunday|tomorrow|next week|eow|eod)(.{0,60})",
    ]

    for msg in conv.text_messages:
        if not msg.text:
            continue
        for pattern in patterns:
            for match in re.finditer(pattern, msg.text, re.IGNORECASE):
                action = match.group(0).strip().rstrip(".,;:")
                if len(action) > 15 and action not in actions:
                    actions.append(action)

    return actions[:10]


def extract_deal_signals(conv: WhatsAppConversation) -> list[dict[str, str]]:
    """Detect deal-related signals from conversation."""
    signals: list[dict[str, str]] = []
    all_text = " ".join(m.text for m in conv.text_messages if m.text)

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


def extract_thesis_signals(conv: WhatsAppConversation) -> list[dict[str, str]]:
    """Detect thesis-relevant signals."""
    signals: list[dict[str, str]] = []
    all_text = " ".join(m.text for m in conv.text_messages if m.text)

    thesis_keywords = {
        "agentic_ai": r"(?:agentic|ai\s+agent|autonomous\s+agent|agent\s+(?:framework|infra))",
        "developer_tools": r"(?:dev\s*tools?|developer\s+(?:experience|platform)|devops|ci/?cd)",
        "fintech": r"(?:fintech|digital\s+(?:payments?|banking|lending)|neobank)",
        "climate": r"(?:climate\s*tech|carbon|sustainability|clean\s*energy|ev\s)",
        "cybersecurity": r"(?:cyber\s*security|infosec|zero\s*trust|siem|soc\s)",
    }
    for thesis_name, pattern in thesis_keywords.items():
        if re.search(pattern, all_text, re.IGNORECASE):
            signals.append({"thesis": thesis_name, "signal": "mention", "strength": "weak"})

    return signals


def generate_conversation_summary(conv: WhatsAppConversation, classification: str) -> str:
    """Generate a structured summary WITHOUT including raw message text.

    This is the ONLY text that gets stored. Raw messages are used for
    classification and signal extraction in-memory, then discarded.
    """
    parts = [f"{conv.chat_name or conv.chat_jid}"]

    if conv.is_group:
        parts.append(f"(group, {len(conv.participant_jids)} participants)")
    else:
        parts.append("(1:1)")

    parts.append(f"— {conv.message_count} messages")
    parts.append(f"[{classification}]")

    if conv.media_types:
        parts.append(f"Media: {', '.join(conv.media_types)}")

    if conv.has_voice_notes:
        parts.append("(includes voice notes)")

    # Add topic-level summary based on classification (no raw text)
    if classification == "deal":
        parts.append("— deal-related discussion")
    elif classification == "portfolio":
        parts.append("— portfolio update discussion")
    elif classification == "thesis":
        parts.append("— thesis-relevant discussion")
    elif classification == "operational":
        parts.append("— scheduling/logistics")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Phone Number Utilities
# ---------------------------------------------------------------------------


def jid_to_phone(jid: str) -> str:
    """Extract phone number from WhatsApp JID.

    '919999999999@s.whatsapp.net' -> '+919999999999'
    """
    number = jid.replace("@s.whatsapp.net", "").replace("@g.us", "")
    if number and number[0] != "+":
        number = f"+{number}"
    return number


# ---------------------------------------------------------------------------
# Database Operations
# ---------------------------------------------------------------------------


class WhatsAppDBWriter:
    """Async Postgres writer for WhatsApp interactions."""

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
        """Check if interaction already exists (dedup)."""
        if self._pool is None:
            return None
        row = await self._pool.fetchrow(
            "SELECT id FROM interactions WHERE source = 'whatsapp' AND source_id = $1",
            source_id,
        )
        return row["id"] if row else None

    async def resolve_person_by_phone(self, phone: str) -> Optional[dict[str, Any]]:
        """Tier 2 resolution: match by phone number."""
        if self._pool is None:
            return None
        row = await self._pool.fetchrow(
            "SELECT id, person_name, role_title FROM network WHERE phone = $1",
            phone,
        )
        return dict(row) if row else None

    async def resolve_person_by_name(self, name: str) -> list[dict[str, Any]]:
        """Tier 5 resolution: match by name (may return multiple)."""
        if self._pool is None:
            return []
        rows = await self._pool.fetch(
            "SELECT id, person_name, role_title, email, phone FROM network WHERE LOWER(person_name) = LOWER($1)",
            name,
        )
        return [dict(r) for r in rows]

    async def write_interaction(
        self,
        conv: WhatsAppConversation,
        classification: str,
        summary: str,
        linked_ids: list[int],
        signals: dict[str, Any],
    ) -> Optional[int]:
        """Write WhatsApp interaction to DB. Raw text is NEVER stored."""
        if self.dry_run:
            logger.info("[DRY RUN] Would write interaction: %s", conv.source_id)
            return None

        if self._pool is None:
            raise RuntimeError("Database not connected")

        # raw_data contains ONLY metadata — never raw message text
        raw_data = json.dumps({
            "chat_name": conv.chat_name,
            "session_type": conv.session_type,
            "message_count": conv.message_count,
            "time_span": conv.time_span,
            "media_types": conv.media_types,
            "has_voice_notes": conv.has_voice_notes,
            "classification": classification,
        })

        # Participants as phone numbers
        participants = []
        if conv.is_group:
            participants = [jid_to_phone(jid) for jid in conv.participant_jids if jid]
        else:
            participants = [jid_to_phone(conv.chat_jid)] if conv.chat_jid else []

        # Timestamp from last message
        last_ts = conv.messages[-1].timestamp if conv.messages else datetime.now(timezone.utc)

        row = await self._pool.fetchrow(
            """
            INSERT INTO interactions (
                source, source_id, thread_id, participants, linked_people,
                summary, raw_data, timestamp, action_items,
                thesis_signals, deal_signals
            ) VALUES (
                'whatsapp', $1, $2, $3, $4, $5, $6::jsonb, $7::timestamptz,
                $8, $9::jsonb, $10::jsonb
            )
            ON CONFLICT (source, source_id) DO UPDATE SET
                summary = COALESCE(EXCLUDED.summary, interactions.summary),
                linked_people = COALESCE(EXCLUDED.linked_people, interactions.linked_people),
                action_items = COALESCE(EXCLUDED.action_items, interactions.action_items),
                thesis_signals = COALESCE(EXCLUDED.thesis_signals, interactions.thesis_signals),
                deal_signals = COALESCE(EXCLUDED.deal_signals, interactions.deal_signals),
                updated_at = NOW()
            RETURNING id
            """,
            conv.source_id,                                              # $1
            conv.chat_jid or None,                                       # $2 thread_id
            participants,                                                 # $3
            linked_ids if linked_ids else None,                           # $4
            summary,                                                      # $5
            raw_data,                                                     # $6
            last_ts.isoformat(),                                          # $7
            signals.get("action_items", []),                              # $8
            json.dumps(signals.get("thesis_signals", [])),                # $9
            json.dumps(signals.get("deal_signals", [])),                  # $10
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
            if self.dry_run:
                logger.info(
                    "[DRY RUN] Would link person %d to interaction %d",
                    person_id, interaction_id,
                )
            return
        await self._pool.execute(
            """
            INSERT INTO people_interactions (person_id, interaction_id, role, surface,
                                              identifier_used, link_confidence)
            VALUES ($1, $2, $3, 'whatsapp', $4, $5)
            ON CONFLICT (person_id, interaction_id) DO NOTHING
            """,
            person_id, interaction_id, role, identifier, confidence,
        )

    async def write_datum_request(
        self,
        phone: str,
        name: str,
        context: str,
        interaction_id: Optional[int],
    ) -> None:
        """Send unknown person to Datum Agent via cai_inbox."""
        if self.dry_run:
            logger.info("[DRY RUN] Would send datum_person for %s (%s)", name, phone)
            return
        if self._pool is None:
            return
        metadata = json.dumps({
            "name": name,
            "phone": phone,
            "source": "cindy_whatsapp",
            "context": context,
            "interaction_id": interaction_id,
        })
        await self._pool.execute(
            """
            INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
            VALUES ('datum_person', $1, $2::jsonb, FALSE, NOW())
            """,
            f"New person from WhatsApp: {name} ({phone})",
            metadata,
        )

    async def write_action_items(
        self,
        actions: list[str],
        conv: WhatsAppConversation,
        classification: str,
    ) -> None:
        """Write extracted action items to actions_queue."""
        if self.dry_run or self._pool is None:
            return
        for action_text in actions:
            await self._pool.execute(
                """
                INSERT INTO actions_queue (action, action_type, priority, status,
                                           assigned_to, source, reasoning, notion_synced,
                                           created_at, updated_at)
                VALUES ($1, 'Meeting/Outreach', 'P1 - This Week', 'Proposed',
                        'Aakash', 'Cindy-WhatsApp', $2, FALSE, NOW(), NOW())
                """,
                action_text,
                f"Extracted from WhatsApp conversation with {conv.chat_name} [{classification}]",
            )

    async def write_thesis_signal(
        self,
        signals: list[dict[str, str]],
        conv: WhatsAppConversation,
        interaction_id: Optional[int],
    ) -> None:
        """Route strong thesis signals to Megamind via cai_inbox."""
        if self.dry_run or self._pool is None or not signals:
            return
        metadata = json.dumps({
            "signal_type": "thesis_conviction",
            "strength": "weak",
            "summary": f"Thesis signals from WhatsApp with {conv.chat_name}",
            "thesis_connections": [s.get("thesis", "") for s in signals],
            "interaction_id": interaction_id,
        })
        await self._pool.execute(
            """
            INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
            VALUES ('cindy_signal', $1, $2::jsonb, FALSE, NOW())
            """,
            f"Thesis signal from WhatsApp conversation with {conv.chat_name}",
            metadata,
        )


# ---------------------------------------------------------------------------
# State Management (incremental extraction)
# ---------------------------------------------------------------------------


def load_last_extraction() -> Optional[float]:
    """Load last extraction CF timestamp from state file."""
    if not LAST_EXTRACTION_FILE.exists():
        return None
    try:
        data = json.loads(LAST_EXTRACTION_FILE.read_text())
        return data.get("last_cf_timestamp")
    except (json.JSONDecodeError, KeyError):
        return None


def save_last_extraction(cf_timestamp: float) -> None:
    """Save last extraction CF timestamp to state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LAST_EXTRACTION_FILE.write_text(json.dumps({
        "last_cf_timestamp": cf_timestamp,
        "last_extraction_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2))


# ---------------------------------------------------------------------------
# Main Processing
# ---------------------------------------------------------------------------


async def process_conversation(
    conv: WhatsAppConversation,
    db: WhatsAppDBWriter,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Process a single conversation: classify, resolve people, extract signals, write."""
    result: dict[str, Any] = {
        "source_id": conv.source_id,
        "chat_name": conv.chat_name,
        "message_count": conv.message_count,
        "action": "skipped",
        "people_linked": 0,
        "people_new": 0,
    }

    # Skip empty conversations
    if conv.message_count == 0:
        result["action"] = "skipped_empty"
        return result

    # 1. Dedup check
    existing_id = await db.interaction_exists(conv.source_id)
    if existing_id:
        logger.info("Already processed: %s (interaction #%d)", conv.source_id, existing_id)
        result["action"] = "already_processed"
        result["interaction_id"] = existing_id
        return result

    # 2. Classify conversation
    classification = classify_conversation(conv)
    result["classification"] = classification

    # 3. Resolve participants
    linked_ids: list[int] = []
    jids_to_resolve = conv.participant_jids if conv.is_group else [conv.chat_jid]

    for jid in jids_to_resolve:
        if not jid or jid in AAKASH_JIDS or "@g.us" in jid:
            continue

        phone = jid_to_phone(jid)

        # Tier 2: Phone match
        person = await db.resolve_person_by_phone(phone)
        if person:
            linked_ids.append(person["id"])
            result["people_linked"] += 1
            logger.info("Linked by phone: %s -> %s (#%d)", phone, person["person_name"], person["id"])
            continue

        # Tier 5: Name match (using push name / chat name)
        name = conv.chat_name if not conv.is_group else ""
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

        # Tier 6: Unresolved — send to Datum Agent
        await db.write_datum_request(
            phone,
            conv.chat_name if not conv.is_group else f"participant in {conv.chat_name}",
            f"WhatsApp {'group' if conv.is_group else '1:1'} conversation",
            None,
        )
        result["people_new"] += 1
        logger.info("New person (sent to Datum): %s (%s)", conv.chat_name, phone)

    # 4. Generate summary (NO raw text)
    summary = generate_conversation_summary(conv, classification)

    # 5. Extract signals (only for high-signal classifications)
    signals: dict[str, Any] = {
        "action_items": [],
        "deal_signals": [],
        "thesis_signals": [],
    }

    if classification in ("deal", "portfolio", "thesis"):
        signals["action_items"] = extract_action_items(conv)
        signals["deal_signals"] = extract_deal_signals(conv)
        signals["thesis_signals"] = extract_thesis_signals(conv)

    result["signals"] = {k: len(v) for k, v in signals.items()}

    # 6. Write interaction
    interaction_id = await db.write_interaction(conv, classification, summary, linked_ids, signals)
    result["action"] = "processed"
    result["interaction_id"] = interaction_id

    # 7. Write people links
    if interaction_id:
        for person_id in linked_ids:
            phone = ""
            for jid in jids_to_resolve:
                if jid and jid not in AAKASH_JIDS:
                    p = await db.resolve_person_by_phone(jid_to_phone(jid))
                    if p and p["id"] == person_id:
                        phone = jid_to_phone(jid)
                        break

            await db.write_people_interaction(
                person_id, interaction_id, "participant",
                f"phone:{phone}" if phone else f"name:{conv.chat_name}",
                1.0 if phone else 0.80,
            )

    # 8. Write action items to actions_queue
    if signals["action_items"]:
        await db.write_action_items(signals["action_items"], conv, classification)

    # 9. Route thesis signals
    if signals["thesis_signals"]:
        await db.write_thesis_signal(signals["thesis_signals"], conv, interaction_id)

    return result


async def run(
    dry_run: bool = False,
    since: Optional[str] = None,
) -> None:
    """Main entry point: find ChatStorage.sqlite, extract, process."""
    database_url = os.environ.get("DATABASE_URL", "")

    if not database_url and not dry_run:
        logger.error("DATABASE_URL not set (required when not in --dry-run mode)")
        sys.exit(1)

    # 1. Find ChatStorage.sqlite
    db_path = find_chat_storage()
    if db_path is None:
        logger.error("Cannot proceed without ChatStorage.sqlite")
        sys.exit(1)

    # 2. Determine time range
    since_dt: Optional[datetime] = None
    if since:
        m = re.match(r"(\d+)([hmd])", since)
        if m:
            val, unit = int(m.group(1)), m.group(2)
            delta = {"h": timedelta(hours=val), "m": timedelta(minutes=val), "d": timedelta(days=val)}
            since_dt = datetime.now(timezone.utc) - delta.get(unit, timedelta(hours=val))
    else:
        # Default: last 24 hours, or last extraction timestamp
        last_cf = load_last_extraction()
        if last_cf:
            since_dt = cf_to_datetime(last_cf)
            logger.info("Resuming from last extraction: %s", since_dt.isoformat())
        else:
            since_dt = datetime.now(timezone.utc) - timedelta(hours=24)

    since_cf = datetime_to_cf(since_dt)
    logger.info("Extracting messages since: %s (CF: %.2f)", since_dt.isoformat(), since_cf)

    # 3. Read conversations from SQLite
    conversations = read_conversations(db_path, since_cf)
    logger.info("Read %d conversations from ChatStorage.sqlite", len(conversations))

    if not conversations:
        logger.info("No new conversations to process")
        return

    # 4. Process conversations
    db = WhatsAppDBWriter(database_url, dry_run=dry_run)

    try:
        if not dry_run:
            await db.connect()

        results: list[dict[str, Any]] = []
        for conv in conversations:
            result = await process_conversation(conv, db, dry_run=dry_run)
            results.append(result)

        # 5. Summary
        processed = [r for r in results if r["action"] == "processed"]
        skipped = [r for r in results if r["action"] == "already_processed"]
        classifications = {}
        for r in processed:
            cls = r.get("classification", "unknown")
            classifications[cls] = classifications.get(cls, 0) + 1

        total_people = sum(r.get("people_linked", 0) for r in processed)
        total_new = sum(r.get("people_new", 0) for r in processed)
        total_actions = sum(r.get("signals", {}).get("action_items", 0) for r in processed)
        total_thesis = sum(r.get("signals", {}).get("thesis_signals", 0) for r in processed)

        cls_str = ", ".join(f"{count} {cls}" for cls, count in classifications.items())

        logger.info(
            "WhatsApp processing complete: %d processed (%s), %d skipped, "
            "%d people linked, %d new, %d actions, %d thesis signals",
            len(processed), cls_str, len(skipped),
            total_people, total_new, total_actions, total_thesis,
        )

        # 6. Save extraction timestamp for incremental runs
        if not dry_run and conversations:
            latest_cf = max(
                datetime_to_cf(msg.timestamp)
                for conv in conversations
                for msg in conv.messages
            )
            save_last_extraction(latest_cf)

        if dry_run:
            print(json.dumps(results, indent=2, default=str))

    finally:
        await db.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Cindy WhatsApp iCloud Backup Extractor")
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    parser.add_argument(
        "--since", type=str,
        help="Time window: e.g. 2h, 30m, 7d (default: since last extraction or 24h)",
    )
    args = parser.parse_args()

    asyncio.run(run(dry_run=args.dry_run, since=args.since))


if __name__ == "__main__":
    main()
