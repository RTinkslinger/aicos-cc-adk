#!/usr/bin/env python3
"""
WhatsApp SQLite → Markdown Extraction Script

Reads the WhatsApp ChatStorage.sqlite database (read-only) from macOS
and exports each conversation as a markdown file to data/whatsapp/.

Supports incremental extraction: only processes messages newer than
the last run timestamp stored in data/whatsapp/.last_run.

Usage:
    python3 scripts/whatsapp_extract.py              # incremental (since last run)
    python3 scripts/whatsapp_extract.py --full        # full re-extraction
    python3 scripts/whatsapp_extract.py --since 30    # last 30 days only
    python3 scripts/whatsapp_extract.py --chat "DeVC" # single chat by name
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# WhatsApp stores timestamps as Core Data timestamps (seconds since 2001-01-01)
COREDATA_EPOCH = 978307200  # Unix timestamp of 2001-01-01 00:00:00 UTC

# Session types
SESSION_TYPE_MAP = {
    0: "1:1",
    1: "Group",
    2: "Broadcast",
    3: "Status",
    4: "Community",
    5: "Unknown",
}

# Message types to include (0 = text, others are media/system)
# We include all but extract text only
SYSTEM_MESSAGE_TYPES = {6, 7, 10, 14}  # group events, system notifications

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "whatsapp"
LAST_RUN_FILE = OUTPUT_DIR / ".last_run"
DB_PATH = Path.home() / "Library" / "Group Containers" / "group.net.whatsapp.WhatsApp.shared" / "ChatStorage.sqlite"


def coredata_to_datetime(ts: float | None) -> datetime | None:
    """Convert Core Data timestamp to datetime."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts + COREDATA_EPOCH, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None


