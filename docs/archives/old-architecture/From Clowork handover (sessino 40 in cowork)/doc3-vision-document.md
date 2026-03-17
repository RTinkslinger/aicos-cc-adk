# AI Chief of Staff — Vision Document v4
## "What's Next?" — The Definitive System Vision
**March 2026 · Synthesized from vision-v1, v2, v3, 39 sessions of iteration, and the Architecture Brainstorm**

> This document is the canonical vision reference for the AI CoS system. It supersedes vision-v1 (Dec 2024), v2 (Jan 2025), and v3 (Mar 2026) by incorporating all three plus the architecture brainstorm decisions and 39 sessions of implementation ground truth. Hand this to any new Claude session as the complete briefing alongside Doc 1 (brainstorm summary) and Doc 2 (architecture specification).

---

## 1. The Premise

Aakash Kumar operates as Managing Director of Z47 (~$550M AUM) and DeVC (~$60M AUM). He meets 7-8 people per day, consumes content across 5+ surfaces, builds thesis through rabbit holes, runs IDS (Increasing Degrees of Sophistication) on hundreds of people and companies simultaneously, and manages a growing DeVC Collective of external evaluators — all while living on WhatsApp and mobile.

Every transition between capture → connection → action leaks signal. The entire system runs on fuzzy mental memory with no intelligence layer managing time allocation, follow-up, or dot connection.

The AI Chief of Staff exists to close this gap. Not as a tool Aakash uses — as an extension of how he thinks and operates.

**Aakash and his AI CoS are a singular entity** optimizing across a full stakeholder and action space to maximize investment returns.

---

## 2. The Evolution of the Question

Each vision iteration sharpened the core question:

| Version | Date | Question | Limitation |
|---------|------|----------|------------|
| v1 | Dec 2024 | "What happened and what's next on my to-do list?" | Task automation — morning briefs, post-meeting capture. Plumbing. |
| v2 | Jan 2025 | "Who should I meet next?" | Network optimization — but only covered meeting slots. One slice of the action space. |
| v3 | Mar 2026 | "What's next?" | Full action space optimization across stakeholder + intelligence actions. The right question. |
| v4 | Mar 2026 | **"What's next?" — with learning, infrastructure, and a build path grounded in 39 sessions of reality** | This document. |

The question hasn't changed from v3. What v4 adds: the concrete architecture decisions from the brainstorm session (MCP as hook layer, Agent SDK narrow runners, Preference Store as learning foundation, Postgres migration path), the corrections from implementation reality (no Attio, Notion rate limits, sandbox constraints, subagent patterns), and the synthesis of v1's Agent SDK depth with v3's action-space framing.

---

## 3. The Optimization Problem

### 3.1 The Stakeholder Space

Two data models, both in Notion today:

**Companies** (~200 today, growing 50-60/year):
- Pipeline companies at various conviction levels
- Portfolio companies under continuous IDS
- Thesis-relevant companies being tracked
- Stored in Companies DB (49 fields, Deal Status 3D matrix: pipeline stage × conviction × active/inactive) and Portfolio DB (94 fields)

**Network** (400+ contacts and growing):
- Founders, investors, operators, thesis contacts, Collective members
- Connected to companies, thesis threads, and each other
- Stored in Network DB (40+ fields, 13 archetypes: EXT Target, EXT Active, EXT Dormant, GP/Partner, LP/Allocator, Operator, Founder/CEO, Board Member, Advisor, Media, Academic, Government, Collective Member)

### 3.2 The Action Space

Everything Aakash can do falls into two categories:

**Stakeholder Actions** — with people/companies. Generate new actions.
- Meetings (7-8/day — the highest-bandwidth channel)
- Calls / WhatsApp (quick syncs, async communication)
- Email (formal communication, updates, requests)
- Intros (connecting two nodes in the network — creates value for both)
- Follow-ups (the most-leaked action type today)

**Intelligence Actions** — not with stakeholders, but generate stakeholder actions.
- Content consumption (YouTube, podcasts, articles, X, LinkedIn)
- Research / analysis (deep dives, sector analysis, thesis building)
- Information digestion (reading meeting notes, reviewing portfolio updates)

### 3.3 The Loop

```
Do actions → Generate new actions → Prioritize → Do highest-value actions → Repeat
```

The AI CoS sits in the middle of this loop. It continuously helps Aakash prioritize across the full action space — not just the meeting calendar, not just content, but everything.

### 3.4 The Four Priority Buckets

All actions, whether stakeholder or intelligence, ultimately serve four objectives:

