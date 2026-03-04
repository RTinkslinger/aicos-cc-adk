# Parallel AI CoS Development — Research & Phased Plan

**Session:** 034 | **Date:** 2026-03-04
**Status:** Research Complete, Plan Ready — No Implementation Yet

---

## Executive Summary

The AI CoS codebase has a natural parallelism ceiling defined by file contention patterns. The research shows that **most Build Roadmap items are already parallelizable** — the bottleneck isn't code conflicts, it's coordination overhead. The recommended approach: lightweight git branching (worktrees) + Notion-based task coordination + file classification scoring in Build Roadmap, rolled out in 3 phases.

**Key insight:** Elaborate build sessions are the anti-pattern. The winning model is **small, scoped tasks** (1-2 files, <30 min) that agents/Cowork tasks pick off from a shared queue — exactly what you intuited.

---

## Part 1: Research Findings

### 1.1 Isolation Mechanisms Available

| Mechanism | How It Works | Best For | Limitations |
|-----------|-------------|----------|-------------|
| **Git worktrees** | Multiple working directories from same repo, each on own branch | Parallel feature work that touches different files | Merge conflicts on shared files; need merge discipline |
| **Cowork parallel tasks** | Each task = separate sandboxed Linux VM, shared mounted folder | Independent workstreams (research + code + content) | Last-write-wins on file conflicts — NO locking |
| **Claude Code `--worktree`** | Auto-creates git worktree per agent invocation | CLI-based parallel dev with auto-isolation | Requires git repo; human reviews/merges branches |
| **Task tool subagents** | `isolation: "worktree"` creates temp worktree per subagent | Parallel subtasks within a single Cowork session | Single-level only (no nested subagents); worktree auto-cleaned if no changes |
| **Notion task queue** | DB rows as tasks with Status + Assignment fields | Coordination layer across agents/sessions | Not real-time; no true locking; relies on convention |

### 1.2 File Contention Analysis — AI CoS Codebase

Classified every key file by parallel safety:

**🟢 SAFE_PARALLEL (can be edited by multiple agents simultaneously)**
- `docs/iteration-logs/*` — append-only, unique filenames per session
- `docs/session-checkpoints/*` — unique filenames per checkpoint
- `docs/research/*` — each research doc is standalone
- `aicos-digests/src/data/*.json` — each digest is a separate file
- `aicos-digests/src/app/d/[slug]/page.tsx` — rarely changes after v1
- New skill files (new skills in their own directories)
- Notion DB entries (each row is independent)

**🟡 NEEDS_COORDINATION (can be parallel with discipline)**
- `aicos-digests/src/lib/digests.ts` — shared utility but changes are additive
- `aicos-digests/src/lib/types.ts` — TypeScript types, changes are additive
- `scripts/publish_digest.py` — single file, changes usually isolated to functions
- `CONTEXT.md` — large file but sections are distinct; append to different sections OK
- Individual Notion DB schemas — schema changes need sequencing

**🔴 SEQUENTIAL_ONLY (must be single-writer)**
- `skills/ai-cos-v6-skill.md` — the master skill, changes compound
- `CLAUDE.md` — project instructions, changes compound
- `docs/v6-artifacts-index.md` — version tracker, must be consistent
- `docs/claude-memory-entries-v6.md` — memory entries, order matters
- `docs/layered-persistence-coverage.md` — audit state, single writer
- `aicos-digests/package.json` — dependency changes need sequencing

### 1.3 Multi-Agent Architecture Patterns

**Best fit for AI CoS: Hierarchical Delegation with Task Queue**

```
┌─────────────────────────────────────────────┐
│  YOU (Aakash) — Strategic Direction          │
│  "Work on Content Pipeline v5 this week"     │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  COORDINATOR SESSION (Cowork Task #1)        │
│  Reads Build Roadmap → assigns tasks →       │
│  reviews PRs → merges → updates Roadmap      │
└──────┬───────────┬───────────┬──────────────┘
       │           │           │
┌──────▼───┐ ┌────▼─────┐ ┌──▼──────────┐
│ Worker   │ │ Worker   │ │ Worker      │
│ Task #2  │ │ Task #3  │ │ Subagent    │
│ Feature A│ │ Feature B│ │ Research C  │
│ (worktree│ │ (worktree│ │ (read-only) │
│  branch) │ │  branch) │ │             │
└──────────┘ └──────────┘ └─────────────┘
```

Why this over alternatives:
- **Parallel competition** (race multiple agents, pick best) — wasteful for a solo dev's credit budget
- **Sequential specialists** — too slow, defeats the purpose
- **Flat parallel** (no coordinator) — merge hell on shared files

### 1.4 Recommended State Sync: Git + Notion Hybrid

**Git** (source of truth for code):
- `main` branch = stable, always deployable
- Feature branches = one per parallelizable task
- Worktrees = local mechanism for parallel branches
- Merge back to main after each task completes

