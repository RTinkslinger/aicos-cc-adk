# Granola Meeting Integration Architecture — AI CoS Research

**Document:** Granola Integration Research
**Date:** 2026-03-04
**Session:** 035 (Parallel Development, Subagent Research)
**Status:** Complete Research
**Next Step:** Incorporate into Build Roadmap phase planning

---

## Executive Summary

Granola is Aakash's meeting transcription system. It captures live audio from meetings (microphone + system audio) and generates real-time transcripts. The AI CoS can integrate Granola transcripts into the action optimization loop: meeting → transcript → IDS signal extraction → entity matching → action generation → Actions Queue.

**Key Finding:** Granola now has an official API (released early 2025). Previous reverse-engineering efforts are archived, but comprehensive API documentation exists. The AI CoS can programmatically:
- List all Granola workspaces (organizations)
- Fetch documents (meeting notes) with pagination
- Retrieve transcripts with speaker source, timestamps, and confidence scores
- Parse ProseMirror-formatted document content

**Integration Complexity:** Moderate. Authentication requires OAuth 2.0 refresh token management (WorkOS-based, with mandatory token rotation). Transcripts are available immediately after meetings. No automatic diarization (speaker identification) yet — transcripts show "Me" (microphone) vs "Them" (system audio).

---

## Part 1: Granola MCP Tools Available

The AI CoS system has four Granola MCP tools pre-connected:

### Tool 1: `list_meetings`
**Purpose:** List Granola meeting notes within a time range.

**Inputs:**
- `time_range`: Predefined ranges (`"this_week"`, `"last_week"`, `"last_30_days"`, `"custom"`)
- `custom_start` / `custom_end`: ISO date format if `time_range = "custom"`

**Output:** Meeting titles and metadata (no transcripts)

**Use Case:** "Show me all meetings from the past week" → scan for new meetings before analyzing

---

### Tool 2: `get_meetings`
**Purpose:** Retrieve detailed meeting information by ID.

**Inputs:**
- `meeting_ids`: Array of Granola meeting UUIDs (max 10)

**Output:** Private notes, AI-generated summary, attendees, metadata

**Use Case:** Load full meeting details after `list_meetings` identifies relevant meetings

---

### Tool 3: `get_meeting_transcript`
**Purpose:** Fetch verbatim transcript for a specific meeting.

**Inputs:**
- `meeting_id`: Granola meeting UUID

**Output:** Full transcript (utterance-by-utterance, verbatim)

**Use Case:** Extract raw transcript for IDS signal analysis, sentiment, commitments, entities

---

### Tool 4: `query_granola_meetings`
**Purpose:** Natural-language query over meeting notes with semantic search.

**Inputs:**
- `query`: Natural-language question (e.g., "What did [person] say about [topic]?")
- `document_ids`: Optional filter to specific meetings

**Output:** Tailored response with inline citation links to source meetings

**Use Case:** "What follow-ups did I commit to with founder X?" → semantic search across all meetings

---

## Part 2: Granola API Architecture (Underlying)

The MCP tools wrap Granola's official REST API. Understanding the API surface clarifies integration boundaries:

### Authentication: OAuth 2.0 with Refresh Token Rotation

**Flow:**
1. Initial setup: Extract `refresh_token` from WorkOS authentication (one-time)
2. Token refresh: `POST https://api.workos.com/user_management/authenticate`
   - Request: `client_id`, `grant_type: "refresh_token"`, current `refresh_token`
   - Response: new `access_token` (1-hour TTL), rotated `refresh_token` (invalidates old token)
3. **Critical:** Refresh tokens are single-use. Each auth response includes a NEW `refresh_token` that MUST be saved for the next request. Reusing old tokens fails.

**Implication for AI CoS:** MCP tool handles token rotation transparently. Pipeline should assume valid authentication; if 401 errors occur, restart session.

### API Endpoints (Raw Layer)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `api.workos.com/user_management/authenticate` | POST | Refresh access token |
| `api.granola.ai/v1/get-workspaces` | POST | List all organizations (workspaces) |
| `api.granola.ai/v2/get-document-lists` | POST | List folders (document collections) |
| `api.granola.ai/v2/get-documents` | POST | Fetch paginated meeting notes (up to 100/page) |
| `api.granola.ai/v1/get-documents-batch` | POST | Fetch multiple documents by ID (includes shared) |
| `api.granola.ai/v1/get-document-transcript` | POST | Retrieve transcript for a document |

