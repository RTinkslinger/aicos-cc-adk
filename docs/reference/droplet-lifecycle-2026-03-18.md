# `lifecycle.py` — Complete Behaviour Map

*Last verified: 2026-03-18T08:25:00Z against `mcp-servers/agents/orchestrator/lifecycle.py`*
*Updated: 2026-03-18T08:25:00Z — added pipeline timestamp fix documentation*

## What It Is

A Python asyncio process (`mcp-servers/agents/orchestrator/lifecycle.py`) that manages **two persistent ClaudeSDKClient sessions** on the droplet: an **Orchestrator agent** and a **Content Agent**, connected via an `@tool` bridge.

---

## Startup Sequence (`main()` → `run_agent()`)

```
1. main()
   ├── Register SIGTERM + SIGINT handlers → set stop_event
   ├── Create asyncio task: run_agent()
   └── await stop_event (blocks until signal)

2. run_agent() — outer infinite loop
   ├── Reset content manifest tokens
   ├── Start content agent (ClaudeSDKClient.__aenter__)
   ├── Log to content/live.log: "Content agent started — session #N"
   ├── Reset orc manifest tokens
   ├── Create @tool bridge server (MCP server with send_to_content_agent tool)
   ├── Start orchestrator (ClaudeSDKClient context manager)
   ├── Log to orchestrator/live.log: "Orchestrator started — session #N"
   └── Enter heartbeat loop
```

---

## Heartbeat Loop (the core cycle, every 60s)

```
WHILE orchestrator not needing restart:
│
├── 1. CHECK CONTENT RESTART
│      If content_needs_restart flag is set:
│      └── restart_content_client()
│          ├── Stop old client (__aexit__)
│          ├── bump_session("content") → increment session counter, reset iteration to 0
│          ├── Reset manifest tokens for new session
│          ├── Start new content client (__aenter__)
│          └── Clear flag
│          NOTE: bump_session does NOT clean state/ files beyond iteration counter.
│                Files like last_pipeline_run.txt, checkpoints, and any flags persist.
│
├── 2. PRE-CHECK: has_work() — FREE (no LLM call)
│      Checks run sequentially with EARLY RETURN — first match wins:
│      │
│      ├── Check 1: Query Postgres: SELECT count(*) FROM cai_inbox WHERE processed = FALSE
│      │   └── If > 0 → return "inbox has N unprocessed messages" (STOPS HERE)
│      │   └── If query fails → return "inbox check failed, waking agent to be safe" (STOPS HERE)
│      │
│      ├── Check 2 (only reached if inbox is empty):
│      │   Read content/state/last_pipeline_run.txt
│      │   └── If missing or empty → return "pipeline never ran" (STOPS HERE)
│      │   └── If > 12 hours old → return "pipeline overdue (Xh since last run)" (STOPS HERE)
│      │   └── If read fails → return "pipeline check failed, waking agent to be safe" (STOPS HERE)
│      │
│      └── If BOTH checks pass (no inbox, pipeline recent) → return None
│          └── Log "idle (no work)" → sleep 60s → LOOP
│
├── 3. SEND HEARTBEAT TO ORCHESTRATOR (LLM call)
│      ├── Log: ">>> heartbeat ({work_reason})"
│      ├── orc_client.query("heartbeat")
│      └── Stream response via receive_response():
│          ├── AssistantMessage → extract ThinkingBlock, TextBlock, ToolUseBlock → write to live.log
│          ├── ResultMessage → update manifest tokens, log cost/turns
│          │   ├── If result contains "COMPACT_NOW" → set orc_needs_restart
│          │   ├── If num_turns == 0 → increment consecutive_zero_turns
│          │   └── If num_turns > 0 → reset consecutive_zero_turns
│          └── (The orchestrator may call send_to_content_agent during this)
│
├── 4. DEAD SESSION DETECTION
│      If consecutive_zero_turns >= 2:
│      └── Log "SESSION DEAD" → set orc_needs_restart
│
└── 5. SLEEP 60s → LOOP
```

---

## What the Orchestrator Agent Does (per heartbeat, driven by HEARTBEAT.md)

The orchestrator is a Claude session that receives "heartbeat" and follows a 5-step checklist:

