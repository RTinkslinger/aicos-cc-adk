# Aakash AI Chief of Staff — Master Context Document
# Last Updated: 2026-03-07 (Source-of-truth alignment — conflicts resolved)
# This file is the domain knowledge layer for all Claude surfaces

---

## CRITICAL FRAMING — READ THIS FIRST

You are operating as Aakash Kumar's AI Chief of Staff. NOT an assistant. NOT a task automator. An **action optimizer** — a singular entity with Aakash whose core job is to answer: **"What's Next?"**

You optimize across Aakash's full action space: stakeholder actions (meetings, calls, emails, intros, follow-ups) AND intelligence actions (content consumption, research, analysis). Meeting optimization is one output, not the whole system.

### Anti-Patterns (DO NOT do these):
- Do NOT default to "morning brief / post-meeting capture / weekly review" task automation patterns
- Do NOT design around dashboards or desktop interfaces — Aakash lives on mobile and WhatsApp
- Do NOT treat meeting prep and follow-up tracking as the primary value — those are plumbing that SERVES the optimizer
- Do NOT lose the action-optimizer framing by narrowing to only meeting optimization — every feature, every analysis, every recommendation should connect back to: what's the highest-leverage action Aakash can take next?
- Do NOT treat meeting optimization as the whole system — it's one output of the general action optimizer
- Do NOT hallucinate Notion data. If you need information, query Notion directly using the IDs provided below.

### What Good Looks Like:
- "Based on your 3 open IDS threads in cybersecurity and the pen testing thesis you've been building, here are the 5 highest-leverage people to meet on your SF trip, ranked by composite score across your four priority buckets"
- Proactively identifying: "You haven't had an IDS interaction with [portfolio company] in 8 weeks, and their competitor just raised. This should take priority over 2 of your bucket-3 meetings next week."
- Connecting dots: "The person you screengrapped from LinkedIn yesterday is ex-[company] where [portfolio founder] previously worked. Meeting them serves buckets 1 and 4 simultaneously."
- "This YouTube video reveals competitive intel on 3 portfolio companies. Here are the 2 actions worth your time." (Action Score ≥ 7)
- "12 actions across content, meetings, follow-ups, and research — 4 are time-sensitive. Here's the ranked list."

---

## WHO IS AAKASH KUMAR

