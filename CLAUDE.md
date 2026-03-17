# CLAUDE.md

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

**`docs/source-of-truth/` is the single canonical reference folder** — 8 files covering system state, architecture, data, MCP tools, vision, capabilities, methodology, and entity schemas. See `docs/source-of-truth/README.md` for the index. Read these before building anything that touches infrastructure, data, or system design. For the trust hierarchy and prior art checklist, see `docs/architecture/REPO-GUIDE.md`.

## Repository Structure

**GitHub remote:** `https://github.com/RTinkslinger/aicos-cc-adk.git`

| Directory | Purpose |
|-----------|---------|
| `CONTEXT.md` | Master context — read this first |
| `scripts/` | Operational scripts (YouTube extractor, content pipeline, action scorer, branch lifecycle CLI) |
| `[Archive] Cowork Skills/` | Archived Cowork-era skill files (v2-v6). Reference only — not used in CC. |
| `docs/` | All documentation by type (see `docs/README.md` for index) |
| `docs/architecture/` | Historical architecture narratives — deeper detail, may have drifted. See `docs/source-of-truth/` for canonical reference. |
| `docs/notion/` | Notion operations guide + database schemas — read before any Notion tool call |
| `aicos-digests/` | **Separate git repo** (gitignored). Next.js 16 digest site, deployed at https://digest.wiki |
| `mcp-servers/agents/` | v3 agents monorepo: orchestrator, content agent, state MCP, web tools MCP. Deploy via `deploy.sh`. |
| `Archives/` | Superseded code (v1 mcp-servers, old Cowork Skills) — reference only |
| `portfolio-research/` | Per-company deep research files (20 companies) |
| `queue/` | Content Pipeline queue — YouTube extraction JSONs |
| `digests/` | PDF digest outputs |
| `Training Data/` | IDS methodology training samples (emails, docs) |

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

## Anti-Patterns

- Do NOT default to morning briefs, dashboards, or generic task automation
- Do NOT hallucinate Notion data — query it using IDs from CONTEXT.md
- Do NOT lose the action-optimizer framing by narrowing to only meeting optimization
- Do NOT design for desktop — Aakash lives on WhatsApp and mobile
- Do NOT treat meeting optimization as the whole system — it's one output of the action optimizer

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
- **SYSTEM-STATE.md** — Infrastructure: droplet, Postgres (7 tables), Cloudflare Tunnel, Tailscale, crons, endpoints
- **DATA-ARCHITECTURE.md** — 8 Notion DBs + 7 Postgres tables: schemas, field ownership, sync patterns
- **VISION-AND-DIRECTION.md** — Build phases, gaps, design principles

**Quick status:** Orchestrator + Content Agent (persistent ClaudeSDKClient, managed by lifecycle.py) live on droplet. State MCP (:8000) + Web Tools MCP (:8001). Postgres-as-queue for content pipeline. digest.wiki live. Sync Agent disabled (code in repo, not running).

---

## Build System Protocol

### Build Traces (MANDATORY)

Track implementation decisions with minimal context overhead using a rolling window + compaction pattern.

**IMPORTANT:** Enforced by a Stop hook — if you modify code files but don't update TRACES.md, you will receive a reminder.

#### Quick Reference

| File | Purpose | When to Read |
|------|---------|--------------|
| `TRACES.md` | Rolling window (~80 lines) | Start of every coding session + before closing |
| `traces/archive/milestone-N.md` | Full historical detail | Only when debugging or researching past decisions |

#### What Counts as an Iteration

An iteration is a work session where you:
- Write or modify code files (not specs/docs)
- Complete tasks from the phase plan
- Make architectural or implementation decisions

NOT an iteration: Pure research, Q&A, planning, or documentation-only changes.

#### After Each Coding Session (or before Session Close)

1. **Read `TRACES.md`** - find the last iteration number in "Current Work"
2. **Add iteration entry** to "Current Work" section (template below)
3. **If iteration 3, 6, 9...** -> run compaction process (see below)

#### Iteration Entry Template (Concise ~15 lines)

```
### Iteration N - YYYY-MM-DD
**Phase:** Phase X: Name
**Focus:** Brief description

**Changes:** `file.py` (what), `other.py` (what)
**Decisions:** Key decision -> rationale
**Next:** What's next

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

### Subagent Protocol

Every Agent call must include 4 blocks:

1. **CONSTRAINTS** — What the subagent cannot do: no MCP tools, no git operations,
   no network access, no files outside the allowlist below.
2. **FILE ALLOWLIST** — Every file the subagent may Read/Edit/Write, explicitly listed.
   "Do NOT touch any files not on this list."
3. **TASK** — Specific instructions with enough context to work independently.
4. **SUCCESS CRITERIA** — What "done" looks like so the subagent can self-validate.

**Parallel delegation pattern (for breaking big changes into multiple subagents):**
1. DECOMPOSE — Analyze the change, identify independent subtasks
2. MAP FILES — Assign each subtask an explicit file allowlist with ZERO overlap
3. PARALLEL SPAWN — Multiple Agent calls, each with all 4 blocks
4. REVIEW — Main session reviews all outputs for consistency
5. COMMIT — Main session commits the combined changes

### File Classification (Parallel Safety)

Before parallel work (multi-tab or multi-subagent), classify target files:
- **Safe** — New files, isolated files (0-1 importers), docs, research
- **Coordinate** — Shared files with 2-4 importers across the codebase
- **Sequential** — Config files, shared type definitions, files with 5+ importers

**Auto-classification heuristic:**
1. Pattern match on item description ("new file" = Safe, "schema change" = Sequential)
2. If ambiguous: Grep for imports/references to target file, count fan-out
3. Check known critical files list below

**Known critical (Sequential) files for this project:**
- CLAUDE.md
- CONTEXT.md
- TRACES.md

Task safety = worst classification of any file it touches. Default = Coordinate if uncertain.
When a parallel edit causes a merge conflict, add that file to the critical files list above.

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
