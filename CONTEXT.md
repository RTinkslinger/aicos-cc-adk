# Aakash AI Chief of Staff — Master Context Document
# Last Updated: 2026-03-05 (Session 040 — Claude Code Transition)
# This file is the SINGLE SOURCE OF TRUTH for all Claude Code sessions

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

## THREE-LAYER ARCHITECTURE

The system is evolving from session-based development to a persistent, autonomous architecture. Full specs in `docs/architecture/`.

### Layer 1: Observation (Signal Processor)
Continuously monitors all of Aakash's surfaces: YouTube, Granola meetings, email, calendar, LinkedIn/X, screenshots. Each signal source produces a normalized Signal fed into the Intelligence Layer. Currently live: YouTube (Content Pipeline v4), Granola MCP (connected), Calendar MCP, Gmail MCP.

### Layer 2: Intelligence (The Brain)
Agent SDK runners + MCP tools reason over data. Five specialist runners planned: PostMeetingAgent, ContentAgent, OptimiserAgent, IngestAgent, SyncAgent. The custom `ai-cos-mcp` server provides shared tools (`cos_score_action`, `cos_get_preferences`, `cos_load_context`, etc.). The Preference Store (`action_outcomes` table in Postgres) enables learning from every accept/reject decision.

### Layer 3: Interface (Operating Surface)
How Aakash interacts: Claude mobile (primary conversational), digest.wiki (content digests + future action triage), Notion (structured data UI), WhatsApp (future proactive push). Claude Code is the build surface, not an end-user interface.

**See:** `docs/architecture/doc2-architecture-v0.2-enhanced.md` (full architecture spec), `docs/architecture/doc3-vision-document.md` (vision + build phases)

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

## THESIS TRACKER (Notion Sync Point)

**Database ID:** `4e55c12373c54e309c2031aa9f0c8f60`
**Data Source ID:** `3c8d1a34-e723-4fb1-be28-727777c22ec6`
**URL:** https://www.notion.so/4e55c12373c54e309c2031aa9f0c8f60

The Thesis Tracker is the **shared state** for thesis threads across all Claude surfaces. Both Claude.ai and Claude Code have Notion access, making this the sync point that closes the feedback loop.

### Schema
- **Thread Name** (title) — Name of the thesis thread
- **Status** — Active / Exploring / Parked / Archived
- **Conviction** — High / Medium / Low / TBD
- **Core Thesis** — One-liner: what is the durable value insight?
- **Key Question** — The open question that moves conviction up or down
- **Evidence For** — IDS notation: ++ and + signals
- **Evidence Against** — IDS notation: ? and ?? signals
- **Key Companies** — Companies connected to this thesis
- **Key People** — High-value people for this thread
- **Connected Buckets** — Multi-select: New Cap Tables, Deepen Existing, New Founders, Thesis Evolution
- **Discovery Source** — Claude.ai / Claude Code / Meeting / Research / X/LinkedIn / Other
- **Investment Implications** — What should Aakash DO about this thesis?
- **Date Discovered** — When the thread was first identified
- **Last Updated** — Auto-set on edit

### Sync Protocol
**When discovering a new thesis thread:**
1. Create a new page in the Thesis Tracker with Discovery Source = "Claude Code" (or "Claude.ai" from that surface)
2. Fill in at minimum: Thread Name, Status (Exploring), Core Thesis, Key Question, Discovery Source
3. Also update CONTEXT.md's thesis threads section

**When updating an existing thread:**
1. Query the Thesis Tracker for the thread by name
2. Update the relevant fields (evidence, conviction, companies, people)
3. The Last Updated timestamp auto-updates

**When reading thesis state:**
1. Query data source `3c8d1a34-e723-4fb1-be28-727777c22ec6` to get all thesis threads
2. Use this as the authoritative source for thesis-related recommendations
3. Connect thesis threads to People Scoring Model (thesis_intersection factor)

---

## CONTENT PIPELINE v4 (YouTube → more surfaces coming)

**Purpose:** Process Aakash's content consumption through an AI pipeline that extracts investing-relevant insights, connects to active thesis threads and portfolio/deal pipeline, generates rich digests (PDF + mobile-friendly HTML), and proposes concrete actions. Currently supports YouTube; designed to extend to podcasts, articles, bookmarks.

**Trigger phrases:** "process my content queue", "process my YouTube queue", "process my videos"

