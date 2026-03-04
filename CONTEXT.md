# Aakash AI Chief of Staff — Master Context Document
# Last Updated: 2026-03-05 (Session 039 — Parallel Dev Phase 2-3 + Lifecycle CLI)
# This file is the SINGLE SOURCE OF TRUTH for all Claude sessions (Cowork + Claude Code)

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
2. **Thesis-building:** Content consumption (X, LinkedIn, Substack, YouTube, Apple Podcasts), rabbit holes, deep research sessions (currently ChatGPT, migrating to Claude), brainstorming

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

## THE THREE-LAYER ARCHITECTURE

### Layer 1: Observation (Always-On)
Continuously monitors all of Aakash's surfaces: WhatsApp, email, calendar, LinkedIn/X browsing, YouTube/podcast consumption, AI tool sessions (Claude, GPT, Perplexity). Communication tools are the critical observation surface. Feeds everything into the Intelligence Layer.

### Layer 2: Intelligence (The Strategist)
Maintains the living network graph. Scores every person. Connects dots across contexts. Detects patterns in Aakash's behavior. Optimizes meeting allocation. This is the core product.

### Layer 3: Action (The Plumbing)
Proactively fills gaps the strategist identifies. Drafts outreach, queues follow-ups, preps meeting context, updates Notion, coordinates with Sneha. Doesn't wait for instructions — continuously closes the gap between "what the strategist recommends" and "what's actually happening."

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
| **Actions Queue** (was Actions Queue) | `e1094b9890aa45b884f37ab46fda7661` | `1df4858c-6629-4283-b31d-50c5e7ef885d` |
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

The Thesis Tracker is the **shared state** between Claude.ai and Cowork for thesis threads. Both surfaces have Notion access, making this the sync point that closes the feedback loop.

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
- **Discovery Source** — Claude.ai / Cowork / Meeting / Research / X/LinkedIn / Other
- **Investment Implications** — What should Aakash DO about this thesis?
- **Date Discovered** — When the thread was first identified
- **Last Updated** — Auto-set on edit

### Sync Protocol
**When Claude.ai discovers a new thesis thread:**
1. Create a new page in the Thesis Tracker with Discovery Source = "Claude.ai"
2. Fill in at minimum: Thread Name, Status (Exploring), Core Thesis, Key Question, Discovery Source
3. The Cowork AI CoS skill will pick this up on next session via Notion query

**When Cowork discovers a new thesis thread:**
1. Create a new page in the Thesis Tracker with Discovery Source = "Cowork"
2. Fill in all available fields including Evidence For/Against, Key Companies/People
3. Also update CONTEXT.md's thesis threads section

**When updating an existing thread (either surface):**
1. Query the Thesis Tracker for the thread by name
2. Update the relevant fields (evidence, conviction, companies, people)
3. The Last Updated timestamp auto-updates

**When reading thesis state (either surface):**
1. Query data source `3c8d1a34-e723-4fb1-be28-727777c22ec6` to get all thesis threads
2. Use this as the authoritative source for thesis-related recommendations
3. Connect thesis threads to People Scoring Model (thesis_intersection factor)

---

## CONTENT PIPELINE v4 (YouTube → more surfaces coming)

**Purpose:** Process Aakash's content consumption through an AI pipeline that extracts investing-relevant insights, connects to active thesis threads and portfolio/deal pipeline, generates rich digests (PDF + mobile-friendly HTML), and proposes concrete actions. Currently supports YouTube; designed to extend to podcasts, articles, bookmarks.

