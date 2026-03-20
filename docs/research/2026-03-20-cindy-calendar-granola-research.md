# Cindy Communications Agent: Calendar & Granola Integration Research

**Date:** 2026-03-20
**Purpose:** Research calendar access, Granola MCP capabilities, gap detection algorithm, and WebFront UI concept for the Cindy Communications Agent.
**Prerequisite:** [Cindy Email Infrastructure Research](./2026-03-20-cindy-email-infrastructure.md) (AgentMail as email backbone)

---

## Executive Summary

Cindy needs to know about ALL meetings, detect which ones she lacks rich context on, and proactively ask Aakash for information. This research covers three integration paths and a gap detection algorithm.

**Recommended approach:** A three-source calendar awareness system:

1. **Google Calendar API** (primary, real-time) -- poll or push-notify for all calendar events. Richest data: attendees with emails, response status, conference links, recurrence, description.
2. **Granola MCP** (post-meeting enrichment) -- match completed meetings to Granola notes via time window + attendee overlap. Extract transcripts, AI summaries, action items.
3. **AgentMail .ics parsing** (supplementary) -- when Cindy is CC'd on calendar invites, parse the .ics attachment for meeting context. Works as a fallback and as the trigger for Cindy's awareness that she's been explicitly included.

**Gap detection:** For each upcoming/recent meeting, score context richness across 4 sources (Granola transcript, email thread, WhatsApp thread, Network DB history). Meetings scoring below threshold trigger a proactive context request via WebFront.

---

## Part 1: Calendar Integration

### 1.1 Three Approaches Compared

| Approach | Data Richness | Real-time | Setup Complexity | Best For |
|----------|--------------|-----------|------------------|----------|
| **Google Calendar API** | Highest (full event resource) | Push or poll | Medium (OAuth 2.0, GCP project) | Primary calendar awareness |
| **AgentMail .ics parsing** | Good (standard iCal fields) | Push (email webhook) | Low (already planned for Cindy) | Supplementary; explicit CC trigger |
| **Gmail search for invites** | Medium (email metadata + .ics) | Poll | Low (already connected via MCP) | Fallback; historical lookups |

### 1.2 Google Calendar API (Recommended Primary)

**Why:** Aakash uses M365 for work email/calendar (from CONTEXT.md), but Granola's calendar sync and the existing `Google Calendar MCP` reference in CONTEXT.md indicate Google Calendar is also in play. The Google Calendar API provides the richest programmatic access to events.

**Key finding:** No Google Calendar MCP tool currently exists in the available toolset. CONTEXT.md lists it as "Connected" but it may be a Granola-mediated connection or a planned integration. This means either:
- (a) A Google Calendar MCP connector needs to be set up (Claude.ai supports Google Calendar as a connector), or
- (b) We use the Google Calendar REST API directly from the droplet agent

#### Event Resource Schema (What's Available)

The Google Calendar Event resource provides everything Cindy needs:

```
Core:        id, summary (title), description, location, status
Timing:      start.dateTime, end.dateTime, timeZone, recurrence
People:      organizer.email, creator.email
             attendees[].email, attendees[].displayName,
             attendees[].responseStatus (needsAction|accepted|declined|tentative)
Conference:  conferenceData.entryPoints[].uri (Meet/Zoom links)
Versioning:  sequence (increment = update), updated (ISO timestamp)
Identity:    iCalUID (matches .ics UID for cross-referencing)
```

#### Change Detection: New vs Updated vs Cancelled

| Signal | How to Detect |
|--------|---------------|
| **New event** | `events.list()` with `syncToken` returns new items; `status: "confirmed"` |
| **Updated event** | `sequence` incremented; `updated` timestamp changed; `syncToken` delta |
| **Cancelled event** | `status: "cancelled"` in response |
| **RSVP change** | `attendees[].responseStatus` changed between polls |

**Recommended polling pattern:**
1. Initial sync: `events.list(calendarId='primary', timeMin=now-7d, singleEvents=true)` -- get baseline
2. Incremental sync: Use `syncToken` from previous response. Returns only changed events since last sync.
3. Poll frequency: Every 5 minutes (matches content pipeline cadence)
4. Store `syncToken` in Postgres for persistence across restarts

