# CLAUDE.md

## MANDATORY CONTEXT — CANNOT BE SKIPPED UNDER ANY CIRCUMSTANCES

**THE FOLLOWING IS NOT OPTIONAL. IT IS NOT A SUGGESTION. IT IS A HARD REQUIREMENT.**
**EVERY SINGLE SESSION IN THIS PROJECT MUST FOLLOW THESE RULES.**
**THERE ARE NO EXCEPTIONS. THERE ARE NO SHORTCUTS. THERE IS NO "I'LL DO IT DIFFERENTLY."**

### STEP 0: Before ANYTHING else — read the golden pattern file

```
Read docs/source-of-truth/GOLDEN-SESSION-PATTERN.md — THE ENTIRE FILE, NOT SKIMMING
```

This file contains the ONLY correct way to operate in this project. **Golden Pattern v2** — extracted from session 2026-03-20 (rated 10/10) + refined through 100+ corrections + perfected in the last 60 minutes of session 2026-03-21 (perpetual loops, feedback infrastructure, agent-first architecture). Every deviation has resulted in wasted hours.

**"Resume machineries" = read Section 9 of the golden pattern file. It tells you EXACTLY what to do.**

### HARD RULES (violating ANY of these is a session failure)

1. **AGENTS DO ALL THINKING.** Claude Agent SDK PERSISTENT agents reason. SQL functions fetch data. Python scripts move data. If you write SQL that scores, assesses, recommends, detects, or predicts — you have FAILED. That logic belongs in an agent. NOT ephemeral agents. NOT Python scripts. PERSISTENT ClaudeSDKClient on the droplet.

2. **MACHINE LOOP ≠ AGENT DOING WORK.** M4 machine loop BUILDS the Datum agent (its code, skills, tools, instructions). Datum agent RUNS AUTONOMOUSLY on the droplet. The machine loop makes agents SMARTER. It does not DO the agent's work. Machine loops build: SQL tools + skill files + CLAUDE.md updates + hooks. ALL TOGETHER, never one without the others.

2b. **AGENT CLAUDE.md = OBJECTIVES, NOT SCRIPTS.** Agent CLAUDE.md defines objectives, identity, boundaries. Skills define tools + patterns of success + anti-patterns. The agent REASONS about how to chain tools to achieve objectives. NEVER write step-by-step processing instructions in agent CLAUDE.md. NEVER. The agent is a reasoner, not a script runner. This has been violated in EVERY agent file written so far.

3. **MACHINES ARE PERPETUAL.** They loop forever with internal specialist steps (product leadership → research → build → review → fix → cross-machine). They do NOT stop after one build. They do NOT ask "shall I proceed?" They EXECUTE.

4. **DATUM RUNS EVERY SESSION.** M4 Datum has been neglected in every session since the golden one. This is the #1 recurring failure. Datum = data quality, linkages, enrichment, embedding health. Skip it and every other machine works with garbage data.

5. **ORCHESTRATOR DIFFUSES CONTEXT.** The CC main thread reads agent results, routes findings to other machines, spawns fix agents, routes user feedback in real-time, maintains the task dashboard, captures the feedback timeline. It does NOT launch agents and walk away.

6. **USER IS THE ONLY JUDGE.** Machine self-grades are meaningless. The system reported 9.6/10 while the user experienced 3/10. Technical health ≠ product quality. If the user says 3/10, it's 3/10.

7. **WEBFRONT DEPLOYS EVERY M1 LOOP.** The user is the sole consumer. They test live on digest.wiki. No batching deploys.

8. **FEEDBACK TIMELINE CREATED AT SESSION START.** `docs/feedback-timeline-YYYY-MM-DD.md` — append every user reaction with timestamp. At pause: analyze patterns, feed reasoned analysis to machines.

9. **BACKEND = LIGHT PLUMBING.** lifecycle.py, systemd, deploy.sh, cron. No reasoning. No intelligence logic in Python or SQL. Ever.

