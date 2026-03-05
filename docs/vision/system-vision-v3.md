# Aakash AI CoS — System Vision v3
## "What's Next?"

### The Reframe

v1 designed a task automator — morning briefs, post-meeting capture, weekly reviews. That's plumbing.

v2 reframed around **"Who should I meet next?"** — network optimization for meeting slot allocation. Better, but still too narrow. It only covered one slice of the action space.

v3 recognizes the actual problem: **Aakash and his AI CoS are a singular entity** optimizing across a full action space to maximize value from a stakeholder space. The AI CoS doesn't just answer "who should I meet?" — it answers **"What's next?"** across everything Aakash does.

### The True Optimization Problem

**Stakeholder Space** (two data models):
- **Companies** — Portfolio companies, pipeline companies, thesis-relevant companies. ~200 today, growing 50-60/year.
- **Network** — People connected to companies, thesis threads, and each other. 400+ and growing.

**Action Space** (everything Aakash can do):

| Action Type | With Stakeholders? | What It Generates |
|-------------|-------------------|-------------------|
| Meetings | Yes — founders, investors, operators, thesis contacts | New actions (follow-ups, IDS updates, intros, investment decisions) |
| Calls / WhatsApp | Yes — quick syncs, async communication | New actions (schedule meeting, share info, make intro) |
| Email | Yes — formal communication, updates, requests | New actions (respond, schedule, flag, follow up) |
| Content consumption | No — YouTube, podcasts, articles, X, LinkedIn | Stakeholder actions (reach out to person, update thesis, evaluate company) |
| Research / Analysis | No — deep dives, sector analysis, thesis building | Stakeholder actions (new thesis thread, pipeline addition, conviction change) |
| Information digestion | No — reading meeting notes, reviewing portfolio updates | Stakeholder actions (follow-up needed, concern flagged, opportunity identified) |

**The loop:**

```
Do actions → Generate new actions → Prioritize → Do highest-value actions → Repeat
```

The AI CoS sits in the middle of this loop. It continuously helps Aakash prioritize across the full action space, not just the meeting calendar.

**Two categories of actions:**
1. **Stakeholder actions** — meetings, calls, emails, intros, follow-ups. These are WITH people/companies. They generate new actions.
2. **Intelligence actions** — content consumption, research, information analysis. These are NOT with stakeholders but they generate stakeholder actions.

The system maximizes **investment returns** as the end goal. Everything else — ecosystem building, personal brand, thesis influence, Collective growth — are inputs to that function.

### The Four Priority Buckets (Unchanged)

All actions, whether stakeholder or intelligence, ultimately serve these buckets:

| Priority | Objective | Weight | When |
|----------|-----------|--------|------|
| 1 | **New cap tables** — Expand network to be on more amazing companies' cap tables | Highest | Always |
| 2 | **Deepen existing cap tables** — Continuous IDS on portfolio to make ownership increase decisions | High | Always |
| 3 | **New founders/companies** — Meet potential backable founders via DeVC Collective pipeline | High | Always |
| 4 | **Thesis evolution** — Meet interesting people who keep thesis lines evolving | Lower when conflicted with 1-3, but **highest when capacity exists** | Fill remaining capacity, but never zero |

---

## THE ARCHITECTURE: Three Layers, One Brain

### Layer 1: Signal Processor (The Eyes and Ears)

The Signal Processor observes every surface Aakash touches and converts raw signals into structured intelligence the engine can reason about. Each signal source represents one pathway in the action space.

**Every signal source produces a normalized Signal:**

```typescript
interface Signal {
  source: "youtube" | "granola" | "email" | "whatsapp" | "social" | "research";
  content: string;           // raw content / transcript
  entities: {                // extracted people, companies, topics
    people: string[];
    companies: string[];
    topics: string[];
  };
  metadata: Record<string, any>;  // source-specific metadata
  timestamp: string;
}
```

**The key principle: Same Brain, Different Eyes.** The Intelligence Engine doesn't care WHERE the signal came from. It runs the same flow for all sources: match → retrieve context → analyze → score impact → generate actions → present.

**Signal sources (in build order):**

| Source | Action Type | Status | Notes |
|--------|-------------|--------|-------|
| YouTube / Podcasts | Intelligence action | ✅ Live (v4) | Content Pipeline — first Signal Processor |
| Granola Meeting Notes | Stakeholder action output | Next | Highest value-add: direct IDS signal from meetings |
| Email (M365) | Stakeholder action | Future | Founder updates, investor comms, intro requests |
| WhatsApp | Stakeholder action | Future | Requires custom integration |
| LinkedIn / X | Intelligence action | Future | Screengrabs, bookmarks, connections |
| Market Signals | Passive intelligence | Future | Funding announcements, exec changes, press |

Each iteration on a new signal source gets us closer to the full vision. We don't need all sources to ship value — each one independently improves the loop.

### Layer 2: Intelligence Engine (The Brain)

The Intelligence Engine receives signals, retrieves relevant context, analyzes impact, and generates prioritized actions. It's the core of the "What's Next?" system.

