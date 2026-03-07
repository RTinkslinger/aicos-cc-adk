# AI Chief of Staff — Architecture v0.3
**March 2026 · Updated from v0.2 to reflect Claude Code era build-out**

> **Currency note (2026-03-07):** Some sections of this document have drifted from live state. For the most current and accurate reference, see `docs/source-of-truth/` — particularly ARCHITECTURE.md, MCP-TOOLS-INVENTORY.md, and SYSTEM-STATE.md. Key differences: SyncAgent is now LIVE (10-min cron), 17 MCP tools exist (not 4), Postgres has 7 live tables (not 2), and Data Sovereignty Phases 1-4 are complete.

> Evolved from the Cowork handover architecture (v0.2). Preserves the Three-Layer vision while updating all details for current implementation reality. Original v0.2 preserved in `From Clowork handover (sessino 40 in cowork)/`.

---

## Overview — Three-Layer Architecture

The AI CoS organises into three layers: **Observation** (everything that feeds the system), **Intelligence** (Agent SDK runners + MCP tools that reason over data), and **Action/Interface** (how Aakash interacts and how the system closes gaps). All three layers read and write from a shared **State layer** — a hybrid of Notion (source of truth for human-managed fields) and Postgres on the droplet (source of truth for machine-speed operations, preference store, and agent-generated enrichments). Field-level ownership between Notion and droplet is defined in `DATA-SOVEREIGNTY.md`.

> **Naming note:** CONTEXT.md uses "Observation → Intelligence → Action (The Plumbing)". Vision-v3 used "Signal Processor → Intelligence Engine → Operating Interface". This document uses "Observation → Intelligence → Interface" with the Action layer subsumed into Intelligence (Agent SDK runners close gaps autonomously) and Interface (how outputs surface to Aakash).

**Core principle:** Claude mobile is always the primary conversational interface. Agent SDK runners enrich the underlying state continuously so that when Aakash asks "what's next?", Claude is reasoning over rich, current, preference-calibrated data — not a stale snapshot.

**The learning loop is the point.** Every accept/reject decision feeds the preference store. Every Agent SDK reasoning session reads the preference store before proposing actions. After 6 months the system is measurably better at predicting what Aakash will act on than after 6 days. This compounding is the AI CoS vision — not just smart pipelines.

---

## Layer 1 — Observation

Everything that feeds signal into the system. All inputs route to the Intelligence layer for processing. Each signal source produces a normalized Signal:

```typescript
interface Signal {
  source: "youtube" | "granola" | "email" | "whatsapp" | "social" | "research";
  content: string;           // raw content / transcript
  entities: {
    people: string[];
    companies: string[];
    topics: string[];
  };
  metadata: Record<string, any>;
  timestamp: string;
}
```

| Source | Trigger | Signal Type | Status | Notes |
|--------|---------|-------------|--------|-------|
| YouTube / RSS | Droplet cron every 5 min + on-demand `yt` CLI | Content → thesis signals | ✅ Live (autonomous) | Full pipeline on droplet: yt-dlp extraction → ContentAgent → publish → Notion writes. Cookies refreshed from Safari every 1-2 weeks. |
| Granola | Granola MCP (query/transcript) | Meeting signals, IDS updates, commitments | ✅ MCP connected | 7-8 meetings/day. `query_granola_meetings`, `get_meeting_transcript`. Processing pipeline not yet automated. |
| Notion | Enhanced Connector MCP + Raw API | Action outcomes, manual edits, status changes | ✅ Live | Source of truth for human-managed structured data. 8 databases mapped. |
| digest.wiki UI | User interaction (accept/reject) | Revealed preferences | ✅ Live (partial) | Currently surfaces content digests; accept/reject UX planned for Action Frontend. |
| Calendar | Google Calendar MCP | Location + schedule context | ✅ MCP connected | Powers geographic overlap factor in People Scoring Model |
| Email | Gmail MCP | Founder updates, investor comms, intro requests | ✅ MCP connected | Not yet processed by agents — raw access only |
| X / LinkedIn | Manual trigger (URL/screenshot drop) | Thesis signals, network signals | 🔜 Manual only | No clean API. IngestAgent (future) will process these. |
| Profile screenshots | Manual trigger (image drop) | New network nodes | 🔜 Manual only | Vision extraction → Notion Network DB entry |
| WhatsApp | Future | Response signals, async communication | 🔜 Future | Primary communication channel but no API integration yet |