### Architecture
- **Part 1 — Mac Extractor** (`scripts/youtube_extractor.py` or CLI shortcut `yt`): Runs on Mac. Uses yt-dlp + youtube-transcript-api. Saves JSON to `queue/`.
- **Part 2 — Content Analysis**: Processes queue with thesis/portfolio matching, generates structured analysis, PDF digests, writes to Notion Content Digest DB, proposes actions to Actions Queue.
- **Part 3 — Mobile Review** (Claude.ai): "Review my content actions" / "review my portfolio actions" queries pending items for approve/dismiss.

**Transition:** ContentAgent (Agent SDK runner) will replace the manual analysis step. See `docs/architecture/doc2-architecture-v0.2-enhanced.md` for runner specs.

### Queue Flow
```
Mac (8:30 PM daily via launchd): youtube_extractor.py → queue/youtube_extract_*.json
Analysis: queue/ → content analysis → PDF digests → Notion → review
Post-processing: move to queue/processed/
Back-propagation (daily): Actions Queue Done → Content Digest "Actions Taken"
```

### Content Digest DB
- **Database ID:** `3fde8298-419e-4558-b95e-c3a4b5a69299`
- **Data Source ID:** `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`
- Properties: Video Title, Channel, Video URL, Upload Date, Duration, Summary, Thesis Connections, Portfolio Relevance, Key Insights, Proposed Actions, Action Status, Connected Buckets, Content Type, Relevance Score, Discovery Source, Processing Date, Batch ID
- **v3 Fields:** Topic Map, Watch These Sections, Net Newness (select), Contra Signals, Rabbit Holes, Essence Notes

### HTML Content Digest Site
- **Project:** `aicos-digests/` — Next.js 16 + TypeScript + Tailwind CSS v4
- **Architecture:** SSG. Each digest = JSON file in `src/data/{slug}.json` → rendered at `/d/{slug}` with dynamic OG tags
- **Deployment:** Live at https://digest.wiki. Push to `main` → GitHub Action → Vercel (~90s)
- **GitHub repo:** `RTinkslinger/aicos-digests` (private)
- **Pipeline integration:** `scripts/publish_digest.py` saves JSON, deploys via git push → GitHub Action

### Intelligence Architecture
The pipeline is an **AI strategist, not a keyword matcher**. Context layers:
| Layer | Source | Status |
|-------|--------|--------|
| Base | Portfolio DB (Notion) | ✅ Live |
| Depth | Deep Research Enrichment (`portfolio-research/*.md`) | ✅ Available |
| History | Previous Content Digests (net newness baseline) | ✅ Live |
| Conviction | Structured Interviews | 🔜 Planned |
| Real-time | Email/Messaging access | 🔜 Future |
| Signal | Meeting notes (Granola) | 🔜 Future |

---

## PORTFOLIO ACTIONS TRACKER

**Database ID:** `e1094b9890aa45b884f37ab46fda7661`
**Data Source ID:** `1df4858c-6629-4283-b31d-50c5e7ef885d`

The Actions Queue is the **single action sink** for ALL action types — portfolio, thesis, network, and research. Actions flow here from Content Pipeline, deep research, meetings, manual entry, and agent-generated analysis. Thesis Tracker stays as pure conviction/knowledge tracker; thesis-related actions route through Actions Queue with Thesis relation.

### Schema
- **Action** (title) — Concise action description
- **Company** (relation to Portfolio DB `4dba9b7f-e623-41a5-9cb7-2af5976280ee`) — Links to portfolio company (optional)
- **Thesis** (relation to Thesis Tracker `3c8d1a34-e723-4fb1-be28-727777c22ec6`) — Links to thesis thread (optional). An action can relate to a company, a thesis, or both.
- **Source Digest** (relation to Content Digest DB `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`) — Provenance link. Enables back-propagation: when action with Source Digest = X reaches Done, Content Digest DB entry X moves to "Actions Taken".
- **Action Type** (select): Thesis Update, Meeting/Outreach, Research, Follow-on Eval, Portfolio Check-in, Pipeline Action, Content Follow-up
- **Priority** (select): P0 - Act Now, P1 - This Week, P2 - This Month, P3 - Backlog
- **Status** (select): Proposed → Accepted → In Progress → Done / Dismissed
- **Source** (select): Content Pipeline, Agent, Manual, Meeting, Thesis Research, IDS Review
- **Assigned To** (select): Aakash, Agent, Sneha, Team
- **Created By** (select): Claude Code, Claude.ai, Manual
- **Relevance Score** (number) — 0-100
- **Reasoning** (text) — Why this action matters
- **Thesis Connection** (text) — Legacy free-text thesis link (prefer Thesis relation)
- **Source Content** (text) — Legacy free-text source reference (prefer Source Digest relation)
- **Due Date** (date)
- **Outcome** (text) — Result after completion

