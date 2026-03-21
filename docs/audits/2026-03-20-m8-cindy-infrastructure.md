# M8 Cindy Communications Infrastructure — Audit Report

**Date:** 2026-03-20
**Machine:** M8 (Cindy — Continuous Comms Capability)
**Loops:** 5-10

---

## Summary

Built the complete communications infrastructure that Cindy (the intelligent EA agent) needs to observe and act on Aakash's communications across 4 surfaces. All code is under `mcp-servers/agents/cindy/` and follows the patterns established in the Cindy skills documentation.

---

## Loop 5: AgentMail Email Processing Pipeline — COMPLETE

**File:** `cindy/email/email_processor.py`

**What was built:**
- Full async AgentMail API client (httpx-based, Bearer token auth)
- Email parser that handles various AgentMail response shapes (dict/string from/to fields)
- Signal extraction: action items, deal signals, thesis signals (regex-based, no LLM)
- People resolution: Tier 1 (email match) with Datum delegation for unknowns
- Deduplication by message_id against existing interactions
- AgentMail label management for audit trail (processed, action-required, deal-signal, thesis-signal)
- .ics attachment detection and flagging for calendar processing
- Skips Aakash's own emails and Cindy's address during people resolution

**AgentMail API details:**
- Base URL: `https://api.agentmail.to/v0`
- Auth: Bearer token via `AGENTMAIL_API_KEY` env var
- Inbox: `cindy.aacash@agentmail.to`
- Key endpoints: `GET /inboxes`, `GET /inboxes/{id}/messages`, `PATCH /inboxes/{id}/messages/{id}`

**CLI:** `python3 -m cindy.email.email_processor [--dry-run] [--since 2h] [--limit 50]`

---

## Loop 6: Calendar .ics Processing — COMPLETE

**File:** `cindy/calendar/ics_processor.py`

**What was built:**
- .ics file parser using Python `icalendar` library
- CalendarEvent dataclass with attendee parsing, organizer extraction, duration calculation
- Conference URI extraction from descriptions (Meet/Zoom/Teams links)
- Auto-skip rules: internal meetings (all @z47.com/@devc.fund), short meetings (<15 min), cancelled events
- Attendee resolution via Tier 1 (email match) — calendar is the strongest surface for email-based resolution
- Pre-meeting context assembly for future events: recent interactions, open actions, per-attendee context
- Writes context_assembly JSONB on the interaction record
- Datum delegation for unresolved attendees

**CLI:** `python3 -m cindy.calendar.ics_processor --file event.ics [--dry-run]`

---

## Loop 7: WhatsApp Extraction Script — COMPLETE

**File:** `cindy/whatsapp/whatsapp_extractor.py`

**What was built:**
- WhatsApp "Export Chat" .txt file parser (handles multiple date/time formats)
- System message filtering (encryption notices, group changes, joins/leaves)
- Media type detection from export placeholders
- Multi-line message continuation handling
- Conversation classification: deal, portfolio, thesis, operational, social
- Commitment extraction (regex-based) with I_OWE/THEY_OWE classification
- State management to track processed files (prevents reprocessing)
- Privacy-safe DB writes: raw message text is NEVER stored, only summaries and metadata

**Critical finding:** WhatsApp iCloud backups are **ENCRYPTED** (`.enc` files at `~/Library/Mobile Documents/57T9237FN3~net~whatsapp~WhatsApp/Accounts/919820820663/backup/ChatStorage.sqlite.enc`). Direct SQLite access is impossible without the device encryption key. The script uses WhatsApp's "Export Chat" .txt files as the practical input path. Users export individual chats from WhatsApp and place .txt files in `~/Documents/whatsapp-exports/`.

**CLI:** `python3 -m cindy.whatsapp.whatsapp_extractor [--export-dir ~/wa-exports] [--dry-run] [--since 2d]`

---

## Loop 8: Granola Meeting Notes Integration — COMPLETE

**File:** `cindy/granola/granola_processor.py`

**What was built:**
- Granola meeting data parser (handles MCP tool output shapes)
- Transcript obligation extraction with speaker identification:
  - `source: "microphone"` = Aakash speaking = I_OWE_THEM
  - `source: "system"` = other participant = THEY_OWE_ME
