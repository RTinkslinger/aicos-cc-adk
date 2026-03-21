#!/usr/bin/env python3
"""
WhatsApp iCloud Backup Extractor for Cindy — Plumbing Only.

Reads ChatStorage.sqlite from WhatsApp Mac app (or iCloud backup),
parses conversations, and stages raw structured data in interaction_staging.
NO signal extraction, NO people resolution, NO obligation detection, NO action creation.

Datum Agent handles: participant resolution (phone->network), entity linking, writing to interactions.
Cindy Agent handles: LLM-based signal extraction, obligation reasoning, action creation.

Privacy: Raw message text is NEVER stored in the database. Only structured metadata
(participant list, message count, media types, timestamps) is staged.

Usage:
    python3 -m cindy.whatsapp.extractor                      # last 24h
    python3 -m cindy.whatsapp.extractor --since 48h          # last 48 hours
    python3 -m cindy.whatsapp.extractor --since 7d           # last 7 days
    python3 -m cindy.whatsapp.extractor --dry-run             # preview without DB writes
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
WHATSAPP_MAC_APP_DB = (
    Path.home()
    / "Library"
    / "Group Containers"
    / "group.net.whatsapp.WhatsApp.shared"
    / "ChatStorage.sqlite"
)

# iCloud WhatsApp backup path (fallback)
ICLOUD_WHATSAPP_BASE = (
    Path.home()
    / "Library"
    / "Mobile Documents"
    / "57T9237FN3~net~whatsapp~WhatsApp"
)

STATE_DIR = Path(__file__).parent.parent / "state"
LAST_EXTRACTION_FILE = STATE_DIR / "whatsapp_last_extraction.json"

# Aakash's JIDs (skip during participant listing)
AAKASH_JIDS = {"919820820663@s.whatsapp.net"}

# Internal group keywords (Datum will use for classification)
INTERNAL_GROUP_KEYWORDS = {"z47", "devc", "internal", "team"}

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
        names = {
            1: "image", 2: "video", 3: "voice_note",
            5: "location", 7: "document", 8: "sticker",
        }
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
        if self.messages:
            date_str = self.messages[-1].timestamp.strftime("%Y%m%d")
        else:
            date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        clean_jid = self.chat_jid.replace("@s.whatsapp.net", "").replace("@g.us", "_g")
        return f"wa_{clean_jid}_{date_str}"

    def to_staging_json(self) -> dict[str, Any]:
        """Convert to raw JSON for staging. NEVER includes raw message text."""
        # Determine if this is likely internal
        is_internal = any(
            kw in (self.chat_name or "").lower()
            for kw in INTERNAL_GROUP_KEYWORDS
        )

        # Participants as phone numbers
        participants = []
        if self.is_group:
            participants = [jid_to_phone(jid) for jid in self.participant_jids if jid]
        else:
            participants = [jid_to_phone(self.chat_jid)] if self.chat_jid else []

        return {
            "chat_jid": self.chat_jid,
            "chat_name": self.chat_name,
            "session_type": self.session_type,
            "is_group": self.is_group,
            "is_internal": is_internal,
            "message_count": self.message_count,
            "text_message_count": len(self.text_messages),
            "time_span": self.time_span,
            "media_types": self.media_types,
            "has_voice_notes": self.has_voice_notes,
            "participants": participants,
            "participant_count": len(participants),
            # Message-level metadata (NO raw text)
            "from_me_count": sum(1 for m in self.messages if m.is_from_me),
            "from_others_count": sum(1 for m in self.messages if not m.is_from_me),
            "has_replies": any(m.reply_to_pk for m in self.messages),
        }


# ---------------------------------------------------------------------------
# Timestamp Conversion
# ---------------------------------------------------------------------------


def cf_to_datetime(cf_timestamp: float) -> datetime:
    return CF_EPOCH + timedelta(seconds=cf_timestamp)


def datetime_to_cf(dt: datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt - CF_EPOCH).total_seconds()


# ---------------------------------------------------------------------------
# Phone Number Utilities
# ---------------------------------------------------------------------------


def jid_to_phone(jid: str) -> str:
    number = jid.replace("@s.whatsapp.net", "").replace("@g.us", "")
    if number and number[0] != "+":
        number = f"+{number}"
    return number


# ---------------------------------------------------------------------------
# SQLite Reader (ChatStorage.sqlite)
# ---------------------------------------------------------------------------


def find_chat_storage() -> Optional[Path]:
    """Locate ChatStorage.sqlite."""
    if WHATSAPP_MAC_APP_DB.exists():
        logger.info("Found WhatsApp Mac app database: %s", WHATSAPP_MAC_APP_DB)
        return WHATSAPP_MAC_APP_DB

    if not ICLOUD_WHATSAPP_BASE.exists():
        logger.error(
            "WhatsApp database not found. Install WhatsApp for Mac from the App Store, "
            "or check iCloud backup at: %s",
            ICLOUD_WHATSAPP_BASE,
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
                "Use WhatsApp Mac app instead.",
                enc_db,
            )
            return None

    logger.error("No ChatStorage.sqlite found")
    return None


def read_conversations(db_path: Path, since_cf: float) -> list[WhatsAppConversation]:
    """Read conversations with messages since the given CF timestamp."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conversations: list[WhatsAppConversation] = []

    try:
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

            participant_jids: list[str] = []
            if session_type == 1:
                participant_jids = list({
                    m.sender_jid for m in messages
                    if m.sender_jid and m.sender_jid not in AAKASH_JIDS
                })

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
# Staging Writer
# ---------------------------------------------------------------------------


