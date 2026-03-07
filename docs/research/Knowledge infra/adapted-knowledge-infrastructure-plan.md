> **SUBSUMED — Canonical versions now live in `docs/source-of-truth/`.** Content split across CAPABILITY-MAP.md (capabilities, dependency graph), METHODOLOGY.md (principles, technology evaluation), and ENTITY-SCHEMAS.md (schemas, patterns, sovereignty model). This file is preserved as the original research artifact.

# Adapted Knowledge Infrastructure Plan
**Version:** v2-adapted | **Date:** 2026-03-07 | **Status:** Subsumed into source-of-truth
**Reconciled from:** `knowledge-infrastructure-plan.md` (original, Draft v1)
**Reconciliation Q&A:** `reconciliation-qna/A-G + IC` (7 sections, 33 questions answered)

---

## 0. How to Read This Document

This is NOT a project plan with phases and timelines. It is:

1. **A capability map** — what the AI CoS knowledge infrastructure needs to do
2. **A dependency graph** — what requires what
3. **A technology evaluation** — what to build with, assessed by migration cost
4. **A pattern library** — reusable patterns for building new capabilities
5. **A methodology codex** — the 15 principles that govern how we build

Every capability is expressed at multiple IDS levels (+, ++, +++). You don't build +++ upfront — you build + when friction demands it, and graduate when + hits its limits.

**Who decides what to build when?** Aakash. This document gives him the map and the constraints. It does not prescribe sequence.

**Build cadence assumption:** 3-4 hour sessions with Claude Code, every 2nd day (~10-14 hrs/week). Each capability must decompose into session-sized work.

---

## 1. Methodology Codex — The 15 Principles

These emerged from the reconciliation exercise and govern all build decisions.

### Build Philosophy
1. **Vision is north star, not blueprint.** The 6-store topology, Context Assembly API, full ER pipeline — these are directional targets. They get refined through building, not designed in advance.
2. **Functional build vs vision architecture.** Build with whatever works NOW (LLM-as-matcher, Notion queries, simple Postgres). Graduate to proper architecture when triggers fire.
3. **Infrastructure follows friction.** Don't build infra speculatively. Build when a workflow hits a concrete limitation. Each infra piece starts as MVP and graduates through IDS levels.
4. **Migration cost as decision framework.** For each technology: assess cost of migrating from pragmatic-first to end-vision. Low migration cost → start pragmatic. High migration cost → lean toward end-vision tech upfront.

### Plan Structure
5. **Dependency graphs, not phases.** Define what requires what. Leave sequencing to Aakash's judgment at build time.
6. **Define patterns, not rosters.** Don't enumerate all future runners or signal sources. Define the runner pattern, the signal source pattern, and let instances emerge from need.
7. **Deepen + Broaden dual-track.** Track 1: take the content pipeline closer to uber vision (pulls infra). Track 2: add new signal sources in parallel (stress-tests infra). Both tracks feed each other.

### Architecture
8. **Preference Store = RL infrastructure.** Not just "remember what Aakash liked." It's the reinforcement learning substrate. Every accept/reject feeds scoring models, runner behavior, action prioritization. The compounding mechanism.
9. **Action Frontend is infrastructure, not a feature.** It completes the human-in-the-loop feedback cycle. Without it, the RL loop is broken.
10. **Three ingestion tiers: Active → Passive → Ambient.** Each requires more infrastructure and more trust. This is IDS applied to signal capture.
11. **Trust spectrum as governance framework.** Read → Suggest → Act → Auto-act, earned at category level. Runners earn trust through operation, not design.

### Data
12. **CRM is a swappable interface.** Notion now, Attio later. Build to an abstraction, not to a specific backend.
13. **Schema divergence is by design.** Postgres (agent layer) will be a superset of Attio/Notion (human layer). Agents need fields humans don't.

### Operations
14. **Documentation is infrastructure.** Great docs enable Claude Code productivity and potential future developer onboarding. If it's not documented, it doesn't compound.
15. **Budget unconstrained; operational simplicity is the constraint.** Prefer Postgres extensions and managed services over self-hosted engines.

---

## 2. Current State — What Exists

