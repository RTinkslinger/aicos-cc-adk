# CC ↔ CAI Sync Architecture — v2.2 Addendum
## Cash Build System Analysis & Sync Hook Implementation

**Date:** March 12, 2026
**Version:** 2.2 (addendum to v2.0 + v2.1 — completes Section 4.2 placeholder, adds Sections 15-17)
**Status:** Architecture Final + Reference Implementation Ready
**Completed by:** CC (Claude Code session)

---

## Changes from v2.1

1. **Section 4.2 (Sync Hooks)** — placeholder replaced with complete design based on Cash Build System analysis
2. **New Section 15** — Cash Build System Analysis Findings (completes Handoff Plan Step 3)
3. **New Section 16** — Sync Hook Design & Rationale
4. **New Section 17** — Implementation Specifications & Deployment Guide

---

## Section 15: Cash Build System Analysis Findings

### 15.1 System Overview

**CASH = Context-Aware Session Handling** (current: v1.1-beta, 2026-03-10)

A project-agnostic build system providing:
- Branch lifecycle protocol (CREATE → WORK → REVIEW → SHIP → VERIFY)
- Notion Build Roadmap integration for PDLC tracking
- Learning loop (captures trial-and-error patterns, graduates to CLAUDE.md)
- Subagent delegation protocol with 4-block validation
- Enforcement via 6 hooks (command-type for determinism, prompt-type for judgment)

### 15.2 In-Project File Standard

| File | Purpose | Committed? |
|------|---------|------------|
| `TRACES.md` | Rolling window (~80 lines) of current & recent iterations | Yes |
| `traces/archive/milestone-N.md` | Full historical detail per 3-iteration milestone | Yes |
| `LEARNINGS.md` | Trial-and-error patterns; graduates to CLAUDE.md at compaction | Yes |
| `ROADMAP.md` | Local working copy of Notion Build Roadmap (ephemeral) | No (.gitignored) |
| `.claude/sequential-files.txt` | Files that shouldn't be edited in parallel by subagents | Yes |
| `.claude/hooks/*.sh` | Hook scripts | Yes |

### 15.3 Hook Inventory (6 Hooks)

| # | Hook Event | Type | Matcher | Script/Inline | Purpose |
|---|------------|------|---------|---------------|---------|
| 1 | **Stop** | command | — | `stop-check.sh` | Detects code changes without TRACES.md update. Exit 2 → Claude continues and updates traces. |
| 2 | **SessionStart** | command | `startup` | inline echo | REQUIRED directives: read TRACES, check Roadmap for Verifying items, scan LEARNINGS. |
| 3 | **SessionStart** | command | `compact` | inline sed | Re-injects TRACES.md header after context compaction. |
| 4 | **PreToolUse** | prompt | `Agent` | inline | Validates subagent calls have 4 blocks: CONSTRAINTS, FILE ALLOWLIST, TASK, SUCCESS CRITERIA. |
| 5 | **PreToolUse** | command | `Edit\|Write` | `check-sequential-files.sh` | Advisory warning when subagent edits a sequential file. Never blocks. |
| 6 | **PostToolUseFailure** | prompt | `Bash\|Edit\|Write` | inline | Nudges logging of failed→working patterns to LEARNINGS.md. |

### 15.4 Execution Model

**Command-type hooks:**
- Run as shell subprocesses. Receive JSON on stdin with context (`cwd`, `tool_input`, `agent_type`, `stop_hook_active`).
- Exit 0 = allow/stop. Exit 1 = error. Exit 2 = continue with stderr fed to Claude as context.
- Stdout → fed to Claude as additional context.
- Zero LLM token cost. Deterministic.

**Prompt-type hooks:**
- Text injected into Claude's context for LLM evaluation.
- Claude decides whether to block (respond `{ok: false}`) or allow.
- Costs tokens but enables judgment-based decisions.

