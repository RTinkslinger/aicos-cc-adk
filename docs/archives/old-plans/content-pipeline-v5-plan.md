# Content Pipeline v5 — Architecture Plan
## From Content Pipeline to Signal Processor → Intelligence Engine
### Session 023 — March 3, 2026 (DRAFT — iterating)

---

## 1. Where v4 Breaks

v4 is battle-tested and works. But it was designed for 20 Fund Priority companies with file-based enrichment. Here's what breaks at scale:

| Constraint | v4 Reality | v5 Requirement |
|-----------|-----------|----------------|
| Portfolio coverage | 20 DeVC Fund Priority companies | 200+ companies (DeVC + Z47), growing 50-60/yr |
| Company context | Hardcoded enrichment .md files (11-18KB each) | Dynamic context from multiple sources (Notion, meetings, email, research) |
| Matching approach | Keyword pre-scan + load relevant enrichment files into subagent | Semantic retrieval across 200+ companies — can't prompt-stuff |
| Action volume | 36-76 per run, manageable in chat | Potentially hundreds per run at full portfolio scale — chat triage breaks |
| Action quality | Every thesis-tangential connection generates an action | Need impact threshold — not every connection deserves Aakash's attention |
| Action surface | Cowork chat (accept/dismiss in conversation) | Vercel frontend (accept/dismiss at digest level, consolidated view) |
| Deduplication | None — each content piece generates independent actions | Cross-content consolidation needed (similar actions from different videos cluster) |
| Signal sources | YouTube only | YouTube + Granola + email + WhatsApp + social (future) |
| Memory | Stateless per run (loads context fresh each time) | Persistent knowledge store that compounds across all signals |

**The fundamental shift:** v4 is a "content analysis pipeline." v5 is the first real implementation of the Signal Processor + Intelligence Engine from the system vision — content is just one observation surface.

---

## 2. Target Architecture (v5 Full Vision)

