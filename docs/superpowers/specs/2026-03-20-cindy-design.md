# Cindy — Communications Agent Design Specification
*Created: 2026-03-20*

Cindy is the communications observation agent for the AI CoS system. She watches Aakash's interactions across four surfaces — Email, WhatsApp, Granola, and Calendar — and ensures no interaction intelligence is lost. She observes, links people to the Network DB, extracts actionable signals, detects context gaps, and feeds intelligence to the rest of the agent fleet.

---

## 1. Architecture Overview

### Where Cindy Sits

```
OBSERVATION LAYER (4 Communication Surfaces)
  Email (CC/forward to cindy@3niac.com)
  WhatsApp (daily iCloud backup parse)
  Granola (meeting transcripts via MCP)
  Calendar (invites via email .ics)
                 | raw interaction signals
                 v
INTELLIGENCE LAYER
  Orchestrator → Cindy Agent (via @tool bridge)
                 Cindy Agent:
                   1. Parse interaction from any surface
                   2. Extract participants, topics, signals
                   3. Link people to Network DB (cross-surface identity resolution)
                   4. Detect context gaps (meetings without coverage)
                   5. Extract action items, thesis signals, relationship signals
                   6. Feed downstream agents
                 |
                 v
STATE LAYER
  Postgres: interactions (canonical interaction records)
  Postgres: context_gaps (meetings needing coverage)
  Postgres: people_interactions (per-person activity index)
                 |
                 v
DOWNSTREAM AGENTS
  Datum Agent  → new/updated people → Network DB
  ENIAC        → action items → Actions Queue
  Megamind     → strategic signals → Strategic Assessments
                 |
                 v
INTERFACE LAYER
  WebFront (/comms): Interaction Feed, People Activity, Context Gaps, Stats
  CAI: "You have 3 context gaps for tomorrow's meetings"
```

### Relationship to Existing Agents

| Agent | Role | Cindy's Relationship |
|-------|------|---------------------|
| **Orchestrator** | Lifecycle manager, heartbeat-driven routing | Routes `cindy_*` inbox messages to Cindy via @tool bridge. Triggers daily WhatsApp extraction and gap detection scans. |
| **Content Agent** | Content analysis, thesis updates | Cindy feeds thesis signals FROM interactions. Content Agent feeds thesis signals FROM content. Both write to `cai_inbox` for Orchestrator routing — no direct agent-to-agent calls. |
| **Datum Agent** | Entity ingestion, enrichment, dedup | Cindy identifies people across surfaces. New/unlinked people go to Datum Agent via `datum_person` or `datum_entity` inbox messages for dedup + enrichment. |
| **Megamind** | Strategic reasoning, depth grading | Cindy surfaces high-signal interactions (thesis-relevant meetings, conviction-changing email threads) as strategic signals to Megamind via `strategy_*` inbox messages. |
| **ENIAC** | Scoring | Action items Cindy extracts get scored by ENIAC's model before entering Actions Queue. |

### Key Design Principles

1. **Observe, Don't Initiate.** Cindy watches interactions but never sends emails, WhatsApp messages, or calendar invites on Aakash's behalf. She is a sensor, not an actuator.

2. **Cross-Surface Identity Resolution.** The same person appears in email (by address), WhatsApp (by phone), Granola (by attendee name), and Calendar (by invite). Cindy's core intelligence is linking these into a unified interaction history per person.

3. **Context Gap Detection Is Proactive.** For every calendar meeting, Cindy checks: do we have a Granola transcript? An email thread with these attendees? A WhatsApp conversation? If all sources are silent, Cindy asks Aakash for structured input.

4. **Append-Only Interaction Log.** Every observed interaction creates a record. Records are never deleted or modified — only enriched with links and extracted signals.

---

## 2. Four Observation Surfaces

### 2.1 Email

**Mechanism:** Cindy has her own email address: `cindy@agent.aicos.ai` (subdomain to avoid MX conflicts with existing domain email). Powered by **AgentMail** ($20/month Developer tier) — a purpose-built email provider for AI agents. Aakash CCs or forwards relevant emails. AgentMail pushes events to a WebSocket listener on the droplet (no public webhook endpoint needed).

**Provider:** AgentMail (YC-backed, $6M seed, launched March 2026)
- Python SDK: `pip install agentmail`
- WebSocket real-time events (pure outbound connection — no firewall changes)
- Native thread management (auto-threaded conversations)
- Reply text extraction via `extracted_text` / `extracted_html` (strips quoted history automatically using Talon)
- Custom domain support (DNS: SPF + DKIM + MX)
- Cost: $20/month (Developer tier, 10 inboxes, 10K emails/month)

**Ingestion Flow:**

```
Aakash CCs cindy@agent.aicos.ai on email
    |
    v
AgentMail Cloud receives email, parses, auto-threads
    |
    v
WebSocket event (message.received) → droplet listener (/opt/agents/cindy/)
    |
    v
Listener writes to cai_inbox:
    {
      type: "cindy_email",
      content: "New email from AgentMail inbox",
      metadata: {
        from: "rahul@composio.dev",
        to: ["ak@z47.com"],
        cc: ["cindy@agent.aicos.ai", "sneha@z47.com"],
        subject: "Re: Series A follow-up",
        thread_id: "thd_abc123",
        extracted_text: "...",   // reply only, no quoted history
        full_text: "...",        // full email including quotes
        html: "...",
        attachments: [{id: "att_123", name: "deck.pdf", size: 1024000, content_type: "application/pdf"}],
        message_id: "<msg_id@agentmail.to>",
        in_reply_to: "<parent_msg_id@agentmail.to>",
        received_at: "2026-03-20T10:30:00Z"
      }
    }
    |
    v
Orchestrator heartbeat picks up → routes to Cindy Agent
```

**Processing Pipeline:**

1. **Parse**: Extract sender, recipients, CC list, subject, body, thread_id, attachments, timestamps
2. **Thread tracking**: AgentMail provides native `thread_id`. If it matches an existing interaction, update it (append to thread). Otherwise, create new interaction record. Use `extracted_text` (not `full_text`) for signal extraction — this is the reply content only with quoted history stripped.
3. **Extract people**: Every email address in from/to/cc → attempt match to Network DB by email field
4. **Unmatched people**: For unmatched emails, extract name from AgentMail's parsed `from` field (AgentMail parses display names from headers) → create `datum_person` inbox message for Datum Agent
5. **Extract signals**: Action items ("Let's schedule...", "Can you send..."), thesis-relevant discussion, company mentions, deal-related language, follow-up commitments
6. **Attachment awareness**: Log attachment names/types. Flag decks, term sheets, financial docs as high-signal.
7. **Store**: Write to `interactions` table with source='email'
8. **Feed downstream**: High-signal threads → write `cindy_signal` to cai_inbox for Megamind. Action items → write to `actions_queue` with source='Cindy-Email'.

**Email-Specific Intelligence:**

| Signal | Detection | Downstream |
|--------|-----------|-----------|
| Meeting request | "Can we meet...", "Let's schedule..." | Calendar linking, context enrichment |
| Deal signal | "term sheet", "valuation", "follow-on", "runway" | Megamind strategic signal |
| Intro request | "I'd like to introduce you to..." | Datum Agent (new person) + ENIAC (action scoring) |
| Follow-up commitment | "I'll send...", "Will circle back..." | Actions Queue (Aakash or Agent) |
| Portfolio update | Email from portfolio founder | Flag for thesis/portfolio linking |
| Calendar invite (.ics) | `text/calendar` MIME part detected | Parse via `icalendar` library, create calendar interaction |

**AgentMail Integration Details:**

- **WebSocket listener**: A persistent async listener runs alongside Cindy on the droplet, subscribed to `message.received` events for Cindy's inbox. No public HTTP endpoint needed.
- **Thread management**: AgentMail auto-threads conversations. `thread_id` groups related messages. Use `client.inboxes.threads.get()` for full thread context.
- **Reply extraction**: Use `extracted_text` (not `full_text`) for signal extraction — AgentMail strips quoted history using the Talon library, so Cindy sees only what the sender actually wrote.
- **Attachments**: Download via `client.inboxes.messages.get_attachment()`. Log metadata (name, type, size) in interaction record. Download deck/term sheet attachments only when flagged as high-signal.
- **Labels**: Tag processed emails as `processed`, `action-required`, `thesis-signal` via AgentMail Labels API for debugging and audit.
- **Calendar invites**: Detect `text/calendar` MIME parts in attachments. Parse with Python `icalendar` library (RFC 5545 compliant). Extract UID, attendees, time, title, location.
- **Semantic search**: AgentMail provides org-wide semantic search for finding relevant past conversations.

### 2.2 WhatsApp

**Mechanism:** Daily iCloud backup extraction. Aakash's iPhone backs up WhatsApp to iCloud Drive daily at 2:00 AM IST. A daily cron job on the Mac (3:00 AM IST, after backup completes) downloads the backup via `brctl`, decrypts `ChatStorage.sqlite`, parses new conversations, and sends structured data to the droplet.

**Backup location:** `~/Library/Mobile Documents/57T9237FN3~net~whatsapp~WhatsApp/Accounts/[phone]/backup/`

**Key files:** `ChatStorage.sqlite.enc` (encrypted SQLite database of all messages), `Media.tar` / `Video.tar` (media archives — metadata only, not extracted).

**Prerequisite:** WhatsApp E2E backup encryption must be **disabled** (default for many users). If enabled, the backup is encrypted with a user-chosen password and programmatic extraction becomes significantly harder.

**Parsing tool:** WhatsApp-Chat-Exporter (`pip install whatsapp-chat-exporter`) — production-ready parser supporting iOS encrypted backups, message extraction, reactions, replies, and call history. MIT license, actively maintained.

