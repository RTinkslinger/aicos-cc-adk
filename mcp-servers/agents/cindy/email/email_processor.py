#!/usr/bin/env python3
"""
AgentMail Email Processor for Cindy.

Polls AgentMail inbox (cindy.aacash@agentmail.to) for new emails,
parses them, extracts signals and obligations, and writes to Supabase.

Usage:
    python3 -m cindy.email                                 # process new emails
    python3 -m cindy.email --dry-run                       # preview without DB writes
    python3 -m cindy.email --since 2h                      # emails from last 2 hours
    python3 -m cindy.email --dry-run --use-sample-data     # test with sample data
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

import httpx

# Async Postgres
try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cindy.email")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AGENTMAIL_BASE_URL = "https://api.agentmail.to/v0"
CINDY_EMAIL = "cindy.aacash@agentmail.to"

# Environment variables
# AGENTMAIL_API_KEY  — Bearer token for AgentMail API
# DATABASE_URL       — Postgres connection string (Supabase)


@dataclass
class EmailMessage:
    """Parsed representation of an AgentMail message."""

    message_id: str
    thread_id: str
    inbox_id: str
    from_email: str
    from_name: str
    to: list[str]
    cc: list[str]
    bcc: list[str]
    subject: str
    text_body: str
    html_body: str
    extracted_text: str  # Reply content only (quoted history stripped by AgentMail/Talon)
    attachments: list[dict[str, Any]]
    received_at: str  # ISO 8601
    in_reply_to: Optional[str] = None
    labels: list[str] = field(default_factory=list)

    @property
    def all_participants(self) -> list[str]:
        """All email addresses involved (from + to + cc)."""
        emails = [self.from_email] + self.to + self.cc
        return [e for e in emails if e and e != CINDY_EMAIL]

    @property
    def signal_text(self) -> str:
        """Best text for signal extraction: extracted_text (reply only) > text_body."""
        return self.extracted_text or self.text_body or ""

    @property
    def has_ics_attachment(self) -> bool:
        return any(
            a.get("content_type", "").startswith("text/calendar")
            or a.get("filename", "").endswith(".ics")
            for a in self.attachments
        )


# ---------------------------------------------------------------------------
# AgentMail API Client
# ---------------------------------------------------------------------------


class AgentMailClient:
    """Async HTTP client for AgentMail API v0.

    API docs: https://docs.agentmail.to/api-reference
    Base URL: https://api.agentmail.to/v0
    Auth: Bearer token in Authorization header
    Pagination: page_token / next_page_token pattern
    """

    def __init__(self, api_key: str, base_url: str = AGENTMAIL_BASE_URL) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    # -- Inbox discovery --

    async def list_inboxes(self) -> list[dict[str, Any]]:
        """List all inboxes. Response: {"inboxes": [...], "count": N, "next_page_token": ...}"""
        resp = await self._client.get("/inboxes")
        resp.raise_for_status()
        data = resp.json()
        return data.get("inboxes", []) if isinstance(data, dict) else data

    async def find_inbox_id(self, email: str = CINDY_EMAIL) -> Optional[str]:
        """Resolve inbox_id for a given email address."""
        inboxes = await self.list_inboxes()
        for inbox in inboxes:
            if inbox.get("email") == email:
                return inbox["inbox_id"]
        return None

    # -- Messages --

    async def list_messages(
        self,
        inbox_id: str,
        limit: int = 50,
        page_token: Optional[str] = None,
        after: Optional[str] = None,
    ) -> dict[str, Any]:
        """List messages in an inbox (newest first).

        Response: {"messages": [...], "count": N, "next_page_token": ...}
        Filtering: after (ISO 8601 datetime), labels (array)
        """
        params: dict[str, Any] = {"limit": limit}
        if page_token:
            params["page_token"] = page_token
        if after:
            params["after"] = after
        resp = await self._client.get(f"/inboxes/{inbox_id}/messages", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_message(self, inbox_id: str, message_id: str) -> dict[str, Any]:
        """Get a single message by ID. Returns full message with text/html/extracted_text."""
        resp = await self._client.get(f"/inboxes/{inbox_id}/messages/{message_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_attachment(
        self, inbox_id: str, message_id: str, attachment_id: str
    ) -> bytes:
        """Download attachment content by attachment_id."""
        resp = await self._client.get(
            f"/inboxes/{inbox_id}/messages/{message_id}/attachments/{attachment_id}"
        )
        resp.raise_for_status()
        return resp.content

    async def update_message(
        self, inbox_id: str, message_id: str, labels: Optional[list[str]] = None
    ) -> None:
        """Update a message (e.g., add labels for audit trail)."""
        payload: dict[str, Any] = {}
        if labels is not None:
            payload["labels"] = labels
        resp = await self._client.patch(
            f"/inboxes/{inbox_id}/messages/{message_id}",
            json=payload,
        )
        resp.raise_for_status()


# ---------------------------------------------------------------------------
# Email Parser
# ---------------------------------------------------------------------------


def _parse_email_address(addr: str) -> tuple[str, str]:
    """Parse 'Display Name <email@domain.com>' or bare 'email@domain.com'.

    Returns (email, display_name).
    """
    if not addr:
        return "", ""
    # Match: Display Name <email@domain.com>
    m = re.match(r"^(.+?)\s*<([^>]+)>$", addr.strip())
    if m:
        return m.group(2).strip(), m.group(1).strip().strip('"')
    # Bare email
    return addr.strip(), ""


def _extract_email_list(field_val: Any) -> list[str]:
    """Extract bare email addresses from AgentMail to/cc/bcc fields.

    The API returns arrays of strings, each formatted as:
      - 'email@domain.com'
      - 'Display Name <email@domain.com>'
    """
    if not field_val:
        return []
    if isinstance(field_val, list):
        result: list[str] = []
        for item in field_val:
            if isinstance(item, str):
                email, _ = _parse_email_address(item)
                if email:
                    result.append(email)
            elif isinstance(item, dict):
                # Fallback: handle object format if API ever changes
                result.append(item.get("email", item.get("address", "")))
        return [e for e in result if e]
    if isinstance(field_val, str):
        email, _ = _parse_email_address(field_val)
        return [email] if email else []
    return []


def parse_agentmail_message(raw: dict[str, Any], inbox_id: str) -> EmailMessage:
    """Convert raw AgentMail JSON to EmailMessage dataclass.

    AgentMail API fields (GET /v0/inboxes/{inbox_id}/messages/{message_id}):
      - from: string "Display Name <email>" or "email@domain.com"
      - to, cc, bcc: arrays of strings in same format
      - text: plain text body
      - html: HTML body
      - extracted_text: reply content only (quoted history stripped by Talon)
      - extracted_html: reply HTML only
      - subject, preview, message_id, thread_id, inbox_id
      - attachments: [{attachment_id, filename, size, content_type, content_disposition}]
      - labels, timestamp, created_at, updated_at
      - in_reply_to, references
    """
    # Parse sender (string format: "Display Name <email>" or "email@domain.com")
    from_raw = raw.get("from", "")
    if isinstance(from_raw, str):
        from_email, from_name = _parse_email_address(from_raw)
    elif isinstance(from_raw, dict):
        # Fallback for object format
        from_email = from_raw.get("email", from_raw.get("address", ""))
        from_name = from_raw.get("name", from_raw.get("display_name", ""))
    else:
        from_email, from_name = "", ""

    attachments: list[dict[str, Any]] = []
    for att in raw.get("attachments", []):
        attachments.append({
            "id": att.get("attachment_id", att.get("id", "")),
            "filename": att.get("filename", ""),
            "content_type": att.get("content_type", ""),
            "size": att.get("size", 0),
            "content_disposition": att.get("content_disposition", "attachment"),
        })

    return EmailMessage(
        message_id=raw.get("message_id", raw.get("id", "")),
        thread_id=raw.get("thread_id", ""),
        inbox_id=inbox_id,
        from_email=from_email,
        from_name=from_name,
        to=_extract_email_list(raw.get("to")),
        cc=_extract_email_list(raw.get("cc")),
        bcc=_extract_email_list(raw.get("bcc")),
        subject=raw.get("subject", ""),
        text_body=raw.get("text", ""),
        html_body=raw.get("html", ""),
        extracted_text=raw.get("extracted_text", ""),
        attachments=attachments,
        received_at=raw.get("timestamp", raw.get("created_at", "")),
        in_reply_to=raw.get("in_reply_to"),
        labels=raw.get("labels", []),
    )


# ---------------------------------------------------------------------------
# Signal Extraction (pattern-based, no LLM)
# ---------------------------------------------------------------------------


def extract_action_items(text: str) -> list[str]:
    """Extract action items from email text using pattern matching."""
    actions: list[str] = []
    patterns = [
        r"(?:let'?s|can we|should we|need to|let me|i'?ll)\s+(.{10,80})",
        r"(?:please|could you|can you|would you)\s+(.{10,80})",
        r"(?:action item|todo|to-do|follow[- ]?up)[:;]\s*(.{10,80})",
        r"by (?:friday|monday|tuesday|wednesday|thursday|saturday|sunday|tomorrow|next week|eow|eod|end of (?:day|week))(.{0,60})",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            action = match.group(0).strip().rstrip(".,;:")
            if len(action) > 15 and action not in actions:
                actions.append(action)
    return actions[:10]  # cap at 10


def extract_deal_signals(text: str) -> list[dict[str, str]]:
    """Detect deal-related language."""
    signals: list[dict[str, str]] = []
    deal_patterns = {
        "term_sheet": r"term\s*sheet",
        "valuation": r"(?:valuation|pre-?money|post-?money|\$\d+[MmBb]\s+(?:pre|post))",
        "fundraise": r"(?:series\s+[a-e]|seed|bridge|extension|follow[- ]?on|fundrais)",
        "financials": r"(?:cap\s*table|burn\s*rate|runway|revenue|arr|mrr|gmv)",
        "diligence": r"(?:due\s*diligence|dd\s+process|data\s*room|ic\s+(?:meeting|review|deck))",
    }
    for signal_type, pattern in deal_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            signals.append({"type": signal_type, "strength": "detected"})
    return signals


def extract_thesis_signals(text: str) -> list[dict[str, str]]:
    """Detect thesis-relevant language."""
    signals: list[dict[str, str]] = []
    thesis_keywords = {
        "agentic_ai": r"(?:agentic|ai\s+agent|autonomous\s+agent|agent\s+(?:framework|infra))",
        "developer_tools": r"(?:dev\s*tools?|developer\s+(?:experience|platform)|devops|ci/?cd)",
        "fintech": r"(?:fintech|digital\s+(?:payments?|banking|lending)|neobank)",
        "climate": r"(?:climate\s*tech|carbon|sustainability|clean\s*energy|ev\s)",
        "cybersecurity": r"(?:cyber\s*security|infosec|zero\s*trust|siem|soc\s)",
    }
    for thesis_name, pattern in thesis_keywords.items():
        if re.search(pattern, text, re.IGNORECASE):
            signals.append({"thesis": thesis_name, "signal": "mention", "strength": "weak"})
    return signals


# ---------------------------------------------------------------------------
# Database Operations
# ---------------------------------------------------------------------------


class DatabaseWriter:
    """Async Postgres writer for interactions and related tables."""

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
        """Check if interaction already processed (dedup)."""
        if self._pool is None:
            return None
        row = await self._pool.fetchrow(
            "SELECT id FROM interactions WHERE source = 'email' AND source_id = $1",
            source_id,
        )
        return row["id"] if row else None

    async def write_interaction(self, email: EmailMessage, signals: dict[str, Any]) -> Optional[int]:
        """Insert or update interaction record."""
        if self.dry_run:
            logger.info("[DRY RUN] Would write interaction for message_id=%s", email.message_id)
            return None

        if self._pool is None:
            raise RuntimeError("Database not connected")

        raw_data = json.dumps({
            "subject": email.subject,
            "from_name": email.from_name,
            "from_email": email.from_email,
            "to": email.to,
            "cc": email.cc,
            "extracted_text": email.extracted_text[:20000] if email.extracted_text else "",
            "full_text": email.text_body[:20000] if email.text_body else "",
            "attachment_count": len(email.attachments),
            "attachments": [
                {"filename": a["filename"], "content_type": a["content_type"], "size": a["size"]}
                for a in email.attachments
            ],
            "has_ics": email.has_ics_attachment,
            "in_reply_to": email.in_reply_to,
        })

        row = await self._pool.fetchrow(
            """
            INSERT INTO interactions (
                source, source_id, thread_id, participants, summary,
                raw_data, timestamp, action_items, thesis_signals, deal_signals
            ) VALUES (
                'email', $1, $2, $3, $4, $5::jsonb, $6::timestamptz,
                $7, $8::jsonb, $9::jsonb
            )
            ON CONFLICT (source, source_id) DO UPDATE SET
                summary = COALESCE(EXCLUDED.summary, interactions.summary),
                action_items = COALESCE(EXCLUDED.action_items, interactions.action_items),
                thesis_signals = COALESCE(EXCLUDED.thesis_signals, interactions.thesis_signals),
                deal_signals = COALESCE(EXCLUDED.deal_signals, interactions.deal_signals),
                updated_at = NOW()
            RETURNING id
            """,
            email.message_id,                                    # $1
            email.thread_id or None,                             # $2
            email.all_participants,                               # $3
            f"{email.subject} — from {email.from_name or email.from_email}",  # $4
            raw_data,                                             # $5
            email.received_at or datetime.now(timezone.utc).isoformat(),  # $6
            signals.get("action_items", []),                      # $7
            json.dumps(signals.get("thesis_signals", [])),        # $8
            json.dumps(signals.get("deal_signals", [])),          # $9
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
        if self.dry_run:
            logger.info(
                "[DRY RUN] Would link person %d to interaction %d (role=%s)",
                person_id, interaction_id, role,
            )
            return
        if self._pool is None:
            return
        await self._pool.execute(
            """
            INSERT INTO people_interactions (person_id, interaction_id, role, surface,
                                              identifier_used, link_confidence)
            VALUES ($1, $2, $3, 'email', $4, $5)
            ON CONFLICT (person_id, interaction_id) DO NOTHING
            """,
            person_id, interaction_id, role, identifier, confidence,
        )

    async def resolve_person_by_email(self, email_addr: str) -> Optional[dict[str, Any]]:
        """Tier 1 resolution: match by email in network table."""
        if self._pool is None:
            return None
        row = await self._pool.fetchrow(
            "SELECT id, person_name, role_title FROM network WHERE email = $1",
            email_addr,
        )
        return dict(row) if row else None

    async def write_datum_request(
        self, name: str, email_addr: str, context: str, interaction_id: Optional[int]
    ) -> None:
        """Send unknown person to Datum Agent via cai_inbox."""
        if self.dry_run:
            logger.info("[DRY RUN] Would send datum_person request for %s <%s>", name, email_addr)
            return
        if self._pool is None:
            return
        metadata = json.dumps({
            "name": name,
            "email": email_addr,
            "source": "cindy_email",
            "context": context,
            "interaction_id": interaction_id,
        })
        await self._pool.execute(
            """
            INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
            VALUES ('datum_person', $1, $2::jsonb, FALSE, NOW())
            """,
            f"New person from email: {name} <{email_addr}>",
            metadata,
        )


# ---------------------------------------------------------------------------
# Main Processor
# ---------------------------------------------------------------------------

# Emails to skip during people resolution (Aakash's own addresses + Cindy)
SKIP_EMAILS = {
    "ak@z47.com",
    "aakash@z47.com",
    "aakash@devc.fund",
    "cindy.aacash@agentmail.to",
    "cindy@agent.aicos.ai",
}


async def process_email(
    email: EmailMessage,
    db: DatabaseWriter,
    client: Optional[AgentMailClient] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Process a single email: dedup, resolve people, extract signals + obligations, write to DB."""
    from cindy.email.obligation_extractor import extract_obligations

    result: dict[str, Any] = {
        "message_id": email.message_id,
        "subject": email.subject,
        "from": email.from_email,
        "action": "skipped",
        "people_linked": 0,
        "people_new": 0,
        "signals": {},
        "obligations": {"i_owe": 0, "they_owe": 0},
    }

    # 1. Dedup
    existing_id = await db.interaction_exists(email.message_id)
    if existing_id:
        logger.info("Already processed: %s (interaction #%d)", email.message_id, existing_id)
        result["action"] = "already_processed"
        result["interaction_id"] = existing_id
        return result

    # 2. Extract signals from text — prefer extracted_text (reply only, no quoted history)
    text = email.signal_text
    signals = {
        "action_items": extract_action_items(text),
        "deal_signals": extract_deal_signals(text),
        "thesis_signals": extract_thesis_signals(text),
    }
    result["signals"] = {k: len(v) for k, v in signals.items()}

    # 3. Extract obligations (MANDATORY post-signal step per Cindy CLAUDE.md Section 7.5)
    obligations = extract_obligations(
        text=text,
        sender_email=email.from_email,
        sender_name=email.from_name,
        subject=email.subject,
        surface="email",
    )
    i_owe = [o for o in obligations if o["obligation_type"] == "I_OWE_THEM"]
    they_owe = [o for o in obligations if o["obligation_type"] == "THEY_OWE_ME"]
    result["obligations"] = {
        "i_owe": len(i_owe),
        "they_owe": len(they_owe),
        "details": obligations,
    }

    # 4. Write interaction
    interaction_id = await db.write_interaction(email, signals)
    result["action"] = "processed"
    result["interaction_id"] = interaction_id

    # 5. People resolution
    for addr in email.all_participants:
        if addr.lower() in SKIP_EMAILS:
            continue

        person = await db.resolve_person_by_email(addr)
        if person:
            if interaction_id:
                role = "sender" if addr == email.from_email else "recipient"
                if addr in email.cc:
                    role = "cc"
                await db.write_people_interaction(
                    person["id"], interaction_id, role,
                    f"email:{addr}", 1.0,
                )
            result["people_linked"] += 1
            logger.info("Linked person: %s -> %s (#%d)", addr, person["person_name"], person["id"])
        else:
            # Tier 6: delegate to Datum Agent
            name = email.from_name if addr == email.from_email else ""
            await db.write_datum_request(
                name, addr,
                f"{'Sender' if addr == email.from_email else 'Participant'} on email: {email.subject}",
                interaction_id,
            )
            result["people_new"] += 1
            logger.info("New person (sent to Datum): %s", addr)

    # 6. Label the message in AgentMail for audit trail
    if not dry_run and client is not None:
        try:
            labels = ["processed"]
            if signals["action_items"]:
                labels.append("action-required")
            if signals["deal_signals"]:
                labels.append("deal-signal")
            if signals["thesis_signals"]:
                labels.append("thesis-signal")
            if obligations:
                labels.append("has-obligations")
            await client.update_message(email.inbox_id, email.message_id, labels=labels)
        except Exception as e:
            logger.warning("Failed to label message %s: %s", email.message_id, e)

    # 7. Flag .ics attachments for calendar processing
    if email.has_ics_attachment:
        logger.info("Email has .ics attachment — flagging for calendar processing")
        result["has_ics"] = True

    return result