**Key principle: Same Brain, Different Eyes.** The Intelligence Engine doesn't care WHERE the signal came from. It runs the same flow for all sources: match → retrieve context → analyze → score impact → generate actions → present.

---

## Layer 2 — Intelligence

### 2a. Runners — One Orchestrator, Specialist Subagents

The pattern: specialist runners handle specific signal types. Each is a focused Python script calling MCP tools and/or the Claude API directly. The ContentAgent is live and autonomous; others are planned.

#### ContentAgent ✅ LIVE
- **Location:** `mcp-servers/ai-cos-mcp/runners/content_agent.py`
- **Trigger:** New content item in `queue/` (YouTube JSON). Unified pipeline runs via droplet cron every 5 min.
- **Reads:** Thesis threads from Notion Thesis Tracker (including open key questions), portfolio company profiles from Companies DB, preference history, CONTEXT.md domain context
- **Does:** Calls Claude API with structured prompt (`runners/prompts/content_analysis.md`). Produces DigestData JSON: thesis connections with conviction assessments, portfolio connections with actions, contra signals, rabbit holes, proposed actions scored against 7-factor model. Creates new thesis threads autonomously.
- **Writes:** Content Digest DB entry (20+ fields), proposed actions to Actions Queue (with company lookup, scoring, thesis connections), thesis evidence updates to Thesis Tracker (conviction changes, key questions lifecycle), new thesis threads at Conviction="New". Publishes digest JSON to digest.wiki repo.
- **Pipeline:** `extraction.py` (yt-dlp) → `content_agent.py` (Claude analysis) → `publishing.py` (Notion writes + digest.wiki publish + git push + Vercel deploy)

#### PostMeetingAgent 🔜 PLANNED
- **Trigger:** New Granola transcript detected (poll via `list_meetings` or webhook)
- **Reads:** Existing IDS notes (Companies DB), preference store history, Network DB (who was in meeting), Thesis Tracker (active threads)
- **Does:** Extract IDS signals (using IDS notation: +, ++, ?, ??, +?, -), update conviction trail, detect open commitments, identify new people for Network DB, score follow-up actions
- **Writes:** IDS updates to Companies DB, new contacts to Network DB, proposed actions to Actions Queue (Source = "Meeting"), thesis evidence to Thesis Tracker
- **Why not cron:** "What did this meeting change?" requires reasoning over prior context. Claude needs to check existing IDS notes, cross-reference signals, assess conviction delta.

#### OptimiserAgent 🔜 PLANNED
- **Trigger:** Nightly cron + on-demand from Claude mobile ("what's next?")
- **Reads:** Full Network DB (400+ contacts), Calendar (location signals), preference store, Actions Queue (history + pending), Companies DB (funnel states, conviction levels), Thesis Tracker, relationship temperature signals
- **Does:** Re-score full action queue using Action Scoring Model, surface dormant connections, "best person to meet today in SF" reasoning, identify network gaps vs thesis needs, flag conviction changes, gap analysis ("you're underweighting bucket 2")
- **Key outputs:** Prioritized action triage (daily), meeting optimization (weekly/trip), slot filling (real-time), gap analysis (periodic)

#### IngestAgent 🔜 PLANNED
- **Trigger:** Manual (screenshot drop, X/LinkedIn URL)
- **Does:** Profile screenshot → structured Network DB entry (vision extraction). Post URL → thesis signal extraction. New person → relationship edges inferred from shared companies/contexts.
- **Future:** When X/LinkedIn APIs or MCPs become available, this becomes a continuous observer.

#### SyncAgent ✅ LIVE
- **Location:** `mcp-servers/ai-cos-mcp/runners/sync_agent.py`
- **Trigger:** Cron every 10 min on droplet
- **Does:** Thesis status sync (Notion → Postgres), actions bidirectional sync (Outcome from Notion), retry queue drain (exponential backoff), change detection (field-level diffs → `change_events` table), action generation from changes (conviction→High, status changes, Gold outcomes).
- **Also running:** Back-propagation sweep (Actions Queue Done → Content Digest "Actions Taken") as part of unified pipeline (5-min cron).

