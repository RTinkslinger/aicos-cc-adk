# Cindy Communications Agent — Setup Assessment

**Date:** 2026-03-20 | **Milestone:** 8 | **Loop:** 4
**Purpose:** Verify the Cindy build and identify all SETUP work required before Cindy can process real data.

---

## 1. Verification Results

### 1.1 Code Quality

| Check | Result | Notes |
|-------|--------|-------|
| **lifecycle.py AST parse** | PASS | `python3 -c "import ast; ast.parse(...)"; print('AST OK')` |
| **Cindy functions in lifecycle.py** | PASS | All present: `build_cindy_options()`, `start_cindy_client()`, `stop_cindy_client()`, `restart_cindy_client()`, `send_to_cindy_agent()`, `_read_cindy_response()` |
| **Bridge tool registration** | PASS | `send_to_cindy_agent` included in bridge MCP server tools array |
| **Orchestrator CLAUDE.md routing** | PASS | Section 5d covers `cindy_*` routing, including `cindy_signal` -> Megamind exception |
| **Cindy CLAUDE.md completeness** | PASS | 838 lines, all 4 surfaces covered, 20 anti-patterns, ACK protocol, privacy rules, error handling |

### 1.2 Cindy Agent Build Artifacts

| Artifact | Status | Path |
|----------|--------|------|
| **CLAUDE.md** (agent instructions) | PRESENT | `mcp-servers/agents/cindy/CLAUDE.md` (838 lines) |
| **CHECKPOINT_FORMAT.md** | PRESENT | `mcp-servers/agents/cindy/CHECKPOINT_FORMAT.md` |
| **settings.json** (hooks config) | PRESENT | `mcp-servers/agents/cindy/.claude/settings.json` |
| **Stop hook** | PRESENT | `cindy/.claude/hooks/stop-iteration-log.sh` |
| **UserPromptSubmit hook** | PRESENT | `cindy/.claude/hooks/prompt-manifest-check.sh` (compaction at 100K tokens) |
| **PreCompact hook** | PRESENT | `cindy/.claude/hooks/pre-compact-flush.sh` |
| **State files** | PRESENT | `cindy/state/cindy_session.txt` (1), `cindy_iteration.txt` (0), `cindy_last_log.txt` |
| **Email processing skill** | PRESENT | `skills/cindy/email-processing.md` (167 lines) |
| **WhatsApp parsing skill** | PRESENT | `skills/cindy/whatsapp-parsing.md` (227 lines) |
| **Calendar gap detection skill** | PRESENT | `skills/cindy/calendar-gap-detection.md` (318 lines) |
| **People linking skill** | PRESENT | `skills/cindy/people-linking.md` (253 lines) |

### 1.3 Database Schema on Supabase

| Table | Status | Columns | Matches Migration SQL |
|-------|--------|---------|----------------------|
| **interactions** | DEPLOYED | 22 columns including `embedding` + `embedding_input` | YES — exact match |
| **context_gaps** | DEPLOYED | 16 columns | YES — exact match |
| **people_interactions** | DEPLOYED | 8 columns | YES — exact match |
| **network ALTER** (4 new columns) | DEPLOYED | `last_interaction_at`, `last_interaction_surface`, `interaction_count_30d`, `interaction_surfaces` | YES |
| **interactions_public view** | DEPLOYED | Excludes `raw_data` | YES |

### 1.4 Indexes

| Index | Status |
|-------|--------|
| `idx_interactions_source_time` | DEPLOYED |
| `idx_interactions_people` (GIN) | DEPLOYED |
| `idx_interactions_timestamp` | DEPLOYED |
| `idx_interactions_thread` (partial) | DEPLOYED |
| `idx_interactions_summary_fts` (GIN) | DEPLOYED |
| `idx_interactions_companies` (GIN) | DEPLOYED |
| `idx_interactions_embedding` (IVFFlat) | DEPLOYED |
| `idx_context_gaps_pending` (partial) | DEPLOYED |
| `idx_context_gaps_date` | DEPLOYED |
| `idx_pi_person` | DEPLOYED |
| `idx_pi_interaction` | DEPLOYED |
| `idx_pi_person_surface` | DEPLOYED |
| UNIQUE constraints (3) | DEPLOYED |

