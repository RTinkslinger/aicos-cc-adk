# AI Chief of Staff — Engineering Overview (Cowork Era Snapshot)

**Last updated:** 2026-03-05 (Session 040)
**Status:** Historical reference — Cowork-era snapshot. Some file paths, execution patterns, and workflows are outdated (e.g., `/mnt/` paths, `osascript` bridging, Cowork VM constraints, 8-step session close). For current canonical references, see CLAUDE.md, CONTEXT.md, and `docs/architecture/`. Most valuable sections for CC: Content Pipeline data flow (§5), DigestData schema (§5.2), digest site architecture (§6), and Full Cycle DAG pattern (§10).

**Purpose:** Complete technical reference for what was built through Session 040. Covers what exists, where it lives, how data flows, and how users interact with each component.

---

## 1. What This System Is

The AI CoS is an **action optimizer** for Aakash Kumar (MD at Z47 / DeVC). It answers one question: **"What's Next?"**

It operates across two action types:

- **Stakeholder actions** — meetings, calls, emails, intros, follow-ups (with people/companies)
- **Intelligence actions** — content consumption, research, analysis (generate stakeholder actions)

The system is NOT a meeting scheduler or a dashboard. It ingests intelligence (YouTube videos, research, meeting notes), cross-references against active investment thesis threads and portfolio companies, proposes scored actions, and surfaces the highest-leverage next step.

---

## 2. Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER SURFACES                                │
│  Cowork Desktop  ·  Claude.ai (mobile)  ·  Claude Code (terminal)  │
│  WhatsApp (via digest links)  ·  digest.wiki (HTML digests)        │
└─────────────┬───────────────────────────────┬───────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────┐   ┌──────────────────────────────────────┐
│    INTELLIGENCE LAYER   │   │         OPERATING LAYER              │
│                         │   │                                      │
│  Content Pipeline       │   │  Action Scoring Model                │
│  (YouTube → Analysis)   │   │  People Scoring Model (subset)       │
│                         │   │  IDS Methodology                     │
│  PDF Digest Generator   │   │  Priority Buckets (4)                │
│  HTML Digest Publisher  │   │  Thesis Tracker (sync point)         │
│  Dedup Tracker          │   │                                      │
└────────────┬────────────┘   └──────────────┬───────────────────────┘
             │                               │
             ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     NOTION DATA LAYER                               │
│                                                                     │
│  Network DB  ·  Companies DB  ·  Portfolio DB  ·  Tasks Tracker     │
│  Thesis Tracker  ·  Content Digest DB  ·  Actions Queue             │
│  Build Roadmap                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Project File Structure

All files live in the project folder: `/Users/Aakash/Claude Projects/Aakash AI CoS/`

```
Aakash AI CoS/
├── CONTEXT.md                 # Single source of truth — master context doc
├── CLAUDE.md                  # Claude Code / Cowork operating rules
├── aicos-digests/             # Next.js 16 HTML digest site (has its own GitHub repo)
│   ├── .github/workflows/
│   │   └── deploy.yml         # GitHub Action → Vercel deploy
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx       # Homepage — lists all digests
│   │   │   └── d/[slug]/
│   │   │       └── page.tsx   # Individual digest page (SSG)
│   │   ├── components/
│   │   │   └── DigestClient.tsx  # Client-side digest renderer
│   │   ├── data/
│   │   │   └── *.json         # One JSON per digest (pipeline output)
│   │   └── lib/
│   │       ├── types.ts       # DigestData TypeScript schema
│   │       └── digests.ts     # Data loading + normalization layer
│   └── package.json           # Next.js 16, React 19, Tailwind 4
├── scripts/
│   ├── youtube_extractor.py   # YouTube → transcript + metadata JSON
│   ├── process_youtube_queue.py  # Queue reader / manifest builder
│   ├── publish_digest.py      # JSON → git commit → deploy trigger
│   ├── content_digest_pdf.py  # JSON → PDF digest (ReportLab)
│   ├── action_scorer.py       # Action Scoring Model implementation
│   ├── dedup_utils.py         # DedupTracker for pipeline idempotency
│   ├── branch_lifecycle.sh    # Git branch lifecycle CLI
│   ├── yt                     # Symlink/wrapper for youtube_extractor
│   ├── com.aakash.youtube-extractor.plist  # macOS launchd schedule
│   └── subagent-prompts/      # Pre-written prompt templates for subagents
│       ├── session-close-file-edits.md
│       ├── skill-packaging.md
│       ├── git-push-deploy.md
│       ├── general-file-edit.md
│       └── branch-workflow.md
├── skills/
│   ├── ai-cos-v6-skill.md    # Master AI CoS skill (v6.2.0)
│   ├── full-cycle/SKILL.md   # Meta-orchestrator skill
│   ├── youtube-content-pipeline/SKILL.md  # Content pipeline skill
│   └── parallel-deep-research/  # Multi-source research skill
├── queue/                     # YouTube extraction JSON files land here
│   ├── processed/             # Completed extractions move here
│   └── pipeline-run-log.md    # Log of pipeline executions
├── digests/                   # PDF digest output directory
├── docs/
│   ├── iteration-logs/        # One log per session (append-only)
│   ├── session-checkpoints/   # Mid-session state saves
│   ├── audit-reports/         # Behavioral audit outputs
│   ├── research/              # Research documents
│   └── v6-artifacts-index.md  # Cross-surface version tracker
└── data/                      # Misc data files
```