10. **NEVER BYPASS USER TRIAGE.** The depth grading system (Skip/Scan/Investigate/Ultra) exists so the USER decides what to delegate to agents. Never auto-delegate. Never remove user control.

### IF YOU FIND YOURSELF DOING ANY OF THESE — STOP IMMEDIATELY

- Writing a complex SQL function that "assesses risk" or "generates intelligence"
- Launching one fat agent with "do 10 loops"
- Skipping Datum machine
- Not deploying M1 after a loop
- Reporting 9/10 when the user said 3/10
- Asking "shall I proceed?" instead of executing
- Not creating the feedback timeline
- Building smarter SQL instead of smarter agents
- Not reading GOLDEN-SESSION-PATTERN.md

---

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

This is the **Aakash AI Chief of Staff (AI CoS)** project — an action optimizer answering **"What's Next?"** for Aakash Kumar (MD at Z47 / $550M fund + MD at DeVC / $60M fund). It optimizes across his full stakeholder and action space: meetings, content consumption, research, thesis building, and portfolio management.

**CONTEXT.md is the domain knowledge layer** — Aakash's world, priorities, methodology, and data architecture. It is NOT auto-loaded; read it when you need domain context.

**Read CONTEXT.md when:**
- Querying or writing to Notion (DB IDs, schemas, property formats, routing protocols)
- Scoring or ranking actions/people (scoring models, priority buckets, thresholds)
- Working with thesis threads (active threads, IDS notation, conviction spectrum)
- Running or modifying the Content Pipeline (queue flow, DB state machine, digest schema)
- Decoding domain references (people abbreviations like "VV"/"RA", operational playbooks, deal flow)
- Domain knowledge changed (thesis threads, methodology, people, priorities)

**Skip CONTEXT.md when:** pure code edits, repo tooling, frontend styling, git operations, or anything that doesn't touch AI CoS domain logic.

**`docs/source-of-truth/` is the single canonical reference folder** — 9 files covering vision, methodology, architecture, data, MCP tools, capabilities, entity schemas, droplet operations, and tunnel setup. See `docs/source-of-truth/README.md` for the index. Read these before building anything that touches infrastructure, data, or system design.

## Repository Structure

**GitHub remote:** `https://github.com/RTinkslinger/aicos-cc-adk.git`

| Directory | Purpose |
|-----------|---------|
| `CONTEXT.md` | Master context — read this first |
| `scripts/` | Operational scripts (YouTube extractor, branch lifecycle CLI) |
| `docs/source-of-truth/` | All canonical reference files — read before building anything |
| `docs/superpowers/plans/` | Implementation plans |
| `docs/superpowers/specs/` | Design specs and architecture docs |
| `docs/superpowers/brainstorms/` | Think-throughs, assessments, brainstorming sessions |
| `docs/research/` | Deep research reports and reference docs |
| `docs/audits/` | System audits, health checks, analysis outputs |
| `docs/notion/` | Notion operations guide + database schemas |
| `mcp-servers/agents/` | v3 agents monorepo: orchestrator, content agent, state MCP, web tools MCP. Deploy via `deploy.sh`. |
| `aicos-digests/` | **Separate git repo** (gitignored). Next.js 16 digest site at https://digest.wiki |
| `portfolio-research/` | Per-company deep research files (20 companies) |
| `Archives/` | Superseded code + old docs — reference only |

## Artefact Routing (MANDATORY)

All generated artefacts MUST go to the correct folder. No exceptions. Skills that have default save paths are overridden by these rules.

| Artefact Type | Save To | Naming | Source/Trigger |
|---------------|---------|--------|----------------|
| Implementation plans | `docs/superpowers/plans/` | `YYYY-MM-DD-<slug>.md` | writing-plans skill, any build/migration plan |
| Design specs | `docs/superpowers/specs/` | `YYYY-MM-DD-<slug>.md` | Architecture specs, API specs, design docs |
| Brainstorms | `docs/superpowers/brainstorms/` | `YYYY-MM-DD-<slug>.md` | think-through skill, assessments, brainstorming |
| Research | `docs/research/` | `YYYY-MM-DD-<slug>.md` | Deep research, ultra reports, reference docs |
| Audits/Analysis | `docs/audits/` | `YYYY-MM-DD-<slug>.md` | Health checks, system audits, code reviews, file audits |
| Pending items | `docs/` | `PENDING-ITEMS-YYYY-MM-DD.md` | Extracted from plan compaction |

