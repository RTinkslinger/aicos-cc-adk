# AI CoS Build System — Complete Reference

*Version 1.0.0 | Session 040 | March 2026*

This document is the exhaustive reference for the AI Chief of Staff build system — the full CI/CD pipeline, parallel development architecture, session lifecycle, audit framework, and deployment infrastructure built over 39+ sessions. It describes how code gets written, tested, merged, deployed, and maintained across a multi-surface AI agent system.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Execution Environment](#2-execution-environment)
3. [Git Infrastructure & Branch Lifecycle](#3-git-infrastructure--branch-lifecycle)
4. [Parallel Development Architecture](#4-parallel-development-architecture)
5. [Subagent System](#5-subagent-system)
6. [Deployment Pipeline](#6-deployment-pipeline)
7. [Session Lifecycle Management](#7-session-lifecycle-management)
8. [Behavioral Audit Framework](#8-behavioral-audit-framework)
9. [Layered Persistence Architecture](#9-layered-persistence-architecture)
10. [Skill Packaging & Distribution](#10-skill-packaging--distribution)
11. [Build Roadmap Workflow](#11-build-roadmap-workflow)
12. [Content Pipeline (CI for Content)](#12-content-pipeline-ci-for-content)
13. [Scheduled Automation](#13-scheduled-automation)
14. [Operational Scripts Inventory](#14-operational-scripts-inventory)
15. [Known Constraints & Anti-Patterns](#15-known-constraints--anti-patterns)

---

## 1. Architecture Overview

> **CC REVIEW:** Session numbering DROPPED for Claude Code. IDS principle CARRIES FORWARD. Self-documenting covered via TRACES.md. Multi-surface: Cowork still used but NOT for AI CoS project edits — Claude Code + Claude.ai are the build surfaces.

The AI CoS build system is not a traditional CI/CD pipeline. It is a **session-based development system** where an AI agent (Claude, operating across Cowork desktop, Claude Code CLI, and Claude.ai web/mobile) is the primary developer, working within a sandboxed Linux VM with controlled access to user files and external services via MCP (Model Context Protocol) tools.

### Core Design Principles

- ~~**Session = unit of work.** Each conversation with Claude is a numbered session (001–039+). Sessions produce code, docs, and Notion state changes. Session state persists via checkpoint files and iteration logs.~~ **DROPPED for Claude Code.**
- **IDS (Increasing Degrees of Sophistication).** The system grows incrementally — each session adds capabilities on top of what exists. No big-bang rewrites. **CARRY FORWARD.**
- **Self-documenting.** The system maintains its own documentation through mandatory session-end routines, behavioral audits, and persistence layer updates. **Covered via TRACES.md protocol.**
- **Multi-surface coherence.** The same AI CoS skill runs on 3 surfaces (Cowork, Claude Code, Claude.ai). Each surface has different tool access, but shares the same Notion databases as ground truth.

### System Topology

```
┌─────────────────────────────────────────────────────────────┐
│  COWORK (Desktop App — Linux VM Sandbox)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │ Bash     │  │ Read/    │  │ MCP Tools (via Mac host): │  │
│  │ Subagents│  │ Write/   │  │ • osascript (git, deploy) │  │
│  │          │  │ Edit     │  │ • Notion (read/write DBs) │  │
│  └──────────┘  └──────────┘  │ • Gmail, Calendar, Granola│  │
│                               │ • Vercel, WebSearch       │  │
│                               └──────────────────────────┘  │
│  Mounted: /mnt/Aakash AI CoS/ ←→ Mac: ~/Claude Projects/   │
└─────────────────────────────────────────────────────────────┘
        │                              │
        │ osascript bridge             │ MCP APIs
        ▼                              ▼
┌──────────────────┐         ┌──────────────────┐
│  Mac Host         │         │  External Services│
│  • Git repo (local)│        │  • Notion DBs     │
│  • launchd crons  │         │  • GitHub (remote) │
│  • yt CLI         │         │  • Vercel CDN      │
│  • homebrew tools │         │  • Google (Cal/Mail)│
└──────────────────┘         └──────────────────┘
```

---

## 2. Execution Environment

> **CC REVIEW:** ENTIRELY IRRELEVANT for Claude Code. Claude Code runs natively on Mac — no sandbox, no osascript bridge, no path mapping. Skip this entire section.

### The Sandbox (Cowork Linux VM)

Claude runs inside a lightweight Ubuntu 22 VM. This sandbox provides:

**HAS access to:**
- Bash shell, Python 3, Node.js, npm
- File read/write/edit on the mounted workspace folder
- MCP tool calls to external services (Notion, Gmail, Calendar, Vercel, etc.)
- Spawning Bash subagents for parallel file work

**Does NOT have:**
- Outbound network access (no `curl`, `wget`, `pip install` from PyPI, `git push`)
- Direct access to Mac filesystem (`/Users/Aakash/...` paths fail)
- Access to Mac-native applications
- File deletion on mounted `/mnt/` paths (requires special permission)

### The osascript Bridge

All operations that need the Mac host or outbound network use the `osascript` MCP tool, which executes AppleScript on the user's Mac:

```
osascript: do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS' && <COMMAND> 2>&1"
```

Common bridge uses:
- `git push origin main` — Push to GitHub
- `git checkout -b <branch>` — Branch operations
- `./scripts/branch_lifecycle.sh <cmd>` — Lifecycle CLI
- `curl` / `wget` — Any outbound HTTP
- `yt` — YouTube transcript extraction CLI

### Path Mapping

| Context | Path |
|---------|------|
| Sandbox (Cowork VM) | `/sessions/<id>/mnt/Aakash AI CoS/` |
| Mac host | `/Users/Aakash/Claude Projects/Aakash AI CoS/` |
| Git repo root | Same as Mac host path |
| Digest site (sub-repo) | `aicos-digests/` (has own `.git`, excluded from parent via `.gitignore`) |

### Critical Environment Rules

| Task | ❌ BROKEN (never try) | ✅ WORKING (use this) |
|------|----------------------|----------------------|
| Push to GitHub | `git push` from sandbox Bash | `osascript` MCP on Mac host |
| Any outbound HTTP | `curl`/`wget` from sandbox | `osascript` MCP or MCP tools (Vercel, etc.) |
| Read Mac-native paths | `ls /Users/Aakash/...` | Glob/Read on mounted `/mnt/` path |
| List directory contents | `Read` tool on a directory | `ls` via Bash |
| Edit a file | `Edit` without reading first | Always `Read` first, then `Edit` |
| Git operations on parent | `git diff` in `/mnt/Aakash AI CoS/` | Run git inside `aicos-digests/` (the actual git repo with remote) or via osascript |

---

## 3. Git Infrastructure & Branch Lifecycle

> **CC REVIEW:** Branch naming convention CARRIES FORWARD. 6-step lifecycle SIMPLIFIED to 4-step (CREATE → WORK → REVIEW → SHIP) + VERIFY step for user testing. `branch_lifecycle.sh` DROPPED — Claude Code does git natively. Worktrees via native `EnterWorktree`. osascript orchestration DROPPED. Notion Build Roadmap integration CARRIES FORWARD as real-time updates (not batch-at-end). Plugin is the target implementation vehicle.

### Repository Structure

Two git repositories coexist:

1. **Local-only repo** (AI CoS root) — `~/Claude Projects/Aakash AI CoS/`
   - No remote. Local branching/worktrees for parallel development.
   - `main` = stable baseline.
   - `aicos-digests/` excluded via `.gitignore`.

2. **GitHub repo** (Digest site) — `aicos-digests/`
   - Remote: GitHub. Push triggers CI/CD.
   - Single deploy path: push to `main` → GitHub Action → Vercel.

### Branch Naming Convention

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feat/` | New feature | `feat/content-pipeline-v5-scoring` |
| `fix/` | Bug fix | `fix/dedup-logic` |
| `research/` | Research task (always 🟢 Safe) | `research/agent-sdk-architecture` |
| `infra/` | Infrastructure | `infra/parallel-dev-phase1` |

### The 6-Step Branch Lifecycle

Every code change follows a standardized 6-step lifecycle, managed by the CLI at `scripts/branch_lifecycle.sh`:

```
Step 1: CREATE ─→ Step 2: WORK ─→ Step 3: COMPLETE ─→ Step 4: REVIEW ─→ Step 5: MERGE ─→ Step 6: CLOSE
  (automated)      (manual)        (manual)            (automated)        (automated)       (automated)
```

**Step 1: CREATE** — Create and checkout a new branch from `main`.
```bash
./scripts/branch_lifecycle.sh create feat/my-feature
```
Side effects: Update Build Roadmap in Notion → Branch = branch name, Status = 🔨 In Progress.

**Step 2: WORK** — Make changes, commit to branch. Scoped: 1-2 files, <30 min.
```bash
git add <files> && git commit -m "<message>"
```

**Step 3: COMPLETE** — All work done. Update Roadmap: Status = 🧪 Testing.

**Step 4: REVIEW** — Coordinator reviews diff vs main.
```bash
./scripts/branch_lifecycle.sh diff feat/my-feature
```
Shows stat summary + full diff. No auto-merge — human/coordinator must approve.

**Step 5: MERGE** — Merge branch to main.
```bash
./scripts/branch_lifecycle.sh merge feat/my-feature
```

**Step 6: CLOSE** — Delete branch, update Roadmap: Branch = clear, Status = ✅ Shipped.
```bash
./scripts/branch_lifecycle.sh close feat/my-feature
```

### Lifecycle CLI Commands

| Command | Description | Interactive? |
|---------|-------------|-------------|
| `create <branch>` | Create + checkout branch | No |
| `status` | Show branches + worktrees + HEAD | No |
| `diff <branch>` | Review changes vs main | No |
| `merge <branch>` | Merge to main | No |
| `close <branch>` | Delete branch | No |
| `full <branch>` | Steps 4→5→6 with confirmation | Yes — DON'T use via osascript |
| `full-auto <branch>` | Steps 4→5→6 without prompting | No — USE THIS via osascript |
| `full <branch> --yes` | Same as full-auto | No |
| `worktree-create <branch>` | Create worktree + branch | No |
| `worktree-clean <branch>` | Merge + remove worktree + delete branch | No |
| `worktree-list` | List active worktrees | No |

### Git Worktrees for Parallel Development

Worktrees enable true parallel development — multiple branches checked out simultaneously in separate directories:

```bash
# Create worktree (from main)
./scripts/branch_lifecycle.sh worktree-create feat/feature-a
# Creates: .worktrees/feat-feature-a/  (slug = branch name with / → -)

# Work in worktree
cd .worktrees/feat-feature-a/
# make changes, commit...

# Clean up (merge + remove worktree + delete branch)
cd ../..
./scripts/branch_lifecycle.sh worktree-clean feat/feature-a
```

Worktree paths: `<project-root>/.worktrees/<slug>/` where slug = branch name with `/` replaced by `-`.

### Orchestration Pattern (Cowork)

All git operations happen via `osascript` on the Mac host. Subagents handle file edits only. The main session orchestrates the handoff:

**Pattern A: Single Branch + Subagent**
```
1. CREATE — main session via osascript
2. WORK — spawn Bash subagent for file edits
3. COMMIT — main session via osascript
4-6. REVIEW + MERGE + CLOSE — main session via osascript (full-auto)
```

**Pattern B: Worktree + Parallel Subagents**
```
1. CREATE WORKTREES — main session via osascript (multiple)
2. PARALLEL WORK — spawn multiple Bash subagents, each in own worktree
3. COMMIT EACH — main session via osascript per worktree
4-6. CLEAN EACH — main session via osascript (worktree-clean per branch)
```

---

## 4. Parallel Development Architecture

### File Classification System

Every file in the project has a parallel safety classification that determines how it can be worked on:

| Safety | Symbol | Rule | Example Files |
|--------|--------|------|---------------|
| **SAFE_PARALLEL** | 🟢 | Any number of agents can work simultaneously | New docs, research files, new scripts |
| **NEEDS_COORDINATION** | 🟡 | Multiple agents OK, but each must own a specific section | `CONTEXT.md`, `FOLDER-INDEX.md` |
| **SEQUENTIAL_ONLY** | 🔴 | One agent at a time. Queue all work. | `ai-cos-v6-skill.md`, `CLAUDE.md`, `v6-artifacts-index.md`, `layered-persistence-coverage.md`, `package.json` |

**Classification heuristic:** List all files a task will touch → check each against the table → task safety = WORST classification of any file it touches. Default to 🟡 if uncertain.

### Six Operational Rules

1. **Never parallel-edit 🔴 files.** Two agents editing simultaneously = guaranteed conflict.
2. **🟡 files use section ownership.** Each agent assigned a specific section, no overlap.
3. **Coordinator reviews ALL diffs before merge.** No auto-merge from subagents.
4. **Check Parallel Safety before starting any Build Roadmap item.** Query Roadmap → check item's safety → if 🔴, ensure no other 🔴 work on same files is in progress.
5. **Small tasks > big sessions.** Sweet spot: 1-2 files, <30 min, single commit.
6. **Research tasks are always 🟢.** Any task producing only new docs is inherently parallelizable.

### 3-Layer Enforcement Architecture

**Layer 1: Prompt Allowlist** — Every subagent prompt includes an explicit list of files it may edit. "Do NOT edit any other files." Prevents scope creep.

**Layer 2: Pre-Edit Self-Check** — Before any Edit/Write call, the agent checks: "Is this file in my allowlist? Is it 🔴 and is someone else working on it?" If violated, abort and report.

**Layer 3: Coordinator Diff Review** — Main session runs `git diff main..<branch>` after subagent completes. Reviews every changed file. Rejects unexpected changes.

**Layer 4 (Future): PreToolUse Hook** — Automated enforcement via Claude Code hooks. Not yet implemented.

### Parallel Workflow Example

```
Session Start
  │
  ├── Query Build Roadmap (3 sec)
  │
  ├── Pick up 2 items:
  │     Item A: feat/scoring-model (🟢 — new script)
  │     Item B: fix/dedup-logic (🟢 — existing script, isolated)
  │
  ├── osascript: worktree-create feat/scoring-model
  ├── osascript: worktree-create fix/dedup-logic
  │
  ├── Spawn Subagent A → works in .worktrees/feat-scoring-model/
  ├── Spawn Subagent B → works in .worktrees/fix-dedup-logic/
  │     (parallel execution)
  │
  ├── Both complete → coordinator reviews diffs
  │
  ├── osascript: worktree-clean feat/scoring-model
  ├── osascript: worktree-clean fix/dedup-logic
  │
  └── Update Build Roadmap: both → ✅ Shipped
```

---

## 5. Subagent System

### What Subagents Are

Bash subagents are lightweight agents spawned via `Task(subagent_type="Bash")`. They execute file operations in isolation and return results to the main session.

### Tool Inventory

| Tool | Available? |
|------|-----------|
| Bash, Read, Edit, Write, Glob, Grep | ✅ Yes |
| MCP tools (osascript, Notion, Vercel, Gmail, etc.) | ❌ No |
| Outbound network (curl, wget, git push) | ❌ No |
| File deletion on mounted `/mnt/` paths | ❌ No |
| CLAUDE.md, skills, conversation history | ❌ Not auto-loaded |

### Spawning Checklist

Before every `Task(subagent_type="Bash")` call:

| Step | Action |
|------|--------|
| 1. Check template library | Does `scripts/subagent-prompts/` have a template? Use it. |
| 2. Include constraints block | Every prompt MUST start with the SUBAGENT CONSTRAINTS block. |
| 3. Include file allowlist | List EVERY file the subagent may edit + "Do NOT edit any other files." |
| 4. Include sandbox rules | If task touches mounted paths, network, or git: include relevant rules. |
| 5. Plan MCP hand-offs | List what main session must do after (Notion writes, osascript, present_files). |
| 6. Verify scope | Is the subagent doing ONLY file work? If it needs MCP tools, split the task. |

### Template Library (`scripts/subagent-prompts/`)

| Template | Purpose | Used By |
|----------|---------|---------|
| `session-close-file-edits.md` | Steps 2, 3, 5 of session close checklist | Session end |
| `skill-packaging.md` | Package `.skill` ZIP file | Session end (Step 6) |
| `general-file-edit.md` | Any 🔴 sequential file edit | On-demand |
| `branch-workflow.md` | Main session reference for branch + subagent orchestration | Parallel dev |

### Template Structure

Every template follows this structure:

```
# SUBAGENT CONSTRAINTS (mandatory header)
Tool inventory, critical rules, what the subagent CANNOT do.

# TASK
Specific instructions with placeholder variables ({{SESSION_NUMBER}}, etc.)

# ALLOWED FILES
Explicit list of files that may be edited.

# HAND-OFF
What the main session must do after subagent completes.
```

### Anti-Pattern

**Never** spawn a subagent with a bare task description like "update CONTEXT.md with session info." Always include the full constraints block, file allowlist, and hand-off protocol. Subagents inherit nothing — no CLAUDE.md, no skills, no MCP tools, no conversation history.

---

## 6. Deployment Pipeline

### Digest Site (aicos-digests)

The only actively deployed artifact. Architecture:

```
Cowork Session
  │
  ├── Edit files in /mnt/Aakash AI CoS/aicos-digests/
  ├── Bash: cd aicos-digests/ && git add . && git commit -m "..."
  │
  ├── osascript MCP:
  │     do shell script "cd '/Users/Aakash/Claude Projects/Aakash AI CoS/aicos-digests' && git push origin main 2>&1"
  │
  ├── GitHub receives push
  │     └── GitHub Action triggers
  │           └── Vercel CLI deploys to production
  │
  └── Live at https://digest.wiki (~90 sec end-to-end)
```

**Key constraints:**
- Single deploy path. No deploy hooks, no manual Vercel CLI, no alternative methods.
- `git push` MUST happen via osascript on Mac host (sandbox has no network).
- `aicos-digests/` has its own `.git` — separate from the parent AI CoS repo.
- Parent repo's `.gitignore` excludes `aicos-digests/`.

### Digest Site Stack

- **Framework:** Next.js 16 (App Router)
- **Hosting:** Vercel (production)
- **Domain:** digest.wiki (custom domain → Vercel)
- **Content:** Static JSON files in `src/data/` → SSG pages at `/d/{slug}`
- **OG Tags:** Dynamic per-digest for WhatsApp sharing

### Content-to-Deploy Flow

```
YouTube transcript (via yt CLI / launchd)
  → queue/processed/*.json (extraction output)
  → scripts/process_youtube_queue.py (analysis + thesis/portfolio matching)
  → Notion Content Digest DB (structured record)
  → scripts/publish_digest.py (JSON → aicos-digests/src/data/ + osascript git push)
  → GitHub Action → Vercel → https://digest.wiki/d/{slug}
  → Digest URL written back to Notion Content Digest DB
```

---

## 7. Session Lifecycle Management

### Session Numbering

Sessions are numbered sequentially (001, 002, ... 039, 040). Each session produces:

- An iteration log at `docs/iteration-logs/session-NNN-*.md`
- Updates to `CONTEXT.md` (session entry in history)
- Updates to `CLAUDE.md` (last session reference)
- Optionally: checkpoint files at `docs/session-checkpoints/`

### Mid-Session Checkpoints

Triggered by: "checkpoint", "save state", "save progress"

Action: Write a pickup file to `docs/session-checkpoints/` capturing:
- What's done
- What's in progress
- What's pending
- Key files modified

Target: Under 60 seconds.

### Mandatory 8-Step Session Close Checklist

Triggered by: "close session", "end session", "wrap up", "session done"

| Step | Action | Executor |
|------|--------|----------|
| 1a | Write iteration log to `docs/iteration-logs/` | Bash subagent |
| 1b | Write session checkpoint (pickup file) | Bash subagent |
| 1c | Run behavioral audit (JSONL analysis) | Bash subagent |
| 2 | Update `CONTEXT.md` with session entry | Bash subagent |
| 3 | Update `CLAUDE.md` last session reference | Bash subagent |
| 4 | Sync thesis threads to Notion Thesis Tracker | Main session (MCP) |
| 5 | Update `v6-artifacts-index.md` if versions bumped | Bash subagent |
| 6 | Package new `.skill` ZIP if skill changed | Bash subagent |
| 7 | Confirm all steps complete | Main session |
| 8 | Note connections to thesis/pipeline/actions | Main session |

**Critical rule:** Steps 2, 3, and 5 involve 🔴 sequential files. Use subagents to avoid context compaction death spiral (discovered session 035). Main session stays lean for MCP calls and coordination only.

---

## 8. Behavioral Audit Framework

### Purpose

The behavioral audit system ensures the AI CoS follows its own rules. It analyzes session transcripts against all reference files and produces compliance reports.

### Audit Triggers

- **Mandatory:** Step 1c of every session close
- **On-demand:** "audit session", "behavioral audit", "check my rules", "how did we do"
- **Periodic:** Every 5 sessions, a full persistence audit

### Audit Categories (9 Types)

| Category | What It Checks |
|----------|----------------|
| A. Sandbox Compliance | No curl/wget/git-push from sandbox, osascript for outbound, path mapping |
| B. Notion Method Compliance | notion-mastery skill loaded, view:// URLs used, property formatting correct |
| C. Session Lifecycle | Close checklist followed, checkpoint files written, iteration logs complete |
| D. Parallel Dev Compliance | File classification respected, allowlists included, coordinator diff review done |
| E. Subagent Template Usage | Templates from library used, constraints block included, hand-off protocol followed |
| F. Skill Management | .skill = ZIP, version field present, description ≤1024 chars, artifacts index updated |
| G. Action Optimizer Framing | "What's Next?" framing maintained, not narrowed to only meetings |
| H. Error Recovery | Broken methods tried only once before switching to working methods |
| I. Persistence Compliance | All 6 layers checked for consistency, no drift across artifacts |

### Correction Loop Detection

The audit detects 9 types of trial-and-error loops (patterns where the agent tries a broken method, fails, then finds the working method):

| Pattern | Severity | Example |
|---------|----------|---------|
| Sandbox network attempt | MEDIUM | Tried `curl` → failed → used osascript |
| Raw API Notion call | HIGH | Tried `API-query-data-source` → failed → used `notion-query-database-view` |
| Unqualified tool name | LOW | Tried `mcp__abc__notion-fetch` → failed → detected by suffix |
| Property format error | MEDIUM | Tried `"Due Date": "2026-03-15"` → failed → used `"date:Due Date:start"` |
| Git in sandbox | MEDIUM | Tried `git push` → failed → used osascript |
| Missing skill load | HIGH | Made Notion call without loading notion-mastery first |
| Parallel safety violation | HIGH | Edited 🔴 file without checking if in use |
| Missing allowlist | MEDIUM | Spawned subagent without file allowlist |
| Schema assumption | MEDIUM | Assumed property name → wrong → had to fetch schema |

### Audit Output

The audit produces a structured report in `docs/audit-reports/` with:
- Session metadata (number, date, duration)
- Per-category compliance status (PASS/FAIL with evidence)
- Correction loops detected (with line numbers from JSONL)
- Persistence upgrade recommendations
- New rules to add

---

## 9. Layered Persistence Architecture

### The Problem

AI agent conversations have finite context windows. Instructions that live in only one place get lost when context compresses. Rules that caused errors in sessions 2-6 were still being violated in sessions 17-18 because they only existed in CLAUDE.md.

### The Solution: 6-Layer Redundancy

Every critical instruction is stored in multiple layers. The more sessions a rule has caused errors, the more layers it needs.

| Layer | Artifact | Max Size | Surface | When Loaded |
|-------|----------|----------|---------|-------------|
| L0a | Global Instructions | ~2000 chars | All Claude surfaces | Every conversation start |
| L0b | User Preferences | ~2000 chars | All Claude surfaces | Every conversation start |
| L1 | Claude.ai Memory | 500 chars/entry × 18 entries | Claude.ai only | Every conversation start |
| L2 | ai-cos Skill (v6.2.0) | Unlimited | All (when loaded) | On trigger words |
| L3 | CLAUDE.md | Unlimited | Cowork + Claude Code | Auto-loaded per project |
| L4 | CONTEXT.md | Unlimited | Cowork + Claude Code | Read on demand |

### Coverage Map

The coverage map at `docs/persistence/layered-persistence-coverage.md` tracks 23 instruction sets across all 6 layers:

- Each instruction has a minimum required layer count (based on violation history)
- ≥2 session violations → needs 3+ layer coverage
- Violation history is tracked per rule per session

### Persistence Audit Protocol (Every 5 Sessions)

1. Review iteration logs for patterns of drift/trial-and-error
2. Grep for known violation patterns
3. Instructions that keep failing → upgrade layer count
4. Update coverage map
5. Update affected artifacts

### Version Management

All artifacts are version-tracked in `docs/persistence/v6-artifacts-index.md`:

| Artifact | Current Version | Format |
|----------|----------------|--------|
| ai-cos Skill | v6.2.0-s037 | `.skill` ZIP (SKILL.md inside) |
| notion-mastery Skill | v1.2.0 | `.skill` ZIP |
| User Preferences | v6.0.0-s026 | Claude.ai settings |
| Memory Entries | v6.2.0-s037 | 18 × 500-char entries |
| CLAUDE.md | v6.2.0-s039 | Project file |
| CONTEXT.md | v6.2.0-s039 | Project file |
| Global Instructions | v6.0.0-s026 | Claude.ai settings |
| System Vision | v3.0.0 | Reference doc |

**Bump protocol:** When bumping any artifact, check ALL artifacts for consistency. Use `v6-artifacts-index.md` as the checklist.

---

## 10. Skill Packaging & Distribution

### What Skills Are

Skills are instruction bundles that teach Claude how to perform specific tasks. They're loaded on-demand via trigger words in user messages.

### Skill File Format

A `.skill` file is a **ZIP archive** (not plain text) containing a directory with a `SKILL.md` file:

```
my-skill.skill (ZIP)
  └── my-skill/
       └── SKILL.md
```

### SKILL.md Frontmatter Requirements

```yaml
---
name: ai-cos
version: 6.2.0
description: "Aakash Kumar's AI Chief of Staff — action optimizer..." (≤1024 characters)
---
```

- `version` field is REQUIRED (Cowork can't track without it)
- `description` MUST be ≤1024 characters (Cowork rejects longer)

### Packaging Recipe

```bash
# 1. Create temp directory structure
mkdir -p /tmp/pkg/ai-cos

# 2. Copy source skill file
cp skills/ai-cos-v6-skill.md /tmp/pkg/ai-cos/SKILL.md

# 3. Package as ZIP
cd /tmp/pkg && zip -r /path/to/output/ai-cos-v6.2.0.skill ai-cos/

# 4. Verify
unzip -l /path/to/output/ai-cos-v6.2.0.skill
# Should show: ai-cos/SKILL.md

# 5. Present to user for installation
present_files on the .skill file
```

### Active Skills

| Skill | Trigger Words | Location |
|-------|--------------|----------|
| ai-cos | meetings, network, portfolio, IDS, thesis, scoring, pipeline, actions, build roadmap | `skills/ai-cos-v6-skill.md` |
| notion-mastery | Any Notion MCP tool call (auto-trigger by tool usage pattern) | `.skills/skills/notion-mastery/` |
| parallel-deep-research | "research deep and wide", "deep research", "exhaustive research" | `.skills/skills/parallel-deep-research/` |
| full-cycle | "run full cycle", "run everything", "process everything" | `skills/full-cycle/SKILL.md` |
| youtube-content-pipeline | "process my content queue" | `skills/youtube-content-pipeline/SKILL.md` |

---

## 11. Build Roadmap Workflow

### Overview

The Build Roadmap is a Notion database that tracks all AI CoS product build items. It serves as the single source of truth for what's being built, what's in progress, and what's shipped.

### Database IDs

- Data Source: `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f`
- Database: `3446c7df9bfc43dea410f17af4d621e0`
- Default View: `view://4eb66bc1-322b-4522-bb14-253018066fef`

### Status Pipeline

```
💡 Insight → 📋 Backlog → 🎯 Planned → 🔨 In Progress → 🧪 Testing → ✅ Shipped → 🚫 Won't Do
```

### Key Properties

| Property | Type | Purpose |
|----------|------|---------|
| Item | Title | Description of the build item |
| Status | Select | Pipeline stage |
| Priority | Select | P0 (Critical) through P4 (Nice to have) |
| Epic | Select | Feature group |
| Build Layer | Select | System layer (Infra, Pipeline, Intelligence, etc.) |
| Parallel Safety | Select | 🟢/🟡/🔴 classification |
| Branch | Text | Git branch name (when in progress) |
| Assigned To | Text | Agent/session ID |
| T-Shirt Size | Select | Effort estimate |
| Dependencies | Self-relation | Blocked-by links |
| Technical Notes | Rich Text | Implementation context |
| Source | Select | Where the item came from |
| Discovery Session | Text | Session that discovered it |

### 2-Step Roadmap Gate

Before any code change (Edit/Write to non-doc, non-research file):

1. **Check:** Does a Build Roadmap item exist for this work?
2. **If not:** Quick-add one (~30 sec) with Status = 💡 Insight, then proceed.

No untracked code changes. The gate doesn't block — it ensures tracking.

### Always-Query Rule

Every session fetches Build Roadmap context (~3 sec via `notion-query-database-view` with `view://4eb66bc1-322b-4522-bb14-253018066fef`). This replaces keyword-based "build session" detection.

### Read Pattern (ONE call)

```
notion-query-database-view with view_url: "view://4eb66bc1-322b-4522-bb14-253018066fef"
```

Returns all rows with full properties. Filter in-context after fetching.

### Write Pattern (Add insight)

```
notion-create-pages with parent: { data_source_id: "6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f" }
properties: {
  "Item": "Description",
  "Status": "💡 Insight",
  "Build Layer": "<layer>",
  "Source": "Session Insight",
  "Discovery Session": "Session NNN",
  "Technical Notes": "Context"
}
```

### Update Pattern (Move through pipeline)

```
notion-update-page with command: "update_properties"
page_id: "<page-id>"
properties: { "Status": "🔨 In Progress" }
```

---

## 12. Content Pipeline (CI for Content)

The Content Pipeline is the AI CoS equivalent of CI/CD for content intelligence — it extracts, analyzes, cross-references, and publishes content digests.

### Pipeline Stages

```
EXTRACT → ANALYZE → CROSS-REFERENCE → PUBLISH → ACT
```

**Stage 1: EXTRACT** — YouTube transcripts via `yt` CLI or automated launchd (8:30 PM daily).
- Input: YouTube URLs
- Output: JSON transcripts in `queue/processed/`

**Stage 2: ANALYZE** — `scripts/process_youtube_queue.py` runs thesis/portfolio matching.
- Input: Extraction JSONs
- Output: Structured analysis with thesis connections, portfolio relevance, key insights

**Stage 3: CROSS-REFERENCE** — Match against Notion Thesis Tracker and Portfolio DB.
- Scores: thesis_relevance, portfolio_relevance, novelty, actionability
- Tags: matching thesis threads, relevant portfolio companies

**Stage 4: PUBLISH** — `scripts/publish_digest.py` creates Notion Content Digest DB entry + pushes HTML digest.
- Notion: Content Digest DB entry with all metadata
- HTML: JSON → `aicos-digests/src/data/` → git push → Vercel
- URL: `https://digest.wiki/d/{slug}` with dynamic OG tags

**Stage 5: ACT** — Proposed actions routed to Actions Queue.
- Each digest can generate 0-N proposed actions
- Actions relate back to Source Digest, Company, and Thesis Thread
- Review: "review my content actions" on mobile queries Pending actions

### Scheduled Automation

- **YouTube extraction:** launchd at 8:30 PM daily
- **Content Pipeline analysis:** Scheduled task at 9 PM daily
- **Full cycle:** Manual trigger via "run full cycle" command

---

## 13. Scheduled Automation

### Infrastructure

Scheduled tasks use two mechanisms:

1. **macOS launchd** — For Mac-native operations (YouTube extraction).
   - Config: `.plist` files in `scripts/`
   - Setup: `scripts/setup_youtube_cron.sh`

2. **Cowork Scheduled Tasks** — For Claude-driven operations.
   - Managed via `mcp__scheduled-tasks__*` tools
   - SKILL.md: `skills/full-cycle/SKILL.md` (must be updated when new tasks added)

### Active Scheduled Tasks

| Task | Schedule | Mechanism | What It Does |
|------|----------|-----------|--------------|
| YouTube extraction | 8:30 PM daily | launchd | `yt` CLI → queue/processed/ |
| Content Pipeline | 9:00 PM daily | Cowork scheduled task | Analyze queue → Notion + HTML digests |

---

## 14. Operational Scripts Inventory

| Script | Purpose | Runs Where |
|--------|---------|-----------|
| `youtube_extractor.py` | YouTube transcript extraction (launchd) | Mac host |
| `process_youtube_queue.py` | Content Pipeline analysis | Cowork sandbox |
| `publish_digest.py` | JSON → Notion + digest site publish | Cowork + osascript |
| `content_digest_pdf.py` | PDF digest generation | Cowork sandbox |
| `action_scorer.py` | Action scoring model (session 039) | Cowork sandbox |
| `dedup_utils.py` | Deduplication utilities (session 039) | Cowork sandbox |
| `branch_lifecycle.sh` | 6-step branch lifecycle CLI + worktree manager | Mac host (via osascript) |
| `auto_push.sh` | Auto-push helper | Mac host |
| `validate-skill-package.sh` | Skill ZIP validation | Cowork sandbox |
| `setup_youtube_cron.sh` | Launchd cron setup | Mac host |
| `notify_digest_template.py` | Notion digest template | Cowork sandbox |
| `yt` | YouTube CLI wrapper | Mac host |

### Subagent Prompt Templates

| Template | Purpose |
|----------|---------|
| `subagent-prompts/session-close-file-edits.md` | Session close Steps 2, 3, 5 |
| `subagent-prompts/skill-packaging.md` | Skill .skill ZIP packaging |
| `subagent-prompts/git-push-deploy.md` | Commit + hand-off for osascript push |
| `subagent-prompts/general-file-edit.md` | Any 🔴 file edit |
| `subagent-prompts/branch-workflow.md` | Branch + subagent orchestration reference |
| `session-behavioral-audit-prompt.md` | Behavioral audit subagent prompt (v1.3.0) |

---

## 15. Known Constraints & Anti-Patterns

### Notion Operation Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|---------|--------------|
| `API-query-data-source` (all `/data_sources/*` endpoints broken) | `notion-query-database-view` with `view://UUID` |
| `notion-fetch` on `collection://` URL (schema only, no rows) | `notion-query-database-view` with `view://UUID` |
| `notion-query-database-view` with `https://...?v=` URL | Use `view://UUID` format only |
| `API-retrieve-a-page` (404 on some pages) | `notion-fetch` (Enhanced Connector — broader access) |
| `API-patch-page` with `in_trash: true` (404 for Enhanced pages) | Update status to "Dismissed" + prefix title `[DELETED]` |
| Set multi_select with multiple values in create | Create page first, then `notion-update-page` one at a time |
| `"Due Date": "2026-03-15"` | `"date:Due Date:start": "2026-03-15"`, `"date:Due Date:is_datetime": 0` |
| `"Done": true` | `"Done": "__YES__"` or `"__NO__"` |
| `"Company": "page-id"` | `"Company": "[\"https://www.notion.so/page-id\"]"` |
| `"Score": "8"` (string) | `"Score": 8` (native number) |
| Hardcode MCP tool UUIDs | Detect by suffix pattern (UUIDs change per session) |
| Make Notion call without loading skill | Always load `notion-mastery` skill first |

### Schema & Data Integrity Rules

| Rule | Why |
|------|-----|
| Pipeline skill template fields MUST match TypeScript types exactly | Schema drift caused dead digest links |
| When schema changes, update BOTH skill template AND TypeScript atomically | One-sided updates = silent drift |
| Validate JSON before committing to `src/data/` | Invalid JSON breaks Next.js SSG silently |
| LLM outputs need runtime normalization as defense-in-depth | Prompt engineering alone is insufficient |
| Always fetch DB schema before writing to ANY Notion database | Property names are case-sensitive |
| Large DB schemas (90+ fields) can exceed context | Use Grep on output to find specific properties |

### Bootstrap Paradox

The Lifecycle CLI (`branch_lifecycle.sh`) lives in the git repo it manages. If you create a branch to upgrade the CLI, the branch has the old CLI. Workaround: upgrade on a branch, manually merge, then the upgraded CLI serves future branches.

---

## Appendix A: Quick Reference Card

### "I want to..."

| Goal | Steps |
|------|-------|
| **Ship a code change** | Check Roadmap → create branch → subagent edits → commit → coordinator review → merge → close → update Roadmap |
| **Deploy digest site** | Commit in aicos-digests/ → osascript git push → wait ~90s → live at digest.wiki |
| **Add a build insight** | `notion-create-pages` with Status = 💡 Insight to Build Roadmap |
| **Run content pipeline** | "run full cycle" or manually: extract → analyze → publish |
| **Close a session** | 8-step checklist (subagents for file edits, main session for Notion) |
| **Package a skill** | Verify source → check version/description → `zip -r output.skill name/` → present_files |
| **Run behavioral audit** | Spawn Bash subagent with `session-behavioral-audit-prompt.md` template |
| **Do parallel work** | Create worktrees → spawn parallel subagents → coordinator reviews → merge each |

### Key File Locations

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Master context — single source of truth |
| `CLAUDE.md` | Operating rules, anti-patterns, session history |
| `skills/ai-cos-v6-skill.md` | Current skill source |
| `scripts/branch_lifecycle.sh` | Branch/worktree lifecycle CLI |
| `scripts/subagent-prompts/` | 4 subagent prompt templates |
| `scripts/session-behavioral-audit-prompt.md` | Audit prompt v1.3.0 |
| `docs/persistence/layered-persistence-coverage.md` | 6-layer coverage map |
| `docs/persistence/v6-artifacts-index.md` | Version tracking for all artifacts |
| `docs/iteration-logs/` | Session history logs |
| `docs/session-checkpoints/` | Mid-session pickup files |

---

*This document should be updated when new build system components are added. Last updated: Session 040.*