def coredata_to_str(ts: float | None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Convert Core Data timestamp to formatted string."""
    dt = coredata_to_datetime(ts)
    return dt.strftime(fmt) if dt else "unknown"


def sanitize_filename(name: str) -> str:
    """Create a safe filename from a chat name."""
    # Remove or replace problematic characters
    clean = re.sub(r'[<>:"/\\|?*]', '', name)
    clean = re.sub(r'\s+', ' ', clean).strip()
    # Truncate to reasonable length
    if len(clean) > 80:
        clean = clean[:80].strip()
    return clean or "unnamed"


def build_name_resolver(db: sqlite3.Connection) -> dict[str, str]:
    """Build a JID → display name mapping from multiple sources."""
    resolver: dict[str, str] = {}

    # Source 1: ZWAPROFILEPUSHNAME (most reliable)
    cur = db.execute("SELECT ZJID, ZPUSHNAME FROM ZWAPROFILEPUSHNAME WHERE ZPUSHNAME IS NOT NULL")
    for jid, name in cur:
        if name and name.strip():
            resolver[jid] = name.strip()

    # Source 2: ZWACHATSESSION partner names (1:1 chats, maps contact JID to name)
    cur = db.execute(
        "SELECT ZCONTACTJID, ZPARTNERNAME FROM ZWACHATSESSION "
        "WHERE ZSESSIONTYPE = 0 AND ZPARTNERNAME IS NOT NULL AND ZPARTNERNAME != ''"
    )
    for jid, name in cur:
        if jid and name and jid not in resolver:
            resolver[jid] = name.strip()

    # Source 3: ZWAGROUPMEMBER contact names
    cur = db.execute(
        "SELECT ZMEMBERJID, ZCONTACTNAME FROM ZWAGROUPMEMBER "
        "WHERE ZCONTACTNAME IS NOT NULL AND ZCONTACTNAME != ''"
    )
    for jid, name in cur:
        if jid and name and jid not in resolver:
            resolver[jid] = name.strip()

    return resolver


def resolve_name(jid: str | None, resolver: dict[str, str]) -> str:
    """Resolve a JID to a display name."""
    if not jid:
        return "You"
    name = resolver.get(jid)
    if name:
        return name
    # Extract phone number from JID if possible
    match = re.match(r"(\d+)@s\.whatsapp\.net", jid)
    if match:
        return f"+{match.group(1)}"
    # LID format - no phone number
    match = re.match(r"(\d+)@lid", jid)
    if match:
        return f"[{match.group(1)[:8]}...]"
    return jid.split("@")[0][:15]


def get_chat_sessions(db: sqlite3.Connection, chat_filter: str | None = None) -> list[dict]:
    """Get all active chat sessions."""
    query = """
        SELECT
            cs.Z_PK,
            cs.ZCONTACTJID,
            cs.ZPARTNERNAME,
            cs.ZSESSIONTYPE,
            cs.ZMESSAGECOUNTER,
            cs.ZLASTMESSAGEDATE,
            cs.ZUNREADCOUNT
        FROM ZWACHATSESSION cs
        WHERE cs.ZREMOVED = 0
          AND cs.ZSESSIONTYPE IN (0, 1, 4)
    """
    params: list = []

    if chat_filter:
        query += " AND cs.ZPARTNERNAME LIKE ?"
        params.append(f"%{chat_filter}%")

    query += " ORDER BY cs.ZLASTMESSAGEDATE DESC"

    rows = db.execute(query, params).fetchall()
    sessions = []
    for row in rows:
        sessions.append({
            "pk": row[0],
            "jid": row[1],
            "name": row[2] or row[1] or f"chat_{row[0]}",
            "session_type": row[3],
            "message_counter": row[4] or 0,
            "last_message_date": row[5],
            "unread_count": row[6] or 0,
        })
    return sessions


def get_group_participants(db: sqlite3.Connection, session_pk: int, resolver: dict[str, str]) -> list[str]:
    """Get participant names for a group chat."""
    rows = db.execute(
        """
        SELECT ZMEMBERJID, ZCONTACTNAME, ZFIRSTNAME, ZISACTIVE
        FROM ZWAGROUPMEMBER
        WHERE ZCHATSESSION = ?
        ORDER BY ZISACTIVE DESC, ZMEMBERJID
        """,
        (session_pk,),
    ).fetchall()

    participants = []
    for jid, contact_name, first_name, is_active in rows:
        name = contact_name or first_name or resolve_name(jid, resolver)
        if name:
            participants.append(name)
    return participants


def get_messages(
    db: sqlite3.Connection,
    session_pk: int,
    resolver: dict[str, str],
    since_ts: float | None = None,
) -> list[dict]:
    """Get messages for a chat session."""
    query = """
        SELECT
            m.Z_PK,
            m.ZISFROMME,
            m.ZMESSAGEDATE,
            m.ZTEXT,
            m.ZMESSAGETYPE,
            m.ZGROUPMEMBER,
            m.ZFROMJID,
            gm.ZMEMBERJID
        FROM ZWAMESSAGE m
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        WHERE m.ZCHATSESSION = ?
    """
    params: list = [session_pk]

    if since_ts is not None:
        query += " AND m.ZMESSAGEDATE > ?"
        params.append(since_ts)

    query += " ORDER BY m.ZMESSAGEDATE ASC"

    rows = db.execute(query, params).fetchall()
    messages = []
    for row in rows:
        pk, is_from_me, msg_date, text, msg_type, group_member_fk, from_jid, member_jid = row

        # Skip null-text system messages
        if text is None and msg_type in SYSTEM_MESSAGE_TYPES:
            continue

        # Resolve sender
        if is_from_me:
            sender = "You"
        else:
            # For group messages, use the group member JID
            sender_jid = member_jid or from_jid
            sender = resolve_name(sender_jid, resolver)

        # Determine content
        if text:
            content = text
        elif msg_type == 1:
            content = "[Image]"
        elif msg_type == 2:
            content = "[Video]"
        elif msg_type == 3:
            content = "[Audio]"
        elif msg_type == 4:
            content = "[Contact]"
        elif msg_type == 5:
            content = "[Location]"
        elif msg_type == 8:
            content = "[Document]"
        elif msg_type == 15:
            content = "[Sticker]"
        elif msg_type == 46:
            content = "[Poll]"
        elif msg_type in SYSTEM_MESSAGE_TYPES:
            content = f"[System: {text or 'event'}]"
        else:
            content = text or f"[Media type {msg_type}]"

        messages.append({
            "pk": pk,
            "sender": sender,
            "date": msg_date,
            "date_str": coredata_to_str(msg_date),
            "content": content,
            "is_from_me": bool(is_from_me),
            "msg_type": msg_type,
        })

    return messages


def format_conversation_markdown(
    session: dict,
    messages: list[dict],
    participants: list[str],
) -> str:
    """Format a conversation as markdown."""
    name = session["name"]
    stype = SESSION_TYPE_MAP.get(session["session_type"], "Unknown")

    # Date range
    if messages:
        first_date = coredata_to_str(messages[0]["date"], "%Y-%m-%d")
        last_date = coredata_to_str(messages[-1]["date"], "%Y-%m-%d")
        date_range = f"{first_date} to {last_date}"
    else:
        date_range = "no messages"

    # Count text messages (non-media)
    text_msgs = sum(1 for m in messages if m["msg_type"] == 0)
    media_msgs = len(messages) - text_msgs

    # Unique senders
    senders = sorted(set(m["sender"] for m in messages if m["sender"] != "You"))

    lines = [
        f"# {name}",
        "",
        "## Metadata",
        f"- **Type:** {stype}",
        f"- **JID:** `{session['jid']}`",
        f"- **Messages:** {len(messages)} ({text_msgs} text, {media_msgs} media/system)",
        f"- **Date Range:** {date_range}",
        f"- **Last Message:** {coredata_to_str(session['last_message_date'])}",
    ]

    if participants:
        lines.append(f"- **Participants ({len(participants)}):** {', '.join(participants[:50])}")
        if len(participants) > 50:
            lines.append(f"  *(and {len(participants) - 50} more)*")
    elif senders:
        lines.append(f"- **Participants:** {', '.join(senders[:30])}")

    lines.extend(["", "---", "", "## Messages", ""])

    # Group messages by date
    current_date = ""
    for msg in messages:
        msg_date = coredata_to_str(msg["date"], "%Y-%m-%d")
        if msg_date != current_date:
            current_date = msg_date
            lines.append(f"### {current_date}")
            lines.append("")

        time_str = coredata_to_str(msg["date"], "%H:%M")
        sender = msg["sender"]
        content = msg["content"]

        # Format multi-line messages
        content_lines = content.split("\n")
        if len(content_lines) > 1:
            first_line = content_lines[0]
            rest = "\n".join(f"  {l}" for l in content_lines[1:])
            lines.append(f"**[{time_str}] {sender}:** {first_line}")
            lines.append(rest)
        else:
            lines.append(f"**[{time_str}] {sender}:** {content}")

        lines.append("")

    return "\n".join(lines)


def get_last_run_timestamp() -> float | None:
    """Get the Core Data timestamp of the last successful run."""
    if LAST_RUN_FILE.exists():
        try:
            data = json.loads(LAST_RUN_FILE.read_text())
            return data.get("last_run_coredata_ts")
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def save_last_run_timestamp(ts: float) -> None:
    """Save the current run timestamp."""
    data = {
        "last_run_coredata_ts": ts,
        "last_run_utc": coredata_to_str(ts, "%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    LAST_RUN_FILE.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract WhatsApp conversations to markdown")
    parser.add_argument("--full", action="store_true", help="Full re-extraction (ignore last run)")
    parser.add_argument("--since", type=int, metavar="DAYS", help="Extract messages from last N days")
    parser.add_argument("--chat", type=str, metavar="NAME", help="Extract only chats matching NAME")
    parser.add_argument("--min-messages", type=int, default=1, help="Skip chats with fewer messages (default: 1)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be extracted without writing")
    args = parser.parse_args()

    # Validate DB exists
    if not DB_PATH.exists():
        print(f"ERROR: WhatsApp database not found at {DB_PATH}")
        print("Make sure WhatsApp is installed and has synced.")
        sys.exit(1)

    # Ensure output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Determine since timestamp
    since_ts: float | None = None
    if args.full:
        since_ts = None
        print("Mode: FULL re-extraction")
    elif args.since:
        since_dt = datetime.now(timezone.utc).timestamp() - (args.since * 86400)
        since_ts = since_dt - COREDATA_EPOCH
        print(f"Mode: Last {args.since} days")
    else:
        since_ts = get_last_run_timestamp()
        if since_ts:
            print(f"Mode: Incremental (since {coredata_to_str(since_ts)})")
        else:
            print("Mode: FULL (no previous run found)")

    # Connect read-only
    db = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    db.execute("PRAGMA query_only = ON")

    try:
        # Build name resolver
        print("Building name resolver...", end=" ", flush=True)
        resolver = build_name_resolver(db)
        print(f"{len(resolver)} names loaded")

        # Get chat sessions
        sessions = get_chat_sessions(db, chat_filter=args.chat)
        print(f"Found {len(sessions)} active conversations")

        # Track max timestamp for incremental
        max_ts: float = since_ts or 0.0

        # Stats
        total_chats = 0
        total_messages = 0
        skipped_empty = 0

        for i, session in enumerate(sessions):
            name = session["name"]

            # Get messages
            messages = get_messages(db, session["pk"], resolver, since_ts=since_ts)

            if len(messages) < args.min_messages:
                skipped_empty += 1
                continue

            # Track max timestamp
            for msg in messages:
                if msg["date"] and msg["date"] > max_ts:
                    max_ts = msg["date"]

            # Get participants for groups
            participants: list[str] = []
            if session["session_type"] in (1, 4):  # Group or Community
                participants = get_group_participants(db, session["pk"], resolver)

            total_chats += 1
            total_messages += len(messages)

            if args.dry_run:
                stype = SESSION_TYPE_MAP.get(session["session_type"], "?")
                print(f"  [{stype}] {name}: {len(messages)} messages")
                continue

            # Format and write
            markdown = format_conversation_markdown(session, messages, participants)
            filename = sanitize_filename(name) + ".md"
            filepath = OUTPUT_DIR / filename

            filepath.write_text(markdown, encoding="utf-8")

            if (i + 1) % 50 == 0 or (i + 1) == len(sessions):
                print(f"  Progress: {i + 1}/{len(sessions)} sessions processed")

        # Save last run timestamp
        if not args.dry_run and max_ts > 0:
            save_last_run_timestamp(max_ts)

        # Summary
        print(f"\n{'DRY RUN ' if args.dry_run else ''}Summary:")
        print(f"  Conversations exported: {total_chats}")
        print(f"  Total messages: {total_messages:,}")
        print(f"  Skipped (< {args.min_messages} msgs): {skipped_empty}")
        if not args.dry_run:
            print(f"  Output: {OUTPUT_DIR}/")
            print(f"  Last run saved: {coredata_to_str(max_ts)}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