### Live Infrastructure
| Component | Status | Details |
|-----------|--------|---------|
| DO Droplet | ✅ Live | Ubuntu 24.04, Tailscale mesh, Cloudflare Tunnel |
| PostgreSQL | ✅ Live | 7 tables: thesis_threads, actions_queue, action_outcomes, companies, network, sync_queue, change_events |
| ai-cos-mcp | ✅ Live | FastMCP Python, 17 tools, streamable HTTP at mcp.3niac.com |
| ContentAgent | ✅ Live | Cron 5-min: YouTube → analysis → Notion + digest.wiki + Actions Queue + Thesis Tracker |
| SyncAgent | ✅ Live | Cron 10-min: Thesis status sync, Actions bidirectional sync, change detection → action generation |
| digest.wiki | ✅ Live | Next.js 16, Vercel, auto-deploy on git push |
| Notion (8 DBs) | ✅ Live | Network, Companies, Portfolio, Tasks, Thesis Tracker, Content Digest, Actions Queue, Build Roadmap |
| Preference Store | ✅ Live | action_outcomes table in Postgres |

### Live Patterns
| Pattern | Implementation | Proven? |
|---------|---------------|---------|
| Write-ahead | Postgres first → Notion push → sync_queue on failure | ✅ Yes |
| Runner | Narrow specialist, Claude API call, structured prompt, cron-scheduled | ✅ Yes (ContentAgent, SyncAgent) |
| MCP tool routing | ai-cos-mcp tools for Thesis/Content/Actions, Notion MCP for everything else | ✅ Yes |
| Change detection | Notion pull → field-level diff → change_events → action generation | ✅ Yes |
| Conviction engine | AI-managed thesis threads, 6-level conviction spectrum, evidence accumulation | ✅ Yes |

### Known Gaps (from VISION-AND-DIRECTION.md + reconciliation)
| Gap | Impact |
|-----|--------|
| Action Frontend missing | RL loop broken — no clean accept/reject signal, poor triage UX |
| action_scorer not wired into Content Pipeline | Actions proposed without scoring |
| 2 scoring factors missing (key_question_relevance, stakeholder_priority) | Scoring model incomplete |
| Full preference injection not flowing | Runners don't learn from past decisions |
| Only 1 signal source (YouTube, partially autonomous) | Most of Aakash's information intake not captured |
| No entity resolution | Same person/company appears differently across surfaces |
| No vector search | Can't search semantically across content |
| Owe/Owed Ledger not modeled | Key relationship attribute missing from data model |
| Archetype classification not stored | 13 archetypes referenced but not queryable |

---

## 3. Capability Map

Each capability is defined with:
- **What it does**
- **IDS levels** (+, ++, +++) — what each level of sophistication looks like
- **Dependencies** — what must exist before this can be built
- **Infrastructure it pulls** — what infra gets built as a side effect

### 3.1 Entity Resolution

**What:** Resolve entity references across all surfaces (Notion, transcripts, email, content) to canonical records.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Basic** | Company Index: Postgres table mapping company names/aliases → Notion page IDs. Person Index: same for people. LLM-as-matcher for fuzzy resolution. | Postgres tables + Claude API calls |
| **++ Structured** | Confidence scoring (auto-merge >0.9, flag 0.7-0.9, tentative 0.5-0.7). Alias learning from corrections. Cross-surface entity linking. | Postgres + scoring logic in Python |
| **+++ Full Pipeline** | 5-stage ER (NER → candidates → disambiguation → resolution → output). RL from correction feedback. Proactive entity discovery from new signals. | Postgres + dedicated ER service + vector similarity for candidate matching |

**Dependencies:** None — can start building + immediately.
**Infra pulled:** Company Index (Postgres table) at +. Vector similarity search at +++.
**Migration cost + → +++:** LOW. Postgres tables persist; LLM-as-matcher logic becomes the disambiguation stage; confidence scoring adds on top.

### 3.2 Action Scoring & Preference Learning (RL Infrastructure)

**What:** Score proposed actions, learn from human decisions, improve over time.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Current** | 5-factor action_scorer.py. Preference Store (action_outcomes table) records accept/reject. Manual weight tuning. | Python script + Postgres |
| **++ Complete** | 7-factor model (add key_question_relevance, stakeholder_priority). Preference injection: every runner reads past preferences before proposing. Scoring wired into Content Pipeline. | Same + MCP tool for preference retrieval per-runner |
| **+++ Adaptive** | Weight auto-adjustment from preference data. Per-category trust calibration. Cross-runner preference transfer. Counterfactual analysis ("what would have surfaced if weights were different?"). | Same + ML pipeline for weight optimization |