### 1.5 Triggers & Functions

| Trigger | Table | Status |
|---------|-------|--------|
| `trg_update_network_interaction` | people_interactions | DEPLOYED (auto-updates network.last_interaction_*) |
| `trg_interactions_updated` | interactions | DEPLOYED (auto-updates updated_at) |
| `trg_context_gaps_updated` | context_gaps | DEPLOYED (auto-updates updated_at) |
| `trg_interactions_embedding_input` | interactions | DEPLOYED (auto-populates embedding_input) |
| `cir_interactions` | interactions | DEPLOYED (Supabase Change in Record detection) |

### 1.6 Embeddings Status

| Item | Status | Notes |
|------|--------|-------|
| `embedding` column (vector 1024) | DEPLOYED | On interactions table |
| `embedding_input` auto-populate trigger | DEPLOYED | Fires on INSERT/UPDATE of summary, participants, source |
| `populate_interactions_embedding_input()` function | DEPLOYED | Concatenates summary, participants, source |
| **Queue embeddings trigger for interactions** | **MISSING** | No `queue_embeddings` trigger on interactions table. Other tables (content_digests, thesis_threads, etc.) have auto-embedding via pgmq queue. Interactions does NOT. |
| IVFFlat index | DEPLOYED | Will need REINDEX after initial data load |

**Action needed:** Configure Supabase Auto Embeddings for the interactions table (add `queue_embeddings` trigger), or add a manual embedding trigger that uses the same pgmq pattern as other tables.

### 1.7 Data Status

- **interactions table:** 0 rows (empty — never processed real data)
- **context_gaps table:** 0 rows
- **people_interactions table:** 0 rows
- **Cindy session:** #1, iteration 0 (never run)

---

## 2. Per-Surface Setup Assessment

### 2.1 Email (AgentMail)

**Status:** NOT SET UP — No account, no inbox, no listener, no scripts

| Step | Who | Effort | Dependency | Notes |
|------|-----|--------|------------|-------|
| **1. Create AgentMail account** | User | 10 min | None | $20/month. Visit agentmail.to. Choose domain (e.g., `agent.aicos.ai`) |
| **2. Create inbox** | User | 5 min | Step 1 | Create `cindy@agent.aicos.ai` (or similar) |
| **3. Configure forwarding** | User | 5 min | Step 2 | Set up Aakash's email client to CC/forward relevant emails to Cindy's inbox |
| **4. Write WebSocket listener script** | Automatable | 2-3 hr | Steps 1-2 | Python script on droplet: connects to AgentMail WebSocket, receives `message.received` events, writes `cindy_email` to `cai_inbox` table. Managed as systemd service. |
| **5. Install `icalendar` on droplet** | Automatable | 5 min | None | `pip install icalendar` — needed for .ics calendar invite parsing from emails |
| **6. Test end-to-end** | User + Auto | 30 min | Steps 1-5 | Send test email to Cindy, verify WebSocket receives it, verify `cai_inbox` record, verify Orchestrator routes to Cindy, verify interaction record created |

**Total effort:** ~3-4 hours + $20/month recurring
**Dependencies:** AgentMail account is the single blocker.

### 2.2 WhatsApp (iCloud Backup)

**Status:** PARTIALLY READY — iCloud backup directory EXISTS with account `919820820663`

| Step | Who | Effort | Dependency | Notes |
|------|-----|--------|------------|-------|
| **1. Verify ChatStorage.sqlite** | Automatable | 10 min | None | iCloud dir exists at `~/Library/Mobile Documents/57T9237FN3~net~whatsapp~WhatsApp/`. Account dir for `919820820663` present. Need to verify sqlite file inside `Accounts/919820820663/` |
| **2. Install whatsapp-chat-exporter** | Automatable | 5 min | None | `pip3 install whatsapp-chat-exporter` (NOT currently installed) |
| **3. Write extraction script** | Automatable | 3-4 hr | Steps 1-2 | Python script that: (a) copies ChatStorage.sqlite, (b) queries messages since last extraction (Apple CF timestamps), (c) groups by conversation, (d) resolves JIDs to phones, (e) builds structured JSON batch, (f) POSTs to droplet cai_inbox as `cindy_whatsapp` record, (g) stores `last_extraction_timestamp` in local state file |
| **4. Set up Mac cron job** | Automatable | 15 min | Step 3 | `launchd` plist for 3:00 AM IST daily run. Must run as Aakash's user (iCloud access). |
| **5. Write droplet receiver** | Automatable | 1 hr | Step 3 | Simple HTTP endpoint on droplet (or direct psql INSERT from Mac script if DATABASE_URL available on Mac) |
| **6. Test extraction** | User + Auto | 30 min | Steps 1-5 | Extract one conversation, verify parsing, verify structured data arrives in cai_inbox, verify Cindy processes it |