```
┌──────────────────────────────────────────────────────────────┐
│                    SIGNAL SOURCES                             │
│  YouTube │ Podcasts │ Granola │ Email │ WhatsApp │ Social     │
└─────┬────┴────┬─────┴────┬────┴───┬───┴────┬─────┴────┬──────┘
      │         │          │        │        │          │
      ▼         ▼          ▼        ▼        ▼          ▼
┌──────────────────────────────────────────────────────────────┐
│                  SIGNAL PROCESSOR                             │
│  Extract → Normalize → Embed → Store                         │
│  Each source has its own extractor, all produce              │
│  the same "signal" schema for the intelligence layer         │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                 KNOWLEDGE STORE                               │
│                                                               │
│  ┌─────────────┐   ┌──────────────────────────────────┐      │
│  │ Notion      │   │ Vector Store                      │      │
│  │ (Structured)│   │ (Unstructured / Semantic)         │      │
│  │             │   │                                    │      │
│  │ • Deal status│  │ • Company context embeddings       │      │
│  │ • IDS scores│   │ • Meeting note embeddings          │      │
│  │ • Portfolio │   │ • Content analysis embeddings      │      │
│  │   fields    │   │ • Email/WhatsApp signal embeddings │      │
│  │ • Relations │   │ • Research embeddings              │      │
│  │ • Actions   │   │ • Thesis evidence embeddings       │      │
│  └──────┬──────┘   └──────────┬───────────────────────┘      │
│         │                      │                              │
│         └──────────┬───────────┘                              │
│                    │                                          │
│              RETRIEVAL API                                    │
│   "Given this signal, what's relevant?"                      │
│   → Top-K companies + thesis threads + people                │
│   → Full structured context from Notion                      │
│   → Semantic context from vector store                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                INTELLIGENCE ENGINE                            │
│                                                               │
│  1. ANALYZE: Cross-reference signal against retrieved context │
│  2. SCORE: Impact assessment per company × thesis thread      │
│     - Does this change conviction? (High impact)              │
│     - Does this answer a Key Question? (High impact)          │
│     - Does this reveal competitive risk? (High impact)        │
│     - Is this reinforcing known info? (Low impact → filter)   │
│  3. FILTER: Only surface actions above impact threshold       │
│  4. GENERATE: Digest + filtered actions                       │
│  5. LEARN: Update embeddings, update thesis evidence          │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│              OPERATING INTERFACE (Vercel Frontend)            │
│                                                               │
│  /d/{slug}     — Content digest with inline action triage    │
│  /actions      — Consolidated action dashboard               │
│  /actions/{co} — Per-company action view                     │
│                                                               │
│  Accept/Dismiss → Notion API → Portfolio Actions Tracker     │
│                                                               │
│  Scheduled: Nightly consolidation task                        │
│  → Cluster similar actions across digests                    │
│  → Merge duplicates                                          │
│  → Promote recurring themes to P0                            │
│  → Archive stale dismissed actions                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. The Knowledge Store — Architecture Decision

Aakash's instinct: **Hybrid — Notion for structured, vector store for unstructured.** Here's the critique:

### Option A: Hybrid (Notion + Vector DB)
**How it works:** Notion remains source of truth for operational data (deal status, IDS scores, portfolio fields, relations, actions). A vector store (MongoDB Atlas + Voyage AI, or Pinecone, or pgvector) holds embeddings of unstructured data (meeting notes, content analysis, research, email context). At retrieval time, query both: vector store for semantic relevance, Notion for structured context.

| Pros | Cons |
|------|------|
| Clean separation: operational state vs. intelligence layer | Two systems to maintain and keep in sync |
| Notion stays familiar for team use | Every Notion update requires re-embedding |
| Vector store handles the scale problem for unstructured data | Cost: MongoDB Atlas / Pinecone aren't free |
| Industry-standard pattern for RAG systems | More moving parts = more failure modes |
| Can handle megabytes of meeting notes per company | Need a sync pipeline (Notion webhook → embed → store) |

### Option B: Vector DB as primary, Notion as input
**How it works:** MongoDB Atlas becomes the "brain." Notion data gets ingested alongside everything else. All retrieval goes through the vector store. Notion still exists for human use but isn't queried programmatically.

| Pros | Cons |
|------|------|
| Single retrieval interface | Big migration — everything currently queries Notion |
| Cleaner architecture long-term | Notion edits don't flow back without sync |
| Better for multi-surface ingestion | Team still uses Notion daily — can't replace it |
| Natural path to custom Agent SDK tier | Over-engineering for current needs |

### Option C: Notion + LLM-as-matcher (no vector DB yet)
**How it works:** Build a "company index" — a lightweight summary (100-150 words each) of all 200+ companies, generated from Notion data. At analysis time, pass the full index (~30-40KB) to the LLM and ask "which companies are most relevant to this content?" The LLM does the semantic matching. No vector infrastructure needed.

| Pros | Cons |
|------|------|
| Works TODAY with zero new infrastructure | Doesn't scale past ~500 companies comfortably |
| No sync pipeline, no hosting costs | Re-generates index each run (or caches) |
| LLM matching quality is actually excellent | Can't handle unstructured data at scale (meeting notes, emails) |
| Incremental — can migrate to vector DB later | Slightly slower (LLM call vs. vector similarity) |
| Keeps complexity low while we validate the approach | |

### Recommendation: **Start with Option C, migrate to Option A when signal surfaces expand**

Here's the IDS reasoning:

**Why not jump to vector DB now:**
- The immediate bottleneck is coverage (20 → 200 companies), not retrieval speed
- At 200 companies × 150 words = 30KB — comfortably fits in a single LLM context window for matching
- We haven't validated what the right retrieval patterns ARE yet. Building a vector DB before we know what queries we'll run = premature optimization
- The content pipeline is the only signal source today. Vector DB becomes essential when we add Granola + email + WhatsApp

**When to introduce vector DB (trigger conditions):**
1. We add a second signal source (Granola meeting notes) that generates significant unstructured data
2. Company count exceeds ~500 where the index approach gets unwieldy
3. We need sub-second retrieval for real-time applications (live meeting context)
4. We find ourselves re-embedding the same company context repeatedly

**The migration path is clean:** The "company index" approach generates the same data structures a vector DB would use. When we add embeddings, we're adding infrastructure under the same retrieval API, not rewriting the intelligence layer.

---

## 4. Expanded Portfolio Coverage — The Company Index

### Current State
- 20 companies with rich enrichment files (11-18KB each in `portfolio-research/`)
- Hardcoded page IDs in the pipeline skill
- Pre-scan matches content to companies via keyword search

### v5 Approach: Two-Tier Company Context

**Tier 1: Company Index (ALL 200+ companies)**
A lightweight, auto-generated index entry per company (~100-150 words):
```
COMPANY: [Name]
FUND: DeVC | Z47 | Both
SECTOR: [sector]
STAGE: [stage]
HEALTH: [Green/Yellow/Red]
ONE-LINER: [what they do, from Notion description]
KEY QUESTIONS: [top 2-3 open questions]
THESIS THREADS: [connected thesis names]
COMPETITIVE CONTEXT: [key competitors, 1 line]
LAST IDS: [date of last meaningful interaction]
```

**How it's built:**
1. Query Portfolio DB for ALL companies (not just Fund Priority)
2. For each, extract key structured fields from Notion
3. If an enrichment file exists in `portfolio-research/`, pull the executive summary
4. Generate the index entry
5. Cache the index (regenerate weekly or on-demand)

**Total size:** 200 × 150 words = 30K words ≈ 40K tokens. Fits comfortably in a matching prompt.

**Tier 2: Deep Context (retrieved on match)**
When the matching stage identifies a company as relevant to content, THEN load the full context:
- Notion fields (all 94 Portfolio DB fields)
- Enrichment file (if exists)
- Recent actions from Portfolio Actions Tracker
- Recent Content Digest connections
- Thesis thread connections with evidence

Only 5-10 companies get Tier 2 context per analysis — keeps subagent prompts manageable.

### The Matching Flow

```
Content Signal (transcript / notes / article)
        │
        ▼