**Database schema:** ChatStorage.sqlite uses Core Data (Apple's ORM) with Apple Core Foundation timestamps (seconds since 2001-01-01, NOT Unix epoch). Key tables:
- `ZWACHATSESSION` — conversations (private, group, broadcast, status)
- `ZWAMESSAGE` — messages (~34 columns: text, sender JID, timestamp, type, reply chain via `ZPARENTMESSAGE`)
- `ZWAMEDIAITEM` — media metadata (file path, size, duration, type)
- `ZWAPROFILEPUSHNAME` — display names
- JID format: `919999999999@s.whatsapp.net` (individual), `120363025555555555@g.us` (group)

**ToS risk:** LOW. This is accessing your own iCloud data on your own Mac. No third-party API abuse, no WhatsApp server protocol violation.

**Ingestion Flow:**

```
iPhone → iCloud Drive backup (daily 2:00 AM IST, automatic)
    |
    v
Mac cron job (daily 3:00 AM IST):
  1. brctl download ChatStorage.sqlite.enc from iCloud Drive
  2. Decrypt to ChatStorage.sqlite (if standard iCloud encryption only)
  3. Open SQLite, query ZWAMESSAGE + ZWACHATSESSION since last_extraction_timestamp
     - Convert Apple CF timestamps: datetime(2001,1,1) + timedelta(seconds=cf_time)
     - Filter by ZMESSAGEDATE > last_extraction
  4. Group messages by ZCHATSESSION (conversation)
  5. For each conversation, extract:
     - Chat type (ZSESSIONTYPE: 0=1:1, 1=group)
     - Participant JIDs → strip @s.whatsapp.net → phone numbers
     - Messages: text, sender JID, timestamp, type, reply context (ZPARENTMESSAGE)
     - Media: metadata only (type, filename, size) — NOT the actual files
  6. POST structured batch to droplet endpoint (or write directly to Supabase):
    {
      type: "cindy_whatsapp",
      content: "WhatsApp batch: 47 new messages across 12 conversations",
      metadata: {
        extraction_timestamp: "2026-03-20T03:15:00+05:30",
        conversations: [
          {
            chat_jid: "919999999999@s.whatsapp.net",
            chat_name: "Rahul Sharma",
            session_type: 0,  // 0=private, 1=group
            participants: ["+919999999999"],
            messages: [
              {
                sender_jid: "919999999999@s.whatsapp.net",
                is_from_me: false,
                text: "Great meeting today. Let's sync on the Series A terms next week.",
                timestamp: "2026-03-19T18:45:00+05:30",
                message_type: 0,  // 0=text, 1=image, 2=video, 3=voice, 7=document
                media_meta: null,  // {type: "document", filename: "deck.pdf", size: 1024000} if media
                reply_to_stanza_id: null  // for reply chain reconstruction
              },
              ...
            ]
          },
          ...
        ]
      }
    }
    |
    v
Orchestrator heartbeat picks up → routes to Cindy Agent
```

**Processing Pipeline:**

1. **Parse batch**: Iterate over conversations since last extraction
2. **Match participants**: JID → strip `@s.whatsapp.net` → phone number → Network DB match (phone field). For group chats, query all participant JIDs from ZWACHATSESSION. Cross-reference with `ZWAPROFILEPUSHNAME` for display names.
3. **Unmatched participants**: Phone number + push name (from WhatsApp's display name system) → `datum_person` inbox message for Datum Agent. Include phone in standard international format.
4. **Conversation classification**: Classify each conversation:
   - **Deal-related**: Mentions companies, valuations, terms
   - **Portfolio update**: Message from/about portfolio founder
   - **Thesis-relevant**: Discusses industry trends, technologies, market signals
   - **Operational**: Scheduling, logistics, admin
   - **Social**: Personal, low-signal
5. **Extract signals**: Same signal types as email (action items, thesis signals, deal signals) but adapted for conversational format
6. **Group chat intelligence**: Z47 team chats and DeVC group chats contain high-density signals. Flag cross-references between group discussions and upcoming meetings.
7. **Store**: Write to `interactions` table with source='whatsapp'
8. **Feed downstream**: Same routing as email signals

**WhatsApp-Specific Intelligence:**

| Signal | Detection | Downstream |
|--------|-----------|-----------|
| Forwarded content | WhatsApp forward metadata | Content Agent (if URL/article) |
| Voice note | `media_type: "audio"` | Log existence, flag for manual review |
| Document share | `media_type: "document"` | Log filename, flag if deck/terms |
| Group consensus | Multiple people agreeing on a point | Thesis signal (stronger than 1:1) |
| Meeting debrief | Discussion about a meeting that just happened | Link to Calendar event, fill context gap |

**Privacy Constraints:**

- Cindy processes WhatsApp messages for signal extraction only. Raw message text is NOT stored in the interactions table — only structured summaries, extracted signals, and participant links.
- Group chat messages from other participants (not Aakash) are summarized at the conversation level, not stored individually.
- Media files (images, documents, voice notes) are logged by type and filename only. The actual files are not extracted or stored.

**Incremental Extraction:** The Mac cron script stores `last_extraction_timestamp` (Apple CF format) in a local state file. Each run queries `WHERE ZMESSAGEDATE > last_extraction_timestamp`. This ensures only new messages since the last run are processed, regardless of backup frequency.

**Reply Chain Reconstruction:** `ZWAMESSAGE.ZPARENTMESSAGE` is a foreign key to the parent message, enabling reply thread reconstruction. Cindy uses this to understand conversation flow and identify responses to specific questions.

**Contact Resolution Path:** JID → phone number → Network DB phone field match → if no match, try `ZWAPROFILEPUSHNAME` display name → Network DB person_name fuzzy match → if still no match, create `datum_person` inbox message.

### 2.3 Granola (Meeting Transcripts)

**Mechanism:** Granola MCP is connected to Claude.ai with 4 verified tools: `list_meetings`, `get_meetings`, `get_meeting_transcript`, and `query_granola_meetings`. Orchestrator polls every 30 minutes using `list_meetings`. Transcripts are available 2-5 minutes after meeting ends.

**Ingestion Flow:**

```
Meeting happens → Granola records + transcribes
    |
    v
Two ingestion paths:

Path A — Orchestrator scheduled poll (every 30 min):
  1. Query Granola MCP: list_meetings(time_range="this_week")
     - Returns meeting titles + metadata (no transcripts at this stage)
  2. For each meeting not already tracked:
     - Get details: get_meetings(meeting_ids=[meeting_id])
       → Returns: attendees, AI summary, private notes, ProseMirror content
     - Get transcript: get_meeting_transcript(meeting_id)
       → Returns: utterance array [{source, text, start_timestamp, end_timestamp, confidence}]
       → source: "microphone" = Aakash, "system" = others (no multi-speaker diarization)
       → Returns 404 if no recording — retry with backoff (5 min, 10 min, 20 min)
     - Write to cai_inbox:
       {
         type: "cindy_meeting",
         content: "New Granola transcript available",
         metadata: {
           meeting_id: "granola_abc123",
           title: "Series A Discussion — Composio",
           start_time: "2026-03-20T10:00:00Z",
           end_time: "2026-03-20T10:45:00Z",
           attendees: ["Aakash Kumar", "Rahul Sharma", "Sarah Lee"],
           ai_summary: "Discussed Series A terms...",
           transcript_utterances: [{source: "microphone", text: "...", start_timestamp: "..."}],
           action_items: ["Follow up on term sheet", "Schedule BRC"],
           private_notes: "..."
         }
       }

Path B — CAI relay (Aakash triggers from Claude mobile):
  "Process my meeting with Rahul about Composio"
  → cai_inbox type: "cindy_meeting" with meeting reference
```

**Processing Pipeline:**

1. **Parse transcript**: Extract full text, identify speakers (if speaker diarization available), timestamps
2. **Extract attendees**: From Granola attendee list → match to Network DB by name. Cross-reference with Calendar invite for email-based matching.
3. **Unmatched attendees**: Name + meeting context → `datum_person` inbox message for Datum Agent
4. **Transcript analysis**: Apply IDS methodology lens:
   - **Thesis signals**: What investment themes were discussed?
   - **Conviction signals**: Did anything move conviction up/down?
   - **Key questions**: Were any open key questions addressed?
   - **Action items**: Explicit commitments, next steps, follow-ups
   - **Relationship signals**: Warmth, engagement level, rapport indicators
5. **Calendar linking**: Match to Calendar event using multi-signal scoring (time overlap 50% weight + attendee match 30% + title similarity 20%). Threshold: 0.5+ = confident match. Time overlap alone is insufficient for back-to-back meetings (Aakash has 7-8/day).
6. **Context gap fill**: If this meeting had an open context_gap record, mark it as filled
7. **Store**: Write to `interactions` table with source='granola'
8. **Feed downstream**:
   - Action items → `actions_queue` with source='Cindy-Meeting'
   - Thesis signals → `cindy_signal` to cai_inbox for Megamind
   - Entity references → `datum_entity` batch to cai_inbox for Datum Agent
   - Key question answers → Content Agent territory (thesis evidence updates)

**Granola-Specific Intelligence:**

| Signal | Detection | Downstream |
|--------|-----------|-----------|
| Founder pitch | Meeting with founder, company discussion | Companies DB linkage, thesis matching |
| Portfolio review | Meeting with portfolio company | Portfolio DB linkage, IDS update signal |
| BRC discussion | Board/review committee language | High-priority flag, P0 action items |
| Intro received | "Let me introduce you to..." in transcript | Datum Agent (new person), action item |
| Competitive intel | Competitor mentions, market positioning | Thesis signal, Content Agent research trigger |

**Granola Tool Reference:**
- `list_meetings(time_range)`: Discovery. Fixed ranges: `this_week`, `last_week`, `last_30_days`. Returns titles + metadata.
- `get_meetings(meeting_ids)`: Details. Max 10 IDs. Returns attendees, AI summary, private notes.
- `get_meeting_transcript(meeting_id)`: Full transcript. Utterance array with speaker + timestamps. 404 if no recording.
- `query_granola_meetings(query)`: Semantic search across all meetings. Returns AI response with citation links.

**Speaker Diarization:** `source: "microphone"` = Aakash (recorded locally), `source: "system"` = other participants (from meeting audio). No multi-speaker diarization for remote participants on desktop.

**Transcript Availability:** 2-5 minutes post-meeting. Allow 5+ minute buffer before querying. Retry with exponential backoff if 404.

**Granola Action Items vs Cindy's:** Use Granola's AI-generated action items as a starting point, but Cindy should also extract from the raw transcript — Granola may miss IDS-specific signals (conviction, thesis, key questions) that require domain context.

### 2.4 Calendar

**Mechanism:** Calendar events reach Cindy through three paths: (1) Google Calendar API (or MS Graph API) polling with syncToken for incremental sync every 5 minutes, (2) .ics attachments in emails forwarded/CC'd to cindy@agent.aicos.ai (parsed via `icalendar` library), and (3) Calendar MCP if available. Calendar is the anchor surface — it defines what meetings ARE happening, and Cindy checks whether the other surfaces (Granola, Email, WhatsApp) have provided context.

**Open question:** CONTEXT.md says "M365 (work email + calendar)" for Aakash's work tools, but Google Calendar MCP is referenced as connected. Need to confirm which is the authoritative meeting calendar — the API pattern is nearly identical (Google Calendar API vs Microsoft Graph), only auth and endpoints differ.

**Ingestion Flow:**

```
Path A — .ics in email:
  Email webhook delivers email with .ics attachment
  → Parsed alongside regular email processing
  → Calendar event extracted and stored

Path B — Calendar API incremental sync (every 5 min via Orchestrator):
  1. Poll Google Calendar API (or MS Graph) with stored syncToken
     - Initial sync: events.list(calendarId='primary', timeMin=now-7d, singleEvents=true)
     - Incremental: events.list(syncToken=stored_token) → returns only changes
     - Detects: new events, updated events (sequence increment), cancelled events
  2. For each new/updated event:
     {
       type: "cindy_calendar",
       content: "New calendar event detected",
       metadata: {
         event_id: "gcal_abc123",
         ical_uid: "uid@google.com",  // For cross-referencing with .ics from email
         title: "Composio Series A Discussion",
         start_time: "2026-03-21T10:00:00Z",
         end_time: "2026-03-21T10:45:00Z",
         attendees: [
           {email: "rahul@composio.dev", name: "Rahul Sharma", response: "accepted"},
           {email: "sarah@composio.dev", name: "Sarah Lee", response: "tentative"}
         ],
         location: "Google Meet / Zoom / In-person",
         description: "Discussion about Series A terms...",
         organizer: "sneha@z47.com",
         conference_uri: "https://meet.google.com/abc-def-ghi",
         sequence: 0,  // 0=new, >0=updated
         status: "confirmed"  // confirmed | cancelled
       }
     }
```

**Processing Pipeline:**

1. **Parse event**: Title, time, attendees (name + email), location, description, organizer
2. **Attendee resolution**: Email addresses → Network DB match. Names → fuzzy match. For unmatched: `datum_person` inbox message.
3. **Pre-meeting context assembly** (for upcoming events):
   - Query `interactions` for recent interactions with each attendee (last 30 days)
   - Query `thesis_threads` for connected thesis threads (by company/person)
   - Query `actions_queue` for open actions related to attendees
   - Assemble pre-meeting brief (stored as `context_assembly` in interactions record)
4. **Post-meeting gap detection** (for past events):
   - Check `interactions` for Granola transcript matching this time window
   - Check `interactions` for email threads with these attendees in the last 48h
   - Check `interactions` for WhatsApp conversations with these attendees in the last 48h
   - If ALL sources empty → create `context_gaps` record
5. **Store**: Write to `interactions` table with source='calendar'
6. **Feed downstream**: Context gaps surface on WebFront. Pre-meeting briefs surface to CAI/WhatsApp.

**Context Gap Detection Algorithm** (see Section 4 for full specification).

---

## 3. People Linking Algorithm (Cross-Surface Identity Resolution)

The core intelligence challenge: the same person appears differently across surfaces.

### Identity Signals by Surface

| Surface | Available Identifiers | Reliability |
|---------|----------------------|-------------|
| Email | Email address, display name | High (email is unique) |
| WhatsApp | Phone number, contact name | High (phone is unique) |
| Granola | Full name (from invite) | Medium (name variations) |
| Calendar | Email address, display name | High (email is unique) |

### Resolution Algorithm

```
FUNCTION resolve_person(signal: PersonSignal) -> Resolution:
    """
    Given an identifier from any surface, find or create the canonical
    person record in Network DB.

    Returns: { status: 'matched' | 'created' | 'ambiguous', person_id: int }
    """

    # Tier 1: Email match (strongest — works for Email, Calendar)
    IF signal.email IS NOT NULL:
        match = query("SELECT id, person_name FROM network WHERE email = $1", signal.email)
        IF match:
            update_interaction_link(match.id, signal)
            RETURN { status: 'matched', person_id: match.id }

    # Tier 2: Phone match (strong — works for WhatsApp)
    IF signal.phone IS NOT NULL:
        match = query("SELECT id, person_name FROM network WHERE phone = $1", signal.phone)
        IF match:
            update_interaction_link(match.id, signal)
            RETURN { status: 'matched', person_id: match.id }

    # Tier 3: LinkedIn URL match (if available from any prior enrichment)
    IF signal.linkedin IS NOT NULL:
        match = query("SELECT id, person_name FROM network WHERE linkedin = $1", signal.linkedin)
        IF match:
            update_interaction_link(match.id, signal)
            RETURN { status: 'matched', person_id: match.id }

    # Tier 4: Exact name + company match
    IF signal.name AND signal.company:
        match = query("""
            SELECT id, person_name FROM network
            WHERE LOWER(person_name) = LOWER($1)
              AND LOWER(current_role) ILIKE '%' || LOWER($2) || '%'
        """, signal.name, signal.company)
        IF match:
            update_interaction_link(match.id, signal)
            RETURN { status: 'matched', person_id: match.id }

    # Tier 5: Name-only match (lower confidence)
    IF signal.name:
        matches = query("""
            SELECT id, person_name, current_role, email, phone
            FROM network
            WHERE LOWER(person_name) = LOWER($1)
        """, signal.name)

        IF len(matches) == 1:
            # Single match — likely correct but flag for confirmation
            update_interaction_link(matches[0].id, signal, confidence=0.80)
            RETURN { status: 'matched', person_id: matches[0].id }
        ELIF len(matches) > 1:
            # Multiple matches — ambiguous, need human help
            RETURN { status: 'ambiguous', candidates: [m.id for m in matches] }

    # Tier 6: No match — delegate to Datum Agent for creation
    write_datum_inbox({
        type: "datum_person",
        content: f"New person from {signal.source}: {signal.name or signal.email or signal.phone}",
        metadata: {
            name: signal.name,
            email: signal.email,
            phone: signal.phone,
            company: signal.company,
            source: f"cindy_{signal.source}",
            context: signal.interaction_context
        }
    })
    RETURN { status: 'created', person_id: null }  # ID assigned by Datum Agent
```

### Cross-Surface Linking (Identity Stitching)

When Cindy resolves a person on one surface, she checks whether that person has identifiers from other surfaces. If not, she enriches:

```
FUNCTION cross_link_person(person_id: int, new_signal: PersonSignal):
    """
    After matching a person, check if we can fill cross-surface identifiers.
    """
    existing = query("SELECT email, phone, linkedin FROM network WHERE id = $1", person_id)

    # If we have a new email and the person has no email
    IF new_signal.email AND existing.email IS NULL:
        update_network(person_id, { email: new_signal.email })

    # If we have a new phone and the person has no phone
    IF new_signal.phone AND existing.phone IS NULL:
        update_network(person_id, { phone: new_signal.phone })

    # Log the cross-surface appearance
    INSERT INTO people_interactions (
        person_id, interaction_id, surface, identifier_used, linked_at
    ) VALUES (person_id, signal.interaction_id, signal.source, signal.identifier, NOW())
```

### Identity Confidence Levels

| Confidence | Condition | Action |
|------------|-----------|--------|
| 1.0 | Email or phone exact match | Auto-link, no review |
| 0.95 | Exact name + company match | Auto-link, note in log |
| 0.80-0.94 | Single name-only match | Auto-link, flag for confirmation (datum request) |
| 0.50-0.79 | Multiple name matches | Create datum request with candidates |
| < 0.50 | No match | Send to Datum Agent for creation |

### Learning Loop

As Aakash confirms or corrects identity links (via WebFront datum requests), the resolution algorithm improves:
- Confirmed matches → aliases added to Network DB, improving future matching
- Corrections → identity signals recalibrated (e.g., "Rahul S." in WhatsApp = "Rahul Sharma" in Calendar)
- Over time, the system builds a complete cross-surface identity map for Aakash's entire network

---

## 4. Context Gap Detection

### What Is a Context Gap

A context gap is a calendar meeting for which Cindy has no observational coverage from any other surface. It represents lost interaction intelligence — a meeting happened, but the system learned nothing from it.

### Gap Detection Algorithm

```
FUNCTION detect_context_gaps():
    """
    Run after Calendar poll. Check past 24h meetings for coverage.
    Also run when new Granola/Email/WhatsApp interactions arrive (retroactive fill).
    """

    # Get all calendar events from the past 24 hours
    recent_events = query("""
        SELECT i.id, i.source_id, i.summary, i.timestamp, i.participants,
               (i.raw_data->>'end_time')::timestamptz as end_time
        FROM interactions i
        WHERE i.source = 'calendar'
          AND i.timestamp > NOW() - INTERVAL '24 hours'
          AND i.timestamp < NOW() - INTERVAL '30 minutes'  -- Give meeting time to finish
    """)

    FOR event IN recent_events:
        # Check if we already have a context_gap for this event
        existing_gap = query("""
            SELECT id, status FROM context_gaps
            WHERE calendar_event_id = $1
        """, event.source_id)

        IF existing_gap AND existing_gap.status IN ('filled', 'skipped'):
            CONTINUE  # Already handled

        # Check coverage from other surfaces
        coverage = check_surface_coverage(event)

        IF coverage.has_granola OR coverage.has_email_thread OR coverage.has_whatsapp:
            # Meeting has coverage — no gap
            IF existing_gap:
                update_gap(existing_gap.id, status='filled', filled_sources=coverage.sources)
            CONTINUE

        IF NOT existing_gap:
            # No coverage from any surface — create context gap
            INSERT INTO context_gaps (
                calendar_event_id, meeting_title, meeting_date,
                attendees, missing_sources, status, created_at
            ) VALUES (
                event.source_id, event.summary, event.timestamp,
                event.participants, coverage.missing, 'pending', NOW()
            )

            # Write notification for CAI
            write_notification(
                type='context_gap',
                content=f"Context gap: {event.summary} ({format_time(event.timestamp)}). "
                        f"No Granola transcript, email thread, or WhatsApp discussion found. "
                        f"Fill at /comms/gaps or reply with meeting notes.",
                metadata={
                    gap_id: new_gap.id,
                    meeting_title: event.summary,
                    attendees: event.participants
                }
            )


FUNCTION check_surface_coverage(calendar_event) -> Coverage:
    """
    For a calendar event, check which other surfaces have data.
    """
    coverage = Coverage(sources=[], missing=[])
    event_start = calendar_event.timestamp
    event_end = calendar_event.end_time or (event_start + INTERVAL '1 hour')
    attendee_names = calendar_event.participants
    attendee_emails = extract_emails(calendar_event)

    # Check Granola: transcript exists in the time window
    granola = query("""
        SELECT id FROM interactions
        WHERE source = 'granola'
          AND timestamp BETWEEN $1 - INTERVAL '15 minutes' AND $2 + INTERVAL '15 minutes'
    """, event_start, event_end)

    IF granola:
        coverage.sources.append('granola')
    ELSE:
        coverage.missing.append('granola')

    # Check Email: thread with attendees in the past 48h
    email = query("""
        SELECT id FROM interactions
        WHERE source = 'email'
          AND timestamp > $1 - INTERVAL '48 hours'
          AND linked_people && (
              SELECT ARRAY_AGG(id) FROM network
              WHERE email = ANY($2)
          )
    """, event_start, attendee_emails)

    IF email:
        coverage.sources.append('email')
    ELSE:
        coverage.missing.append('email')

    # Check WhatsApp: conversation with attendees in the past 48h
    whatsapp = query("""
        SELECT id FROM interactions
        WHERE source = 'whatsapp'
          AND timestamp > $1 - INTERVAL '48 hours'
          AND linked_people && (
              SELECT ARRAY_AGG(id) FROM network
              WHERE person_name = ANY($2) OR phone = ANY($3)
          )
    """, event_start, attendee_names, extract_phones(calendar_event))

    IF whatsapp:
        coverage.sources.append('whatsapp')
    ELSE:
        coverage.missing.append('whatsapp')

    coverage.has_granola = 'granola' IN coverage.sources
    coverage.has_email_thread = 'email' IN coverage.sources
    coverage.has_whatsapp = 'whatsapp' IN coverage.sources

    RETURN coverage
```

### Context Richness Scoring (Research-Informed)

In addition to the binary surface coverage check above, Cindy computes a weighted context richness score per meeting:

```
context_richness(meeting) -> 0.0 to 1.0

Weights:
  Granola transcript:  0.35  (richest single source — full conversation)
  Email threads:       0.25  (decision context, shared docs)
  Network DB history:  0.25  (person history, IDS state, relationship context)
  WhatsApp:            0.15  (async signals — future, currently 0)

Thresholds:
  < 0.3  → Context gap (pending) — proactive request to Aakash
  0.3-0.6 → Partial context — present what we have, offer to fill gaps
  > 0.6  → Rich context — no intervention needed
```

### Gap Detection Thresholds

| Condition | Gap Status | Action |
|-----------|-----------|--------|
| Context richness < 0.3 AND event within 24h | `pending` (urgent) | Prompt Aakash immediately via notification |
| Context richness < 0.3 AND event 24-48h away | `pending` (planned) | Queue context request, give Aakash time |
| Context richness 0.3-0.6 | `partial` | Show what we have, offer to enrich |
| Context richness > 0.6 | `filled` | No gap — meeting is well-covered |
| Meeting is internal-only (Z47/DeVC team) | `auto_skip` | Skip gap detection for internal meetings |
| Meeting < 15 minutes | `auto_skip` | Skip — too short to warrant full coverage |
| Past meeting, no Granola transcript after 30 min | `post_meeting_gap` | "Meeting ended but no transcript. How did it go?" |

### Gap Resolution

Gaps are resolved in three ways:

1. **Automatic fill**: A Granola transcript, email thread, or WhatsApp conversation arrives after the gap was created. Cindy's retroactive check marks the gap as `filled`.

2. **User input via WebFront**: Aakash fills in structured meeting notes at `/comms/gaps`:
   ```
   Meeting: Composio Series A Discussion
   Date: March 20, 2026 10:00 AM
   Attendees: Rahul Sharma, Sarah Lee

   [Quick notes field]
   "Discussed Series A terms. They want $20M at $100M pre.
   Need to review with IC next week. Rahul impressive — deep
   technical background, ex-Google. Sarah handles ops."

   [Submit] [Skip]
   ```
   On submit, Cindy processes the notes through the same signal extraction pipeline.

3. **User skip**: Aakash marks the gap as `skipped` — the meeting was low-signal or doesn't warrant capture.

### Pre-Meeting Context Assembly

For upcoming meetings (next 48h), Cindy proactively assembles context:

```
FUNCTION assemble_pre_meeting_context(calendar_event) -> PreMeetingBrief:
    attendees = resolve_all_attendees(calendar_event)

    brief = PreMeetingBrief(
        meeting_title: calendar_event.summary,
        meeting_time: calendar_event.timestamp,
        attendees: []
    )

    FOR person IN attendees:
        IF person.status == 'matched':
            person_brief = {
                name: person.name,
                role: person.current_role,
                archetype: person.archetype,
                last_interaction: query_last_interaction(person.id),
                interaction_count_30d: query_interaction_count(person.id, days=30),
                open_actions: query_open_actions_for_person(person.id),
                thesis_connections: query_thesis_connections(person.id),
                notes: query_recent_interaction_summaries(person.id, limit=3)
            }
            brief.attendees.append(person_brief)
        ELSE:
            brief.attendees.append({ name: person.name, status: 'unknown' })

    # Company context (if meeting title or description mentions a company)
    company = extract_company_from_meeting(calendar_event)
    IF company:
        brief.company_context = query_company_context(company)

    RETURN brief
```

---

## 5. CLAUDE.md Draft (Cindy Agent System Prompt)

```markdown
# Cindy — AI CoS Communications Observer

You are **Cindy**, the communications observation agent for Aakash Kumar's AI Chief of Staff
system. You are a persistent, autonomous observer running on a droplet. You receive work
prompts from the Orchestrator Agent. Your purpose: watch Aakash's interactions across four
surfaces (Email, WhatsApp, Granola, Calendar), link people, extract signals, detect gaps,
and feed intelligence to the rest of the agent fleet.

---

## 1. Identity

**Who you work for:** Aakash Kumar — Managing Director at Z47 ($550M fund) AND Managing
Director at DeVC ($60M fund). His interactions are his primary signal source. Every meeting,
email, and message contains intelligence that should compound into better decisions.

**Your role:** Communications Observer. You watch, you link, you extract, you detect gaps.
You are the system's eyes on Aakash's interaction surfaces. You ensure no interaction
intelligence is lost.

**You are NOT an assistant.** You are an autonomous agent. You reason, decide, and act via
your instructions, tools, and skills. There is no human in the loop during your execution.

**You are an observer, NOT an actor.** You never send emails, WhatsApp messages, or calendar
invites on Aakash's behalf. You observe and extract intelligence from interactions that have
already happened or are scheduled to happen.

**You are persistent.** You remember interactions you've processed within this session. Use
this to avoid re-processing and to accumulate cross-surface context about people and
conversations.

**You receive work from the Orchestrator.** The Orchestrator sends you prompts when there
is communication data to process — email webhooks, WhatsApp batches, Granola transcripts,
Calendar polls. You don't run on timers. You activate on demand.

---

## 2. Capabilities

| Tool | Purpose |
|------|---------|
| **Bash** | Shell commands. `psql $DATABASE_URL` for all DB access. |
| **Read** | Read files |
| **Write** | Write files |
| **Edit** | Edit files |
| **Grep** | Search file contents |
| **Glob** | Find files by pattern |
| **Skill** | Load skill markdown files for domain knowledge |

No web tools. Cindy reasons over interaction data, not web content. If web enrichment is
needed (e.g., looking up a person), delegate to Datum Agent via datum_* inbox messages.

---

## 3. Database Access

**Method:** Bash + psql with `$DATABASE_URL`. No Python DB modules.

**Schema reference:** Load `skills/data/postgres-schema.md` for base schemas. Load
`skills/cindy/cindy-schema.md` for Cindy-specific tables.

**Tables you read/write:**

| Table | Access | Purpose |
|-------|--------|---------|
| `interactions` | Read + Write | Canonical interaction records from all 4 surfaces |
| `context_gaps` | Read + Write | Meetings needing coverage |
| `people_interactions` | Read + Write | Per-person interaction index |
| `notifications` | Write | Alerts and context gap notifications to CAI |

**Tables you read only:**

| Table | Access | Purpose |
|-------|--------|---------|
| `network` | Read | People resolution |
| `companies` | Read | Company identification in interactions |
| `thesis_threads` | Read | Thesis signal matching |
| `actions_queue` | Read | Open actions for pre-meeting context |
| `cai_inbox` | Read | Only to understand forwarded message context |

**Tables you NEVER touch:**

| Table | Why |
|-------|-----|
| `content_digests` | Content Agent territory |
| `thesis_threads` (writes) | Content Agent territory — you only read |
| `actions_queue` (writes) | You write proposed actions here, but don't modify status of existing actions |

---

## 4. Processing Flow

### For Email (type: cindy_email)

1. Parse email: sender, recipients, CC, subject, body, thread_id, attachments
2. Thread tracking: match thread_id to existing interaction or create new
3. Resolve people: every email address → Network DB match
4. Unmatched people → write datum_person to cai_inbox
5. Extract signals: action items, thesis connections, deal language, follow-ups
6. Store in interactions table (source='email')
7. High-signal threads → write cindy_signal to cai_inbox for Megamind routing
8. Action items → write to actions_queue with source='Cindy-Email'

### For WhatsApp (type: cindy_whatsapp)

1. Parse batch: iterate conversations
2. Resolve participants: phone numbers → Network DB match
3. Unmatched → write datum_person to cai_inbox
4. Classify conversations: deal/portfolio/thesis/operational/social
5. Extract signals from deal, portfolio, and thesis conversations only
6. Store in interactions table (source='whatsapp', summary only — not raw messages)
7. Feed signals downstream same as email

### For Granola (type: cindy_meeting)

1. Parse transcript: full text, speakers, timestamps, attendees
2. Resolve attendees: names → Network DB match, cross-ref with Calendar emails
3. Unmatched → write datum_person to cai_inbox
4. Apply IDS methodology: thesis signals, conviction signals, key questions, action items
5. Link to Calendar event by time window overlap
6. Fill context_gaps if this meeting had one
7. Store in interactions table (source='granola')
8. Feed signals: actions → actions_queue, thesis → cindy_signal, entities → datum_entity

### For Calendar (type: cindy_calendar)

1. Parse event: title, time, attendees, location, description
2. Resolve attendees: email → Network DB match
3. Unmatched → write datum_person to cai_inbox
4. For upcoming events: assemble pre-meeting context
5. For past events: run context gap detection
6. Store in interactions table (source='calendar')
7. Surface gaps on WebFront + notification to CAI

---

## 5. People Resolution Protocol

For every person reference, follow this sequence:

1. **Email match:** `SELECT id FROM network WHERE email = $1` → auto-link (confidence 1.0)
2. **Phone match:** `SELECT id FROM network WHERE phone = $1` → auto-link (confidence 1.0)
3. **LinkedIn match:** `SELECT id FROM network WHERE linkedin = $1` → auto-link (confidence 1.0)
4. **Exact name + company:** `WHERE LOWER(person_name) = LOWER($1) AND current_role ILIKE '%company%'` → auto-link (0.95)
5. **Name-only (single match):** → auto-link with flag (0.80)
6. **Name-only (multiple matches):** → create datum request asking user to pick
7. **No match:** → write datum_person to cai_inbox for Datum Agent

After linking, cross-populate identifiers: if the person had no email and this interaction
provides one, UPDATE the email field. Same for phone. This progressively builds the
cross-surface identity map.

---

## 6. Signal Extraction Templates

### Action Items
Look for: commitments, follow-ups, scheduled next steps, requests
Format:
```sql
INSERT INTO actions_queue (action, action_type, priority, status, assigned_to, source,
                           reasoning, thesis_connection, created_at)
VALUES ('Follow up with Rahul on Series A terms', 'Meeting/Outreach', 'P1 - This Week',
        'Proposed', 'Aakash', 'Cindy-Meeting',
        'Explicit commitment in Granola transcript: "Let''s circle back next week on terms."',
        'Agentic AI Infrastructure', NOW());
```

### Thesis Signals
Look for: industry trends, competitive moves, market data, technology shifts
Write to cai_inbox for routing:
```sql
INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
VALUES ('cindy_signal', 'Thesis signal from meeting with Composio founders',
        '{"signal": "Composio seeing 10x growth in API calls — validates Agentic AI tooling demand",
          "thesis": "Agentic AI Infrastructure",
          "source": "granola",
          "interaction_id": 123,
          "strength": "strong"}'::jsonb,
        FALSE, NOW());
```

### Relationship Signals
Track interaction frequency and temperature per person:
```sql
INSERT INTO people_interactions (person_id, interaction_id, role, surface, linked_at)
VALUES (42, 123, 'primary_contact', 'email', NOW());
```

---

## 7. Acknowledgment Protocol

Every response MUST end with a structured ACK:

```
ACK: [summary]
- [surface] [count] interactions processed
- [count] people linked, [count] new (sent to Datum)
- [count] action items extracted
- [count] thesis signals identified
- [count] context gaps: [created/filled/unchanged]
```

---

## 8. State Tracking

| File | When to Write |
|------|---------------|
| `state/cindy_last_log.txt` | After every prompt — one-line summary for Stop hook |
| `state/cindy_iteration.txt` | Incremented by Stop hook after every prompt |

### Session Compaction
When prompt includes "COMPACTION REQUIRED":
1. Read `CHECKPOINT_FORMAT.md`
2. Write checkpoint to `state/cindy_checkpoint.md`
3. End response with: **COMPACT_NOW**

### Session Restart
If `state/cindy_checkpoint.md` exists:
1. Read it, absorb state, delete it
2. Log: `resumed from checkpoint, session #N`

---

## 9. Anti-Patterns (NEVER Do These)

1. **Never send emails, messages, or calendar invites.** You are an observer, not an actor.
2. **Never store raw WhatsApp message text.** Store structured summaries only. Privacy critical.
3. **Never create duplicate interactions.** Check source + source_id before INSERT.
4. **Never skip people resolution.** Every participant must be resolved or sent to Datum.
5. **Never import Python DB modules.** Use Bash + psql exclusively.
6. **Never skip the ACK.** Every response must include structured acknowledgment.
7. **Never modify thesis_threads.** Write signals to cai_inbox for routing. Content Agent
   manages thesis evidence.
8. **Never process internal-only meetings for gap detection.** Skip Z47/DeVC internal meetings.
9. **Never auto-link people at confidence < 0.80.** Create a datum request for ambiguous matches.
10. **Never skip state tracking.** Always write cindy_last_log.txt.
11. **Never ignore COMPACTION REQUIRED.** Write checkpoint + COMPACT_NOW immediately.
12. **Never process media files.** Log media metadata (type, filename) only.
13. **Never overwrite existing interaction records.** Append new data, update linked_people.
14. **Never write to network table directly for new records.** New people go through Datum Agent.
    You MAY update cross-surface identifiers (email, phone) on existing records.
```

---

## 6. Database Schema

### New Table: interactions

The canonical record for every observed interaction across all four surfaces.

```sql
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,

    -- Source identification
    source TEXT NOT NULL,
        -- 'email' | 'whatsapp' | 'granola' | 'calendar'
    source_id TEXT NOT NULL,
        -- Unique ID from the source system (email message_id, whatsapp chat_id+timestamp,
        -- granola meeting_id, calendar event_id)
    thread_id TEXT,
        -- Groups related interactions (email thread, whatsapp conversation, calendar recurrence)

    -- Participants
    participants TEXT[] NOT NULL,
        -- Raw participant identifiers as received (email addresses, phone numbers, names)
    linked_people INTEGER[],
        -- FK references to network.id (resolved by Cindy's people resolution)
    linked_companies INTEGER[],
        -- FK references to companies.id (when company is identified in interaction)

    -- Content
    summary TEXT,
        -- Agent-generated summary of the interaction (NOT raw content for WhatsApp)
    raw_data JSONB,
        -- Full structured data from the source (email body, granola transcript, calendar details)
        -- For WhatsApp: metadata only, NOT raw message text

    -- Timing
    timestamp TIMESTAMPTZ NOT NULL,
        -- When the interaction occurred (email sent_at, meeting start_time, message timestamp)
    duration_minutes INTEGER,
        -- For meetings: duration. For email threads: NULL. For WhatsApp: NULL.

    -- Extracted intelligence
    action_items TEXT[],
        -- Extracted action items (also written to actions_queue)
    thesis_signals JSONB,
        -- Array of {thesis_thread, signal, strength, direction}
    relationship_signals JSONB,
        -- {warmth, engagement, key_topics, follow_up_needed}
    deal_signals JSONB,
        -- {company, stage, terms_mentioned, next_steps}

    -- Context assembly (for calendar events)
    context_assembly JSONB,
        -- Pre-meeting brief: attendee context, open actions, thesis connections
    context_gap_id INTEGER,
        -- FK to context_gaps.id if this interaction fills a gap

    -- Metadata
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Dedup constraint
    UNIQUE(source, source_id)
);

-- Index: recent interactions by source
CREATE INDEX idx_interactions_source_time ON interactions(source, timestamp DESC);

-- Index: interactions by person (for people activity view)
CREATE INDEX idx_interactions_people ON interactions USING gin(linked_people);

-- Index: interactions by time (for gap detection)
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp DESC);