| Priority | Objective | Weight | When |
|----------|-----------|--------|------|
| 1 | **New cap tables** — Expand network to be on more amazing companies' cap tables | Highest | Always |
| 2 | **Deepen existing cap tables** — Continuous IDS on portfolio for ownership increase decisions | High | Always |
| 3 | **New founders/companies** — Meet potential backable founders via DeVC Collective pipeline | High | Always |
| 4 | **Thesis evolution** — Meet interesting people who keep thesis lines evolving | Lower when conflicted with 1-3, but **highest when capacity exists** | Fill remaining capacity, never zero |

### 3.5 The End Goal

The system maximizes **investment returns**. Everything else — ecosystem building, personal brand, thesis influence, Collective growth — are inputs to that function.

---

## 4. The Intelligence Models

### 4.1 Action Scoring Model (Primary — "What's Next?")

Every potential action gets scored before being surfaced:

```
Action Score = f(
    bucket_impact,                — Which bucket(s) does this serve? How much?
    conviction_change_potential,  — Could this change investment conviction?
    key_question_relevance,      — Does this address an open Key Question?
    time_sensitivity,            — Is there a reason to act NOW?
    action_novelty,              — Is this a new insight or a rehash?
    stakeholder_priority,        — How important is this company/person?
    effort_vs_impact             — Quick win or heavy lift?
)
```

**Thresholds:**
- **Score ≥ 7:** Surface as action (high-confidence recommendation)
- **Score 4-6:** Tag as "Low Confidence" — available but not promoted
- **Score < 4:** Context enrichment only — updates the Knowledge Store, no discrete action

Implementation: `scripts/action_scorer.py` (172 lines, created Session 039). Not yet wired into Content Pipeline — next integration step.

### 4.2 People Scoring Model (Subset — for meeting-type actions)

When the action type is "meeting," the Action Scoring Model specializes into 9 factors:

```
Person Score = f(
    bucket_relevance,      — which of the 4 objectives does meeting this person serve?
    current_ids_state,     — where are they in the IDS journey? what's the open question?
    time_sensitivity,      — reason to meet NOW vs later?
    info_gain_potential,   — what will Aakash learn that he doesn't know?
    network_multiplier,    — who else does this person connect to?
    thesis_intersection,   — sits at a thesis convergence point?
    relationship_temp,     — warm/cold? last interaction? trend?
    geographic_overlap,    — will they be in the same city?
    opportunity_cost       — what does Aakash miss by NOT meeting them now?
)
```

**Composite Score** (from v2, still valid): `weighted_sum(bucket_scores) × urgency_multiplier × geographic_overlap × relationship_trajectory`

The People Scoring Model is NOT a separate brain. Meeting optimization is one output of the general action optimizer. The system doesn't need two scoring engines — it needs one engine with specialization per action type.

### 4.3 The Learning Loop (The Compounding Mechanism)

This is the most critical missing primitive. The Preference Store (see §6.3) enables the system to learn from Aakash's actual decisions:

**What it tracks:**
- Accept/dismiss ratios per company × action type → weight adjustment
- Meeting outcomes (when Granola post-meeting processing is live) → revealed preference learning
- Nightly consolidation → cluster similar actions, merge duplicates, promote recurring themes, archive stale
- Thesis thread tracking → which threads generate the most acted-on signals?

**How it works:** Not ML training. Not fine-tuning. The structured accept/reject history (with scoring factor snapshots) is injected into every reasoning session — Agent SDK runner or interactive — BEFORE the system reasons about new actions. The model calibrates to Aakash's actual behavior, not just stated priorities.

**The compounding insight:** After 6 months, the preference store makes the AI CoS measurably better at predicting Aakash's actions than after 6 days. This is how the system becomes a true extension of Aakash — not just following rules, but learning judgment.

**Current state:** Actions Queue already captures accept/reject via Status field (Proposed → Accepted/Dismissed). Content Digest DB captures action lifecycle (Pending → Reviewed → Actions Taken → Skipped). The Preference Store would formalize this into a structured Postgres table optimized for context injection.

### 4.4 IDS as the Operating Methodology

Everything the AI CoS does is grounded in Aakash's IDS methodology:

- **Notation:** +, ++, ?, ??, +?, - (conviction signals from interactions)
- **Conviction spectrum:** 100% Yes → Strong Yes → Strong Maybe → Maybe → Weak No → Pass Forever
- **Spiky Score:** 7 dimensions × 1.0 scale (evaluates founder quality)
- **Evaluation framework:** EO/FMF/Thesis/Price (4 dimensions × /10)
- **7 IDS context types:** First Meeting, Follow-up, BRC Prep, Portfolio Check-in, Thesis Research, Network Mapping, Content Analysis

The AI CoS doesn't replace IDS. It externalizes and scales it — making every signal compound into the IDS graph instead of leaking between surfaces.

---

