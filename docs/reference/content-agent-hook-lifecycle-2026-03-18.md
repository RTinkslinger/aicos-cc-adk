# Content Agent — Hook Lifecycle Reference

*Last verified: 2026-03-18T08:25:00Z against `mcp-servers/agents/content/.claude/`*
*Updated: 2026-03-18T08:25:00Z — pipeline timestamp fix implemented and tested (13/13 tests pass)*

## Overview

The Content Agent is a persistent `ClaudeSDKClient` session managed by `lifecycle.py`. It receives prompts via the `send_to_content_agent` bridge tool and processes them sequentially. Hooks fire at specific points in each query lifecycle.

**Source files:**
- `.claude/settings.json` — hook registration (3 shell hooks)
- `.claude/hooks/stop-iteration-log.sh` — Stop hook
- `.claude/hooks/prompt-manifest-check.sh` — UserPromptSubmit hook
- `.claude/hooks/pre-compact-flush.sh` — PreCompact hook
- `lifecycle.py:298-312` — PostToolUse hook (Python, live logging)

---

## Hook Inventory

| Hook Event | Type | Script/Function | When It Fires |
|------------|------|-----------------|---------------|
| **UserPromptSubmit** | Shell | `prompt-manifest-check.sh` | Before agent processes each `query()` prompt. Two duties: (1) pipeline detection — sets `state/pipeline_requested.txt` flag if prompt contains "pipeline cycle", (2) compaction check — injects COMPACTION REQUIRED if tokens > 100K. |
| **PostToolUse** | Python | `_make_tool_hook(CONTENT_LIVE_LOG)` | After every tool call during processing |
| **PreCompact** | Shell | `pre-compact-flush.sh` | Before SDK auto-compaction (safety net) |
| **Stop** | Shell | `stop-iteration-log.sh` | After agent completes each `query()` response. Three duties: (1) iteration logging, (2) pipeline timestamp — writes `last_pipeline_run.txt` if flag exists AND ACK contains "Pipeline", (3) flag cleanup — always removes stale `pipeline_requested.txt`. |

---

## Event Flow: Normal Pipeline Cycle

```
Orchestrator calls send_to_content_agent("Run your content pipeline cycle...")
│
├── 1. QUERY ARRIVES → content_client.query(prompt)
│
├── 2. UserPromptSubmit FIRES
│      Script: prompt-manifest-check.sh
│      Input: JSON with { cwd, prompt, ... }
│      │
│      ├── Pipeline detection:
│      │   ├── Extract prompt text from input JSON (.prompt // .message)
│      │   ├── If prompt contains "pipeline cycle":
│      │   │   └── touch state/pipeline_requested.txt (flag for Stop hook)
│      │   └── If prompt does NOT contain "pipeline cycle":
│      │       └── No flag set (inbox relay, research, etc.)
│      │
│      ├── Context limit check:
│      │   ├── Read traces/manifest.json
│      │   ├── Sum input_tokens + output_tokens for "content"
│      │   ├── If total > 100,000:
│      │   │   ├── Write to stderr: "COMPACTION REQUIRED: Session at N tokens..."
│      │   │   └── Exit 2 (inject context, continue processing)
│      │   │   └── Agent sees "COMPACTION REQUIRED" prepended to its prompt
│      │   └── If total <= 100,000:
│      │       └── Exit 0 (proceed normally)
│      │
│      └── NOTE: Both pipeline detection AND compaction can fire on the same prompt.
│
├── 3. AGENT PROCESSES (LLM reasoning + tool calls)
│      ├── Phase 1: Discover & Queue (watch list → INSERT content_digests)
│      ├── Phase 2: Process Queue (fetch → analyze → score → publish)
│      ├── Phase 3: Wrap Up (write last_pipeline_run.txt, write ACK)
│      │
│      └── For EACH tool call during processing:
│          └── PostToolUse FIRES (Python hook)
│              └── Writes to content/live.log: "TOOL: {name} | {input_snippet}"
│
├── 4. RESPONSE COMPLETES (ResultMessage received by _read_content_response)
│      ├── Update manifest tokens
│      ├── Log cost/turns to live.log
│      ├── If response contains "COMPACT_NOW" → set content_needs_restart
│      └── Set content_busy = False
│
└── 5. Stop FIRES
       Script: stop-iteration-log.sh
       Input: JSON with { cwd, stop_hook_active, ... }
       │
       ├── Guard: if stop_hook_active == true → exit 0 (prevent double-fire)
       ├── Read state/content_session.txt → session number
       ├── Read state/content_iteration.txt → current iteration
       ├── Increment iteration: N → N+1, write back
       ├── Read state/content_last_log.txt → one-line summary (written by agent)
       ├── Clear content_last_log.txt (truncate to 0 bytes)
       ├── If summary empty → default to "did nothing"
       ├── Format: "$content | sess #N | it M | HH:MM UTC :: 'summary'"
       ├── Append to traces/{active_traces_file}
       │
       └── Pipeline timestamp (two-condition check):
           ├── If state/pipeline_requested.txt exists:
           │   ├── If summary contains "pipeline" (case-insensitive):
           │   │   └── Write ISO timestamp to state/last_pipeline_run.txt
           │   └── Always: delete pipeline_requested.txt (clean stale flags)
           └── If no flag: skip (inbox/research/compaction — no timestamp)
```

---

## Event Flow: Inbox Relay (No Pipeline)