**Never save artefacts to:** project root, random subdirectories, `.claude/plans/`, or temp locations.

## Key Commands

### YouTube Content Extraction
```bash
# CLI shortcut (default playlist, last 3 days)
./scripts/yt
# Custom: last 7 days
./scripts/yt 7
# Custom playlist URL
./scripts/yt <PLAYLIST_URL>
# Direct script
python3 scripts/youtube_extractor.py <PLAYLIST_URL_OR_ID> --since-days 3
```
**Requires:** `pip3 install yt-dlp youtube-transcript-api`

### Branch Lifecycle (Parallel Development)
```bash
./scripts/branch_lifecycle.sh create feat/my-feature
./scripts/branch_lifecycle.sh status          # show all branches
./scripts/branch_lifecycle.sh diff feat/x     # diff vs main
./scripts/branch_lifecycle.sh merge feat/x    # merge to main
./scripts/branch_lifecycle.sh close feat/x    # delete branch
./scripts/branch_lifecycle.sh full feat/x     # interactive review+merge+close
./scripts/branch_lifecycle.sh full-auto feat/x # non-interactive
./scripts/branch_lifecycle.sh worktree-create feat/x
./scripts/branch_lifecycle.sh worktree-clean feat/x
./scripts/branch_lifecycle.sh worktree-list
```
Branch naming: `feat/`, `fix/`, `research/`, `infra/`

### Digest Site (aicos-digests/)
```bash
cd aicos-digests && npm run dev    # local dev
cd aicos-digests && npm run build  # verify build
```
Deploy: Pipeline on droplet auto-publishes → git push → Vercel deploy hook (~30s). Live at https://digest.wiki.
Manual deploy from Mac: `cd aicos-digests && npx vercel deploy --prod`

### Agents Monorepo (live)
```bash
cd mcp-servers/agents && bash deploy.sh           # deploy to droplet (3-phase: sync, bootstrap, cleanup)
```
**Public endpoints:** `https://mcp.3niac.com/mcp` (State MCP), `https://web.3niac.com/mcp` (Web Tools MCP)
**Services:** Orchestrator (lifecycle.py manages both agents), State MCP (:8000), Web Tools MCP (:8001)
**Live monitoring:** `ssh -t root@aicos-droplet /opt/agents/live-orc.sh` (also live-content.sh, live-traces.sh)

### Agent SDK Runners (planned)
```bash
cd agents/ && python -m agents.<runner_name>     # run individual agent
```

## Remote Repo Sync Discipline

This project now has a **GitHub remote** (`RTinkslinger/aicos-cc-adk`). It also contains sub-directories that are **separate git repos with their own remotes** (e.g., `aicos-digests/`). These sub-repos are gitignored from the parent.

**Mandatory protocol for all remote-connected repos (including this one):**
1. **Pull before editing:** Always `git pull --ff-only origin main` before making any changes
2. **Push after editing:** Always `git push origin main` after committing
3. **Author identity:** Use `Aakash Kumar <hi@aacash.me>` — Vercel and other services may reject unknown authors

This applies everywhere these repos are touched: the droplet pipeline (`publishing.py`), `deploy.sh`, manual edits from Mac, and any future agents or services.

**Current remote repos:**
| Directory | Remote | Purpose |
|-----------|--------|---------|
| `.` (root) | `github.com/RTinkslinger/aicos-cc-adk` | AI CoS main repo |
| `aicos-digests/` | `github.com/RTinkslinger/aicos-digests` | digest.wiki Next.js site |