**Dependencies:** Action Frontend (for clean accept/reject signal) is critical for ++ and +++.
**Infra pulled:** Preference injection MCP tool at ++. ML training pipeline at +++.
**Migration cost + → +++:** LOW. Same Postgres table, same scoring function. Weights evolve, logic extends.

### 3.3 Action Frontend

**What:** Human-layer surface for triaging, accepting/dismissing, and providing feedback on proposed actions.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ MVP** | /actions route on digest.wiki. List view with accept/dismiss buttons. Writes back to Actions Queue (Notion) + action_outcomes (Postgres). | Next.js 16 + shadcn/ui + API routes → MCP server |
| **++ Rich** | Sortable/filterable by score, thesis, source. Bulk actions. Detail panel with evidence/context. Score breakdown visualization. | Same stack, more components |
| **+++ Intelligent** | Personalized ordering based on preference history. "Why this action?" explanations. Suggested groupings (thesis clusters, time-sensitive batches). | Same stack + preference-driven ranking API |

**Dependencies:** None for +. Scoring model (3.2 ++) for score display. Preference learning (3.2 ++) for +++.
**Infra pulled:** API routes on digest.wiki at +. This is the bridge between frontend and MCP/Postgres.
**Note:** This is INFRASTRUCTURE, not a feature. It closes the RL feedback loop. High urgency.

### 3.4 Signal Source Ingestion

**What:** Capture signals from the world and feed them into the system.

**The Signal Source Pattern** (every source follows this):
1. **Connector** — How to access the source (API, scrape, file watch, webhook)
2. **Extractor** — How to pull structured data from raw content
3. **Entity Resolver** — How to match extracted entities to canonical records (uses 3.1)
4. **Action Generator** — How to produce proposed actions from extracted signals
5. **Writer** — How to persist results (Notion + Postgres via MCP tools)

| Source | Current Tier | Notes |
|--------|-------------|-------|
| YouTube (playlist) | Active | Live via ContentAgent. Partially autonomous — requires manual playlist curation. |
| YouTube (subscriptions) | Not built | Passive tier — would auto-process subscription feed without manual curation. |
| LinkedIn | Not built | Content flow signal source. |
| X (Twitter) | Not built | Content flow signal source. |
| Granola (meetings) | Not built | Stakeholder signal source. Highest signal density (7-8 meetings/day). MCP tools exist. |
| WhatsApp | Not built | Stakeholder action space. Passive/ambient ingestion tier. |
| Gmail | Not built | Deal flow, follow-ups, thesis signals. |
| Calendar | Not built | Meeting context, scheduling patterns. |

**IDS levels apply per source:**
| Level | Description |
|-------|-------------|
| **+ Active** | User explicitly sends signals to system (current: add to playlist) |
| **++ Passive** | System monitors sources autonomously (future: subscription feeds, channel monitoring) |
| **+++ Ambient** | System captures from natural workflows without explicit action (future: WhatsApp monitoring) |

**Dependencies:** Entity Resolution (3.1 +) for reliable entity matching. Runner pattern for processing.
**Infra pulled:** Each new source may require a new connector. Passive/ambient sources require background monitoring infrastructure.

### 3.5 Searchable Document Corpus (Vector Search + Document Store)

**What:** Search semantically across all content the system has ingested — transcripts, digests, research, emails.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Basic** | pgvector extension on existing Postgres. Embed document chunks. Semantic search across content. | Postgres + pgvector + embedding model (Claude / OpenAI) |
| **++ Dedicated** | Separate vector DB for better performance. Hybrid search (semantic + keyword). Multi-index (content type separation). | Qdrant or Pinecone + Postgres for metadata |
| **+++ Multi-Store** | Full document corpus architecture. S3 for blob storage. Vector DB for semantic retrieval. Cross-document entity linking. | S3 + Vector DB + ER integration |

**Dependencies:** Content to search (3.4 signal sources feed this). Entity Resolution (3.1) for cross-document linking at +++.
**Infra pulled:** pgvector extension at +. Embedding generation pipeline. Potentially separate vector DB at ++.
**Migration cost + → ++:** LOW. Embeddings are portable. Query patterns are similar. pgvector → Qdrant/Pinecone is a storage backend swap.
**Migration cost ++ → +++:** MEDIUM. Adding S3 + cross-document linking is new architecture, but vector search layer persists.