---

### 2b. MCP Server — The Shared Tool Layer ✅ LIVE

The `ai-cos-mcp` server is live on the DO droplet as a systemd service. FastMCP Python. Connected via Tailscale from all Claude surfaces.

**17 live tools** (full inventory in `docs/source-of-truth/MCP-TOOLS-INVENTORY.md`):

| Category | Tools |
|----------|-------|
| Health | `health_check` |
| Context | `cos_load_context` |
| Scoring | `cos_score_action`, `cos_get_preferences` |
| Thesis CRUD | `cos_create_thesis_thread`, `cos_update_thesis`, `cos_get_thesis_threads` |
| Data Access | `cos_get_recent_digests`, `cos_get_actions` |
| Sync Ops | `cos_sync_thesis_status`, `cos_seed_thesis_db`, `cos_retry_sync_queue`, `cos_sync_actions`, `cos_full_sync` |
| Observability | `cos_get_changes`, `cos_sync_status`, `cos_process_changes` |

**Planned tools (not yet built):**

| Tool Group | Tools | Used By |
|-----------|-------|---------|
| Network | `cos_get_person()`, `cos_get_company()`, `cos_search_network()`, `cos_best_meetings_today()`, `cos_relationship_temp(person)` | OptimiserAgent, Claude mobile |
| Retrieval | `cos_search()` — semantic over Postgres + vector DB (when available) | All runners, Claude mobile |
| Ingest | `cos_process_screenshot()`, `cos_process_post()` | IngestAgent, Claude mobile triggers |

**Existing MCP tools (connected per surface):** Notion Enhanced Connector, Notion Raw API, Granola MCP, Google Calendar MCP, Gmail MCP, Vercel MCP, PDF Tools. The `ai-cos-mcp` server complements these with cross-cutting AI CoS logic.

---

## Layer 3 — State

### Hybrid: Notion + Postgres (Field-Level Ownership)

Data sovereignty follows `DATA-SOVEREIGNTY.md`. Notion is the human interface; the droplet is the brain. For shared databases (Companies, Network, Portfolio), Notion owns human-managed fields (company name, deal status, sector, contact info) and the droplet owns enriched fields (agent IDS notes, computed scores, historical signals).

**Notion databases (8 mapped):**

