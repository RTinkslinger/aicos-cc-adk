# AI Chief of Staff — Vision Document v5
## "What's Next?" — The Definitive System Vision
**March 2026 · Updated from v4 to reflect Claude Code era build-out**

> This document is the canonical vision reference for the AI CoS system. It supersedes all prior versions by incorporating implementation reality from the Claude Code era: autonomous Content Pipeline, AI-managed Thesis Tracker conviction engine, live MCP server, droplet infrastructure, and the full Cowork→Claude Code transition. Original v4 preserved in `From Clowork handover (sessino 40 in cowork)/`.

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
| v4 | Mar 2026 | "What's next?" — with architecture decisions from brainstorm | Added MCP hook layer, Agent SDK narrow runners, Preference Store, Postgres migration path. Corrections from implementation reality. |
| v5 | Mar 2026 | **"What's next?" — with autonomous infrastructure live** | Content Pipeline autonomous on droplet. Thesis Tracker = AI-managed conviction engine. MCP server + Postgres live. Cowork fully deprecated → Claude Code primary. First real compounding in production. |

The question hasn't changed from v3. What v5 adds: the reality of an autonomous system processing signals 24/7 without human intervention, an AI-managed conviction engine that evolves thesis threads continuously, and the full transition from Cowork sessions to Claude Code as the build surface.

---

## 3. The Optimization Problem

### 3.1 The Stakeholder Space

Two data models, both in Notion today:

**Companies** (~200 today, growing 50-60/year):
- Pipeline companies at various conviction levels
- Portfolio companies under continuous IDS
- Thesis-relevant companies being tracked
- Stored in Companies DB (49 fields, Deal Status 3D matrix: pipeline stage × conviction × active/inactive) and Portfolio DB (94 fields, hidden `Company Name` relation linking to Companies DB)

**Network** (400+ contacts and growing):
- Founders, investors, operators, thesis contacts, Collective members
- Connected to companies, thesis threads, and each other
- Stored in Network DB (40+ fields, 13 archetypes)

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

**Thesis-weighted scoring:** Actions connected to thesis threads that Aakash has marked as "Active" (Status field) receive a multiplier on `key_question_relevance` and `conviction_change_potential`. This is the mechanism by which Aakash's human attention signals influence AI prioritization.

Implementation: `scripts/action_scorer.py` (172 lines). Not yet wired into Content Pipeline — next integration step.

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

**Composite Score:** `weighted_sum(bucket_scores) × urgency_multiplier × geographic_overlap × relationship_trajectory`

The People Scoring Model is NOT a separate brain. Meeting optimization is one output of the general action optimizer.

### 4.3 The Learning Loop (The Compounding Mechanism)

The Preference Store enables the system to learn from Aakash's actual decisions:

**What it tracks:**
- Accept/dismiss ratios per company × action type → weight adjustment
- Meeting outcomes (when Granola post-meeting processing is live) → revealed preference learning
- Nightly consolidation → cluster similar actions, merge duplicates, promote recurring themes, archive stale
- Thesis thread tracking → which threads generate the most acted-on signals?

**How it works:** Not ML training. Not fine-tuning. The structured accept/reject history (with scoring factor snapshots) is injected into every reasoning session — Agent SDK runner or interactive — BEFORE the system reasons about new actions. The model calibrates to Aakash's actual behavior, not just stated priorities.

**The compounding insight:** After 6 months, the preference store makes the AI CoS measurably better at predicting Aakash's actions than after 6 days. This is how the system becomes a true extension of Aakash — not just following rules, but learning judgment.

**Current state:** The `action_outcomes` table exists in Postgres on the droplet. Actions Queue captures accept/reject via Status field. Content Digest DB captures action lifecycle. The plumbing is in place — preference injection into all reasoning sessions is the next step.

### 4.4 IDS as the Operating Methodology

Everything the AI CoS does is grounded in Aakash's IDS methodology:

- **Notation:** +, ++, ?, ??, +?, - (conviction signals from interactions)
- **Conviction spectrum:** 100% Yes → Strong Yes → Strong Maybe → Maybe → Weak No → Pass Forever
- **Spiky Score:** 7 dimensions × 1.0 scale (evaluates founder quality)
- **Evaluation framework:** EO/FMF/Thesis/Price (4 dimensions × /10)
- **7 IDS context types:** First Meeting, Follow-up, BRC Prep, Portfolio Check-in, Thesis Research, Network Mapping, Content Analysis

The AI CoS doesn't replace IDS. It externalizes and scales it — making every signal compound into the IDS graph instead of leaking between surfaces.

### 4.5 The AI-Managed Conviction Engine (Thesis Tracker)

The Thesis Tracker has evolved from a passive database to an AI-managed conviction engine. This is the first subsystem where the AI CoS truly operates autonomously — writing all fields except Status (human-only).

**Conviction Spectrum (two axes compressed into one dimension):**
- Maturity axis: **New** → **Evolving** → **Evolving Fast** (thesis still forming, evidence accumulating at varying velocity)
- Strength axis: **Low** → **Medium** → **High** (well-formed thesis with clear evidence base, assessed on weight of evidence)

**Key Questions as structured tracking:** Critical questions that would move conviction up or down are stored as page content blocks with `[OPEN]` prefix. When evidence answers a question, it's marked `[ANSWERED]` with evidence citation. This lifecycle is automated by ContentAgent — every content analysis checks existing open questions against new evidence.

**Autonomous thread creation:** When content analysis reveals a genuinely new investment thesis not covered by existing threads, ContentAgent creates a new thread at Conviction="New" with Discovery Source="Content Pipeline". New threads include initial evidence and 2-3 key questions.

**Evidence accumulation:** Evidence For and Evidence Against are appended to thesis properties using IDS notation (+ for, ? against). Page body accumulates structured evidence blocks: `[date] [source] (direction) evidence text`.

**Active thesis threads (6+):** Agentic AI Infrastructure, Cybersecurity/Pen Testing, USTOL/Aviation, SaaS Death/Agentic Replacement (High conviction), CLAW Stack, Healthcare AI Agents. New threads are created autonomously when evidence warrants.

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

**Signal sources (by status):**

| Source | Action Type | Status | Integration |
|--------|-------------|--------|-------------|
| YouTube / Podcasts | Intelligence | ✅ Live (autonomous) | Droplet: yt-dlp extraction → ContentAgent (Claude API) → publish to Notion + digest.wiki. Cron every 5 min. |
| Granola Meeting Notes | Stakeholder output | ✅ MCP connected | Granola MCP (query, transcript, list, get) — automated processing pipeline not yet built |
| Calendar | Location + schedule | ✅ MCP connected | Google Calendar MCP — powers geographic overlap factor |
| Email (Gmail) | Stakeholder | ✅ MCP connected | Gmail MCP — raw access, not yet processed by agents |
| WhatsApp | Stakeholder | 🔜 Future | Requires custom bridge (Business API + whatsapp-web.js hybrid) |
| LinkedIn / X | Intelligence | 🔜 Manual only | No clean API — screengrab → IngestAgent |
| Market Signals | Passive intelligence | 🔜 Future | Web monitoring |

Each new signal source independently improves the loop. YouTube alone (live today) already generates actions across 20+ portfolio companies. Each new source compounds.

### 5.2 Layer 2 — Intelligence Engine (The Brain)

The Intelligence Engine receives signals, retrieves relevant context, analyzes impact, and generates prioritized actions.

#### 5.2a The Knowledge Store

**Notion (Structured — operational state):**
- Companies DB (49 fields), Network DB (40+ fields, 13 archetypes), Portfolio DB (94 fields)
- Thesis Tracker — AI-managed conviction engine (6+ active threads)
- Actions Queue — single sink for ALL action types
- Content Digest DB — AI-analyzed content with thesis/portfolio connections
- Build Roadmap, Tasks Tracker, Finance DB

**Postgres on Droplet (Machine-speed operations, ✅ live):**
- `action_outcomes` — the Preference Store (learning foundation)
- Content pipeline data — processing state, queue management
- Future: `actions_queue` mirror, `network_graph`, `ids_trail`, `thesis_signals`