### Content Digest DB ↔ Actions Queue State Contract
Content Digest `Action Status` state machine:
- `Pending` → Unreviewed (set by pipeline)
- `Reviewed` → All proposed actions triaged (accepted → Actions Queue, or rejected)
- `Actions Taken` → At least one downstream action marked Done (back-propagated)
- `Skipped` → Dismissed without review / duplicate

### Action Routing Protocol
**From Content Pipeline:** Source = "Content Pipeline", Status = "Proposed", Created By = "Claude Code".
**From Deep Research:** Source = "Agent", Created By = "Claude Code".
**From Meetings/Manual:** Source = "Meeting" or "Manual", Created By = "Manual".

**Action Type Mapping:**
- Follow-up Call → Meeting/Outreach
- Intro Needed → Meeting/Outreach
- Risk Flag → Portfolio Check-in
- Follow-on Decision → Follow-on Eval
- Strategic Input → Research
- Market Intel → Thesis Update

**Priority Mapping:** High → P0, Medium → P1, Low → P2

### Current State (Session 017)
112 total actions: 76 from deep research enrichment (Session 015) + 36 from Content Pipeline v4 (Session 017). Action types: Research, Meeting/Outreach, Thesis Update, Portfolio Check-in, Content Follow-up, Pipeline Action.

---

## THESIS THREADS (Active as of March 2026)

Based on analyzed ChatGPT Deep Research sessions + Content Pipeline:

1. **Agentic AI Infrastructure** — Layer model (Model/Agent/Harness/Application). Thesis: harness layer is where durable value lives. Specific companies: Composio, Smithery.ai, Poetic (YC W25 — "Django for AI agents"). MCP ecosystem. Evidence expanded Session 017: developer tooling convergence (Cursor → Claude Code shift), CLAW stack emergence, infrastructure layer consolidation.
2. **Cybersecurity / Pen Testing** — Evolution from services to platforms. Crowdsourced → Automated → AI-augmented. Companies: Bugcrowd, HackerOne, Pentera. "Service → platform transition = venture-scale value creation."
3. **USTOL / Aviation / Deep Tech Mobility** — Ultra-short takeoff and landing. Electra Aero. Sweet spot between VTOL flexibility and CTOL range. Applications: defense, logistics, urban air mobility.
4. **SaaS Death / Agentic Replacement** (Session 016, **upgraded to High conviction Session 017**) — AI agents replacing traditional SaaS tools entirely. 4/4 independent sources converge (YC, EO, a16z, 20VC). Klarna as case study. Portfolio exposure: Unifize, CodeAnt, Highperformr need AI moat evaluation.
5. **CLAW Stack Standardization & Orchestration Moat** (Session 017) — CLAW (Compute, LLM, Agent, Workflow) stack analogous to LAMP/MEAN. Orchestration layer is where durable enterprise value lives. Key question: commoditized by hyperscalers or indie? Exploring, Medium conviction.
6. **Healthcare AI Agents** (Session 017 signal) — AI enabling personalized care pathways. Early signal, monitor for convergence.

---

## PERSISTENCE

Claude Code persistence: **CLAUDE.md** (project instructions, auto-loaded) + **CONTEXT.md** (master context, read on demand) + **auto memory** (`~/.claude/projects/.../memory/`). Historical Cowork 6-layer persistence model documented in `docs/architecture/BUILD-SYSTEM.md`.

**The Feedback Loop:** Every session that produces new understanding should sync it:
- **New thesis threads** → Write to Notion Thesis Tracker + update CONTEXT.md
- **Updated thesis conviction/evidence** → Update existing Thesis Tracker entry
- **New build state, patterns, Notion IDs** → Update CONTEXT.md + CLAUDE.md
- This ensures compound learning across all Claude surfaces.

---

## SESSION LIFECYCLE

Sessions are the atomic unit of AI CoS work. The system enforces maintenance, not the human.

**Checkpoint triggers:** "checkpoint" / "save state" → Write to `docs/session-checkpoints/SESSION-{NNN}-CHECKPOINT-{N}.md`

**Session Close Checklist (5 steps, MANDATORY):** See CLAUDE.md for the authoritative checklist. Summary:
1. Iteration log → `docs/iteration-logs/`
2. Update CONTEXT.md
3. Update CLAUDE.md
4. Thesis Tracker sync → Notion
5. Confirm completion

**Checkpoint format:**
```markdown
# Session {NNN} Checkpoint {N}
**Timestamp:** {ISO datetime}
**Session Title:** {descriptive title}

## What's Done
- {completed items, key decisions, files modified}

## What's In Progress
- {current task, where you left off}

## What's Pending
- {remaining tasks from original request}

## Key State
- **Files modified:** {list}
- **Notion changes:** {any DB writes/updates}
- **Decisions made:** {key decisions that affect future work}
- **New learnings:** {patterns, IDs, gotchas discovered}
```