**Privacy concern:** The extraction script must be carefully audited. Raw message text processes in-memory on Mac only; only structured summaries travel to the droplet. The CLAUDE.md and whatsapp-parsing skill already document this constraint thoroughly.

**Total effort:** ~5-6 hours
**Dependencies:** None external. iCloud backup already exists. Extraction runs locally on Mac.

### 2.3 Granola (MCP)

**Status:** MCP TOOLS AVAILABLE — Granola MCP tools are visible in the Claude Code environment

Available tools (confirmed from MCP server list):
- `mcp__claude_ai_Granola__list_meetings`
- `mcp__claude_ai_Granola__get_meetings`
- `mcp__claude_ai_Granola__get_meeting_transcript`
- `mcp__claude_ai_Granola__query_granola_meetings`

| Step | Who | Effort | Dependency | Notes |
|------|-----|--------|------------|-------|
| **1. Verify Granola MCP on droplet** | Automatable | 15 min | None | Granola MCP is available in CC on Mac. Need to verify if it's also available on the droplet (where Cindy actually runs). The droplet agent uses `claude` CLI with SDK — MCP tools may not be available in that context. |
| **2. Option A: Granola MCP from CC** | No work | N/A | Step 1 success | If Granola MCP works on droplet, Cindy can poll directly via `list_meetings` / `get_meeting_transcript`. This is the ideal path. |
| **3. Option B: Polling relay from Mac** | Automatable | 2-3 hr | Step 1 failure | If Granola MCP is NOT available on droplet: write a Mac-side polling script that calls Granola API, extracts new transcripts, POSTs to droplet cai_inbox as `cindy_meeting`. Runs via launchd every 30 min. |
| **4. Test end-to-end** | User + Auto | 30 min | Steps 2 or 3 | List recent meetings, get a transcript, verify Cindy processes it |

**Key uncertainty:** Whether Granola MCP is available on the droplet. The droplet runs `claude` agent SDK, not the full CC environment with all MCP servers. This needs investigation.

**Likely outcome:** Granola MCP probably does NOT work on the droplet because it's a Claude.ai integration MCP, not a standalone server. Option B (Mac relay) is more likely needed.

**Total effort:** 30 min (if Option A) or 3-4 hours (if Option B)
**Dependencies:** Granola app must be running on Mac with recent meetings.

### 2.4 Calendar

**Status:** NOT SET UP — Need to decide approach

| Step | Who | Effort | Dependency | Notes |
|------|-----|--------|------------|-------|
| **1. Choose approach** | User decision | 15 min | None | Two options: (A) Google Calendar API with incremental sync, or (B) .ics via AgentMail email |
| **Option A: Google Calendar API** | | | | |
| **A.1 Create Google Cloud project** | User | 20 min | None | Enable Calendar API |
| **A.2 Create OAuth credentials** | User | 30 min | A.1 | Service account or OAuth2 for Aakash's calendar |
| **A.3 Write polling script** | Automatable | 3-4 hr | A.2 | Python script on droplet: uses syncToken incremental sync, polls every 5 min, writes events to cai_inbox as `cindy_calendar`. Stores syncToken in state file. |
| **A.4 Set up systemd timer** | Automatable | 15 min | A.3 | 5-minute polling interval |
| **A.5 Test** | User + Auto | 30 min | A.1-A.4 | Create test event, verify poll picks it up, verify Cindy processes it |
| **Option B: .ics via AgentMail** | | | | |
| **B.1 Forward calendar invites** | User | 5 min | AgentMail setup | Configure email client to auto-forward .ics attachments to Cindy |
| **B.2 Enhance email listener** | Automatable | 1 hr | Email setup | Add .ics detection and parsing to the WebSocket listener (uses `icalendar` library) |
| **B.3 Test** | User + Auto | 15 min | B.1-B.2 | Send calendar invite, verify parsing, verify Cindy creates calendar interaction |