**Push notification alternative:** Google Calendar supports webhooks (`events.watch()`), but requires:
- HTTPS endpoint with valid SSL certificate
- Domain verification with Google
- Channels expire (max 30 days) and must be renewed
- Notifications tell you *something changed* but not *what* -- you still need to call `events.list()` with syncToken

**Verdict:** Polling with syncToken is simpler and sufficient for 5-minute cadence. Push notifications add complexity for marginal latency improvement.

#### Python Implementation Pattern

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_info(token_info)
service = build('calendar', 'v3', credentials=creds)

# Incremental sync (after initial load)
events_result = service.events().list(
    calendarId='primary',
    syncToken=stored_sync_token,  # from previous run
    singleEvents=True,
    maxResults=50
).execute()

for event in events_result.get('items', []):
    status = event.get('status')  # confirmed, cancelled
    summary = event.get('summary', 'No title')
    start = event['start'].get('dateTime', event['start'].get('date'))
    attendees = event.get('attendees', [])
    sequence = event.get('sequence', 0)

    attendee_emails = [a['email'] for a in attendees]
    response_map = {a['email']: a.get('responseStatus') for a in attendees}

# Save new syncToken for next run
new_sync_token = events_result.get('nextSyncToken')
```

#### Auth Considerations

Google Calendar API requires OAuth 2.0 with these scopes:
- `https://www.googleapis.com/auth/calendar.readonly` (read-only access to all calendars)
- Refresh token management (similar pattern to Granola's WorkOS tokens)

If Aakash's primary calendar is actually **M365/Outlook**, the equivalent is **Microsoft Graph API**:
- Endpoint: `GET /me/calendar/events`
- Delta queries: `GET /me/calendarView/delta` (equivalent to syncToken)
- Attendees: `event.attendees[].emailAddress.address`
- Same polling pattern works

**Action needed:** Confirm whether Aakash's primary meeting calendar is Google Calendar or M365 Outlook. The API approach is nearly identical; only the auth and endpoint differ.

### 1.3 AgentMail .ics Parsing (Supplementary Path)

When Aakash adds `cindy@aicos.ai` (or `cindy@agent.aicos.ai`) to a calendar invite, it arrives as an email with a `text/calendar` MIME part containing a `.ics` attachment.

#### How Calendar Invites Arrive via Email

Calendar invites sent via email follow the iTIP standard (RFC 5546):

```
Email Headers:
  Content-Type: multipart/mixed; OR multipart/alternative;

Parts:
  Part 1: text/plain (human-readable description)
  Part 2: text/html (formatted description)
  Part 3: text/calendar; method=REQUEST; name="invite.ics"
          (the actual .ics data -- this is what we parse)
```

#### .ics File Structure and Fields

An .ics file (RFC 5545) contains a `VCALENDAR` with one or more `VEVENT` components:

```
BEGIN:VCALENDAR
METHOD:REQUEST                    ← REQUEST (new/update), CANCEL, REPLY
BEGIN:VEVENT
UID:unique-id@calendar            ← Stable ID across updates
SEQUENCE:0                        ← Increments on update (0=new, 1+=update)
STATUS:CONFIRMED                  ← CONFIRMED, CANCELLED, TENTATIVE
DTSTART:20260320T143000Z          ← Start time (UTC or with TZID)
DTEND:20260320T150000Z            ← End time
SUMMARY:Board Review - XYZ Corp   ← Meeting title
DESCRIPTION:Quarterly review...   ← Meeting description/agenda
LOCATION:Google Meet / Room 4B    ← Physical or virtual location
ORGANIZER;CN=Aakash:mailto:ak@z47.com  ← Organizer name + email
ATTENDEE;CN=Jane;PARTSTAT=ACCEPTED:mailto:jane@xyz.com   ← Each attendee
ATTENDEE;CN=Cindy;PARTSTAT=NEEDS-ACTION:mailto:cindy@aicos.ai
RRULE:FREQ=WEEKLY;COUNT=10       ← Recurrence rule (if recurring)
END:VEVENT
END:VCALENDAR
```

#### Detecting New vs Updated vs Cancelled

| METHOD | SEQUENCE | Meaning |
|--------|----------|---------|
| `REQUEST` | 0 | New meeting invitation |
| `REQUEST` | > 0 | Updated meeting (time/location/attendees changed) |
| `CANCEL` | any | Meeting cancelled |
| `REPLY` | any | Attendee RSVP response |

#### Python Parsing with `icalendar` Library

```python
from icalendar import Calendar
from email import message_from_bytes

def parse_calendar_invite(raw_email: bytes) -> dict | None:
    """Extract meeting details from an email with .ics attachment."""
    msg = message_from_bytes(raw_email)

    for part in msg.walk():
        content_type = part.get_content_type()

        if content_type == 'text/calendar':
            ics_data = part.get_payload(decode=True)
            cal = Calendar.from_ical(ics_data)

            method = str(cal.get('METHOD', 'REQUEST'))

            for component in cal.walk():
                if component.name == 'VEVENT':
                    return {
                        'method': method,  # REQUEST, CANCEL, REPLY
                        'uid': str(component.get('UID')),
                        'sequence': int(component.get('SEQUENCE', 0)),
                        'status': str(component.get('STATUS', 'CONFIRMED')),
                        'summary': str(component.get('SUMMARY', '')),
                        'description': str(component.get('DESCRIPTION', '')),
                        'location': str(component.get('LOCATION', '')),
                        'dtstart': component.get('DTSTART').dt,
                        'dtend': component.get('DTEND').dt,
                        'organizer': str(component.get('ORGANIZER', '')),
                        'attendees': [
                            {
                                'email': str(a).replace('mailto:', ''),
                                'name': a.params.get('CN', ''),
                                'status': a.params.get('PARTSTAT', 'NEEDS-ACTION'),
                                'rsvp': a.params.get('RSVP', 'FALSE'),
                            }
                            for a in (component.get('ATTENDEE', [])
                                      if isinstance(component.get('ATTENDEE'), list)
                                      else [component.get('ATTENDEE')]
                                      if component.get('ATTENDEE') else [])
                        ],
                        'recurrence': str(component.get('RRULE', '')),
                    }
    return None
```

**Library:** `pip install icalendar` (mature, RFC 5545 compliant, actively maintained -- v7.0+)

#### AgentMail Integration Point

When a `message.received` event arrives via WebSocket:

```python
async def process_email_for_cindy(msg):
    # Check if this email contains a calendar invite
    for attachment in msg.attachments:
        if attachment.content_type == 'text/calendar' or attachment.filename.endswith('.ics'):
            ics_data = client.inboxes.messages.get_attachment(
                inbox_id=inbox.inbox_id,
                message_id=msg.message_id,
                attachment_id=attachment.attachment_id
            )
            meeting = parse_ics(ics_data)
            if meeting:
                await handle_calendar_event(meeting)
```

**Note:** Some calendar systems send the .ics as a MIME part (not a named attachment). AgentMail's `extracted_text` may not capture this. Need to test whether AgentMail exposes raw MIME parts or only parsed text/HTML/attachments.

### 1.4 Gmail MCP for Calendar Invite Lookup (Fallback)

The Gmail MCP tools (`gmail_search_messages`, `gmail_read_message`) can search for calendar invites in Aakash's Gmail:

```
# Search for calendar invites
gmail_search_messages(q="has:attachment filename:ics newer_than:7d")
gmail_search_messages(q="from:calendar-notification@google.com")
gmail_search_messages(q="subject:invitation newer_than:1d")
```

**Limitation:** This gives access to Aakash's personal Gmail, not the M365 work calendar. Useful for personal meetings only. Work meetings on M365 would need Microsoft Graph API or the .ics-via-AgentMail approach.

### 1.5 Calendar Integration Decision Matrix

| Scenario | Recommended Source |
|----------|--------------------|
| Full calendar awareness (all meetings) | Google Calendar API or MS Graph API (poll with syncToken/delta) |
| Cindy explicitly included in invite | AgentMail .ics parsing (email webhook) |
| Historical meeting lookup | Gmail MCP search + Granola query |
| Meeting metadata for gap detection | Calendar API (attendees, time) cross-referenced with Granola |

---

## Part 2: Granola MCP Capabilities

### 2.1 Available Tools (Verified)

Four MCP tools are connected and operational:

#### `list_meetings`
- **Input:** `time_range` (enum: `this_week`, `last_week`, `last_30_days`)
- **Output:** Meeting titles and metadata (no transcripts)
- **Use:** Discovery -- find meetings, get IDs for deeper queries
- **Limitation:** Fixed time ranges only; no custom date range; no `custom` option despite prior research suggesting one

#### `get_meetings`
- **Input:** `meeting_ids` (array of UUIDs, max 10)
- **Output:** Private notes, AI-generated summary, attendees, metadata
- **Use:** Detailed meeting info after identifying IDs via `list_meetings`
- **Key data:** This is where **attendee lists** and **AI summaries** come from

#### `get_meeting_transcript`
- **Input:** `meeting_id` (single UUID)
- **Output:** Full verbatim transcript (utterance-by-utterance)
- **Use:** Raw transcript for signal extraction, exact quotes
- **Note:** Returns 404 if meeting has no recording/transcript

#### `query_granola_meetings`
- **Input:** `query` (natural language string), optional `document_ids` (UUID array)
- **Output:** AI-generated response with inline citation links to source meetings
- **Use:** Semantic search across all meetings ("What did [person] say about [topic]?")
- **Best for:** Open-ended questions, finding mentions across multiple meetings

### 2.2 Data Available Per Meeting

From the Granola API (via MCP tools and Enterprise API docs):

| Data Field | Available Via | Notes |
|------------|--------------|-------|
| Meeting title | `list_meetings`, `get_meetings` | From calendar sync |
| Date/time | `list_meetings`, `get_meetings` | `meeting_date` from first transcript timestamp |
| Attendees (names) | `get_meetings` | Via calendar sync; includes names |
| Attendees (emails) | `get_meetings` (Enterprise API) | The Enterprise API `/v0/notes/{id}` returns `calendar_event.invitees` |
| AI summary | `get_meetings` | Auto-generated after meeting |
| Action items | `get_meetings`, `query_granola_meetings` | In AI summary section |
| Full transcript | `get_meeting_transcript` | Utterance array: `{source, text, start_timestamp, end_timestamp, confidence}` |
| Speaker identification | `get_meeting_transcript` | `source: "microphone"` (Aakash) vs `source: "system"` (others). No multi-speaker diarization on desktop. |
| Private notes | `get_meetings` | Aakash's manual notes added during meeting |
| ProseMirror content | `get_meetings` | Rich-text formatted notes (convertible to Markdown) |

### 2.3 Matching Granola Meetings to Calendar Events

**The matching problem:** A calendar event says "Meeting with Jane Doe, 2:30 PM." Granola has a meeting note titled "Jane Doe - Product Review." How do we know they're the same meeting?

**Matching strategy (multi-signal):**

```
match_score = 0

# 1. Time overlap (strongest signal)
if granola.meeting_date overlaps calendar.start within ±15 minutes:
    match_score += 0.5

# 2. Attendee overlap (strong signal)
calendar_emails = {a.email for a in calendar.attendees}
granola_names = {a.name for a in granola.attendees}
if fuzzy_match(calendar_emails, granola_names) > 0.5:
    match_score += 0.3

# 3. Title similarity (weak signal -- titles often differ)
if fuzzy_match(calendar.summary, granola.title) > 0.4:
    match_score += 0.2

# Match threshold: 0.5+ = confident match
```

**Why time alone isn't enough:** Back-to-back meetings (common for Aakash with 7-8/day) may overlap. Combining time + attendees gives high confidence.

**Why title matching is weak:** Calendar says "Catch-up with Jane" but Granola says "XYZ Corp Board Prep" (because Aakash changed the note title). Attendee matching is more reliable.

### 2.4 Historical Depth

- `list_meetings` supports `last_30_days` as the maximum predefined range
- The Enterprise API (`/v0/notes`) supports `created_after` / `created_before` parameters for arbitrary date ranges
- The MCP tool `query_granola_meetings` appears to search across all available meetings (no explicit time limit documented)
- Practically, Granola retains all meetings since the user started using it

### 2.5 Transcript Availability Timing

- Transcripts are available **2-5 minutes** after meeting ends (processing delay)
- The automated pipeline should wait **5+ minutes** after `calendar.end` before querying Granola
- If transcript isn't ready yet (404), retry with exponential backoff (5 min, 10 min, 20 min)

---

## Part 3: Gap Detection Algorithm

### 3.1 The Core Problem

Cindy needs to answer: "For this meeting, do I have enough context to be useful -- or do I need to ask Aakash?"

### 3.2 Context Sources (4 pillars)

For each meeting, check these sources:

| Source | What It Provides | How to Check |
|--------|------------------|--------------|
| **Granola** | Transcript, AI summary, action items | `get_meetings` by time-matched ID; check for non-null transcript |
| **Email threads** | Discussion context, shared docs, decisions | Gmail MCP: `search_messages(q="from:{attendee_email} OR to:{attendee_email} newer_than:30d")` |
| **Network DB** | Person history, IDS state, relationship context | Supabase query: `network_master WHERE email IN (attendee_emails)` |
| **WhatsApp** | Async context, quick updates, relationship signals | Future integration; currently not available programmatically |

### 3.3 Context Richness Score

```python
def compute_context_richness(meeting: CalendarEvent) -> float:
    """
    Score 0.0 to 1.0 indicating how much context Cindy has for this meeting.
    Below 0.3 = context gap -> ask Aakash.
    0.3-0.6 = partial context -> present what we have, offer to fill gaps.
    Above 0.6 = rich context -> no intervention needed.
    """
    score = 0.0
    weights = {
        'granola': 0.35,      # Transcript is the richest single source
        'email': 0.25,        # Email threads provide decision context
        'network_db': 0.25,   # Person history enables personalized prep
        'whatsapp': 0.15,     # Async signals (future; default 0 for now)
    }

    # Granola check
    granola_match = find_granola_match(meeting)
    if granola_match:
        has_transcript = granola_match.transcript is not None
        has_summary = granola_match.summary is not None
        granola_score = (0.7 if has_transcript else 0.0) + (0.3 if has_summary else 0.0)
        score += weights['granola'] * granola_score

    # Email thread check
    attendee_emails = [a.email for a in meeting.attendees if a.email != aakash_email]
    email_threads = search_email_threads(attendee_emails, days=30)
    if email_threads:
        # More threads = more context; cap at 1.0
        email_score = min(len(email_threads) / 5.0, 1.0)
        score += weights['email'] * email_score

    # Network DB check
    known_attendees = lookup_network_db(attendee_emails)
    if known_attendees:
        # Score based on: have we met before? Do we have IDS state?
        network_score = sum(
            0.5 + (0.5 if person.ids_state else 0.0)
            for person in known_attendees
        ) / max(len(attendee_emails), 1)
        score += weights['network_db'] * min(network_score, 1.0)

    # WhatsApp check (future -- always 0 for now)
    score += 0.0

    return score
```

### 3.4 Gap Detection Flow

```
EVERY 5 MINUTES (or triggered by calendar change):

1. FETCH calendar events for next 48 hours
   └── Google Calendar API: events.list(timeMin=now, timeMax=now+48h)

2. For each event with 2+ attendees:
   a. Compute context_richness_score
   b. If score < 0.3 AND event starts within 24 hours:
      → URGENT: Create "context gap" card on WebFront
      → "You have a meeting with [Person] in [X hours] -- I don't have context."
   c. If score < 0.3 AND event is 24-48 hours away:
      → PLANNED: Queue context request (give Aakash time)
   d. If score 0.3-0.6:
      → PARTIAL: Show what we have, offer to enrich
   e. If score > 0.6:
      → GOOD: No action needed; context available for meeting prep

3. For PAST events (last 24 hours, meeting already happened):
   a. Check if Granola transcript exists
   b. If NO transcript after 30 minutes post-meeting:
      → "Meeting with [Person] ended but no transcript found. Was this a no-show?"
   c. If transcript exists:
      → Queue for post-meeting signal extraction pipeline
```

### 3.5 Context Gap Types

| Gap Type | Trigger | Cindy's Ask |
|----------|---------|-------------|
| **Complete blank** | Score < 0.1; unknown attendees, no email, no Granola | "Who is [Person]? What's this meeting about? What should we discuss?" |
| **Known person, no recent context** | Network DB match but no recent email/Granola | "Last interaction with [Person] was [X weeks ago]. Any updates I should know?" |
| **First meeting with known company** | Company in DB but person not in Network | "First meeting with someone from [Company]. What's the context?" |
| **Post-meeting gap** | Meeting happened, no Granola transcript | "How did the meeting with [Person] go? Key takeaways?" |
| **Recurring meeting, stale context** | Recurring event, last Granola transcript > 2 weeks old | "Weekly with [Person] -- anything different this time?" |

---

## Part 4: WebFront UI Concept

### 4.1 Design Philosophy

The context capture UI should feel like **talking to Cindy**, not filling out a form. Chat-like UX with structured data extraction underneath.

**Key principle from CONTEXT.md:** "Aakash lives on WhatsApp and mobile." The UI must be:
- Mobile-first (touch targets 44x44px+)
- Quick to respond to (one-tap common responses, voice-to-text friendly)
- Non-blocking (can dismiss and return later)

### 4.2 WebFront Location

New section on digest.wiki: `/meetings` or integrated into the existing action triage flow.

**Option A: Dedicated meetings page** -- `/meetings` shows upcoming calendar with gap indicators
**Option B: Integrated into actions** -- Context gap cards appear in the Actions feed alongside content-derived actions

**Recommendation:** Option B (integrated). Context gaps ARE actions -- they're "things Cindy needs from Aakash." They use the same accept/dismiss/snooze UX. This avoids creating a separate surface Aakash has to check.

### 4.3 Context Gap Card Design

```
┌────────────────────────────────────────────┐
│ 🔍 CONTEXT GAP                    Tomorrow │
│                                    2:30 PM │
│                                             │
│ Meeting with Jane Doe                       │
│ XYZ Corp · Board Review                    │
│                                             │
│ I don't have notes from your last           │
│ interaction. What should I know?            │
│                                             │
│ ┌──────────────────────────────────────┐   │
│ │ Type a quick note or key points...   │   │
│ └──────────────────────────────────────┘   │
│                                             │
│ Quick responses:                            │
│ [Routine check-in] [Follow-up on deal]     │
│ [First meeting] [Skip - I'll handle it]    │
│                                             │
│ ── or share structured context ──          │
│ [+ Add context details]                     │
└────────────────────────────────────────────┘
```

### 4.4 Structured Context Capture (Expandable)

When user taps "+ Add context details":

```
┌────────────────────────────────────────────┐
│ Context for: Jane Doe · Board Review       │
│                                             │
│ What's this meeting about?                 │
│ ┌──────────────────────────────────────┐   │
│ │ Quarterly board review, discussing... │   │
│ └──────────────────────────────────────┘   │
│                                             │
│ Key topics to cover:                        │
│ ┌──────────────────────────────────────┐   │
│ │ + Add topic                          │   │
│ │ · Series B timeline                  │   │
│ │ · Q1 revenue numbers                 │   │
│ └──────────────────────────────────────┘   │
│                                             │
│ Any asks or follow-ups from last time?     │
│ ┌──────────────────────────────────────┐   │
│ │ They were going to send updated cap  │   │
│ │ table by end of February...          │   │
│ └──────────────────────────────────────┘   │
│                                             │
│ [Save context]  [Skip for now]              │
└────────────────────────────────────────────┘
```

### 4.5 Post-Meeting Context Capture

When Granola doesn't have a transcript (meeting not recorded):

```
┌────────────────────────────────────────────┐
│ 📝 MEETING NOTES NEEDED            2h ago │
│                                             │
│ Meeting with Jane Doe ended at 3:30 PM     │
│ No transcript found in Granola.            │
│                                             │
│ How did it go?                             │
│ ┌──────────────────────────────────────┐   │
│ │ Quick notes or voice memo...         │   │
│ └──────────────────────────────────────┘   │
│                                             │
│ Quick tags:                                 │
│ [Went well ✓] [Needs follow-up]            │
│ [No-show] [Rescheduled]                    │
│                                             │
│ Any action items?                           │
│ ┌──────────────────────────────────────┐   │
│ │ + Add action item                    │   │
│ └──────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

### 4.6 Implementation in WebFront Stack

The WebFront is Next.js 16 on Vercel with Supabase (Neon Postgres). Context gap cards would:

1. **Data source:** New Supabase table `meeting_context_gaps` written by Cindy's agent on the droplet
2. **Frontend:** New component `ContextGapCard.tsx` (similar pattern to existing `ActionCard.tsx`)
3. **Server action:** `submitContext()` in `src/lib/actions/meetings.ts` writes response back to Supabase
4. **Real-time:** Supabase Realtime subscription for new gaps appearing (like planned action realtime)
5. **Agent reads response:** Cindy polls `meeting_context_gaps` for `status: 'responded'` entries, incorporates into meeting prep

### 4.7 Data Model

```sql
CREATE TABLE meeting_context_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_event_id TEXT NOT NULL,          -- Google Calendar / M365 event ID
    meeting_title TEXT,
    meeting_start TIMESTAMPTZ,
    meeting_end TIMESTAMPTZ,
    attendees JSONB,                          -- [{email, name, role}]
    gap_type TEXT NOT NULL,                   -- 'complete_blank', 'no_recent_context', etc.
    context_richness_score FLOAT,
    granola_match_id UUID,                    -- matched Granola meeting ID if any
    status TEXT DEFAULT 'pending',            -- pending, responded, dismissed, expired
    cindy_prompt TEXT,                        -- what Cindy asked
    user_response TEXT,                       -- Aakash's free-text response
    structured_context JSONB,                 -- parsed topics, action items, etc.
    quick_tags TEXT[],                        -- ['routine', 'follow_up', etc.]
    created_at TIMESTAMPTZ DEFAULT NOW(),
    responded_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ                   -- auto-expire after meeting + 24h
);

