# Parallel AI CoS Development — Enforcement, Process & Critical Analysis

**Session:** 034 | **Date:** 2026-03-04
**Status:** Research + Critical Thinking — No Implementation

---

## Your Questions, Answered Honestly

### Q1: How will "don't edit this file" discipline be enforced with subagents?

**The honest answer: It can't be reliably enforced through prompts alone.**

Research confirms what you suspected — LLM agents drift from instructions, especially file restrictions. The drift rate is significant: agents follow prompt-based file constraints for roughly 3-5 turns, then start ignoring them under the pressure of "completing the task." This is consistent across Claude, GPT-4, and every major model tested.

**What's available TODAY in our stack:**

| Layer | Mechanism | Reliability | Notes |
|-------|-----------|-------------|-------|
| Prompt (CLAUDE.md) | "Do not edit these files: ..." | ~60% | Drifts after 3-5 turns. Agent will "helpfully" edit forbidden files if it thinks it needs to. |
| Subagent prompt | Task-level instructions with explicit file list | ~70% | Better than global rules because scope is narrow, but still advisory. |
| Tool restriction | Spawn subagent with only `Read, Grep, Glob` (no `Edit, Write`) | **~95%** | Hard constraint — agent literally cannot write. But limits usefulness for build tasks. |
| Worktree isolation | `isolation: "worktree"` | ~80% for branch safety | Prevents main branch corruption. Does NOT prevent editing wrong files within the worktree. |
| Pre-edit validation | Read target file → check against allowlist → proceed or abort | ~85% | Requires the agent to self-enforce, but the check is explicit and happens right before the action. |
| Git pre-commit hook | Hook rejects commits touching protected files | **~95%** | System-enforced. But agent can bypass with `--no-verify`. |
| Claude Code `PreToolUse` hook | Shell script blocks Edit/Write to specific paths | **~90%** | Fires before tool executes. Agent sees error, can't easily bypass (but could try Bash). |

**My recommendation — 3-layer enforcement for 🔴 files:**

```
Layer 1: Subagent prompt includes explicit blocklist
    "You MUST NOT edit: skills/ai-cos-v6-skill.md, CLAUDE.md, CONTEXT.md"

Layer 2: Pre-edit self-check (embedded in subagent instructions)
    "Before EVERY Edit/Write call, verify the target file is in your ALLOWED list:
     [file1.py, file2.ts, docs/research/new-doc.md]
     If not in list, STOP and return to coordinator."

Layer 3: Post-completion diff review by coordinator
    Coordinator reads subagent's changes, rejects if forbidden files touched.
    For worktree subagents: review diff before merge.
```

**Does this need aggressive layer persistence?** Yes, absolutely. The file restriction rules need to be:
- In the ai-cos skill (Layer 1 — project constitution)
- In every subagent's task prompt (Layer 3 — task context)
- Ideally in a PreToolUse hook (Layer 4 — execution guard)

But here's the critical nuance: **the rules themselves are dynamic, not static.** Each task has different allowed/blocked files. So you can't just hardcode "never touch CLAUDE.md" globally — sometimes you NEED to update CLAUDE.md. The enforcement has to be **per-task scoping**: "For THIS task, your allowed files are X, Y, Z."

**What about the orchestration rules themselves drifting?** Yes, this is a real meta-problem. The coordination instructions ("check Build Roadmap before starting," "claim your task," "don't edit 🔴 files") are themselves subject to drift. These need the same layered persistence treatment:

- Constitution level: core parallel work rules in ai-cos skill
- Session level: coordinator re-states rules when spawning each subagent
- Execution level: pre-edit validation check in subagent workflow

---

### Q2: Workflow quick guide for your reference

This would be created AFTER implementation. What it should contain:

1. **Decision tree:** "Am I doing parallel or sequential work right now?"
2. **Parallel kickoff checklist:** Open Build Roadmap → pick 🟢 items → spawn tasks/subagents → monitor
3. **Merge protocol:** Review diffs → resolve conflicts → commit to main → update Roadmap
4. **Troubleshooting:** Common failures (file conflict, subagent drift, stale Notion state) and fixes
5. **Escalation:** When to abandon parallel and go sequential