class StagingWriter:
    """Writes raw WhatsApp data to interaction_staging table."""

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
            "SELECT id FROM interaction_staging WHERE source = 'whatsapp' AND source_id = $1",
            source_id,
        )
        return row is not None

    async def stage(self, conv: WhatsAppConversation) -> Optional[int]:
        if self.dry_run:
            logger.info("[DRY RUN] Would stage conversation: %s — %s", conv.source_id, conv.chat_name)
            return None
        if self._pool is None:
            raise RuntimeError("Database not connected")

        row = await self._pool.fetchrow(
            """
            INSERT INTO interaction_staging (source, source_id, raw_data)
            VALUES ('whatsapp', $1, $2::jsonb)
            ON CONFLICT (source, source_id) DO NOTHING
            RETURNING id
            """,
            conv.source_id,
            json.dumps(conv.to_staging_json()),
        )
        return row["id"] if row else None


# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------


def load_last_extraction() -> Optional[float]:
    if not LAST_EXTRACTION_FILE.exists():
        return None
    try:
        data = json.loads(LAST_EXTRACTION_FILE.read_text())
        return data.get("last_cf_timestamp")
    except (json.JSONDecodeError, KeyError):
        return None


def save_last_extraction(cf_timestamp: float) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LAST_EXTRACTION_FILE.write_text(json.dumps({
        "last_cf_timestamp": cf_timestamp,
        "last_extraction_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2))


# ---------------------------------------------------------------------------
# Main Fetcher
# ---------------------------------------------------------------------------


async def extract_and_stage(
    dry_run: bool = False,
    since: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Extract WhatsApp conversations and stage raw metadata. No intelligence."""
    database_url = os.environ.get("DATABASE_URL", "")

    if not database_url and not dry_run:
        logger.error("DATABASE_URL not set")
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
            delta = {
                "h": timedelta(hours=val),
                "m": timedelta(minutes=val),
                "d": timedelta(days=val),
            }
            since_dt = datetime.now(timezone.utc) - delta.get(unit, timedelta(hours=val))
    else:
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
        return []

    # 4. Stage each conversation
    writer = StagingWriter(database_url, dry_run=dry_run)

    try:
        if not dry_run:
            await writer.connect()

        results: list[dict[str, Any]] = []
        staged = 0
        skipped = 0

        for conv in conversations:
            if conv.message_count == 0:
                skipped += 1
                continue

            if not dry_run and await writer.already_staged(conv.source_id):
                skipped += 1
                continue

            staging_id = await writer.stage(conv)
            results.append({
                "source_id": conv.source_id,
                "chat_name": conv.chat_name,
                "is_group": conv.is_group,
                "message_count": conv.message_count,
                "participant_count": len(conv.participant_jids) if conv.is_group else 1,
                "staging_id": staging_id,
                "action": "staged",
            })
            staged += 1

        logger.info("WhatsApp extraction complete: %d staged, %d skipped", staged, skipped)

        # Save extraction timestamp
        if not dry_run and conversations:
            latest_cf = max(
                datetime_to_cf(msg.timestamp)
                for conv in conversations
                for msg in conv.messages
            )
            save_last_extraction(latest_cf)

        if dry_run:
            print(json.dumps(results, indent=2, default=str))
        return results

    finally:
        await writer.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cindy WhatsApp Extractor — stages raw metadata only"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    parser.add_argument(
        "--since", type=str,
        help="Time window: e.g. 2h, 30m, 7d (default: since last extraction or 24h)",
    )
    args = parser.parse_args()

    asyncio.run(extract_and_stage(dry_run=args.dry_run, since=args.since))


if __name__ == "__main__":
    main()