-- Index: interactions by thread (for thread grouping)
CREATE INDEX idx_interactions_thread ON interactions(thread_id) WHERE thread_id IS NOT NULL;

-- Index: full-text search on summary
CREATE INDEX idx_interactions_summary_fts ON interactions USING gin(to_tsvector('english', summary));
```

### New Table: context_gaps

Meetings where Cindy lacks observational coverage.

```sql
CREATE TABLE context_gaps (
    id SERIAL PRIMARY KEY,

    -- Calendar event reference
    calendar_event_id TEXT NOT NULL,
        -- Source ID from the calendar surface
    calendar_interaction_id INTEGER,
        -- FK to interactions.id for the calendar record

    -- Meeting details (denormalized for quick access on WebFront)
    meeting_title TEXT NOT NULL,
    meeting_date TIMESTAMPTZ NOT NULL,
    attendees TEXT[] NOT NULL,
        -- Participant names/emails

    -- Gap analysis
    missing_sources TEXT[] NOT NULL,
        -- Which surfaces have no data: ['granola', 'email', 'whatsapp']
    available_sources TEXT[],
        -- Which surfaces DO have data

    -- Resolution
    status TEXT NOT NULL DEFAULT 'pending',
        -- 'pending' | 'partial' | 'filled' | 'skipped' | 'auto_skip'
    user_input JSONB,
        -- Structured notes from Aakash when filling manually:
        -- { notes: "...", key_takeaways: [...], action_items: [...], people_mentioned: [...] }
    filled_by TEXT,
        -- 'automatic' (retroactive source arrival) | 'webfront' | 'cai' | NULL
    filled_sources TEXT[],
        -- Which source(s) resolved the gap

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    filled_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Dedup
    UNIQUE(calendar_event_id)
);