┌─────────────────────────────────────┐
│  STAGE 1: Semantic Matching         │
│  Input: signal + full company index │
│  LLM call: "Which of these 200     │
│  companies are most relevant to     │
│  this content? Rank top 10 with     │
│  relevance reasoning."              │
│  Output: ranked company list        │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  STAGE 2: Deep Context Load         │
│  For top 5-10 matched companies:    │
│  - Full Notion data                 │
│  - Enrichment file (if exists)      │
│  - Recent actions & digests         │
│  - Thesis thread context            │
│  Build subagent context package     │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  STAGE 3: Analysis + Actions        │
│  Subagent with: signal + deep       │
│  context for matched companies +    │
│  thesis threads                     │
│  Output: structured analysis JSON   │
└─────────────────────────────────────┘
```

### Z47 Portfolio Coverage
Z47's portfolio likely has different Notion structure than DeVC's Portfolio DB. Two approaches:

1. **If Z47 portfolio is in the same Notion workspace:** Map the database, add to the index generation query
2. **If Z47 portfolio is in a separate system:** Build a one-time import, maintain a lightweight entry in the company index

**Action needed:** Determine where Z47 portfolio data lives and what fields are available.

---

## 5. Impact Scoring & Action Filtering

### The Problem
At 20 companies, generating 8-12 actions per content piece is manageable. At 200 companies, every piece of content will have SOME tangential connection to MANY companies. Without filtering, we'd generate 50-100 actions per video — noise overwhelms signal.

### The Impact Threshold Model

For each potential action, compute an **Impact Score** before generating it:

```
Impact Score = f(
    conviction_change_potential,   — Could this change Aakash's conviction on the company? (0-10)
    key_question_relevance,        — Does this address an open Key Question? (0-10)
    time_sensitivity,              — Is there a reason to act NOW? (0-10)
    action_novelty,                — Is this a new insight or a rehash? (0-10)
    company_priority,              — How important is this company in the portfolio? (multiplier)
)
```

**Thresholds:**
- **Impact ≥ 7:** Generate action (high-confidence recommendation)
- **Impact 4-6:** Generate but tag as "Low Confidence" — appears in expanded view, not primary list
- **Impact < 4:** Log as context enrichment only — updates company embeddings but doesn't generate a discrete action

### Deduplication & Consolidation

**Per-digest dedup (at generation time):**
- If two actions for the same company are essentially the same thing, merge them
- If a thesis update action duplicates what auto-sync already handles, drop it

**Cross-digest consolidation (scheduled nightly task):**
- Query Portfolio Actions Tracker for Status = "Proposed" from last 7 days
- Cluster actions by: company × action type × theme
- If 3+ actions for the same company on the same theme → merge into a single high-priority action with all evidence
- If an action was already accepted/in-progress and a new similar one comes in → flag as "reinforcing evidence" rather than creating duplicate
- Promote recurring themes: if the same thesis concern appears across 3+ content pieces → auto-escalate to P0

### Thesis Thread Impact Filtering

Same principle for thesis threads. Not every content-thesis connection deserves a Thesis Tracker update.

**Update threshold:**
- **New evidence that changes conviction** → Update Evidence For/Against + conviction level
- **New Key Question identified** → Add to Key Questions
- **New company identified for the thesis** → Add to Key Companies
- **Reinforcing already-known evidence** → Skip update (log for audit trail only)
- **New thesis thread emerging** → Create only when 2+ independent signals converge (currently we create on first signal — too aggressive)

---

## 6. Action Frontend (Vercel Digest Site)

### Phase 1: Accept/Dismiss on Digest Pages (v5.0)

Each digest page (`/d/{slug}`) already renders `proposed_actions`. Add:

1. **Action cards** with Accept / Dismiss buttons
2. **Backend API route** (`/api/actions`) that:
   - Reads actions from the digest JSON (or from Notion)
   - On Accept: calls Notion API to update Portfolio Actions Tracker status → "Accepted"
   - On Dismiss: calls Notion API to update status → "Dismissed"
3. **Auth**: Simple token-based (Aakash is the only user). Store Notion API key as env var in Vercel.
4. **Optimistic UI**: Button press immediately updates local state, API call happens async

**Data flow:**
```
Digest Page → Click Accept → API Route → Notion Update → Confirm
```

**What changes in the pipeline:**
- Pipeline still writes to Notion (Portfolio Actions Tracker) with Status = "Proposed"
- Pipeline still writes digest JSON to Vercel
- The DIGEST JSON now includes action IDs (Notion page IDs) so the frontend can target updates
- Accept/dismiss happens on the frontend instead of Cowork chat

### Phase 2: Consolidated Action Dashboard (v5.1+)

New route: `/actions` — aggregated view across all digests

**Views:**
- **By Priority:** P0 → P1 → P2 → P3 with counts per category
- **By Company:** Group actions under each company, show total pending count
- **By Thesis:** Group actions under thesis threads
- **Pending Review:** All Proposed actions, sorted by priority × recency
- **Recently Accepted:** Last 7 days of accepted actions for tracking

**Features:**
- Bulk accept (select multiple → accept all)
- Filter by source (Content Pipeline, Agent, Meeting)
- Search across actions
- Company-level summary: "Unifize: 3 pending actions (1 P0, 2 P1) — thesis connections: SaaS Death, Agentic AI"

### Phase 3: The Full Operating Interface (v5.2+)

The digest site evolves into the AI CoS operating interface:
- Digest consumption (existing)
- Action triage (Phase 1-2)
- Portfolio dashboard (company-level view with health, actions, last IDS, thesis connections)
- Thesis tracker view (thesis threads with evidence, conviction, connected companies)
- Meeting optimizer output (when "Optimize My Meetings" ships)

This is the progression from "content digest viewer" to "AI CoS cockpit."

---

## 7. Multi-Surface Signal Processing (Future)

The content pipeline is Signal Source #1. Here's how each additional source maps to the same architecture:

### Granola Meeting Notes (Signal Source #2 — highest value add)
- **Extractor:** Granola MCP tool → extract transcript + attendees + topic
- **Signal schema:** Same as content but with: meeting_type, attendees (linked to Network DB), IDS signals extracted
- **Matching:** Attendees auto-link to companies. Semantic matching for thesis connections.
- **Actions:** Post-meeting follow-ups, IDS updates, conviction changes, intro suggestions
- **Digest:** Meeting digest (lighter format than content digest — more like a structured IDS note)

### Email (Signal Source #3)
- **Extractor:** M365 MCP → extract emails matching patterns (founder updates, investor comms, intro requests)
- **Signal schema:** Sender/recipients linked to Network DB, intent classification (meeting request, update, FYI, risk flag)
- **Matching:** Sender → company → portfolio/pipeline. Content → thesis connections.
- **Actions:** Respond, schedule, flag for attention, update IDS

### WhatsApp (Signal Source #4 — requires custom integration)
- **Extractor:** WhatsApp Business API or screen capture
- **Signal schema:** Sender, content, links shared, screengrabs
- **Matching:** Same as email but more casual signals — links to process, people to look up
- **Actions:** Process link, enrich person, add to network, schedule meeting

### The Key Principle: Same Brain, Different Eyes

Every signal source produces a normalized "Signal" object:
```typescript
interface Signal {
  source: "youtube" | "granola" | "email" | "whatsapp" | "social";
  content: string;           // the raw content / transcript
  entities: {                // extracted people, companies, topics
    people: string[];
    companies: string[];
    topics: string[];
  };
  metadata: Record<string, any>;  // source-specific metadata
  timestamp: string;
}
```

The Intelligence Engine doesn't care WHERE the signal came from. It runs the same flow: match → retrieve context → analyze → score impact → generate actions → present.

---

## 8. Vector DB Architecture (When Triggered)

When we cross the trigger conditions (second signal source, or 500+ companies, or need sub-second retrieval):

### Recommended Stack: Supabase pgvector (or MongoDB Atlas + Voyage)

**Why Supabase pgvector first:**
- Postgres-based — familiar, simple, hosted
- Free tier is generous (500MB storage, enough for years)
- pgvector handles cosine similarity natively
- Same Supabase project can host the action API (replacing Notion API calls for action CRUD)
- If we outgrow it, migration to MongoDB Atlas / Pinecone is straightforward

**Alternatively, MongoDB Atlas + Voyage AI:**
- Voyage AI embeddings are best-in-class for retrieval
- MongoDB Atlas Vector Search is purpose-built
- Better for complex document structures (nested company profiles)
- Higher cost but more capable at scale

**What gets embedded:**
1. **Company summaries** (updated weekly from Notion): ~200 entries × 768-dim vectors
2. **Meeting note chunks** (from Granola): chunked at ~500 words, embedded per chunk
3. **Content analysis summaries** (from Content Digest DB): per-video embeddings
4. **Email context** (from M365): key emails embedded, linked to companies/people
5. **Thesis thread evidence** (from Thesis Tracker): each evidence entry embedded separately
6. **Research reports** (from portfolio-research/): chunked and embedded

**Embedding model:** Voyage AI `voyage-3` (best for retrieval) or Anthropic's own embeddings (if/when available)

**Index size estimate (Year 1):**
- 200 companies × 3-5 vectors each = ~1000 vectors
- 500 meetings × 5 chunks each = ~2500 vectors
- 200 content analyses × 1 each = ~200 vectors
- 1000 emails × 1 each = ~1000 vectors
- Total: ~5000 vectors → trivial for any vector DB

---

## 9. System Vision v2 → v3 Updates

The system vision v2 is well-framed but missing operational details that v5 planning reveals. Proposed updates:

### What to ADD to the vision:

1. **The Knowledge Store layer** — v2 talks about the "Network Graph" as the data layer but doesn't address how to handle the scale of unstructured data (meetings, emails, content). Add the hybrid Notion + vector store architecture.

2. **Impact scoring and filtering** — v2's Intelligence Engine assumes all connections are worth surfacing. At scale, the impact threshold model becomes essential. The engine needs to learn what Aakash actually acts on vs. dismisses.

3. **The Action Frontend** — v2's Operating Interface is WhatsApp-first. But before WhatsApp, the Vercel digest site becomes the first real Operating Interface — content digests + action triage + consolidated views. This is the stepping stone.

4. **The Signal Processor specification** — v2 describes the Signal Processor abstractly. v5 gives it a concrete architecture: source-specific extractors → normalized signal schema → embedding → storage → retrieval API.

5. **The consolidation/learning loop** — v2 says "it learns from revealed preferences." v5 specifies HOW: nightly consolidation task clusters actions, tracks accept/dismiss ratios per company × action type, adjusts impact scoring weights.

6. **The IDS between Cowork 10x and Agent SDK 100x** — v2 has a gap between "build in Cowork" and "build custom agents." v5 fills the gap: the Vercel frontend + API routes + vector store can be the persistent infrastructure that survives the transition. Cowork builds the intelligence. The frontend serves it. When custom agents come, they use the same Knowledge Store and Frontend.

### What to REVISE:

1. **"Optimize My Trip" as first capability** → The content pipeline evolution (v5) is actually building more of the Intelligence Engine infrastructure than a trip optimizer would. Revise the build order: Content Pipeline v5 → Action Frontend → Knowledge Store → THEN "Optimize My Meetings" (which by that point has the infrastructure it needs).

2. **Three agents → fewer, more distinct layers** → The "three agent" framing (Intelligence Engine, Signal Processor, Operating Interface) still works but should be framed as layers, not separate agents. In practice they share infrastructure (knowledge store, Notion, vector DB).

---

## 10. IDS Milestones (Layered Build Plan)

### v5.0 — Coverage + Matching + Impact Filtering
**Sessions: 2-3 | Value: Pipeline now covers full portfolio**

**Build:**
1. Company Index Generator
   - Script that queries Portfolio DB for ALL companies (DeVC + Z47)
   - Generates lightweight index entries (~150 words each)
   - Caches to `data/company-index.json`
   - Regenerated on-demand or weekly

2. Two-Stage Matching
   - Stage 1: LLM matches content against full company index → top 10 relevant companies
   - Stage 2: Load Tier 2 deep context only for matched companies
   - Replace hardcoded enrichment file loading

3. Impact Scoring Gate
   - Compute Impact Score for each potential action
   - Only generate actions above threshold
   - Tag low-confidence actions separately

4. Updated Pipeline Skill (v5)
   - New SKILL.md incorporating above changes
   - Backwards-compatible with existing queue/digest flow
   - Thesis matching also uses index approach (not hardcoded list)

**Validation:** Process 3 videos, verify that (a) companies beyond the original 20 are matched, (b) action count is filtered to high-impact only, (c) quality per action is maintained or improved.

### v5.1 — Action Frontend (Minimal)
**Sessions: 2 | Value: Triage moves to mobile-friendly web UI**

**Build:**
1. API routes on Vercel digest site
   - `POST /api/actions/[id]/accept` → Notion update
   - `POST /api/actions/[id]/dismiss` → Notion update
   - `GET /api/actions/pending` → List all pending actions
   - Auth: simple API key in header (Aakash only user)

2. Action cards on digest pages
   - Render proposed_actions with Accept/Dismiss buttons
   - Optimistic UI with loading states
   - Action IDs link to Notion pages

3. Pipeline updates
   - Digest JSON includes Notion page IDs for each action
   - Pipeline creates actions in Notion FIRST, then includes IDs in digest JSON
   - Digest page reads actions from JSON + checks Notion for current status

**Validation:** Process a batch, open digest on phone, accept/dismiss 5 actions, verify Notion updates correctly.

### v5.2 — Consolidation + Action Dashboard
**Sessions: 1-2 | Value: Cross-content action intelligence**

**Build:**
1. Nightly consolidation scheduled task
   - Query Portfolio Actions Tracker for recent Proposed actions
   - Cluster by company × action type × theme
   - Merge duplicates, promote recurring themes
   - Report: "Consolidated 47 actions → 22 unique, 3 promoted to P0"

2. `/actions` dashboard route
   - By Priority, By Company, By Thesis views
   - Bulk operations
   - Search and filter

**Validation:** After 2 weeks of pipeline runs, consolidation task produces meaningful clusters and the dashboard is the primary triage surface.

### v5.3 — Knowledge Store (Vector DB)
**Sessions: 2-3 | Value: Semantic retrieval across all company context**

**Trigger:** When we add Granola meeting notes as second signal source, OR when company count exceeds threshold.

**Build:**
1. Vector store setup (Supabase pgvector or MongoDB Atlas)
2. Embedding pipeline: company summaries + enrichment chunks → vectors
3. Retrieval API: given signal content, return top-K relevant context
4. Replace LLM-based matching with hybrid (vector similarity + LLM verification)
5. Add meeting note ingestion (Granola MCP → chunk → embed → store)

### v5.4 — Multi-Surface Ingestion
**Sessions: 2-3 per source | Value: Brain sees everything, not just YouTube**

**Build (in priority order):**
1. Granola meeting notes → Signal Processor
2. Podcast transcripts (same extractor pattern as YouTube)
3. Email signals (M365 MCP, filtered patterns)
4. Article/bookmark processing

### v5.5 — The Brain
**Sessions: Ongoing | Value: The Intelligence Engine from the vision**

At this point, the infrastructure exists to:
- Continuously ingest signals from all surfaces
- Semantically retrieve relevant context at sub-second speed
- Score impact and filter noise
- Present actions through a proper frontend
- Learn from accept/dismiss patterns
- Consolidate across sources

This IS the Intelligence Engine. The next step is the "Optimize My Meetings" capability — which now has all the context it needs to actually score and rank Aakash's universe.

---

## 11. Open Questions (To Resolve Before Building)

1. **Z47 Portfolio DB:** Where does Z47 portfolio data live? Same Notion workspace? What fields are available? Mapping this determines how quickly we can build the full company index.

2. **Notion API for Action Frontend:** The Vercel site needs to call Notion API to update action statuses. This means storing a Notion API key as a Vercel env var. Is that acceptable, or do we want a middleware layer?

3. **Company Index refresh cadence:** Weekly? Daily? On-demand? Affects whether we cache or generate dynamically.

4. **Impact threshold calibration:** The initial thresholds will be guesses. How many cycles of accept/dismiss data do we need before the thresholds auto-adjust?

5. **Existing enrichment files:** The 20 enrichment files in `portfolio-research/` are high-quality but will become stale. Should we auto-regenerate them periodically using Parallel AI deep research? Or deprecate them in favor of vector-stored context?

6. **DeVC vs Z47 action routing:** Actions for DeVC portfolio companies and Z47 portfolio companies may need different routing (different teams, different follow-up processes). Does the Pipeline Actions Tracker need a "Fund" field?

7. **Authentication for digest site:** Currently static with no auth. Adding action triage means adding auth. Options: simple shared secret, Vercel Auth, Clerk.dev, or just a URL-based token since Aakash is the only user.

---

## 12. Summary: What Changes vs. What Stays

### Stays the Same
- YouTube extractor (Mac-side `yt` CLI)
- Queue-based flow (JSON files in queue/)
- Subagent architecture (parallel Task per video)
- Content Digest DB in Notion (same schema)
- Portfolio Actions Tracker in Notion (same schema + possible new Fund field)
- Thesis Tracker sync protocol
- HTML digest generation + Vercel deployment
- PDF digest generation

### Changes
- Company matching: keyword pre-scan → two-stage semantic matching via company index
- Company coverage: 20 hardcoded → 200+ from full portfolio query
- Action generation: everything → impact-scored and filtered
- Action triage: Cowork chat → Vercel frontend
- Action quality: standalone per-digest → cross-digest consolidated + deduped
- Context loading: file-based enrichment → index + on-demand deep context retrieval
- Future: single-source → multi-surface signal processing
- Future: stateless → persistent knowledge store (vector DB)