**Trigger phrases:** "process my content queue", "process my YouTube queue", "process my videos"
**Mobile review:** "review my content actions" (Claude.ai Memory #11), "review my portfolio actions" (Memory #12)

### Architecture (v4 — Orchestrator + Parallel Subagents)
- **Part 1 — Mac Extractor** (`scripts/youtube_extractor.py` or CLI shortcut `yt`): Runs on Aakash's Mac. Uses yt-dlp + youtube-transcript-api. Saves JSON to `queue/`.
- **Part 2 — Cowork Intelligence** (`skills/youtube-content-pipeline/SKILL.md`): Orchestrator loads queue + builds shared context → dispatches parallel Task subagents (one per video, each with own full context window) → collects structured JSON results → generates PDF digests → writes to Notion → presents interactive review with PDF links + scannable summaries
- **Part 3 — Mobile Review** (Claude.ai Memory #11/#12): Query Content Digest DB or Actions Queue for Pending/Proposed items, approve/dismiss.

### v4 Improvements (Session 016)
1. **Parallel subagent architecture:** Each video gets its own Task subagent with full context window. Prevents context bloat when processing 3+ videos. Orchestrator stays lean (~30-40KB).
2. **Rich PDF digests:** Videos ≥10 min get a full PDF via `scripts/content_digest_pdf.py` (reportlab). Includes: essence notes, topic map, watch sections, contra signals, rabbit holes, proposed actions. Saved to `digests/`.
3. **Redesigned UX:** Chat review leads with PDF links and scannable 1-line summaries, not wall-of-text analysis dumps. Actions presented separately for accept/dismiss decisions.
4. **Automatic thesis tracker sync:** Thesis thread updates sync to Notion automatically during processing — not gated behind accept/dismiss. Reduces decision fatigue.
5. **Selective company loading:** Pre-scan transcripts for sector keywords before dispatching subagents. Each subagent only gets context for relevant companies (3-8 out of 20), not all 20.

### Queue Flow
```
Mac (8:30 PM daily via launchd): youtube_extractor.py <PLAYLIST_URL> --since-days 3 → queue/youtube_extract_*.json
Cowork (9:00 PM daily scheduled task): read queue/ → parallel subagent analysis → PDF digests → Notion → interactive review
Post-processing: move to queue/processed/
Back-propagation (10:00 AM daily scheduled task): Actions Queue Done → Content Digest "Actions Taken"
```

### Full Cycle Command (on-demand)
**Trigger:** "run full cycle", "full cycle", "run everything", "run all pipelines", "process everything", "catch up on everything"
**Skill:** `skills/full-cycle/SKILL.md` (v1.0)
Runs ALL pipeline tasks in dependency order with human checkpoints:
```
Step 0: Pre-flight (verify queue, Notion access, pending work)
Step 1: YouTube extraction (Mac osascript)  ⏸ confirm
Step 2: Content Pipeline (full v4 analysis)  ⏸ review actions
Step 3: Back-propagation sweep
```
DAG-based — steps declare dependencies. Self-checks against `list_scheduled_tasks` for drift. **Must be updated when new scheduled tasks are added.** Supports partial runs.

### Mac Automation
- **CLI shortcut:** `yt` (default playlist, last 3 days), `yt 7` (last 7 days), `yt <URL>` (custom playlist)
- **Launchd plist:** `scripts/com.aakash.youtube-extractor.plist` — runs daily at 8:30 PM local time (fires on wake if missed)
- **Setup:** `bash scripts/setup_youtube_cron.sh` (installs deps + launchd job + `yt` CLI)
- **Default Playlist:** `PLSAj-XU9ZUhPHrwSpZKxop1mDL8NgVPkD`
- **Filter:** Last 3 days of uploads (rolling window via `--since-days 3`)

### Content Digest DB
- **Database ID:** `3fde8298-419e-4558-b95e-c3a4b5a69299`
- **Data Source ID:** `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`
- Properties: Video Title, Channel, Video URL, Upload Date, Duration, Summary, Thesis Connections, Portfolio Relevance, Key Insights, Proposed Actions, Action Status, Connected Buckets, Content Type, Relevance Score, Discovery Source, Processing Date, Batch ID
- **v3 Fields:** Topic Map, Watch These Sections, Net Newness (select), Contra Signals, Rabbit Holes, Essence Notes

### Key Scripts
- `scripts/youtube_extractor.py` — Mac-side YouTube playlist extractor
- `scripts/content_digest_pdf.py` — Rich PDF digest generator (reportlab). Input: structured analysis dict. Output: 3-5 page branded PDF per video.

### HTML Content Digest Site (Session 019)
- **Project:** `aicos-digests/` — Next.js 16 + TypeScript + Tailwind CSS v4 app for mobile-friendly, shareable content digests
- **Why:** PDF digests aren't mobile-friendly or WhatsApp-shareable. HTML digests render perfectly on mobile with dynamic OG tags for social sharing.
- **Architecture:** Static Site Generation (SSG). Each digest = a JSON file in `src/data/{slug}.json` → rendered by shared React components at `/d/{slug}`.
- **Tech stack:** Next.js 16 App Router, TypeScript, Tailwind v4 (CSS-based `@theme inline {}` config, NOT tailwind.config.ts), Instrument Serif + DM Sans + JetBrains Mono fonts
- **Design:** Dark mode "Linear" aesthetic with thesis-coded color system (flame/cyan/amber/violet/green), reveal animations, timeline components, priority badges
- **Key files:**
  - `src/lib/types.ts` — TypeScript schema matching pipeline JSON
  - `src/lib/digests.ts` — Server-side helpers, color mapping, priority styling
  - `src/components/DigestClient.tsx` — Main client component (~400 lines, 12+ sections with IntersectionObserver)
  - `src/app/d/[slug]/page.tsx` — Dynamic route with SSG + per-digest OG metadata
  - `src/app/page.tsx` — Index listing all digests
  - `src/data/*.json` — Digest data files (same JSON the pipeline produces)
- **Deployment:** ✅ Live at https://digest.wiki (custom domain → Vercel)
- **GitHub repo:** `RTinkslinger/aicos-digests` (private)
- **Auto-deploy (single path):** Push to `main` → GitHub Action (`.github/workflows/deploy.yml`) → `vercel pull → build → deploy --prebuilt --prod` (~90s). Secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` in GitHub repo settings. From Cowork: commit locally, then osascript MCP `git push origin main` on Mac host.
- **Pipeline integration:** ✅ Wired. `scripts/publish_digest.py` saves JSON, pipeline skill Step 4b calls this after generation. Deploy via osascript git push → GitHub Action.
- **Status:** ✅ Deployed and live. Digests at `https://digest.wiki/d/{slug}`. Digest URLs stored in Content Digest DB "Digest URL" property.

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
- **Thesis** (relation to Thesis Tracker `3c8d1a34-e723-4fb1-be28-727777c22ec6`) — Links to thesis thread (NEW, optional). An action can relate to a company, a thesis, or both.
- **Source Digest** (relation to Content Digest DB `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`) — Provenance link back to originating content digest (NEW). Enables back-propagation: when any action with Source Digest = X reaches Done, Content Digest DB entry X moves to "Actions Taken".
- **Action Type** (select): Thesis Update, Meeting/Outreach, Research, Follow-on Eval, Portfolio Check-in, Pipeline Action, Content Follow-up
- **Priority** (select): P0 - Act Now, P1 - This Week, P2 - This Month, P3 - Backlog
- **Status** (select): Proposed → Accepted → In Progress → Done / Dismissed
- **Source** (select): Content Pipeline, Agent, Manual, Meeting, Thesis Research, IDS Review
- **Assigned To** (select): Aakash, Agent, Sneha, Team
- **Created By** (select): Cowork, Claude.ai, Manual
- **Relevance Score** (number) — 0-100
- **Reasoning** (text) — Why this action matters
- **Thesis Connection** (text) — Legacy free-text thesis link (kept for backward compat; prefer Thesis relation)
- **Source Content** (text) — Legacy free-text source reference (kept for backward compat; prefer Source Digest relation)
- **Due Date** (date)
- **Outcome** (text) — Result after completion

### Content Digest DB ↔ Actions Queue State Contract
Content Digest `Action Status` state machine:
- `Pending` → Unreviewed (set by pipeline)
- `Reviewed` → All proposed actions triaged (each accepted → routed to Actions Queue, or rejected). Terminal if no actions complete.
- `Actions Taken` → At least one downstream action in Actions Queue marked Done (back-propagated)
- `Skipped` → Dismissed without review / duplicate
One-way linkage: Content Digest only receives "Done" signal from downstream. Dismissals at Actions Queue level don't propagate back.

### Action Routing Protocol
**From Content Pipeline:** After Step 4 (Content Digest write), for each proposed action with portfolio relevance, create entry with Source = "Content Pipeline", Status = "Proposed", Created By = "Cowork".

**From Deep Research:** When research generates actionable items for portfolio companies, route with Source = "Agent", Created By = "Cowork".

**From Meetings/Manual:** Source = "Meeting" or "Manual", Created By = "Manual".

**Action Type Mapping (from research interviews):**
- Follow-up Call → Meeting/Outreach
- Intro Needed → Meeting/Outreach
- Risk Flag → Portfolio Check-in
- Follow-on Decision → Follow-on Eval
- Strategic Input → Research
- Market Intel → Thesis Update

**Priority Mapping:** High → P0, Medium → P1, Low → P2

### Mobile Review (Claude.ai Memory #12)
"Review my portfolio actions" → Query Actions Queue for Status = "Proposed", present by priority, approve/dismiss actions.

### Current State (Session 017)
112 total actions: 76 from deep research enrichment (Session 015, Status = "Proposed") + 36 from Content Pipeline v4 second live run (Session 017, Status = "Accepted"). Session 017 actions: 3 P0, 17 P1, 14 P2, 2 P3. Action types: Research, Meeting/Outreach, Thesis Update, Portfolio Check-in, Content Follow-up, Pipeline Action. Assigned To: mix of Aakash (meetings/outreach) and Agent (research/monitoring).

---

## THESIS THREADS (Active as of March 2026)

Based on analyzed ChatGPT Deep Research sessions + Content Pipeline:

1. **Agentic AI Infrastructure** — Layer model (Model/Agent/Harness/Application). Thesis: harness layer is where durable value lives. Specific companies: Composio, Smithery.ai, Poetic (YC W25 — "Django for AI agents"). MCP ecosystem. Evidence expanded Session 017: developer tooling convergence (Cursor → Claude Code shift), CLAW stack emergence, infrastructure layer consolidation.
2. **Cybersecurity / Pen Testing** — Evolution from services to platforms. Crowdsourced → Automated → AI-augmented. Companies: Bugcrowd, HackerOne, Pentera. "Service → platform transition = venture-scale value creation."
3. **USTOL / Aviation / Deep Tech Mobility** — Ultra-short takeoff and landing. Electra Aero. Sweet spot between VTOL flexibility and CTOL range. Applications: defense, logistics, urban air mobility.
4. **SaaS Death / Agentic Replacement** (Session 016, **upgraded to High conviction Session 017**) — AI agents replacing traditional SaaS tools entirely, not just augmenting them. 4/4 independent sources converge (YC, EO, a16z, 20VC). Klarna as case study. Portfolio exposure: Unifize, CodeAnt, Highperformr need AI moat evaluation. Po-Shen Loh's math education approach validates individual-centric AI replacing institutional SaaS. Ben Horowitz: "10x bigger" framing = total SaaS rebuild, not incremental.
5. **CLAW Stack Standardization & Orchestration Moat** (Session 017, Content Pipeline) — Emerging thesis: CLAW (Compute, LLM, Agent, Workflow) stack as analogous to LAMP/MEAN stacks. Orchestration layer (not individual agents) is where durable enterprise value lives. Evidence: Jerry Murdock's CLAW framework, Poetic's harness layer proof, Composio/Smithery.ai positioning. Key question: will orchestration be commoditized by hyperscalers or remain indie? Exploring, Medium conviction.
6. **Healthcare AI Agents** (Session 017 signal) — Po-Shen Loh's "education for one" thesis generalizes to healthcare. AI enabling personalized care pathways. Early signal, not yet a full thread — monitor for convergence with other sources.

---

## CURRENT BUILD STATE

### What Exists Today
- 24 sessions of deep understanding documented in iteration logs
- System vision v3 document (action optimizer answering "What's Next?", not just network strategist / meeting allocation). Supersedes v2. File: `docs/aakash-ai-cos-system-vision-v3.md`
- All Notion DBs mapped with schemas and IDs
- IDS methodology fully decoded
- 4 ChatGPT thesis sessions analyzed
- **Multi-surface persistence architecture (Session 012):**
  - **Layer 1: Claude.ai Memory** — 16 entries (v6, updated Session 033) covering identity, vision, buckets, IDS, people, style, build architecture, feedback loop, Notion write-through, deep research protocol, content pipeline review, portfolio actions review, action scoring model, Notion skill semantic trigger, layered persistence architecture, Cowork operating rules. Persists across ALL Claude.ai conversations (web, mobile, desktop). File: `docs/claude-memory-entries-v6.md`
  - **Layer 2: AI CoS Cowork Skill v6** — Action optimizer framing, Action Scoring Model, full action space, Cowork Operating Ref, 8-step close checklist, parallel development rules. File: `skills/ai-cos-v6.1.0.skill` (packaged), `skills/ai-cos-v6-skill.md` (source)
  - **Layer 3: CLAUDE.md** — Project-level context for Claude Code sessions (already existed)
  - **Layer 0: Cowork User Preferences** — Enhanced preference string recommended
  - **Feedback loop defined:** Every session updates CONTEXT.md → skill rebuilt periodically → Memory entries refreshed monthly
  - Full strategy documented in `docs/persistence-strategy.md`
  - **Notion Thesis Tracker (Session 013):** Database `3c8d1a34-e723-4fb1-be28-727777c22ec6` — shared state for thesis threads between Claude.ai and Cowork. Seeded with 3 active thesis threads. Sync protocol defined in CONTEXT.md. Closes the Claude.ai → Notion → Cowork feedback loop.
  - **Notion Mastery Skill (Session 018, updated 032 → v1.2.0):** Universal cross-surface reference for all Notion operations. Located at `.skills/skills/notion-mastery/SKILL.md` in the workspace AND installed as Cowork auto-loaded skill. Covers tool detection (Enhanced Connector vs Raw API, surface-agnostic UUID patterns), property formatting, 8 database schemas, `view://UUID` bulk-read pattern (session 032 discovery), 6 recipes (including Build Roadmap), API limits, 15+ gotchas. Semantic pattern-based description triggers on tool usage patterns, not keywords. Load this skill before any Notion CRUD operations on any surface.
  - **Build Roadmap DB (Session 031, extended 034):** Data source `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` (DB: `3446c7df9bfc43dea410f17af4d621e0`). Self-contained product roadmap for AI CoS build items — fully separate from Actions Queue (no external relations). 16 properties: Status (7-state kanban with emojis), Build Layer, Epic, Priority, T-Shirt Size, Perceived Impact, Dependencies (self-relation), Source, Discovery Session, Technical Notes, **Parallel Safety** (🟢/🟡/🔴), **Assigned To**, **Branch**, **Task Breakdown** + auto timestamps. Insights-led kanban: 💡 Insight → 📋 Backlog → 🎯 Planned → 🔨 In Progress → 🧪 Testing → ✅ Shipped → 🚫 Won't Do. 22 items classified by parallel safety (10🟢, 7🟡, 5🔴). Optimized read/write recipes in CLAUDE.md. Review purely on-demand ("review my build roadmap").
  - **Parallel Deep Research (Session 013):** "Research deep and wide" trigger phrase works across all three surfaces with surface-appropriate engines:
    - **Claude Code:** `parallel-cli` via `parallel-agent-skills` plugin (CLI-based, subagent pattern)
    - **Cowork:** `parallel-deep-research` skill using Parallel MCP tools (`createDeepResearch` → `getStatus` → `getResultMarkdown`)
    - **Claude.ai:** Memory #10 drives 6-10 parallel `WebSearch` calls across angles, manual synthesis
    - All three surfaces end with thesis connection check + Thesis Tracker sync offer
  - **YouTube Content Pipeline (Session 014):** Two-part architecture for processing YouTube content consumption:
    - Mac extractor (`scripts/youtube_extractor.py`) → JSON queue → Cowork intelligence pipeline → Content Digest DB in Notion
    - Content Digest DB: `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` — stores AI-analyzed video entries with thesis/portfolio connections and action tracking
    - Scheduled task (`process-youtube-queue`) runs daily at 9 PM; on-demand via "process my YouTube queue"
    - Cross-references Thesis Tracker, Companies DB, Portfolio DB for every video
    - Proposes concrete actions: thesis updates, meeting suggestions, research triggers, outreach
    - This is the first implementation of "Process My Discoveries" capability (YouTube surface)
  - **Actions Queue + Deep Research Enrichment (Session 015):**
    - Actions Queue DB: `1df4858c-6629-4283-b31d-50c5e7ef885d` — structured kanban for all portfolio actions (Proposed → Accepted → In Progress → Done/Dismissed)
    - Deep research enrichment on all 20 Fund Priority companies via Parallel AI (`createDeepResearch`)
    - Research files stored in `portfolio-research/` (11-18KB each, covering funding, traction, competitive landscape, risks)
    - Summary spreadsheet: `portfolio-research-summary.xlsx` (20 companies × 15 columns, sorted by Money In)
    - Structured interview agent generated 76 actionable items across 20 companies
    - All 76 actions written to Actions Queue in Notion with proper Company relations
    - Mobile review via Claude.ai Memory #12: "review my portfolio actions" queries Proposed items
  - **Content Pipeline v4 + PDF Digests (Session 016):**
    - First live run processed 3 videos (Jenny Wen, Klarna CEO, Bret Taylor) → 3 Content Digest DB entries + 8 portfolio actions + 1 new thesis thread
    - Portfolio actions review: 6 accepted, 1 dismissed (Sierra AI — out of strike zone for both DeVC and Z47), 1 thesis research accepted
    - New thesis thread created: "SaaS Death / Agentic Replacement" — synced to Thesis Tracker with investment implications
    - **Content Digest DB v3 fields added:** Topic Map, Watch These Sections, Net Newness (select), Contra Signals, Rabbit Holes, Essence Notes
    - **PDF digest generator built:** `scripts/content_digest_pdf.py` (reportlab) — generates 3-5 page branded PDFs per video with essence notes, topic maps, watch sections, contra signals, rabbit holes, proposed actions. Prototype tested with Bret Taylor video.
    - **SKILL.md upgraded to v4:** Orchestrator + parallel subagent architecture. Each video gets its own Task subagent with full context window. Prevents context bloat. Redesigned UX leads with PDF links + scannable summaries. Automatic thesis tracker sync (not gated behind accept/dismiss). Selective company loading via pre-scan.
    - **Key learning:** Sierra AI out of strike zone for both funds — this type of "not relevant to us" signal is valuable for improving future action filtering
  - **Notion Mastery Skill + PDF v5 (Session 018):**
    - **`notion-mastery` skill created:** Universal cross-surface reference for all Notion operations (`skills/notion-mastery/SKILL.md`). Works on Cowork, Claude.ai, and Claude Code. Covers: tool detection (Enhanced Connector vs Raw API), property formatting (expanded dates, multi-select JSON arrays, checkbox strings, relation URLs, native numbers), all 7 key database IDs with collection:// URLs, 5 common recipes (Content Digest, Portfolio Action, Thesis Thread Update, Raw API Query, Search & Cross-Reference), API limits/guardrails, 15 gotchas discovered through live testing.
    - **Key technical findings:**
      - Enhanced Connector has broader page access than Raw API (pages returning 404 on raw API work on enhanced connector)
      - Raw API `API-query-data-source` consistently fails with "Invalid request URL" — use enhanced connector views or search instead
      - Raw API cannot trash pages created via enhanced connector (404 error)
      - Tool UUIDs are session/surface-specific — skill uses suffix-based detection pattern, not hardcoded UUIDs
    - **Live-tested all operations:** Created test page in Actions Queue, verified property round-trip (text, select, number, expanded dates), confirmed update works, documented access gap pattern
    - **PDF digest template v5 finalized:** `scripts/content_digest_pdf.py` redesigned with clean production layout. This is the production template for all future PDF digests.
    - **AI CoS Command Library (Phase 3):** Notion reference page (`31729bcc-b6fc-8193-9974-ed2e07c0b013`) documenting all AI CoS commands across surfaces. 7 sections: Content Pipeline (5 commands), Portfolio Actions (2), Content Actions Review (1), Deep Research (3 surfaces), Thesis Management (3 automatic), Notion Operations (1), Planned Capabilities (5). Plus "Which Surface For What?" quick reference and System Architecture overview. Living document — update as new capabilities ship.
    - **All 3 phases of Session 018 complete.**
  - **HTML Content Digest Site (Session 019):**
    - Replaced PDF-only content digests with mobile-friendly, shareable HTML digests hosted on Vercel
    - Next.js 16 + TypeScript + Tailwind v4 app at `aicos-digests/` — dark mode "Linear" aesthetic with thesis-coded color system
    - Static Site Generation: each digest = JSON file → pre-rendered at `/d/{slug}` with dynamic OG tags for WhatsApp/social sharing
    - 12+ rendered sections: core arguments, key data, frameworks, quotes, predictions, watch sections, contra signals, portfolio impact, rabbit holes, actions (priority-grouped), thesis impact, net assessment
    - Design evolved significantly from Claude.ai HTML prototype — professional, scan-optimized, mobile-first
    - First digest (Cursor/Insight Partners) built and build-verified locally
    - **Deployment complete:** Live at https://aicos-digests.vercel.app/ — GitHub (`RTinkslinger/aicos-digests`) → Vercel auto-deploy on push
    - **Phase 2 planned:** Pipeline integration — `content_digest_pdf.py` also saves JSON to `aicos-digests/src/data/`, git push triggers auto-deploy

### What to Build Next (Cowork Tier — 10x)
1. ~~**🔬 TEST: Content Pipeline v4 live run**~~ ✅ **VALIDATED (Session 017)** — Second live run processed 4 videos (Poetic/YC, Po-Shen Loh/EO, Ben & Marc/a16z, Jerry Murdock/20VC). Parallel subagents work correctly, PDFs generate properly, thesis sync automatic. 36 actions generated, user approved all. New thesis thread (CLAW Stack) emerged organically. Pipeline is production-ready.
2. **📱 Content consumption <10 min:** Design handling for short-form content (tweets, LinkedIn posts, short videos). Currently only ≥10 min videos get PDF digests. Need a lighter format.
3. **🔧 More content surfaces:** Screengrab/bookmark/LinkedIn connection processing with enrichment and scoring. YouTube is done — expand to podcasts, articles, bookmarks.
4. **"Optimize My Meetings" capability** — The first real strategist output. Given a planning window + geography, score and rank Aakash's universe, produce optimized meeting slate.
5. **"Who Am I Underweighting?" analysis** — Gap detection across portfolio, pipeline, collective, thesis.
6. **🔧 Portfolio Company Interviews** — Structured interviews with Aakash about each Fund Priority company to add conviction/gut-feel context layer.
7. The plumbing (meeting prep, IDS capture, follow-up tracking) — SERVING the strategist, not replacing it.

### What to Build (Custom Agent SDK — 100x+)
- Three-agent architecture: Intelligence Engine (brain), Signal Processor (eyes), Operating Interface (WhatsApp voice)
- Network Graph as persistent data store
- WhatsApp integration (primary interface)
- M365 integration (email + calendar)
- Authenticated browser sessions (LinkedIn, X)
- The People Scoring Model as a continuously running optimization engine

---

## PERSISTENCE ARCHITECTURE

The AI CoS maintains context across three surfaces via a layered persistence model:

**Layer 1 — Claude.ai Memory (ambient awareness):** 16 memory entries in Claude.ai Settings → Memory (500-char limit per entry). These persist across ALL Claude conversations — web, mobile, desktop. Entries: #1 Identity & Roles, #2 AI CoS Vision ("action optimizer answering 'What's Next?'"), #3 Four Priority Buckets (action allocation), #4 IDS Methodology, #5 Key People & Tools, #6 Working Style & Thesis Threads, #7 AI CoS Build Architecture (3-layer arch, build order, current state, digest.wiki), #8 Feedback Loop (flag AI CoS relevance + concrete actions for action queue), #9 New Thesis → Notion write-through, #10 Deep Research Protocol, #11 Content Pipeline Review, #12 Portfolio Actions Review, #13 Action Scoring Model (split from #2 due to 500-char limit), #14 Notion Skill Semantic Trigger (load notion-mastery before any Notion tool call, even when prompt doesn't mention "Notion"), #15 Layered Persistence Architecture (6 layers, triage principle, audit cadence, 7-step close checklist), #16 Cowork Operating Rules (sandbox constraints, deploy path, Notion property formatting, skill packaging). Source of truth: `docs/claude-memory-entries-v6.md`. Refresh monthly as thesis threads and priorities evolve.

**Layer 2 — AI CoS Cowork Skill v6.0.0 (deep activation):** Triggers aggressively on any investing/network/meeting/action keyword. "Action optimizer answering 'What's Next?'", Action Scoring Model, full action space (not just meetings). Contains inline essential context as fallback + dynamically locates CONTEXT.md when the project folder is mounted. **v6.0.0 (milestone):** Cowork Operating Ref block (sandbox rules, deploy architecture, Notion property formatting, skill packaging — repeated-mistake prevention), 7-step close checklist, layered persistence architecture, self-documenting audit mechanism. Rebuild the .skill file when CONTEXT.md has had significant updates. Source of truth: `skills/ai-cos-v6-skill.md`, packaged as `ai-cos-v6.0.0.skill`. **For any Notion operations, load the `notion-mastery` skill** — it has the complete cross-surface reference for tool detection, property formatting, recipes, and gotchas.

**Layer 3 — CLAUDE.md (code context):** Project-level file for Claude Code sessions. Quick orientation + Notion IDs + anti-patterns.

**Layer 0a — Cowork Global Instructions (operational directives):** Applied to ALL Cowork sessions before any skill loads. Contains: session lifecycle enforcement (checkpoint + close checklist triggers), project context pointer (CONTEXT.md location, skill loading rules), operating principles (mobile-first, IDS, every interaction = learning session). This fires before the ai-cos skill, so session hygiene works even in non-AI-CoS sessions. Source of truth: `docs/cowork-global-instructions-v6.md`. Location: Claude Desktop → Settings → Cowork → Global Instructions.

**Layer 0b — Cowork User Preferences (identity baseline):** Short preference blurb shown in every Cowork session. v5 framing: "action optimizer that answers 'What's Next?'", expanded trigger words (action triage, what's next, prioritize, content pipeline, portfolio actions). Source of truth: `docs/claude-user-preferences-v6.md`.

**Notion Thesis Tracker (sync point):** Data source `3c8d1a34-e723-4fb1-be28-727777c22ec6`. Both Claude.ai and Cowork have Notion access. When either surface discovers a new thesis thread, it writes to the Thesis Tracker. When either surface needs thesis context, it reads from the Thesis Tracker. This closes the feedback loop that previously dead-ended in Claude.ai Memory.

**The Feedback Loop:** Every Claude interaction is a potential input. At session end, ask: did this produce learnings? New thesis threads → Thesis Tracker (Notion) + CONTEXT.md. New patterns → CONTEXT.md. New capabilities needed → CONTEXT.md. Build state changes → CONTEXT.md. The document compounds. Monthly: refresh Claude.ai Memory entries. Periodically: rebuild skill from updated CONTEXT.md.

**The Principle:** CONTEXT.md is the living brain. Claude.ai Memory is the ambient awareness. The skill is the activation mechanism. Every session that touches any of these makes the next session smarter.

### Layered Persistence Coverage Map (audit every 5 sessions)

**Triage principle:** If an instruction is violated 2+ times across sessions, upgrade its layer count. Target: CRITICAL instructions at 3+ layers, IMPORTANT at 2+, STANDARD at 1+.

| Instruction Set | Criticality | Layer 0a | Layer 0b | Layer 1 (Memory) | Layer 2 (Skill) | Layer 3 (CLAUDE.md) | CONTEXT.md | Coverage |
|----------------|-------------|----------|----------|-------------------|-----------------|---------------------|------------|----------|
| Session close checklist (7-step) | CRITICAL | ✅ | — | ✅ (#15) | ✅ | ✅ | ✅ | 5/6 |
| Notion skill auto-load | CRITICAL | ✅ | — | ✅ (#14) | ✅ | ✅ | ✅ | 5/6 |
| Action optimizer framing | CRITICAL | — | ✅ | ✅ (#2) | ✅ | ✅ | ✅ | 5/6 |
| Feedback loop (end-of-task) | CRITICAL | ✅ | ✅ | ✅ (#8) | ✅ | — | ✅ | 5/6 |
| Cowork sandbox rules | CRITICAL | — | — | ✅ (#16) | ✅ | ✅ | — | 3/6 |
| Deploy architecture | CRITICAL | — | — | ✅ (#16) | ✅ | ✅ | — | 3/6 |
| Notion property formatting | CRITICAL | — | — | ✅ (#16) | ✅ | ✅ | — | 3/6 |
| Skill packaging rules | IMPORTANT | — | — | ✅ (#16) | ✅ | ✅ | — | 3/6 |
| Notion bulk-read (view://UUID) | IMPORTANT | — | — | — | ✅ | ✅ | — | 2/6 |
| IDS methodology | IMPORTANT | — | — | ✅ (#4) | ✅ | — | ✅ | 3/6 |
| Four priority buckets | IMPORTANT | — | — | ✅ (#3) | ✅ | — | ✅ | 3/6 |
| Action Scoring Model | IMPORTANT | — | — | ✅ (#13) | ✅ | ✅ | ✅ | 4/6 |
| Thesis sync protocol | IMPORTANT | — | — | ✅ (#9) | ✅ | — | ✅ | 3/6 |
| Content Pipeline review | STANDARD | — | — | ✅ (#11) | ✅ | ✅ | ✅ | 4/6 |
| Portfolio actions review | STANDARD | — | — | ✅ (#12) | ✅ | ✅ | ✅ | 4/6 |
| Layered persistence meta | META | — | — | ✅ (#15) | — | ✅ | ✅ | 3/6 |

**Last audit:** Session 033. **Next audit due:** Session 038.
**Source of truth for coverage map:** `docs/layered-persistence-coverage.md` (detailed) + this table (summary).

---

## SESSION LIFECYCLE MANAGEMENT

Sessions are the atomic unit of AI CoS work. Every session must maintain state hygiene — the system enforces this, not the human.

### Trigger Words
- **"checkpoint"** / **"save state"** / **"save progress"** → Write a session checkpoint (mid-session state save)
- **"close session"** / **"end session"** / **"wrap up"** / **"session done"** → Execute the Session Close Checklist

### Session Checkpoints (mid-session state saves)
Use at ~50% and ~75% context usage, or whenever significant progress has been made that would be painful to reconstruct. Aakash says "checkpoint" and the AI CoS writes a pickup file.

**File:** `docs/session-checkpoints/SESSION-{NNN}-CHECKPOINT-{N}.md`
**Format:**
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

**Rules:**
- Checkpoints are fast — aim for <60 seconds to write
- Don't re-read everything; capture what's in working memory
- Each session can have multiple checkpoints (numbered sequentially)
- Checkpoints are disposable — iteration logs are the permanent record

### Session Close Checklist (MANDATORY — never skip, 7 steps)
When Aakash says "close session" or equivalent, execute ALL steps in order:

**Step 1 — Write Iteration Log**
- File: `docs/iteration-logs/{date}-session-{NNN}-{slug}.md`
- Include: what was done, key decisions, files created/modified, learnings, open items
- Reference any checkpoint files created during the session
- **Step 1b — Build Roadmap Insights:** If this session produced build insights, capability gaps, or bug patterns → create entries in Build Roadmap DB (data source `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f`) with Status = `💡 Insight`, Source = `Session Insight`, Discovery Session = current session number.

**Step 2 — Update CONTEXT.md**
- Add session entry to DETAILED ITERATION LOGS section
- Update any changed: build state, thesis threads, Notion IDs, new capabilities, framing changes
- Update "Last Updated" line at top of file

**Step 3 — Update CLAUDE.md**
- Update "Last Session" reference to current session number + title
- Update any new capabilities, IDs, or cross-surface changes

**Step 4 — Thesis Tracker Sync**
- If any new thesis threads discovered → Write to Notion Thesis Tracker
- If any thesis conviction/evidence changed → Update existing Thesis Tracker entry
- If no thesis changes → Skip (note "No thesis changes" in iteration log)

**Step 5 — Update Artifacts Index**
- Update `docs/v6-artifacts-index.md` with any version bumps, new artifacts, or changed session references
- This is the single cross-surface version tracker — prevents artifact drift

**Step 6 — Package Updated Skills**
- If ANY skill was modified this session: (a) Ensure frontmatter has `version` field and `description` ≤1024 chars. (b) Package as ZIP: `mkdir -p /tmp/pkg/{name} && cp source.md /tmp/pkg/{name}/SKILL.md && cd /tmp/pkg && zip -r /tmp/{name}.skill {name}/` (c) Copy ZIP to workspace folder. (d) Present via `present_files`. **`.skill` = ZIP archive, NEVER plain text.**
- If no skills modified → Skip

**Step 7 — Confirm Completion**
- State: "Session {NNN} closed. Iteration log ✅, CONTEXT.md ✅, CLAUDE.md ✅, Thesis sync ✅, Artifacts index ✅, Skills packaged ✅ (or N/A)"
- If any step couldn't be completed, state why

**Known Gap:** Sessions 012-016 and 018-022 have no iteration log files (only CONTEXT.md entries). Session 023 skipped CONTEXT.md v5 framing update. This checklist exists to prevent future gaps.

### Persistence Audit (every 5 sessions — self-documenting)
**Next audit due:** Session 038.
**Trigger:** At the START of sessions 038, 043, 048, ... (every 5th from 033), before doing any user work, run the persistence audit.
**Protocol:**
1. Read iteration logs from the last 5 sessions (`docs/iteration-logs/`)
2. Grep for patterns: "BROKEN", "failed", "wrong method", "trial-and-error", property formatting mistakes, sandbox violations, "should have", "forgot to"
3. For each pattern found 2+ times: check `docs/layered-persistence-coverage.md`, upgrade layer count if below target
4. Update the coverage map (both detailed file + CONTEXT.md summary table)
5. If new Memory entries needed: update `docs/claude-memory-entries-v6.md` + flag for user to paste into Claude.ai
6. If ai-cos skill changed: bump version + package .skill
7. Update "Next audit due" line in this section and in the coverage map

---

## DETAILED ITERATION LOGS

For full history of how we got here, see:
- `/docs/iteration-logs/2026-03-01-session-007-008-009-ids-training-and-cross-reference.md`
- `/docs/iteration-logs/2026-03-01-session-010-workflow-interview-and-thesis-building.md`
- `/docs/iteration-logs/2026-03-01-session-011-chatgpt-thesis-analysis.md`
- `/docs/persistence-strategy.md` (Session 012 — multi-surface persistence architecture)
- Session 013 — Notion Thesis Tracker creation + sync architecture + parallel deep research skill (3-surface parity)
- Session 014 — YouTube Content Pipeline (Mac extractor + Cowork intelligence pipeline + Content Digest DB + scheduled task)
- Session 015 — Actions Queue + Deep Research Enrichment (20 Fund Priority companies researched, 76 actions generated, Actions Queue DB created with kanban flow) + Content Pipeline v2 redesign (deep context profiles, semantic matching, contextual action generation)
- Session 016 — Content Pipeline v4: first live run (3 videos → 3 digests, 8 actions, 1 thesis thread), PDF digest generator (`content_digest_pdf.py`), subagent architecture (orchestrator + parallel Task per video), v3 Content Digest DB fields, redesigned review UX (PDF links + scannable summaries), automatic thesis tracker sync, Sierra AI out-of-strike-zone learning
- Session 017 — Content Pipeline v4 second live run: 4 videos (Poetic/YC, Po-Shen Loh/EO, Ben & Marc/a16z, Jerry Murdock/20VC) → 4 Content Digest entries + 4 PDF digests + 36 portfolio actions (all Accepted: 3 P0, 17 P1, 14 P2, 2 P3). New thesis thread: CLAW Stack Standardization & Orchestration Moat (Exploring, Medium). SaaS Death conviction upgraded Medium → High (4/4 source convergence). Agentic AI Infrastructure evidence expanded. Notion multi_select workaround discovered (create-pages can't handle multiple values; use update-page for single-value adds). Pipeline validated as production-ready.
- Session 018 — Notion Mastery Skill: universal cross-surface Notion operations reference (Cowork + Claude.ai + Claude Code). PDF digest v5 template finalized. Live-tested Enhanced Connector vs Raw API — documented access gaps, property formatting, 15 gotchas. AI CoS Command Library created in Notion (full reference page: all commands × surfaces × statuses). AI CoS Skill v4 packaged. All 3 phases complete.
- Session 019 — HTML Content Digest Site: Replaced PDF-only digests with mobile-friendly HTML via Next.js 16 + TypeScript + Tailwind v4 app (`aicos-digests/`). Dark mode "Linear" aesthetic with thesis-coded color system (flame/cyan/amber/violet/green), 12+ sections, IntersectionObserver reveal animations, dynamic OG metadata for WhatsApp sharing. SSG architecture: JSON data → pre-rendered pages at `/d/{slug}`. First digest (Cursor/Insight Partners) built. Tailwind v4 uses CSS-based `@theme inline {}` config (not JS). Build verified. Deployment pending GitHub MCP connection → Vercel auto-deploy. Phase 2: pipeline integration to auto-publish JSON + git push.
- Session 020 — Vercel Auto-Deploy + Phase 2 Pipeline Wiring: Diagnosed broken Vercel GitHub webhook (known Vercel bug — no webhook created in repo despite connection). Tried deploy hooks (failed), then built GitHub Action (`.github/workflows/deploy.yml`) using Vercel CLI (checkout → build → deploy with token). Confirmed working (~90s deploys). Created `scripts/publish_digest.py` with dual-path deploy: git push → GitHub Action auto-deploy, fallback `npx vercel --prod` for Cowork sandbox. Fixed DigestClient.tsx Numbers That Matter section bug. Pipeline skill Step 4b wired. GitHub secrets configured: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`. All MD files updated. Site live at https://aicos-digests.vercel.app/.
- Session 021 — Bulk Digest Publishing: Audited Content Digest DB (10 entries, 7 unique titles) against published HTML digests (1: cursor-is-obsolete). Generated 6 missing digest JSONs via Python script parsing Notion page data into DigestData TypeScript schema. Digests: ben-marc-10x-bigger (a16z), nuclear-energy-renaissance (Real Engineering), startup-outsmarted-big-ai-labs (YC/Poetic), agi-po-shen-loh (EO/CMU), india-saas-50b-2030 (SaaS Podcast), design-process-dead-jenny-wen (Lenny's Podcast). All committed to `aicos-digests/src/data/`. Pushed via Mac terminal.
- Session 022 — Deploy Auto-Push Solved: Exhaustive research on Vercel auto-deploy from Cowork sandbox. Tested 8 approaches. **Key finding:** Cowork sandbox blocks ALL outbound network (curl, git, npm, WebFetch to api.github.com/api.vercel.com all fail). **Solution:** `osascript` MCP tool (Control your Mac) runs shell commands on Mac host, bypassing sandbox entirely. Proven e2e: local commit → osascript `git push` → GitHub Action → Vercel production in ~90s. Zero manual intervention. Gotcha: invalid JSON in `src/data/` breaks Next.js SSG — only commit valid digest JSONs. Artifacts: `DEPLOY-PLAN.md` (research + solution), `scripts/auto_push.sh` + plist (launchd fallback). Updated `publish_digest.py` docstring with deploy architecture.
- Session 023 — System Vision v3 Reframe: Core reframe from "Who should I meet next?" (network strategist) to "What's Next?" (action optimizer). Full action space: Stakeholder Space (companies + network) × Action Space (stakeholder + intelligence actions). Action Scoring Model subsumes People Scoring Model. Build order: Content Pipeline → Action Frontend → Knowledge Store → Multi-Surface → Meeting Optimizer → Always-On. Artifacts: `docs/aakash-ai-cos-system-vision-v3.md`, `skills/ai-cos-v5-skill.md` (196 lines), CLAUDE.md updated to v5. Session 023 pickup note at `docs/SESSION-023-PICKUP.md`.
- Session 024 — v5 Alignment Audit: Discovered packaged Cowork skill was still v4 (169 lines) not v5 (196 lines). Packaged `skills/ai-cos-v5.skill` — installed in Claude Desktop. Audited Claude.ai memories: 4 entries updated, #13 added (Action Scoring Model, split from #2 due to 500-char limit) → 13 total entries. Created `docs/claude-user-preferences-v5.md`, rewrote `docs/claude-memory-entries-v5.md` to match exact live state. Created `docs/v5-artifacts-index.md` as single reference hub with v-bump checklist. Updated CONTEXT.md to v5 framing. All three surfaces now aligned on "What's Next?" action optimizer framing.
- Session 025 — Session Lifecycle Management: Built system-enforced session maintenance. Three capabilities: (1) Mid-session checkpoints via "checkpoint"/"save state" trigger → `docs/session-checkpoints/` pickup files, (2) Mandatory 5-step session close checklist via "close session"/"wrap up" trigger → iteration log + CONTEXT.md + CLAUDE.md + thesis sync + confirm, (3) Trigger words added to ai-cos skill description for auto-loading. Skill updated to v5b (212 lines). Meta-learning: maintenance that depends on the human remembering will be inconsistent; system-enforced maintenance via trigger words and checklists is reliable.
- Session 026 — Cowork Global Instructions: Discovered empty Global Instructions field in Claude Desktop → Settings → Cowork. Created `docs/cowork-global-instructions-v1.md` with session hygiene triggers (checkpoint + close checklist), project context pointers, and operating principles. Added as Layer 0a in persistence architecture (Layer 0 split: 0a = operational directives via Global Instructions, 0b = identity baseline via User Preferences). Pasted and live.
- Session 027 — Deploy Pipeline Fix & Schema Drift Root-Cause: Fixed dead Vercel digest links — 3 root causes: uncommitted files, missing GitHub webhook, expired VERCEL_TOKEN. Root-caused schema drift between pipeline skill template and TypeScript types. Two-pronged fix: aligned skill template + expanded normalization layer (7 normalizations) as defense-in-depth. All 12 digests live at HTTP 200. Commits: `d01ba1f`, `566088c`.
- Session 028 — Operating Rules Expansion + digest.wiki: (1) Mined ALL 27 sessions via sub-agents → expanded CLAUDE.md operating rules from 8 sandbox-only → 35 rules across 4 categories (Sandbox, Notion Ops, Schema Integrity, Skill Management). Elevated core principle: LLM pipelines need runtime normalization. (2) Consolidated deploy path — deleted duplicate webhook, single GitHub Action only. (3) File compaction — DEPLOY-PLAN.md 236→26. (4) digest.wiki custom domain integration — verified, added Digest URL property to Content Digest DB, populated all 15 Notion pages, updated CLAUDE.md + CONTEXT.md references.
- Session 029 — Actions Queue Architecture + Content Digest Hygiene: Renamed "Portfolio Actions Tracker" → "Actions Queue" (single sink for ALL action types). Added Thesis relation (→ Thesis Tracker) + Source Digest relation (→ Content Digest DB) to Actions Queue schema. Defined state contract: Pending → Reviewed → Actions Taken (back-propagated). Updated Content Pipeline skill Steps 2d, 5a, 5b. Deduplicated 3 Content Digest DB entries. All 6 artifacts synced.
- Session 030 — Back-propagation/Dedup Verification + Full Cycle Command: (1) Hardened back-propagation sweep (5 fixes: concrete query method, Source Digest relation parsing, idempotency guard, pagination, condensed results fallback). (2) Hardened dedup guard (5 fixes: URL normalization across 4 YouTube formats, notion-fetch primary method, property updates on blank dupes, multi-match handling, cleaner outcomes). (3) Built Full Cycle on-demand meta-orchestrator (`skills/full-cycle/SKILL.md` v1.0) — DAG-based pipeline: Pre-flight → YouTube extraction ⏸ → Content Pipeline ⏸ → Back-propagation sweep. Self-evolving: Pipeline Registry + self-check against `list_scheduled_tasks` for drift. Supports partial runs.
- Session 031 — Build Roadmap DB + Skill Packaging Rules: (1) Designed Build Roadmap plan (`docs/build-roadmap-plan.md`) — separate DB, no external relations, insights-led kanban, 12-property schema. (2) Created Build Roadmap DB in Notion (data source `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f`). (3) Seeded 16 initial backlog items (1 Shipped, 14 Backlog, 1 Insight). (4) Added optimized read/write recipes to CLAUDE.md — no trial-and-error for future sessions. (5) Updated notion-mastery skill with Build Roadmap recipe. (6) Updated AI CoS skill with Build Roadmap triggers (request type H). (7) Permanently documented skill packaging rules in CLAUDE.md § D: .skill = ZIP archive, frontmatter requires version, description ≤1024 chars, exact packaging recipe. (8) Added Step 5 "Package updated skills" to session close checklist. (9) Captured first Build Roadmap insight: "Automated skill packaging validation". Gotchas: dual self-relation via API → 500 (use one-way + UI toggle); .skill plain text → "invalid zip file"; description >1024 → rejected.
- Session 032 — Notion Systemic Fix + 5-Layer Skill Defense: Three-phase infrastructure session. (1) Permanently fixed Notion bulk-read: discovered `notion-query-database-view` with `view://UUID` format is the ONLY working method (all other methods documented as broken in CLAUDE.md Operating Rules). Known view URL: Build Roadmap = `view://4eb66bc1-322b-4522-bb14-253018066fef`. (2) Deployed notion-mastery as Cowork auto-loaded skill (v1.1.0 → v1.2.0). (3) Researched Cowork skill triggering architecture — confirmed description-only semantic matching, no dependency system, no tool-usage triggers. Designed and implemented 5-layer defense for implicit Notion skill loading: CLAUDE.md semantic trigger instruction, Claude.ai Memory #14, ai-cos v5.2.0 inline Notion Quick Ref, notion-mastery semantic description rewrite, Build Roadmap insight "Tool-triggered skill loading." All layers implemented and verified. No thesis changes (infrastructure session).
- Session 033 — Layered Persistence Architecture + v6.0 Milestone: (1) Built self-documenting layered persistence architecture: created `docs/layered-persistence-coverage.md` coverage map, upgraded 5 under-covered instructions to 3+ layer coverage, added Memory entries #15 (persistence triage principle) and #16 (Cowork operating rules). (2) Built auto-audit mechanism: every 5 sessions (038, 043, 048...) review iteration logs for drift → upgrade layer count. Added to CLAUDE.md Persistence Audit Check. (3) v6.0 milestone bump: all artifacts renamed and version-bumped from v5.x → v6.0 (ai-cos skill, memory entries, user preferences, global instructions, artifacts index). Unified versioning across all surfaces. All cross-references updated in CONTEXT.md, CLAUDE.md, artifacts index. (4) User confirmed: installed v5.3.0 .skill (pre-bump), updated Claude.ai Memory (16 entries), updated Cowork Global Instructions. (5) Packaged ai-cos v6.0.0.skill for install. No thesis changes (infrastructure session). Artifact state: ai-cos v6.0.0, Memory 16 entries (v6.0), User Prefs v6.0, Global Instructions v6.0, Artifacts Index v6.0.
- Session 036 (2026-03-04) — Session Behavioral Audit v1.1 + v6.2.0: Built Session Behavioral Audit v1.1.0 with prompt template, 9 categories (A-I), trial-and-error detection (6 patterns). First audit run: 318-line report, 58% compliance, 4 trial-and-error loops found. Added persistence layering for subagent delegation (CLAUDE.md §D). Parallel dev review: 8-dimension assessment of sessions 034-036. Build Roadmap read/write validated (22 items, select gotcha documented). Version bump: v6.1.0 → v6.2.0.
- Session 035 — Parallel Development Phase 1: Subagent Test: (1) Deep research on parallelizing AI CoS development — file contention analysis, multi-agent architecture, enforcement mechanisms. Two research docs produced. (2) Key decisions: hierarchical delegation, lightweight build gates, feature-level roadmap with ephemeral task decomposition, local git only. (3) Phase 0 implementation: extended Build Roadmap schema (+4 properties: Parallel Safety, Assigned To, Branch, Task Breakdown), classified all 22 non-shipped items (10🟢, 7🟡, 5🔴), created 3 build insights. (4) Updated ai-cos skill with full parallel dev rules section (file classification, 6 rules, subagent allowlist protocol, 3-layer enforcement, parallel workflow). (5) Updated CLAUDE.md section E with 7-rule operating rules table + heuristic. (6) Close checklist upgraded 7→8 steps. No thesis changes (infrastructure). Artifact state: ai-cos v6.1.0, all others unchanged.
- Session 037 (2026-03-04) — Subagent Context Gap Fix + Multi-Layer Persistence: Root-caused subagent violations (Bash subagents don't inherit CLAUDE.md, skills, MCP tools — receive ONLY prompt text). 4-fix implementation: (1) Template library at `scripts/subagent-prompts/` with 4 templates (session-close, skill-packaging, git-push, general-file-edit), each with SUBAGENT CONSTRAINTS block + file allowlist + HAND-OFF protocol. (2) Spawning checklist (6-step, CLAUDE.md §F). (3) ai-cos skill documentation subsection. (4) Behavioral Audit v1.2.0→v1.3.0 with Section D2 subagent template usage correctness (per-spawn 4-step validation, severity mapping). Multi-layer persistence propagated to 5/6 layers (L0a, L0b, L1 #17+#18, L2, L3). L0a/L0b surface distinction discovered and documented. Orphaned file cleanup (7 stale docs). First successful templated subagent test (audit). Session close used 3 templated subagents for steps 2,3,5.
- Session 038 (2026-03-04) — QA Audit + Parallel Dev Phase 1: QA audit found 2 bugs (content pipeline dedup, launchd PATH) — logged to Build Roadmap as Phase 2.2 test subjects. Parallel dev Phase 1 implementation: (1) Git repo initialized at AI CoS root (local, no remote), initial commit e94123f (219 files), main branch. (2) .gitignore excludes aicos-digests/ and standard patterns. (3) CLAUDE.md §E expanded (248→280 lines) with git infrastructure, branch naming (feat/fix/research/infra/), 6-step branch lifecycle (CREATE→WORK→COMPLETE→REVIEW→MERGE→CLOSE), 2-step roadmap gate, always-query rule. (4) ai-cos skill updated (374→377 lines) with always-query rule, 2-step roadmap gate, coordinator recipe. (5) Active Branches view created by user in Build Roadmap (list view, filter: Branch not empty OR Status = In Progress). Design refined through 3 critique rounds: lightweight always-query (~3 sec) replaces keyword detection; code-only gate not universal; IDS-based drift detection not fixed-schedule. 3 continuations needed (context exhaustion). No thesis changes (infrastructure).

- Session 039 (2026-03-05) — Parallel Dev Phase 2-3 + Lifecycle CLI: Full parallel dev test suite across 16+ context windows. Phase 2.2: two real bugs (PATH fix f6cb6ce + dedup fix a571950) as sequential branch test — both merged cleanly. Phase 2.3a: controlled merge conflict test — manual resolution validated. Phase 2.3b: true parallel subagents — `action_scorer.py` (172 lines) + `dedup_utils.py` (139 lines) created simultaneously on separate branches. Phase 3.0: worktree-based isolation — refactored youtube_extractor.py + created `branch_lifecycle.sh` (322 lines) in parallel worktrees. Lifecycle CLI → daily use: upgraded with `full-auto` (non-interactive), worktree commands (`worktree-create`/`worktree-clean`/`worktree-list`), `PROJECT_ROOT` helper. E2E tested all commands via osascript. Created `branch-workflow.md` subagent prompt template. Bootstrap paradox documented: CLI upgrades on branch need manual merge first. No thesis changes (infrastructure).
For the full system vision documents:
- `/docs/aakash-ai-cos-system-vision.md` (v1 — task automation approach, superseded)
- `/docs/aakash-ai-cos-system-vision-v2.md` (v2 — network strategist approach, superseded)
- `/docs/aakash-ai-cos-system-vision-v3.md` (v3 — action optimizer / "What's Next?", current)

---

## HOW TO USE THIS DOCUMENT

**If you're a new Claude session (Cowork or Claude Code):**
1. Read this entire document FIRST before doing anything
2. Understand the anti-patterns — do NOT default to task automation
3. Check the "Current Build State" section for what's been done and what's next
4. If Aakash asks for something, always frame your response through the action optimizer lens
5. When in doubt, ask: "Does this help answer 'What's Next?' for Aakash?"

**If you're updating this document:**
- Update the "Last Updated" date and session number at the top
- Add new thesis threads as they're discovered
- Update "Current Build State" as things get built
- Add new Notion IDs as they're discovered
- Keep this document under 15,000 words — it needs to fit in context alongside actual work