---

## 4. Notion Databases

All structured data lives in Notion. Every database has a **data source ID** used for programmatic access.

| Database | Data Source ID | Purpose | Key Fields |
|----------|---------------|---------|------------|
| **Network DB** | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` | People universe (400+) | 40+ fields, 13 archetypes, relationship tracking |
| **Companies DB** | `1edda9cc-df8b-41e1-9c08-22971495aa43` | Deal pipeline + IDS trail | 49 fields, conviction tracking, spiky scores |
| **Portfolio DB** | `4dba9b7f-e623-41a5-9cb7-2af5976280ee` | Active portfolio companies | 94 fields, full investment data |
| **Tasks Tracker** | `1b829bcc-b6fc-80fc-9da8-000b4927455b` | Tasks and follow-ups | Standard task fields |
| **Thesis Tracker** | `3c8d1a34-e723-4fb1-be28-727777c22ec6` | Investment thesis threads | Thread Name, Status, Core Thesis, Key Question, Discovery Source |
| **Content Digest DB** | `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` | Content analysis output | Title, Relevance Score, Action Status, Digest URL, thesis/portfolio connections |
| **Actions Queue** | `1df4858c-6629-4283-b31d-50c5e7ef885d` | All proposed actions | Priority (P0-P3), Status (Proposed→Accepted→In Progress→Done/Dismissed), relations to Company, Thesis, Source Digest |
| **Build Roadmap** | `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` | Product build items | Status pipeline (💡→📋→🎯→🔨→🧪→✅→🚫), Priority, Epic, Parallel Safety, Dependencies (self-relation) |

**How to read from any database:**
1. `notion-fetch` on the database ID → response includes `<view url="view://UUID">` tags
2. `notion-query-database-view` with `view_url: "view://UUID"` → returns all rows with full properties

**Known shortcut:** Build Roadmap has a cached view URL: `view://4eb66bc1-322b-4522-bb14-253018066fef`

**Property formatting rules (these will bite you):**

| Type | Wrong | Correct |
|------|-------|---------|
| Dates | `"Due Date": "2026-03-15"` | `"date:Due Date:start": "2026-03-15"`, `"date:Due Date:is_datetime": 0` |
| Checkbox | `"Done": true` | `"Done": "__YES__"` or `"__NO__"` |
| Relations | `"Company": "page-id"` | `"Company": "[\"https://www.notion.so/page-id\"]"` |
| Numbers | `"Score": "8"` | `"Score": 8` (native number) |
| Multi-select | Set multiple values at create | Create page first, then `notion-update-page` one value at a time |

---

## 5. Content Pipeline (the primary intelligence loop)

This is the most complete pipeline in the system. It turns YouTube videos into scored, actionable intelligence.

### 5.1 Data Flow

