# Email Processing — Cindy Skill

## Overview

Cindy processes emails from AgentMail webhook events delivered to `cindy@agent.aicos.ai`.
Aakash CCs or forwards relevant emails. AgentMail auto-threads conversations, strips
quoted history, and pushes events via WebSocket.

## AgentMail Event Structure

When the WebSocket listener receives a `message.received` event, it writes to `cai_inbox`:

```json
{
  "type": "cindy_email",
  "content": "New email from AgentMail inbox",
  "metadata": {
    "from": "rahul@composio.dev",
    "from_name": "Rahul Sharma",
    "to": ["ak@z47.com"],
    "cc": ["cindy@agent.aicos.ai", "sneha@z47.com"],
    "subject": "Re: Series A follow-up",
    "thread_id": "thd_abc123",
    "extracted_text": "...",
    "full_text": "...",
    "html": "...",
    "attachments": [
      {"id": "att_123", "name": "deck.pdf", "size": 1024000, "content_type": "application/pdf"}
    ],
    "message_id": "<msg_id@agentmail.to>",
    "in_reply_to": "<parent_msg_id@agentmail.to>",
    "received_at": "2026-03-20T10:30:00Z"
  }
}
```

## Key Fields

| Field | Purpose | Usage |
|-------|---------|-------|
| `extracted_text` | Reply content only (quoted history stripped by Talon) | Use for signal extraction |
| `full_text` | Complete email including quotes | Store in raw_data for context |
| `thread_id` | AgentMail's native thread grouping | Maps to interactions.thread_id |
| `from_name` | Display name parsed from email headers | Use for people resolution when email not in Network DB |
| `message_id` | Unique message identifier | Maps to interactions.source_id |
| `in_reply_to` | Parent message reference | Thread chain reconstruction |

## Processing Steps

### 1. Parse and Dedup

```bash
# Check if already processed
psql $DATABASE_URL -t -A -c "SELECT id FROM interactions WHERE source = 'email' AND source_id = '<msg_id>';"
```

If exists, this is a re-delivery. Update linked_people if new participants, skip full re-processing.

### 2. Thread Management

```bash
# Check for existing thread
psql $DATABASE_URL -t -A -c "SELECT id, summary FROM interactions WHERE source = 'email' AND thread_id = 'thd_abc123' ORDER BY timestamp DESC LIMIT 1;"
```

If thread exists: this is a continuation. Create new interaction record linked to same thread.
Accumulate participants across the thread for broader people resolution.

### 3. People Resolution

Extract all email addresses from `from`, `to`, and `cc` fields. For each:

```bash
# Resolve by email
psql $DATABASE_URL -t -A -c "SELECT id, person_name FROM network WHERE email = 'rahul@composio.dev';"
```

If no match: extract name from `from_name` field. Create `datum_person` inbox message.

### 4. Signal Extraction

Use `extracted_text` (not `full_text`) for signal extraction. This is the reply content
only, with quoted history stripped by AgentMail's Talon library.

**Action item patterns:**
- "Let's schedule..." / "Can we meet..."
- "I'll send..." / "Will circle back..."
- "Can you..." / "Could you..."
- "Need to..." / "Should we..."
- Explicit deadlines: "by Friday", "next week", "before the BRC"

**Deal signal patterns:**
- "term sheet" / "valuation" / "cap table"
- "$NM at $NM pre" / "follow-on" / "bridge"
- "runway" / "burn rate" / "revenue"
- "Series A/B/C" / "round" / "fundraise"

**Thesis signal patterns:**
- Industry trend mentions
- Competitive intelligence
- Market data / growth metrics
- Technology shift indicators

**Intro request patterns:**
- "I'd like to introduce you to..."
- "You should meet..."
- "Connecting you with..."
- "Looping in..."

### 5. Attachment Handling

Log attachment metadata only. Flag high-signal attachments:

| Content Type | Signal Level | Action |
|-------------|-------------|--------|
| `application/pdf` with "deck" / "pitch" | High | Note in deal_signals |
| `application/pdf` with "term" | High | Note in deal_signals, flag for Megamind |
| `text/calendar` (.ics) | Medium | Parse with `icalendar`, create calendar interaction |
| `image/*` | Low | Log metadata only |
| Other | Low | Log metadata only |

### 6. Calendar Invite Detection

When an attachment has `content_type: "text/calendar"` or filename ending in `.ics`:

```bash
# Parse .ics with Python icalendar library via Bash
python3 -c "
import icalendar
import json
import sys

cal = icalendar.Calendar.from_ical(sys.stdin.read())
for event in cal.walk('VEVENT'):
    print(json.dumps({
        'uid': str(event.get('UID', '')),
        'summary': str(event.get('SUMMARY', '')),
        'dtstart': event.get('DTSTART').dt.isoformat() if event.get('DTSTART') else None,
        'dtend': event.get('DTEND').dt.isoformat() if event.get('DTEND') else None,
        'attendees': [str(a) for a in (event.get('ATTENDEE', []) if isinstance(event.get('ATTENDEE', []), list) else [event.get('ATTENDEE')] if event.get('ATTENDEE') else [])],
        'location': str(event.get('LOCATION', '')),
    }))
" <<< "$ICS_CONTENT"
```

Create a separate `cindy_calendar` inbox message for the extracted event.

## AgentMail Labels

After processing, tag emails via AgentMail Labels API (for debugging and audit):

| Label | When |
|-------|------|
| `processed` | After successful processing |
| `action-required` | Contains extracted action items |
| `thesis-signal` | Contains thesis-relevant signals |
| `deal-signal` | Contains deal-related language |

## Error Handling

| Error | Action |
|-------|--------|
| Missing `extracted_text` | Fall back to `full_text`, log warning |
| Missing `from` field | Log error, skip people resolution for sender |
| Malformed `thread_id` | Create interaction without thread linking |
| Attachment download failure | Log metadata only, skip content analysis |