**Data Format:**
- Documents stored as ProseMirror (rich text format) with metadata (created_at, updated_at, workspace_id, folders)
- Transcripts: Array of utterances: `{ source: "microphone|system", text: "...", start_timestamp, end_timestamp, confidence }`
- Response metadata includes workspace_id, folder associations, meeting_date (from first transcript)

### Transcript Structure

```json
[
  {
    "source": "microphone",           // "Me" in Granola UI
    "text": "Great, let's discuss the Series A timeline.",
    "start_timestamp": "2026-03-04T14:32:15Z",
    "end_timestamp": "2026-03-04T14:32:22Z",
    "confidence": 0.96
  },
  {
    "source": "system",               // "Them" in Granola UI
    "text": "We're looking at Q2 2026 for close.",
    "start_timestamp": "2026-03-04T14:32:23Z",
    "end_timestamp": "2026-03-04T14:32:30Z",
    "confidence": 0.94
  }
]
```

**Limitations:**
- No speaker diarization (desktop). iPhone app supports speaker identification; desktop shows "Me" vs "Them" only.
- 404 if document has no transcript (not all notes have recordings)
- `get-documents` does NOT return shared documents; use `get-documents-batch` for shared notes

---

## Part 3: Integration Architecture (AI CoS)

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ MEETING PREP (Before Meeting)                                   │
├─────────────────────────────────────────────────────────────────┤
│ 1. Query Network DB: Find person profile (prior meetings, IDS)   │
│ 2. Query Companies DB: Find company profile, conviction, thesis  │
│ 3. Query Thesis Tracker: Find relevant threads (AI, security)    │
│ 4. Query Granola: Fetch recent transcripts with person          │
│    → Extract: Prior commitments, signals, relationship temp      │
│ 5. Generate: Meeting brief (key questions, context, prep notes)  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ LIVE MEETING (During)                                            │
├─────────────────────────────────────────────────────────────────┤
│ Granola captures audio → live transcription (no AI CoS action)   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ POST-MEETING PIPELINE (After Meeting, ~5-10 min delay)          │
├─────────────────────────────────────────────────────────────────┤
│ 1. Poll Granola: Fetch latest meeting transcript (meeting_ids)  │
│ 2. Extract Signals:                                             │
│    - IDS notation: ++ (strong conviction), + (positive),        │
│      ? (open question), ?? (major uncertainty), +? (unclear),   │
│      - (concern)                                                │
│    - Commitments: "I'll send you X", "Let's follow up on Y"    │
│    - Key statements: Competitive threats, product updates       │
│    - Sentiment: Overall tone (enthusiastic, cautious, etc.)     │
│ 3. Entity Matching:                                             │
│    - Map names → Network DB (find person_id)                    │
│    - Map companies → Companies DB (find company_id)             │
│    - Map products/tech → Thesis topics                          │
│ 4. Generate Actions:                                            │
│    - Commitments → Actions Queue (Type: Follow-up, Status: Due) │
│    - IDS signals → Actions Queue (Type: Conviction Update)      │
│    - New contacts → Actions Queue (Type: Intro Request)         │
│ 5. Update DBs:                                                  │
│    - Network DB: Update person.last_interaction, IDS_state      │
│    - Companies DB: Update conviction (if strong signal)         │
│    - Thesis Tracker: Add new threads if discovered              │
│ 6. Route to Actions Queue: With Source Digest relation back     │
│    to original Granola meeting + extracted context              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
        Actions Queue (single sink for all actions)
        → Pending (awaiting approval)
        → Approved (ready to execute)
        → Dismissed (not actionable)