```
YouTube Playlists/URLs
        │
        ▼
┌───────────────────────────┐
│ 1. EXTRACTION             │  Runs on: Mac (not in VM)
│    youtube_extractor.py   │  Tool: yt-dlp + youtube-transcript-api
│    + dedup_utils.py       │  Output: queue/youtube_extract_*.json
│    + yt CLI wrapper        │  Schedule: launchd at 8:30 PM or manual
└───────────┬───────────────┘
            │ JSON files land in queue/
            ▼
┌───────────────────────────┐
│ 2. ANALYSIS               │  Runs on: Cowork VM (Claude LLM)
│    Claude AI analysis      │  Reads: queue/*.json transcripts
│    via ai-cos skill        │  Cross-refs: Thesis Tracker, Portfolio DB
│                            │  Schedule: 9 PM daily or "process my content queue"
│    Produces per-video:     │
│    - Relevance score       │
│    - Net newness category  │
│    - Essence notes         │
│    - Thesis connections    │
│    - Portfolio connections  │
│    - Proposed actions      │
│    - Contra signals        │
│    - Rabbit holes          │
└───────────┬───────────────┘
            │ analysis JSON
            ▼
┌───────────────────────────────────────────────────────┐
│ 3. OUTPUT (three parallel tracks)                      │
│                                                        │
│ A) PDF Digest                                          │
│    content_digest_pdf.py → digests/*.pdf               │
│    ReportLab-generated, scannable format               │
│                                                        │
│ B) HTML Digest                                         │
│    publish_digest.py → aicos-digests/src/data/*.json   │
│    → git commit → git push (osascript) → GitHub Action │
│    → Vercel prod → https://digest.wiki/d/{slug}       │
│    OG tags for WhatsApp sharing                        │
│                                                        │
│ C) Notion Records                                      │
│    → Content Digest DB (digest metadata + URL)         │
│    → Actions Queue (proposed actions with relations     │
│      back to Source Digest, Company, Thesis)            │
│    → Thesis Tracker updates (if new evidence)          │
└───────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────┐
│ 4. ACTION REVIEW           │  User: "review my content actions"
│    Mobile (Claude.ai) or   │  or "review my portfolio actions"
│    Cowork desktop           │
│                            │  Queries Actions Queue for
│    Approve / Dismiss       │  Status = "Proposed"
│    → updates Status field  │  Presents by priority P0→P3
└───────────────────────────┘
```

### 5.2 The DigestData Schema

Every content analysis produces a JSON object conforming to this TypeScript interface (defined in `aicos-digests/src/lib/types.ts`):

```typescript
interface DigestData {
  // Identity
  slug: string;            // URL-safe identifier
  title: string;           // Video/content title
  channel: string;         // Source channel
  url: string;             // Original URL

  // Dashboard
  relevance_score: "High" | "Medium" | "Low";
  net_newness: { category: "Mostly New" | "Additive" | "Reinforcing" | "Contra" | "Mixed", reasoning: string };
  connected_buckets: string[];

  // Analysis sections
  essence_notes: {
    core_arguments: string[];
    data_points: string[];
    frameworks: string[];
    key_quotes: { text: string, speaker: string, timestamp: string }[];
    predictions: string[];
  };
  watch_sections: { timestamp_range, title, why_watch, connects_to }[];
  contra_signals: { what, evidence, strength, implication }[];
  rabbit_holes: { title, what, why_matters, entry_point, newness }[];

  // Connections to investment universe
  portfolio_connections: { company, relevance, key_question, conviction_impact, actions }[];
  thesis_connections: { thread, connection, strength, evidence_direction }[];
  proposed_actions: { action, priority, type, assigned_to, company?, thesis_connection? }[];
}
```

### 5.3 Schema Normalization

Because the analysis is LLM-generated, the `digests.ts` loader includes **7 runtime normalizations** to handle schema drift between pipeline versions (v4 vs v5). For example: `core_argument` (string) → `core_arguments` (string[]), `challenge` → `what`, `Tangential` → `Weak`. This is a defense-in-depth pattern — prompt engineering sets the ideal, runtime normalization is the safety net.

### 5.4 Deduplication

`dedup_utils.py` provides a `DedupTracker` class that persists processed video IDs to a JSON file. The YouTube extractor uses it to skip already-processed videos across runs. It implements a context manager pattern (`with DedupTracker(...) as tracker`) for automatic save on exit.

