# AI Chief of Staff — Architecture v0.2 (Enhanced)
**March 2026 · Directional Draft → Corrected against CONTEXT.md + CLAUDE.md + Vision Docs v1-v3**
> Original was a memory-only draft. This version: all 🔴 gaps filled, Attio references removed (Notion is the data layer), layer naming aligned with ground truth, schemas populated from actual Notion field inventory.

---

## Overview — Three-Layer Architecture

The AI CoS organises into three layers: **Observation** (everything that feeds the system), **Intelligence** (Agent SDK runners + MCP tools that reason over data), and **Action/Interface** (how Aakash interacts and how the system closes gaps). All three layers read and write from a shared **State layer** — currently Notion as source of truth for both machine and human operations, migrating to Postgres for machine-speed operations with Notion as the human UI layer.

> **Naming note:** CONTEXT.md uses "Observation → Intelligence → Action (The Plumbing)". Vision-v3 uses "Signal Processor → Intelligence Engine → Operating Interface". This document uses "Observation → Intelligence → Interface" with the Action layer subsumed into Intelligence (Agent SDK runners close gaps autonomously) and Interface (how outputs surface to Aakash).

**Core principle:** Claude mobile is always the primary conversational interface. Agent SDK runners enrich the underlying state continuously so that when Aakash asks "what's next?", Claude is reasoning over rich, current, preference-calibrated data — not a stale snapshot.

**The learning loop is the point.** Every accept/reject decision feeds the preference store. Every Agent SDK reasoning session reads the preference store before proposing actions. After 6 months the system is measurably better at predicting what Aakash will act on than after 6 days. This compounding is the AI CoS vision — not just smart pipelines.

---

## Layer 1 — Observation

Everything that feeds signal into the system. All inputs route to the Intelligence layer for processing. Each signal source produces a normalized Signal (per vision-v3):

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
| Granola | Granola MCP (query/transcript) | Meeting signals, IDS updates, commitments | ✅ MCP connected | 7-8 meetings/day. `query_granola_meetings`, `get_meeting_transcript` |
| YouTube / RSS | Cron 8:30 PM IST (launchd) + on-demand `yt` CLI | Content → thesis signals | ✅ Live (Content Pipeline v4) | Feeds ContentAgent pipeline. Daily scheduled task at 9 PM. |
| Notion | Enhanced Connector MCP + Raw API | Action outcomes, manual edits, status changes | ✅ Live | Source of truth for structured data. 8 databases mapped. |
| digest.wiki UI | User interaction (accept/reject) | Revealed preferences | ✅ Live (partial) | Currently surfaces content; accept/reject wiring = preference store input. |
| Calendar | Google Calendar MCP | Location + schedule context | ✅ MCP connected | Powers geographic overlap factor in People Scoring Model |
| Email | Gmail MCP | Founder updates, investor comms, intro requests | ✅ MCP connected | Not yet processed by agents — raw access only |
| X / LinkedIn | Manual trigger (URL/screenshot drop) | Thesis signals, network signals | 🔜 Manual only | No clean API. Explorium MCP provides some enrichment. IngestAgent (future). |
| Profile screenshots | Manual trigger (image drop) | New network nodes | 🔜 Manual only | Vision extraction → Notion Network DB entry |
| WhatsApp | Future | Response signals, async communication | 🔜 Future | Primary communication channel but no API integration yet |

**Key principle (vision-v3): Same Brain, Different Eyes.** The Intelligence Engine doesn't care WHERE the signal came from. It runs the same flow for all sources: match → retrieve context → analyze → score impact → generate actions → present.

---

## Layer 2 — Intelligence

### 2a. Agent SDK — One Orchestrator, Specialist Subagents

Single `AiCosOrchestrator` as entry point. Spawns specialist subagents based on trigger type. Mirrors the existing Cowork subagent pattern (Content Pipeline v4 already uses orchestrator + parallel Task subagents). Each subagent is 50-100 lines of Python calling MCP tools.

#### PostMeetingAgent
- **Trigger:** New Granola transcript detected (poll via `list_meetings` or webhook)
- **Reads:** Existing IDS notes (Companies DB), preference store history, Network DB (who was in meeting), Thesis Tracker (active threads)
- **Does:** Extract IDS signals (using IDS notation: +, ++, ?, ??, +?, -), update conviction trail, detect open commitments, identify new people for Network DB, score follow-up actions using Action Scoring Model (7 factors → threshold ≥7/4-6/<4)
- **Writes:** IDS updates to Companies DB, new contacts to Network DB, proposed actions to Actions Queue (Source = "Meeting"), thesis evidence to Thesis Tracker
- **Why Agent SDK not cron:** "What did this meeting change?" requires reasoning over prior context. Claude needs to check existing IDS notes, cross-reference signals, assess conviction delta. Intermediate lookups change the output.