**Notion Build Roadmap** (source of truth for task state):
- Add "Parallel Safety" property (🟢/🟡/🔴)
- Status field already tracks pipeline: Insight → Backlog → Planned → In Progress → Done
- Add "Branch" text field when work begins (e.g., `feat/content-pipeline-v5-scoring`)
- Coordinator checks Roadmap before assigning tasks — never assign two 🔴 items simultaneously

**Why NOT a cloud-synced git repo?** The AI CoS folder is a Claude Projects folder, not a proper git repo (except `aicos-digests/` which already has GitHub). Adding git to the root folder creates complexity for marginal benefit. The coordination overhead of proper git (PRs, reviews, CI) exceeds the parallelism benefit at current scale (1 human + 2-3 concurrent agents). **Revisit when moving to Agent SDK** where you control the execution environment.

---

## Part 2: Phased Implementation Plan

### Phase 0: Foundation (1 session, ~45 min)
**Goal:** Add parallel safety scoring to Build Roadmap, classify existing items

| Task | Safety | Files Touched | Est. Time |
|------|--------|--------------|-----------|
| 0.1 Add "Parallel Safety" select property to Build Roadmap (🟢 Safe / 🟡 Coordinate / 🔴 Sequential) | 🟢 | Notion schema only | 5 min |
| 0.2 Add "Branch" text property to Build Roadmap | 🟢 | Notion schema only | 2 min |
| 0.3 Classify all existing Backlog/Planned items with Parallel Safety scores | 🟢 | Notion rows only | 15 min |
| 0.4 Update ai-cos skill with parallel work rules (when to use worktrees, file classification ref) | 🔴 | `skills/ai-cos-v6-skill.md` | 15 min |
| 0.5 Update CLAUDE.md with parallel dev operating rules | 🔴 | `CLAUDE.md` | 10 min |

**Dependency:** 0.1-0.3 can run parallel. 0.4 and 0.5 must be sequential (both 🔴 files).

### Phase 1: Single-Session Parallelism via Subagents (1-2 sessions)
**Goal:** Use `Task` tool with `isolation: "worktree"` for parallel subtasks within a single Cowork session

| Task | Safety | Files Touched | Est. Time |
|------|--------|--------------|-----------|
| 1.1 Create a "parallel task launcher" recipe in ai-cos skill — given a list of Build Roadmap items marked 🟢, spawn worktree subagents for each | 🔴 | `skills/ai-cos-v6-skill.md` | 20 min |
| 1.2 Test with 2 genuine 🟢 Build Roadmap items (e.g., two independent research docs) | 🟢 | New files only | 30 min |
| 1.3 Test with 1 🟡 item + 1 🟢 item — verify coordination protocol works | 🟡 | Existing + new files | 30 min |
| 1.4 Document merge workflow: subagent completes → review diff → merge to main working dir | 🔴 | `CLAUDE.md` or skill | 10 min |

**Key constraint:** Subagents can't spawn their own subagents (single-level). So the coordinator (main session) spawns workers, reviews results, merges.

### Phase 2: Multi-Task Parallelism (2-3 sessions)
**Goal:** Run 2-3 Cowork tasks simultaneously on different Build Roadmap items

| Task | Safety | Files Touched | Est. Time |
|------|--------|--------------|-----------|
| 2.1 Initialize git in AI CoS root folder (lightweight — `.gitignore` for large files, no remote) | 🟢 | New `.git/`, `.gitignore` | 10 min |
| 2.2 Create "task checkout" protocol: Cowork task starts → reads Build Roadmap → picks unclaimed 🟢 item → sets Status = In Progress → creates branch → works → commits → sets Status = Testing | 🔴 | Skill + CLAUDE.md | 20 min |
| 2.3 Create "task merge" protocol: coordinator task reviews branches → merges to main → resolves any conflicts → updates Build Roadmap Status = Shipped | 🔴 | Skill + CLAUDE.md | 15 min |
| 2.4 Test: open 3 Cowork tasks, each picks a different 🟢 item, works independently, coordinator merges | 🟢 | Various (by design, non-overlapping) | 45 min |
| 2.5 Test conflict resolution: intentionally have 2 tasks edit CONTEXT.md (🟡 file) — verify merge protocol | 🟡 | `CONTEXT.md` | 20 min |

**Key decision at Phase 2:** Whether to add a GitHub remote for the root folder. Recommendation: **don't** — the overhead isn't justified until Agent SDK migration. Local git + Notion coordination is sufficient.

### Phase 3: Steady-State Operations (ongoing)
**Goal:** Parallel development is the default mode, not a special case