## Agent SDK Build Rules (MANDATORY)

Any agent building or modification MUST cross-reference the Agent SDK documentation and research before implementation:
1. **Read before coding:** Review relevant docs from `docs/research/claude-agent-sdk-reference/` (14 files covering every SDK topic)
2. **Verify patterns:** Every SDK pattern (tools, hooks, permissions, sessions, deployment) must be verified against official docs, not memory
3. **No silent fallbacks:** If the Agent SDK can't do something, STOP and discuss before taking an alternative path
4. **Research first:** Read `docs/research/2026-03-15-agent-web-mastery/` for web browsing problem statements and solutions

## FUNDAMENTAL ARCHITECTURE RULE (HARDCODED — NEVER VIOLATE)

**Claude Agent SDK agents do ALL the thinking. SQL/Python/scripts are PLUMBING ONLY.**

The stack:
1. **Infrastructure** (Postgres, pgvector, pgmq) → enables agents, stores data
2. **Data** (structured + unstructured) → raw material for agents to query
3. **SQL functions** → simple data access tools FOR agents. NOT intelligence logic. NOT scoring formulas. NOT risk assessment algorithms.
4. **Python scripts** → plumbing (data movement, API calls, file I/O). NOT reasoning.
5. **Claude Agent SDK agents** (ENIAC, Datum, Cindy, Megamind) → ALL reasoning, scoring, risk assessment, strategic analysis, obligation prioritization, intelligence generation. WITH tools + skills + instructions + examples.

**WHAT THIS MEANS FOR MACHINE LOOPS:**
- Do NOT build smarter SQL functions that encode intelligence (no 15-multiplier scoring procedures, no weighted risk assessment in SQL)
- DO build SQL functions as simple TOOLS that agents call (fetch data, aggregate, join, store results)
- DO build agent skills, tools, instructions that make AGENTS smarter
- The scoring function, risk assessment, intelligence generation = AGENT REASONING, not procedural SQL
- WebFront renders AGENT OUTPUT (stored in DB after agent reasoning), not SQL function results
- Preference stores, feedback loops, self-learning = agents reading accumulated user decisions and adapting their reasoning
- This is REAL AI — Claude/Anthropic model power reasoning with full context, not SQL pretending to think

**EVERY TIME you're about to write a complex SQL function that "scores" or "assesses" or "recommends" — STOP. That logic belongs in an agent.**

## Anti-Patterns

- Do NOT default to morning briefs, dashboards, or generic task automation
- Do NOT hallucinate Notion data — query it using IDs from CONTEXT.md
- Do NOT lose the action-optimizer framing by narrowing to only meeting optimization
- Do NOT design for desktop — Aakash lives on WhatsApp and mobile
- Do NOT treat meeting optimization as the whole system — it's one output of the action optimizer
- Do NOT build intelligence logic in SQL functions — agents reason, SQL fetches data
- Do NOT write Python scripts that make intelligence decisions — scripts are plumbing for agents
- Do NOT build "smarter SQL" when the answer is "smarter agents" — this has been violated 100+ times

## MCP Tool Routing (MANDATORY)

**Prefer ai-cos-mcp tools over direct Notion MCP for these databases:**

| Database | Reads | Writes |
|----------|-------|--------|
| **Thesis Tracker** | `cos_get_thesis_threads` | `cos_create_thesis_thread`, `cos_update_thesis` |
| **Content Digest** | `cos_get_recent_digests` | Pipeline only (no manual writes) |
| **Actions Queue** | `cos_get_actions` | Notion MCP for status changes (accept/dismiss) |

**Use Notion MCP for:** Companies DB, Network DB, Portfolio DB, and any operation without a cos_* tool.

**Conviction guardrail:** Never set the `conviction` parameter on thesis tools from Claude Code. Provide evidence and ask Aakash if conviction should change. Conviction requires full evidence picture.

## Notion Operations