## 5. The Architecture: Three Layers, One Brain

### 5.1 Layer 1 — Signal Processor (The Eyes and Ears)

The Signal Processor observes every surface Aakash touches and converts raw input into structured intelligence. Each signal source produces a normalized Signal:

```typescript
interface Signal {
  source: "youtube" | "granola" | "email" | "whatsapp" | "social" | "research";
  content: string;
  entities: {
    people: string[];
    companies: string[];
    topics: string[];
  };
  metadata: Record<string, any>;
  timestamp: string;
}
```

**Key principle: Same Brain, Different Eyes.** The Intelligence Engine doesn't care WHERE the signal came from. It runs the same flow for all sources: match → retrieve context → analyze → score impact → generate actions → present.

**Signal sources (in build order):**

| Source | Action Type | Status | Integration |
|--------|-------------|--------|-------------|
| YouTube / Podcasts | Intelligence | ✅ Live (Content Pipeline v4) | Mac extractor → JSON queue → Cowork subagent analysis |
| Granola Meeting Notes | Stakeholder output | 🔜 Next | Granola MCP connected (query, transcript, list, get) — processor not built |
| Email (M365) | Stakeholder | Future | M365 connector coming to Cowork |
| WhatsApp | Stakeholder | Future | Requires custom bridge (Business API + whatsapp-web.js hybrid) |
| LinkedIn / X | Intelligence | Future | No clean API — authenticated browser or screengrab → IngestAgent |
| Market Signals | Passive intelligence | Future | Explorium enrichment + web monitoring |

Each new signal source independently improves the loop. We don't need all sources to ship value.

### 5.2 Layer 2 — Intelligence Engine (The Brain)

The Intelligence Engine receives signals, retrieves relevant context, analyzes impact, and generates prioritized actions.

#### 5.2a The Knowledge Store

**Notion (Structured — operational state, today):**
- Companies DB (49 fields) — pipeline stage, conviction, deal status 3D matrix
- Network DB (40+ fields) — 13 archetypes, IDS state, relationship data
- Portfolio DB (94 fields) — investment, metrics, health, team, follow-on status
- Thesis Tracker — 6 active threads, evidence, conviction, key questions
- Actions Queue — single sink for ALL action types with relations to Portfolio, Thesis, Content Digest
- Content Digest DB — AI-analyzed content with thesis/portfolio connections
- Build Roadmap — 22 items, 7-state kanban, parallel safety classification
- Tasks Tracker, Finance DB

**Postgres (High-frequency tables, Phase 2):**
When Notion API latency (200-800ms) and rate limits become bottlenecks for autonomous processing, core operational tables migrate to Postgres (<5ms):
- `actions_queue` — high-write from multiple signal sources
- `content_digest` — Content Pipeline output
- `thesis_signals` — evidence accumulation
- `session_log` — cross-session continuity
- `action_outcomes` — the Preference Store (learning foundation)

Notion continues as the UI layer — Aakash views and edits there. A sync worker (dirty flag pattern, 60s batch cycle) keeps both in sync.

**Vector Store (Unstructured — semantic intelligence, Phase 3):**
pgvector on Postgres. Triggered when: second signal source (Granola) is processing, 500+ companies, or sub-second retrieval needed. None of these triggers have fired yet — correctly deferred.

**Build strategy:** LLM-as-matcher first (Notion + company index in prompt). Postgres when autonomous runners need speed. Vector DB when retrieval volume demands it.

#### 5.2b The Scoring Models