---

## BUILD HISTORY

39 sessions across 5 days built the system from scratch. Key milestones:

- **Sessions 001-011:** Deep discovery — Notion DB mapping, IDS methodology decoding, 4 ChatGPT thesis sessions analyzed, system vision v1→v2→v3
- **Sessions 012-013:** Multi-surface persistence architecture, Notion Thesis Tracker, parallel deep research
- **Sessions 014-018:** Content Pipeline v1→v4 (YouTube → analysis → PDF/HTML digests → Notion → Actions Queue), notion-mastery skill, 20 portfolio companies deep-researched (76 actions)
- **Sessions 019-022:** digest.wiki built + deployed (Next.js 16, Vercel, WhatsApp-shareable), deploy pipeline solved
- **Sessions 023-028:** System Vision v3 reframe ("What's Next?"), v5→v6 artifact alignment, session lifecycle enforcement, operating rules expansion
- **Sessions 029-033:** Actions Queue architecture, Full Cycle command, Build Roadmap DB, layered persistence v6.0 milestone
- **Sessions 034-039:** Parallel development (git repo, branch lifecycle CLI, worktrees, file safety classification, subagent patterns, action_scorer.py + dedup_utils.py)
- **Session 040:** Claude Code transition — CLAUDE.md + CONTEXT.md rewritten for Claude Code + Agent SDK + MCP + cloud architecture

For per-session details: `docs/session-timeline.md` and `docs/iteration-logs/`

---

## CURRENT BUILD STATE

### What Works Today
- **Content Pipeline v4:** YouTube → Mac extractor (launchd 8:30 PM) → JSON queue → content analysis → PDF/HTML digests → Content Digest DB → Actions Queue
- **digest.wiki:** Next.js 16, live at https://digest.wiki, WhatsApp-shareable, 12+ section digests with dynamic OG tags
- **Notion as full data layer:** 8 databases with cross-references, all actively used
- **IDS methodology fully encoded** in CONTEXT.md with notation, conviction, scoring frameworks
- **Scoring models defined:** Action Scoring (7 factors), People Scoring (9 factors), `action_scorer.py` (172 lines)
- **Parallel development system:** Local git repo, `branch_lifecycle.sh` CLI, worktrees, file safety classification (🟢/🟡/🔴)
- **Deep research:** 20 Fund Priority companies researched, 76 actions generated, stored in `portfolio-research/`
- **6 active thesis threads** tracked in Notion Thesis Tracker

### What's Being Built Next
The system is transitioning from session-based development to persistent autonomous architecture. See `docs/architecture/` for full specs.

1. **Custom ai-cos-mcp server** — FastMCP Python on DO droplet. Key tools: `cos_load_context`, `cos_score_action`, `cos_get_preferences`, `cos_propose_actions`. Enables all Claude surfaces to share cross-cutting logic.
2. **Preference Store** — `action_outcomes` table in Postgres. Every accept/reject with scoring factor snapshots. Injected into reasoning sessions for calibration. The compounding mechanism.
3. **Action Frontend** — Accept/dismiss on digest.wiki pages, consolidated `/actions` route
4. **Cloud infrastructure** — DO droplet ($12/mo), Postgres, Tailscale. Sync worker: Notion ↔ Postgres with dirty flag pattern.
5. **Agent SDK runners** — 5 narrow specialists (PostMeetingAgent, ContentAgent, OptimiserAgent, IngestAgent, SyncAgent). Build order follows dependency: SyncAgent → ContentAgent → PostMeetingAgent → IngestAgent → OptimiserAgent.
6. **Content Pipeline v5** — Full portfolio coverage (200+ companies), semantic matching, multi-source (podcasts, articles, bookmarks)
7. **WhatsApp integration** — Proactive push (pre-meeting briefs, signal alerts, follow-up reminders)

---

## HOW TO USE THIS DOCUMENT

**If you're a new Claude Code session:**
1. Read this entire document FIRST before doing anything
2. Understand the anti-patterns — do NOT default to task automation
3. Check "Current Build State" for what's done and what's next
4. Read `docs/architecture/` for full technical specs when building
5. Frame every response through the action optimizer lens: "Does this help answer 'What's Next?' for Aakash?"

**If you're updating this document:**
- Update the "Last Updated" date and session number at the top
- Add new thesis threads as they're discovered
- Update "Current Build State" as things get built
- Add new Notion IDs as they're discovered
- Keep this document under control — architecture details belong in `docs/architecture/`, not here