CREATE INDEX idx_context_gaps_status ON meeting_context_gaps(status);
CREATE INDEX idx_context_gaps_meeting_start ON meeting_context_gaps(meeting_start);
```

---

## Part 5: Recommended Integration Pattern

### 5.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ CALENDAR AWARENESS LAYER (Cindy on Droplet)                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Google Calendar API ──→ Calendar Sync Module                │
│  (poll every 5 min)      │                                   │
│                           ├─→ Meeting Store (Supabase)       │
│  AgentMail .ics ─────────┤                                   │
│  (push via webhook)       ├─→ Gap Detection Engine           │
│                           │   │                              │
│  Granola MCP ────────────┤   ├─→ meeting_context_gaps table  │
│  (query after meetings)   │   │                              │
│                           │   └─→ WebFront notification      │
│  Gmail MCP ──────────────┘                                   │
│  (supplementary search)        │                             │
│                                v                              │
│                     ┌──────────────────┐                     │
│                     │ Meeting Prep Gen │                     │
│                     │ (pre-meeting)    │                     │
│                     └──────────────────┘                     │
│                                │                              │
│                     ┌──────────────────┐                     │
│                     │ Signal Extraction│                     │
│                     │ (post-meeting)   │                     │
│                     └──────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                     │                    │
                     v                    v
              WebFront (digest.wiki)   Actions Queue
              context gap cards        follow-ups, commitments
```