(See §4.1 and §4.2 — Action Scoring and People Scoring feed directly into the Intelligence Engine's reasoning.)

#### 5.2c The Learning Loop

(See §4.3 — the Preference Store is the learning foundation that makes the Intelligence Engine compound over time.)

#### 5.2d The Decision Layer

The scoring models feed concrete outputs:

**Action triage (daily):** "Here are your 12 highest-priority actions across content, meetings, follow-ups, and research. 4 are time-sensitive."

**Meeting optimization (weekly/trip):** "For your SF trip: 25 people scored and ranked. Your mix: 8 portfolio (bucket 1-2), 10 new founders (bucket 3), 4 thesis contacts (bucket 4), 3 reconnections."

**Slot filling (real-time):** "Meeting cancelled. [Person X] is the highest-scored replacement — pre-computed and ready."

**Signal integration (continuous):** "This YouTube video reveals competitive intel on 3 portfolio companies. Here are the 2 actions worth your time."

**Gap analysis (periodic):** "You're underweighting bucket 2 — 4 portfolio companies have stale IDS. Your cybersecurity thesis has the most unresolved questions."

### 5.3 Layer 3 — Operating Interface (The Voice)

The Operating Interface is how Aakash interacts with the "What's Next?" system. It evolves across phases — but the principle is constant: **Aakash and the AI CoS are a singular entity. The interface isn't a tool Aakash uses — it's the medium through which the combined entity operates.**

**Current interfaces (live):**
- Cowork (primary build surface — 39 sessions of iteration)
- Claude.ai web/mobile (MCP-connected, mobile-friendly for action review)
- digest.wiki (content digests, mobile-optimized, WhatsApp-shareable)
- Claude Code (daily coding, hooks, CLAUDE.md, subagents)

**Future interfaces:**
- Action Frontend on digest.wiki (accept/dismiss on digests → consolidated dashboard)
- WhatsApp (proactive recommendations, quick capture, meeting prep briefs)
- Agent SDK runners (autonomous execution, no human in loop)

---

## 6. The Infrastructure Decisions

These decisions emerged from the Architecture Brainstorm session, grounded against 39 sessions of implementation reality.

### 6.1 MCP Server as Cross-Surface Hook Layer

**Problem:** Claude Code hooks don't work in Cowork or Claude.ai. Cross-cutting logic (context injection, action scoring, preference loading) is scattered across skill prompts and CONTEXT.md.

**Solution:** A custom `ai-cos-mcp` FastMCP server (~200 lines Python) that consolidates:
- Context injection at session start (loads relevant state from Notion/Postgres)
- Action scoring (calls scoring model with full context)
- Preference injection (loads accept/reject history before reasoning)
- State sync (writes back to Notion/Postgres after mutations)

Deploy to URL. Connect from Claude Code, Claude.ai, Cowork, Claude desktop. One server, all surfaces.

**Why MCP, not just Agent SDK:** MCP is the tool layer. Agent SDK is the execution runtime. They compose — Agent SDK runners USE MCP tools. MCP without Agent SDK = no autonomous execution. Agent SDK without MCP = Claude has only built-in tools.

### 6.2 Agent SDK — Narrow Runners, Not General Agent

**The lesson from OpenClaw deployment:** General-purpose agents with computers produce slop on open-ended work. Claude Code with human in loop produces quality.

**The discipline:** Agent SDK only executes what has already been designed in Claude Code. It never designs.

**Five specialist runners** (pragmatic consolidation of v1's seven agents):

| Runner | Role | Reads | Writes | Trigger |
|--------|------|-------|--------|---------|
| **PostMeetingAgent** | Extracts signals from Granola transcripts, drafts IDS updates, generates follow-up actions | Granola MCP, Network DB, Companies DB, Portfolio DB, Thesis Tracker | Actions Queue (with Source Meeting relation), Notion entity updates (draft for approval) | New Granola transcript appears |
| **ContentAgent** | Analyzes content queue, cross-references thesis/portfolio, generates actions | Content queue JSON, Content Digest DB, Companies DB, Portfolio DB, Thesis Tracker | Content Digest DB, Actions Queue (with Source Digest relation), digest.wiki publish | New items in content queue |
| **OptimiserAgent** | Runs scoring models, produces ranked meeting/action lists, detects gaps and underweighting | All Notion DBs, Calendar, Preference Store | Actions Queue (meeting-type actions), gap analysis reports | Nightly + on-demand |
| **IngestAgent** | Processes manual captures (screengrabs, URLs, bookmarks), enriches, classifies | Raw capture input, Network DB, Companies DB, Explorium | Network DB entries, Companies DB entries, Actions Queue | Aakash drops capture |
| **SyncAgent** | Maintains Notion ↔ Postgres consistency, runs nightly consolidation | Both data stores | Both data stores, consolidation logs | 60s sync cycle + nightly consolidation |

**Mapping to v1's seven agents:** PostMeetingAgent ≈ Meeting Intelligence. ContentAgent ≈ Pipeline Manager + Signal Catcher (content). OptimiserAgent ≈ Network Weaver + Calendar Intelligence. IngestAgent ≈ Signal Catcher (manual). SyncAgent = new infrastructure agent.

**The pattern is proven:** Content Pipeline already uses orchestrator + parallel Task subagents (one per video). Session close uses Bash subagents with prompt templates from `scripts/subagent-prompts/`. The Agent SDK version is this same pattern running autonomously on a droplet.

### 6.3 The Preference Store

The most critical missing primitive. Must exist before the first Agent SDK runner writes its first action.

```sql
CREATE TABLE action_outcomes (
    id            SERIAL PRIMARY KEY,
    action_id     TEXT NOT NULL,        -- Notion Actions Queue page ID
    action_type   TEXT NOT NULL,        -- 'content_signal', 'meeting_follow_up', 'thesis_update', ...
    company_id    TEXT,                 -- Notion Companies/Portfolio page ID (nullable)
    person_id     TEXT,                 -- Notion Network page ID (nullable)
    proposed_at   TIMESTAMPTZ NOT NULL,
    decided_at    TIMESTAMPTZ,
    decision      TEXT CHECK (decision IN ('accepted','dismissed','deferred','expired')),
    proposed_score    REAL,
    scoring_factors   JSONB,            -- snapshot of all 7 factor values at proposal time
    context_snapshot  JSONB,            -- what context was loaded when score was computed
    feedback_note TEXT,                 -- optional free-text from Aakash
    source_signal TEXT                  -- which Signal produced this action
);

CREATE INDEX idx_ao_type_decision ON action_outcomes(action_type, decision);
CREATE INDEX idx_ao_company ON action_outcomes(company_id) WHERE company_id IS NOT NULL;
CREATE INDEX idx_ao_person ON action_outcomes(person_id) WHERE person_id IS NOT NULL;
CREATE INDEX idx_ao_proposed ON action_outcomes(proposed_at);
```

**Why scoring_factors JSONB:** When the system asks "why did Aakash dismiss this?" it needs to see what the model thought at proposal time. Without factor snapshots, you can only learn that something was dismissed — not which factor was miscalibrated.

**How it's used:** Before every Agent SDK reasoning session:
1. Load last 200 action outcomes for this action type
2. Compute accept/dismiss ratios by company, person, thesis, and factor
3. Inject as structured context: "For content_signal actions, Aakash accepts 73% of thesis-related signals but only 31% of general market signals. For company X, he accepts follow-ups 90% of the time."
4. The LLM adjusts its scoring and presentation accordingly — not through weight tuning, but through richer context

### 6.4 Cloud Infrastructure

$12/month Digital Ocean droplet (1 vCPU, 2GB RAM). Tailscale for secure networking.

**Phase 1 (current):** MCP server + Notion as backend. All existing integration patterns continue.

**Phase 2:** Add Postgres for high-frequency tables. Sync worker with dirty flag pattern, 60s batch cycle, respects Notion rate limits. Notion continues as UI.

**Phase 3:** Web UI for on-demand triggers. Agent SDK runner layer. Notion for human-readable views only.

---

## 7. The DeVC Collective as a Subsystem

The DeVC Collective is not separate from the AI CoS — it's one of the highest-throughput signal sources and action generators in the system.

### 7.1 The Deal Flow Funnel

**TOFU (Top of Funnel):** Lead Generation + Initial Screening
- 7 sourcing channels: Collective Member Referrals, Direct Inbound, Co-investor Introductions, Conference/Event Pipeline, Content-Led Discovery, Thesis-Driven Outbound, Platform Signals (Explorium, web monitoring)
- Each channel feeds both Companies DB and Network DB
- AI CoS scores inbound signals against thesis threads and bucket priorities

**MOFU (Middle of Funnel):** IDS + Evaluation
- IDS deep dives: notation (+, ++, ?, ??), conviction tracking, Key Questions
- Collective members activated as evaluators based on domain expertise match
- AI CoS tracks IDS progression, flags stalls, ensures BRC scheduling

**BOFU (Bottom of Funnel):** IC Process + Close
- IC process v1.1: IDS deck 48-72hrs prior, formal evaluation framework
- Follow-on evaluation: Founder MPI gate → Traction → TAM
- AI CoS ensures nothing falls through — every commitment tracked

### 7.2 Collective Member Lifecycle

The Collective is a network of external evaluators that extends Aakash's reach:

```
Prospect → Engaged → Signed → Active → Dormant
```

- **Prospect:** Identified via screengrab, LinkedIn, event, referral. Enriched via Explorium. Scored for domain expertise, network reach, evaluation quality potential.
- **Engaged:** Outreach initiated. Tracking response, interest level, scheduling.
- **Signed:** Formal agreement in place. Onboarded with playbook.
- **Active:** Producing evaluations, attending events, sourcing deals. Tracked: evaluation quality, response time, deal flow contribution.
- **Dormant:** No activity in 90+ days. Reactivation or archive decision.

The AI CoS manages this funnel as a subset of the Network DB, with Collective-specific actions flowing into the Actions Queue.

---

## 8. The Interaction Model

### 8.1 How Aakash Interacts Today

**Cowork (primary build surface):** Deep work sessions — "optimize my trip," "process my content queue," "research this company," "run full cycle." Interactive, high-bandwidth, requires sitting at desktop.

**Claude.ai mobile:** Quick queries — "review my content actions," "what's the status of [company]," "who should I meet in SF?" Enabled by Claude.ai Memories (#11, #12) that point to Notion.

**digest.wiki:** Consuming content digests on mobile. WhatsApp-shareable. Currently read-only — action triage (accept/dismiss) planned for Phase 2.

### 8.2 How Aakash Will Interact (With Agent SDK)

**WhatsApp (the primary surface):**

Proactive messages from AI CoS:
```
🔵 Pre-Meeting Brief
Meeting with [Name] in 30min
Last met: [date] — discussed [topic]
IDS: [current conviction notation]
Key context: [2-3 bullets]
Suggested asks: [2-3 items]
```

```
🟢 Signal Captured
[Person/Company] — [signal type]
[1-line summary]
Connected to: [thesis/pipeline item]
Action needed? [suggestion]
```

```
🟡 Follow-Up Due
[Task] for [Person/Company]
Originally committed: [date]
Context: [1-line]
[Reply "done", "defer", or "drop"]
```

```
🔴 Alert
[Urgent signal about portfolio company or high-priority item]
[Context]
[Suggested action]
```

Aakash's inputs:
- Voice note after a meeting → transcribed → PostMeetingAgent processes
- Screenshot of a profile → IngestAgent enriches and classifies
- Forward a link → ContentAgent or IngestAgent processes
- "prep me for [meeting]" → full brief generated
- "who in my network knows [topic]?" → OptimiserAgent responds
- "yes" / "approved" → executes proposed action

**The key principle:** The conversation should feel like texting an exceptionally well-prepared, always-available chief of staff. Not a chatbot that waits for commands — a proactive strategic advisor.

### 8.3 The Authorization Model

Trust builds over time:
1. **Read** (default) — surface intelligence, prepare briefs
2. **Suggest** (earned) — propose actions for approval
3. **Act** (earned) — execute with approval per-action
4. **Auto-act** (earned per category) — execute without approval for trusted action types

"Auto-approve follow-up reminders" is different from "auto-approve investment decisions." The system earns trust at the category level.

---

## 9. What's Already Built (Ground Truth — Session 039)

### 9.1 Live and Working

- **Content Pipeline v4:** YouTube → Mac extractor (launchd 8:30 PM) → JSON queue → Cowork parallel subagent analysis → PDF/HTML digests → Content Digest DB → Actions Queue. Daily scheduled task at 9 PM.
- **digest.wiki:** Next.js 16 + TypeScript + Tailwind v4. Live at https://digest.wiki. SSG renders mobile-friendly, WhatsApp-shareable digests. Single deploy path: commit → osascript git push → GitHub Action → Vercel production (~90s).
- **Notion as full data layer:** 8 databases with cross-references, all actively used. Actions Queue as single action sink with relations to Portfolio, Thesis, Content Digest.
- **Layered persistence:** 6 layers (Global Instructions, User Preferences, Claude.ai Memories ×16, AI CoS Skill v6.2.0, CLAUDE.md, CONTEXT.md). Cross-surface coverage tracked.
- **IDS methodology fully encoded:** Notation, conviction spectrum, Spiky Score, evaluation framework, 7 IDS context types — all in skill prompts.
- **Scoring models defined:** Action Scoring (7 factors), People Scoring (9 factors), thresholds set. `action_scorer.py` exists (172 lines).
- **Parallel development system:** Local git repo, branch lifecycle CLI (`scripts/branch_lifecycle.sh`), worktree-based isolation, file safety classification (🟢/🟡/🔴), 2-step roadmap gate.
- **Subagent patterns proven:** 4 prompt templates in `scripts/subagent-prompts/`, behavioral audit template, session close delegated to subagents to avoid context compaction.
- **Deep research enrichment:** All 20 Fund Priority companies researched, 76 actions generated.
- **6 active thesis threads:** Agentic AI Infrastructure, Cybersecurity/Pen Testing, USTOL/Aviation, SaaS Death/Agentic Replacement (High conviction), CLAW Stack, Healthcare AI Agents.

### 9.2 Designed but Not Yet Built

- Preference Store (action_outcomes table)
- Custom ai-cos-mcp server
- Postgres migration (Phase 2 infrastructure)
- Agent SDK runners (5 specialists)
- action_scorer.py wired into Content Pipeline
- Content Pipeline v5 (full portfolio coverage, semantic matching)
- Action Frontend on digest.wiki (accept/dismiss UX)
- Granola post-meeting processing pipeline
- WhatsApp integration

### 9.3 Known Gaps

- No retrieval layer beyond Granola MCP full-text search
- No cross-session memory beyond CONTEXT.md + Notion + 16 Claude.ai Memory entries
- All automation triggered by Aakash or simple cron — nothing autonomous with reasoning
- No feedback loop structured for preference learning injection
- Scoring models defined but not production-wired
- Relationship temperature not formally modeled (one of 9 People Scoring factors, needs design)

---

## 10. The Build Path

### Phase 1: Wire the Intelligence (Current → Month 1)
*Make the existing system smarter.*

1. Wire `action_scorer.py` into Content Pipeline — every proposed action gets scored
2. Build Preference Store in Notion (before Postgres) — capture accept/reject with factor snapshots
3. Build `ai-cos-mcp` server — consolidate context injection + scoring + preference loading
4. Content Pipeline v5 — full portfolio coverage (200+ companies), semantic matching

**Value delivered:** Content actions are scored and prioritized instead of flat lists. The system starts learning from Aakash's decisions.

### Phase 2: Build the Action Frontend (Month 1-2)
*Give Aakash a proper triage surface.*

1. Accept/dismiss on digest pages (digest.wiki `/d/{slug}` → add action buttons)
2. Consolidated `/actions` route on digest.wiki — all pending actions, filterable
3. Portfolio dashboard view
4. Thesis tracker view with evidence feed

**Value delivered:** Without a triage surface, increased action volume from Phase 1 overwhelms the chat-based review workflow. This is the first real Operating Interface.

### Phase 3: Cloud Infrastructure (Month 2-3)
*Move to persistent, fast, autonomous-ready infrastructure.*

1. DO droplet + Postgres + Tailscale
2. Migrate high-frequency tables (actions_queue, content_digest, thesis_signals, session_log, action_outcomes)
3. Sync worker: dirty flag pattern, 60s batch cycle, Notion as UI layer
4. Vector DB (pgvector) — triggered by Granola processing or 500+ companies

**Value delivered:** Sub-5ms data access for autonomous processing. Notion rate limit bottleneck eliminated. Foundation for Agent SDK runners.

### Phase 4: Agent SDK Runners (Month 3-5)
*The system starts operating autonomously.*

Build order follows dependency chain:
1. **SyncAgent** first — infrastructure, ensures Notion ↔ Postgres consistency
2. **ContentAgent** — automates Content Pipeline (currently cron + manual Cowork session)
3. **PostMeetingAgent** — the highest value-add: direct IDS signal from every meeting
4. **IngestAgent** — processes manual captures (screengrabs, URLs, bookmarks)
5. **OptimiserAgent** — runs scoring models, produces ranked lists, detects gaps

**Value delivered:** The system processes signals 24/7 without Aakash opening anything. Every meeting, every content signal, every capture gets analyzed, scored, and either surfaced or stored.

### Phase 5: Multi-Surface + WhatsApp (Month 5-8)
*The system meets Aakash where he lives.*

1. WhatsApp integration (Business API for outbound + bridge for monitoring)
2. Pre-meeting briefs via WhatsApp (PostMeetingAgent → WhatsApp)
3. Signal capture via WhatsApp (screenshots, links, voice notes → IngestAgent)
4. Proactive recommendations via WhatsApp (OptimiserAgent → WhatsApp)
5. Email signal processing (M365 when available)

**Value delivered:** The AI CoS is no longer something Aakash goes to — it comes to him. Zero-friction capture and proactive intelligence on the surface where he already lives.

### Phase 6: Always-On Intelligence (Month 8+)
*The full singular entity.*

- Continuous signal ingestion across all surfaces
- Real-time optimization as signals arrive
- Meeting slot filling (cancellation → instant scored replacement)
- Network Pulse (weekly WhatsApp: relationships to tend, connections to make)
- Thesis convergence detection (multiple signals from different sources pointing to same insight)
- 24/7 compound intelligence — the system gets measurably better every month

---

## 11. What 100x Looks Like

### A Day in Aakash's Life (Phase 5+)

**7:30 AM:** WhatsApp from AI CoS: Morning brief with all 8 meetings contextualized, top 3 follow-ups due, one thesis connection surfaced overnight ("The pen testing company from your pipeline had a competitor raise $30M yesterday — three portfolio companies have exposure").

**8:45 AM:** Pre-meeting brief lands on WhatsApp: full IDS context on the founder he's about to meet, Explorium enrichment, mutual connections, note: "This founder's approach to vertical AI connects to your CLAW stack thesis."

**9:30 AM:** Meeting ends. Voice note to AI CoS: "Good meeting, sharp founder. Strong on product, questions on GTM. Follow up on customer references. ++product, ?gtm." AI CoS responds: "Captured. Drafted Notion update and follow-up task for customer references. The Confido Health channel partner approach might be relevant — want me to pull that playbook? Approve update?"

**11:00 AM:** Screenshot of a LinkedIn post dropped to AI CoS on WhatsApp. Response: "This is [Name], [Title] at [Company]. Enriched: [key details]. Matches Collective criteria — strong cybersecurity evaluator. Added to Network DB as EXT Target, flagged for outreach. They follow [mutual connection]. Draft approach message?"

**2:00 PM:** Proactive: "BRC for [Company] scheduled next week. IDS deck needed 48-72hrs prior. Draft compiled from all IDS history. [Link]. Review when you get a chance."

**5:30 PM:** End of day: "Today: 4 meetings processed, 2 signals enriched, 1 pipeline company moved from Maybe to Maybe+, 3 follow-ups completed, 2 new. Your USTOL thesis has 3 new data points. Tomorrow: 6 meetings, starting with [X] who's critical for [Y]."

**Sunday evening:** Weekly synthesis: network heat map, pipeline movement, thesis threads, follow-up accountability, next week optimization. Aakash reviews in 10 minutes instead of 2 hours of mental backlog clearing.

### The Compound Effect

**Without AI CoS:** Actions driven by who reaches out, what Sneha schedules, what Aakash remembers, what his fuzzy mental map surfaces. Maybe 30-40% of his action space is optimally allocated.

**With AI CoS:** Every action slot — meetings, follow-ups, research, content consumption — is informed by a scored, contextual analysis of his entire stakeholder space. The system catches what he'd miss: the second-degree connection, the content signal that changes conviction on a portfolio company, the thesis thread that reveals a new investment opportunity. Maybe 70-80% optimal allocation.

Across 7-8 meetings/day, hundreds of content signals per week, and 200+ companies — going from 40% to 80% optimal allocation is a massive compounding effect on investment quality and returns.

The 100x comes from the flywheel: **better actions → better IDS → better decisions → better outcomes → better network → even better actions.** The flywheel accelerates because the AI CoS keeps the full picture updated and the optimization running continuously — and because the Preference Store makes the system smarter with every decision Aakash makes.

---

## 12. Design Principles (Accumulated from 39 Sessions)

1. **WhatsApp-first, mobile-native.** Any system that requires desktop as primary interaction will fail. The AI CoS meets Aakash where he already is.

2. **Capture must be zero-friction.** Screengrab-as-memory and WhatsApp-self-as-bookmark exist because they're lowest-friction. The AI CoS must be even lower friction — or it won't get used.

3. **IDS is the core operating methodology.** Everything compounds. A meeting note from November becomes critical context for a BRC in March. Every signal is a node in an ever-growing intelligence graph, not a transient event.

4. **Judgment stays with Aakash. Everything else is leverage.** The AI CoS never makes investment decisions. It makes Aakash's judgment more effective by ensuring right context, right time, right connections.

5. **Plumbing serves the optimizer, not the other way around.** Never build infrastructure for its own sake. Every piece of plumbing must make "What's Next?" answerable with higher accuracy.

6. **Agent SDK executes what Claude Code designs.** Narrow runners, not general agents. The discipline from 39 sessions: human-in-loop for design, autonomous for execution of known patterns.

7. **The preference store is the compounding mechanism.** Without learning from accept/reject history, you have smart one-shot reasoning but no improvement over time. The learning loop is what separates a tool from a true extension of Aakash.

8. **Each signal source independently improves the loop.** We don't need all sources to ship value. YouTube alone (live today) already generates 76+ actions from 20 companies. Each new source compounds.

9. **Gradual trust building.** Start with read-only intelligence. Earn the right to act through demonstrated accuracy. Category-level trust, not blanket permission.

10. **The system enforces its own maintenance.** Session close checklists, persistence audits every 5 sessions, behavioral audits, CONTEXT.md as living brain — the AI CoS is self-documenting and self-correcting.

---

## Changelog

| Version | Date | Key Changes |
|---------|------|-------------|
| v1 | Dec 2024 | Task automation: morning briefs, post-meeting capture, weekly reviews. 7 specialist agents + Orchestrator. Tier 1 (Cowork 5-10x) + Tier 2 (Agent SDK 100x). |
| v2 | Jan 2025 | Network optimization: "Who should I meet next?" Four buckets, People Scoring Model, Composite Score. Three agents (Intelligence Engine, Signal Processor, Operating Interface). |
| v3 | Mar 2026 | Full action space: "What's next?" Stakeholder + intelligence actions. Action Scoring subsumes People Scoring. Three layers sharing infrastructure. Learning Loop. Normalized Signal schema. 6-phase build order. |
| v4 | Mar 2026 | **Definitive synthesis.** Architecture brainstorm decisions (MCP hook layer, Agent SDK narrow runners, Preference Store, Postgres migration). All corrections from 39 sessions of ground truth (no Attio, Notion constraints, sandbox rules, subagent patterns). v1's Agent SDK detail (5 runner consolidation of 7 agents). v2's scoring models (composite score formula). Build path grounded in what's actually live vs. planned. DeVC Collective as subsystem. Authorization model. |