| Database | Data Source ID | Key Role |
|----------|---------------|----------|
| Network DB | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` | People: 13 archetypes, IDS notes, relationship status |
| Companies DB | `1edda9cc-df8b-41e1-9c08-22971495aa43` | IDS repository, deal status 3D matrix, thesis alignment |
| Portfolio DB | `4dba9b7f-e623-41a5-9cb7-2af5976280ee` | Investment tracking, follow-on scoring, financial rollups. Hidden `Company Name` relation to Companies DB. |
| Actions Queue | `1df4858c-6629-4283-b31d-50c5e7ef885d` | Single action sink: Status (Proposed→Accepted→Done/Dismissed). Bidirectional sync. |
| Content Digest DB | `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` | AI-analyzed content with thesis/portfolio connections. SoT: Droplet. |
| Thesis Tracker | `3c8d1a34-e723-4fb1-be28-727777c22ec6` | AI-managed conviction engine (see below). SoT: Notion (AI-managed). |
| Build Roadmap | `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` | Product roadmap: 7-state kanban, parallel safety, dependencies |
| Tasks Tracker | `1b829bcc-b6fc-80fc-9da8-000b4927455b` | Pipeline/portfolio tasks with company/person relations |

### Thesis Tracker — AI-Managed Conviction Engine

The Thesis Tracker is not a passive database — it's an AI-managed conviction engine. All fields are written by AI except Status (human-only: Active / Exploring / Parked / Archived).

**Conviction Spectrum (6 levels, two axes):**
- Maturity axis: **New** → **Evolving** → **Evolving Fast** (thesis still forming, evidence accumulating)
- Strength axis: **Low** → **Medium** → **High** (well-formed thesis, assessed on evidence base)

**AI writes:** Thread Name, Conviction, Core Thesis, Key Questions (as `[OPEN]`/`[ANSWERED]` page content blocks), Evidence For/Against (IDS notation: + for, ? against), Investment Implications, Key Companies, Connected Buckets, Discovery Source.

**Key Questions lifecycle:** Formulated as critical questions that would move conviction up or down. Stored as page content blocks with `[OPEN]` prefix. When evidence answers a question, marked `[ANSWERED]` with evidence citation. This lifecycle is automated by ContentAgent.

**Multiple write surfaces:** ContentAgent (autonomous), Claude.ai (manual), Claude Code (manual). All write through ai-cos-mcp tools on the droplet (write-ahead to Postgres, then push to Notion). The droplet is the single write authority.

### Postgres on Droplet ✅ LIVE

Core machine-speed tables are live on the DO droplet:

| Table | Status | Description |
|-------|--------|-------------|
| `action_outcomes` | ✅ Live | THE preference store. Every accept/reject with scoring factor snapshots. |
| `thesis_threads` | ✅ Live | Postgres backing for Thesis Tracker. Write-ahead pattern. |
| `actions_queue` | ✅ Live | Postgres backing for Actions Queue. Bidirectional sync. |
| `sync_queue` | ✅ Live | Failed Notion writes queued for retry (exponential backoff). |
| `change_events` | ✅ Live | Field-level change log from sync detection. |
| `companies` | Schema only | Postgres mirror schema exists. Sync deferred (Phase 5). |
| `network` | Schema only | Postgres mirror schema exists. Sync deferred (Phase 5). |

### Preference Store Schema (action_outcomes) ✅ LIVE

```sql
CREATE TABLE action_outcomes (
    id            SERIAL PRIMARY KEY,
    action_id     TEXT NOT NULL,
    action_type   TEXT NOT NULL,
    company_id    TEXT,
    person_id     TEXT,
    proposed_at   TIMESTAMPTZ NOT NULL,
    decided_at    TIMESTAMPTZ,
    decision      TEXT CHECK (decision IN ('accepted','dismissed','deferred','expired')),
    proposed_score    REAL,
    scoring_factors   JSONB,
    context_snapshot  JSONB,
    feedback_note TEXT,
    source_signal TEXT
);
```

**How learning works:** Every reasoning session calls `cos_get_preferences()` before reasoning. Claude sees structured history: "last 12 research actions rejected", "every intro action for Agentic AI thesis accepted", "P2 Agent-assigned research has 10% follow-through". It calibrates proposals accordingly. No ML training required — just structured history injected into context.

### Vector / Semantic Search Layer — Correctly Deferred

**Build strategy:** Start with LLM-as-matcher (Notion + company index in the prompt). Add vector DB when triggered by: second signal source (Granola active processing), 500+ companies, or need for sub-second retrieval. None of these triggers have fired yet.

**Reference architecture:** pgvector on Postgres. Designed to be swappable — sits behind `cos_search()` in the MCP layer.

---

### Network Graph Schema — As It Exists in Notion Today

#### Network DB (40+ fields, 13 archetypes)

**Archetypes:** Founder, DF (Domain Fighter), CXO, Operator, Angel, Collective Member, LP, Academic, Journalist, Government, Advisor, EXT Target, Other

**Key fields:**
- **Identity:** Person Name, Archetype (select from 13), Company (text/relation), Role, LinkedIn URL, Email, Phone, City
- **IDS State:** IDS Notes (rich text — contains the full IDS trail), Relationship Status, Last Interaction (date), Source (how they entered the network)
- **DeVC Context:** Collective Status (for Collective Member archetype), Fund Context (Z47/DeVC/Both)

#### Companies DB (49 fields)

**Key fields:**
- **Identity:** Company Name, Sector, Stage, Website, Description
- **IDS Repository:** Company pages contain the full IDS trail. The Companies DB IS the IDS database.
- **Deal Status 3D:** Combines pipeline stage × conviction × active/inactive.
- **Scoring:** Spiky Score (7 criteria × 1.0), EO/FMF/Thesis/Price scores (4 categories × /10)
- **Relations:** Founders (relation to Network DB), Team Notes, JTBD

#### Portfolio DB (94 fields)

**Key fields:**
- **Investment:** Fund, vintage, Money In, ownership, valuation
- **EF/EO:** Entrepreneurial Fire / Entrepreneurial Orientation formalized scoring
- **Financial:** Rollup structure linking to Finance DB
- **Follow-on:** Follow-on tracking, follow-on scoring criteria
- **Relations:** Company Name (hidden relation to Companies DB), Founders

#### Relationship Temperature Model

Not a separate model — it's the `relationship_temp` factor within the People Scoring Model (9 factors). Composite signal:

```
Relationship Temperature = f(
    last_interaction_recency,    — days since last meeting/call/meaningful exchange
    interaction_frequency,       — meetings per quarter (rolling 6 months)
    mutual_active_connections,   — shared people in Network DB who are active
    open_commitments,           — pending actions in Actions Queue involving this person
    communication_direction,    — who initiates? balanced vs one-sided
    response_latency            — how quickly do they respond to outreach?
)
```

**Temperature scale:** Hot (active, <2 weeks) → Warm (responsive, 2-8 weeks) → Cool (no interaction 2-6 months) → Cold (>6 months, requires re-introduction).

**Implementation path:** Phase 1 = recency-only from Notion Last Interaction field. Phase 2 = frequency from Granola MCP `list_meetings` history. Phase 3 = full model when messaging integrations land.

---

## DeVC Collective — Graph + Funnel

### Deal Flow Funnel

| Stage | Description | Key Actions | Transition Trigger |
|-------|-------------|-------------|-------------------|
| **TOFU** | Sourced via VCs, MPI + team, 1:Many channels | Background research, initial screening | Aakash + Mohit meeting scheduled |
| **MOFU** | Aakash + Mohit meeting completed | IDS evaluation begins, follow-up meetings, IDS Q progression | MPI Eval completed |
| **BOFU** | MPI Eval complete | If positive → auto-commit. If negative → full IDS review. IC prep, term sheet. | Investment decision (close or pass) |

### Collective Member Lifecycle

```
Prospect → Engaged → Signed → Active → Dormant
```

Collective members are people nodes in Network DB with `Archetype = Collective Member`. `Collective Status` field tracks pipeline state. OptimiserAgent (when live) will query collective member nodes when scoring intro opportunities.

---

## Impact Score / Action Scoring

The "impact score" IS the Action Scoring Model. There is no separate impact score.

### Action Scoring Model (7 Factors)

```
Action Score = f(
    bucket_impact,                  — Which of the 4 priority buckets does this serve?
    conviction_change_potential,    — Could this move investment conviction?
    key_question_relevance,         — Does this address an open Key Question?
    time_sensitivity,               — Is there a reason to act NOW?
    action_novelty,                 — New information vs redundant?
    stakeholder_priority,           — How important is the person/company involved?
    effort_vs_impact                — Time cost vs expected value?
)
```

**Thresholds:** ≥7 surface, 4-6 low-confidence tag, <4 context enrichment only.

**Implementation:** `scripts/action_scorer.py` (172 lines). Not yet wired into Content Pipeline — next integration step.

### People Scoring Model (Subset for Meeting-Type Actions)

```
Person Score = f(
    bucket_relevance, current_ids_state, time_sensitivity,
    info_gain_potential, network_multiplier, thesis_intersection,
    relationship_temp, geographic_overlap, opportunity_cost
)
```

**Composite Score:** `weighted_sum(bucket_scores) × urgency_multiplier × geographic_overlap × relationship_trajectory`

---

## Layer 4 — Interface

| Surface | Primary Use | Powered By | Proactive? | Status |
|---------|------------|------------|-----------|--------|
| Claude mobile | Conversational queries, "what's next?", trigger runners | MCP over Notion/Postgres state | No — Aakash initiates | ✅ Live |
| Claude desktop | Same as mobile, larger context window | MCP over Notion/Postgres state | No | ✅ Live |
| digest.wiki | Browse content digests, future: accept/reject actions | Vercel SSG → JSON data, future: Postgres API | No | ✅ Live |
| Notion | Action queue triage, thesis notes, build roadmap, IDS trail | Direct Notion + runner syncs | No | ✅ Live |
| Claude Code | Primary build surface, hooks, CLAUDE.md, subagents, Tailscale to droplet | CLI + hooks + Tailscale | No | ✅ Primary |
| WhatsApp | Proactive push summaries from runners | Agent SDK runner → Twilio/WA API | **YES** | 🔜 Future |

---

## Known Gaps — Remaining

### Technical Decisions Deferred
- **Vector DB final choice** — pgvector vs alternatives. Trigger: 2nd signal source active, 500+ companies, or sub-second retrieval need. None fired yet.
- **Graph traversal depth** — Postgres FK joins handles most cases. Evaluate Neo4j if 2-3 hop queries become complex.
- **X / LinkedIn ingestion** — No clean API. Profile screenshots via vision is current path.
- **Granola auto-processing** — Granola MCP provides access. Question: should PostMeetingAgent poll `list_meetings` on cron, or does Granola support webhooks?
- **WhatsApp output channel** — Twilio or WhatsApp Business API. Priority rises when OptimiserAgent is live.
- **action_scorer.py integration** — Exists (172 lines) but not wired into Content Pipeline scoring flow.

### Resolved Since v0.2
- ~~Cowork deprecation timing~~ — Fully deprecated. Claude Code is primary build surface.
- ~~MCP server deployment~~ — Live on droplet as systemd service.
- ~~Postgres infrastructure~~ — Live on droplet.
- ~~Preference Store~~ — `action_outcomes` table exists.
- ~~Thesis Tracker design~~ — AI-managed conviction engine implemented.
- ~~ContentAgent autonomy~~ — Runs autonomously on droplet every 5 min.

---

## Build Phasing (Updated)

| Phase | What Gets Built | Status |
|-------|----------------|--------|
| **Phase 1 — MCP + Preference Foundation** | Custom `ai-cos-mcp` server on droplet ✅. Postgres with action_outcomes ✅. ContentAgent autonomous ✅. Thesis Tracker conviction engine ✅. Wire `action_scorer.py` into pipeline. Expand MCP tools. | **~70% Complete** |
| **Phase 2 — Action Frontend** | Accept/dismiss on digest pages. Consolidated `/actions` route on digest.wiki. Portfolio dashboard view. Thesis tracker view with evidence feed. | **Not started** |
| **Phase 3 — Autonomous Runners** | PostMeetingAgent (Granola → IDS → actions). SyncAgent ✅ (live, 10-min cron). IngestAgent (screenshots, URLs → DB). | **SyncAgent done, others not started** |
| **Phase 4 — Optimisation + Scale** | OptimiserAgent. `cos_best_meetings_today()`. Relationship temperature scoring. Gap analysis. WhatsApp output. Vector DB (if triggered). | **Not started** |

---

## Full Architecture Diagram (Text)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OBSERVATION LAYER (Signal Sources)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Granola MCP     Notion MCP      YouTube/RSS ✅   Calendar MCP
Gmail MCP       digest.wiki     X/LinkedIn(🔜)  WhatsApp(🔜)
Screenshots     Apple Notes
               ↓ normalized Signals
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTELLIGENCE LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ContentAgent ✅     PostMeetingAgent(🔜)   OptimiserAgent(🔜)
IngestAgent(🔜)     SyncAgent(🔜)
    ↑ reads preference store before every reasoning session
               ↓ all call
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL LAYER — ai-cos-mcp ✅ + existing MCPs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cos_load_context ✅  cos_get_preferences ✅
cos_score_action ✅  health_check ✅
cos_search(🔜)       cos_best_meetings_today(🔜)
cos_log_outcome(🔜)  cos_relationship_temp(🔜)
               ↓ reads/writes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATE LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Notion (8 DBs — human interface, SoT for human fields)
Postgres ✅ (action_outcomes, content pipeline data)
Thesis Tracker ✅ (AI-managed conviction engine)
Vector DB (🔜 when triggered)

DATA-SOVEREIGNTY.md defines field-level ownership
               ↓ surfaces to
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERFACE LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Claude mobile    digest.wiki ✅  Notion ✅
Claude Code ✅   WhatsApp(🔜)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ↻ LEARNING LOOP
    accept/reject → action_outcomes ✅
    → preference injection → better proposals
    → compound over time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