**Recommendation:** Option A (Google Calendar API) is the correct approach. It provides:
- Full event coverage (not just invites forwarded)
- Incremental sync (only changed events)
- Attendee response status
- Cancelled event detection
- The anchor surface for gap detection NEEDS comprehensive calendar access

Option B is a supplement, not a replacement — it catches .ics invites in emails but misses directly-created events.

**Total effort:** Option A: ~5-6 hours + 30 min user setup. Option B: ~1.5 hours (but incomplete).

---

## 3. Missing Components (Not Surface-Specific)

### 3.1 Auto Embeddings for Interactions Table

The `interactions` table has the `embedding` column and `embedding_input` auto-populate trigger, but is **missing the `queue_embeddings` trigger** that sends embedding jobs to the pgmq queue. Other tables (content_digests, thesis_threads, actions_queue, companies, network, portfolio) all have this trigger.

**Fix:** Add the queue_embeddings trigger:
```sql
CREATE TRIGGER queue_interactions_embedding
  AFTER INSERT OR UPDATE OF embedding_input ON interactions
  FOR EACH ROW
  EXECUTE FUNCTION queue_embeddings('populate_interactions_embedding_input', 'embedding');
```
Or use the Supabase Auto Embeddings configuration approach (the `cir_interactions` trigger suggests Supabase CIR is already configured, but the embedding pipeline is not wired up).

**Effort:** 15 min (single SQL migration)

### 3.2 IVFFlat Index Rebuild

The IVFFlat index `idx_interactions_embedding` was created on an empty table. IVFFlat indexes need data to build effective clusters. After the first batch of interactions (50+ rows), the index should be rebuilt:
```sql
REINDEX INDEX idx_interactions_embedding;
```

**Effort:** 5 min (automated, run after first data load)

### 3.3 Cindy Skills Deployment to Droplet

The skills files exist at `mcp-servers/agents/skills/cindy/` in the Mac repo. These need to be deployed to the droplet (at `/opt/agents/skills/cindy/`) via `deploy.sh`.

**Effort:** Already handled by existing `deploy.sh` (it syncs the entire `mcp-servers/agents/` directory). Just needs to be run.

---

## 4. What the USER Must Do (Cannot Be Automated)

| # | Action | Effort | Blocking? |
|---|--------|--------|-----------|
| 1 | **Create AgentMail account** ($20/month) | 10 min | YES — blocks email surface |
| 2 | **Create Cindy inbox** (e.g., `cindy@agent.aicos.ai`) | 5 min | YES — blocks email surface |
| 3 | **Configure email forwarding** to CC Cindy | 5 min | YES — blocks email surface |
| 4 | **Decide Calendar approach** (Google Calendar API vs .ics only) | 5 min | YES — blocks calendar surface |
| 5 | **Create Google Cloud project + Calendar API credentials** (if Option A) | 30 min | YES — blocks calendar surface |
| 6 | **Verify iCloud backup** contains recent WhatsApp data | 5 min | Partially — WhatsApp dir exists, need to confirm sqlite freshness |

---

## 5. What Can Be Automated (Claude Code / Scripts)

| # | Action | Effort | Dependency |
|---|--------|--------|------------|
| 1 | **Write AgentMail WebSocket listener** (droplet systemd service) | 2-3 hr | AgentMail account |
| 2 | **Write WhatsApp extraction script** (Mac, launchd) | 3-4 hr | None |
| 3 | **Write Calendar API polling script** (droplet systemd timer) | 3-4 hr | Google credentials |
| 4 | **Write Granola relay script** (Mac, launchd) — if MCP not on droplet | 2-3 hr | Granola MCP status |
| 5 | **Add interactions embedding trigger** (SQL migration) | 15 min | None |
| 6 | **Deploy Cindy to droplet** (`deploy.sh`) | 5 min | None |
| 7 | **Install Python packages** (`icalendar` on droplet, `whatsapp-chat-exporter` on Mac) | 10 min | None |