#### 2a. The Knowledge Store

**Notion (Structured — operational state):**
- Deal status, pipeline stage, conviction levels
- IDS scores and open questions
- Portfolio fields (metrics, health, team)
- Relationships and connections
- Actions (proposed, accepted, completed)
- Thesis threads (evidence, conviction, key questions)

**Vector Store (Unstructured — semantic intelligence):**
- Company context embeddings (summaries, enrichment, research)
- Meeting note chunks (from Granola)
- Content analysis summaries (from Content Pipeline)
- Email context (from M365)
- Thesis evidence embeddings

**Build strategy:** Start with LLM-as-matcher (Notion + company index in the prompt). Add vector DB when triggered by: second signal source (Granola), 500+ companies, or need for sub-second retrieval.

#### 2b. The Scoring Models

**Action Scoring (primary — "What's next?"):**

Every potential action gets scored before being surfaced:

```
Action Score = f(
    bucket_impact,                 — Which bucket(s) does this serve? How much?
    conviction_change_potential,   — Could this change investment conviction?
    key_question_relevance,        — Does this address an open Key Question?
    time_sensitivity,              — Is there a reason to act NOW?
    action_novelty,                — Is this a new insight or a rehash?
    stakeholder_priority,          — How important is this company/person?
    effort_vs_impact               — Quick win or heavy lift?
)
```

**Thresholds:**
- **Score ≥ 7:** Surface as action (high-confidence recommendation)
- **Score 4-6:** Tag as "Low Confidence" — available but not promoted
- **Score < 4:** Context enrichment only — updates the Knowledge Store, no discrete action

**People Scoring (for meeting optimization — subset of action scoring):**

```
Person Score = f(
    bucket_relevance,      — which of the 4 objectives does meeting this person serve?
    current_ids_state,     — where are they in the IDS journey?
    time_sensitivity,      — reason to meet NOW vs later?
    info_gain_potential,   — what will Aakash learn?
    network_multiplier,    — who else does this person connect to?
    thesis_intersection,   — sits at a thesis convergence point?
    relationship_temp,     — warm/cold? trend?
    geographic_overlap,    — same city?
    opportunity_cost       — what's missed by NOT meeting them?
)
```

The People Scoring Model is a specialization of the Action Scoring Model — applied specifically when the action type is "meeting." The system doesn't need two separate brains. Meeting optimization is one output of the general action optimizer.

#### 2c. The Learning Loop

The system tracks what Aakash acts on vs. dismisses:

- **Accept/dismiss ratios** per company × action type → weight adjustment
- **Meeting outcomes** (when Granola is connected) → revealed preference learning
- **Nightly consolidation** → cluster similar actions, merge duplicates, promote recurring themes, archive stale
- **Thesis thread tracking** → which thesis threads generate the most acted-on signals?

Over time, the scoring model calibrates to Aakash's actual behavior, not just stated priorities. This is how the AI CoS becomes a true extension of Aakash — not just following rules, but learning judgment.

#### 2d. The Decision Layer

The scoring models feed concrete outputs:

**Action triage (daily):** "Here are your 12 highest-priority actions across content, meetings, follow-ups, and research. 4 are time-sensitive."

**Meeting optimization (weekly/trip):** "For your SF trip: 25 people scored and ranked. Your mix: 8 portfolio (bucket 1-2), 10 new founders (bucket 3), 4 thesis contacts (bucket 4), 3 reconnections."

**Slot filling (real-time):** "Meeting cancelled. [Person X] is the highest-scored replacement — pre-computed and ready."

**Signal integration (continuous):** "This YouTube video reveals competitive intel on 3 portfolio companies. Here are the 2 actions worth your time."

**Gap analysis (periodic):** "You're underweighting bucket 2 — 4 portfolio companies have stale IDS. Your thesis threads in cybersecurity have the most unresolved questions."

### Layer 3: Operating Interface (The Voice)

The Operating Interface is how Aakash interacts with the "What's Next?" system. It evolves in phases:

#### Phase 1: Content Digests + Action Triage (Current → v5.1)

The Vercel digest site (`aicos-digests.vercel.app`) — the first Operating Interface:

- Content digests — Mobile-friendly, shareable
- Action cards — Accept/Dismiss on each digest
- Consolidated view — `/actions` route for all pending actions

#### Phase 2: AI CoS Cockpit (v5.2+)

The digest site evolves:
- Portfolio dashboard
- Thesis tracker view
- Meeting optimizer output
- Cross-source signal feed

#### Phase 3: WhatsApp (Agent SDK Tier)

The system's intelligence moves to WhatsApp:
- Proactive recommendations
- Quick capture (screengrab → instant scoring)
- Meeting prep (pre-calendar-event IDS brief)
- Voice note processing

**The key principle:** Aakash and the AI CoS are a singular entity. The Operating Interface isn't a tool Aakash uses — it's the medium through which the combined entity operates. "What's next?" is not a question Aakash asks the system. It's the question the system always has an answer to.

---

