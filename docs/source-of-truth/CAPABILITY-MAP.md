# Capability Map
*Last Updated: 2026-03-07*

Forward-looking capability map for the AI CoS knowledge infrastructure. Each capability is expressed at IDS levels (+, ++, +++) — build + when friction demands it, graduate when + hits its limits.

This is NOT a project plan with timelines. It's a dependency graph and a capability ladder. Aakash decides what to build when.

---

## 1. Entity Resolution

**What:** Resolve entity references across all surfaces (Notion, transcripts, email, content) to canonical records.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Basic** | Company Index + Person Index: Postgres tables mapping names/aliases to Notion page IDs. LLM-as-matcher for fuzzy resolution. | Postgres tables + Claude API calls |
| **++ Structured** | Confidence scoring (auto-merge >0.9, flag 0.7-0.9, tentative 0.5-0.7). Alias learning from corrections. Cross-surface entity linking. | Postgres + scoring logic |
| **+++ Full Pipeline** | 5-stage ER (NER, candidates, disambiguation, resolution, output). RL from correction feedback. Proactive entity discovery. | Postgres + dedicated ER service + vector similarity |

**Dependencies:** None — can start immediately.
**Infra pulled:** Company/Person Index tables at +. Vector similarity at +++.
**Migration cost + to +++:** LOW. Tables persist; LLM-as-matcher becomes the disambiguation stage; confidence scoring adds on top.

---

## 2. Action Scoring & Preference Learning

**What:** Score proposed actions, learn from human decisions, improve over time. This is the RL infrastructure — the compounding mechanism of the entire system.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Current** | 5-factor action_scorer.py. Preference Store (action_outcomes table) records accept/reject. Manual weight tuning. | Python + Postgres |
| **++ Complete** | 7-factor model (add key_question_relevance, stakeholder_priority). Preference injection: every runner reads past preferences before proposing. Scoring wired into Content Pipeline. | Same + MCP tool for preference retrieval |
| **+++ Adaptive** | Weight auto-adjustment from preference data. Per-category trust calibration. Cross-runner preference transfer. Counterfactual analysis. | Same + ML pipeline for weight optimization |

**Dependencies:** Action Frontend (cap. 3) for clean accept/reject signal is critical for ++ and +++.
**Infra pulled:** Preference injection MCP tool at ++. ML training pipeline at +++.
**Migration cost + to +++:** LOW. Same table, same function. Weights evolve, logic extends.

---

## 3. Action Frontend

**What:** Human-layer surface for triaging, accepting/dismissing, and providing feedback on proposed actions. This is INFRASTRUCTURE, not a feature — it closes the RL feedback loop.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ MVP** | /actions route on digest.wiki. List view with accept/dismiss buttons. Writes to Actions Queue (Notion) + action_outcomes (Postgres). | Next.js + shadcn/ui + API routes via MCP server |
| **++ Rich** | Sortable/filterable by score, thesis, source. Bulk actions. Detail panel with evidence/context. Score breakdown visualization. | Same stack, more components |
| **+++ Intelligent** | Personalized ordering based on preference history. "Why this action?" explanations. Suggested groupings. | Same + preference-driven ranking API |

**Dependencies:** None for +. Scoring (cap. 2 ++) for score display. Preferences (cap. 2 ++) for +++.
**Infra pulled:** API routes on digest.wiki at +.

---

## 4. Signal Source Ingestion

**What:** Capture signals from the world and feed them into the system.

**The Signal Source Pattern** (every source follows this):
1. **Connector** — How to access the source (API, scrape, file watch, webhook)
2. **Extractor** — How to pull structured data from raw content
3. **Entity Resolver** — Match extracted entities to canonical records (uses cap. 1)
4. **Action Generator** — Produce proposed actions from extracted signals
5. **Writer** — Persist results (Notion + Postgres via MCP tools)

