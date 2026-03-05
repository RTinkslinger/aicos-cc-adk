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

**Architecture docs in `docs/architecture/` are canonical technical references.** See Architecture Direction below for summary; see those docs for full specs. For the full trust hierarchy and prior art checklist, see `docs/architecture/REPO-GUIDE.md`.

## Repository Structure

This is a **local-only git repo** (no remote). Used for branching/worktrees in parallel development.

| Directory | Purpose |
|-----------|---------|
| `CONTEXT.md` | Master context — read this first |
| `scripts/` | Operational scripts (YouTube extractor, content pipeline, action scorer, branch lifecycle CLI) |
| `skills/` | Historical skill files + Agent SDK system prompt reference (`ai-cos-v6-skill.md`) |
| `docs/` | All documentation by type (see `docs/README.md` for index) |
| `docs/architecture/` | Canonical architecture docs: BUILD-SYSTEM.md, architecture-v0.2, vision-v4 |
| `docs/notion/` | Notion operations guide + database schemas — read before any Notion tool call |
| `aicos-digests/` | **Separate git repo** (gitignored). Next.js 16 digest site, deployed at https://digest.wiki |
| `mcp-servers/` | Planned: ai-cos-mcp server (FastMCP Python) |
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

### MCP Server (planned)
```bash
cd mcp-servers/ai-cos-mcp && uv run server.py   # local dev
# Deploy: push to DO droplet via Tailscale
```

### Agent SDK Runners (planned)
```bash
cd agents/ && python -m agents.<runner_name>     # run individual agent
```

## Remote Repo Sync Discipline

This project (AI CoS) is a **local-only git repo**, but it contains sub-directories that are **separate git repos with GitHub remotes** (e.g., `aicos-digests/`, future repos in `mcp-servers/`). These are gitignored from the parent.

**Mandatory protocol for all remote-connected repos:**
1. **Pull before editing:** Always `git pull --ff-only origin main` before making any changes
2. **Push after editing:** Always `git push origin main` after committing
3. **Author identity:** Use `Aakash Kumar <hi@aacash.me>` — Vercel and other services may reject unknown authors

This applies everywhere these repos are touched: the droplet pipeline (`publishing.py`), `deploy.sh`, manual edits from Mac, and any future agents or services.

**Current remote repos:**
| Directory | Remote | Purpose |
|-----------|--------|---------|
| `aicos-digests/` | `github.com/RTinkslinger/aicos-digests` | digest.wiki Next.js site |

## Anti-Patterns