---

## 6. HTML Digest Site (digest.wiki)

A statically-generated Next.js 16 app that renders mobile-friendly, shareable content digests.

### 6.1 Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 16.1.6 (App Router, SSG) |
| UI | React 19, Tailwind CSS 4 |
| Hosting | Vercel (production) |
| Domain | digest.wiki (custom domain → Vercel) |
| CI/CD | GitHub Actions → Vercel CLI |
| Data | Static JSON files in `src/data/` |

### 6.2 How It Works

Each digest is a JSON file in `src/data/{slug}.json`. At build time, Next.js reads all JSON files via `digests.ts`, generates static HTML for each digest page, and produces dynamic OG metadata for WhatsApp sharing previews.

**Pages:**
- `/ ` — Homepage listing all digests, sorted by date (newest first)
- `/d/{slug}` — Individual digest page, rendered by `DigestClient.tsx`

**The `DigestClient.tsx` component** is the main client-side renderer. It takes a `DigestData` object and renders sections: dashboard header (relevance, newness, buckets), essence notes, watch sections, contra signals, rabbit holes, portfolio connections, thesis connections, and proposed actions.

### 6.3 Deploy Pipeline

There is exactly one deploy path. No alternatives.

```
1. Commit JSON to aicos-digests/src/data/
2. git push origin main  (via osascript MCP when in Cowork)
3. GitHub Action triggers (deploy.yml)
4. Vercel CLI: pull env → build → deploy to production
5. Live at https://digest.wiki/d/{slug} (~90 seconds end-to-end)
```

The `publish_digest.py` script automates steps 1-2: it takes an analysis JSON, generates a slug, writes the file to `src/data/`, and commits. When called from Cowork, the push happens via `osascript` MCP on the Mac host (the Cowork VM has no outbound network).

---

## 7. Scoring Models

### 7.1 Action Scoring Model (primary)

The core ranking function for all actions across the system.

```
Action Score = f(
  bucket_impact,              # Which priority bucket? (10=new cap tables, 8=deepen/founders, 6=thesis)
  conviction_change_potential, # Could this change conviction on an investment?
  key_question_relevance,     # Does this answer a live key question?
  time_sensitivity,           # How urgent? (decays over time)
  action_novelty,             # New insight or repetitive?
  stakeholder_priority,       # How important is this person/company?
  effort_vs_impact            # High impact / low effort = high score
)
```

**Thresholds:**
- ≥7: **Surface** — present as an immediate action candidate
- 4–6.99: **Low confidence** — tag for context enrichment
- <4: **Context only** — informational, no action proposed

Implementation: `scripts/action_scorer.py` (172 lines). Uses `ActionInput` dataclass with `validate()` for range checking, configurable `ScoringWeights`, and `ActionResult` with `classification` enum.

### 7.2 People Scoring Model (subset)

Applied when the action type is "meeting" — adds person-specific dimensions:

```
Person Score = f(
  bucket_relevance, current_ids_state, time_sensitivity,
  info_gain_potential, network_multiplier, thesis_intersection,
  relationship_temp, geographic_overlap, opportunity_cost
)
```

### 7.3 Four Priority Buckets

All scoring maps back to these investment priorities:

1. **New cap tables** — Get on more companies' cap tables (highest, always)
2. **Deepen existing cap tables** — Continuous IDS on portfolio for follow-on decisions (high, always)
3. **New founders/companies** — DeVC Collective pipeline (high, always)
4. **Thesis evolution** — Interesting people who keep thesis lines evolving (variable)

---

## 8. Actions Queue

The **Actions Queue** is the single sink for all action types across the system. Every proposed action, regardless of source (content pipeline, deep research, meetings, manual entry), routes here.

**Status pipeline:** Proposed → Accepted → In Progress → Done / Dismissed

**Relations:**
- Company → Portfolio DB (links action to a portfolio company)
- Thesis → Thesis Tracker (links action to a thesis thread)
- Source Digest → Content Digest DB (traces action back to the content that spawned it)

**User interaction:**
- "Review my portfolio actions" — queries for Status = Proposed, presents by priority P0→P3
- User approves or dismisses each action
- Batch accept supported for high-confidence items

---