#### ContentAgent
- **Trigger:** New content item in queue (currently YouTube JSON in `queue/`)
- **Reads:** Thesis threads (Thesis Tracker), portfolio company profiles (Companies DB + `portfolio-research/*.md`), preference store (what content actions get accepted), previous Content Digests (net newness baseline)
- **Does:** Summarise content, score against thesis threads, find portfolio connections, find network connections, propose actions calibrated to preference history, generate digest JSON for digest.wiki
- **Writes:** Content Digest DB entry, proposed actions to Actions Queue (Source = "Content Pipeline", with Source Digest relation), thesis evidence updates to Thesis Tracker
- **Current state:** This is Content Pipeline v4, already running as Cowork orchestrator + parallel subagents. Agent SDK version = same logic, autonomous execution.

#### OptimiserAgent
- **Trigger:** Nightly cron + on-demand from Claude mobile ("what's next?")
- **Reads:** Full Network DB (400+ contacts), Calendar (location signals), preference store, Actions Queue (history + pending), Companies DB (funnel states, conviction levels), Thesis Tracker, relationship temperature signals
- **Does:** Re-score full action queue using Action Scoring Model, surface dormant connections, "best person to meet today in SF" reasoning, identify network gaps vs thesis needs, flag conviction changes, gap analysis ("you're underweighting bucket 2")
- **Key outputs:** Prioritized action triage (daily), meeting optimization (weekly/trip), slot filling (real-time), gap analysis (periodic)

#### IngestAgent
- **Trigger:** Manual (screenshot drop, X/LinkedIn URL)
- **Does:** Profile screenshot → structured Network DB entry (vision extraction). Post URL → thesis signal extraction. New person → relationship edges inferred from shared companies/contexts.
- **Future:** When X/LinkedIn APIs or MCPs become available, this becomes a continuous observer.

#### SyncAgent
- **Trigger:** Cron every 2hr (or event-driven)
- **Does:** Notion ↔ Postgres sync (when Postgres is live), Content Digest DB state contract enforcement (Pending → Reviewed → Actions Taken back-propagation), preference store aggregation from Actions Queue status changes. Mostly deterministic Python — minimal Agent SDK reasoning needed.
- **Current partial implementation:** Back-propagation sweep already runs as scheduled task at 10 AM daily.

---

### 2b. MCP Server — The Shared Tool Layer

All Agent SDK runners AND Claude mobile call the same MCP tools. Deployed to a URL on the droplet. FastMCP Python, ~200 lines for core tools.

| Tool Group | Tools | Used By |
|-----------|-------|---------|
| Context | `cos_load_context()`, `cos_get_thesis_threads()`, `cos_get_funnel_state()`, `cos_get_ids_state(company)` | Claude mobile, all runners |
| Learning | `cos_get_action_history(limit, include_outcomes)`, `cos_log_outcome()`, `cos_get_preferences(action_type)` | All runners, digest.wiki webhooks |
| Network | `cos_get_person()`, `cos_get_company()`, `cos_search_network()`, `cos_best_meetings_today()`, `cos_relationship_temp(person)` | OptimiserAgent, Claude mobile |
| Actions | `cos_score_action()`, `cos_propose_actions()`, `cos_update_ids()`, `cos_triage_actions()` | PostMeetingAgent, ContentAgent |
| Retrieval | `cos_search()` — semantic over Postgres + vector DB (when available) | All runners, Claude mobile |
| Ingest | `cos_process_screenshot()`, `cos_process_post()`, `cos_run_pipeline()` | IngestAgent, Claude mobile triggers |
| Sync | `cos_sync_state()`, `cos_log_action()`, `cos_back_propagate()` | SyncAgent, session close |

**Existing MCP tools (already connected):** Notion Enhanced Connector, Notion Raw API, Granola MCP, Google Calendar MCP, Gmail MCP, Vercel MCP, Explorium MCP, Claude in Chrome, Apple Notes, PDF Tools. The `ai-cos-mcp` server complements these with cross-cutting AI CoS logic.

---

## Layer 3 — State

### Currently: Notion as Source of Truth