**Read `docs/notion/README.md` before any Notion tool call.** This applies even when the user's prompt doesn't mention "Notion" — if the task will touch any Notion database, read the operations guide first. It contains tool selection, property formatting, recipes, gotchas, and database schema references.

### Key Database IDs (Data Source IDs)

| Database | Data Source ID |
|----------|---------------|
| Network DB | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` |
| Companies DB | `1edda9cc-df8b-41e1-9c08-22971495aa43` |
| Portfolio DB | `4dba9b7f-e623-41a5-9cb7-2af5976280ee` |
| Tasks Tracker | `1b829bcc-b6fc-80fc-9da8-000b4927455b` |
| Thesis Tracker | `3c8d1a34-e723-4fb1-be28-727777c22ec6` |
| Content Digest DB | `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2` |
| Actions Queue | `1df4858c-6629-4283-b31d-50c5e7ef885d` |
| Build Roadmap | `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f` |

### Critical Guardrails
- **Bulk-read pattern:** `notion-fetch` on DB ID → find `view://UUID` → `notion-query-database-view`. One call, all rows.
- **Build Roadmap view URL:** `view://4eb66bc1-322b-4522-bb14-253018066fef`
- **NEVER use:** `API-query-data-source` (broken), `notion-fetch` on `collection://` URLs (schema only), `https://` URLs with `notion-query-database-view` (fails)
- **Property formatting:** dates = `"date:Field:start"`, checkbox = `"__YES__"`, relations = `"[\"https://www.notion.so/page-id\"]"`, numbers = native int (not string)

## Session Close Checklist

Trigger: "close session" / "end session" / "wrap up". All steps are conditional — skip any that don't apply.

1. **Build Traces** → If code files were modified, read `TRACES.md` and add an iteration entry. Run compaction if needed (every 3 iterations). Also enforced by Stop hook.
2. **LEARNINGS.md** → Review session for trial-and-error patterns. Log any unrecorded broken > working pairs.
3. **Build Roadmap** → Ensure Roadmap items reflect current state (In Progress, Verifying, Insight). Create items for untracked code changes.
4. **Update CLAUDE.md** → Only if structural changes happened: new capabilities, new IDs, new commands, new repo structure.
5. **Update MEMORY.md** → Only if stable cross-session patterns were discovered (not session-specific details).
6. **Update CONTEXT.md** → Only if domain knowledge changed: thesis threads, methodology, people, priorities. NOT for session bookkeeping.
7. **Notion sync** → Only if Notion-tracked data changed (Thesis Tracker, Build Roadmap).
8. **Claude.ai sync** → Only if architectural changes happened (new infrastructure, schema changes, new runners, workflow changes). Update `claude-ai-sync/memory-entries.md` + `claude-ai-sync/CHANGELOG.md`. Tell Aakash to paste into Claude.ai Settings → Memory.

## Parallel Development Rules

1. **Always query Build Roadmap** before starting work — check for conflicts, claim items
2. **Branch naming:** `{feat|fix|research|infra}/{slug}` from `main`
3. **File classification:** Scripts and skills have ownership by feature — check before editing shared files
4. Use `branch_lifecycle.sh` for the standard 6-step workflow

## Machine → Loop → Step → Army Pattern (HARDCODED)

**This is the MANDATORY execution pattern for all permanent machineries. No simplification.**

**PLAYBOOK:** Read `docs/source-of-truth/MACHINE-LOOP-PLAYBOOK.md` before ANY "resume machineries" command. It contains the definitive execution pattern with anti-patterns, agent templates, and the orchestrator's role. Reference session: 2026-03-20.

**FEEDBACK TIMELINE (MANDATORY):** When running machine loops, IMMEDIATELY create `docs/feedback-timeline-YYYY-MM-DD.md` and append ALL user feedback with timestamps as it comes in. At pause/sync, reason about patterns and feed into next wave. This is hardcoded — no exceptions.

