#!/usr/bin/env python3
"""
WhatsApp Markdown → Supabase Ingestion Script

Reads extracted WhatsApp markdown files from data/whatsapp/ and upserts
them into the whatsapp_conversations table in Supabase.

Modes:
  --sql     Generate SQL INSERT statements to stdout (for MCP execute_sql)
  --api     Use Supabase REST API directly (requires SUPABASE_URL + SUPABASE_SECRET_KEY in .env.local)
  --dry-run Show what would be ingested without writing

Usage:
    python3 scripts/whatsapp_ingest.py --sql > /tmp/whatsapp_inserts.sql
    python3 scripts/whatsapp_ingest.py --sql --batch 50   # batch of 50
    python3 scripts/whatsapp_ingest.py --api               # direct REST API
    python3 scripts/whatsapp_ingest.py --dry-run            # preview
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
INPUT_DIR = PROJECT_ROOT / "data" / "whatsapp"
ENV_FILE = PROJECT_ROOT / ".env.local"


def parse_markdown_metadata(filepath: Path) -> dict | None:
    """Parse metadata header from a WhatsApp conversation markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  WARN: Cannot read {filepath.name}: {e}", file=sys.stderr)
        return None

    # Extract chat name from H1
    match = re.search(r"^# (.+)$", content, re.MULTILINE)
    chat_name = match.group(1).strip() if match else filepath.stem

    # Extract metadata fields
    metadata: dict = {"chat_name": chat_name, "filename": filepath.name}

    # Type
    match = re.search(r"\*\*Type:\*\*\s*(.+)", content)
    metadata["chat_type"] = match.group(1).strip() if match else "Unknown"

    # JID
    match = re.search(r"\*\*JID:\*\*\s*`(.+?)`", content)
    metadata["jid"] = match.group(1).strip() if match else None

    # Messages count
    match = re.search(r"\*\*Messages:\*\*\s*(\d+)", content)
    metadata["message_count"] = int(match.group(1)) if match else 0

    # Date Range
    match = re.search(r"\*\*Date Range:\*\*\s*(.+)", content)
    if match:
        date_range = match.group(1).strip()
        metadata["date_range"] = date_range
        # Parse first and last dates
        dates = re.findall(r"(\d{4}-\d{2}-\d{2})", date_range)
        if len(dates) >= 2:
            metadata["first_message_at"] = dates[0] + "T00:00:00Z"
            metadata["last_message_at"] = dates[1] + "T23:59:59Z"
        elif len(dates) == 1:
            metadata["first_message_at"] = dates[0] + "T00:00:00Z"
            metadata["last_message_at"] = dates[0] + "T23:59:59Z"

    # Last Message (more precise)
    match = re.search(r"\*\*Last Message:\*\*\s*(.+)", content)
    if match:
        last_msg_str = match.group(1).strip()
        # Format: YYYY-MM-DD HH:MM
        try:
            metadata["last_message_at"] = last_msg_str.replace(" ", "T") + ":00Z"
        except Exception:
            pass

    # Participants
    match = re.search(r"\*\*Participants\s*\((\d+)\):\*\*\s*(.+?)(?:\n|$)", content)
    if match:
        metadata["participant_count"] = int(match.group(1))
        # Parse participant names
        raw_participants = match.group(2).strip()
        participants = [p.strip() for p in raw_participants.split(",") if p.strip()]
        metadata["participants"] = participants
    else:
        match = re.search(r"\*\*Participants:\*\*\s*(.+?)(?:\n|$)", content)
        if match:
            raw = match.group(1).strip()
            participants = [p.strip() for p in raw.split(",") if p.strip()]
            metadata["participants"] = participants
            metadata["participant_count"] = len(participants)
        else:
            metadata["participants"] = []
            metadata["participant_count"] = 0

    # Full text (the entire markdown)
    metadata["full_text"] = content

    # Summary: metadata section + first 500 chars of messages
    summary_parts = []
    meta_match = re.search(r"(## Metadata.+?)(?=\n---|\n## Messages)", content, re.DOTALL)
    if meta_match:
        summary_parts.append(meta_match.group(1).strip())

    # First few messages
    msg_match = re.search(r"## Messages\n+(.+)", content, re.DOTALL)
    if msg_match:
        msg_text = msg_match.group(1)[:1000]
        summary_parts.append(msg_text)

    metadata["summary"] = "\n\n".join(summary_parts)[:2000]

    return metadata


def escape_sql(s: str | None) -> str:
    """Escape a string for SQL insertion."""
    if s is None:
        return "NULL"
    # Escape single quotes by doubling them
    escaped = s.replace("'", "''")
    # Remove null bytes
    escaped = escaped.replace("\x00", "")
    return f"'{escaped}'"