-- Index: pending gaps for WebFront display
CREATE INDEX idx_context_gaps_pending ON context_gaps(status, meeting_date DESC)
    WHERE status IN ('pending', 'partial');

-- Index: gaps by date (for gap detection queries)
CREATE INDEX idx_context_gaps_date ON context_gaps(meeting_date DESC);
```

### New Table: people_interactions

Per-person interaction index linking people to their interactions across all surfaces.

```sql
CREATE TABLE people_interactions (
    id SERIAL PRIMARY KEY,

    -- Links
    person_id INTEGER NOT NULL,
        -- FK to network.id
    interaction_id INTEGER NOT NULL,
        -- FK to interactions.id

    -- Context
    role TEXT NOT NULL DEFAULT 'participant',
        -- 'organizer' | 'sender' | 'recipient' | 'cc' | 'participant' | 'mentioned'
    surface TEXT NOT NULL,
        -- 'email' | 'whatsapp' | 'granola' | 'calendar'
    identifier_used TEXT,
        -- Which identifier matched: 'email:rahul@composio.dev' | 'phone:+91XXXXXXXXXX' | 'name:Rahul Sharma'
    link_confidence REAL NOT NULL DEFAULT 1.0,
        -- 0.0-1.0: how confident is the person match

    -- Timestamps
    linked_at TIMESTAMPTZ DEFAULT NOW(),

    -- Dedup: one link per person per interaction
    UNIQUE(person_id, interaction_id)
);