def _parse_since(since: str) -> Optional[datetime]:
    """Parse a relative time string like '2h', '30m', '1d' into a datetime."""
    m = re.match(r"(\d+)([hmd])", since)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2)
    delta_map = {"h": timedelta(hours=val), "m": timedelta(minutes=val), "d": timedelta(days=val)}
    return datetime.now(timezone.utc) - delta_map.get(unit, timedelta(hours=val))


async def run(
    dry_run: bool = False,
    since: Optional[str] = None,
    limit: int = 50,
    use_sample_data: bool = False,
) -> list[dict[str, Any]]:
    """Main entry point: poll AgentMail, process new emails.

    Returns list of processing results (one per message).
    """
    # --- Sample data mode (for development/testing) ---
    if use_sample_data:
        from cindy.email.test_data import SAMPLE_MESSAGES
        logger.info("Using %d sample messages (no API call)", len(SAMPLE_MESSAGES))
        db = DatabaseWriter("", dry_run=True)
        results: list[dict[str, Any]] = []
        for raw_msg in SAMPLE_MESSAGES:
            email = parse_agentmail_message(raw_msg, "sample_inbox")
            result = await process_email(email, db, client=None, dry_run=True)
            results.append(result)
        _print_summary(results, dry_run=True)
        return results

    # --- Live mode ---
    api_key = os.environ.get("AGENTMAIL_API_KEY")
    database_url = os.environ.get("DATABASE_URL")

    if not api_key:
        logger.error("AGENTMAIL_API_KEY not set")
        sys.exit(1)
    if not database_url and not dry_run:
        logger.error("DATABASE_URL not set (required when not in --dry-run mode)")
        sys.exit(1)

    client = AgentMailClient(api_key)
    db = DatabaseWriter(database_url or "", dry_run=dry_run)

    try:
        # Connect to DB
        if not dry_run:
            await db.connect()

        # Find Cindy's inbox
        inbox_id = await client.find_inbox_id(CINDY_EMAIL)
        if not inbox_id:
            logger.error("Could not find inbox for %s", CINDY_EMAIL)
            inboxes = await client.list_inboxes()
            logger.info("Available inboxes: %s", [i.get("email") for i in inboxes])
            return []

        logger.info("Found inbox: %s (id=%s)", CINDY_EMAIL, inbox_id)

        # Build time filter for API-side filtering
        since_dt: Optional[datetime] = None
        after_iso: Optional[str] = None
        if since:
            since_dt = _parse_since(since)
            if since_dt:
                after_iso = since_dt.isoformat()

        # Fetch messages — API returns {"messages": [...], "count": N, "next_page_token": ...}
        response = await client.list_messages(inbox_id, limit=limit, after=after_iso)
        messages_raw = response.get("messages", [])
        if not isinstance(messages_raw, list):
            messages_raw = []

        logger.info("Fetched %d messages from AgentMail", len(messages_raw))

        # Process each message
        results = []
        for raw_msg in messages_raw:
            email = parse_agentmail_message(raw_msg, inbox_id)

            # Client-side time filter as fallback (if API after= not supported)
            if since_dt and email.received_at:
                try:
                    msg_dt = datetime.fromisoformat(email.received_at.replace("Z", "+00:00"))
                    if msg_dt < since_dt:
                        continue
                except ValueError:
                    pass

            # Skip already-labeled messages (avoid re-processing)
            if "processed" in (email.labels or []):
                logger.debug("Skipping already-labeled message: %s", email.message_id)
                continue

            result = await process_email(email, db, client=client, dry_run=dry_run)
            results.append(result)

        _print_summary(results, dry_run=dry_run)
        return results

    finally:
        await client.close()
        await db.close()