**Note:** The original plan's "Document Store" and "Vector Store" collapse into a single capability. The real need is searchable document corpus, not separate blob storage.

### 3.6 Relationship Intelligence

**What:** Model, score, and optimize Aakash's network relationships for better prioritization.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Data Model** | Extend Person entity with: temperature score, owe/owed ledger (directional obligations), last interaction date, interaction frequency. Store in Network DB + Postgres. | Postgres columns + Notion properties |
| **++ Computed** | Auto-update temperature from interaction signals (meetings, messages, content mentions). Owe/owed auto-populated from meeting action items. Relationship strength scoring. | Runner logic + signal processing |
| **+++ Graph** | Full relationship graph: person↔person, person↔company, person↔thesis connections. Network gap analysis ("who should you know but don't?"). Intro path optimization. | Graph DB (Neo4j) or Postgres recursive CTEs |

**Dependencies:** Signal sources (3.4) for interaction data. Entity Resolution (3.1) for person matching. Meeting ingestion (Granola) for auto-populating owe/owed.
**Infra pulled:** Postgres schema extensions at +. Graph DB evaluation at +++.
**Migration cost + → +++:** MEDIUM-HIGH for graph DB route. Postgres recursive CTEs can handle ++ but +++ graph queries (shortest paths, community detection, centrality) may genuinely need Neo4j. **This is the one capability where end-vision tech should be evaluated early** — before committing to deep Postgres graph modeling that may need rewriting.

### 3.7 Context Assembly

**What:** Assemble rich context bundles for any entity on demand — used by runners, scoring, and human-facing surfaces.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Ad-hoc** | Current state: each runner/tool assembles its own context via MCP calls. Works but duplicates logic. | MCP tools (existing) |
| **++ Standardized** | Context Assembly MCP tool: given an entity, return a standardized bundle (profile, timeline, relationships, evidence, open questions). Shared across all runners. | New MCP tool + Postgres queries |
| **+++ Intelligent** | Context level adaptation (full/scoring/minimal based on use case). Caching for frequently-accessed entities. Predictive pre-assembly for likely-needed contexts. | Same + caching layer + prediction logic |

**Dependencies:** Entity Resolution (3.1 ++) for reliable entity lookup. Relationship Intelligence (3.6 +) for relationship data in bundles. Searchable Corpus (3.5 +) for evidence retrieval.
**Infra pulled:** New MCP tool at ++. Caching at +++.
**Trigger for building ++:** When a 2nd runner (e.g., PostMeetingAgent) needs the same context bundle pattern that ContentAgent already assembles ad-hoc. That's when duplication becomes painful enough to abstract.

### 3.8 Infrastructure Observer (Data Quality)

**What:** Proactively monitor data stores for quality issues, gaps, staleness, and conflicts. (Distinct from the vision-level Observation Layer which is about signal ingestion from the world.)

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Current** | SyncAgent's change detection → action generation. Reactive: detects changes when they happen. | SyncAgent (existing) |
| **++ Proactive** | Scheduled scans: stale profiles (no interaction in N days), missing fields, entity conflicts, orphaned records. Gap reports surfaced as actions. | SyncAgent evolution + scheduled scan jobs |
| **+++ Intelligent** | Pattern detection: "these 3 companies are always mentioned together but have no formal connection." Schema gap detection: "this new signal source produces a field we don't store." | ML/heuristic analysis on accumulated data |

**Dependencies:** Entity Resolution (3.1 +) for conflict detection. Multiple signal sources (3.4) for meaningful pattern detection at +++.
**Infra pulled:** Extends SyncAgent. No new infrastructure at + or ++.
**Note:** Renamed from "Observation Layer" to avoid confusion with the vision-level signal ingestion layer.

---

## 4. Dependency Graph