-- Index: all interactions for a person (People Activity view)
CREATE INDEX idx_pi_person ON people_interactions(person_id, linked_at DESC);

-- Index: all people in an interaction
CREATE INDEX idx_pi_interaction ON people_interactions(interaction_id);

-- Index: interactions by surface per person
CREATE INDEX idx_pi_person_surface ON people_interactions(person_id, surface);
```

### ALTER TABLE: network (additional columns for Cindy)

```sql
-- Last interaction tracking (computed by Cindy)
ALTER TABLE network ADD COLUMN IF NOT EXISTS last_interaction_at TIMESTAMPTZ;
    -- When was the most recent interaction with this person (any surface)
ALTER TABLE network ADD COLUMN IF NOT EXISTS last_interaction_surface TEXT;
    -- Which surface: 'email' | 'whatsapp' | 'granola' | 'calendar'
ALTER TABLE network ADD COLUMN IF NOT EXISTS interaction_count_30d INTEGER DEFAULT 0;
    -- Rolling count of interactions in the last 30 days
ALTER TABLE network ADD COLUMN IF NOT EXISTS interaction_surfaces TEXT[];
    -- Which surfaces this person has appeared on: ['email', 'whatsapp', 'granola']
```

### Auto Embeddings

The `interactions` table gets an embedding column for semantic search:

```sql
ALTER TABLE interactions ADD COLUMN IF NOT EXISTS embedding vector(1024);
ALTER TABLE interactions ADD COLUMN IF NOT EXISTS embedding_input TEXT;
    -- Format: "{summary} | {participants} | {source}"
```

Supabase Auto Embeddings trigger on INSERT/UPDATE of `embedding_input`. Same pipeline as content_digests and thesis_threads: trigger -> pgmq -> pg_cron -> Edge Function -> Voyage AI -> vector column.

---

## 7. WebFront Integration (/comms)

Cindy gets her own section on digest.wiki at route `/comms`. Four pages:

### Page 1: Interaction Feed (`/comms`)

Chronological feed of all observed interactions across all surfaces, with source badges and signal highlights.

```
/comms

+--------------------------------------------------------------------+
|  Interaction Feed                           [12 today] [47 this wk] |
+--------------------------------------------------------------------+
|                                                                      |
|  [Filters: All | Email | WhatsApp | Granola | Calendar]             |
|  [Search: ___________________________]                              |
|                                                                      |
|  +--- 10:45 AM --- GRANOLA -----------------------------------------+
|  |                                                                    |
|  |  Composio Series A Discussion                                     |
|  |  With: Rahul Sharma, Sarah Lee                                    |
|  |  Duration: 45 min                                                  |
|  |                                                                    |
|  |  Summary: Discussed Series A terms. $20M at $100M pre.            |
|  |  Need IC review next week. Rahul strong technical background.     |
|  |                                                                    |
|  |  Signals: [Agentic AI] [Deal] [2 actions]                        |
|  |  [View transcript]                                                 |
|  +--------------------------------------------------------------------+
|                                                                      |
|  +--- 9:30 AM --- EMAIL --------------------------------------------+
|  |                                                                    |
|  |  Re: DeVC Collective — March Cohort Applications                  |
|  |  From: sneha@z47.com  To: Aakash  CC: cindy                      |
|  |  Thread: 4 messages                                                |
|  |                                                                    |
|  |  Summary: 12 new applications received. 3 flagged for review.     |
|  |  Signals: [DeVC Pipeline] [1 action]                              |
|  +--------------------------------------------------------------------+
|                                                                      |
|  +--- Yesterday 6:15 PM --- WHATSAPP --------------------------------+
|  |                                                                    |
|  |  Conversation with Karan Vaidya                                   |
|  |  Messages: 8 (since last extraction)                              |
|  |                                                                    |
|  |  Summary: Discussed competitive landscape for agent tooling.      |
|  |  Signals: [Thesis: Agentic AI]                                    |
|  +--------------------------------------------------------------------+
|                                                                      |
+--------------------------------------------------------------------+
```

**Data source:** `interactions` table ordered by timestamp DESC. JOIN with `people_interactions` and `network` for name resolution.

**Rendering:** Server Component (dynamic). Reads from Supabase via `@supabase/ssr`. Realtime subscription for new interactions.

### Page 2: People Activity (`/comms/people`)

Per-person view showing all interactions across all surfaces. Answers: "When did I last interact with X? Via what channel? How often?"

```
/comms/people

+--------------------------------------------------------------------+
|  People Activity                              [142 people tracked]   |
+--------------------------------------------------------------------+
|                                                                      |
|  [Search: ___________________________]                              |
|  [Sort: Last Interaction | Frequency | Name]                        |
|                                                                      |
|  +--- Rahul Sharma --- CTO, Composio ------ Last: today 10:45 AM --+
|  |                                                                    |
|  |  Surfaces: [Email 3] [Granola 2] [WhatsApp 5] [Calendar 4]       |
|  |  30-day interactions: 14                                           |
|  |  Trend: [graph showing interaction frequency]                     |
|  |                                                                    |
|  |  Recent:                                                          |
|  |    Today 10:45  Granola  "Composio Series A Discussion"           |
|  |    Mar 18 2:00  Email    "Re: Term sheet review"                  |
|  |    Mar 17 6:15  WhatsApp "Competitive landscape chat"             |
|  |    Mar 15 11:00 Calendar "Intro call — Composio"                  |
|  |                                                                    |
|  |  Open actions: 2  |  Thesis: Agentic AI Infrastructure           |
|  |  [View full history]                                               |
|  +--------------------------------------------------------------------+
|                                                                      |
|  +--- Sneha --- EA, Z47 -------------- Last: today 9:30 AM ---------+
|  |  Surfaces: [Email 12] [WhatsApp 8] [Calendar 6]                  |
|  |  30-day interactions: 26   (No Granola — internal, expected)      |
|  +--------------------------------------------------------------------+
|                                                                      |
+--------------------------------------------------------------------+
```

**Data source:** `people_interactions` JOIN `network` JOIN `interactions`. Aggregate counts per surface.

**Key feature:** Relationship temperature indicator based on interaction frequency decay. If someone Aakash was meeting weekly drops to zero interactions for 3+ weeks, flag as "cooling."

### Page 3: Context Gaps (`/comms/gaps`)

Meetings Cindy lacks context on, with structured input prompts for Aakash.

```
/comms/gaps

+--------------------------------------------------------------------+
|  Context Gaps                                       [3 pending]      |
+--------------------------------------------------------------------+
|                                                                      |
|  +--- PENDING --- today 2:00 PM ------------------------------------+
|  |                                                                    |
|  |  Meeting: Coffee with Priya Mehta                                 |
|  |  Attendees: Priya Mehta (Investor, Accel)                         |
|  |  Missing: Granola, Email, WhatsApp                                |
|  |                                                                    |
|  |  +---------------------------------------------------+            |
|  |  | Quick notes about this meeting:                   |            |
|  |  |                                                   |            |
|  |  |                                                   |            |
|  |  +---------------------------------------------------+            |
|  |  Key takeaways (optional):                                        |
|  |  [+Add]                                                            |
|  |  Action items (optional):                                         |
|  |  [+Add]                                                            |
|  |                                                                    |
|  |  [Submit notes]  [Skip — low signal]                              |
|  +--------------------------------------------------------------------+
|                                                                      |
|  +--- PARTIAL --- yesterday 4:00 PM --------------------------------+
|  |                                                                    |
|  |  Meeting: Cybersecurity thesis review — internal                  |
|  |  Coverage: [Email thread found]                                   |
|  |  Missing: [Granola] [WhatsApp]                                    |
|  |  (Lower priority — has partial coverage)                          |
|  +--------------------------------------------------------------------+
|                                                                      |
|  --- Filled (5) --- Skipped (2) ------------------------------------ |
+--------------------------------------------------------------------+
```

**Data source:** `context_gaps` table with status='pending' or 'partial'.

**Server Actions:**
```typescript
async function fillContextGap(gapId: number, input: GapInput) {
  // 1. Update context_gaps record
  await supabase
    .from('context_gaps')
    .update({
      status: 'filled',
      user_input: input,
      filled_by: 'webfront',
      filled_at: new Date().toISOString(),
    })
    .eq('id', gapId);

  // 2. Write to cai_inbox for Cindy to process the notes
  await supabase.from('cai_inbox').insert({
    type: 'cindy_gap_filled',
    content: `User filled context gap for: ${gap.meeting_title}`,
    metadata: { gap_id: gapId, input },
    processed: false,
    created_at: new Date().toISOString(),
  });
}

async function skipContextGap(gapId: number) {
  await supabase
    .from('context_gaps')
    .update({ status: 'skipped', updated_at: new Date().toISOString() })
    .eq('id', gapId);
}
```

### Page 4: Observation Stats (`/comms/stats`)

Dashboard showing Cindy's observation coverage.

```
/comms/stats

+--------------------------------------------------------------------+
|  Observation Stats                                                   |
+--------------------------------------------------------------------+
|                                                                      |
|  --- This Week ---                                                   |
|                                                                      |
|  Interactions Processed: 47                                          |
|    Email: 18  |  WhatsApp: 15  |  Granola: 8  |  Calendar: 6       |
|                                                                      |
|  People Linked: 34 unique                                            |
|    Matched existing: 28  |  New (sent to Datum): 6                  |
|                                                                      |
|  Signals Extracted:                                                  |
|    Action items: 12  |  Thesis signals: 8  |  Deal signals: 3       |
|                                                                      |
|  Context Gaps:                                                       |
|    Created: 5  |  Filled: 3  |  Skipped: 1  |  Pending: 1          |
|    Coverage rate: 88% (of meetings have at least 1 source)           |
|                                                                      |
|  --- Trends (4 weeks) ---                                            |
|                                                                      |
|  [Interaction volume chart — stacked by source]                      |
|  [Coverage rate trend — line chart]                                  |
|  [People activity heatmap — who interacts most]                      |
|                                                                      |
+--------------------------------------------------------------------+
```

**Data source:** Aggregation queries over `interactions`, `people_interactions`, and `context_gaps`.

**Rendering:** Server Component with ISR (revalidate every 15 minutes).

### WebFront Phase Integration

Cindy's WebFront pages fit as **Phase 3** or **Phase 3.5** in the WebFront roadmap:

| Phase | Feature | Dependency |
|-------|---------|------------|
| 1 | Action Triage + Semantic Search | (current) |
| 2 | Thesis Interaction | Phase 1 |
| 2.5 | Megamind: Strategic Overview | Phase 1 + Megamind |
| **3** | **Pipeline Status** | Phase 1 |
| **3.5** | **Cindy: /comms pages** | **Phase 1 (Supabase) + Cindy agent running** |
| 4 | Agent Messaging | Phase 1 |

---

## 8. Data Flow Diagrams

### Email Flow

```
Email sent with CC: cindy@agent.aicos.ai
    |
    v
AgentMail Cloud (receives, parses, auto-threads, strips quoted history)
    |  WebSocket event: message.received
    v
Droplet WebSocket listener (persistent async connection, no public endpoint)
    |  parses event, writes to Postgres
    v
cai_inbox: type='cindy_email', metadata={from, to, cc, subject, extracted_text, thread_id}
    |
    v
Orchestrator heartbeat (60s) detects cindy_* message
    |  send_to_cindy_agent(@tool bridge)
    v
Cindy Agent processes:
    |- Parse email
    |- Resolve people (Network DB)
    |   |- Matched: link to interaction
    |   |- Unmatched: write datum_person → cai_inbox
    |- Extract signals
    |- Write interaction record
    |- Write action items → actions_queue
    |- Write thesis signals → cai_inbox (cindy_signal)
    v
