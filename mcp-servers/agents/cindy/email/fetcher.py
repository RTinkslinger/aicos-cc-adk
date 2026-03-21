#!/usr/bin/env python3
"""
Thin Email Fetcher for Cindy — Plumbing Only.

Polls AgentMail inbox (cindy.aacash@agentmail.to), fetches new emails,
parses them into structured JSON, and stages raw data in interaction_staging.
NO signal extraction, NO obligation detection, NO people resolution.

Datum Agent handles: people resolution, entity linking, writing to interactions.
Cindy Agent handles: LLM-based signal extraction, obligation reasoning, action creation.

Usage:
    python3 -m cindy.email.fetcher                          # fetch + stage new emails
    python3 -m cindy.email.fetcher --dry-run                # preview without DB writes
    python3 -m cindy.email.fetcher --since 2h               # emails from last 2 hours
    python3 -m cindy.email.fetcher --dry-run --use-sample   # test with sample data
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

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cindy.email.fetcher")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AGENTMAIL_BASE_URL = "https://api.agentmail.to/v0"
CINDY_EMAIL = "cindy.aacash@agentmail.to"

# Emails to skip (Aakash's own addresses + Cindy)
SKIP_EMAILS = {
    "ak@z47.com",
    "aakash@z47.com",
    "aakash@devc.fund",
    "cindy.aacash@agentmail.to",
    "cindy@agent.aicos.ai",
}


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
    extracted_text: str
    attachments: list[dict[str, Any]]
    received_at: str
    in_reply_to: Optional[str] = None
    labels: list[str] = field(default_factory=list)

    @property
    def all_participants(self) -> list[str]:
        """All email addresses involved (from + to + cc), excluding Cindy/Aakash."""
        emails = [self.from_email] + self.to + self.cc
        return [e for e in emails if e and e.lower() not in SKIP_EMAILS]

    @property
    def has_ics_attachment(self) -> bool:
        return any(
            a.get("content_type", "").startswith("text/calendar")
            or a.get("filename", "").endswith(".ics")
            for a in self.attachments
        )

    def to_raw_json(self) -> dict[str, Any]:
        """Convert to raw JSON for staging in interaction_staging."""
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "inbox_id": self.inbox_id,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "to": self.to,
            "cc": self.cc,
            "bcc": self.bcc,
            "subject": self.subject,
            "text_body": self.text_body[:20000] if self.text_body else "",
            "html_body": self.html_body[:20000] if self.html_body else "",
            "extracted_text": self.extracted_text[:20000] if self.extracted_text else "",
            "attachments": [
                {"filename": a["filename"], "content_type": a["content_type"], "size": a["size"]}
                for a in self.attachments
            ],
            "has_ics": self.has_ics_attachment,
            "received_at": self.received_at,
            "in_reply_to": self.in_reply_to,
            "all_participants": self.all_participants,
        }


# ---------------------------------------------------------------------------
# AgentMail API Client (pure HTTP — no intelligence)
# ---------------------------------------------------------------------------


class AgentMailClient:
    """Async HTTP client for AgentMail API v0."""

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

    async def list_inboxes(self) -> list[dict[str, Any]]:
        resp = await self._client.get("/inboxes")
        resp.raise_for_status()
        data = resp.json()
        return data.get("inboxes", []) if isinstance(data, dict) else data

    async def find_inbox_id(self, email: str = CINDY_EMAIL) -> Optional[str]:
        inboxes = await self.list_inboxes()
        for inbox in inboxes:
            if inbox.get("email") == email:
                return inbox["inbox_id"]
        return None

    async def list_messages(
        self,
        inbox_id: str,
        limit: int = 50,
        page_token: Optional[str] = None,
        after: Optional[str] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if page_token:
            params["page_token"] = page_token
        if after:
            params["after"] = after
        resp = await self._client.get(f"/inboxes/{inbox_id}/messages", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_message(self, inbox_id: str, message_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/inboxes/{inbox_id}/messages/{message_id}")
        resp.raise_for_status()
        return resp.json()

    async def update_message(
        self, inbox_id: str, message_id: str, labels: Optional[list[str]] = None
    ) -> None:
        payload: dict[str, Any] = {}
        if labels is not None:
            payload["labels"] = labels
        resp = await self._client.patch(
            f"/inboxes/{inbox_id}/messages/{message_id}", json=payload
        )
        resp.raise_for_status()


# ---------------------------------------------------------------------------
# Email Parser (pure data transformation — no intelligence)
# ---------------------------------------------------------------------------


def _parse_email_address(addr: str) -> tuple[str, str]:
    """Parse 'Display Name <email@domain.com>' or bare 'email@domain.com'."""
    if not addr:
        return "", ""
    m = re.match(r"^(.+?)\s*<([^>]+)>$", addr.strip())
    if m:
        return m.group(2).strip(), m.group(1).strip().strip('"')
    return addr.strip(), ""


def _extract_email_list(field_val: Any) -> list[str]:
    """Extract bare email addresses from AgentMail to/cc/bcc fields."""
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
                result.append(item.get("email", item.get("address", "")))
        return [e for e in result if e]
    if isinstance(field_val, str):
        email, _ = _parse_email_address(field_val)
        return [email] if email else []
    return []


def parse_agentmail_message(raw: dict[str, Any], inbox_id: str) -> EmailMessage:
    """Convert raw AgentMail JSON to EmailMessage dataclass."""
    from_raw = raw.get("from", "")
    if isinstance(from_raw, str):
        from_email, from_name = _parse_email_address(from_raw)
    elif isinstance(from_raw, dict):
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
# Staging Writer (writes raw data to interaction_staging — no intelligence)
# ---------------------------------------------------------------------------


class StagingWriter:
    """Writes raw email data to interaction_staging table."""

    def __init__(self, database_url: str, dry_run: bool = False) -> None:
        self.database_url = database_url
        self.dry_run = dry_run
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg not installed. Run: pip install asyncpg")
        self._pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=3)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def already_staged(self, source_id: str) -> bool:
        """Check if this email was already staged."""
        if self._pool is None:
            return False
        row = await self._pool.fetchrow(
            "SELECT id FROM interaction_staging WHERE source = 'email' AND source_id = $1",
            source_id,
        )
        return row is not None

    async def stage(self, email: EmailMessage) -> Optional[int]:
        """Write raw email data to interaction_staging."""
        if self.dry_run:
            logger.info("[DRY RUN] Would stage email: %s — %s", email.message_id, email.subject)
            return None
        if self._pool is None:
            raise RuntimeError("Database not connected")

        row = await self._pool.fetchrow(
            """
            INSERT INTO interaction_staging (source, source_id, raw_data)
            VALUES ('email', $1, $2::jsonb)
            ON CONFLICT (source, source_id) DO NOTHING
            RETURNING id
            """,
            email.message_id,
            json.dumps(email.to_raw_json()),
        )
        return row["id"] if row else None


# ---------------------------------------------------------------------------
# Main Fetcher
# ---------------------------------------------------------------------------


def _parse_since(since: str) -> Optional[datetime]:
    m = re.match(r"(\d+)([hmd])", since)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2)
    delta_map = {"h": timedelta(hours=val), "m": timedelta(minutes=val), "d": timedelta(days=val)}
    return datetime.now(timezone.utc) - delta_map.get(unit, timedelta(hours=val))


async def fetch_and_stage(
    dry_run: bool = False,
    since: Optional[str] = None,
    limit: int = 50,
    use_sample: bool = False,
) -> list[dict[str, Any]]:
    """Fetch emails from AgentMail and stage raw data. No intelligence."""

    if use_sample:
        from cindy.email.test_data import SAMPLE_MESSAGES
        logger.info("Using %d sample messages (no API call)", len(SAMPLE_MESSAGES))
        results: list[dict[str, Any]] = []
        for raw_msg in SAMPLE_MESSAGES:
            email = parse_agentmail_message(raw_msg, "sample_inbox")
            results.append({
                "message_id": email.message_id,
                "subject": email.subject,
                "from": email.from_email,
                "participants": email.all_participants,
                "action": "staged (dry run)",
            })
        logger.info("Staged %d emails (sample mode)", len(results))
        if dry_run:
            print(json.dumps(results, indent=2, default=str))
        return results

    api_key = os.environ.get("AGENTMAIL_API_KEY")
    database_url = os.environ.get("DATABASE_URL")

    if not api_key:
        logger.error("AGENTMAIL_API_KEY not set")
        sys.exit(1)
    if not database_url and not dry_run:
        logger.error("DATABASE_URL not set")
        sys.exit(1)

    client = AgentMailClient(api_key)
    writer = StagingWriter(database_url or "", dry_run=dry_run)

    try:
        if not dry_run:
            await writer.connect()

        inbox_id = await client.find_inbox_id(CINDY_EMAIL)
        if not inbox_id:
            logger.error("Could not find inbox for %s", CINDY_EMAIL)
            return []

        logger.info("Found inbox: %s (id=%s)", CINDY_EMAIL, inbox_id)

        since_dt = _parse_since(since) if since else None
        after_iso = since_dt.isoformat() if since_dt else None

        response = await client.list_messages(inbox_id, limit=limit, after=after_iso)
        messages_raw = response.get("messages", [])
        if not isinstance(messages_raw, list):
            messages_raw = []

        logger.info("Fetched %d messages from AgentMail", len(messages_raw))

        results = []
        staged = 0
        skipped = 0

        for raw_msg in messages_raw:
            email = parse_agentmail_message(raw_msg, inbox_id)

            # Time filter
            if since_dt and email.received_at:
                try:
                    msg_dt = datetime.fromisoformat(email.received_at.replace("Z", "+00:00"))
                    if msg_dt < since_dt:
                        continue
                except ValueError:
                    pass

            # Skip already-labeled
            if "staged" in (email.labels or []):
                skipped += 1
                continue

            # Check if already staged
            if not dry_run and await writer.already_staged(email.message_id):
                skipped += 1
                continue

            # Stage it
            staging_id = await writer.stage(email)

            # Label in AgentMail
            if not dry_run:
                try:
                    await client.update_message(email.inbox_id, email.message_id, labels=["staged"])
                except Exception as e:
                    logger.warning("Failed to label message %s: %s", email.message_id, e)

            results.append({
                "message_id": email.message_id,
                "subject": email.subject,
                "from": email.from_email,
                "participants": email.all_participants,
                "staging_id": staging_id,
                "action": "staged",
            })
            staged += 1

        logger.info("Email fetch complete: %d staged, %d skipped", staged, skipped)
        if dry_run:
            print(json.dumps(results, indent=2, default=str))
        return results

    finally:
        await client.close()
        await writer.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cindy Email Fetcher — stages raw data only")
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    parser.add_argument("--since", type=str, help="Time window: e.g. 2h, 30m, 1d")
    parser.add_argument("--limit", type=int, default=50, help="Max messages to fetch")
    parser.add_argument("--use-sample", action="store_true", help="Use sample data")
    args = parser.parse_args()

    asyncio.run(fetch_and_stage(
        dry_run=args.dry_run or args.use_sample,
        since=args.since,
        limit=args.limit,
        use_sample=args.use_sample,
    ))


if __name__ == "__main__":
    main()