def generate_sql_upsert(records: list[dict]) -> str:
    """Generate SQL upsert statements for a batch of records."""
    statements = []

    for rec in records:
        jid = rec.get("jid")
        if not jid:
            # Use chat_name as fallback identifier
            jid = f"local:{rec['chat_name']}"

        participants_json = json.dumps(rec.get("participants", []))

        # Truncate full_text for SQL if extremely large (> 500KB)
        full_text = rec.get("full_text", "")
        if len(full_text) > 500000:
            full_text = full_text[:500000] + "\n\n[TRUNCATED - full text exceeds 500KB]"

        sql = f"""INSERT INTO public.whatsapp_conversations
  (chat_name, chat_type, jid, participant_count, message_count,
   first_message_at, last_message_at, participants,
   full_text, summary, updated_at)
VALUES (
  {escape_sql(rec['chat_name'])},
  {escape_sql(rec.get('chat_type', 'Unknown'))},
  {escape_sql(jid)},
  {rec.get('participant_count', 0)},
  {rec.get('message_count', 0)},
  {escape_sql(rec.get('first_message_at'))},
  {escape_sql(rec.get('last_message_at'))},
  {escape_sql(participants_json)}::jsonb,
  {escape_sql(full_text)},
  {escape_sql(rec.get('summary', ''))},
  now()
)
ON CONFLICT (jid) DO UPDATE SET
  chat_name = EXCLUDED.chat_name,
  chat_type = EXCLUDED.chat_type,
  participant_count = EXCLUDED.participant_count,
  message_count = EXCLUDED.message_count,
  first_message_at = EXCLUDED.first_message_at,
  last_message_at = EXCLUDED.last_message_at,
  participants = EXCLUDED.participants,
  full_text = EXCLUDED.full_text,
  summary = EXCLUDED.summary,
  updated_at = now();"""

        statements.append(sql)

    return "\n\n".join(statements)


def ingest_via_api(records: list[dict], supabase_url: str, supabase_key: str) -> tuple[int, int]:
    """Ingest records via Supabase REST API."""
    success = 0
    failed = 0

    for rec in records:
        jid = rec.get("jid") or f"local:{rec['chat_name']}"

        full_text = rec.get("full_text", "")
        if len(full_text) > 500000:
            full_text = full_text[:500000] + "\n\n[TRUNCATED]"

        payload = {
            "chat_name": rec["chat_name"],
            "chat_type": rec.get("chat_type", "Unknown"),
            "jid": jid,
            "participant_count": rec.get("participant_count", 0),
            "message_count": rec.get("message_count", 0),
            "first_message_at": rec.get("first_message_at"),
            "last_message_at": rec.get("last_message_at"),
            "participants": rec.get("participants", []),
            "full_text": full_text,
            "summary": rec.get("summary", ""),
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }

        url = f"{supabase_url}/rest/v1/whatsapp_conversations?on_conflict=jid"
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as resp:
                success += 1
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            print(f"  FAIL: {rec['chat_name']}: {e.code} - {error_body[:200]}", file=sys.stderr)
            failed += 1

    return success, failed


def load_env() -> dict[str, str]:
    """Load environment variables from .env.local."""
    env: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest WhatsApp conversations to Supabase")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sql", action="store_true", help="Generate SQL statements to stdout")
    mode.add_argument("--api", action="store_true", help="Use Supabase REST API")
    mode.add_argument("--dry-run", action="store_true", help="Preview without writing")

    parser.add_argument("--batch", type=int, default=0, metavar="N",
                        help="Process only N conversations (0 = all)")
    parser.add_argument("--min-messages", type=int, default=5,
                        help="Skip conversations with fewer messages (default: 5)")
    parser.add_argument("--offset", type=int, default=0,
                        help="Skip first N conversations (for batched SQL generation)")
    args = parser.parse_args()

    if not INPUT_DIR.exists():
        print(f"ERROR: Input directory not found: {INPUT_DIR}", file=sys.stderr)
        print("Run whatsapp_extract.py first.", file=sys.stderr)
        sys.exit(1)

    # Collect markdown files
    md_files = sorted(INPUT_DIR.glob("*.md"))
    print(f"Found {len(md_files)} markdown files in {INPUT_DIR}", file=sys.stderr)

    # Parse all files
    records = []
    for f in md_files:
        meta = parse_markdown_metadata(f)
        if meta and meta.get("message_count", 0) >= args.min_messages:
            records.append(meta)

    print(f"Parsed {len(records)} conversations (>= {args.min_messages} messages)", file=sys.stderr)

    # Apply offset and batch
    if args.offset:
        records = records[args.offset:]
    if args.batch:
        records = records[:args.batch]

    print(f"Processing {len(records)} conversations (offset={args.offset}, batch={args.batch})", file=sys.stderr)

    if args.dry_run:
        for rec in records:
            print(f"  {rec['chat_type']:6s}  {rec['chat_name'][:50]:50s}  "
                  f"msgs={rec['message_count']:5d}  "
                  f"participants={rec.get('participant_count', 0):3d}  "
                  f"text_size={len(rec.get('full_text', '')):,d}")
        print(f"\nTotal: {len(records)} conversations", file=sys.stderr)
        return

    if args.sql:
        sql = generate_sql_upsert(records)
        print(sql)
        print(f"\nGenerated {len(records)} upsert statements", file=sys.stderr)
        return

    if args.api:
        env = load_env()
        supabase_url = env.get("SUPABASE_URL", "https://llfkxnsfczludgigknbs.supabase.co")
        supabase_key = env.get("SUPABASE_SECRET_KEY") or env.get("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_key:
            print("ERROR: SUPABASE_SECRET_KEY not found in .env.local", file=sys.stderr)
            print("Add: SUPABASE_SECRET_KEY=sb_secret_... to .env.local", file=sys.stderr)
            sys.exit(1)

        success, failed = ingest_via_api(records, supabase_url, supabase_key)
        print(f"\nIngestion complete: {success} success, {failed} failed", file=sys.stderr)


if __name__ == "__main__":
    main()