### 5.2 Phased Implementation

#### Phase 1: Calendar Awareness (Week 1)

- Set up Google Calendar API OAuth flow (or MS Graph if M365 is primary)
- Implement syncToken-based polling (every 5 min cron on droplet)
- Store normalized calendar events in Supabase `calendar_events` table
- Parse attendees, extract emails, cross-reference with Network DB

**Deliverable:** Cindy knows about all upcoming meetings.

#### Phase 2: Granola Matching (Week 1-2)

- After each meeting ends (+5 min buffer), query `list_meetings` for matches
- Implement time + attendee matching algorithm
- Store Granola match ID alongside calendar event
- Test with 1 week of real meetings

**Deliverable:** Calendar events are linked to Granola transcripts.

#### Phase 3: Gap Detection + WebFront (Week 2-3)

- Implement context richness scoring
- Create `meeting_context_gaps` table
- Build `ContextGapCard` component on WebFront
- Build `submitContext()` server action
- Wire gap detection engine to run after each calendar sync

**Deliverable:** Cindy proactively asks about low-context meetings.

#### Phase 4: Post-Meeting Pipeline (Week 3-4)

- After Granola transcript is available, trigger signal extraction (from prior Granola research Phase 2)
- Generate IDS signals, commitments, entity matches
- Route to Actions Queue with source relation
- If no transcript after 30 min, create post-meeting context gap card