All structured data lives in Notion today. 8 databases with mapped schemas and IDs:

| Database | Data Source ID | Fields | Role |
|----------|---------------|--------|------|
| Network DB | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` | 40+ | People: 13 archetypes, IDS notes, relationship status |
| Companies DB | `1edda9cc-df8b-41e1-9c08-22971495aa43` | 49 | IDS repository, deal status 3D matrix, thesis alignment |
| Portfolio DB | `4dba9b7f-e623-41a5-9cb7-2af5976280ee` | 94 | Investment tracking, follow-on scoring, financial rollups |
| Actions Queue | `1df4858c-6629-4283-b31d-50c5e7ef885d` | 18 | Single action sink: Status (Proposed→Accepted→Done/Dismissed) |
| Content Digest DB | `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` | 17+ | AI-analyzed content with thesis/portfolio connections |
| Thesis Tracker | `3c8d1a34-e723-4fb1-be28-727777c22ec6` | 12 | Shared thesis state: conviction, evidence, key questions |
| Build Roadmap | `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` | 16 | Product roadmap: 7-state kanban, parallel safety, dependencies |
| Tasks Tracker | `1b829bcc-b6fc-80fc-9da8-000b4927455b` | — | Pipeline/portfolio tasks with company/person relations |

### Future: Postgres on Droplet — Source of Truth for Machine Operations

High-frequency tables migrate here. Notion syncs FROM Postgres. Sync worker: dirty flag pattern, 60s batch cycle, respects Notion rate limits (3 req/sec average).

#### Core Tables (Postgres)

| Table | Description | Sync Target |
|-------|-------------|-------------|
| `actions_queue` | Scored, bucketed, sourced, assigned_to (agent/aakash) | Notion Actions Queue |
| `action_outcomes` | THE preference store. Every accept/reject with full context. | — (machine only) |
| `network_graph` | People + companies + relationship edges (synced from Notion) | Notion Network/Companies DB |
| `ids_trail` | Conviction history per company. Append-only. | Notion Companies DB |
| `funnel_state` | Pipeline stages per company per fund context | Notion Companies DB |
| `content_digests` | Processed + scored content items | Notion Content Digest DB + digest.wiki |
| `thesis_signals` | Extracted signals per thread, with strength score | Notion Thesis Tracker |
| `session_log` | Audit trail across all agents and sessions | — |

#### Preference Store Schema (action_outcomes)
```sql
CREATE TABLE action_outcomes (
    id UUID PRIMARY KEY,
    action_id UUID REFERENCES actions_queue(id),
    outcome VARCHAR(20),           -- accepted / rejected / deferred / dismissed
    outcome_at TIMESTAMPTZ,
    action_type VARCHAR(50),        -- Thesis Update, Meeting/Outreach, Research, Follow-on Eval, etc.
    bucket INTEGER,                 -- 1-4 (priority bucket served)
    thesis_connection TEXT,         -- thesis thread name
    source_type VARCHAR(30),        -- Content Pipeline, Agent, Manual, Meeting, Thesis Research
    assigned_to VARCHAR(20),        -- Aakash / Agent / Sneha / Team
    score_at_proposal DECIMAL,      -- Action Score (0-10) when proposed
    scoring_factors JSONB,          -- full 7-factor breakdown at proposal time
    followed_through BOOLEAN,       -- did accepted action actually get done?
    outcome_quality VARCHAR(20),    -- good / neutral / bad (rated later)
    company_id TEXT,                -- Notion company page ID (if applicable)
    person_id TEXT,                 -- Notion person page ID (if applicable)
    context_snapshot JSONB          -- frozen context at decision time for replay
);