```
                    ┌─────────────────────┐
                    │   Action Frontend   │
                    │       (3.3)         │
                    └──────────┬──────────┘
                               │ closes RL loop
                    ┌──────────▼──────────┐
                    │  Scoring & Prefs    │
                    │     (3.2 RL)        │◄──── Preference data from all human interactions
                    └──────────┬──────────┘
                               │ scores actions from
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼────┐  ┌───────▼──────┐  ┌──────▼───────┐
    │  Content     │  │  Meeting     │  │  Network     │
    │  Pipeline    │  │  Pipeline    │  │  Pipeline    │
    │  (3.4 YT+)  │  │  (3.4 Gran)  │  │  (3.4 WA+)  │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                  │
           └────────┬────────┴──────────┬───────┘
                    │                   │
          ┌─────────▼────────┐ ┌────────▼─────────┐
          │ Entity Resolution│ │ Searchable Corpus │
          │     (3.1)        │ │     (3.5)         │
          └─────────┬────────┘ └────────┬──────────┘
                    │                   │
                    └────────┬──────────┘
                    ┌────────▼──────────┐
                    │ Context Assembly  │
                    │     (3.7)         │
                    └────────┬──────────┘
                             │ feeds
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼────┐ ┌──────▼──────┐ ┌─────▼──────────┐
    │ Relationship │ │ Infra       │ │ All Runners     │
    │ Intelligence │ │ Observer    │ │ (via context    │
    │   (3.6)      │ │   (3.8)    │ │  bundles)       │
    └──────────────┘ └─────────────┘ └────────────────┘
```

**Key dependency chains:**
- Action Frontend → RL Loop → Better Scoring → Better Actions (THE compounding loop)
- Entity Resolution → reliable signal processing → every pipeline benefits
- Signal Sources → data volume → vector search justification → searchable corpus
- Context Assembly triggered when 2+ runners need same context pattern
- Relationship Intelligence depends on meeting ingestion for owe/owed data

**No dependency on (can start anytime):**
- Entity Resolution + (Company Index / Person Index)
- Action Frontend + (MVP accept/dismiss)
- Scoring model completion (add 2 missing factors)
- New signal source connectors (following the Signal Source Pattern)

---

## 5. Technology Evaluation by Migration Cost

For each store in the vision topology, assessed against Principle #4 (migration cost as decision framework).

| Vision Store | Pragmatic Start (+) | Migration Cost → Vision | Recommendation |
|-------------|-------------------|------------------------|----------------|
| **OLTP / CRM** | Notion (current) | LOW → Attio (same data model, API-first, designed as swappable) | ✅ Stay on Notion. Build CRM abstraction layer. Migrate to Attio when human-layer UX benefit justifies the effort. |
| **Document Store** | Local files + Notion + digest.wiki JSONs | LOW → S3 (blob migration is mechanical) | ✅ Stay pragmatic. Add S3 when cross-document retrieval is needed. |
| **Vector Search** | pgvector (Postgres extension) | LOW → Qdrant/Pinecone (embeddings are portable) | ✅ Start with pgvector. Zero new infra. Graduate when query patterns or scale exceed pgvector limits. |
| **Graph Store** | Postgres JSONB + recursive CTEs | MEDIUM-HIGH → Neo4j (query paradigm shift, data model rewrite) | ⚠️ EVALUATE EARLY. Before building deep graph logic in Postgres, spike a Neo4j prototype for the relationship queries you actually need (network paths, community detection, centrality). If those queries are rare/simple, Postgres is fine. If they're core, Neo4j from the start saves a rewrite. |
| **Timeline Store** | Postgres (timestamp columns, range queries) | LOW → TimescaleDB (it IS Postgres, just an extension) | ✅ Start with plain Postgres. Add TimescaleDB extension when time-series query patterns emerge (interaction frequency trends, conviction trajectory over time). |
| **ER Index** | Postgres + LLM-as-matcher | MEDIUM → Elasticsearch (different query paradigm, but ER data is derived/rebuildable) | ✅ Start with Postgres. Elasticsearch only justified at high entity volume + complex fuzzy matching. Current scale (~200 companies, ~400 contacts) doesn't warrant it. |

**Summary:** 4 of 6 stores are safe to start pragmatic with Postgres. Graph Store needs early evaluation. CRM layer needs an abstraction interface.

### The 6-Store Topology — Adapted

The original plan's 6-store topology remains the vision, with one simplification discovered during reconciliation:

**Document Store + Vector Store = Searchable Document Corpus** — these are one capability, not two. S3 stores blobs; vector DB stores embeddings; together they enable semantic search across documents. No need to treat them as architecturally separate.