ACK to Orchestrator
```

### WhatsApp Flow

```
iPhone → iCloud Backup (continuous)
    |
    v
Mac LaunchDaemon (daily 3:00 AM IST, after iCloud backup at 2:00 AM)
    |  Extract ChatStorage.sqlite
    |  Parse conversations since last extraction
    |  POST batch to droplet endpoint (or write directly to cai_inbox)
    v
cai_inbox: type='cindy_whatsapp', metadata={conversations: [...]}
    |
    v
Orchestrator heartbeat → Cindy Agent
    |
    v
Cindy processes batch:
    |- For each conversation:
    |   |- Resolve participants (phone → Network DB)
    |   |- Classify: deal/portfolio/thesis/operational/social
    |   |- Extract signals (skip social conversations)
    |   |- Write interaction record (summary only, no raw text)
    |- Write action items, thesis signals downstream
    v
ACK to Orchestrator
```

### Granola Flow

```
Meeting happens → Granola transcribes
    |
    v
Orchestrator scheduled poll (every 30 min):
    |  Granola MCP: list_meetings(since=last_check)
    |  For each new meeting: get_meeting_transcript(meeting_id)
    v
cai_inbox: type='cindy_meeting', metadata={meeting_id, transcript, attendees, action_items}
    |
    v
Orchestrator heartbeat → Cindy Agent
    |
    v
Cindy processes:
    |- Parse transcript, extract speakers
    |- Resolve attendees (name → Network DB, cross-ref Calendar emails)
    |- Apply IDS lens: thesis signals, conviction impact, key questions
    |- Link to Calendar event (time window match)
    |- Fill context_gap if one exists
    |- Write interaction record
    |- Feed: actions → actions_queue, thesis → cindy_signal, entities → datum_entity
    v
ACK to Orchestrator
```

### Calendar Flow

```
Two ingestion paths:

Path A: .ics in email → same as Email flow but event extracted from attachment
Path B: Google Calendar MCP poll (every 30 min via Orchestrator)

    |
    v
cai_inbox: type='cindy_calendar', metadata={event_id, title, attendees, time, location}
    |
    v
Orchestrator heartbeat → Cindy Agent
    |
    v
Cindy processes:
    |- Parse event
    |- Resolve attendees (email → Network DB)
    |
    |- IF upcoming (next 48h):
    |   |- Assemble pre-meeting context
    |   |- Query recent interactions with attendees
    |   |- Query open actions, thesis connections
    |   |- Store context_assembly in interaction record
    |   |- Write notification: "Pre-meeting brief ready for [meeting]"
    |
    |- IF past (last 24h):
    |   |- Run context gap detection
    |   |- Check Granola coverage (time window match)
    |   |- Check Email coverage (attendee overlap, last 48h)
    |   |- Check WhatsApp coverage (attendee overlap, last 48h)
    |   |- If no coverage → create context_gap
    |   |- Write notification: "Context gap: [meeting]"
    |
    |- Write interaction record
    v
ACK to Orchestrator
```

---

## 9. Orchestrator Integration

### New Inbox Message Types

| Type | Source | Example Content | Routes To |
|------|--------|----------------|-----------|
| `cindy_email` | Email webhook handler | "New email thread from cindy@3niac.com" | Cindy Agent |
| `cindy_whatsapp` | Mac extraction cron | "WhatsApp batch: 47 messages across 12 conversations" | Cindy Agent |
| `cindy_meeting` | Granola MCP poll / CAI relay | "New Granola transcript available" | Cindy Agent |
| `cindy_calendar` | Calendar MCP poll / .ics email | "New calendar event detected" | Cindy Agent |
| `cindy_gap_filled` | WebFront Server Action | "User filled context gap for: [meeting]" | Cindy Agent |
| `cindy_signal` | Cindy Agent (outbound) | "Thesis signal from meeting" | Megamind (via Orchestrator) |

### Orchestrator HEARTBEAT.md Additions

```markdown
## Step 2.8: Cindy Communication Processing (NEW)

### Check for Cindy inbox messages
```bash
psql $DATABASE_URL -t -A -c "
  SELECT id, type, content
  FROM cai_inbox
  WHERE type LIKE 'cindy_%'
    AND type != 'cindy_signal'
    AND processed = FALSE
  ORDER BY created_at
  LIMIT 5"
```

If results exist:
1. Batch cindy messages of the same type (e.g., 3 cindy_email messages → single batch prompt)
2. Call `send_to_cindy_agent` with the batch prompt
3. If Cindy is busy: skip, retry next heartbeat

### Check for Cindy signals needing routing
```bash
psql $DATABASE_URL -t -A -c "
  SELECT id, content, metadata
  FROM cai_inbox
  WHERE type = 'cindy_signal'
    AND processed = FALSE
  ORDER BY created_at
  LIMIT 3"
```

If results exist:
1. Route to Megamind via `send_to_megamind_agent` for strategic assessment
2. Mark messages as processed

### Granola poll trigger (every 30 min)
```bash
# Check if 30 min since last Granola poll
last_granola=$(cat state/last_granola_poll.txt 2>/dev/null || echo "1970-01-01")
mins_since=$(( ($(date +%s) - $(date -d "$last_granola" +%s)) / 60 ))
if [ $mins_since -ge 30 ]; then
    # Trigger Granola MCP poll — write trigger message to cai_inbox
    psql $DATABASE_URL -c "INSERT INTO cai_inbox (type, content, processed, created_at) VALUES ('cindy_granola_poll', 'Poll Granola for new meetings', FALSE, NOW())"
    date -u +"%Y-%m-%dT%H:%M:%SZ" > state/last_granola_poll.txt
fi
```

### Calendar poll trigger (every 30 min)
Same pattern as Granola, with `state/last_calendar_poll.txt`.

### Context gap detection trigger (daily at 8 PM IST)
Trigger Cindy to scan past 24h calendar events for gaps.
```

### New Bridge Tool (lifecycle.py)

```python
@tool(
    "send_to_cindy_agent",
    "Send communication data to the persistent Cindy Agent for processing. "
    "Handles email, WhatsApp, Granola, and Calendar signals. "
    "Returns immediately — Cindy works in background. "
    "If Cindy is busy, returns a busy message.",
    {"prompt": str},
)
async def send_to_cindy_agent(args: dict[str, Any]) -> dict[str, Any]:
    # Same pattern as send_to_content_agent, send_to_datum_agent, send_to_megamind_agent
```

### New ClientState Fields

```python
class ClientState:
    content_client: Any = None
    content_needs_restart: bool = False
    content_busy: bool = False

    datum_client: Any = None
    datum_needs_restart: bool = False
    datum_busy: bool = False

    megamind_client: Any = None
    megamind_needs_restart: bool = False
    megamind_busy: bool = False

    cindy_client: Any = None         # NEW
    cindy_needs_restart: bool = False  # NEW
    cindy_busy: bool = False          # NEW
```

---

## 10. Datum Integration (New People Flow)

When Cindy encounters a person she cannot match to the Network DB, she creates a datum request via cai_inbox rather than creating records directly. This ensures Datum Agent's dedup algorithm is the single gatekeeper for entity creation.

### Flow

```
Cindy encounters "rahul@composio.dev" in email CC
    |
    v
Network DB query: SELECT id FROM network WHERE email = 'rahul@composio.dev'
    |
    v (no match)
    |
Cindy writes to cai_inbox:
    {
      type: "datum_person",
      content: "New person from email: Rahul Sharma <rahul@composio.dev>",
      metadata: {
        name: "Rahul Sharma",
        email: "rahul@composio.dev",
        company: null,
        role: null,
        source: "cindy_email",
        context: "CC'd on email thread: 'Re: Series A follow-up' with ak@z47.com",
        interaction_id: 123
      }
    }
    |
    v
Orchestrator routes to Datum Agent (datum_* type)
    |
    v
Datum Agent: dedup, enrich, create record → network.id = 42
    |
    v
Datum Agent writes notification: "Created person: Rahul Sharma, ID=42"
    |
    v
Next Cindy cycle: re-resolve "rahul@composio.dev" → matches ID=42
    → Updates people_interactions + interaction.linked_people
```

### Batch Entity Flow (from Granola transcripts)

```
Cindy processes meeting transcript with 4 attendees:
  - Aakash Kumar (matched, ID=1)
  - Rahul Sharma (matched, ID=42)
  - Sarah Lee (no match)
  - Unknown Attendee (no match, name only)

Cindy writes batch to cai_inbox:
    {
      type: "datum_entity",
      content: "Entity batch from Granola meeting: Composio Series A Discussion",
      metadata: {
        entities: [
          { type: "person", name: "Sarah Lee", company: "Composio",
            context: "Attendee in meeting about Composio Series A" },
          { type: "person", name: "Unknown Attendee",
            context: "Unidentified attendee in Composio meeting" }
        ],
        source: "cindy_meeting",
        interaction_id: 456
      }
    }
```

---

## 11. Megamind Integration (Strategic Signals)

Cindy surfaces high-value interaction signals to Megamind for strategic reasoning. Not every interaction generates a strategic signal — only those that could affect investment thesis, portfolio decisions, or action prioritization.

### Signal Routing Criteria

| Signal Type | Threshold | Example |
|-------------|-----------|---------|
| Deal signal | Any mention of terms, valuation, funding | "Discussed $20M at $100M pre with Composio" |
| Thesis conviction change | Strong signal (++ or ??) | "Granola transcript: AI agent adoption hitting inflection point" |
| Portfolio risk | Any portfolio company signal | "WhatsApp: Composio founder mentions runway concerns" |
| Relationship cooling | Person score > 7 + no interaction for 21 days | "Last interaction with Rahul was 3 weeks ago — was meeting weekly" |
| Meeting cluster | 3+ meetings with same company in 7 days | "3 meetings with Composio team this week — escalating" |

### Signal Format

```sql
INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
VALUES (
    'cindy_signal',
    'Strategic signal from Cindy: Deal acceleration at Composio',
    '{
        "signal_type": "deal_signal",
        "strength": "strong",
        "summary": "3 meetings with Composio team this week. Term sheet discussion in latest meeting. Series A at $100M pre.",
        "thesis_connections": ["Agentic AI Infrastructure"],
        "people_involved": [42, 43],
        "company": "Composio",
        "interaction_ids": [123, 456, 789],
        "recommended_action": "IC review next week — deal momentum building"
    }'::jsonb,
    FALSE,
    NOW()
);
```

### Megamind Processing

Megamind receives cindy_signals via Orchestrator routing and:
1. Evaluates the strategic ROI of the signal
2. Checks thesis thread state for connected threads
3. Re-ranks open actions in the blast radius
4. May generate new depth-graded research tasks
5. Surfaces summary to Aakash via notification

---

## 12. Privacy and Security Considerations

### Data Classification

| Surface | Raw Data | Storage Policy |
|---------|----------|---------------|
| **Email** | Full email body, headers, attachments | Store full body in `raw_data` JSONB. Attachments: metadata only (name, type, size). |
| **WhatsApp** | Chat messages, media | **NEVER store raw message text.** Store structured summary only. Media: metadata only (type, filename). |
| **Granola** | Meeting transcripts | Store full transcript in `raw_data` JSONB (already processed by Granola). |
| **Calendar** | Event details | Store full event data in `raw_data` JSONB. |

### WhatsApp Privacy Rules (MANDATORY)

1. **No raw message storage.** Cindy processes WhatsApp messages in-context for signal extraction, then discards raw text. Only the structured summary survives.
2. **No third-party message storage.** Messages from other participants in group chats are summarized at the conversation level. Individual messages from non-Aakash participants are not stored.
3. **No media extraction.** WhatsApp media files (images, documents, voice notes) are logged by type and filename only. The actual files are never copied, transferred, or stored.
4. **Extraction runs locally on Mac.** The iCloud backup parsing runs on Aakash's Mac, not on the droplet. Only structured data (summaries, participant lists, timestamps) travels to the droplet.

### Access Control

| Actor | Access Level |
|-------|-------------|
| Cindy Agent (droplet) | Full read/write on interactions, context_gaps, people_interactions |
| Other Agents (droplet) | Read-only on interactions (for context). No access to raw_data. |
| WebFront (Vercel) | Read via PostgREST with RLS. Summaries visible, raw_data restricted. |
| Supabase Dashboard | Full access (admin). Protected by Supabase auth. |

### Supabase RLS Policy

```sql
-- WebFront can read interaction summaries but NOT raw_data
CREATE POLICY "webfront_read_interactions" ON interactions
    FOR SELECT
    USING (true)
    WITH CHECK (false);