---

## 6. Recommended Activation Order

### Phase 1: Foundation (can start immediately)
1. **Deploy Cindy to droplet** — run `deploy.sh` to sync all files including skills
2. **Add interactions embedding trigger** — single SQL migration
3. **Install Python packages** on Mac and droplet
4. **Verify Granola MCP on droplet** — determines Option A vs B for Granola

### Phase 2: Granola (easiest surface, highest value)
- **Why first:** Granola transcripts are the richest single source (0.35 weight in context richness). MCP tools may already work.
- **Steps:** Test Granola MCP on droplet -> if works, just trigger `cindy_granola_poll`; if not, write Mac relay script.
- **Effort:** 30 min to 3 hr depending on MCP availability

### Phase 3: Email (AgentMail)
- **Why second:** Email is the second-most-connected surface. AgentMail provides the cleanest integration (WebSocket push, auto-threading, Talon quote stripping).
- **Steps:** User creates account -> write WebSocket listener -> configure forwarding -> test
- **Effort:** ~3-4 hr + user actions

### Phase 4: Calendar (Google Calendar API)
- **Why third:** Calendar is the anchor surface for gap detection, but gap detection is only valuable once Granola + Email are flowing (otherwise every meeting shows as a gap).
- **Steps:** User creates credentials -> write polling script -> test
- **Effort:** ~5-6 hr + user actions

### Phase 5: WhatsApp (iCloud Extraction)
- **Why last:** Lowest weight in context richness (0.15). Most complex extraction (iCloud backup, Core Data timestamps, privacy constraints). Also carries the highest privacy risk.
- **Steps:** Verify iCloud backup -> write extraction script -> set up cron -> test
- **Effort:** ~5-6 hr

---

## 7. Total Effort Summary

| Category | Effort |
|----------|--------|
| **User actions** | ~1 hour (accounts, credentials, decisions) |
| **Automated scripts** | ~12-16 hours (4 surface integrations + infra) |
| **Testing** | ~2 hours |
| **Total to full operation** | ~15-19 hours |

### Minimum Viable Cindy (1 surface operational)

**Granola only:** Deploy + test MCP = 30 min to 3 hr. Cindy can immediately start processing meeting transcripts, extracting action items, thesis signals, and linking people. No external accounts needed.

---

## 8. Verification Checklist Summary

| Item | Status |
|------|--------|
| lifecycle.py AST | PASS |
| Cindy functions in lifecycle.py | PASS |
| Bridge tool registration | PASS |
| Orchestrator routing (CLAUDE.md) | PASS |
| Cindy CLAUDE.md (4 surfaces) | PASS |
| Cindy CLAUDE.md (obligation detection / signals) | PASS |
| Cindy CLAUDE.md (anti-patterns: 20 rules) | PASS |
| Cindy CLAUDE.md (privacy rules) | PASS |
| Cindy CLAUDE.md (ACK protocol) | PASS |
| Cindy hooks (Stop, UserPromptSubmit, PreCompact) | PASS |
| Cindy skills (4 files) | PASS |
| Schema: interactions table | PASS |
| Schema: context_gaps table | PASS |
| Schema: people_interactions table | PASS |
| Schema: network ALTER columns | PASS |
| Schema: interactions_public view | PASS |
| Indexes (14) | PASS |
| Triggers (5) | PASS |
| Functions (4 Cindy-specific) | PASS |
| Auto Embeddings trigger for interactions | **FAIL** — missing queue_embeddings trigger |
| Data: interactions table | 0 rows (expected — never run) |
| WhatsApp iCloud backup directory | EXISTS (account 919820820663) |
| Python packages (Mac): whatsapp-chat-exporter, icalendar | NOT INSTALLED |
| AgentMail account | NOT CREATED |
| Google Calendar API credentials | NOT CREATED |
| Granola MCP on droplet | UNKNOWN — needs verification |