### Structure
```
MACHINE (e.g., M1 WebFront) — permanent, loops forever
  └── LOOP (one full cycle of all steps — runs N times per session)
       ├── STEP: Build/Execute → ARMY of 4-5 specialist agents
       ├── STEP: QA + User Review + Intelligence Review → ARMY of specialists
       ├── STEP: Product Leadership Assessment → ARMY of specialists
       │    (defines problems + exploratory solutions, NOT instructions)
       ├── STEP: Think, Research, Problem Solve → ARMY of specialists
       │    (deep research on unknowns, study best-in-class products)
       └── STEP: Build/Execute (next iteration, using all prior step outputs)
```

### Rules
1. **Each STEP has a SERIAL CHAIN of 5 specialist agents (minimum).** Like a product org at Uber/Airbnb/ByteDance: work passes from specialist to specialist, each building on the prior one's output.
2. **"Add X more agents per machine" = staff MORE specialists in each step's chain.** Not a longer task list.
3. **Loops are FULL CYCLES** — input → build → assess → product leadership → research → build again. Each cycle's output feeds the next cycle's input. Flywheel improvement.
4. **Cross-machine sync is MANDATORY.** Machines are intertwined. Every specialist needs context from OTHER machines' recent outputs. Propagate changes across all machines.
5. **Product Leadership step** suggests problems + exploratory directions, NOT instructions. "UX feels rough on tab transitions → maybe try visual loading feedback, faster data streaming, or novel approaches."
6. **Think/Research/Solve step** = deep and wide research. Study Linear, Superhuman, Bloomberg. Research is core behavior, not optional.
7. **Parallelism is ACROSS machines (8 running simultaneously), not within steps.** Within each step, specialists work serially — each building on the previous one's output. This mirrors how product orgs work (designer → engineer → QA).

### How Specialists Work Within a Step
```
Step (e.g., Build/Execute):
  Specialist 1 (Product Designer): Reviews requirements → design brief
  Specialist 2 (Engineer): Takes design brief → implements code
  Specialist 3 (Data Engineer): Takes implementation → wires data layer
  Specialist 4 (UX Researcher): Takes result → reviews against best practices
  Specialist 5 (QA): Takes all output → tests, documents issues
  → Step output = final specialist's refined result
```
Each specialist receives ALL prior specialists' output. The chain compounds quality. The machine agent role-plays each specialist in sequence.

### Agent Architecture (Python = plumbing, Claude = reasoning)
- Python scripts: data extraction, API calls, file I/O (plumbing ONLY)
- Claude Agent SDK agents: all reasoning, signal extraction, people resolution, intelligence work
- Datum agent: data ops (resolve, link, enrich, dedup)
- Cindy agent: communications intelligence (obligations, signals — LLM reasoning, not regex)
- Megamind agent: strategic reasoning (co-strategist, not slave)
- ENIAC agent: research analyst (content + thesis)

## Action Scoring Model

```
Action Score = f(bucket_impact, conviction_change_potential, key_question_relevance,
                 time_sensitivity, action_novelty, stakeholder_priority, effort_vs_impact)
```
Thresholds: ≥7 surface as action, 4-6 low-confidence tag, <4 context enrichment only.

People Scoring Model is a subset — applied when the action type is "meeting."

## Content Pipeline Architecture

```
Droplet (cron every 5 min): extraction.py → queue/*.json
ContentAgent: queue/ → Claude analysis → digest JSON → Notion + Actions Queue + Thesis updates
Publishing: digest.wiki → git push → Vercel auto-deploy (~15s)
SyncAgent (10-min cron): Notion ↔ Postgres bidirectional sync, change detection, action generation
```

Key services (on droplet `/opt/agents/`): `orchestrator/lifecycle.py` (manages both agents), State MCP (`state/server.py`), Web Tools MCP (`web/server.py`). Content pipeline runs via persistent ClaudeSDKClient content agent, triggered by orchestrator heartbeat or CAI inbox messages.

**ContentAgent + SyncAgent are live** — running autonomously on the droplet. See `docs/source-of-truth/ARCHITECTURE.md` for runner specs.

## Architecture & Build State