-- Mask raw_data in PostgREST responses via a view
CREATE VIEW interactions_public AS
    SELECT id, source, source_id, thread_id, participants, linked_people,
           linked_companies, summary, timestamp, duration_minutes,
           action_items, thesis_signals, relationship_signals, deal_signals,
           context_assembly, processed_at, created_at
    FROM interactions;
    -- raw_data column excluded
```

### Data Retention

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| Interaction summaries | Indefinite | Core intelligence, needed for people activity and relationship tracking |
| Email raw_data | 90 days | Full email bodies useful for context but not needed long-term |
| Granola raw_data | 90 days | Transcripts useful for review but summarized data suffices long-term |
| Context gaps (filled) | 30 days | Resolved gaps have no ongoing value |
| Context gaps (pending) | Until resolved | Kept until Aakash fills or skips |
| People interactions | Indefinite | Relationship tracking is cumulative |

---

## 13. Infrastructure Requirements

### Where Things Run

| Component | Location | Why |
|-----------|----------|-----|
| **Cindy Agent** | Droplet (as ClaudeSDKClient in lifecycle.py) | Same as all other agents. Persistent session, Bash+psql access. |
| **AgentMail WebSocket listener** | Droplet (async Python in lifecycle.py) | Persistent WebSocket connection to AgentMail cloud. Pure outbound — no public endpoint needed. Receives `message.received` events. |
| **WhatsApp extraction** | Mac (LaunchDaemon, daily 3:00 AM IST) | `brctl download` from iCloud Drive → decrypt ChatStorage.sqlite → parse with WhatsApp-Chat-Exporter → POST structured data to droplet. Requires Mac always-on or wake-on-schedule. |
| **Granola MCP polling** | Droplet (via Orchestrator) | Orchestrator triggers the poll, Granola MCP connected via Claude.ai. 4 tools: list_meetings, get_meetings, get_meeting_transcript, query_granola_meetings. |
| **Calendar API polling** | Droplet (via Orchestrator or cron) | Google Calendar API (or MS Graph) with syncToken incremental sync every 5 minutes. OAuth 2.0 credentials stored on droplet. |
| **WebFront /comms pages** | Vercel (Next.js) | Same as all other WebFront pages. Server Components + Supabase. |
| **Postgres tables** | Supabase (Mumbai) | Same as all other data tables. |

### New Infrastructure Needed

| Component | Effort | Dependencies | Notes |
|-----------|--------|-------------|-------|
| **AgentMail setup** | S (1-3h) | AgentMail account ($20/mo) | Create `cindy@agent.aicos.ai`, configure DNS (SPF/DKIM/MX on subdomain) |
| **WebSocket listener** | S (1-3h) | AgentMail Python SDK | Persistent async listener in lifecycle.py, writes to cai_inbox on message.received |
| **Calendar API credentials** | S (1-3h) | Google/M365 OAuth | OAuth 2.0 setup, store refresh token on droplet, confirm Google vs M365 primary |
| **WhatsApp extraction script** | M (3-8h) | Mac always-on, iCloud Drive sync, `whatsapp-chat-exporter` | Python script: `brctl download` → decrypt → SQLite parse → POST to droplet. LaunchDaemon at 3AM IST. |
| **Cindy agent workspace** | S (1-3h) | lifecycle.py pattern (exists) | `mcp-servers/agents/cindy/` directory structure |
| **Database migrations** | S (1-3h) | Supabase access (exists) | 3 new tables + ALTER TABLE on network |
| **Auto Embeddings config** | XS (<1h) | Supabase dashboard | Trigger on interactions table for semantic search |
| **Orchestrator updates** | S (1-3h) | lifecycle.py, HEARTBEAT.md | New bridge tool, new routing rules, new poll triggers |

### Cloudflare Tunnel Configuration

No new Cloudflare Tunnel routes needed for Cindy. AgentMail uses WebSocket (pure outbound connection from droplet — no public endpoint required). The existing Cloudflare Tunnel routes for State MCP and Web Tools MCP remain unchanged.

---

## 14. Implementation Plan

### Phase 0: Infrastructure (Prerequisites)
**Estimated effort:** S (1-3 hours)
**Dependencies:** Supabase access, existing lifecycle.py

- [ ] Run database migrations (interactions, context_gaps, people_interactions tables + network ALTER TABLE)
- [ ] Configure Auto Embeddings trigger for interactions table (Supabase dashboard)
- [ ] Create `mcp-servers/agents/cindy/` directory structure:
  ```
  cindy/
    CLAUDE.md
    CHECKPOINT_FORMAT.md
    state/
      cindy_session.txt
      cindy_iteration.txt
      cindy_last_log.txt
    live.log
  ```
- [ ] Create `skills/cindy/cindy-schema.md` (interactions schema + query patterns)
- [ ] Create `skills/cindy/people-resolution.md` (cross-surface identity resolution algorithm)
- [ ] Modify lifecycle.py: add Cindy ClientState, bridge tool, options builder, lifecycle hooks
- [ ] Modify Orchestrator HEARTBEAT.md: add cindy_* routing rules
- [ ] Modify Orchestrator CLAUDE.md: add `send_to_cindy_agent` to capabilities

### Phase 1: Calendar Surface (MVP)
**Estimated effort:** M (3-8 hours)
**Dependencies:** Phase 0, Calendar API OAuth credentials (Google or MS Graph — confirm with Aakash)

Calendar is the anchor surface and delivers immediate value: context gap detection for every meeting.

- [ ] **Confirm calendar provider:** Ask Aakash whether primary meeting calendar is Google Calendar or M365 Outlook
- [ ] Set up OAuth 2.0 credentials for Calendar API (GCP project + consent screen if Google, Azure AD app if M365)
- [ ] Store refresh token securely on droplet (`.env` or secrets file)
- [ ] Implement syncToken-based incremental polling (every 5 min via Orchestrator or cron):
  - Initial sync: fetch all events from past 7 days
  - Incremental: use syncToken to get only changes (new/updated/cancelled events)
  - Store syncToken in Postgres for persistence across restarts
- [ ] Write Cindy's Calendar processing pipeline:
  - Parse event: title, time, attendees (email + displayName + responseStatus), location, description
  - Resolve attendees: email → Network DB match
  - Detect changes: new events (sequence=0), updated (sequence>0), cancelled (status='cancelled')
- [ ] Implement pre-meeting context assembly for upcoming events (next 48h)
- [ ] Implement context gap detection with context richness scoring:
  - Check Granola coverage (time window match)
  - Check Email coverage (attendee overlap, last 48h)
  - Check Network DB coverage (known people, IDS state)
  - Score < 0.3 → create context_gap record
- [ ] Write notifications for context gaps (urgent if < 24h, planned if 24-48h)
- [ ] Test: poll Calendar API, verify interactions created, gaps detected for uncovered meetings

### Phase 2: Granola Surface
**Estimated effort:** M (3-8 hours)
**Dependencies:** Phase 1, Granola MCP connected (already operational)

Granola provides the richest signal per interaction — full transcripts with speaker attribution and AI-generated summaries.

- [ ] Implement Granola MCP polling in Orchestrator HEARTBEAT.md (30-min interval):
  - `list_meetings(time_range="this_week")` → get meeting IDs
  - For each new meeting: `get_meetings(meeting_ids=[id])` → attendees, AI summary
  - `get_meeting_transcript(meeting_id)` → utterance array with speaker + timestamps
  - Handle 404 (no transcript): retry with backoff (5 min, 10 min, 20 min) — transcripts available 2-5 min post-meeting
- [ ] Write Cindy's Granola processing pipeline:
  - Parse transcript utterances: `source: "microphone"` = Aakash, `source: "system"` = others
  - Resolve attendees: names from `get_meetings` → Network DB match, cross-ref with Calendar emails
  - Apply IDS methodology lens: thesis signals, conviction impact, key questions
  - Extract action items (both from Granola's AI summary AND from raw transcript — Granola may miss IDS-specific signals)
- [ ] Implement Calendar-Granola linking using multi-signal matching:
  - Time overlap (50% weight): granola.meeting_date within +/-15 min of calendar.start
  - Attendee overlap (30% weight): fuzzy match calendar emails vs granola names
  - Title similarity (20% weight): fuzzy match calendar.summary vs granola.title
  - Threshold: 0.5+ = confident match
- [ ] Implement retroactive context gap filling (transcript arrives → gap resolved)
- [ ] Test: process Granola transcript, verify interaction created, signals extracted, calendar linked, gap filled

### Phase 3: Email Surface
**Estimated effort:** L (1-3 sessions)
**Dependencies:** Phase 0, AgentMail account ($20/mo)

Email uses AgentMail with WebSocket events — no webhook infrastructure needed.

- [ ] Sign up for AgentMail Developer tier ($20/mo)
- [ ] Add `AGENTMAIL_API_KEY` to droplet `.env`
- [ ] Install SDK: `pip install agentmail` on droplet
- [ ] Set up custom domain: add `agent.aicos.ai` subdomain, configure DNS (SPF/DKIM/MX), verify
- [ ] Create Cindy's inbox: `cindy@agent.aicos.ai`
- [ ] Implement persistent WebSocket listener in lifecycle.py (alongside agent management)
  - Subscribe to `message.received` events for Cindy's inbox
  - On event: parse email fields, write to cai_inbox with type='cindy_email'
  - Handle reconnection gracefully (WebSocket drop → auto-reconnect)
- [ ] Write Cindy's Email processing pipeline (parse extracted_text, thread tracking via AgentMail thread_id, resolve people by email, extract signals)
- [ ] Implement .ics detection: detect `text/calendar` attachments, parse with `icalendar` library, create calendar interaction
- [ ] Test: CC cindy@agent.aicos.ai on email, verify interaction created, people linked
- [ ] Test: forward calendar invite, verify calendar event extracted from .ics

### Phase 4: WhatsApp Surface
**Estimated effort:** L (1-3 sessions)
**Dependencies:** Phase 0, Mac always-on, iCloud Drive sync enabled, WhatsApp E2E backup encryption disabled

WhatsApp is the highest-volume surface. Daily batch extraction from iCloud backup.

- [ ] Install extraction tools on Mac: `pip3 install whatsapp-chat-exporter icalendar`
- [ ] Write Mac extraction script (`cindy_whatsapp_extract.py`):
  - `brctl download` ChatStorage.sqlite.enc from iCloud Drive path
  - Decrypt (standard iCloud encryption, not WhatsApp E2E)
  - Open SQLite, query ZWAMESSAGE + ZWACHATSESSION since last_extraction_timestamp
  - Convert Apple CF timestamps to ISO 8601
  - Extract JIDs → phone numbers, push names
  - Group by conversation, extract messages (text only, no media)
  - POST structured JSON batch to droplet endpoint
  - Store last_extraction_timestamp in local state file
- [ ] Set up Mac LaunchDaemon (daily 3:00 AM IST, after iCloud backup at 2:00 AM)
- [ ] Implement droplet receiver endpoint (simple FastAPI on existing port, or direct Supabase write)
- [ ] Write Cindy's WhatsApp processing pipeline:
  - Batch parse conversations
  - Resolve participants: JID → phone → Network DB
  - Classify conversations (deal/portfolio/thesis/operational/social)
  - Extract signals from deal, portfolio, and thesis conversations only
  - Store interaction records (summary only — NOT raw message text)
- [ ] Implement privacy guards: verify no raw WhatsApp text in interactions.raw_data
- [ ] Test: trigger manual backup, run extraction, verify interactions created
- [ ] Test: verify participant phone numbers resolve to Network DB records

### Phase 5: WebFront /comms Pages
**Estimated effort:** L (1-3 sessions)
**Dependencies:** Phases 1-4 (data in tables), WebFront Phase 1 (Supabase connection)

- [ ] Create `/comms` route with Interaction Feed page
- [ ] Create `/comms/people` route with People Activity page
- [ ] Create `/comms/gaps` route with Context Gaps page (Server Actions for fill/skip)
- [ ] Create `/comms/stats` route with Observation Stats page
- [ ] Supabase Realtime subscriptions for new interactions and gaps
- [ ] Interactions public view (hides raw_data from PostgREST)
- [ ] Mobile-first responsive design (44x44 touch targets)
- [ ] Test: process interactions via Cindy, verify they appear on WebFront
- [ ] Test: fill a context gap on WebFront, verify Cindy processes the notes

### Phase 6: Cross-Surface Identity Stitching
**Estimated effort:** M (3-8 hours)
**Dependencies:** Phases 1-4 (all surfaces active)

With all four surfaces operational, identity stitching becomes powerful.

- [ ] Implement cross-link logic: when Cindy matches a person on one surface, check if new identifiers can fill gaps on their Network DB record
- [ ] Implement relationship temperature tracking (interaction frequency decay)
- [ ] Implement "cooling" alerts for high-value people with declining interaction frequency
- [ ] Implement interaction_count_30d and interaction_surfaces rolling updates on network table
- [ ] Test: same person appears in email and Granola with different identifiers, verify cross-linking

### Build Sequence

```
Phase 0 (infra) ──> Phase 1 (Calendar MVP)
                        |
                  Phase 2 (Granola)
                        |
              ┌─────────┴──────────┐
              |                    |
        Phase 3 (Email)     Phase 4 (WhatsApp)
              |                    |
              └─────────┬──────────┘
                        |
                  Phase 5 (WebFront)
                        |
                  Phase 6 (Identity Stitching)