Adapted topology (vision state):
1. **OLTP / CRM** — Attio (human layer) + Postgres (agent layer)
2. **Searchable Corpus** — S3 (blobs) + Vector DB (embeddings) — one capability
3. **Graph Store** — Neo4j or Postgres (pending evaluation spike)
4. **Timeline Store** — TimescaleDB extension on Postgres
5. **ER Index** — Postgres or Elasticsearch (scale-dependent)

All start as Postgres. Graduate individually when triggers fire.

---

## 6. Data Model — Entity Schemas

### Person Entity (canonical)
```
Core:           name, aliases[], email[], phone[], linkedin_url
Classification: archetype (13 types), role, company_id (→ Company)
Relationship:   temperature_score, owe_ledger[], owed_ledger[],
                last_interaction_date, interaction_frequency,
                relationship_strength_score
IDS:            ids_notation (+, ++, ?, ??, +?, -)  // per-context
Resolution:     canonical_id, source_ids[], confidence_score,
                last_resolved_at, resolution_method
Sovereignty:    human_fields (name, archetype, temperature),
                agent_fields (confidence, frequency, strength_score)
```

### Company Entity (canonical)
```
Core:           name, aliases[], domain, sector, stage
Thesis:         thesis_thread_ids[], conviction_context
Pipeline:       pipeline_stage, bucket (4 priority buckets)
Resolution:     canonical_id, source_ids[], confidence_score,
                last_resolved_at
IDS:            ids_trail[] // conviction trajectory over time
Sovereignty:    human_fields (name, stage, bucket),
                agent_fields (aliases, confidence, ids_trail)
```

### Action Entity (canonical)
```
Core:           description, action_type, source_runner
Scoring:        score (7-factor), factor_breakdown{},
                classification (surface/low_confidence/context_only)
Lifecycle:      status (Proposed→Accepted→In Progress→Done→Dismissed),
                proposed_at, decided_at, completed_at
Learning:       outcome_rating, preference_snapshot{},
                was_prediction_correct
Links:          person_id, company_id, thesis_thread_id
```

### Thesis Thread Entity (canonical)
```
Core:           thread_name, core_thesis, conviction_level (6 levels)
Evidence:       evidence_entries[] (text, direction, source, date)
Questions:      key_questions[] (text, status: OPEN/ANSWERED)
Links:          company_ids[], person_ids[], content_digest_ids[]
IDS:            conviction_trajectory[] // over time
Sovereignty:    human_fields (status: Active/Exploring/Parked/Archived),
                agent_fields (conviction, evidence, questions)
```

### New: Owe/Owed Ledger Entry
```
person_id:      → Person
direction:      "owe" | "owed"  // I owe them | they owe me
description:    text
source:         meeting_id | manual | email_id
created_at:     timestamp
resolved_at:    timestamp | null
status:         open | resolved | expired
```

---

## 7. Runner Pattern (The Reusable Template)

Every runner follows this contract:

```
┌─────────────────────────────────────────┐
│              RUNNER                       │
│                                          │
│  Input:   Signal(s) from source          │
│  Context: Assembled via MCP tools        │
│  Logic:   Domain-specific analysis       │
│  Output:  Actions + Entity updates       │
│                                          │
│  Reads:   cos_get_preferences()          │
│           cos_get_thesis_threads()        │
│           Entity context (Company/Person) │
│                                          │
│  Writes:  Actions Queue (scored)         │
│           Thesis updates (evidence)       │
│           Entity updates (new data)       │
│           Content records (if applicable) │
│                                          │
│  Schedule: Cron (interval varies)        │
│  Trust:   Starts at Suggest, earns up    │
│  Logs:    Structured output for audit    │
└─────────────────────────────────────────┘
```

**To create a new runner:**
1. Define the signal source it consumes (following Signal Source Pattern from 3.4)
2. Define the entity types it touches
3. Define the actions it can propose
4. Implement using ContentAgent as the reference implementation
5. Start at Suggest trust level — human approves all actions
6. Graduate trust level based on accuracy rate over N actions

