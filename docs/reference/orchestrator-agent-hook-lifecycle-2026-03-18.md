# Orchestrator Agent — Hook Lifecycle Reference

*Last verified: 2026-03-18T08:25:00Z against `mcp-servers/agents/orchestrator/.claude/`*
*Updated: 2026-03-18T08:25:00Z — cross-referenced with content agent pipeline timestamp fix*

## Overview

The Orchestrator Agent is a persistent `ClaudeSDKClient` session managed by `lifecycle.py`. It receives "heartbeat" prompts every 60 seconds and follows a 5-step checklist (HEARTBEAT.md). Its only tool for delegation is `send_to_content_agent` via the bridge MCP server.

**Source files:**
- `.claude/settings.json` — hook registration (3 shell hooks)
- `.claude/hooks/stop-iteration-log.sh` — Stop hook
- `.claude/hooks/prompt-manifest-check.sh` — UserPromptSubmit hook
- `.claude/hooks/pre-compact-flush.sh` — PreCompact hook
- `lifecycle.py:269-292` — PostToolUse hook (Python, live logging)

---

## Hook Inventory

| Hook Event | Type | Script/Function | When It Fires |
|------------|------|-----------------|---------------|
| **UserPromptSubmit** | Shell | `prompt-manifest-check.sh` | Before agent processes each heartbeat `query()` |
| **PostToolUse** | Python | `_make_tool_hook(ORC_LIVE_LOG)` | After every tool call (Bash, Read, send_to_content_agent, etc.) |
| **PreCompact** | Shell | `pre-compact-flush.sh` | Before SDK auto-compaction (safety net) |
| **Stop** | Shell | `stop-iteration-log.sh` | After agent completes each heartbeat response |

---

## Event Flow: Normal Heartbeat (Work Found)

```
lifecycle.py heartbeat loop: has_work() returns reason string
│
├── 1. orc_client.query("heartbeat")
│
├── 2. UserPromptSubmit FIRES
│      Script: prompt-manifest-check.sh
│      │
│      ├── Read traces/manifest.json
│      ├── Sum input_tokens + output_tokens for "orc"
│      ├── If total > 100,000:
│      │   ├── Write to stderr: "COMPACTION REQUIRED: Session at N tokens..."
│      │   └── Exit 2 (inject context)
│      │   └── Agent sees "COMPACTION REQUIRED" prepended to "heartbeat"
│      └── If total <= 100,000:
│          └── Exit 0 (proceed normally)
│
├── 3. AGENT PROCESSES HEARTBEAT (follows HEARTBEAT.md checklist)
│      │
│      ├── Step 1: Check for checkpoint
│      │   └── If state/orc_checkpoint.md exists → read, absorb, delete
│      │
│      ├── Step 2: Inbox check
│      │   ├── psql: SELECT unprocessed from cai_inbox
│      │   ├── If messages → combine into numbered prompt
│      │   └── Call send_to_content_agent(inbox_prompt)
│      │       └── PostToolUse FIRES (Python) → log to orchestrator/live.log
│      │       └── Bridge: if content busy → returns "still processing"
│      │       └── Bridge: if content free → query(prompt), return "Prompt sent"
│      │   └── If "Prompt sent" → UPDATE cai_inbox SET processed = TRUE
│      │
│      ├── Step 3: Pipeline schedule check
│      │   └── Skip if content agent is busy from Step 2
│      │   └── Read last_pipeline_run.txt
│      │   └── If missing or >12h → send_to_content_agent("Run your content pipeline cycle...")
│      │       └── PostToolUse FIRES (Python) → log to orchestrator/live.log
│      │
│      ├── Step 4: Traces compaction check
│      │   └── Read orc_iteration.txt → if divisible by 30 → run compaction per COMPACTION_PROTOCOL.md
│      │
│      └── Step 5: Write iteration log
│          └── Write one-line summary to state/orc_last_log.txt
│
├── 4. RESPONSE COMPLETES (ResultMessage received by heartbeat loop)
│      ├── Update manifest tokens
│      ├── Log cost/turns
│      ├── If result contains "COMPACT_NOW" → set orc_needs_restart
│      ├── Track consecutive_zero_turns (0 turns = dead session risk)
│      └── PostToolUse fires for each tool call made during processing
│
└── 5. Stop FIRES
       Script: stop-iteration-log.sh
       │
       ├── Guard: if stop_hook_active == true → exit 0
       ├── Read state/orc_session.txt → session number
       ├── Read state/orc_iteration.txt → current iteration
       ├── Increment iteration: N → N+1, write back
       ├── Read state/orc_last_log.txt → one-line summary
       ├── Clear orc_last_log.txt
       ├── Format: "$orc | sess #N | it M | HH:MM UTC :: 'summary'"
       └── Append to traces/{active_traces_file}
```

---

## Event Flow: Idle Heartbeat (No Work)

```
lifecycle.py: has_work() returns None
│
├── Log "idle (no work)"
├── sleep 60s
└── LOOP (no query sent, no hooks fire)
```

**Key point:** When `has_work()` returns None, no heartbeat `query()` is sent. The orchestrator agent is completely idle — no hooks fire, no tokens consumed.

---

## Event Flow: Compaction

