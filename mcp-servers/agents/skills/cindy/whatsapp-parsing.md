# WhatsApp Parsing — Cindy Skill

## Overview

Cindy processes WhatsApp messages from daily iCloud backup extraction. A Mac cron job
(3:00 AM IST) downloads `ChatStorage.sqlite`, parses new conversations since last
extraction, and sends structured data to the droplet.

## ChatStorage.sqlite Schema

WhatsApp on iOS uses Core Data (Apple's ORM). The database uses **Apple Core Foundation
timestamps** (seconds since 2001-01-01 00:00:00 UTC), NOT Unix epoch.

### Key Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `ZWACHATSESSION` | Conversations | `Z_PK`, `ZCONTACTJID`, `ZPARTNERNAME`, `ZSESSIONTYPE` (0=1:1, 1=group) |
| `ZWAMESSAGE` | Messages (~34 cols) | `Z_PK`, `ZCHATSESSION`, `ZFROMJID`, `ZTEXT`, `ZMESSAGEDATE`, `ZMESSAGETYPE`, `ZISFROMME`, `ZPARENTMESSAGE` |
| `ZWAMEDIAITEM` | Media metadata | `ZMESSAGE`, `ZMEDIALOCALPATH`, `ZFILESIZE`, `ZMEDIAURL`, `ZVCARDSTRING` |
| `ZWAPROFILEPUSHNAME` | Display names | `ZJID`, `ZPUSHNAME` |

### JID Format

- Individual: `919999999999@s.whatsapp.net` (country code + number)
- Group: `120363025555555555@g.us`
- Status/broadcast: `status@broadcast`

### Timestamp Conversion

Apple Core Foundation timestamp to ISO 8601:
```python
from datetime import datetime, timedelta

def cf_to_iso(cf_timestamp):
    """Convert Apple Core Foundation timestamp to ISO 8601."""
    epoch = datetime(2001, 1, 1)
    return (epoch + timedelta(seconds=cf_timestamp)).isoformat() + 'Z'
```

### Message Types (ZMESSAGETYPE)

| Value | Type |
|-------|------|
| 0 | Text |
| 1 | Image |
| 2 | Video |
| 3 | Voice note |
| 5 | Location |
| 7 | Document |
| 8 | Sticker |
| 14 | Deleted message |
| 15 | Call |

## Ingestion Flow

The Mac extraction script sends structured batches to the droplet:

```json
{
  "type": "cindy_whatsapp",
  "content": "WhatsApp batch: 47 new messages across 12 conversations",
  "metadata": {
    "extraction_timestamp": "2026-03-20T03:15:00+05:30",
    "conversations": [
      {
        "chat_jid": "919999999999@s.whatsapp.net",
        "chat_name": "Rahul Sharma",
        "session_type": 0,
        "participants": ["+919999999999"],
        "messages": [
          {
            "sender_jid": "919999999999@s.whatsapp.net",
            "is_from_me": false,
            "text": "Great meeting today. Let's sync on the Series A terms next week.",
            "timestamp": "2026-03-19T18:45:00+05:30",
            "message_type": 0,
            "media_meta": null,
            "reply_to_stanza_id": null
          }
        ]
      }
    ]
  }
}
```

## Processing Steps

### 1. Parse Batch

Iterate over `metadata.conversations`. For each conversation:
- Extract `chat_jid`, `chat_name`, `session_type`, `participants`
- Group messages by conversation

### 2. Participant Resolution

```
JID → strip @s.whatsapp.net → phone number → Network DB match

Example:
  "919999999999@s.whatsapp.net" → "+919999999999"
```

```bash
# Resolve by phone
psql $DATABASE_URL -t -A -c "SELECT id, person_name FROM network WHERE phone = '+919999999999';"
```

If no match, use `chat_name` (from `ZWAPROFILEPUSHNAME`) for name-based resolution:

```bash
# Fuzzy name match
psql $DATABASE_URL -t -A -c "SELECT id, person_name, role_title FROM network WHERE LOWER(person_name) = LOWER('Rahul Sharma');"
```

If still no match: create `datum_person` with phone number + push name.

### 3. Group Chat Handling

For group chats (`session_type: 1`):
- Extract all participant JIDs from the conversation
- Resolve each participant individually
- Group name often indicates context (e.g., "Z47 Investment Team", "DeVC Founders")
- Flag Z47/DeVC internal group chats — these contain high-density signals

### 4. Conversation Classification

Classify each conversation before signal extraction. Only extract signals from
deal, portfolio, and thesis-relevant conversations.

| Classification | Keywords / Patterns | Action |
|---------------|-------------------|--------|
| **Deal-related** | company names, valuations, terms, funding | Full signal extraction |
| **Portfolio update** | Known portfolio company names, founder names | Full signal extraction |
| **Thesis-relevant** | Industry terms, technology trends, market signals | Full signal extraction |
| **Operational** | Scheduling, logistics, "meeting at", "call at" | Log interaction only, skip signals |
| **Social** | Personal topics, greetings, informal | Log interaction only, skip signals |

### 5. Reply Chain Reconstruction

`ZWAMESSAGE.ZPARENTMESSAGE` is a foreign key to the parent message, enabling reply thread
reconstruction. Use this to understand conversation flow:

```
Message A: "What do you think about Composio's valuation?"
  └─ Reply B: "I think $100M pre is aggressive but defensible given growth."
     └─ Reply C: "Agreed. Let's discuss at the IC meeting."
```

This reveals deliberation chains that are higher-signal than isolated messages.

## Privacy Constraints (MANDATORY)

### What Gets Stored

```sql
INSERT INTO interactions (source, source_id, participants, linked_people,
                          summary, raw_data, timestamp)
VALUES ('whatsapp', 'wa_919999999999_20260319',
        ARRAY['+919999999999'],
        ARRAY[42],
        'Discussion about Composio Series A terms. Rahul proposes syncing next week.',
        '{"chat_name": "Rahul Sharma", "message_count": 8, "session_type": 0,
          "media_types": ["document"], "has_voice_notes": false}'::jsonb,
        '2026-03-19T18:45:00+05:30');
```

### What NEVER Gets Stored

- Raw message text (use for in-context signal extraction, then discard)
- Individual messages from non-Aakash participants in group chats
- Media file content (images, documents, voice notes, videos)
- Voice note transcriptions
- Location data

### raw_data for WhatsApp

The `raw_data` JSONB for WhatsApp interactions contains ONLY metadata:

```json
{
  "chat_name": "Rahul Sharma",
  "session_type": 0,
  "message_count": 8,
  "time_span": {"first": "2026-03-19T14:00:00Z", "last": "2026-03-19T18:45:00Z"},
  "media_types": ["document"],
  "has_voice_notes": false,
  "has_forwarded_content": true,
  "classification": "deal"
}
```

## WhatsApp-Specific Signal Detection

| Signal | Detection Pattern | Downstream |
|--------|------------------|-----------|
| Forwarded content | WhatsApp forward metadata flag | Content Agent (if URL/article) |
| Voice note | `message_type: 3` | Log existence, flag for manual review |
| Document share | `message_type: 7` | Log filename, flag if deck/terms |
| Group consensus | Multiple participants agreeing | Thesis signal (stronger than 1:1) |
| Meeting debrief | Discussion about a meeting | Link to Calendar event, fill context gap |
| Deal urgency | "urgent", "asap", "deadline", "tomorrow" | Time-sensitive action item |

## Incremental Extraction

The Mac extraction script maintains `last_extraction_timestamp` (Apple CF format) in a
local state file. Each run queries:

```sql
SELECT * FROM ZWAMESSAGE
WHERE ZMESSAGEDATE > last_extraction_timestamp
ORDER BY ZMESSAGEDATE ASC;
```

This ensures only new messages since the last run are processed.

## Error Handling

| Error | Action |
|-------|--------|
| Empty conversation (0 messages) | Skip, do not create interaction |
| Missing chat_name | Use JID as identifier |
| Corrupt timestamp | Skip individual message, process rest of conversation |
| Extraction script failure | Log "WhatsApp extraction failed". Write notification. |
| Batch > 20 conversations | Process first 20. ACK with remainder note. |