**YouTube Content Pipeline as reference implementation:**
```
Signal:     YouTube videos from playlist / subscriptions
Extractor:  yt-dlp + youtube-transcript-api → JSON
Resolver:   Company/person matching in transcript content
Analyzer:   Claude API call with structured prompt
Output:     Content Digest record, thesis evidence, proposed actions
Writer:     Notion (Content Digest DB) + Postgres (actions_queue) + digest.wiki
Schedule:   Every 5 minutes
Trust:      Auto-act for thesis evidence, Suggest for new thesis threads
```

---

## 8. CRM Abstraction Layer

Since Notion and Attio should be swappable (Principle #12), the system needs an interface:

```python
# Conceptual interface — not literal code
class CRMInterface:
    # Person operations
    get_person(canonical_id) → Person
    search_persons(query) → Person[]
    update_person(canonical_id, fields) → void

    # Company operations
    get_company(canonical_id) → Company
    search_companies(query) → Company[]
    update_company(canonical_id, fields) → void

    # Relationship operations
    get_relationships(person_id) → Relationship[]
    get_owe_owed(person_id) → OweOwedEntry[]

    # Respects data sovereignty
    human_writable_fields: set  # only human can modify
    agent_writable_fields: set  # only agent can modify
    shared_fields: set          # both can modify with conflict resolution
```

**Implementation path:**
- **+** Current MCP tools already serve as a de facto CRM interface (cos_get_thesis_threads, Notion fetch/query). The abstraction exists implicitly.
- **++** Extract the interface explicitly. Current Notion MCP calls become the NotionCRMAdapter. When Attio migration happens, build AttioCRMAdapter implementing the same interface.
- **+++** Field-level sync with conflict resolution. Agent writes go to Postgres, human writes go to CRM, sync layer reconciles per data sovereignty rules.

---

## 9. The Deepen + Broaden Model

This is how capabilities grow over time:

```
DEEPEN (Track 1)                    BROADEN (Track 2)
Take content pipeline → vision      Add new signal sources + workflows

YouTube + basic analysis            LinkedIn content
    ↓                                   ↓
+ Entity Resolution (Company Index)  YouTube subscriptions (passive)
    ↓                                   ↓
+ Action Scoring (wired in)          X (Twitter) content
    ↓                                   ↓
+ Preference Learning               Granola (meetings)
    ↓                                   ↓
+ Vector Search (semantic matching)  WhatsApp (ambient)
    ↓                                   ↓
+ Context Assembly (standardized)    Gmail (ambient)
    ↓                                   ↓
Full vision content pipeline         Multi-source intelligence

    ←── Infrastructure shared ──→
    ←── Each deepening helps broadening ──→
    ←── Each broadening stress-tests deepening ──→
```

---

## 10. IDS Trail — The Missing Capability

Identified during reconciliation: the Cowork-era `ids_trail` table concept (per-entity IDS signal history over time) is still valid. This captures the conviction trajectory — how signals about a company or thesis thread have evolved.

**Current state:** thesis_threads has evidence_entries (text blobs appended over time) but no structured conviction trajectory.

**What's needed:**
```
ids_trail_entry:
    entity_type:  "company" | "thesis" | "person"
    entity_id:    canonical_id
    notation:     "+", "++", "?", "??", "+?", "-"
    context_type: one of 7 IDS context types
    signal_source: runner_id | "manual"
    timestamp:    when the signal was observed
    evidence:     brief text
```

**This enables:**
- "Show me the conviction trajectory for Company X over the last 3 months"
- "Which thesis threads have had the most positive signal momentum?"
- "Which companies have gone from ? to ++ in the last month?"

**Implementation:** JSONB column on thesis_threads and companies tables at +. Separate table at ++ if query patterns demand it.

---

## 11. Open Evaluations

These are technology decisions that need a spike/prototype before committing:

### 11.1 Graph Store Evaluation
**Question:** Do the relationship queries we actually need justify Neo4j, or can Postgres recursive CTEs handle them?
**Spike:** Define 5 concrete queries from the Relationship Intelligence capability (3.6). Implement them in both Postgres and Neo4j. Compare: query complexity, performance, maintainability.
**Example queries to test:**
1. "Who connects me to Person X?" (shortest path)
2. "Who are the most connected people in my thesis-relevant network?" (centrality)
3. "Which communities exist in my network?" (community detection)
4. "Who should I know but don't, based on my thesis threads?" (gap analysis)
5. "Show me all relationships between Company X's team and my existing network" (subgraph)

If queries 1-2 are the main use case → Postgres is fine.
If queries 3-5 are frequent → Neo4j is worth the operational cost.

### 11.2 Embedding Model Selection
**Question:** Which embedding model for pgvector / vector search?
**Considerations:** Cost per embed, dimension count (affects storage), quality for investor/startup domain content, API availability.
**Candidates:** OpenAI text-embedding-3-small, Claude embeddings (if available), open-source models via local inference.
**Spike:** Embed 100 existing digests. Test retrieval quality for known-relevant queries.

---

## 12. Data Sovereignty — Extended

The original DATA-SOVEREIGNTY.md defines field-level ownership. The adapted plan extends it with new fields and the 3-actor model:

```
Actor 1: Human (Aakash)
    Surfaces: Notion, Attio, mobile
    Owns: name, status, archetype, temperature_score,
          owe/owed entries (manual), pipeline stage, bucket assignment

Actor 2: Agent Layer (Runners, MCP tools)
    Surfaces: Postgres, MCP server
    Owns: confidence_score, ids_trail, interaction_frequency,
          relationship_strength, last_resolved_at, evidence_entries,
          scoring factor breakdowns, aliases

Actor 3: CRM Layer (Notion now, Attio later)
    Role: Shared surface — both human and agent write here
    Rules: Human fields take precedence on conflict.
           Agent writes to agent-owned fields only.
           Sync layer reconciles on schedule (SyncAgent).
```

**For every new field added to any entity schema, the adapted plan requires declaring:**
1. Which actor owns it
2. Which surfaces it appears on
3. What happens on conflict

---

## Appendix A: Reconciliation Summary

| Original Plan Element | Adapted Plan Treatment |
|----------------------|----------------------|
| 6-store topology | Retained as vision. Start with Postgres for 4 of 6. Graph store needs spike. Document + Vector stores merged. |
| 4-phase build sequence | Replaced with dependency graph + capability map. No prescribed order. |
| Attio migration as Phase 0 | Deferred. CRM abstraction layer instead. Notion → Attio when UX benefit justifies. |
| Entity Resolution pipeline | Retained but expressed at 3 IDS levels. Start with Company/Person Index. |
| Context Assembly API | Retained but triggered when 2+ runners need same context pattern. Not upfront. |
| Observation Layer | Renamed to Infrastructure Observer. Framed as SyncAgent evolution, not new system. |
| 18-week timeline | Removed. Build cadence is session-based (~3-4 hrs every 2nd day). |
| Design constraints C1-C6 | C1 (single developer) confirmed with documentation-as-scaling caveat. Budget unconstrained. |
| Preference Store | Elevated to "RL Infrastructure" — the compounding mechanism of the entire system. |

## Appendix B: New Concepts Added (Not in Original Plan)

| Concept | Source | Section |
|---------|--------|---------|
| Owe/Owed Ledger | Reconciliation F2 | 3.6, 6 |
| IDS Trail (conviction trajectory) | Cowork-era ids_trail + reconciliation D1 | 10 |
| Active → Passive → Ambient ingestion tiers | Reconciliation F3 | 3.4 |
| Signal Leakage + Delayed Relevance gap patterns | Reconciliation F3 | 3.4 |
| Migration cost as decision framework | Reconciliation G2 | 5 |
| Deepen + Broaden dual-track model | Reconciliation E3 | 9 |
| Infrastructure Observer (renamed) | Reconciliation C2 | 3.8 |
| CRM abstraction layer | Reconciliation A2 | 8 |
| 15 Methodology Principles | Full reconciliation | 1 |

## Appendix C: Files in This Reconciliation

```
cowork sandbox/
├── knowledge-infrastructure-plan.md              (original — untouched)
├── adapted-knowledge-infrastructure-plan.md       (this file)
├── suggested-cc-work.md                           (outside-sandbox edit suggestions)
├── droplet-scaling-roadmap.md                     (companion deliverable)
└── reconciliation-qna/
    ├── A-architecture-drift.md
    ├── B-entity-resolution-data-model.md
    ├── C-agent-pipeline-evolution.md
    ├── D-cowork-to-cc-handoff-gaps.md
    ├── E-build-sequence-reality-check.md
    ├── F-vision-evolution.md
    ├── G-technology-decisions.md
    └── IC-internal-contradictions.md
```