```

---

## Part 4: Signal Extraction Model (IDS Notation)

Transform Granola transcripts into structured investment signals for Aakash's action loop.

### Signal Taxonomy

| Signal | IDS Notation | Example | Action |
|--------|--------------|---------|--------|
| Strong validation | `++` | "We've proven retention at 2x benchmarks" | Conviction up; maybe increase check size |
| Positive signal | `+` | "Hiring is going well, just closed our VP Sales" | Monitor hiring momentum |
| Open question | `?` | "How are you thinking about unit economics post-CAC change?" | Add to key_questions; revisit next call |
| Major uncertainty | `??` | "We haven't determined our GTM yet" | Block decision; needs clarity before round |
| Mixed/unclear | `+?` | "Sales is OK, not sure if it's repeatable" | Needs follow-up; conflicted |
| Concern/risk | `-` | "Churn accelerated in Feb; we're investigating" | Risk escalation; monitor closely |

### Extraction Workflow

**Input:** Granola transcript (utterance array with source, text, timestamps)

**Process:**
1. Identify Aakash's utterances (`source: "microphone"`) — these are his signal-gathering questions
2. Extract counterparty responses (`source: "system"`)
3. Classify each response by IDS notation
4. Extract entities (person, company, product, metric, date)
5. Segment by topic (funding, team, product, market, risk)

**Output:** Structured signal object:
```json
{
  "meeting_id": "granola_uuid",
  "meeting_date": "2026-03-04T14:30:00Z",
  "person_id": "network_db_id",
  "company_id": "companies_db_id",
  "signals": [
    {
      "topic": "product",
      "signal": "++",
      "text": "We've proven retention at 2x benchmarks",
      "timestamp": "2026-03-04T14:32:22Z",
      "entities": ["benchmark", "retention"],
      "action_type": "conviction_update"
    }
  ],
  "commitments": [
    {
      "type": "follow-up",
      "text": "I'll send you the metrics deck by Friday",
      "due_date": "2026-03-07",
      "target_person": "person_id"
    }
  ]
}
```

---

## Part 5: Phased Implementation (IDS Progression)

Break Granola integration into phases aligned with **Increasing Degrees of Sophistication**:

### Phase 1: Manual Query (MVP — ~1 week)
- **Capability:** On-demand access to Granola transcripts via MCP tools
- **Interface:** Cowork prompt: "Fetch transcript for [meeting_id]" → `get_meeting_transcript` → display raw transcript
- **Output:** Unstructured transcript (human reads and extracts signals manually)
- **Use:** Post-meeting review; reference lookup during follow-ups
- **Launch:** Immediate; tests MCP connectivity and auth flow

### Phase 2: Prompted Signal Extraction (~2 weeks)
- **Capability:** Automated signal extraction on demand
- **Interface:** Cowork prompt: "Analyze meeting [meeting_id]" → fetch transcript → prompt Claude to extract IDS signals, commitments, entities → return structured JSON
- **Output:** Structured signals (IDS notation, commitments, risks, next questions)
- **Validation:** Manual review before Actions Queue entry (safety check)
- **Use:** Post-meeting analysis; conviction updates; commitment tracking
- **Launch:** Phase 1 + extraction prompts + validation UI

### Phase 3: Automated Pipeline (Scheduled — 4+ weeks)
- **Capability:** Continuous monitoring of new Granola meetings → automatic signal extraction → Actions Queue routing
- **Process:**
  1. Scheduled task (9:15 PM nightly or post-meeting trigger via Granola webhook, if available)
  2. Query `list_meetings` for new meetings since last run
  3. Fetch transcripts for new meetings
  4. Extract signals (Phase 2 prompts)
  5. Entity matching (Network DB, Companies DB, Thesis Tracker)
  6. Auto-route actions to Actions Queue (with Source Digest relation)
  7. Update Network DB + Companies DB (last_interaction, conviction)
- **Output:** Actions Queue updated in real-time; minimal manual overhead
- **Use:** Full AI CoS loop: transcripts feed action prioritization
- **Launch:** Phase 2 validated + scheduled task + entity matching + DB updates

### Phase 4: Meeting Prep Integration (Stretch — 6+ weeks)
- **Capability:** Pre-meeting brief generation from Granola history + Network + Companies DBs
- **Process:** Before Aakash enters a meeting, AI CoS queries:
  - Network DB for person history + IDS state
  - Granola for recent transcripts with person
  - Companies DB for company conviction + thesis
  - Extract: Unresolved questions, prior commitments, relationship temperature
- **Output:** 1-page meeting prep brief (WhatsApp-friendly)
- **Use:** Pre-meeting context; high-signal questioning; relationship continuity
- **Launch:** Phase 3 + meeting prep prompts + Calendar integration (M365)

---

## Part 6: Technical Considerations

### Rate Limiting & Performance
- Granola API does not document rate limits explicitly
- Recommendation: Poll `list_meetings` max 2x/day; fetch full transcripts on-demand or batched nightly
- MCP tools handle connection pooling; assume safe for standard usage

### Transcript Availability
- Transcripts available within ~2-5 minutes after meeting ends (processing delay)
- Recommendation: Automated pipeline waits 5 min after calendar event end before fetching
- Manual queries may hit "transcript not yet available" (404) — retry with backoff

### Privacy & Data Residency
- Granola does NOT record or save audio (only passes to transcription provider)
- Transcripts are stored in Granola's systems
- Extracted signals stored in AI CoS (Notion Actions Queue, Network DB, Companies DB)
- Recommendation: Treat Granola transcript IDs as sensitive; do not expose in URLs

### Speaker Identification Limitation
- Desktop app: "Me" (microphone) vs "Them" (system audio) only
- iPhone app supports full diarization (future desktop feature)
- Workaround: Manually label speakers in signal extraction step OR wait for official diarization

### Shared Documents
- `get-documents` endpoint returns only owned documents
- Use `get-documents-batch` to access shared meeting notes
- Implication: If Granola notes are shared with Aakash by others, must use batch API

---

## Part 7: Architecture Decisions & Tradeoffs

| Decision | Rationale | Tradeoff |
|----------|-----------|----------|
| **Phase 1 MVP first** | Validate MCP auth + tool stability before automation | Delayed full pipeline (3+ weeks) |
| **Manual validation gate in Phase 2** | Safety check before Actions Queue; catch extraction errors | Requires human review (bottleneck) |
| **Entity matching in Phase 3** | Enables Network + Companies DB updates; powers action scoring | Requires robust NLP or manual tagging |
| **Nightly batch vs real-time** | Reduces API load; simpler scheduling; handles Granola delay | 5-10 min lag between meeting end and Actions Queue |
| **IDS notation in extraction** | Aligns with Aakash's conviction language; powers scoring | Requires training extraction prompts on examples |
| **Source Digest relation (Actions) | Audit trail; traceability back to meeting transcript | Adds Notion property complexity |

---

## Part 8: Implementation Checklist (Phase 1 MVP)

**Phase 1: Manual Query (~3-5 days)**

- [ ] **Auth test:** Run `list_meetings` with valid Granola API credentials (test in Cowork)
- [ ] **Tool validation:** Confirm all 4 MCP tools work (list, get, transcript, query)
- [ ] **Transcript fetch:** Pull 1-2 recent meetings; verify transcript completeness
- [ ] **Output format:** Confirm transcript structure matches expected JSON (source, text, timestamp, confidence)
- [ ] **Documentation:** Update CLAUDE.md with Granola tool examples + auth refresh pattern
- [ ] **Build Roadmap entry:** Create item "Granola Transcript Access (Phase 1)" — Status 🧪 Testing, marked 🟢 Safe

**Phase 1 Follow-up: Build Roadmap**

- Link Phase 1 MVP to Phase 2 (Signal Extraction) as dependency
- Schedule Phase 2 kickoff for week of 2026-03-11

---

## Sources & References

- [Granola Official API Documentation](https://docs.granola.ai/introduction)
- [GitHub: Reverse-Engineered Granola API (Archived, refs official API)](https://github.com/getprobo/reverse-engineering-granola-api)
- [Granola Transcription Guide](https://docs.granola.ai/help-center/taking-notes/transcription)
- [Granola Help Center](https://www.granola.ai/docs)

---

## Summary Table: Phased Rollout

| Phase | Timeline | Output | Owner | Status |
|-------|----------|--------|-------|--------|
| 1: Manual Query | Week of 03-04 | Raw transcripts on-demand | Research ✓ | Ready to implement |
| 2: Signal Extraction | Week of 03-11 | Structured JSON + manual validation | Claude Code | Pending Phase 1 |
| 3: Automated Pipeline | Week of 03-25 | Actions Queue feed | Scheduled task | Pending Phase 2 |
| 4: Meeting Prep | Week of 04-08 | Pre-meeting brief | Calendar integration | Pending Phase 3 |

---

**Research completed by:** Session 035 subagent
**Recommended next:** Transfer findings to Build Roadmap phase planning; queue Phase 1 MVP for session 036