-- Index for preference injection queries
CREATE INDEX idx_outcomes_type_recent ON action_outcomes(action_type, outcome_at DESC);
CREATE INDEX idx_outcomes_bucket ON action_outcomes(bucket, outcome);
```

**How learning works:** Every Agent SDK reasoning session calls `cos_get_action_history(limit=100, include_outcomes=True)` before reasoning. Claude sees: "last 12 research actions rejected", "every intro action for Agentic AI thesis accepted", "P2 Agent-assigned research has 10% follow-through". It calibrates proposals accordingly. No ML training required — just structured history injected into context.

---

### Vector / Semantic Search Layer — Deferred

**Build strategy (from vision-v3):** Start with LLM-as-matcher (Notion + company index in the prompt). Add vector DB when triggered by: second signal source (Granola active processing), 500+ companies, or need for sub-second retrieval.

**Reference architecture:** pgvector on Postgres. May be replaced by MongoDB Voyage, Weaviate, or other purpose-built vector DB. Designed to be swappable — sits behind `cos_search()` in the MCP layer.

When active:
- `meeting_embeddings` — semantic search over Granola transcripts
- `content_embeddings` — semantic search over content digests
- `network_embeddings` — semantic search over people + company profiles
- `thesis_embeddings` — semantic search over thesis evidence corpus

---

### Network Graph Schema — As It Exists in Notion Today

#### Network DB (40+ fields, 13 archetypes)

**Archetypes:** Founder, DF (Domain Fighter), CXO, Operator, Angel, Collective Member, LP, Academic, Journalist, Government, Advisor, EXT Target, Other

**Key fields (from CONTEXT.md):**
- **Identity:** Person Name, Archetype (select from 13), Company (text/relation), Role, LinkedIn URL, Email, Phone, City
- **IDS State:** IDS Notes (rich text — contains the full IDS trail), Relationship Status, Last Interaction (date), Source (how they entered the network)
- **DeVC Context:** Collective Status (for Collective Member archetype), Fund Context (Z47/DeVC/Both)
- **Connections:** Relations to Companies DB (via Company field or explicit relation)

#### Companies DB (49 fields)

**Key fields:**
- **Identity:** Company Name, Sector, Stage, Website, Description
- **IDS Repository:** Company pages contain the full IDS trail as comments/content. The Companies DB IS the IDS database.
- **Deal Status 3D:** Combines pipeline stage × conviction × active/inactive in a single structured field. This is the funnel state machine for investment decisions.
- **Scoring:** Spiky Score (7 criteria × 1.0), EO/FMF/Thesis/Price scores (4 categories × /10)
- **Relations:** Founders (relation to Network DB), Team Notes, JTBD (Jobs To Be Done)
- **Thesis:** Thesis alignment field connecting to thesis threads

#### Portfolio DB (94 fields)

**Key fields:**
- **Investment:** Fund, vintage, Money In, ownership, valuation
- **EF/EO:** Entrepreneurial Fire / Entrepreneurial Orientation formalized scoring
- **Financial:** Rollup structure linking to Finance DB
- **Follow-on:** Follow-on tracking, follow-on scoring criteria
- **Relations:** Company (relation to Companies DB), Founders

#### Relationship Temperature Model — ✅ FILLED (was 🔴)

Not a separate model — it's the `relationship_temp` factor within the People Scoring Model (9 factors). Designed here as a composite signal:

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

**Temperature scale:** Hot (active, <2 weeks since interaction, regular cadence) → Warm (responsive, 2-8 weeks, occasional) → Cool (no interaction 2-6 months, needs re-engagement) → Cold (>6 months, requires re-introduction context).

**Signals available today in Notion:** Last Interaction (date field in Network DB), IDS Notes (text — contains interaction history). Missing: interaction frequency (derivable from Granola meeting history), communication direction (requires email/WhatsApp analysis), response latency (requires messaging integration).

**Implementation path:** Phase 1 = recency-only from Notion Last Interaction field. Phase 2 = frequency from Granola MCP `list_meetings` history. Phase 3 = full model when messaging integrations land.

---

## DeVC Collective — Graph + Funnel — ✅ FILLED (was 🔴)

### DeVC as First-Class Graph Entity
The DeVC collective is distinct from Z47 pipeline even when people/companies overlap. It has its own funnel, its own relationship types, and its own value creation logic. DeVC entities live in the same Notion databases (Network DB for people, Companies DB for companies) with `Fund Context` differentiating Z47/DeVC/Both.

### Deal Flow Funnel (from CONTEXT.md)

| Stage | Description | Key Actions | Transition Trigger |
|-------|-------------|-------------|-------------------|
| **TOFU** (Top of Funnel) | Sourced via VCs, MPI + team, 1:Many channels | Background research, initial screening | Aakash + Mohit meeting scheduled |
| **MOFU** (Middle of Funnel) | Aakash + Mohit meeting completed | IDS evaluation begins, follow-up meetings, IDS Q progression | MPI Eval completed |
| **BOFU** (Bottom of Funnel) | MPI Eval complete | If positive → auto-commit. If negative → full IDS review. IC prep, term sheet. | Investment decision (close or pass) |

**In Notion:** Deal Status 3D matrix in Companies DB combines pipeline stage × conviction × active/inactive. This IS the funnel state.

### DeVC Collective Sourcing (7 Channels from CONTEXT.md)

1. **X/LinkedIn content discovery** → screengrabs → async outreach
2. **Extensive bookmarking** across platforms → fuzzy memory map
3. **WhatsApp self-channel** — distilled links Aakash sends to himself
4. **WhatsApp Network DB group** → team updates Notion
5. **Events & introductions** — in-person and referral
6. **Leverage lens** — coverage, evaluation, underwriting (DeVC's unique model)
7. **Downstream investors/VCs** — later-stage funds referring early-stage deals

### Collective Members as Graph Nodes
- Collective members are people nodes in Network DB with `Archetype = Collective Member`
- `Collective Status` field tracks their pipeline: Prospect → Engaged → Signed → Active
- Relationship edges to: portfolio companies (can intro, co-invest), thesis threads (domain expertise), Aakash (relationship strength via temperature model)
- OptimiserAgent queries collective member nodes when scoring intro opportunities — "who in collective knows this founder?"

### Collective Member Engagement Model
- **Prospect:** Identified as potential collective member. Source channel logged.
- **Engaged:** In conversation about joining. IP assignment discussion started.
- **Signed:** Agreement signed. IP assigned. Co-investment rights activated.
- **Active:** Participating — making intros, co-investing, contributing domain expertise. Activity tracked via Actions Queue (actions involving collective members).
- **Dormant:** Signed but inactive >3 months. OptimiserAgent flags for re-engagement.

---

## Impact Score / Action Scoring — ✅ FILLED (was 🔴)

The "impact score" referenced in the Build Roadmap IS the Action Scoring Model from CONTEXT.md. There is no separate impact score — it's the same system.

### Action Scoring Model (7 Factors)

```
Action Score = f(
    bucket_impact,                  — Which of the 4 priority buckets does this serve? How much?
    conviction_change_potential,    — Could this move investment conviction up or down?
    key_question_relevance,         — Does this address an open Key Question on a thesis/company?
    time_sensitivity,               — Is there a reason to act NOW vs later?
    action_novelty,                 — New information vs redundant/already-known?
    stakeholder_priority,           — How important is the person/company involved?
    effort_vs_impact                — Time cost vs expected value?
)
```

**Thresholds:**
- **Score ≥ 7:** Surface as action (high-confidence recommendation)
- **Score 4-6:** Tag as "Low Confidence" — available but not promoted
- **Score < 4:** Context enrichment only — updates the Knowledge Store, no discrete action

**Implementation:** `scripts/action_scorer.py` (172 lines, created Session 039) implements this model. Not yet wired into Content Pipeline — next integration step.

### People Scoring Model (Subset for Meeting-Type Actions)

```
Person Score = f(
    bucket_relevance,      — Which of the 4 objectives does meeting this person serve?
    current_ids_state,     — Where are they in the IDS journey? Open questions?
    time_sensitivity,      — Reason to meet NOW vs later?
    info_gain_potential,   — What will Aakash learn that he doesn't know?
    network_multiplier,    — Who else does this person connect to?
    thesis_intersection,   — Does this person sit at a thesis convergence point?
    relationship_temp,     — Hot/warm/cool/cold? Last interaction? Trend?
    geographic_overlap,    — Will they be in the same city?
    opportunity_cost       — What does Aakash miss by NOT meeting them now?
)
```

### Composite Score (from Vision-v2)

For weekly/trip meeting optimization:
```
Composite Score = weighted_sum(bucket_scores) × urgency_multiplier × geographic_overlap × relationship_trajectory
```

### "Best Meetings Today" Ranking

`cos_best_meetings_today()` combines:
1. People Scoring Model output for all contacts
2. Calendar context (where is Aakash today — geographic overlap factor)
3. Funnel state (anyone in MOFU/BOFU needing follow-up?)
4. Relationship temperature (anyone cooling who should be warmed?)
5. Thesis relevance (any thesis thread with high open-question count?)
6. Preference calibration (what types of meetings does Aakash actually take?)

---

## Layer 4 — Interface

| Surface | Primary Use | Powered By | Proactive? |
|---------|------------|------------|-----------|
| Claude mobile | Conversational queries, "what's next?", trigger runners | MCP over Notion/Postgres state | No — Aakash initiates |
| Claude desktop | Same as mobile, larger context window | MCP over Notion/Postgres state | No |
| digest.wiki | Browse content, accept/reject proposed actions | Vercel SSG → JSON data, future: Postgres API | No |
| Notion | Action queue triage, thesis notes, build roadmap, IDS trail | Direct Notion + runner syncs | No |
| WhatsApp | Proactive push summaries from runners | Agent SDK runner → Twilio/WA API | **YES** |
| Cowork | Current build surface (39 sessions) | Linux VM + MCP tools | No |
| Claude Code | Daily coding, hooks, CLAUDE.md, subagents | CLI + hooks + Tailscale to droplet | No |
| Future Vercel UIs | DeVC funnel view, network graph, best meetings | Vercel → Postgres API | TBD |

---

## Known Gaps — Remaining

### Technical Decisions Deferred
- **Vector DB final choice** — pgvector vs MongoDB Voyage vs Weaviate. Decide when retrieval patterns clearer. (Trigger: 2nd signal source active, 500+ companies, or sub-second retrieval need.)
- **Graph traversal depth** — Postgres FK joins handles most cases. If 2-3 hop queries become complex, evaluate Neo4j or similar.
- **X / LinkedIn ingestion** — no clean API. Profile screenshots via vision is current path. Watch for X MCP or LinkedIn MCP. Explorium provides some enrichment.
- **Granola auto-processing** — Granola MCP provides access. Question: should PostMeetingAgent poll `list_meetings` on cron, or does Granola support webhooks?
- **WhatsApp output channel** — Twilio or WhatsApp Business API. ~2hr setup. Priority rises when OptimiserAgent is live.
- **Cowork deprecation timing** — Cowork has capabilities (browser automation, Vercel deploy, file presentation, scheduled tasks) that need equivalent coverage before migration.

---

## Build Phasing (Corrected)

| Phase | What Gets Built | Unlocks |
|-------|----------------|---------|
| **Phase 1 — MCP + Preference Foundation** | Custom `ai-cos-mcp` server on droplet. Postgres with core tables (actions_queue mirror, action_outcomes). Preference store writes from Actions Queue status changes. Wire `action_scorer.py` into Content Pipeline. | Claude mobile becomes preference-aware. Scoring moves from prompt-embedded to systematic. Preference capture begins. |
| **Phase 2 — Autonomous Runners** | PostMeetingAgent (Granola → IDS updates → actions). ContentAgent (migrate Content Pipeline v4 logic). SyncAgent (Notion ↔ Postgres). | System compounds without Aakash present. Post-meeting processing autonomous. Preference store accumulates. Second signal source (Granola) triggers vector DB evaluation. |
| **Phase 3 — Optimisation** | OptimiserAgent. `cos_best_meetings_today()`. Relationship temperature scoring (Phase 2: frequency from Granola). Gap analysis ("underweighting bucket 2"). Network graph explorer (if needed). | Full "what's next" reasoning across stakeholder + action space. AI CoS vision realised. |
| **Phase 4 — Scale + Multi-Source** | IngestAgent (screenshots, X/LinkedIn when APIs available). Vector DB (if triggered). WhatsApp output channel. Additional Vercel frontends. Surface migration assessment. | Multi-source observation. Full UI ecosystem. Proactive push to WhatsApp. |

---

## Full Architecture Diagram (Text)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OBSERVATION LAYER (Signal Sources)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Granola MCP     Notion MCP      YouTube/RSS     Calendar MCP
Gmail MCP       digest.wiki     X/LinkedIn(🔜)  WhatsApp(🔜)
Screenshots     Explorium       Apple Notes
               ↓ normalized Signals
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTELLIGENCE LAYER — AiCosOrchestrator (Agent SDK)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PostMeetingAgent   ContentAgent   OptimiserAgent
IngestAgent        SyncAgent
    ↑ reads preference store before every reasoning session
               ↓ all call
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL LAYER — ai-cos-mcp + existing MCPs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cos_load_context    cos_get_action_history
cos_search          cos_update_ids
cos_score_action    cos_best_meetings_today
cos_log_outcome     cos_relationship_temp
               ↓ reads/writes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATE LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: Notion (8 DBs, source of truth)
Phase 2: + Postgres (machine-speed, preference store)
Phase 3: + Vector DB (semantic retrieval, if triggered)

action_outcomes (preference)   network_graph
ids_trail (conviction history) funnel_state
content_digests                thesis_signals
               ↓ surfaces to
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERFACE LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Claude mobile    digest.wiki    Notion     Cowork
Claude Code      WhatsApp(🔜)   Future Vercel UIs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ↻ LEARNING LOOP
    accept/reject → action_outcomes
    → preference injection → better proposals
    → compound over time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