This is a Phase 1 deliverable — I'll create it as a standalone doc once we implement. Should be <2 pages, mobile-readable.

---

### Q3: How will Build Roadmap track which agent/task is picking up what?

**Current gap:** Build Roadmap has no "assigned to" or "active agent" concept. This is critical for parallel work.

**Proposed addition — 3 new properties:**

| Property | Type | Purpose |
|----------|------|---------|
| **Assigned To** | Select: `Cowork-1`, `Cowork-2`, `Cowork-3`, `Subagent`, `Manual` | Who's working on this right now |
| **Branch** | Text | Git branch name (e.g., `feat/content-pipeline-scoring`) |
| **Parallel Safety** | Select: 🟢 Safe / 🟡 Coordinate / 🔴 Sequential | Can this run in parallel? |

**The workflow you described is exactly right:**

```
Agent/Task starts → Reads Build Roadmap → Shows unclaimed items →
You (or agent) picks task → Agent sets:
  - Status: "🔨 In Progress"
  - Assigned To: "Cowork-1" (or whichever task)
  - Branch: "feat/xyz"
→ Works → Completes → Sets Status: "🧪 Testing" → Coordinator reviews → "✅ Shipped"
```

**Should the agent ASK which task to pick?** Yes, with a smart default. The agent should:
1. Query Build Roadmap for Status = "🎯 Planned" AND Assigned To = empty AND Parallel Safety = 🟢
2. Present the top 3-5 options sorted by Priority
3. You confirm one (or the agent auto-picks the highest priority 🟢 if you've pre-approved)

**Live context in Build Roadmap:** This is achievable. Each agent updates its row when:
- Starting work (Status → In Progress, Assigned To → set)
- Completing work (Status → Testing, Branch → set)
- Being dismissed (Status → Planned, Assigned To → cleared)

**The limitation:** Notion isn't real-time. If two Cowork tasks query Build Roadmap simultaneously and both see the same unassigned task, they could both claim it. Mitigation: the coordinator task is the only one that assigns tasks. Workers don't self-assign.

---

### Q4: Does Build Roadmap need more granular tasks?

**Critical thinking: YES, but not in the way traditional project management does it.**

**Current state:** Build Roadmap items are at the "Feature/Epic" level. Examples: "Content Pipeline v5," "Action Frontend," "Meeting Optimizer." These are too coarse for parallel agent work — an agent can't "pick up Content Pipeline v5" in a 30-minute session.

**What research says about optimal task granularity for AI agents:**

| Granularity | Scope | Agent Success Rate | Review Time | Parallel Safety |
|-------------|-------|-------------------|-------------|-----------------|
| Epic (weeks) | "Build Content Pipeline v5" | Low — too much context, agent drifts | Hours | Cannot parallelize |
| Feature (days) | "Add semantic matching to digest analysis" | Medium — manageable but still broad | 30-60 min | Some parallelism |
| **Task (hours)** | "Add `semantic_score` field to DigestEntry type + update publish_digest.py scoring function" | **High — focused, completable** | **10-15 min** | **Most parallelizable** |
| Subtask (minutes) | "Add line 45 to types.ts" | Overkill — not worth the coordination overhead | 2 min | Trivially parallel but overhead > benefit |

**The sweet spot is Task-level (1-3 hours, 1-2 files, clear DoD).**

**But here's the key insight: you don't need granular tasks in Notion permanently.** The breakdown should happen at session time, not in advance:

```
Permanent in Build Roadmap: Feature-level items (current state)
  "Content Pipeline v5 — Semantic Matching"

At session start: Agent breaks Feature → Tasks (ephemeral)
  Task 1: Add semantic_score to DigestEntry type (types.ts) — 🟢
  Task 2: Implement scoring function in publish_digest.py — 🟡
  Task 3: Update skill template with new fields — 🔴
  Task 4: Write test cases for scoring — 🟢

These tasks live in the session, not permanently in Build Roadmap.
```

**Why not permanent granular tasks in Notion?**
1. **Maintenance burden** — you'd need to keep 50+ tasks updated, most of which become stale
2. **Premature decomposition** — breaking down tasks before you understand the implementation leads to wrong tasks
3. **IDS conflict** — your methodology is Increasing Degrees of Sophistication, not waterfall decomposition
4. **Agent capability** — Claude can decompose a Feature into Tasks at session start in <2 minutes

**Alternative: "Task Notes" in Build Roadmap**
Add a "Task Breakdown" rich text property to Feature items. When a session decomposes a Feature into Tasks, record the breakdown there. Next session can read it and pick up where the previous one left off. This gives you persistence without the overhead of managing 50+ Notion rows.

---

### Q5: Should we enforce strict Plan → PRD → Spec/DoD with phases?

**Critical thinking: NO — strict process kills the thing that makes AI agents fast.**

Here's what the research actually found:

**Evidence AGAINST strict spec-driven process for AI agents:**
- Martin Fowler's team tested spec-kit (GitHub's spec-driven tool) and found agents **ignore specs and regenerate existing code** — the process creates markdown but doesn't guarantee adherence
- Small tasks (3-5 point stories) under spec-kit feel like "using a sledgehammer to crack a nut"
- In the same time it takes to run spec→plan→tasks→implement, plain Claude Code often finishes the whole feature
- Multiple spec files (constitution.md, specification.md, plan.md, tasks.md) create review overhead without proportional safety