**Ordering:** Hooks within a group fire together. Multiple groups for the same event fire sequentially. If ANY command hook exits 2, Claude continues (regardless of other hooks' exit codes).

### 15.5 Stop Hook Lifecycle (Critical for Sync Design)

The Stop hook has a two-phase lifecycle that sync hooks must account for:

```
Phase 1: Claude tries to stop
  → stop-check.sh fires
  → If code changed but TRACES.md stale:
      exit 2 + stderr "update traces"
      → Claude continues, updates TRACES.md
  → If traces are fresh OR no code changes:
      exit 0 → session ends

Phase 2 (only if Phase 1 continued):
  Claude tries to stop again
  → stop-check.sh fires, stop_hook_active=true → exit 0
  → Session ends
```

**Key insight:** Stop hooks fire 1-2 times per session end. Sync hooks must handle both cases without duplicate side effects.

### 15.6 Deployment Status

| Project | Version | Hook Scripts | Config |
|---------|---------|-------------|--------|
| Flight Mode | v1.1-beta | stop-check.sh, check-sequential-files.sh | All 6 hooks |
| Skills Factory | v1.1-beta | Both scripts | All 6 hooks |
| AI CoS CC ADK | Partial | None (prompt-type only) | 3 hooks |
| Other projects | — | — | Not deployed |

### 15.7 Key Integration Insights

1. **The startup hook is pure context injection.** It echoes text that becomes a REQUIRED directive for Claude. Sync pull can use the same pattern — output text that tells Claude about inbox messages.

2. **The stop hook enforces a workflow.** It doesn't do the work (updating traces) — it forces Claude to do the work by preventing session end. The sync prompt hook should follow this pattern: tell Claude WHAT to update, let Claude do it.

3. **Command hooks are fire-and-forget.** `stop-check.sh` and `check-sequential-files.sh` never modify project files directly — they only influence Claude's behavior through exit codes and output. `sync-push.sh` breaks this pattern intentionally: it modifies files (state.json, inbox.jsonl) and runs git operations. This is safe because sync-push only modifies `.claude/sync/` files (its own domain).

4. **The ROADMAP.md checkout/commit model is a proven sync precedent.** ROADMAP.md is a local working copy of Notion data, rebuilt on session start and optionally committed back. `state.json` follows the same pattern: mechanical fields updated by hook, semantic fields updated by Claude, pushed to GitHub.

---

## Section 16: Sync Hook Design

### 16.1 Design Principles

1. **Piggyback, don't parallel.** Sync hooks fire at the same events as Cash Build System hooks. They're additional hooks in the same configuration, not a separate system.

2. **Command for mechanics, prompt for semantics.** Git pull/push and timestamp updates are command-type (deterministic, zero token cost). Session summaries and decision logging are prompt-type (leverage Claude's understanding).

3. **Never block.** Sync hooks always exit 0. A failed git push or missing jq should never prevent session start or end. Sync is valuable but not critical.

4. **Idempotent across retries.** Because Stop fires 1-2 times, all sync-push operations must handle repeated execution: state.json overwrites are naturally idempotent; inbox appends use a dedup marker.

5. **Defensive defaults.** If `.claude/sync/` doesn't exist, hooks exit immediately. No errors, no warnings. Projects without sync enabled are unaffected.

### 16.2 The Three Sync Hooks

```
┌─────────────────────────────────────────────────────────────────────┐
│ SESSION START                                                        │
│                                                                      │
│  Cash Build System hooks:                                            │
│  ┌─────────────────────────────────────────────┐                    │
│  │ [command] echo "REQUIRED: read TRACES..."    │ ← existing        │
│  │ [command] sync-pull.sh                       │ ← NEW             │
│  └─────────────────────────────────────────────┘                    │
│                                                                      │
│  sync-pull.sh:                                                       │
│    1. git pull --quiet (get CAI inbox writes)                        │
│    2. Clear push marker from previous session                        │
│    3. Parse inbox.jsonl for unacked CAI messages                     │
│    4. Output summary → Claude sees it as context                     │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ SESSION (normal work happens)                                        │
│                                                                      │
│  Claude may update .claude/sync/state.json manually during session   │
│  if significant state changes occur (e.g., after /sync-update cmd)   │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ SESSION END (Stop event)                                             │
│                                                                      │
│  Cash Build System hooks:                                            │
│  ┌─────────────────────────────────────────────┐                    │
│  │ [command] stop-check.sh                      │ ← existing        │
│  │ [command] sync-push.sh                       │ ← NEW             │
│  └─────────────────────────────────────────────┘                    │
│  ┌─────────────────────────────────────────────┐                    │
│  │ [prompt] "Update state.json semantic fields  │ ← NEW             │
│  │  and log decisions to inbox"                 │                    │
│  └─────────────────────────────────────────────┘                    │
│                                                                      │
│  Flow:                                                               │
│    1. stop-check.sh may exit 2 (traces stale) → Claude continues    │
│    2. sync-push.sh updates mechanical fields + pushes (exit 0)      │
│    3. Prompt hook tells Claude to update semantic fields             │
│    4. If stop-check continued: Claude updates traces + state.json   │
│    5. Second Stop: stop-check exits 0, sync-push pushes fresh data  │
│    6. Session ends                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 16.3 Data Flow: What Updates What

```
┌──────────────────────────────────────────────────────────────────┐
│ state.json fields                                                 │
│                                                                   │
│ MECHANICAL (sync-push.sh command hook):                           │
│   .state.last_session.timestamp    ← date command                │
│   .state.key_files_changed_last_session ← git status             │
│   .updated_at                      ← date command                │
│   .updated_by                      ← "cc" (hardcoded)           │
│                                                                   │
│ SEMANTIC (prompt-type Stop hook → Claude updates):                │
│   .state.last_session.summary      ← Claude writes from context │
│   .state.current_tasks             ← Claude writes              │
│   .state.recent_decisions          ← Claude writes              │
│   .state.next_session_priorities   ← Claude writes              │
│   .state.blocked_on                ← Claude writes              │
│                                                                   │
│ STATIC (set on init/migrate, rarely changed):                     │
│   .project.*                       ← /sync-init or /sync-migrate│
│   .architecture.*                  ← manual or periodic refresh  │
│   .schema_version                  ← fixed                      │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ inbox.jsonl appends                                               │
│                                                                   │
│ AUTOMATIC (sync-push.sh):                                         │
│   type: "status" — mechanical session close message               │
│   Content: branch, last commit message, changed files             │
│   One per session (dedup via push marker)                         │
│                                                                   │
│ SEMANTIC (prompt-type Stop hook → Claude appends):                │
│   type: "decision" — architectural/design decisions               │
│   Only when Claude identifies significant decisions this session  │
│                                                                   │
│ FROM CAI (written via GitHub API or manual):                      │
│   type: "task", "question", "research", "note", etc.             │
│   Picked up by sync-pull.sh on next CC session start              │
└──────────────────────────────────────────────────────────────────┘
```

### 16.4 Handling the Double-Stop Problem

When `stop-check.sh` exits 2 (traces stale), the Stop event fires twice. Sync hooks handle this:

| Operation | First Stop | Second Stop | Idempotent? |
|-----------|-----------|-------------|-------------|
| state.json mechanical update | Writes stale timestamp | Overwrites with fresh timestamp | Yes (overwrite) |
| state.json semantic update (prompt) | Claude may not act (also told to update traces) | Claude updates semantic fields | Yes (Claude writes latest) |
| inbox.jsonl status append | Appends message, sets push marker | Marker prevents duplicate | Yes (dedup marker) |
| git commit + push | Pushes stale state | Pushes fresh state (overwrites) | Yes (latest wins) |

### 16.5 Failure Modes & Graceful Degradation

| Failure | Impact | Handling |
|---------|--------|----------|
| No internet / git push fails | Sync files updated locally but not pushed | Next session's git pull will push pending commits |
| jq not installed | state.json not updated, inbox not appended | Scripts exit 0, files unchanged |
| No `.claude/sync/` directory | Hooks do nothing | Early exit, zero overhead |
| state.json malformed | jq update fails | .tmp file not created, original preserved |
| Claude ignores prompt hook | Semantic fields stale | Mechanical fields still updated by command hook |
| inbox.jsonl missing | No status appended | Script exits 0 |

---

## REVISED: Section 4.2 — Sync Triggers (Replaces v2.1 Placeholder)

The v2.1 addendum identified that sync hooks must integrate with the Cash Build System rather than being designed independently. This section completes that design.

### 4.2 Sync Triggers: Integrated with Cash Build System

**Trigger points (mapped to Cash Build System events):**

| Event | Cash Build System Action | CC↔CAI Sync Action |
|-------|-------------------------|-------------------|
| **SessionStart (startup)** | Read TRACES, check Roadmap, scan LEARNINGS | git pull, check inbox for CAI messages |
| **SessionStart (compact)** | Re-inject TRACES.md header | (no sync action needed) |
| **Stop** | Enforce traces update if code changed | Update state.json, append inbox status, git push |
| **PreToolUse (Agent)** | Validate 4-block subagent structure | (no sync action needed) |
| **PreToolUse (Edit/Write)** | Sequential file warning | (no sync action needed) |
| **PostToolUseFailure** | Nudge LEARNINGS.md logging | (no sync action needed) |

**Only SessionStart and Stop need sync hooks.** The mid-session hooks (PreToolUse, PostToolUseFailure) are enforcement/advisory and don't produce state changes worth syncing.

**Future consideration:** A mid-session sync trigger (e.g., after major milestones) could be added as a `/sync-now` command rather than an automatic hook. This keeps the hook system simple while allowing manual sync when needed.

### 4.2.1 Prompt-Type Stop Hook Text

```
If .claude/sync/ exists and you haven't already done so this session:
(1) Update .claude/sync/state.json — set state.current_tasks,
    state.recent_decisions, and state.next_session_priorities to
    reflect this session's work. Update state.last_session.summary
    with a 1-2 sentence session summary.
(2) For any major architectural or design decisions made this session,
    append a decision message to .claude/sync/inbox.jsonl following
    the inbox protocol schema (see architecture v2.0 Section 3.2).
```

---

## Section 17: Implementation & Deployment Guide

### 17.1 Reference Implementation Files

All files are in the `hooks/` directory of this repository:

| File | Purpose |
|------|---------|
| `hooks/sync-pull.sh` | SessionStart command hook — git pull + inbox check |
| `hooks/sync-push.sh` | Stop command hook — state.json update + inbox append + git push |
| `hooks/settings-sync-fragment.json` | Reference settings.local.json showing all hooks (Cash Build System + sync) |

### 17.2 Deploying to a Project

**Prerequisites:**
- Project has `.claude/sync/` initialized (via `/sync-init` or `/sync-migrate`)
- Project has Cash Build System deployed (via `/setup-cash-build-system`)
- `jq` installed (`brew install jq`)

**Steps:**

1. **Copy hook scripts to project:**
   ```bash
   cp hooks/sync-pull.sh /path/to/project/.claude/hooks/
   cp hooks/sync-push.sh /path/to/project/.claude/hooks/
   chmod +x /path/to/project/.claude/hooks/sync-pull.sh
   chmod +x /path/to/project/.claude/hooks/sync-push.sh
   ```

2. **Update `.claude/settings.local.json`:**

   Add `sync-pull.sh` to the SessionStart startup group:
   ```json
   {
     "matcher": "startup",
     "hooks": [
       { "type": "command", "command": "echo 'REQUIRED...'" },
       { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/sync-pull.sh\"" }
     ]
   }
   ```

   Add `sync-push.sh` to the Stop group and add the prompt hook:
   ```json
   "Stop": [
     {
       "hooks": [
         { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/stop-check.sh\"" },
         { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/sync-push.sh\"" }
       ]
     },
     {
       "hooks": [
         {
           "type": "prompt",
           "prompt": "If .claude/sync/ exists and you haven't already done so this session: (1) Update .claude/sync/state.json — set state.current_tasks, state.recent_decisions, and state.next_session_priorities to reflect this session's work. Update state.last_session.summary with a 1-2 sentence session summary. (2) For any major architectural or design decisions made this session, append a decision message to .claude/sync/inbox.jsonl following the inbox protocol schema."
         }
       ]
     }
   ]
   ```

3. **Add push marker to .gitignore:**
   ```
   # CC↔CAI sync internal
   .claude/sync/.last-push
   ```

4. **Verify:**
   ```bash
   # Test sync-pull (should exit 0 silently if no unread messages)
   echo '{"cwd": "/path/to/project"}' | /path/to/project/.claude/hooks/sync-pull.sh

   # Test sync-push (should update state.json and attempt push)
   echo '{"cwd": "/path/to/project"}' | /path/to/project/.claude/hooks/sync-push.sh
   ```

### 17.3 Deploying Without Cash Build System

For projects that DON'T use the Cash Build System, sync hooks can be deployed standalone:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/sync-push.sh\"" }
        ]
      },
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "If .claude/sync/ exists and you haven't already done so this session: (1) Update .claude/sync/state.json — set state.current_tasks, state.recent_decisions, and state.next_session_priorities to reflect this session's work. Update state.last_session.summary with a 1-2 sentence session summary. (2) For any major architectural or design decisions made this session, append a decision message to .claude/sync/inbox.jsonl following the inbox protocol schema."
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/sync-pull.sh\"" }
        ]
      }
    ]
  }
}
```

No stop-check.sh, no sequential file check, no TRACES — just sync.

### 17.4 Deployment Order

| Priority | Action | Effort | Dependency |
|----------|--------|--------|------------|
| **Do first** | Deploy to pilot project (ai-cos-mcp) | 10 min | Step 4 (pilot .claude/sync/) |
| **Then** | Deploy to Flight Mode, Skills Factory | 10 min each | Existing Cash Build System |
| **Then** | Integrate into `/sync-init` command | 30 min | Step 5 |
| **Then** | Integrate into `/sync-migrate` command | 30 min | Step 6 |
| **Last** | Build `/sync-now` for manual mid-session sync | 1 hour | Optional |

---

## Updated Phase Plan (v2.2 Changes Only)

### Phase 3A — COMPLETE: Sync Hook Design

**Before (v2.1):** Placeholder — "examine Cash Build System, then design"

**After (v2.2):**
- Cash Build System analysis complete (Section 15)
- Three sync hooks designed: `sync-pull.sh` (SessionStart), `sync-push.sh` (Stop), prompt-type Stop
- Reference implementations built and documented
- Integration with existing 6-hook Cash Build System validated
- Deployment guide written

**Remaining for Phase 3A:** Deploy to pilot project (requires Steps 4-5 from handoff plan)

### New: Step 3.5 in Handoff Plan

Insert between existing Steps 3 and 4:

**Step 3.5: Validate Sync Hooks Locally**

Test the hook scripts in isolation before deploying:
```bash
# Simulate SessionStart
echo '{"cwd": "/path/to/project"}' | .claude/hooks/sync-pull.sh

# Simulate Stop
echo '{"cwd": "/path/to/project"}' | .claude/hooks/sync-push.sh

# Verify state.json was updated
cat .claude/sync/state.json | jq .updated_at

# Verify inbox got a status message
tail -1 .claude/sync/inbox.jsonl | jq .
```

---

## Summary: What v2.2 Adds

| Aspect | v2.1 (placeholder) | v2.2 (complete) |
|--------|--------------------|-----------------|
| Cash Build System understanding | "TBD — examine in CC" | Full 6-hook analysis with execution model |
| Sync trigger design | "Fire at same points as CBS" | Three hooks: pull (command), push (command), semantic update (prompt) |
| Stop hook lifecycle | Not addressed | Double-stop handling with dedup marker |
| Implementation | None | Two shell scripts + settings reference |
| Deployment | Not addressed | Step-by-step guide for CBS and non-CBS projects |
| Failure modes | Not addressed | 6 failure modes documented with graceful degradation |