## 9. Thesis Tracker

The shared state for investment thesis threads across all Claude surfaces (Cowork, Claude.ai, Claude Code).

**Active threads (March 2026):**

| Thread | Conviction | Key Idea |
|--------|-----------|----------|
| Agentic AI Infrastructure | High | Harness layer is where durable value lives (Composio, Smithery.ai, Poetic, MCP) |
| Cybersecurity / Pen Testing | Medium-High | Service → platform transition = venture-scale value creation |
| USTOL / Aviation / Deep Tech Mobility | Medium | Electrification meets defense meets logistics |
| SaaS Death / Agentic Replacement | High | AI agents replacing traditional SaaS entirely (4/4 source convergence) |
| CLAW Stack Standardization | Medium | CLAW (Compute, LLM, Agent, Workflow) analogous to LAMP/MEAN |
| Healthcare AI Agents | Early | Monitor for convergence |

**Sync protocol:** When any session discovers or updates a thesis thread, it writes to the Thesis Tracker. This ensures compound learning across all Claude surfaces. The `Discovery Source` field tracks which surface created the entry.

---

## 10. Full Cycle Orchestrator

Trigger: "run full cycle" / "run everything" / "process everything"

This is a **DAG-based meta-orchestrator** that runs all pipeline tasks in dependency order with human checkpoints. Defined in `skills/full-cycle/SKILL.md`.

```
Step 0: Pre-flight check          (Cowork)         — verify queue, Notion access
Step 1: YouTube extraction         (Mac/osascript)  — ⏸ confirm before proceeding
Step 2: Content Pipeline analysis  (Cowork/Claude)  — ⏸ review proposed actions
Step 3: Back-propagation sweep     (Cowork)         — update Done actions in Content Digest
```

Each step declares its dependencies. Supports partial runs ("just run the sweep", "just process the queue").

---

## 11. Scheduled Tasks