**Deliverable:** Meetings automatically generate actions and update conviction.

#### Phase 5: Meeting Prep Briefs (Week 4+)

- Before each meeting (e.g., 30 min prior), generate prep brief from:
  - Network DB person history + IDS state
  - Recent Granola transcripts with same person
  - Email thread context
  - Thesis connections (Companies DB + Thesis Tracker)
  - Any user-submitted context from gap cards
- Deliver via WebFront notification or WhatsApp (future)

**Deliverable:** Cindy prepares Aakash for every meeting.

### 5.3 Dependencies and Blockers

| Item | Status | Blocker |
|------|--------|---------|
| AgentMail inbox for Cindy | Planned (from email research) | Custom domain DNS setup |
| Google Calendar API credentials | **Needed** | OAuth setup, confirm Google vs M365 |
| Granola MCP tools | Connected and working | None |
| Gmail MCP tools | Connected and working | None |
| Supabase (Neon) access | Working (WebFront uses it) | None |
| WebFront action cards | Working pattern (ActionCard.tsx) | None |
| Network DB in Supabase | Working (`network_master` table) | None |

### 5.4 Open Questions

1. **Is Aakash's primary calendar Google or M365?** CONTEXT.md says "M365 (work email + calendar)" but also references Google Calendar MCP. Need to confirm which holds the authoritative meeting schedule.