## THE DATA LAYER: The Network Graph

```
Person Node:
  - identity: name, company, role, location, archetype
  - enrichment: Explorium data, LinkedIn, X
  - ids_state: conviction level, open questions, last interaction
  - bucket_scores: [B1, B2, B3, B4]
  - composite_score: current priority
  - geographic: home base, travel
  - relationship: temperature, trajectory
  - connections: edges to people, companies, thesis threads
  - pending_actions: actions generated by/for this person

Company Node:
  - pipeline_state: TOFU/MOFU/BOFU, conviction, deal status
  - portfolio_state: investment, metrics, concerns, follow-on status
  - ids_trail: all notes, meetings, signals
  - connections: founders, team, investors, competitors
  - embeddings: vector representations (when active)
  - pending_actions: actions generated for this company

Thesis Node:
  - topic, domain, conviction level, open questions
  - evidence: research, meetings, content, with direction (for/against/mixed)
  - connections: people, companies
  - action_generation_rate: how many actions this thesis produces (learning signal)
```

---

## THE BUILD ORDER

Each iteration ships value and gets closer to the full vision. We don't need everything to start winning.

### Phase 1: Content Pipeline v5 (Signal Processor + Intelligence Engine via content)
**Status: v4 live, v5 planned**

Expand content pipeline to: full portfolio coverage (200+ companies), semantic matching, impact scoring, multi-source readiness. This is the first real Signal Processor + Intelligence Engine implementation.

**Why first:** Builds the context store, validates matching, creates action patterns. Everything downstream needs this.

### Phase 2: Action Frontend (Operating Interface v1)
**Status: Digest site live, action triage planned**

Accept/dismiss on digest pages → consolidated dashboard → portfolio views. The first proper Operating Interface.

**Why second:** Without triage surface, increased action volume from Phase 1 overwhelms chat workflow.

### Phase 3: Knowledge Store (persistent memory)
**Status: Planned — triggers on second signal source**

Vector DB (Supabase pgvector or MongoDB Atlas + Voyage AI). Embedding pipeline for all context types. Hybrid retrieval.

**Why third:** LLM-as-matcher works for YouTube-only at 200 companies. Second signal source demands proper embeddings.

### Phase 4: Granola + Multi-Surface (expand the eyes)
**Status: Planned**

Add signal sources: Granola meeting notes → podcast transcripts → email → WhatsApp. Each source = one new extractor + same brain + same frontend.

**Why this order:** Granola is highest value (direct stakeholder action output → new actions). Each source independently improves the loop.

### Phase 5: Meeting Optimizer ("Who should I meet next?" as feature)
**Status: Planned — needs Phases 1-4**

Full People Scoring Model with context from all signal sources. Trip planning, weekly optimization, real-time slot filling.

**Why now:** By Phase 5, the system has context, memory, learned preferences, and multi-surface awareness. The meeting optimizer can be truly intelligent.

### Phase 6: Always-On Intelligence (Agent SDK)
**Status: Vision**

Continuous signal ingestion, proactive WhatsApp recommendations, real-time optimization, 24/7 compound intelligence. The full singular entity.

---

## WHAT 100x LOOKS LIKE

**Without AI CoS:** Aakash's actions are driven by: who reaches out, what Sneha schedules, what he remembers, what his fuzzy mental map surfaces. Maybe 30-40% of his action space is optimally allocated.

**With AI CoS:** Every action slot — meetings, follow-ups, research, content consumption — is informed by a scored, contextual analysis of his entire stakeholder space. The system catches what he'd miss: the second-degree connection, the content signal that changes conviction on a portfolio company, the thesis thread that reveals a new investment opportunity. Maybe 70-80% optimal allocation.

Across 7-8 meetings/day, hundreds of content signals per week, and a constantly evolving portfolio of 200+ companies — going from 40% to 80% optimal action allocation is a massive compounding effect on investment quality and returns.

The 100x comes from the compound effect: better actions → better IDS → better decisions → better outcomes → better network → even better actions. The flywheel accelerates because the AI CoS keeps the full picture updated and the optimization running continuously.

---

## CHANGELOG

| Version | Date | Key Changes |
|---------|------|-------------|
| v1 | Dec 2024 | Task automation framing (morning briefs, meeting capture) |
| v2 | Jan 2025 | Network optimization: "Who should I meet next?" Four buckets, People Scoring Model, Three Agents |
| v3 | Mar 2026 | **"What's Next?"** — Full action space optimization, not just meetings. Stakeholder space (companies + network) × Action space (stakeholder actions + intelligence actions). End goal: investment returns. Aakash + AI CoS = singular entity. Three agents → three layers sharing infrastructure. Build order revised based on 23 sessions: Content Pipeline → Action Frontend → Knowledge Store → Multi-Surface → Meeting Optimizer → Always-On. Action Scoring Model (general) subsumes People Scoring Model (meetings). Added: Impact filtering, Consolidation Engine, Learning Loop, normalized Signal schema. Operating Interface starts as web (Vercel), evolves to WhatsApp. |