- Mutual obligation detection ("Let's schedule..." creates two records)
- Action item extraction from transcripts (beyond Granola's own action items)
- Deal signal detection from full transcript text
- Context gap filling: checks and resolves pending gaps when transcript arrives
- File-based processing (JSON dump) for standalone use; in production, Cindy agent calls Granola MCP tools directly

**CLI:** `python3 -m cindy.granola.granola_processor --meetings-json data.json [--dry-run]`

---

## Loop 9: Interactions Table Embedding Trigger — COMPLETE

**SQL applied to Supabase (project: llfkxnsfczludgigknbs):**

1. **`embedding_input_interactions()`** — Content function that generates embedding text from interaction fields (summary + source + participants + action_items)

2. **`clear_interactions_embedding_on_update`** — BEFORE UPDATE trigger that nulls the embedding vector when content changes, so Supabase Auto Embeddings re-embeds the row (same pattern as `content_digests`, `thesis_threads`, `actions_queue`, `network`, `companies`)

3. **`interactions_embedding_queue`** — AFTER INSERT/UPDATE trigger that sends to pgmq `embedding_jobs` queue via `util.queue_embeddings()`, so the embedding worker processes new rows

**Verified:** All 5 triggers now present on `interactions` table:
- `cir_interactions` (CIR change detection)
- `clear_interactions_embedding_on_update` (NEW)
- `interactions_embedding_queue` (NEW)
- `trg_interactions_embedding_input` (populates embedding_input text)
- `trg_interactions_updated` (timestamp)

**SQL saved at:** `mcp-servers/agents/sql/interactions_embedding_triggers.sql`

---

## Loop 10: Obligation Detection Pipeline — COMPLETE

**File:** `cindy/obligations/obligation_detector.py`

**What was built:**
- Full implementation of the `obligation-detection.md` skill specification
- Pattern-based obligation detection for all 4 surfaces
- 10 obligation categories: send_document, reply, schedule, follow_up, introduce, review, deliver, connect, provide_info, other
- I_OWE_THEM / THEY_OWE_ME classification based on speaker identity
- Due date extraction from natural language ("by Friday", "next week", "within 3 days")
- Pleasantry filtering ("Let's catch up sometime" excluded)
- Confidence threshold at 0.7 (below = not created)

**Cindy Priority Formula (5-factor weighted score):**
- Relationship tier (30%): portfolio_founder=1.0 down to cold_new=0.3
- Staleness (25%): 0-2 days=0.2 up to 14+ days=1.0
- Obligation type (20%): I_OWE * category weight vs THEY_OWE base
- Source reliability (15%): explicit=1.0, manual=0.9, implied=0.5
- Recency (10%): today=1.0 down to 7+ days=0.4

**Deduplication:** Checks existing obligations by person_id + interaction_id + description similarity before creating

**Auto-fulfillment:** When processing a new interaction, checks if it resolves existing pending obligations (e.g., Aakash sent email with attachment resolves "I_OWE send_document")

**Megamind routing:** Obligations with priority > 0.7 are routed to Megamind via `cindy_signal` in `cai_inbox`

**CLI:** `python3 -m cindy.obligations.obligation_detector --interaction-id 123 [--dry-run]`
**CLI:** `python3 -m cindy.obligations.obligation_detector --text "I'll send the deck" --source email --person-id 42 --from-aakash [--dry-run]`

---

## File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `cindy/__init__.py` | 2 | Package init |
| `cindy/email/__init__.py` | 2 | Email package init |
| `cindy/email/email_processor.py` | ~420 | AgentMail polling + email processing pipeline |
| `cindy/calendar/__init__.py` | 1 | Calendar package init |
| `cindy/calendar/ics_processor.py` | ~475 | .ics file parsing + pre-meeting context |
| `cindy/whatsapp/__init__.py` | 1 | WhatsApp package init |
| `cindy/whatsapp/whatsapp_extractor.py` | ~490 | Export chat parser + privacy-safe extraction |
| `cindy/granola/__init__.py` | 1 | Granola package init |
| `cindy/granola/granola_processor.py` | ~440 | Meeting transcript analysis + gap filling |
| `cindy/obligations/__init__.py` | 1 | Obligations package init |
| `cindy/obligations/obligation_detector.py` | ~580 | Full obligation detection + priority + fulfillment |
| `sql/interactions_embedding_triggers.sql` | 30 | DB migration (already applied) |

---

## Dependencies Required

All already in `pyproject.toml` or standard library:
- `httpx` (AgentMail API calls)
- `asyncpg` (Postgres async access)
- `icalendar` (needs adding to pyproject.toml for .ics parsing)

---

## What's NOT Done (Future Loops)

1. **AgentMail webhook/WebSocket listener** — currently uses polling. WebSocket would be real-time.
2. **WhatsApp decryption** — backup files are encrypted. Need device key or Apple Keychain integration.
3. **Granola direct API access** — currently processes JSON dumps. Cindy agent calls MCP tools in production.
4. **Implied obligation detection** — pattern matching handles explicit only. Implied (unanswered email 48h+) needs a scheduled scan.
5. **Staleness escalation cron** — checking obligations that crossed warning/overdue/escalation thresholds.
6. **Integration testing** — each module has --dry-run but no automated test suite yet.