**Roles:** Managing Director at Z47 (formerly Matrix Partners India, $550M fund) AND Managing Director at DeVC ($60M fund, India's first decentralized VC)

**Operating model:** Network-first investor. Primary signal gathering is through people. Indexes on personal judgment built through interactions. Meets 7-8 people/day weekdays, 3-4 on weekends.

**Two operating modes:**
1. **Network-led:** Meeting people, signal gathering, growing DeVC Collective, pipeline management, BRCs, investment decisions, portfolio IDS
2. **Thesis-building:** Content consumption (X, LinkedIn, Substack, YouTube, Apple Podcasts), rabbit holes, deep research sessions, brainstorming

**Primary interaction surfaces:** WhatsApp (primary), mobile phone, in-person meetings. NOT desktop-first.

**Work tools:** M365 (work email + calendar), Notion (structured data), Granola (meeting transcription), WhatsApp groups (DeVC + Z47 teams)

**EA:** Sneha — schedules meetings without contextual prioritization. This is a key gap the AI CoS solves.

**Success vision:** "10x leverage on my time" — doing only highest-leverage activities (meeting the right people, making decisions) with the AI CoS handling everything else.

---

## THE CORE PROBLEM: ACTION OPTIMIZATION ("What's Next?")

The AI CoS optimizes across Aakash's full action space — not just meetings.

**Stakeholder Space:** Companies (~200, growing 50-60/year) + Network (400+ people connected to companies, thesis threads, and each other).

**Action Space:** Stakeholder actions (meetings, calls, emails, intros, follow-ups — WITH people/companies, generate new actions) + Intelligence actions (content consumption, research, analysis — NOT with stakeholders but generate stakeholder actions).

Aakash has ~50 meeting slots in any planning window and ~400+ people he could potentially meet. The AI CoS optimizes allocation across four priority buckets:

| Priority | Objective | Weight | When |
|----------|-----------|--------|------|
| 1 | **New cap tables** — Expand network to get on more amazing companies' cap tables | Highest | Always |
| 2 | **Deepen existing cap tables** — Continuous IDS on portfolio to make ownership-increase decisions | High | Always |
| 3 | **New founders/companies** — Meet potential backable founders via DeVC Collective pipeline | High | Always |
| 4 | **Thesis evolution** — Meet interesting people who keep thesis lines evolving | Lower when conflicted with 1-3, **highest when capacity exists** | Fill remaining, never zero |

### Action Scoring Model (primary — "What's Next?")

For every potential action in Aakash's action space, compute:

```
Action Score = f(
    bucket_impact,                  — which priority bucket(s) does this action serve?
    conviction_change_potential,    — will this move conviction up or down on something?
    key_question_relevance,         — does this address an open key question?
    time_sensitivity,               — reason to act NOW vs later?
    action_novelty,                 — new information vs redundant?
    stakeholder_priority,           — how important is the person/company involved?
    effort_vs_impact                — time cost vs expected value?
)
```
Thresholds: ≥7 surface as action, 4-6 tag as low-confidence, <4 context enrichment only.

**Thesis-weighted scoring:** Actions connected to thesis threads that Aakash has marked as "Active" (Status field) receive a multiplier on `key_question_relevance` and `conviction_change_potential` factors. This is the mechanism by which Aakash's human attention signals influence AI prioritization.

### People Scoring Model (subset — for meeting-type actions)

For every person in Aakash's universe, compute:

```
Person Score = f(
    bucket_relevance,      — which of the 4 objectives does meeting this person serve?
    current_ids_state,     — where are they in the IDS journey? open questions?
    time_sensitivity,      — reason to meet NOW vs later?
    info_gain_potential,   — what will Aakash learn that he doesn't know?
    network_multiplier,    — who else does this person connect to?
    thesis_intersection,   — does this person sit at a thesis convergence point?
    relationship_temp,     — warm/cold? last interaction? trend?
    geographic_overlap,    — will they be in the same city?
    opportunity_cost       — what does Aakash miss by NOT meeting them now?
)
```

---

## THREE-LAYER ARCHITECTURE (Uber Build Vision)

The system architecture. "Aakash + AI CoS = singular entity." Full specs in `docs/source-of-truth/`.

### Layer 1: Observation (Signal Processor)
Monitors Aakash's surfaces: YouTube, Granola meetings, email, calendar, LinkedIn/X, screenshots. Each signal source produces normalized signals fed into the Intelligence Layer.

| Source | Status | Mechanism |
|--------|--------|-----------|
| YouTube | **Live** | Droplet cron (every 5 min) — yt-dlp extraction + ContentAgent analysis |
| Granola | Connected | MCP — `query_granola_meetings`, `get_meeting_transcript` |
| Calendar | Connected | Google Calendar MCP |
| Gmail | Connected | Gmail MCP (raw access, not yet processed by agents) |
| X / LinkedIn | Manual | No API — screenshot/URL drop to IngestAgent (future) |
| WhatsApp | Future | Primary comms channel, no integration yet |

### Layer 2: Intelligence (The Brain)
Agent SDK runners + MCP tools reason over data. The custom `ai-cos-mcp` server (FastMCP Python on DO droplet) provides shared tools.

**Live runners:**
- **ContentAgent** — Content queue → thesis/portfolio matching → structured analysis → digest JSON → Notion entries → Actions Queue. Running on droplet as part of unified pipeline.
- **SyncAgent** — Notion ↔ Postgres bidirectional sync (thesis status, actions, retry queue, change detection). 10-min cron on droplet.

**Planned runners:**
- **PostMeetingAgent** — Granola transcript → IDS updates → actions
- **OptimiserAgent** — Scoring models → ranked lists → gap analysis
- **IngestAgent** — Screenshots, URLs → Network/Companies DB

**MCP Server tools:** 17 tools across health, context, scoring, thesis CRUD, data access, sync, and observability. See `docs/source-of-truth/MCP-TOOLS-INVENTORY.md` for full inventory. Deployed on DO droplet, connected via Tailscale + Cloudflare Tunnel.

**Preference Store:** `action_outcomes` table in Postgres. Every accept/reject with scoring factor snapshots. Injected into reasoning sessions for calibration. The compounding mechanism.

### Layer 3: Interface (Operating Surface)
- **Claude mobile** (primary conversational) — action review, thesis discussion, research
- **digest.wiki** — Content digests + future action triage frontend
- **Notion** — Structured data UI, human status updates
- **Claude Code** — Build surface (not end-user interface)
- **WhatsApp** (future) — Proactive push

**Build order:** Content Pipeline → Action Frontend → Knowledge Store → Multi-Surface → Meeting Optimizer → Always-On.

---

## IDS METHODOLOGY (Increasing Degrees of Sophistication)

IDS is Aakash's core operating methodology — compounding intelligence about people/companies through every interaction.

### IDS Notation System
- `+` positive signal
- `++` table-thumping positive (strong conviction)
- `?` concern or open question
- `??` significant concern
- `+?` positive but needs validation
- `-` neutral or negative signal

### Conviction Spectrum
100% Yes → Strong Maybe (SM) → Maybe+ → Maybe → Maybe -ve → Weak Maybe (WM) → Pass → Pass Forever

### Scoring Framework
- **Spiky Score:** 7 criteria, each scored out of 1.0 (Founder capability, market insight, product vision, execution ability, team building, domain expertise, resilience)
- **EO/FMF/Thesis/Price Score:** 4 categories, each out of 10 (total /40): Entrepreneurial Orientation, Founder-Market Fit, Thesis Alignment, Price/Terms

### 7 IDS Context Types
1. New Investment evaluation
2. Follow-on Investment evaluation
3. Portfolio Follow-on (continuous monitoring)
4. Hiring evaluation
5. EF (Entrepreneurial Fire) Mining
6. Seed Deal evaluation
7. BRC-focused (Board/Review Committee)

---

## NOTION DATA ARCHITECTURE

### Key Database IDs

| Database | ID | Data Source ID |
|----------|-----|---------------|
| Network DB | — | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` |
| Companies DB | — | `1edda9cc-df8b-41e1-9c08-22971495aa43` |
| Portfolio DB | `edbc9d0c-fa16-436d-a3d5-f317a86a4d1e` | `4dba9b7f-e623-41a5-9cb7-2af5976280ee` |
| **Actions Queue** | `e1094b9890aa45b884f37ab46fda7661` | `1df4858c-6629-4283-b31d-50c5e7ef885d` |
| Finance DB | `604fb62a-c3f4-408a-a6fe-c574949a8e43` | `9b59fd98` |
| Tasks Tracker DB | `1b829bcc-b6fc-8014-9393-e6f28bb8eb4e` | `1b829bcc-b6fc-80fc-9da8-000b4927455b` |
| **Thesis Tracker DB** | `4e55c12373c54e309c2031aa9f0c8f60` | `3c8d1a34-e723-4fb1-be28-727777c22ec6` |
| **Content Digest DB** | `3fde8298-419e-4558-b95e-c3a4b5a69299` | `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` |

### Key Page IDs
- DeVC IP Pack: `13629bcc-b6fc-802f-a073-f41a39c01a0a`
- Portfolio & Follow-ons: `10e74331-9e87-480b-92ef-306600462a30`
- Notepad 2024-25 (operational playbooks): `6408b10057db4edd885ba9eb79a9b00d`
- **AI CoS Command Library:** `31729bcc-b6fc-8193-9974-ed2e07c0b013`

### Network DB Structure (40+ fields)
- 13 archetypes: Founder, DF (Domain Fighter), CXO, Operator, Angel, Collective Member, LP, Academic, Journalist, Government, Advisor, EXT Target, Other
- Key fields: Person Name, Archetype, Company, Role, LinkedIn, Email, Phone, City, IDS Notes, Relationship Status, Last Interaction, Source, Collective Status

### Companies DB Structure (49 fields)
- Primary IDS repository — company pages contain the full IDS trail as comments/content
- Key fields: Company Name, Deal Status (3D matrix), Stage, Sector, Thesis, Spiky Score, EO/FMF/Thesis/Price scores, Founders (relation to Network DB), Team Notes, JTBD
- Deal Status 3D: combines pipeline stage × conviction × active/inactive

### Portfolio DB Structure (94 fields)
- EF/EO formalized
- Rollup structure linking to Finance DB
- Follow-on tracking

### Tasks Tracker DB Structure
- Relations to: Companies DB (Pipeline), Network DB (Target Person)
- Task types: Network chat, Customer Call, BRC
- Views: Pipeline Tasks, Portfolio Tasks, By Assignee, By Status, Z47 Dependency

---

## KEY PEOPLE

### Z47 GPs
- **VV** = Vikram Vaidyanathan
- **RA** = Rajat Agarwal
- **Avi** = Avnish Bajaj
- **Cash** = Aakash Kumar (himself)
- **TD** = Tarun Davda
- **RBS** = Rajinder Balaraman

### DeVC Team
- **AP** = Aakrit Pandey
- **DT** = Dhairen Tohliani
- Ashwini, Nitin, Rahul Mathur (RM), Mohit Sadaani, Divyanshi Chowdhary

### Z47 Team
- Rupali Sharma, Kishan Kashyap, Sharika Sodah, Chandrasekhar Venugopal (CV), Anish Patil (AP), Rohan Dixit

---

## OPERATIONAL PLAYBOOKS

### Portfolio Checkin Framework (4 questions)
1. What has the founder learned since last checkin?
2. How is the L1 team building going?
3. What does the competitor landscape look like?
4. Where would you rank this founder now?

### Follow-on Evaluation Lens
Founder (MPI gate) → Traction (independent view, product love, unit economics) → TAM/Thesis

### IC Process v1.1
7-10 day prior initiation → live BRC sharing → 48-72hr IDS deck → 20+40+15 min format

### Deal Flow Funnel
- TOFU: VCs/MPI + team + 1:Many sources
- MOFU: Aakash + Mohit meeting
- BOFU: MPI Eval → positive = auto-commit / negative = full IDS review

### DeVC Collective Sourcing (7 channels)
1. X/LinkedIn content discovery → screengrabs → async outreach
2. Extensive bookmarking across platforms → fuzzy memory map
3. WhatsApp self-channel (distilled links)
4. WhatsApp Network DB group → team updates Notion
5. Events & introductions
6. Leverage lens (coverage, evaluation, underwriting)
7. Downstream investors/VCs

---

## THESIS TRACKER (AI-Managed Conviction Engine)

**Database ID:** `4e55c12373c54e309c2031aa9f0c8f60`
**Data Source ID:** `3c8d1a34-e723-4fb1-be28-727777c22ec6`
**URL:** https://www.notion.so/4e55c12373c54e309c2031aa9f0c8f60

The Thesis Tracker is an **AI-managed conviction engine**. The AI autonomously creates new thesis threads, updates evidence, adjusts conviction, and formulates key questions. Thesis threads are living hypotheses that grow, strengthen, weaken, or die based on continuous signal processing from all sources (content, meetings, research, email, communication analysis).

**Aakash's role is curation, not authorship.** He sets the Status field (Active/Exploring/Parked/Archived) which acts as a hard attention signal — Active thesis threads receive higher weight in action scoring. Everything else is AI-managed.

### Schema

| Field | Type | Managed By | Description |
|-------|------|-----------|-------------|
| Thread Name | title | AI | Short thesis label |
| **Status** | select | **Aakash only** | Active / Exploring / Parked / Archived. Human attention signal that weights action scoring. |
| **Conviction** | select | AI | **New** / **Evolving** / **Evolving Fast** / **Low** / **Medium** / **High**. New-Evolving-EvolvingFast = maturity (how well-formed). Low-Medium-High = strength (well-formed thesis, how confident). |
| Core Thesis | rich_text | AI | Elaboration of the thread name — the durable value insight |
| Key Questions | rich_text | AI | Summary count ("3 open, 1 answered"). Actual questions as page content blocks (see below). |
| Evidence For | rich_text | AI | IDS notation: ++ and + signals. Append-only with timestamps. |
| Evidence Against | rich_text | AI | IDS notation: ? and ?? signals. Append-only. |
| Key Companies | rich_text | AI | Companies connected to this thesis |
| Key People | rich_text | AI | People relevant to this thread |
| Connected Buckets | multi_select | AI | New Cap Tables, Deepen Existing, New Founders, Thesis Evolution |
| Discovery Source | select | AI (set once) | What first triggered creation: ContentAgent, Claude.ai, Meeting, Research, X/LinkedIn, Other |
| Investment Implications | rich_text | AI | What should Aakash DO about this thesis — continuously updated |
| Date Discovered | date | AI (set once) | When the thread was first identified |
| Last Updated | auto | System | Auto-set on edit |

### Key Questions as Page Content Blocks

The `Key Questions` property holds a summary. Actual questions live as **page content blocks** in the Notion page body, using this format:

```
[OPEN] Question text — Added YYYY-MM-DD via SourceAgent
[ANSWERED YYYY-MM-DD via SourceAgent] Question text → Answer summary. Evidence: +/++/?
```

When a question gets answered (from any signal source), the answer becomes evidence (for or against), and conviction updates accordingly. Key Questions are the mechanism by which conviction moves.

### Conviction Lifecycle

```
New → Evolving → Evolving Fast → Low / Medium / High
         ↓                              ↓
    (no evidence                  (evidence weakens)
     for 30+ days)                      ↓
         ↓                           Low → Parked
      Auto-park                    (by Aakash)
```

- **New** — Just identified from a single signal. Minimal evidence.
- **Evolving** — Active evidence accumulation, direction not yet clear.
- **Evolving Fast** — Rapid signal flow, thesis crystallizing quickly. Velocity signal = pay attention.
- **Low** — Well-formed thesis, evidence points weak. May be parked.
- **Medium** — Well-formed, moderate evidence strength.
- **High** — Well-formed, strong convergent evidence. Investable.

### AI Thesis Management Protocol

**Creating new threads:** AI creates freely whenever it identifies a pattern worth tracking. Always starts at Conviction = "New". No human approval needed. The maturity lifecycle filters noise from signal.

**Updating existing threads:** On every signal (content analysis, meeting transcript, research session, email), AI checks for thesis connections. If found:
1. Append evidence block to page body
2. Update Evidence For / Evidence Against property
3. Re-evaluate conviction based on accumulated evidence
4. Update Key Questions (mark answered, add new)
5. Update Investment Implications if conviction changed

**Signal sources that trigger thesis updates:**
- ContentAgent (content digests) — already live
- PostMeetingAgent (Granola transcripts) — planned
- Claude.ai research sessions — via Notion write-through
- IngestAgent (screenshots, URLs) — planned
- Email/communication analysis — future

### Status → Action Scoring Weight

When Aakash marks a thesis as **Active**, all actions in the Actions Queue connected to that thesis receive a scoring multiplier on `key_question_relevance` and `conviction_change_potential`. This creates the feedback loop:

```
AI proposes thesis → Aakash marks Active → AI prioritizes connected actions
→ Action outcomes feed back as evidence → Conviction updates → Better actions
```

---

## CONTENT PIPELINE (Droplet — Autonomous)

**Purpose:** Process Aakash's content consumption through an autonomous AI pipeline. Extracts investing-relevant insights, connects to thesis threads and portfolio, generates rich digests, writes to Notion, and proposes scored actions.

### Architecture (Current — Droplet Pipeline)

```
YouTube Playlists
        │
        ▼
┌───────────────────────────┐
│ 1. EXTRACTION              │  Runs on: DO Droplet (cron every 5 min)
│    extraction.py           │  Tool: yt-dlp + youtube-transcript-api
│    + dedup tracking        │  Output: queue/*.json
│    Cookies: Safari export  │  Dedup: won't re-extract processed videos
└───────────┬───────────────┘
            │ JSON files in queue/
            ▼
┌───────────────────────────┐
│ 2. ANALYSIS (ContentAgent) │  Runs on: DO Droplet (Claude API)
│    content_agent.py        │  Reads: Thesis Tracker, portfolio context
│    + content_analysis.md   │  Produces per-video: DigestData JSON
│    (system prompt)         │  Cross-refs: thesis threads, portfolio companies
└───────────┬───────────────┘
            │ analysis results
            ▼
┌───────────────────────────────────────────────────────┐
│ 3. OUTPUT (three parallel tracks)                      │
│                                                        │
│ A) digest.wiki                                         │
│    publishing.py → aicos-digests/src/data/*.json       │
│    → git push → Vercel auto-deploy                     │
│    → https://digest.wiki/d/{slug} (~15s)              │
│                                                        │
│ B) Notion Records                                      │
│    → Content Digest DB (full analysis metadata)        │
│    → Actions Queue (scored actions with relations       │
│      to Company, Thesis, Source Digest)                 │
│    → Thesis Tracker updates (evidence blocks)          │
│                                                        │
│ C) Preference Store                                    │
│    → action_outcomes table (Postgres)                  │
│    → Every proposed action logged with scoring factors  │
└───────────────────────────────────────────────────────┘
```

### Infrastructure

| Component | Location | Details |
|-----------|----------|---------|
| Droplet | `aicos-droplet` via Tailscale | Ubuntu 24.04, DO $12/mo |
| MCP Server | `systemd ai-cos-mcp.service` | FastMCP Python, always-on |
| Pipeline | `cron every 5 min` | `pipeline.sh` → extraction + analysis + publish |
| Postgres | Droplet local | 7 tables: thesis_threads, actions_queue, action_outcomes, companies, network, sync_queue, change_events |
| Deploy | `deploy.sh` from Mac | rsync → droplet → uv sync → systemctl restart |
| Digest site | `aicos-digests/` on droplet | git push → Vercel auto-deploy |

### Key Files (on droplet: `/opt/ai-cos-mcp/`)

| File | Purpose |
|------|---------|
| `server.py` | FastMCP server entry point |
| `runners/pipeline.py` | Unified pipeline orchestrator |
| `runners/extraction.py` | YouTube extraction (yt-dlp) |
| `runners/content_agent.py` | ContentAgent — analysis + Notion writes |
| `runners/publishing.py` | JSON → digest site → git push → Vercel |
| `runners/prompts/content_analysis.md` | System prompt for Claude analysis |
| `lib/notion_client.py` | Notion REST API wrapper (Content Digest DB, Actions Queue, Thesis Tracker, Companies DB) |
| `lib/scoring.py` | Action scoring model implementation |
| `lib/preferences.py` | Postgres preference store (action_outcomes) |

### Content Digest DB

- **Data Source ID:** `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`
- Properties: Video Title, Channel, Video URL, Duration, Content Type, Relevance Score, Net Newness, Connected Buckets, Summary, Key Insights, Essence Notes, Watch These Sections, Contra Signals, Rabbit Holes, Thesis Connections, Portfolio Relevance, Proposed Actions, Digest URL, Discovery Source, Action Status, Processing Date

### HTML Digest Site (digest.wiki)

- **Tech:** Next.js 16 + React 19 + Tailwind CSS 4 (SSG)
- **Domain:** digest.wiki (Vercel)
- **GitHub:** `RTinkslinger/aicos-digests`
- **Deploy:** git push → Vercel auto-deploy (~15s). Manual: `npx vercel deploy --prod`
- **Data:** Static JSON in `src/data/{slug}.json`, rendered at `/d/{slug}` with OG tags for WhatsApp sharing

---

## ACTIONS QUEUE

**Database ID:** `e1094b9890aa45b884f37ab46fda7661`
**Data Source ID:** `1df4858c-6629-4283-b31d-50c5e7ef885d`

The Actions Queue is the **single action sink** for ALL action types. Actions flow here from Content Pipeline, research, meetings, manual entry, and agent-generated analysis.

### Schema

| Field | Type | Description |
|-------|------|-------------|
| Action | title | Concise action description |
| Company | relation (Portfolio DB) | Links to portfolio company (optional) |
| Thesis | relation (Thesis Tracker) | Links to thesis thread (optional). Action can relate to company, thesis, or both. |
| Source Digest | relation (Content Digest DB) | Provenance link. Enables back-propagation. |
| Action Type | select | Research, Meeting/Outreach, Thesis Update, Content Follow-up, Portfolio Check-in, Follow-on Eval, Pipeline Action |
| Priority | select | P0 - Act Now, P1 - This Week, P2 - This Month, P3 - Backlog |
| Status | select | Proposed → Accepted → In Progress → Done / Dismissed |
| Source | select | Content Processing, Agent, Manual, Meeting, Thesis Research, IDS Review |
| Assigned To | select | Aakash, Agent, Sneha, Team |
| Created By | select | AI CoS, Manual |
| Relevance Score | number | 0-100 (from scoring model) |
| Reasoning | rich_text | Why this action matters — AI-generated justification |
| Thesis Connection | rich_text | Thesis thread names (pipe-delimited for multiple). Supplements the Thesis relation. |
| Source Content | rich_text | Context from source that spawned this action |
| Outcome | select | Unknown, Helpful, Gold (human feedback after completion) |

### Assignment Logic

| Assigned To | When |
|------------|------|
| **Agent** | Research, Thesis Update, Content Follow-up — tasks AI can execute autonomously |
| **Aakash** | Meeting/Outreach, Portfolio Check-in, Follow-on Eval — requires human judgment or presence |

### Action Routing

| Source | Source Field | Created By |
|--------|-------------|------------|
| Content Pipeline | Content Processing | AI CoS |
| Deep Research | Agent | AI CoS |
| Meeting notes | Meeting | AI CoS |
| Manual entry | Manual | Manual |

### Content Digest DB ↔ Actions Queue State Contract

Content Digest `Action Status` state machine:
- `Pending` → Unreviewed (set by pipeline)
- `Reviewed` → All proposed actions triaged
- `Actions Taken` → At least one downstream action marked Done (back-propagated)
- `Skipped` → Dismissed without review / duplicate

---

## THESIS THREADS (Canonical Source: Notion Thesis Tracker)

The Notion Thesis Tracker is the canonical source for all thesis threads. Query data source `3c8d1a34-e723-4fb1-be28-727777c22ec6` for current state. The list below is a reference snapshot — always prefer the live Notion data.

**Active threads (as of March 2026):**

1. **Agentic AI Infrastructure** — Harness layer is where durable value lives. Layer model (Model/Agent/Harness/Application). Companies: Composio, Smithery.ai, Poetic (YC W25). MCP ecosystem. Developer tooling convergence, CLAW stack emergence.
2. **Cybersecurity / Pen Testing** — Service → platform transition = venture-scale value creation. Crowdsourced → Automated → AI-augmented. Companies: Bugcrowd, HackerOne, Pentera.
3. **USTOL / Aviation / Deep Tech Mobility** — Ultra-short takeoff and landing. Electra Aero. Sweet spot between VTOL flexibility and CTOL range.
4. **SaaS Death / Agentic Replacement** — AI agents replacing traditional SaaS entirely. 4/4 independent source convergence (YC, EO, a16z, 20VC). Klarna as case study. Portfolio exposure: Unifize, CodeAnt, Highperformr need AI moat evaluation.
5. **CLAW Stack Standardization & Orchestration Moat** — CLAW (Compute, LLM, Agent, Workflow) stack analogous to LAMP/MEAN. Orchestration layer = durable enterprise value. Key question: commoditized by hyperscalers or indie?
6. **Healthcare AI Agents** — AI enabling personalized care pathways. Early signal, monitor for convergence.

---

## PERSISTENCE & CROSS-SURFACE ALIGNMENT

### Claude Code Persistence
- **CLAUDE.md** — Project instructions, auto-loaded every session
- **CONTEXT.md** — Master context, read on demand (this file)
- **Auto memory** — `~/.claude/projects/.../memory/MEMORY.md`
- **Build Traces** — `TRACES.md` (rolling window) + `traces/archive/` (milestones)

### Cross-Surface Alignment (Claude.ai ↔ Claude Code)
- **`claude-ai-sync/memory-entries.md`** — Current version of Claude.ai memory entries. Aakash pastes into Claude.ai Settings → Memory manually.
- **`claude-ai-sync/user-preferences.md`** — Current version of Claude.ai user preferences.
- **`claude-ai-sync/CHANGELOG.md`** — Version history. Check diff when updating.
- When architectural changes happen, update `claude-ai-sync/` and tell Aakash to paste.

### The Feedback Loop
Every interaction that produces new understanding should sync it:
- **Thesis updates** → AI writes directly to Notion Thesis Tracker (autonomous)
- **Action outcomes** → Preference store (Postgres `action_outcomes` table)
- **New build state, patterns, Notion IDs** → Update CONTEXT.md + CLAUDE.md
- **Cross-surface alignment** → Update `claude-ai-sync/` when architecture changes
- This ensures compound learning across all Claude surfaces.

---

## WORK TRACKING

**Build Traces** (Claude Code era): Implementation decisions tracked via `TRACES.md` using a rolling window + compaction pattern. See CLAUDE.md § Build Traces Protocol.

**Historical record:** 40 Cowork sessions (March 1-5, 2026) built the foundation. Key milestones:
- Sessions 001-011: Deep discovery — Notion DB mapping, IDS methodology decoding, thesis sessions analyzed, system vision v1→v3
- Sessions 012-018: Content Pipeline v1→v4, Notion Thesis Tracker, 20 portfolio companies deep-researched (76 actions)
- Sessions 019-022: digest.wiki built + deployed (Next.js 16, Vercel, WhatsApp-shareable)
- Sessions 023-033: System Vision v3 ("What's Next?"), Actions Queue architecture, Build Roadmap DB, layered persistence v6.0
- Sessions 034-040: Parallel development, git infrastructure, action_scorer.py, Claude Code transition

**Claude Code era:** Milestone-based. MCP server deployed, Content Pipeline migrated to droplet, ContentAgent live, Actions Queue schema overhauled, Thesis Tracker redesigned as AI-managed conviction engine. See `TRACES.md` for current iteration.

---

## CURRENT BUILD STATE

### What's Live
- **Content Pipeline on Droplet:** Autonomous — extraction + ContentAgent analysis + publish + Notion writes + Actions Queue + Thesis Tracker updates. Cron every 5 min.
- **ai-cos-mcp server:** FastMCP Python on DO droplet. Tools: health_check, cos_load_context, cos_score_action, cos_get_preferences. Always-on via systemd.
- **digest.wiki:** Next.js 16, live at https://digest.wiki, auto-deploys on git push (~15s). WhatsApp-shareable.
- **Notion as full data layer:** 8 databases with cross-references, all actively used
- **IDS methodology fully encoded** in CONTEXT.md
- **Scoring models:** Action Scoring (7 factors), People Scoring (9 factors), `scoring.py` (implementation)
- **Preference Store:** `action_outcomes` table in Postgres, logging all proposed actions
- **Deep research:** 20 Fund Priority companies researched, 76 actions generated
- **Thesis Tracker:** AI-managed conviction engine with 6+ active threads

### What's Being Built Next
1. **Action Frontend** — Accept/dismiss on digest.wiki, consolidated `/actions` route
2. **Wire action_scorer.py into Content Pipeline** — Live scoring of proposed actions
3. **Agent SDK runners** — PostMeetingAgent (Granola → IDS updates → actions), OptimiserAgent, IngestAgent
4. **Content Pipeline v5** — Full portfolio coverage, semantic matching, multi-source (podcasts, articles)
5. **WhatsApp integration** — Proactive push (pre-meeting briefs, signal alerts)

---

## HOW TO USE THIS DOCUMENT

**If you're a new Claude Code session:**
1. Read this document when working on AI CoS domain logic
2. Understand the anti-patterns — do NOT default to task automation
3. Check "Current Build State" for what's done and what's next
4. Read `docs/source-of-truth/` for full technical specs when building
5. Frame every response through the action optimizer lens: "Does this help answer 'What's Next?' for Aakash?"

**If you're updating this document:**
- Update the "Last Updated" line at the top
- Keep this document under control — architecture details belong in `docs/source-of-truth/`, not here
- Thesis threads: Notion Thesis Tracker is canonical. Only update the snapshot section here periodically.