See `docs/source-of-truth/` for full current state. Key files:
- **ARCHITECTURE.md** — Three-layer system, runners (ContentAgent + SyncAgent live), integrations, component status
- **MCP-TOOLS-INVENTORY.md** — All 17 MCP tools with signatures, routing rules, and categories
- **DROPLET-RUNBOOK.md** — Operational guide for droplet infrastructure
- **DATA-ARCHITECTURE.md** — 8 Notion DBs + 7 Postgres tables: schemas, field ownership, sync patterns
- **VISION-AND-DIRECTION.md** — Build phases, gaps, design principles

**Quick status:** Orchestrator + Content Agent (persistent ClaudeSDKClient, managed by lifecycle.py) live on droplet. State MCP (:8000) + Web Tools MCP (:8001). Postgres-as-queue for content pipeline. digest.wiki live. Sync Agent disabled (code in repo, not running).

---

## Build System Protocol

### Build Traces (MANDATORY)

Track implementation decisions with minimal context overhead using a rolling window + compaction pattern.

**IMPORTANT:** Enforced by a Stop hook — if you modify tracked files but don't update TRACES.md, the hook will prevent you from stopping and require you to update TRACES.md first.

#### Quick Reference

| File | Purpose | When to Read |
|------|---------|--------------|
| `TRACES.md` | Rolling window (~80 lines) | Start of every coding session + before closing |
| `traces/archive/milestone-N.md` | Full historical detail | Only when debugging or researching past decisions |

#### What Counts as an Iteration

An iteration is any work session where tracked files were modified.
Every session that changes something should leave a trace — what was done, why, and any decisions worth preserving.

NOT an iteration: Pure read-only sessions (research, Q&A, reviewing code without changes).

#### After Each Session (or before Session Close)

1. **Read `TRACES.md`** - find the last iteration number in "Current Work"
2. **Add iteration entry** to "Current Work" section (template above)
3. **If iteration 3, 6, 9...** -> run compaction process (see below)

#### Iteration Entry Template

```
### Iteration N - YYYY-MM-DD
**What:** One-sentence summary of what was done and why
**Changes:** `file1.md` (what changed), `file2.py` (what changed)
**Context:** Decisions made, discoveries, or reasoning worth preserving for future sessions
---
```

#### Compaction Process (Every 3 Iterations)

When you complete iteration 3, 6, 9, 12..., perform these steps:

1. **Create archive file** `traces/archive/milestone-N.md`:
   ```
   # Milestone N: [Focus Area]
   **Iterations:** X-Y | **Dates:** YYYY-MM-DD to YYYY-MM-DD

   ## Summary
   [2-3 sentences on what was accomplished]

   ## Key Decisions
   - Decision 1: Rationale
   - Decision 2: Rationale

   ## Iteration Details
   [Copy all 3 iteration entries from Current Work]
   ```

2. **Update Project Summary** in TRACES.md - add key decisions from this milestone
3. **Update Milestone Index** - add one row to the table
4. **Clear Current Work** - remove the 3 archived iterations, keep section header

#### When to Read Archive Files

Only read `traces/archive/` if:
- User asks about historical decisions
- Debugging requires understanding why something was built a certain way
- You need context from a specific past milestone

**Do NOT read archive files during normal iteration updates.**

### Branch Lifecycle

Every code change follows: CREATE > WORK > REVIEW > SHIP

- **CREATE** — `git checkout -b {feat|fix|research|infra}/slug` from main.
  Update Build Roadmap: Status = In Progress, Branch = branch name.
- **WORK** — Edit, commit, iterate. Keep changes scoped (1-2 files ideal, single concern).
- **REVIEW** — `git diff main..branch` — review all changes before merge. This is the quality gate.
- **SHIP** — `git checkout main && git merge branch && git branch -d branch`.
  Update Roadmap: Status = Verifying, Branch = clear.
- **VERIFY** — User tests outside Claude Code. On next session, SessionStart hook asks about
  Verifying items. Pass = Shipped. Fail = spawn fix/ item with Source = Verification Failure.