2. **AgentMail .ics MIME handling:** Does AgentMail expose raw MIME parts, or only parsed text/HTML? Calendar invites may arrive as `text/calendar` MIME parts that aren't standard "attachments." Need to test.

3. **Cindy's agent architecture:** Is Cindy a new persistent ClaudeSDKClient on the droplet (alongside ContentAgent), or a module within the existing Orchestrator? This affects where the calendar sync loop runs.

4. **WhatsApp integration timeline:** WhatsApp is Aakash's primary comms channel. The gap detection algorithm has a 0.15 weight for WhatsApp context but currently scores it as 0. When WhatsApp becomes available, this significantly improves gap detection accuracy.

5. **Granola attendee emails via MCP:** The MCP `get_meetings` tool returns attendees, but does it include email addresses or only display names? The Enterprise API confirms emails are in the `calendar_event.invitees` field, but the MCP tool may return a subset. Need to test with a real meeting.

---

## Sources

### Calendar Integration
- [Google Calendar API Events Reference](https://developers.google.com/workspace/calendar/api/v3/reference/events)
- [Google Calendar Push Notifications](https://developers.google.com/workspace/calendar/api/guides/push)
- [RFC 5545: iCalendar Specification](https://www.rfc-editor.org/rfc/rfc5545)
- [RFC 5546: iTIP (iCalendar Transport-Independent Interoperability Protocol)](https://datatracker.ietf.org/doc/rfc5546/)
- [Python icalendar library docs](https://icalendar.readthedocs.io/en/latest/)
- [icalendar on PyPI](https://pypi.org/project/icalendar/)
- [Working with IMAP and iCalendar (Doug Hellmann)](https://doughellmann.com/posts/working-with-imap-and-icalendar/)
- [Google CalDAV API vs Google Calendar API comparison](https://www.tutorialpedia.org/blog/difference-between-google-caldav-api-and-google-calendar-api/)

### Granola Integration
- [Granola MCP Announcement](https://www.granola.ai/blog/granola-mcp)
- [Granola Enterprise API Documentation](https://docs.granola.ai/help-center/sharing/integrations/enterprise-api)
- [Granola API Introduction](https://docs.granola.ai/introduction)
- [Reverse-Engineered Granola API (GitHub)](https://github.com/getprobo/reverse-engineering-granola-api)
- [granola-cli: Meeting Notes in Your Terminal](https://magarcia.io/reverse-engineered-meeting-notes-into-terminal/)
- [Prior AI CoS Research: Granola Meeting Integration (2026-03-04)](../archives/old-research/granola-meeting-integration-research.md)

### WebFront / Infrastructure
- [Cindy Email Infrastructure Research (2026-03-20)](./2026-03-20-cindy-email-infrastructure.md)
- [WebFront Architecture Decisions (2026-03-18)](../superpowers/brainstorms/2026-03-18-webfront-architecture-decisions.md)
- [Megamind Design Spec (2026-03-20)](../superpowers/specs/2026-03-20-megamind-design.md)