- Do NOT default to morning briefs, dashboards, or generic task automation
- Do NOT hallucinate Notion data — query it using IDs from CONTEXT.md
- Do NOT lose the action-optimizer framing by narrowing to only meeting optimization
- Do NOT design for desktop — Aakash lives on WhatsApp and mobile
- Do NOT treat meeting optimization as the whole system — it's one output of the action optimizer

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
2. **Update CLAUDE.md** → Only if structural changes happened: new capabilities, new IDs, new commands, new repo structure.
3. **Update MEMORY.md** → Only if stable cross-session patterns were discovered (not session-specific details).
4. **Update CONTEXT.md** → Only if domain knowledge changed: thesis threads, methodology, people, priorities. NOT for session bookkeeping.
5. **Notion sync** → Only if Notion-tracked data changed (Thesis Tracker, Build Roadmap).

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
Mac (daily 8:30 PM): youtube_extractor.py → queue/*.json
Analysis: queue/ → content analysis → PDF digests → Notion → review
Post-processing: queue/processed/
Back-propagation (daily 10:00 AM): Actions Queue Done → Content Digest "Actions Taken"
```

Key scripts: `youtube_extractor.py` (extraction), `content_digest_pdf.py` (PDF generation), `publish_digest.py` (JSON → Notion + digest site), `process_youtube_queue.py` (pipeline analysis), `action_scorer.py` (scoring model), `dedup_utils.py` (deduplication).

**Transition:** ContentAgent (Agent SDK runner) will replace the manual analysis step. See `docs/architecture/doc2-architecture-v0.2-enhanced.md` for runner specs.

## Architecture Direction

The AI CoS is evolving from a session-based build system to a persistent, autonomous architecture:

**Three-layer system:**
- **Observation Layer** — Signal sources (YouTube, Granola, Email, Calendar, screenshots, etc.) produce normalized Signals
- **Intelligence Layer** — Agent SDK runners + MCP tools reason over data, score actions, learn from preferences
- **Interface Layer** — Claude mobile, digest.wiki, Notion, WhatsApp (future)

**ai-cos-mcp server** (FastMCP Python, planned for `mcp-servers/`):
- Key tools: `cos_load_context`, `cos_score_action`, `cos_get_preferences`, `cos_propose_actions`
- Deployed to DO droplet, connected from all Claude surfaces

**Agent SDK runners** (5 narrow specialists):
- PostMeetingAgent (Granola → IDS updates → actions)
- ContentAgent (content queue → analysis → digests → actions)
- OptimiserAgent (scoring models → ranked lists → gap analysis)
- IngestAgent (screenshots, URLs → Network/Companies DB)
- SyncAgent (Notion ↔ Postgres consistency)

**Preference Store** — `action_outcomes` table (Postgres): every accept/reject with scoring factor snapshots. Injected into all reasoning sessions for calibration. The compounding mechanism.

**Cloud infrastructure:** DO droplet ($12/mo), Postgres, Tailscale for secure networking.

**Build phases:**
1. MCP server + Preference Store foundation
2. Action Frontend on digest.wiki (accept/dismiss UX)
3. Cloud infrastructure (Postgres, sync worker)
4. Agent SDK Runners (SyncAgent → ContentAgent → PostMeetingAgent → IngestAgent → OptimiserAgent)
5. WhatsApp integration (proactive push)

**Full specs:** `docs/architecture/doc2-architecture-v0.2-enhanced.md` (architecture), `docs/architecture/doc3-vision-document.md` (vision), `docs/architecture/BUILD-SYSTEM.md` (historical build system reference)

## Current Build State

**What works today:**
- Content Pipeline v4 (YouTube → analysis → digests → Notion → Actions Queue)
- digest.wiki (Next.js 16, live at https://digest.wiki, WhatsApp-shareable)
- Notion as full data layer (8 databases, cross-referenced)
- IDS methodology fully encoded in CONTEXT.md
- Scoring models defined (`action_scorer.py`, 172 lines)
- Parallel development system (branch lifecycle CLI, worktrees, file safety classification)
- 20 portfolio companies deep-researched, 76 actions generated
- 6 active thesis threads tracked in Notion Thesis Tracker

**What's being built next:**
1. Custom ai-cos-mcp server (FastMCP Python on DO droplet)
2. Preference Store (action_outcomes table in Postgres)
3. Action Frontend on digest.wiki (accept/dismiss)
4. Agent SDK runners (5 specialists)
5. Content Pipeline v5 (full portfolio coverage, semantic matching, multi-source)

---

## Build Traces Protocol (MANDATORY)

Track implementation decisions with minimal context overhead using a rolling window + compaction pattern.

**IMPORTANT:** Enforced by a Stop hook — if you modify code files but don't update TRACES.md, you will receive a reminder. Also Step 1 of the Session Close Checklist.

### Quick Reference

| File | Purpose | When to Read |
|------|---------|--------------|
| `TRACES.md` | Rolling window (~80 lines) | Start of every coding session + before closing |
| `traces/archive/milestone-N.md` | Full historical detail | Only when debugging or researching past decisions |

### What Counts as an Iteration

An iteration is a work session where you:
- Write or modify code files (not specs/docs)
- Complete tasks from the phase plan
- Make architectural or implementation decisions

NOT an iteration: Pure research, Q&A, planning, or documentation-only changes.

### After Each Coding Session (or before Session Close)

1. **Read `TRACES.md`** - find the last iteration number in "Current Work"
2. **Add iteration entry** to "Current Work" section (template below)
3. **If iteration 3, 6, 9...** → run compaction process (see below)

### Iteration Entry Template (Concise ~15 lines)

```markdown
### Iteration N - YYYY-MM-DD
**Phase:** Phase X: Name
**Focus:** Brief description

**Changes:** `file.py` (what), `other.py` (what)
**Decisions:** Key decision → rationale
**Next:** What's next

---
```

### Compaction Process (Every 3 Iterations)

When you complete iteration 3, 6, 9, 12..., perform these steps:

1. **Create archive file** `traces/archive/milestone-N.md`:
   ```markdown
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

### When to Read Archive Files

Only read `traces/archive/` if:
- User asks about historical decisions
- Debugging requires understanding why something was built a certain way
- You need context from a specific past milestone

**Do NOT read archive files during normal iteration updates.**