```

**Critical path:** Phase 0 → Phase 1. Calendar MVP delivers immediate value: context gap detection for every meeting.

**Value delivery:**
- After Phase 1: Cindy detects meetings with no coverage — the context gap problem is surfaced
- After Phase 2: Meeting transcripts are processed, IDS signals extracted, gaps auto-filled
- After Phase 3: Email intelligence flows into the system — thread tracking, people linking
- After Phase 4: Full cross-surface observation — WhatsApp high-frequency signals captured
- After Phase 5: Aakash has a visual interaction history and can fill gaps
- After Phase 6: Cross-surface identity map connects Aakash's entire network

---

## 15. Cost Model

### Per-Source Token Estimates

| Source | Input Tokens | Output Tokens | Thinking Tokens | Notes |
|--------|-------------|---------------|-----------------|-------|
| Email (single) | ~1,500 | ~500 | ~2,000 | Parse + people resolution + signal extraction |
| WhatsApp (daily batch) | ~5,000 | ~2,000 | ~4,000 | Multiple conversations, classification, signals |
| Granola (single meeting) | ~4,000 | ~1,500 | ~5,000 | Full transcript analysis, IDS methodology |
| Calendar (poll batch) | ~1,000 | ~500 | ~1,000 | Structured data, gap detection queries |
| Context gap fill | ~800 | ~300 | ~1,000 | Process user notes through signal pipeline |

### Cost Per Operation (Sonnet 4 pricing: $3/M input, $15/M output)

| Operation | Cindy Cost | Notes |
|-----------|-----------|-------|
| Single email processing | ~$0.015 | 2-5 emails/day CC'd to Cindy |
| WhatsApp daily batch | ~$0.05 | Once per day |
| Single Granola transcript | ~$0.04 | 7-8 meetings/day = ~$0.30/day |
| Calendar poll + gap check | ~$0.01 | 2-3 times/day |
| Context gap fill (user input) | ~$0.01 | 1-3 per day |

### Monthly Projection

| Scenario | Volume | Cost |
|----------|--------|------|
| Light usage (3 emails, 3 meetings, 1 WhatsApp batch/day) | ~200 ops/month | ~$5-8/month |
| Medium usage (5 emails, 6 meetings, 1 WhatsApp batch/day) | ~400 ops/month | ~$10-16/month |
| Heavy usage (10 emails, 8 meetings, 1 WhatsApp batch/day) | ~600 ops/month | ~$16-25/month |

### Agent Budget Configuration

```python
CINDY_WORKSPACE = AGENTS_ROOT / "cindy"
CINDY_LIVE_LOG = CINDY_WORKSPACE / "live.log"

def build_cindy_options():
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ThinkingConfigEnabled

    cindy_tool_hook = _make_tool_hook(CINDY_LIVE_LOG)

    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill",
        ],
        hooks={"PostToolUse": [HookMatcher(hooks=[cindy_tool_hook])]},
        setting_sources=["project"],
        thinking=ThinkingConfigEnabled(type="enabled", budget_tokens=8000),
        effort="high",
        max_turns=35,
        max_budget_usd=3.0,
        cwd=str(CINDY_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        },
    )
```

### Budget Rationale

| Parameter | Value | Why |
|-----------|-------|-----|
| `max_budget_usd` | 3.0 | Higher than Datum (2.0) because Granola transcript analysis is token-heavy. Lower than Content Agent (5.0) because no web fetching. Same as Megamind (3.0). |
| `max_turns` | 35 | Granola processing: 10-15 turns (parse, resolve 4 attendees, extract signals, write). WhatsApp batch: 15-25 turns (iterate conversations, classify, extract). Email: 5-10 turns. Calendar: 5-8 turns. |
| `thinking` | 8000 tokens | IDS signal extraction from meeting transcripts benefits from extended thinking. People resolution across surfaces requires reasoning about identity. Higher than Datum (5000), lower than Content/Megamind (10000). |
| `effort` | high | People linking correctness is critical — wrong links propagate bad data. Signal extraction quality directly affects downstream action scoring. |

### Total System Cost with Cindy

| Agent | Current Monthly | With Cindy | Change |
|-------|----------------|-----------|--------|
| Orchestrator | ~$3-6 | ~$4-7 | +$1 (more routing) |
| Content Agent | ~$15-30 | ~$15-30 | No change |
| Datum Agent | ~$10-20 | ~$12-22 | +$2 (more entity requests from Cindy) |
| Megamind | ~$6-10 | ~$7-12 | +$1-2 (cindy_signals processing) |
| **Cindy** | -- | **~$10-16** | **New** |
| **Total** | ~$39-81 | ~$48-87 | +$9-16 |

### External Service Costs

| Service | Cost | Notes |
|---------|------|-------|
| AgentMail (email) | $20/month | Developer tier: 10 inboxes, 10K emails/month. Well above expected ~100-200 emails/month. |
| Voyage AI embeddings (interactions) | ~$0.50/month | Auto Embeddings on ~600 interactions/month, negligible |
| iCloud (WhatsApp backup) | $0 | Already included in Aakash's iCloud plan |
| Granola | $0 | MCP already connected, no per-call cost |
| Google Calendar | $0 | MCP already connected, no per-call cost |

---

## Appendix A: Directory Structure

```
mcp-servers/agents/
  cindy/
    CLAUDE.md                    # Full system prompt (Section 5)
    CHECKPOINT_FORMAT.md         # Compaction checkpoint format
    state/
      cindy_session.txt          # Session counter
      cindy_iteration.txt        # Iteration counter
      cindy_last_log.txt         # Last operation log
      cindy_checkpoint.md        # Checkpoint (if compaction needed)
    live.log                     # Real-time operation log

  skills/
    cindy/
      cindy-schema.md            # (new) Interactions/gaps/people_interactions schema + queries
      people-resolution.md       # (new) Cross-surface identity resolution algorithm
    data/
      postgres-schema.md         # (existing) Base schema reference
```

## Appendix B: Production Fleet Overview (with Cindy)

```
+----------------------------------------------------------------------+
|                    LIFECYCLE MANAGER (lifecycle.py)                     |
|  Python process that manages all five ClaudeSDKClient sessions         |
|  Heartbeat: 60s                                                        |
+------------+------------+------------+--------------+-----------------+
|            |            |            |              |                 |
| ORCHESTRATOR| CONTENT   | DATUM      | MEGAMIND     | CINDY           |
| (coordinator| AGENT     | AGENT      | (strategic   | (communications |
|  + routing) | (analysis | (entity    |  reasoning)  |  observer)      |
|            |  + pipe)  |  ingestion)|              |                 |
|            |            |            |              |                 |
| Model:     | Model:     | Model:     | Model:       | Model:          |
| Sonnet 4   | Sonnet 4   | Sonnet 4   | Sonnet 4     | Sonnet 4        |
| Effort:low | Effort:high| Effort:high| Effort:high  | Effort:high     |
| Think: --  | Think:10k  | Think: 5k  | Think: 10k   | Think: 8k       |
| Turns: 15  | Turns: 50  | Turns: 30  | Turns: 25    | Turns: 35       |
| Budget:$0.50| Budget:$5 | Budget:$2  | Budget:$3    | Budget:$3       |
|            |            |            |              |                 |
| Tools:     | Tools:     | Tools:     | Tools:       | Tools:          |
| Bash, R/W/E| Bash, R/W/E| Bash, R/W/E| Bash, R/W/E  | Bash, R/W/E     |
| Glob, Grep | Glob, Grep | Glob, Grep | Glob, Grep   | Glob, Grep      |
| Bridge x4  | Agent,Skill| Skill      | Skill        | Skill           |
|            | Web MCP all| Web MCP    | (no web)     | (no web)        |
|            |            |            |              |                 |
| Workspace: | Workspace: | Workspace: | Workspace:   | Workspace:      |
| orchestrator| content/  | datum/     | megamind/    | cindy/          |
+------------+------------+------------+--------------+-----------------+
```

### Agent Communication Flow (with Cindy)

```
60s heartbeat
    |
    v
ORCHESTRATOR
    |
    +-- Check cai_inbox for messages
    |   +-- datum_* types ---------> DATUM AGENT (entity work)
    |   +-- content_* types -------> CONTENT AGENT (analysis work)
    |   +-- strategy_* types ------> MEGAMIND (strategic assessment)
    |   +-- cindy_* types ---------> CINDY (communication processing)       # NEW
    |   +-- cindy_signal types ----> MEGAMIND (strategic signals from Cindy)  # NEW
    |   +-- general/research ------> CONTENT AGENT (default)
    |
    +-- Check actions_queue for agent-assigned actions needing depth grading
    |   +-- New agent actions -----> MEGAMIND (depth grading)
    |
    +-- Check depth_grades for approved grades needing execution
    |   +-- Route to Content Agent (research, thesis, content tasks)
    |   +-- Route to Datum Agent (entity enrichment tasks)
    |
    +-- Check for completed agent work needing cascade processing
    |   +-- Completed work --------> MEGAMIND (cascade re-ranking)
    |
    +-- Scheduled triggers:
    |   +-- Pipeline check (12h) --> CONTENT AGENT
    |   +-- Granola poll (30min) --> cai_inbox → CINDY                      # NEW
    |   +-- Calendar poll (30min) -> cai_inbox → CINDY                      # NEW
    |   +-- Gap detection (daily) -> cai_inbox → CINDY                      # NEW
```

## Appendix C: Cindy's Interaction with ENIAC

When Cindy extracts action items, she writes them to `actions_queue` with raw scores. ENIAC (currently embedded in Content Agent's scoring functions) scores them.

Cindy uses a simplified scoring heuristic for initial action creation:

| Factor | Cindy's Heuristic |
|--------|------------------|
| `bucket_impact` | Based on person archetype + company stage |
| `conviction_change` | Based on deal_signals presence |
| `time_sensitivity` | Based on explicit deadlines in the interaction |
| `action_novelty` | High if first interaction with this person/company |
| `effort_vs_impact` | Meeting/call = medium effort, email = low effort |

When ENIAC matures into its own agent, Cindy's raw scores will be inputs that ENIAC refines with full context.

## Appendix D: Research Reports (All Complete)

Three parallel research agents investigated infrastructure specifics. All research is complete and findings are integrated into this spec.

| Research Area | Report | Key Findings |
|---------------|--------|-------------|
| **Email Infrastructure** | `docs/research/2026-03-20-cindy-email-infrastructure.md` | AgentMail ($20/mo), WebSocket events, `cindy@agent.aicos.ai`, Python SDK, reply text auto-extraction |
| **WhatsApp Backup Parsing** | `docs/research/2026-03-20-cindy-whatsapp-research.md` | iCloud Drive path, ChatStorage.sqlite schema, WhatsApp-Chat-Exporter, Apple CF timestamps, daily 3AM extraction, LOW ToS risk |
| **Calendar + Granola Integration** | `docs/research/2026-03-20-cindy-calendar-granola-research.md` | 4 Granola MCP tools verified, syncToken Calendar polling, multi-signal matching (time 50% + attendee 30% + title 20%), context richness scoring, Google vs M365 open question |

### Remaining Open Questions

1. **Google Calendar vs M365:** CONTEXT.md says "M365 (work email + calendar)" but Google Calendar MCP is referenced. Need Aakash to confirm which holds the authoritative meeting schedule. API patterns are nearly identical.
2. **WhatsApp E2E backup encryption:** Must be disabled for extraction to work. Need to verify Aakash's current setting.
3. **Granola attendee emails via MCP:** The `get_meetings` tool returns attendees, but unclear if it includes email addresses or only display names. The Enterprise API confirms emails exist in `calendar_event.invitees`. Need to test with a real meeting.
4. **AgentMail .ics MIME handling:** Calendar invites may arrive as `text/calendar` MIME parts that aren't standard "attachments." Need to test whether AgentMail exposes these.