```
PATH A — Agent-driven (primary)
│
├── 1. UserPromptSubmit detects tokens > 100K
│      └── Injects "COMPACTION REQUIRED"
│
├── 2. Agent writes checkpoint to state/orc_checkpoint.md
│      └── Includes: heartbeat interval, active traces, content agent status, pending work
│
├── 3. Agent ends response with "COMPACT_NOW"
│
├── 4. Heartbeat loop detects "COMPACT_NOW"
│      └── Sets orc_needs_restart = True
│
├── 5. Stop FIRES (iteration logged)
│
├── 6. Heartbeat loop breaks (orc_needs_restart check)
│      └── run_agent() outer loop restarts:
│          ├── Stop content client
│          ├── bump_session for both agents
│          ├── Start fresh content client
│          ├── Create new bridge
│          └── Start fresh orchestrator
│
└── 7. New session: agent reads checkpoint → absorbs → deletes → resumes


PATH B — SDK auto-compaction (safety net)
│
├── 1. PreCompact FIRES
│      ├── If orc_checkpoint.md exists → exit 0 (don't overwrite)
│      └── If not: write emergency checkpoint (last 30 trace lines + recovery instructions)
│
├── 2. SDK compacts context
│
└── 3. Agent continues with reduced context
```

**Important difference from Content Agent:** When the orchestrator compacts, it triggers a full restart of BOTH agents (orchestrator + content). The orchestrator's compaction is more disruptive because it exits the heartbeat loop entirely.

---

## Event Flow: Dead Session Detection

```
1. Heartbeat sent → agent responds with 0 turns (no tool calls, no meaningful work)
   └── consecutive_zero_turns += 1

2. Next heartbeat → again 0 turns
   └── consecutive_zero_turns reaches 2

3. Log "SESSION DEAD"
   └── Set orc_needs_restart = True

4. Heartbeat loop breaks → full restart of both agents
```

This catches scenarios where the orchestrator's context is corrupted and it can't follow HEARTBEAT.md. Two consecutive empty responses = restart.

---

## Event Flow: Crash Recovery

```
1. Exception in heartbeat loop or agent processing
   └── Caught by outer while True in run_agent()

2. sleep 5s

3. Full restart of BOTH agents
   ├── Content client stopped + restarted
   ├── Orchestrator stopped + restarted
   └── Both get new session numbers

4. State file persistence:
   ├── state/orc_session.txt — bumped to N+1
   ├── state/orc_iteration.txt — reset to 0
   ├── state/orc_checkpoint.md — survives (read on next heartbeat Step 1)
   ├── state/orc_last_log.txt — survives (may be stale)
   └── traces/manifest.json — reset for new session
```

---

## Orchestrator vs Content Agent: Key Differences

| Aspect | Orchestrator | Content Agent |
|--------|-------------|---------------|
| **Prompt source** | lifecycle.py heartbeat loop ("heartbeat") | Bridge tool call (variable prompts) |
| **Prompt frequency** | Every 60s (when work exists) | On-demand (inbox or pipeline schedule) |
| **Idle behavior** | `has_work()` returns None → no query, no hooks | Waits for bridge call, no hooks |
| **Compaction impact** | Restarts BOTH agents | Restarts only content agent |
| **Dead session detection** | Yes (consecutive_zero_turns) | No (lifecycle.py doesn't monitor content responses for liveness) |
| **Hook scripts** | Identical structure, AGENT="orc" | Identical structure, AGENT="content" |
| **PostToolUse** | Logs to orchestrator/live.log | Logs to content/live.log |
| **Unique tools** | `send_to_content_agent` (bridge) | Agent (subagents), Skill, 10 Web Tools MCP |

---

## State Files

| File | Written By | Read By | Lifecycle |
|------|-----------|---------|-----------|
| `state/orc_session.txt` | lifecycle.py (`bump_session`) | Stop hook | Monotonically increasing |
| `state/orc_iteration.txt` | Stop hook (increment) / lifecycle.py (reset) | Stop hook, HEARTBEAT.md Step 4 | Reset to 0 on session bump |
| `state/orc_last_log.txt` | Orchestrator agent (HEARTBEAT.md Step 5) | Stop hook (read + clear) | Cleared after each Stop |
| `state/orc_checkpoint.md` | Orchestrator agent or PreCompact hook | Orchestrator agent (HEARTBEAT.md Step 1) | Deleted after absorption |

---

## Hook Input/Output Reference

### Stop Hook Input (JSON via stdin)
```json
{
  "cwd": "/opt/agents/orchestrator",
  "stop_hook_active": false,
  "session_id": "...",
  "transcript_summary": "..."
}
```

### UserPromptSubmit Input (JSON via stdin)
```json
{
  "cwd": "/opt/agents/orchestrator",
  "prompt": "heartbeat",
  "session_id": "..."
}
```

### Exit Codes
| Code | Meaning |
|------|---------|
| `0` | Proceed normally |
| `1` | Error (hook failed, agent continues) |
| `2` | Continue with stderr injected as additional context |

---

## Anti-Patterns

1. **Don't send complex prompts to the orchestrator** — it only processes "heartbeat". All intelligence comes from HEARTBEAT.md + CLAUDE.md.
2. **Don't assume idle heartbeats fire hooks** — when `has_work()` returns None, no `query()` is sent. Zero hooks fire. Zero tokens consumed.
3. **Don't treat orchestrator compaction as content-only** — orchestrator compaction restarts BOTH agents.
4. **Don't assume content agent liveness is monitored** — dead session detection only applies to the orchestrator. A stuck content agent stays stuck until `content_busy` timeout or crash.