### Build Roadmap

- **Notion DB Data Source ID:** `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f`
- **Default View URL:** `view://4eb66bc1-322b-4522-bb14-253018066fef`

**Real-time updates (not batch-at-end):**
- Start working on item > update to In Progress immediately
- Ship (merge to main) > update to Verifying immediately
- Discover insight mid-session > create Insight item immediately
- Every code change must have a Roadmap item. If none exists, create one before starting.

**Auto-filled fields:** Priority, Technical Notes (medium depth — implementation approach,
key dependencies, why it matters), Parallel Safety (via 3-tier heuristic), Sprint#,
Source, Task Breakdown (populated when item moves to In Progress).

**Reading the Roadmap:**
```
notion-query-database-view with view_url: "view://4eb66bc1-322b-4522-bb14-253018066fef"
```

**Creating items (IMPORTANT — use exact emoji-prefixed values):**
```
notion-create-pages with parent: { data_source_id: "6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f" }
properties: {
  "Item": "Description",
  "Status": "💡 Insight",  // 💡 Insight | 📋 Backlog | 🎯 Planned | 🔨 In Progress | 🧪 Testing | ✅ Shipped | 🚫 Won't Do
  "Priority": "P1 - Next",  // P0 - Now | P1 - Next | P2 - Later | P3 - Someday
  "Epic": "Infrastructure",  // Content Pipeline v5 | Action Frontend | Knowledge Store | Multi-Surface | Meeting Optimizer | Always-On | Infrastructure
  "Source": "Session Insight",  // Session Insight | AI CoS Relevance Note | User Request | Bug/Regression | Architecture Decision | External Inspiration
  "Sprint#": [current sprint number],
  "T-Shirt Size": "S (1-3hr)",  // XS (< 1hr) | S (1-3hr) | M (3-8hr) | L (1-3 sessions) | XL (3+ sessions)
  "Technical Notes": "[auto-filled context]",
  "Parallel Safety": "🟢 Safe"  // 🟢 Safe | 🟡 Coordinate | 🔴 Sequential
}
```

### Sprint System

- Sprint# = current TRACES.md milestone being worked toward
- Sprint N = all work between Milestone N-1 and Milestone N
- Find current sprint: read TRACES.md > last milestone number + 1
- Items discovered during Sprint N get tagged Sprint# = N
- "What shipped in Sprint 3?" = query Roadmap: Sprint# = 3, Status = Shipped

### LEARNINGS.md Protocol

- When you try a method, it fails, and you succeed with a different method:
  immediately log the broken > working pair to LEARNINGS.md before continuing.
- Don't wait for session end. Capture at the moment of discovery.
- During TRACES.md milestone compaction (every 3 iterations):
  1. Review LEARNINGS.md
  2. Patterns confirmed 2+ times > graduate to CLAUDE.md anti-patterns
  3. Universal patterns (not project-specific) > also add to ~/.claude/CLAUDE.md
  4. Clear graduated entries from LEARNINGS.md


### Cross-Sync Session Protocol (MANDATORY)

Before ending any session on a synced project, update `.claude/sync/state.json`:

1. **Semantic fields** (via Edit tool):
   - `state.last_session.summary` — 1-2 sentences of what was accomplished
   - `state.current_tasks` — array of active work items
   - `state.recent_decisions` — array of `{decision, rationale, date}` objects
   - `state.next_session_priorities` — array of next steps

2. **Pending inbox** (via Edit tool): For substantive decisions or messages, add items to `state.pending_inbox[]`:
   ```json
   {"type": "decision|task|note|flag|research", "content": "message text"}
   ```
   Optional: `"context": {}`, `"priority": "normal|urgent|low"`. sync-push.sh generates full inbox messages automatically.

3. **Cross-project relevance**: If this session's work affects other synced projects, read `~/.claude/sync-registry.json` for project paths and write messages to target inboxes via sync-write.sh.