**Data Sovereignty:** `DATA-SOVEREIGNTY.md` defines field-level ownership between Notion and droplet. Notion owns human-managed fields. Droplet owns enriched fields. Change detection generates events ("Deal Status changed" → actionable signal).

**Vector Store (Unstructured — semantic intelligence, deferred):**
pgvector on Postgres. Triggered when: second signal source processing, 500+ companies, or sub-second retrieval needed. None fired yet — correctly deferred.

#### 5.2b The Scoring Models

(See §4.1 and §4.2 — Action Scoring and People Scoring feed directly into the Intelligence Engine's reasoning.)

#### 5.2c The Learning Loop

(See §4.3 — the Preference Store is the learning foundation that makes the Intelligence Engine compound over time.)

#### 5.2d The Decision Layer

The scoring models feed concrete outputs:

**Action triage (daily):** "Here are your 12 highest-priority actions across content, meetings, follow-ups, and research. 4 are time-sensitive."

**Meeting optimization (weekly/trip):** "For your SF trip: 25 people scored and ranked. Your mix: 8 portfolio (bucket 1-2), 10 new founders (bucket 3), 4 thesis contacts (bucket 4), 3 reconnections."

**Slot filling (real-time):** "Meeting cancelled. [Person X] is the highest-scored replacement — pre-computed and ready."

**Signal integration (continuous, ✅ live for content):** "This YouTube video reveals competitive intel on 3 portfolio companies. Here are the 2 actions worth your time."

**Gap analysis (periodic):** "You're underweighting bucket 2 — 4 portfolio companies have stale IDS. Your cybersecurity thesis has the most unresolved questions."

**Thesis evolution (✅ live):** "New evidence strengthens the Agentic AI Infrastructure thesis — conviction moved from Evolving to Evolving Fast. 2 key questions answered, 1 new question raised."

### 5.3 Layer 3 — Operating Interface (The Voice)

The Operating Interface is how Aakash interacts with the "What's Next?" system. **Aakash and the AI CoS are a singular entity. The interface isn't a tool Aakash uses — it's the medium through which the combined entity operates.**

**Current interfaces (live):**
- Claude.ai web/mobile (MCP-connected, mobile-friendly for action review, thesis discussion)
- digest.wiki (content digests, mobile-optimized, WhatsApp-shareable, auto-deploys on git push ~15s)
- Claude Code (primary build surface, hooks, CLAUDE.md, Build Traces)
- Notion (structured data UI, human status updates, action triage)

**Future interfaces:**
- Action Frontend on digest.wiki (accept/dismiss on digests → consolidated dashboard)
- WhatsApp (proactive recommendations, quick capture, meeting prep briefs)

---

## 6. The Infrastructure Decisions

### 6.1 MCP Server as Cross-Surface Tool Layer ✅ LIVE

**Problem:** Cross-cutting logic (context injection, action scoring, preference loading) needs to be available from all Claude surfaces.

**Solution:** Custom `ai-cos-mcp` FastMCP server on the DO droplet as a systemd service. Connected via Tailscale from Claude Code, Claude.ai, Claude desktop.

**Live tools:** `health_check`, `cos_load_context`, `cos_score_action`, `cos_get_preferences`.

**Planned tools:** Full tool inventory covering context, learning, network, actions, retrieval, ingest, and sync operations. See `architecture-v0.3.md` for complete tool table.

**Why MCP, not just Agent SDK:** MCP is the tool layer. Agent SDK is the execution runtime. They compose — Agent SDK runners USE MCP tools. MCP without Agent SDK = no autonomous execution. Agent SDK without MCP = Claude has only built-in tools.

### 6.2 Runners — Narrow Specialists, Not General Agent

**The lesson from OpenClaw deployment:** General-purpose agents with computers produce slop on open-ended work. Claude Code with human in loop produces quality.

**The discipline:** Runners only execute what has already been designed in Claude Code. They never design.

**Five specialist runners** (pragmatic consolidation of v1's seven agents):

| Runner | Status | Role |
|--------|--------|------|
| **ContentAgent** | ✅ Live | Content queue → thesis/portfolio matching → analysis → digests → Notion → Actions Queue → thesis updates |
| **PostMeetingAgent** | 🔜 Planned | Granola transcript → IDS extraction → conviction updates → follow-up actions |
| **OptimiserAgent** | 🔜 Planned | Scoring models → ranked action/meeting lists → gap analysis |
| **IngestAgent** | 🔜 Planned | Screenshots, URLs → Network/Companies DB enrichment |
| **SyncAgent** | 🔜 Planned | Notion ↔ Postgres consistency per DATA-SOVEREIGNTY.md |

**The pattern is proven:** ContentAgent runs autonomously on the droplet — extraction → Claude API analysis → Notion writes → digest.wiki publish → git push → Vercel deploy. Every 5 minutes. No human in the loop. This validates the narrow-runner pattern for the remaining four.

### 6.3 The Preference Store ✅ EXISTS

The `action_outcomes` table is live in Postgres on the droplet. Schema captures action_id, action_type, company/person IDs, proposal/decision timestamps, decision outcome, proposed score, scoring factor snapshots (JSONB), context snapshot, and feedback notes.

**How it's used:** `cos_get_preferences()` MCP tool loads structured preference history before reasoning sessions. Full injection into all reasoning — runners and interactive — is the next step for the compounding mechanism to activate.

### 6.4 Cloud Infrastructure ✅ LIVE

$12/month Digital Ocean droplet (1 vCPU, 2GB RAM). Tailscale for secure networking. Postgres database.

**What's running:**
- `ai-cos-mcp` server (systemd, always-on)
- Content Pipeline (cron every 5 min: extraction → ContentAgent → publish)
- Postgres (action_outcomes, content pipeline data)
- yt-dlp + deno for YouTube extraction
- Back-propagation sweep (Actions Queue Done → Content Digest "Actions Taken")

**What's next:**
- Expand Postgres tables for full Notion mirroring (per DATA-SOVEREIGNTY.md build phases)
- SyncAgent for bidirectional Notion ↔ Postgres sync
- PostMeetingAgent for Granola processing

---

## 7. The DeVC Collective as a Subsystem

The DeVC Collective is not separate from the AI CoS — it's one of the highest-throughput signal sources and action generators in the system.

### 7.1 The Deal Flow Funnel

**TOFU (Top of Funnel):** Lead Generation + Initial Screening
- 7 sourcing channels: Collective Member Referrals, Direct Inbound, Co-investor Introductions, Conference/Event Pipeline, Content-Led Discovery, Thesis-Driven Outbound, Platform Signals
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

```
Prospect → Engaged → Signed → Active → Dormant
```

- **Prospect:** Identified via screengrab, LinkedIn, event, referral. Scored for domain expertise, network reach.
- **Engaged:** Outreach initiated. Tracking response, interest level, scheduling.
- **Signed:** Formal agreement in place. Onboarded with playbook.
- **Active:** Producing evaluations, attending events, sourcing deals.
- **Dormant:** No activity in 90+ days. Reactivation or archive decision.

The AI CoS manages this funnel as a subset of the Network DB, with Collective-specific actions flowing into the Actions Queue.

---

## 8. The Interaction Model

### 8.1 How Aakash Interacts Today

**Claude.ai mobile:** Quick queries — "review my content actions," "what's the status of [company]," "who should I meet in SF?" MCP-connected for live Notion access.

**digest.wiki:** Consuming content digests on mobile. WhatsApp-shareable. Currently read-only — action triage (accept/dismiss) is the next frontend milestone.

**Claude Code:** Primary build surface. All system development, infrastructure, deployment, architecture happens here. Build Traces track implementation decisions with O(1) context cost.

**Notion:** Structured data triage — Action Queue status changes, thesis status updates, pipeline management.

### 8.2 How Aakash Will Interact (With Full Runner Stack)

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

## 9. What's Built vs. What's Next (Ground Truth — March 2026)

### 9.1 Live and Autonomous

- **Content Pipeline on Droplet:** Fully autonomous. Extraction (yt-dlp) → ContentAgent (Claude API analysis with structured prompt) → Notion writes (Content Digest DB 20+ fields, Actions Queue with company lookup/scoring/thesis connections, Thesis Tracker conviction updates) → digest.wiki publish (JSON → git push → Vercel auto-deploy ~15s). Cron every 5 min.
- **AI-Managed Thesis Tracker:** Conviction engine with 6-level spectrum (New/Evolving/Evolving Fast/Low/Medium/High). Key questions as `[OPEN]`/`[ANSWERED]` page content blocks. Autonomous thread creation from content signals. Evidence For/Against accumulation with IDS notation. 6+ active threads.
- **ai-cos-mcp Server:** FastMCP Python on DO droplet (systemd). Tools: `health_check`, `cos_load_context`, `cos_score_action`, `cos_get_preferences`. Connected via Tailscale.
- **digest.wiki:** Next.js 16 + TypeScript + Tailwind v4. Live at https://digest.wiki. Auto-deploys on `git push origin main` via Vercel Git Integration (~15s).
- **Droplet Infrastructure:** DO droplet ($12/mo), Postgres, Tailscale, systemd services, uv for Python.
- **Preference Store:** `action_outcomes` table in Postgres. Captures accept/reject with scoring factor snapshots.
- **Notion as full data layer:** 8 databases with cross-references, all actively used. Field-level ownership defined in DATA-SOVEREIGNTY.md.
- **IDS methodology fully encoded:** In content analysis prompt, CONTEXT.md, and Thesis Tracker conviction engine.
- **Scoring models defined:** Action Scoring (7 factors), People Scoring (9 factors), thresholds set. `action_scorer.py` exists (172 lines).
- **6+ active thesis threads:** Agentic AI Infrastructure, Cybersecurity/Pen Testing, USTOL/Aviation, SaaS Death/Agentic Replacement (High conviction), CLAW Stack, Healthcare AI Agents. New threads created autonomously by ContentAgent.
- **Claude Code as primary build surface:** Build Traces (O(1) context, rolling window + compaction), branch lifecycle CLI, CLAUDE.md + CONTEXT.md as living brain, `claude-ai-sync/` for cross-surface memory alignment.
- **Cross-surface alignment:** `claude-ai-sync/` folder with versioned memory entries for manual paste into Claude.ai Settings → Memory.

### 9.2 Connected but Not Yet Automated

- Granola MCP (meeting transcripts accessible, processing not automated)
- Google Calendar MCP (schedule data accessible)
- Gmail MCP (email accessible, not processed by agents)

### 9.3 Designed but Not Yet Built

- **PostMeetingAgent** — Granola transcript → IDS updates → actions
- **OptimiserAgent** — Scoring models → ranked lists → gap analysis → "best meetings today"
- **IngestAgent** — Screenshots, URLs → Network/Companies DB enrichment
- **SyncAgent** — Notion ↔ Postgres consistency per DATA-SOVEREIGNTY.md
- **action_scorer.py integration** — Script exists, not wired into Content Pipeline
- **Action Frontend on digest.wiki** — Accept/dismiss UX, consolidated `/actions` route
- **Content Pipeline v5** — Full portfolio coverage (200+ companies), semantic matching, multi-source
- **WhatsApp integration** — Proactive push, capture, meeting prep
- **Vector DB** — pgvector, correctly deferred until triggers fire

### 9.4 Remaining Gaps

- No autonomous meeting processing (Granola signals leak between meetings)
- Scoring models defined but not production-wired into action proposals
- Preference injection not yet flowing into all reasoning sessions
- Relationship temperature not formally modeled (one of 9 People Scoring factors)
- No proactive push channel (WhatsApp)
- No triage surface beyond Notion (action volume increasing without proper frontend)

---

## 10. The Build Path

### Phase 1: Wire the Intelligence ✅ ~70% COMPLETE
*Make the existing system smarter.*

**Done:**
- ✅ Content Pipeline autonomous on droplet
- ✅ Thesis Tracker conviction engine (autonomous conviction updates, key questions, evidence accumulation, thread creation)
- ✅ ai-cos-mcp server live (4 tools)
- ✅ Preference Store table exists
- ✅ Droplet + Postgres infrastructure

**Remaining:**
- Wire `action_scorer.py` into Content Pipeline — every proposed action gets scored
- Expand MCP tools (network, retrieval, sync operations)
- Full preference injection into all reasoning sessions

### Phase 2: Build the Action Frontend
*Give Aakash a proper triage surface.*

1. Accept/dismiss on digest pages (digest.wiki `/d/{slug}` → add action buttons)
2. Consolidated `/actions` route on digest.wiki — all pending actions, filterable
3. Portfolio dashboard view
4. Thesis tracker view with evidence feed

**Value delivered:** Without a triage surface, increased action volume from Phase 1 overwhelms the chat-based review workflow. This is the first real Operating Interface.

### Phase 3: Autonomous Runners
*The system processes all signal types autonomously.*

Build order follows dependency chain:
1. **SyncAgent** — Infrastructure. Notion ↔ Postgres consistency per DATA-SOVEREIGNTY.md
2. **PostMeetingAgent** — Highest value-add: direct IDS signal from every meeting (7-8/day)
3. **IngestAgent** — Processes manual captures (screengrabs, URLs, bookmarks)

**Value delivered:** The system processes signals 24/7 without Aakash opening anything. Every meeting, every content signal, every capture gets analyzed, scored, and either surfaced or stored.

### Phase 4: Optimisation + Multi-Surface
*Full "what's next?" reasoning + WhatsApp push.*

1. **OptimiserAgent** — runs scoring models, produces ranked lists, detects gaps
2. `cos_best_meetings_today()` with full People Scoring Model
3. Relationship temperature scoring (frequency from Granola history)
4. WhatsApp integration (proactive push + capture)
5. Vector DB (pgvector, if triggered by 2nd signal source or 500+ companies)

**Value delivered:** The AI CoS is no longer something Aakash goes to — it comes to him. Full "what's next?" reasoning across the entire stakeholder + action space.

### Phase 5: Always-On Intelligence
*The full singular entity.*

- Continuous signal ingestion across all surfaces
- Real-time optimization as signals arrive
- Meeting slot filling (cancellation → instant scored replacement)
- Network Pulse (weekly WhatsApp: relationships to tend, connections to make)
- Thesis convergence detection (multiple signals from different sources pointing to same insight)
- 24/7 compound intelligence — the system gets measurably better every month

---

## 11. What 100x Looks Like

### A Day in Aakash's Life (Phase 4+)

**7:30 AM:** WhatsApp from AI CoS: Morning brief with all 8 meetings contextualized, top 3 follow-ups due, one thesis connection surfaced overnight ("The pen testing company from your pipeline had a competitor raise $30M yesterday — three portfolio companies have exposure").

**8:45 AM:** Pre-meeting brief lands on WhatsApp: full IDS context on the founder he's about to meet, mutual connections, note: "This founder's approach to vertical AI connects to your CLAW stack thesis. Your Thesis Tracker shows 2 open questions this meeting could answer."

**9:30 AM:** Meeting ends. Voice note to AI CoS: "Good meeting, sharp founder. Strong on product, questions on GTM. Follow up on customer references. ++product, ?gtm." AI CoS responds: "Captured. Drafted Notion update and follow-up task for customer references. The Confido Health channel partner approach might be relevant — want me to pull that playbook? Approve update?"

**11:00 AM:** Screenshot of a LinkedIn post dropped to AI CoS on WhatsApp. Response: "This is [Name], [Title] at [Company]. Matches Collective criteria — strong cybersecurity evaluator. Added to Network DB as EXT Target, flagged for outreach."

**2:00 PM:** Proactive: "BRC for [Company] scheduled next week. IDS deck needed 48-72hrs prior. Draft compiled from all IDS history. [Link]. Review when you get a chance."

**5:30 PM:** End of day: "Today: 4 meetings processed, 2 signals enriched, 1 pipeline company moved from Maybe to Maybe+, 3 follow-ups completed, 2 new. Your USTOL thesis has 3 new data points — conviction moved to Evolving Fast. Tomorrow: 6 meetings, starting with [X] who's critical for [Y]."

**Sunday evening:** Weekly synthesis: network heat map, pipeline movement, thesis threads, follow-up accountability, next week optimization. Aakash reviews in 10 minutes instead of 2 hours of mental backlog clearing.

### The Compound Effect

**Without AI CoS:** Actions driven by who reaches out, what Sneha schedules, what Aakash remembers. Maybe 30-40% of his action space is optimally allocated.

**With AI CoS:** Every action slot is informed by a scored, contextual analysis of his entire stakeholder space. The system catches what he'd miss: the content signal that changes conviction, the thesis thread revealing a new opportunity, the dormant relationship worth re-engaging. Maybe 70-80% optimal allocation.

The 100x comes from the flywheel: **better actions → better IDS → better decisions → better outcomes → better network → even better actions.** The flywheel accelerates because the AI CoS keeps the full picture updated and the optimization running continuously — and because the Preference Store makes the system smarter with every decision Aakash makes.

---

## 12. Design Principles

1. **WhatsApp-first, mobile-native.** Any system that requires desktop as primary interaction will fail. The AI CoS meets Aakash where he already is.

2. **Capture must be zero-friction.** Screengrab-as-memory and WhatsApp-self-as-bookmark exist because they're lowest-friction. The AI CoS must be even lower friction — or it won't get used.

3. **IDS is the core operating methodology.** Everything compounds. A meeting note from November becomes critical context for a BRC in March. Every signal is a node in an ever-growing intelligence graph, not a transient event.

4. **Judgment stays with Aakash. Everything else is leverage.** The AI CoS never makes investment decisions. It makes Aakash's judgment more effective by ensuring right context, right time, right connections.

5. **Plumbing serves the optimizer, not the other way around.** Never build infrastructure for its own sake. Every piece of plumbing must make "What's Next?" answerable with higher accuracy.

6. **Runners execute what Claude Code designs.** Narrow specialists, not general agents. Human-in-loop for design, autonomous for execution of known patterns.

7. **The preference store is the compounding mechanism.** Without learning from accept/reject history, you have smart one-shot reasoning but no improvement over time.

8. **Each signal source independently improves the loop.** YouTube alone already generates thesis updates and portfolio actions. Each new source compounds.

9. **Gradual trust building.** Start with read-only intelligence. Earn the right to act through demonstrated accuracy. Category-level trust, not blanket permission.

10. **The system enforces its own maintenance.** Build Traces (O(1) context), CLAUDE.md + CONTEXT.md as living brain, session close checklists, claude-ai-sync for cross-surface alignment.

---

## Changelog

| Version | Date | Key Changes |
|---------|------|-------------|
| v1 | Dec 2024 | Task automation: morning briefs, post-meeting capture, weekly reviews. 7 specialist agents + Orchestrator. |
| v2 | Jan 2025 | Network optimization: "Who should I meet next?" Four buckets, People Scoring Model, Composite Score. |
| v3 | Mar 2026 | Full action space: "What's next?" Stakeholder + intelligence actions. Action Scoring subsumes People Scoring. Learning Loop. |
| v4 | Mar 2026 | Architecture brainstorm synthesis. MCP hook layer, Agent SDK narrow runners, Preference Store, Postgres migration path. Corrections from 39 sessions of ground truth. |
| v5 | Mar 2026 | **Claude Code era update.** ContentAgent autonomous on droplet. Thesis Tracker = AI-managed conviction engine (6-level conviction, key questions lifecycle, autonomous thread creation). MCP server + Postgres live. Cowork fully deprecated. DATA-SOVEREIGNTY.md for field-level ownership. Build Traces system. Cross-surface alignment via claude-ai-sync/. Build path updated with ~70% Phase 1 complete. |