| Task | Schedule | What It Does |
|------|----------|-------------|
| YouTube extraction | launchd, 8:30 PM daily | Runs `youtube_extractor.py` on configured playlists |
| Content Pipeline | Cowork scheduled task, 9 PM daily | Processes queue/*.json through AI analysis → digests → Notion |
| Back-propagation sweep | Cowork scheduled task, 10 AM daily | Syncs completed action status back to Content Digest DB |

---

## 12. Execution Environment

### 12.1 Cowork (Desktop — Primary Build Surface)

Cowork runs in a **lightweight Linux VM** on the Mac. Key constraints:

| Capability | Status |
|-----------|--------|
| File read/write in mounted folder | ✅ Works |
| Bash commands | ✅ Works |
| MCP tools (Notion, Gmail, Calendar, Vercel, etc.) | ✅ Works |
| Outbound HTTP (curl, wget, fetch) | ❌ Blocked |
| Git push | ❌ Must use `osascript` MCP on Mac host |
| Mac-native paths (`/Users/...`) | ❌ Must use mounted `/sessions/.../mnt/` paths |
| File deletion on mounted paths | ❌ Read-only sandbox restriction |

**Workaround for outbound operations:** Use `osascript` MCP to execute commands on the Mac host:
```
osascript 'do shell script "cd /path/to/repo && git push origin main 2>&1"'
```

### 12.2 Claude.ai (Mobile — Action Review Surface)

Used for reviewing actions on the go. Claude.ai has access to Notion via memories and can query the Actions Queue and Content Digest DB. Primary use cases: "review my content actions", "what's next?", quick thesis lookups.

### 12.3 Claude Code (Terminal — Development Surface)

Used for code-heavy work. Same project folder access. Reads CLAUDE.md and CONTEXT.md. Used for infrastructure work, script development, and complex debugging.

---

## 13. Parallel Development Infrastructure

The project uses a local git repo (no remote for the main project — only `aicos-digests/` has a GitHub remote) for branching and parallel work.

### 13.1 Branch Naming

- `feat/` — new features
- `fix/` — bug fixes
- `research/` — research tasks (always safe to parallelize)
- `infra/` — infrastructure

### 13.2 Branch Lifecycle (6 steps)

Managed via `scripts/branch_lifecycle.sh`:

```bash
./scripts/branch_lifecycle.sh create feat/my-feature    # 1. Create branch
# ... do work, commit ...                                # 2. Work
# ... update Build Roadmap status ...                    # 3. Complete
./scripts/branch_lifecycle.sh diff feat/my-feature       # 4. Review
./scripts/branch_lifecycle.sh merge feat/my-feature      # 5. Merge
./scripts/branch_lifecycle.sh close feat/my-feature      # 6. Close
```

Also supports worktrees: `worktree-create`, `worktree-clean`, `worktree-list`, and `full-auto` (automated lifecycle).

### 13.3 File Safety Classifications

Every file has a parallel safety level. A task's safety = the worst classification of any file it touches.

- **🟢 Safe** — docs/iteration-logs/*, docs/research/*, new JSON data files, Notion DB entries
- **🟡 Coordinate** — CONTEXT.md (section ownership), digests.ts, types.ts, publish_digest.py
- **🔴 Sequential only** — ai-cos skill, CLAUDE.md, package.json, artifacts index, coverage map

### 13.4 Build Roadmap Gate

Before any code change, check if a Build Roadmap item exists. If not, quick-add one with Status = 💡 Insight. No untracked code changes.

---

## 14. Subagent Architecture

Complex tasks are split into subagents (`Task(subagent_type="Bash")`) that run file operations, while the main session handles MCP operations (Notion, osascript, etc.).

**What subagents CAN do:** Bash, Read, Edit, Write, Glob, Grep

**What subagents CANNOT do:** Any MCP tool (Notion, osascript, Gmail, etc.), outbound network, file deletion on mounted paths

**Hand-off protocol:** Subagent does file work → outputs `HAND-OFF: [description]` → main session picks up MCP-only tasks.

**Template library** at `scripts/subagent-prompts/` provides pre-written prompts for common tasks (session close, skill packaging, git operations, general file edits).

---

## 15. Session Lifecycle

### Checkpoints
Trigger: "checkpoint" / "save state" → writes to `docs/session-checkpoints/`

### Session Close (mandatory 8 steps)
Trigger: "close session" / "end session"

1. Write iteration log to `docs/iteration-logs/`
   - 1b. Create Build Roadmap entries for any session insights
   - 1c. Run behavioral audit via subagent
2. Update CONTEXT.md
3. Update CLAUDE.md (last session reference)
4. Sync thesis threads to Notion Thesis Tracker
5. Update artifacts index (`docs/persistence/v6-artifacts-index.md`)
6. Package updated skills as `.skill` ZIP files
7. Update Build Roadmap metadata in Notion
8. Confirm all steps complete

---

## 16. Key Reference Files

| File | Purpose | When to Read |
|------|---------|-------------|
| `CONTEXT.md` | Single source of truth — everything about the system | Start of every session |
| `CLAUDE.md` | Operating rules, anti-patterns, database IDs, recipes | Start of every session |
| `skills/ai-cos-v6-skill.md` | Master AI CoS skill with full methodology | When the ai-cos skill loads |
| `aicos-digests/src/lib/types.ts` | DigestData TypeScript schema | When working on content pipeline or digest site |
| `aicos-digests/src/lib/digests.ts` | Data loading + normalization layer | When debugging digest rendering |
| `docs/persistence/v6-artifacts-index.md` | Cross-surface version tracker | When bumping any artifact version |
| `docs/layered-persistence-coverage.md` | Which rules are covered at which persistence layer | During persistence audits (every 5 sessions) |

---

## 17. What Is NOT Built Yet

For completeness — things referenced in the vision but not yet operational:

- **Action Frontend** — accept/dismiss actions directly from digest pages (currently done via Claude.ai chat)
- **"Optimize My Meetings"** — People Scoring applied to calendar slate (model exists, UI does not)
- **"Who Am I Underweighting?"** — analysis of network gaps (methodology defined, not automated)
- **Multi-source content ingestion** — only YouTube is wired; podcasts, newsletters, and articles are planned
- **WhatsApp voice interface** — the ultimate operating interface (vision-stage)
- **Always-on signal processor** — continuous monitoring layer (vision-stage)
- **Custom Agent SDK build** — migration from Cowork to dedicated agent infrastructure (planned for 100x scale)