def _print_summary(results: list[dict[str, Any]], dry_run: bool = False) -> None:
    """Print a structured summary of processing results."""
    processed = [r for r in results if r["action"] == "processed"]
    skipped = [r for r in results if r["action"] == "already_processed"]
    total_people = sum(r.get("people_linked", 0) for r in processed)
    total_new = sum(r.get("people_new", 0) for r in processed)
    total_i_owe = sum(r.get("obligations", {}).get("i_owe", 0) for r in processed)
    total_they_owe = sum(r.get("obligations", {}).get("they_owe", 0) for r in processed)

    logger.info(
        "Email processing complete: %d processed, %d skipped, "
        "%d people linked, %d new sent to Datum, "
        "%d obligations (%d I-owe, %d they-owe)",
        len(processed), len(skipped), total_people, total_new,
        total_i_owe + total_they_owe, total_i_owe, total_they_owe,
    )

    if dry_run:
        print(json.dumps(results, indent=2, default=str))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cindy AgentMail Email Processor",
        epilog="Examples:\n"
               "  python3 -m cindy.email --dry-run --use-sample-data\n"
               "  python3 -m cindy.email --since 2h\n"
               "  python3 -m cindy.email --limit 10",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    parser.add_argument("--since", type=str, help="Time window: e.g. 2h, 30m, 1d")
    parser.add_argument("--limit", type=int, default=50, help="Max messages to fetch")
    parser.add_argument(
        "--use-sample-data", action="store_true",
        help="Use built-in sample emails (no API key needed, implies --dry-run)",
    )
    args = parser.parse_args()

    asyncio.run(run(
        dry_run=args.dry_run or args.use_sample_data,
        since=args.since,
        limit=args.limit,
        use_sample_data=args.use_sample_data,
    ))


if __name__ == "__main__":
    main()