| Source | Current Status | Ingestion Tier |
|--------|---------------|----------------|
| YouTube (playlist) | **Live** via ContentAgent | Active |
| YouTube (subscriptions) | Not built | Passive |
| Granola (meetings) | Not built — MCP tools exist | Active (highest signal density: 7-8 meetings/day) |
| Gmail | Not built — MCP tools exist | Passive |
| Calendar | Not built — MCP tools exist | Passive |
| LinkedIn | Not built | Passive |
| X (Twitter) | Not built | Passive |
| WhatsApp | Not built | Ambient |

**Ingestion tiers** (IDS applied to signal capture):

| Tier | Description | Trust Required |
|------|-------------|---------------|
| **Active** | User explicitly sends signals to system | Low |
| **Passive** | System monitors sources autonomously | Medium |
| **Ambient** | System captures from natural workflows without explicit action | High |

**Dependencies:** Entity Resolution (cap. 1 +) for reliable entity matching.

---

## 5. Searchable Document Corpus

**What:** Semantic search across all ingested content — transcripts, digests, research, emails.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Basic** | pgvector extension on existing Postgres. Embed document chunks. Semantic search. | Postgres + pgvector + embedding API |
| **++ Dedicated** | Separate vector DB. Hybrid search (semantic + keyword). Multi-index. | Qdrant/Pinecone + Postgres for metadata |
| **+++ Multi-Store** | Full corpus architecture. S3 for blob storage. Vector DB for retrieval. Cross-document entity linking. | S3 + Vector DB + ER integration |

**Dependencies:** Content to search (cap. 4 feeds this). Entity Resolution (cap. 1) for cross-document linking at +++.
**Migration cost + to ++:** LOW. Embeddings are portable.
**Migration cost ++ to +++:** MEDIUM. S3 + cross-document linking is new architecture.
**Note:** The original plan's "Document Store" and "Vector Store" collapse into one capability.

---

## 6. Relationship Intelligence

**What:** Model, score, and optimize Aakash's network relationships.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Data Model** | Extend Person entity with: temperature score, owe/owed ledger, last interaction date, interaction frequency. | Postgres columns + Notion properties |
| **++ Computed** | Auto-update temperature from interaction signals. Owe/owed auto-populated from meeting action items. Relationship strength scoring. | Runner logic + signal processing |
| **+++ Graph** | Full relationship graph. Network gap analysis. Intro path optimization. | Graph DB (Neo4j) or Postgres recursive CTEs |

**Dependencies:** Signal sources (cap. 4) for interaction data. Entity Resolution (cap. 1). Meeting ingestion (Granola) for owe/owed.
**Migration cost + to +++:** MEDIUM-HIGH for graph DB route. This is the one capability where end-vision tech should be evaluated early (see METHODOLOGY.md open evaluations).

---

## 7. Context Assembly

**What:** Assemble rich context bundles for any entity on demand — used by runners, scoring, and human-facing surfaces.

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Ad-hoc** | Current state: each runner assembles its own context via MCP calls. Works but duplicates logic. | MCP tools (existing) |
| **++ Standardized** | Context Assembly MCP tool: given an entity, return a standardized bundle. Shared across all runners. | New MCP tool + Postgres queries |
| **+++ Intelligent** | Context level adaptation. Caching. Predictive pre-assembly. | Same + caching layer |

**Dependencies:** Entity Resolution (cap. 1 ++) for reliable entity lookup. Relationship Intelligence (cap. 6 +). Searchable Corpus (cap. 5 +).
**Build trigger:** When a 2nd runner needs the same context bundle pattern that ContentAgent already assembles ad-hoc. That's when duplication becomes painful enough to abstract.

---

## 8. Infrastructure Observer

**What:** Proactively monitor data stores for quality issues, gaps, staleness, and conflicts. Distinct from signal ingestion (which monitors the external world).

| Level | Description | Technology |
|-------|-------------|------------|
| **+ Current** | SyncAgent's change detection and action generation. Reactive. | SyncAgent (existing) |
| **++ Proactive** | Scheduled scans: stale profiles, missing fields, entity conflicts, orphaned records. Gap reports surfaced as actions. | SyncAgent evolution |
| **+++ Intelligent** | Pattern detection across accumulated data. Schema gap detection. | ML/heuristic analysis |