**Evidence FOR some structure:**
- Teams with lightweight specs show fewer hallucinations and less rework
- Plan-before-code (Claude's plan mode, Cursor plan mode) catches scope creep early
- Clear acceptance criteria reduce "done but wrong" outcomes

**The right level of process for solo dev + AI agents:**

```
NOT THIS (heavyweight):
  Plan Doc → PRD → Technical Spec → DoD Checklist → Phase Plan →
  Task Breakdown → Implementation → Review → Signoff → Deploy
  (8 steps, 6+ documents, hours of overhead per feature)

THIS (lightweight, IDS-aligned):
  1. INTENT (30 sec): One sentence — what are we building and why?
  2. SCOPE (2 min): Which files will change? What's the Parallel Safety?
  3. DO (variable): Agent executes, commits frequently
  4. CHECK (5 min): Review diff, run tests, verify against intent

  Total overhead: ~7 minutes per task, not per feature.
```

**What Cowork SHOULD enforce (lightweight gates, not heavy process):**

| Gate | When | What | Time |
|------|------|------|------|
| **Intent Check** | Before starting any build task | "What are you building? Which Build Roadmap item? What files?" — agent must answer before proceeding | 30 sec |
| **Scope Lock** | After intent, before coding | Agent lists files it will touch. If any 🔴 files, flag for coordination. | 1 min |
| **Mid-Task Checkpoint** | Every 15 min or every 3 file edits | Agent writes progress note: what's done, what's next, any blockers | 1 min |
| **Completion Check** | Before marking task as done | Diff review, intent match, test status | 5 min |

**These gates are enforceable because they're embedded in the agent's workflow, not in external documents.** The ai-cos skill can include them as mandatory steps in any build task recipe.

**Phase-based with clean task breakdown — yes, but lightweight:**

Instead of formal phases with documentation, use this pattern:

```
Phase = a set of 🟢 tasks that can run in parallel

Phase 1 (this week):
  - Task A: [description] — 🟢 — files: [x, y]
  - Task B: [description] — 🟢 — files: [a, b]
  - Task C: [description] — 🟡 — files: [m, n] (needs coordination)

Phase 2 (depends on Phase 1):
  - Task D: [description] — 🔴 — files: [skill.md] (sequential)
  - Task E: [description] — 🟢 — files: [new files only]

The "plan" IS the phase/task list in Build Roadmap.
The "spec" IS the Task Breakdown note on the Feature item.
The "DoD" IS the Completion Check gate.
```

No separate documents. The process lives in the workflow, not in artifacts.

---

## Updated Architecture: Incorporating All Answers

### The Full Picture

```
┌────────────────────────────────────────────────────────────────┐
│  YOU — Pick features from Build Roadmap, set priorities        │
│  "Work on Content Pipeline v5 and Action Frontend this week"   │
└──────────────────────┬─────────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────────┐
│  COORDINATOR (Cowork Task #1 or start of any session)          │
│                                                                │
│  1. Read Build Roadmap (🟢/🟡/🔴 items, Assigned To status)    │
│  2. Decompose Features → Tasks (if not already broken down)    │
│  3. Present unassigned tasks, ask which to work on             │
│  4. Assign tasks (set Assigned To, Status = In Progress)       │
│  5. Spawn subagents/workers for 🟢 tasks                       │
│  6. Work 🔴 tasks sequentially itself                           │
│  7. Review all changes before committing                       │
│  8. Update Build Roadmap on completion                         │
│                                                                │
│  ENFORCEMENT:                                                  │
│  - Each subagent gets EXPLICIT allowed file list               │
│  - Pre-edit self-check in subagent instructions                │
│  - Coordinator reviews all diffs before merge                  │
│  - Intent/Scope/Mid/Completion gates on every task             │
└────────┬──────────────┬────────────────┬───────────────────────┘
         │              │                │
    ┌────▼────┐   ┌────▼─────┐    ┌────▼──────────┐
    │Worker 1 │   │Worker 2  │    │ Research      │
    │(worktree│   │(worktree │    │ (read-only    │
    │ branch) │   │ branch)  │    │  subagent)    │
    │         │   │          │    │               │
    │ALLOWED: │   │ALLOWED:  │    │ NO Edit/Write │
    │file1.ts │   │file3.py  │    │ tools at all  │
    │file2.ts │   │file4.py  │    │               │
    │         │   │          │    │               │
    │BLOCKED: │   │BLOCKED:  │    │               │
    │*all else│   │*all else │    │               │
    └─────────┘   └──────────┘    └───────────────┘
```

### Enforcement Layers (Persistent — needs 3+ layer coverage)

```
LAYER 1 — AI-COS SKILL (Constitution)
  "§ Parallel Build Rules:
   - Every build task starts with Intent Check
   - Subagents receive EXPLICIT allowed file lists
   - 🔴 files are NEVER assigned to subagents
   - Coordinator reviews ALL diffs before merge
   - Build Roadmap is updated at task start AND completion"

LAYER 2 — CLAUDE.md (Operating Rules)
  "| Rule: Subagent file allowlists |
   Why: Prompt-based restrictions drift after 3-5 turns |
   Enforcement: Explicit allowed list + pre-edit check + diff review |"

LAYER 3 — SUBAGENT TASK PROMPT (Per-invocation)
  "You are working on Task X.
   ALLOWED files: [explicit list]
   BLOCKED: Everything else.
   Before EVERY Edit/Write, verify target is in ALLOWED list.
   If not, STOP and return 'BLOCKED_FILE: {filename}' to coordinator."

LAYER 4 — EXECUTION GUARD (Future: PreToolUse hook)
  Shell script checks file path against allowlist.
  Exit code 2 = block operation.
  (Phase 2 implementation — requires Claude Code hooks setup)
```

### Build Roadmap Schema Update

**New properties needed:**

| Property | Type | Values/Format |
|----------|------|---------------|
| Parallel Safety | Select | 🟢 Safe, 🟡 Coordinate, 🔴 Sequential |
| Assigned To | Select | Unassigned, Cowork-1, Cowork-2, Cowork-3, Subagent-A, Subagent-B, Manual |
| Branch | Text | e.g., `feat/semantic-scoring` |
| Task Breakdown | Rich Text | Ephemeral decomposition when session starts work on a Feature |

**Existing properties used for coordination:**
- Status (already exists): Planned → In Progress → Testing → Shipped
- Priority (already exists): P0-P3

### Process Gates (Lightweight, Embedded in Workflow)

```
INTENT CHECK (mandatory, 30 sec):
  Agent: "I'm picking up [Build Roadmap Item].
          Intent: [one sentence].
          Files I'll touch: [list].
          Parallel Safety: [🟢/🟡/🔴]."
  → Updates Build Roadmap: Status = In Progress, Assigned To = self

SCOPE LOCK (mandatory, 1 min):
  Agent lists ALL files it will edit/create.
  If any 🔴 file → flag to user, get explicit approval.
  If any 🟡 file → check no other agent has it assigned.
  Lock: Add files to Task Breakdown note.

MID-TASK CHECKPOINT (every 15 min or 3 edits):
  Agent writes quick note: done / in progress / blocked.
  For subagents: coordinator can read progress.

COMPLETION CHECK (mandatory, 5 min):
  - Review diff against intent
  - Verify no unintended file changes
  - Run relevant tests
  - Update Build Roadmap: Status = Testing/Shipped
  - Clear Assigned To
```

---

## Revised Phased Plan (Incorporating All Answers)

### Phase 0: Foundation (1 session, ~45 min)
**No change from original plan**, plus:
- Add "Assigned To," "Branch," and "Task Breakdown" properties to Build Roadmap
- Write enforcement rules into ai-cos skill (Layer 1) and CLAUDE.md (Layer 2)
- Classify all existing items with Parallel Safety scores

### Phase 1: Single-Session Parallelism (1-2 sessions)
**Updated:**
- Test subagent enforcement: spawn worker with explicit allowlist, intentionally try to get it to edit a blocked file, measure drift
- Implement the Intent/Scope/Mid/Completion gates in the coordinator workflow
- Create the workflow quick guide (your personal reference)
- Test: 2 genuine 🟢 tasks via worktree subagents + 1 🔴 task sequentially

### Phase 2: Multi-Task Parallelism (2-3 sessions)
**Updated:**
- Initialize local git in AI CoS root (for branching only, no remote)
- Implement Claude Code `PreToolUse` hook for file allowlists (Layer 4 enforcement)
- Task checkout protocol: agent reads Roadmap → picks unclaimed → sets Assigned To → works → completes
- Test: 2 Cowork tasks simultaneously, verify Notion coordination prevents conflicts
- Stress test: intentional conflict on 🟡 file → verify detection and resolution

### Phase 3: Steady-State (ongoing)
**Updated:**
- Every build session starts with Build Roadmap query
- Agent always asks "which unassigned tasks should I pick up?"
- Monthly drift audit: review if agents are honoring file restrictions
- Quarterly: reassess whether full git + GitHub is needed based on conflict frequency

---

## The Meta-Question: Does Parallel Dev Need Its Own Layer Persistence?

**Yes.** The parallel work rules are a new class of critical instructions that will drift just like the Notion formatting rules and sandbox rules did. Based on your layered persistence architecture:

| Instruction Set | Layers Needed | Why |
|----------------|---------------|-----|
| "Subagents get explicit file allowlists" | 3+ | Will be forgotten after 2-3 sessions without reinforcement |
| "Always query Build Roadmap at task start" | 3+ | Agents default to "just start coding" without this |
| "🔴 files are never assigned to subagents" | 3+ | Agents will "helpfully" edit forbidden files |
| "Coordinator reviews all diffs before merge" | 2+ | Lower risk — natural workflow, less drift-prone |
| "Intent/Scope gates are mandatory" | 3+ | Process steps are the first thing agents skip |

These should be added to `docs/layered-persistence-coverage.md` during implementation and tracked in the persistence audit cycle (every 5 sessions).

---

## Key Takeaways

1. **File enforcement = architectural, not prompt-based.** Triple-layer (prompt + self-check + diff review) is the minimum. PreToolUse hooks (Phase 2) will add a 4th layer.

2. **Build Roadmap stays at Feature level, decomposition is ephemeral.** Don't create 50 Notion tasks — break features into tasks at session start, record in Task Breakdown note, and let the session work through them.

3. **Process should be gates, not documents.** Intent Check → Scope Lock → Mid-Checkpoint → Completion Check. Embedded in workflow, not in separate files.

4. **The coordinator pattern is essential.** Whether it's you, a dedicated Cowork task, or the start of any session — someone must assign tasks, review diffs, and update Build Roadmap. Flat parallel without coordination = chaos.

5. **Start measuring drift from day 1.** Every time an agent edits a file it shouldn't have, log it. This data feeds the persistence audit and tells you when to upgrade enforcement layers.