```
Orchestrator calls send_to_content_agent("Process these inbox messages: ...")
│
├── 1. UserPromptSubmit FIRES
│      └── Same compaction check as pipeline. Prompt does NOT contain "pipeline cycle".
│
├── 2. AGENT PROCESSES
│      ├── Parse messages, handle each (research, URL analysis, data query)
│      ├── Write ACK summary to content_last_log.txt
│      └── PostToolUse fires per tool call
│
└── 3. Stop FIRES
       └── Same iteration logging as pipeline cycle
```

**Key difference:** No `last_pipeline_run.txt` write. The pipeline timestamp only updates on explicit pipeline cycles, not inbox processing.

---

## Event Flow: Compaction (Token Threshold Exceeded)

```
Two compaction paths exist:

PATH A — Agent-driven (primary, via UserPromptSubmit)
│
├── 1. UserPromptSubmit detects tokens > 100K
│      └── Injects "COMPACTION REQUIRED" via stderr (exit 2)
│
├── 2. Agent writes checkpoint to state/content_checkpoint.md
│      └── Includes: current state, pending work, recent context, key facts
│
├── 3. Agent ends response with "COMPACT_NOW"
│
├── 4. _read_content_response() detects "COMPACT_NOW"
│      └── Sets content_needs_restart = True
│
├── 5. Stop FIRES (response completed, iteration logged)
│
├── 6. Next heartbeat loop: restart_content_client()
│      ├── Stop old client
│      ├── bump_session("content") → increment session #, reset iteration to 0
│      └── Start new client
│
└── 7. New session starts → agent reads checkpoint → absorbs state → deletes checkpoint


PATH B — SDK auto-compaction (safety net, via PreCompact)
│
├── 1. SDK decides to compact (internal threshold, different from our 100K check)
│
├── 2. PreCompact FIRES
│      Script: pre-compact-flush.sh
│      ├── If checkpoint already exists → exit 0 (don't overwrite agent-written checkpoint)
│      └── If no checkpoint:
│          ├── Read last 30 lines from active traces file
│          └── Write emergency checkpoint to state/content_checkpoint.md
│              (Marked: "Written by PreCompact hook, NOT by agent")
│
├── 3. SDK compacts context in-place (session continues, NOT restarted)
│
└── 4. Agent continues processing with reduced context
       └── Stop fires normally at end of response
```

---

## Event Flow: Crash Recovery

```
1. Agent crashes mid-processing
   └── Exception caught by outer while True in lifecycle.py run_agent()

2. sleep 5s

3. BOTH agents restart (full restart, not just content)
   ├── Reset content manifest tokens
   ├── Start new content client
   ├── Create new bridge server
   ├── Start new orchestrator

4. State file persistence:
   ├── state/content_session.txt — survives (bumped by restart logic)
   ├── state/content_iteration.txt — reset to 0
   ├── state/content_checkpoint.md — survives (if written before crash)
   ├── state/last_pipeline_run.txt — survives (whatever was last written)
   ├── state/content_last_log.txt — survives (may contain partial data)
   └── Any flag files — SURVIVE (not cleaned by bump_session)

5. First heartbeat after restart:
   ├── has_work() runs
   ├── Checkpoint exists → agent reads it, absorbs state, deletes it
   └── Normal processing resumes
```

**Known gap:** `bump_session()` only resets the iteration counter. Other state files (flags, partial logs) persist across session boundaries. Code changes that add flag files to `state/` must account for this.

---

## State Files

| File | Written By | Read By | Lifecycle |
|------|-----------|---------|-----------|
| `state/content_session.txt` | lifecycle.py (`bump_session`) | Stop hook | Monotonically increasing, never reset |
| `state/content_iteration.txt` | Stop hook (increment) / lifecycle.py (reset) | Stop hook, compaction check | Reset to 0 on session bump |
| `state/content_last_log.txt` | Content agent (LLM) | Stop hook (read + clear) | Cleared after each Stop |
| `state/content_checkpoint.md` | Content agent or PreCompact hook | Content agent on restart | Deleted after absorption |
| `state/last_pipeline_run.txt` | Stop hook (deterministic) + Content agent Phase 3 (LLM) | lifecycle.py `has_work()` | Persists across sessions. Written when both conditions met: pipeline_requested flag + pipeline ACK. |
| `state/pipeline_requested.txt` | UserPromptSubmit hook (pipeline detection) | Stop hook (two-condition check) | Ephemeral flag. Created on pipeline prompt, deleted by Stop hook (always, even if pipeline didn't complete). Does NOT persist across successful Stop. |

---

## Hook Input/Output Reference

### Stop Hook Input (JSON via stdin)
```json
{
  "cwd": "/opt/agents/content",
  "stop_hook_active": false,
  "session_id": "...",
  "transcript_summary": "..."
}
```

### UserPromptSubmit Input (JSON via stdin)
```json
{
  "cwd": "/opt/agents/content",
  "prompt": "Run your content pipeline cycle...",
  "session_id": "..."
}
```

### Exit Codes
| Code | Meaning |
|------|---------|
| `0` | Proceed normally (hook ran successfully) |
| `1` | Error (hook failed, agent continues) |
| `2` | Continue with stderr content injected as additional context |

---

## Anti-Patterns

1. **Don't assume Stop fires on session end** — it fires per-query. A persistent session may have 100+ Stop events.
2. **Don't rely on `bump_session` for cleanup** — it only resets iteration. Other state files persist.
3. **Don't write state in PreCompact** — it's a safety net. The agent's own checkpoint (Path A) takes priority.
4. **Don't assume UserPromptSubmit sees internal turns** — it fires on the orchestrator's `query()` call, not on agent-internal tool loops.