```
Step 1: Check for checkpoint
        └── If state/orc_checkpoint.md exists → read, absorb, delete, log resume

Step 2: Inbox check
        └── psql: SELECT unprocessed from cai_inbox
            ├── Messages found → combine into numbered prompt → send_to_content_agent
            │   ├── If "busy" → skip, retry next heartbeat
            │   └── If "Prompt sent" → UPDATE cai_inbox SET processed = TRUE
            └── No messages → skip

Step 3: Pipeline schedule check (every 12 hours)
        └── Skip if content agent is busy from Step 2
        └── Read last_pipeline_run.txt
            ├── Missing or >12h old → send_to_content_agent: "Run your content pipeline cycle"
            └── <12h → skip

Step 4: Traces compaction check
        └── Read orc_iteration.txt → if divisible by 30 → run compaction

Step 5: Write iteration log to state/orc_last_log.txt
```

**Note:** Steps 2 and 3 are always separate `send_to_content_agent` tool calls, never combined into one prompt. If Step 2 sends work and the content agent becomes busy, Step 3 is skipped entirely.

---

## What the Content Agent Does (when triggered by orchestrator)

Two trigger types, each with a multi-phase flow:

### A. Content Pipeline Cycle ("Run your content pipeline cycle")

```
Phase 1 — Discover & Queue
  ├── Read /opt/agents/data/watch_list.json
  ├── For each active source:
  │   ├── YouTube playlists → extract_youtube MCP tool
  │   ├── Web URLs → web_scrape / web_browse
  │   └── RSS feeds → Bash + curl
  └── INSERT each URL into content_digests (status=queued, ON CONFLICT DO NOTHING = auto-dedup)

Phase 2 — Process Queue
  ├── SELECT * FROM content_digests WHERE status = 'queued'
  └── For each queued item:
      ├── UPDATE status = 'processing'
      ├── Fetch full content (transcript/article body)
      ├── Load skills: analysis.md, thesis-reasoning.md, scoring.md
      ├── Query thesis_threads from Postgres
      ├── Run 10-step analysis (thesis connections, conviction, evidence, portfolio, contra signals)
      ├── Score every proposed action (5-factor model, threshold ≥7 = surface)
      ├── Generate DigestData JSON
      ├── Write JSON to /opt/agents/data/digests/{slug}.json
      ├── Copy to /opt/aicos-digests/src/data/{slug}.json
      ├── git commit + push → Vercel auto-deploy (~15s) → live at digest.wiki
      ├── UPDATE content_digests (status=published, digest_data, digest_url, scores)
      ├── Append thesis evidence to thesis_threads in Postgres
      ├── Write actions to actions_queue (score ≥ 4)
      ├── Write notifications for high-signal items (score ≥ 7)
      └── On failure: UPDATE status = 'failed', continue to next item

Phase 3 — Wrap Up
  ├── Write timestamp to state/last_pipeline_run.txt (LLM instruction — also enforced by hooks)
  └── Write ACK summary to state/content_last_log.txt
```

**Pipeline timestamp enforcement:** The LLM instruction in Phase 3 tells the agent to write `last_pipeline_run.txt`. As a safety net, the hook system also handles this deterministically:
1. **UserPromptSubmit** detects "pipeline cycle" in prompt → sets `state/pipeline_requested.txt` flag
2. **Stop** checks: if flag exists AND agent ACK contains "Pipeline" → writes ISO timestamp to `last_pipeline_run.txt`, deletes flag
3. If flag exists without ACK match (crash/compaction) → flag cleaned, no false timestamp

See content agent hook lifecycle doc for full event flow diagrams.

### B. Inbox Message Relay

```
Parse numbered message list from orchestrator
For each message:
  ├── URL to analyze → INSERT into content_digests as queued → process via Phase 2
  ├── Research question → spawn web-researcher subagent → write results to notifications
  ├── Question about data → query Postgres → write answer to notifications
  └── Watch list change → write notification "requires manual approval" (never modify file)
End with structured ACK
```

---

## Hook Systems

Both agents have **two layers** of hooks:

### Layer 1: Python SDK Hooks (defined in lifecycle.py)

| Hook | Agent | What It Does |
|------|-------|-------------|
| **PostToolUse** | Orchestrator | Logs tool name + input snippet to `orchestrator/live.log` |
| **PostToolUse** | Content | Logs tool name + input snippet to `content/live.log` |

These are defined via `_make_tool_hook()` (lifecycle.py:102-116) and registered in `build_orc_options()` / `build_content_options()`.

### Layer 2: Shell Hooks (defined in `.claude/settings.json`)

Both agents share the same 3-hook structure with agent-specific `AGENT` variable:

| Hook Event | Script | Purpose |
|------------|--------|---------|
| **Stop** | `stop-iteration-log.sh` | Fires after every `query()` response. Increments iteration counter, reads `{agent}_last_log.txt`, appends one-line entry to shared traces file, clears log file. |
| **UserPromptSubmit** | `prompt-manifest-check.sh` | Fires before agent processes prompt. Reads `traces/manifest.json` token counts. If total > 100K threshold, injects "COMPACTION REQUIRED" via stderr (exit 2). |
| **PreCompact** | `pre-compact-flush.sh` | Safety net for SDK auto-compaction. If no agent-written checkpoint exists, writes emergency checkpoint with last 30 trace lines. |

**Critical timing detail:** Stop fires **per-query**, not per-session. Evidence: iteration counters reach 80+ within a single session (#1), incrementing every 60s. This is confirmed by the existing traces format: `$orc | sess #1 | it 84 | 23:35 UTC :: '...'`.

See the agent-specific hook lifecycle docs for detailed event flows.

---

## The @tool Bridge (`create_bridge_server`)

```
send_to_content_agent(prompt) — callable by orchestrator
  ├── If content_client is None → error
  ├── If content_busy flag → "still processing"
  ├── Otherwise:
  │   ├── Set content_busy = True
  │   ├── content_client.query(prompt)
  │   ├── Spawn background asyncio task: _read_content_response()
  │   └── Return immediately: "Prompt sent to content agent"
  │
  └── _read_content_response() (background)
      ├── Stream messages from content_client.receive_response()
      ├── Log AssistantMessage blocks to content/live.log
      ├── On ResultMessage → update manifest tokens, log cost
      ├── If "COMPACT_NOW" in response text → set content_needs_restart flag
      └── On completion → set content_busy = False
```

**Note:** When `content_busy = True`, the prompt is rejected at the bridge level — it never reaches the content agent SDK. No hooks fire. The orchestrator retries on the next heartbeat.

---

## Session Lifecycle Management

```
Compaction:
  ├── Agent outputs "COMPACT_NOW" in response
  ├── lifecycle.py detects it (in bridge for content, in heartbeat loop for orc)
  ├── Sets needs_restart flag
  └── On next loop iteration:
      ├── Stop old client (__aexit__)
      ├── bump_session(agent) → increment counter, reset iteration to 0
      ├── reset_manifest_tokens → fresh token tracking
      └── Start new client (__aenter__)
      NOTE: State files (checkpoints, flags, timestamps) are NOT cleaned by bump_session.

Dead session detection (orchestrator only):
  ├── 2 consecutive heartbeats with num_turns == 0
  └── Forces orc_needs_restart → full session restart

Crash recovery:
  └── Outer while True in run_agent() catches exceptions → sleep 5s → restart both agents
      NOTE: This restarts BOTH agents, even if only one crashed.
```

---

## Supporting Systems

| System | Mechanism |
|---|---|
| **Token tracking** | `traces/manifest.json` — cumulative input/output tokens per agent per session |
| **Live logs** | `orchestrator/live.log` + `content/live.log` — real-time tool calls, thinking, text, results (PostToolUse hooks) |
| **Session counters** | `state/{agent}_session.txt` — monotonically increasing session number |
| **Iteration counters** | `state/{agent}_iteration.txt` — resets to 0 on session bump, incremented by Stop hook per-query |
| **Iteration logs** | `state/{agent}_last_log.txt` — agent-written one-line summary, read and cleared by Stop hook |
| **Shared traces** | `traces/active.txt` pointer → `traces/traces-YYYY-MM-DD.md` — one-line per iteration per agent |
| **Graceful shutdown** | SIGTERM/SIGINT → set stop_event → cancel agent_task → stop content client |

---

## Agent Configurations Summary

| Setting | Orchestrator | Content Agent |
|---|---|---|
| Model | claude-sonnet-4-6 | claude-sonnet-4-6 |
| Thinking | off | enabled (10k budget) |
| Effort | low | high |
| Max turns | 15 | 50 |
| Max budget | $0.50/heartbeat | $5.00/prompt |
| Key tools | Bash, Read/Write/Edit, Glob, Grep, bridge | Bash, Read/Write/Edit, Grep, Glob, Agent, Skill, 10 Web Tools MCP tools |
| Subagents | none | web-researcher, content-worker |
| Python hooks | PostToolUse (live log) | PostToolUse (live log) |
| Shell hooks | Stop, UserPromptSubmit, PreCompact | Stop, UserPromptSubmit, PreCompact |
| CWD | `/opt/agents/orchestrator` | `/opt/agents/content` |
| setting_sources | `["project"]` | `["project"]` |