**Dependencies:** Entity Resolution (cap. 1 +) for conflict detection. Multiple signal sources (cap. 4) for pattern detection at +++.
**Infra pulled:** Extends SyncAgent. No new infrastructure at + or ++.

---

## CRM Abstraction Layer

Since the CRM backend should be swappable (Notion now, Attio later):

| Level | Description |
|-------|-------------|
| **+ Implicit** | Current MCP tools serve as de facto CRM interface |
| **++ Explicit** | Extract the interface. Current Notion calls become NotionCRMAdapter. Build AttioCRMAdapter when migrating. |
| **+++ Full** | Field-level sync with conflict resolution per data sovereignty rules |

**Trigger for ++:** When Attio migration becomes desirable for human-layer UX.

---

## Dependency Graph

```
                    +---------------------+
                    |   Action Frontend   |
                    |       (cap. 3)      |
                    +----------+----------+
                               | closes RL loop
                    +----------v----------+
                    |  Scoring & Prefs    |
                    |   (cap. 2 -- RL)    |<---- Preference data from all human interactions
                    +----------+----------+
                               | scores actions from
              +----------------+----------------+
              |                |                |
    +---------v----+  +-------v------+  +------v-------+
    |  Content     |  |  Meeting     |  |  Network     |
    |  Pipeline    |  |  Pipeline    |  |  Pipeline    |
    | (cap. 4 YT+) |  | (cap. 4 Gran)|  | (cap. 4 WA+)|
    +------+-------+  +------+-------+  +------+-------+
           |                 |                  |
           +--------+--------+----------+-------+
                    |                   |
          +---------v--------+ +--------v---------+
          | Entity Resolution| | Searchable Corpus |
          |     (cap. 1)     | |     (cap. 5)      |
          +---------+--------+ +--------+----------+
                    |                   |
                    +--------+----------+
                    +--------v----------+
                    | Context Assembly  |
                    |     (cap. 7)      |
                    +--------+----------+
                             | feeds
              +--------------+--------------+
              |              |              |
    +---------v----+ +------v------+ +-----v----------+
    | Relationship | | Infra       | | All Runners     |
    | Intelligence | | Observer    | | (via context    |
    |   (cap. 6)   | |  (cap. 8)  | |  bundles)       |
    +--------------+ +-------------+ +----------------+
```

**Key dependency chains:**
- Action Frontend -> RL Loop -> Better Scoring -> Better Actions (THE compounding loop)
- Entity Resolution -> reliable signal processing -> every pipeline benefits
- Signal Sources -> data volume -> vector search justification -> searchable corpus
- Context Assembly triggered when 2+ runners need same context pattern
- Relationship Intelligence depends on meeting ingestion for owe/owed data

**No dependencies (can start anytime):**
- Entity Resolution + (Company/Person Index)
- Action Frontend + (MVP accept/dismiss)
- Scoring model completion (add 2 missing factors)
- New signal source connectors (following the pattern)

---

## Growth Model: Deepen + Broaden

```
DEEPEN (Track 1)                    BROADEN (Track 2)
Take content pipeline -> vision     Add new signal sources

YouTube + basic analysis            LinkedIn content
    |                                   |
+ Entity Resolution (Company Index)  YouTube subscriptions (passive)
    |                                   |
+ Action Scoring (wired in)          X (Twitter) content
    |                                   |
+ Preference Learning               Granola (meetings)
    |                                   |
+ Vector Search (semantic matching)  WhatsApp (ambient)
    |                                   |
+ Context Assembly (standardized)    Gmail (ambient)
    |                                   |
Full vision content pipeline         Multi-source intelligence

    <-- Infrastructure shared -->
    <-- Each deepening helps broadening -->
    <-- Each broadening stress-tests deepening -->
```