| Task | Safety | Files Touched | Est. Time |
|------|--------|--------------|-----------|
| 3.1 Build Roadmap triage includes Parallel Safety scoring for every new item | 🟢 | Notion workflow | Ongoing |
| 3.2 Weekly "parallel sprint": pick 3-5 🟢 items, knock them off across parallel tasks/subagents | Mixed | Various | 2-3 hrs/week |
| 3.3 Monthly review: analyze merge conflict frequency, adjust file classifications | 🔴 | Coverage doc | 15 min/month |
| 3.4 When migrating to Agent SDK: revisit architecture for always-on parallel agents with proper state sync | — | Architecture doc | Future |

---

## Part 3: Multi-Threading Safety Score — Build Roadmap Integration

### Property: "Parallel Safety" (Select)

| Value | Meaning | Rule |
|-------|---------|------|
| 🟢 Safe | Touches only green files or creates new files. Can run fully parallel with anything. | No coordination needed. Any agent can pick this up. |
| 🟡 Coordinate | Touches yellow files. Can run parallel but needs merge attention. | Only 1 agent per yellow file at a time. Coordinator assigns. |
| 🔴 Sequential | Touches red files (skill, CLAUDE.md, artifacts index). Must run alone. | Block all other tasks touching same red files. |

### Classification Heuristic

When triaging a Build Roadmap item from Insight → Backlog:
1. List all files the task will likely touch
2. Check each file against the classification table (§1.2 above)
3. The task's Parallel Safety = the WORST classification of any file it touches
4. If uncertain, default to 🟡

### Example Classifications for Current Backlog

| Build Roadmap Item | Likely Files | Safety |
|-------------------|-------------|--------|
| New Content Pipeline source (Twitter/X) | New script, new types, `digests.ts` additions | 🟡 |
| Research: Agent SDK architecture | New research doc only | 🟢 |
| Add semantic matching to digest analysis | `publish_digest.py`, prompt templates | 🟡 |
| Update ai-cos skill with new capability | `skills/ai-cos-v6-skill.md` | 🔴 |
| Create new scheduled task | New skill file, `list_scheduled_tasks` | 🟢 |
| Portfolio action auto-routing | `publish_digest.py`, Notion writes | 🟡 |
| Refactor CONTEXT.md sections | `CONTEXT.md` | 🔴 |

---

## Part 4: Operational Rules (to embed in skill/CLAUDE.md when implementing)

### Rule 1: Never parallel-edit 🔴 files
Two agents editing `ai-cos-v6-skill.md` simultaneously = guaranteed conflict. Queue these.

### Rule 2: 🟡 files use section ownership
If two agents must touch `CONTEXT.md`, assign each a specific section. Agent A appends to "Thesis Threads", Agent B appends to "Iteration Logs" — no overlap.

### Rule 3: Notion is the coordination layer, not the locking layer
Build Roadmap Status = "In Progress" is a signal, not a lock. Agents should check before starting but don't need to poll. Convention > enforcement at current scale.

### Rule 4: Small tasks > big sessions
The sweet spot: tasks that touch 1-2 files, take <30 min, and produce a single commit. This maximizes parallelism and minimizes merge risk.

### Rule 5: Coordinator reviews every merge
No auto-merge. The coordinator (you or a dedicated Cowork task) reviews diffs before merging to the main working directory. This catches conflicts early.

### Rule 6: Research tasks are always 🟢
Any task that only produces new documents (research, analysis, planning) is inherently parallelizable. Use subagents aggressively for these.

---

## Part 5: Architecture Decision — Why Not Full Git + Cloud?

**Considered:** Full git repo with GitHub remote for the AI CoS root folder, with PR-based workflow.

**Rejected for now because:**
1. **Overhead exceeds benefit** at 1 human + 2-3 agents scale. PRs, CI, branch management add ceremony without proportional safety.
2. **Cowork sandbox can't push** — every push requires osascript MCP, which adds friction to every parallel task.
3. **The real parallelism bottleneck is human review**, not code isolation. You can only review and merge so fast.
4. **Agent SDK migration is coming** — when you move to custom agents, the execution environment changes fundamentally. Investing in elaborate git workflow now = throwaway work.

**Revisit trigger:** If merge conflicts become frequent (>2 per week) OR if you regularly run >3 parallel tasks, upgrade to full git + GitHub.

**Current recommendation:** Local git in AI CoS root (for branching/worktrees only, no remote) + Notion Build Roadmap as coordination DB. Minimal ceremony, maximum flexibility.

---

## Appendix: Key Research Sources

- Claude Code `--worktree` flag: creates isolated git worktree per invocation
- Cowork Task tool: `isolation: "worktree"` parameter for subagent isolation
- CrewAI hierarchical pattern: Strategy → Planning → Execution layers
- SWE-Bench multi-agent findings: parallel competition vs sequential specialist vs hierarchical delegation
- Event sourcing pattern: agents write immutable events, coordinator reconciles
- Git worktree docs: `git worktree add` for multiple working directories from same repo
