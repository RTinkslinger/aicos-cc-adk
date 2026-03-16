# OpenClaw Architecture — Ultra Research Report

**Source:** Parallel Task MCP (ultra processor)
**Run ID:** trun_4719934bf6364778aa2e5ec7a1d3c6fc
**Date:** 2026-03-16
**32 sources cited**

---

## Key Takeaways for Our Architecture

### 1. Gateway-as-Control-Plane
OpenClaw's Gateway (Node.js WebSocket server) owns session state, routing, scheduling, and access control. It's the single source of truth. Our equivalent: the thin Python lifecycle manager + systemd.

### 2. Heartbeat runs in MAIN SESSION
Heartbeat prompts are injected into the agent's existing persistent session — NOT a new session. The agent has full context of everything prior. `lightContext: true` strips heavy bootstrap files to save tokens.

### 3. Memory is file-first
Agents are "stateless between turns" — their memory relies on reading/writing Markdown files (SOUL.md, AGENTS.md, memory/YYYY-MM-DD.md). Pre-compaction memory flush writes durable state to disk before context overflow.

### 4. Compaction is critical and dangerous
Append-only JSONL sessions need summarization (compaction) to manage context limits. BUT compaction can orphan tool_result blocks, permanently bricking sessions. Must sanitize transcripts.

### 5. Session persistence is automatic
Sessions stored as `.jsonl` files. Resume by ID after crash. Fork for branching. Expire based on idle time.

### 6. Multi-agent: sessions_send + sessions_spawn
- `sessions_send`: peer-to-peer messaging between active sessions (ping-pong, up to 5 turns)
- `sessions_spawn`: native sub-agents in isolated sessions, return results via "announce"
- ACP: external coding harnesses (Claude Code, Codex) as agents

### 7. Cost optimization is mandatory
- Unoptimized 30m heartbeat with 100k context = 4.8M input tokens/day
- With lightContext + activeHours = ~14K tokens/day
- Prompt caching helps but compaction invalidates it
- `cache-ttl` pruning removes old tool_results from memory without deleting from disk

---

## Full Report

[Content from ultra research follows]

---

## Executive Summary

OpenClaw (formerly Clawdbot/Moltbot) operates not as a simple chatbot wrapper, but as an operating system for AI agents. By decoupling the interface layer from the intelligence runtime, it provides a persistent, tool-using assistant accessible across multiple platforms.

Five critical strategic insights:
* **Gateway-as-Control-Plane is the Backbone:** A single WebSocket Gateway owns session state, routing, scheduling, and access control.
* **Heartbeats Require Strict Context Constraints:** Default heartbeats can cause severe token burn and context bloat. Enabling `lightContext` and tuning `activeHours` are mandatory.
* **Memory Persistence is File-First:** "Memory" relies entirely on reading and writing Markdown files. A built-in "pre-compaction memory flush" writes durable state to disk before context overflow.
* **Compaction is Powerful but Brittle:** Unmitigated compaction can orphan `tool_result` blocks, permanently bricking sessions.
* **Multi-Agent Patterns are Native:** Inter-session messaging (`sessions_send`), native sub-agents (`sessions_spawn`), and ACP for external harnesses.

---

## 1. Architecture — One Gateway Orchestrates Sessions, Tools, Channels, and Schedules

### Core Components
* **Gateway (Control Plane):** `src/gateway/server.ts` — Node.js WebSocket server (ws://127.0.0.1:18789). Routes messages, enforces access control, schedules cron/heartbeat.
* **Agent Runtime:** `src/agents/piembeddedrunner.ts` — resolves sessions, assembles context, streams model responses, executes tool calls.
* **Channels:** Adapters for WhatsApp, Telegram, Discord, Slack — normalize messages into session keys.
* **Sessions & Memory:** `sessions.json` metadata + `<sessionId>.jsonl` append-only event logs. Memory as plain Markdown files.

### End-to-End Message Flow
1. Message arrives via channel → Gateway
2. Gateway resolves session key, access control
3. Agent Runtime loads JSONL transcript, builds system prompt (AGENTS.md, SOUL.md, TOOLS.md)
4. Context streamed to LLM, tool_use blocks intercepted and executed
5. Results written to JSONL, output routed back to channel

---

## 2. The Heartbeat System

### Complete Flow
1. **Timer Tick:** Gateway scheduler fires (default 30m). Checks activeHours.
2. **Session Resolution:** Targets agent's main session (or override).
3. **Prompt Injection:** Verbatim: "Read HEARTBEAT.md if it exists. Follow it strictly. If nothing needs attention, reply HEARTBEAT_OK."
4. **lightContext:** If enabled, strips heavy bootstrap files, keeps only HEARTBEAT.md.
5. **Execution:** Agent runs turn in main session with full context.
6. **Suppression:** HEARTBEAT_OK at start/end + remaining text ≤ 300 chars → dropped. Alerts delivered.

### Known Issues
- Double-fire race conditions with manual wake during active heartbeat
- Steer mode can swallow user messages arriving during heartbeat

---

## 3. Session Management

### Storage
- `sessions.json`: key/value metadata (sessionId, updatedAt, tokenCounts, compactionCount)
- `<sessionId>.jsonl`: append-only transcripts (message, tool events, compaction summaries)

### Lifecycle
- **Create:** On first message
- **Resume:** Gateway reads sessions.json, parses JSONL to rebuild context
- **Fork:** Branching via parentId pointers (for editing past messages)
- **Expire:** Based on idleMinutes or daily reset (default 4:00 AM)

### Pre-Compaction Memory Flush
1. When contextTokens exceeds threshold, Gateway triggers silent agentic turn
2. Agent writes durable memories to memory/YYYY-MM-DD.md
3. Agent replies NO_REPLY (suppressed)
4. Standard compaction proceeds safely

### Failure Modes
- **Orphaned tool_result blocks:** Compaction truncates mid-tool-call → session bricked. Fix: transcript-sanitize extension.
- **Global lock contention:** Single sessions.json file lock → stuck session blocks all channels.

---

## 4. Agent Configuration — Markdown Brain

### Bootstrap Files (injected into system prompt)
1. **AGENTS.md:** Operating manual, workflow rules, memory instructions
2. **SOUL.md:** Persona, tone, ethical boundaries
3. **USER.md:** Static user context
4. **TOOLS.md:** Tool conventions

### Memory System
- **Daily logs (memory/YYYY-MM-DD.md):** Append-only working context. Read today + yesterday at session start.
- **Long-term memory (MEMORY.md):** Curated facts. Only loaded in main/private sessions.
- **Tools:** `memory_search` (hybrid vector/keyword) and `memory_get` for retrieval.

---

## 5. Multi-Agent Coordination

### Three Primitives
1. **sessions_send:** Peer-to-peer messaging between active sessions. Reply ping-pong (up to 5 turns). `REPLY_SKIP` terminates loop.
2. **sessions_spawn:** Native sub-agents in isolated sessions. Returns runId immediately. Inherits AGENTS.md + TOOLS.md only. Announces results on completion.
3. **ACP (Agent Communication Protocol):** External harnesses (Claude Code, Codex, Gemini CLI) as agents. Persistent thread bindings.

### Orchestrator Pattern
`maxSpawnDepth: 2` — depth-1 sub-agents become orchestrators spawning depth-2 leaf workers.

---

## 6. Cron vs Heartbeat + Lobster

| Feature | Heartbeat | Cron |
|---------|-----------|------|
| Session | Main (shared history) | Isolated (clean slate) |
| Timing | Interval (~30m) | Exact cron expression |
| Context | Full | None (isolated) |
| Model | Main session model | Can override |
| Output | Suppressed if HEARTBEAT_OK | Announce summary |

### Lobster Workflow Runtime
- Deterministic YAML/JSON pipelines as single tool calls
- Built-in approval gates (needs_approval + resumeToken)
- Resumable without re-running previous steps

---

## 7. Production Patterns

### What Works
1. **Daily Digest:** Cron (isolated) at exact time, opus model, announce to WhatsApp
2. **Inbox Monitor:** Heartbeat (main session) every 30-60m, 3-bullet HEARTBEAT.md checklist
3. **Deterministic Side-Effects:** Lobster for email triage, git commits with approval gates

### Common Failures
- **Context Bloat:** Browser snapshots consume 200k context fast → enable cache-ttl pruning
- **Compaction Amnesia:** Chat-only instructions lost → enforce memory protocol in AGENTS.md
- **Heartbeat Token Waste:** Full history in heartbeats → enable lightContext

---

## 8. Cost and Performance

- **Unoptimized heartbeat (30m, 100k context):** ~4.8M input tokens/day
- **Optimized (lightContext + activeHours 14h):** ~14K input tokens/day
- **Compaction invalidates prompt cache** → delay via cache-ttl pruning
- Gateway is lightweight Node.js. Heavy usage from Chromium + local embeddings.

---

## 9. Claude Agent SDK Mapping

| OpenClaw | Claude Agent SDK | Scaffolding Needed |
|----------|-----------------|-------------------|
| Gateway | None built-in | Custom server for routing |
| Agent Runtime | ClaudeSDKClient / query() | Built-in |
| Session Persistence | continue/resume | Automatic .jsonl |
| Sub-Agents | forkSession | Built-in |
| Tools & Sandboxing | allowedTools | Custom wrappers |

---

## 10. Source Code

- `src/gateway/server.ts` — WebSocket server, lifecycle
- `src/gateway/server-methods.ts` — RPC handlers (chat, cron, sessions, tools)
- `src/agents/piembeddedrunner.ts` — Core execution loop
- `src/config/sessions.ts` — Session schema, key resolution
- `src/auto-reply/reply/memory-flush.ts` — Pre-compaction memory flush

---

## References (32 sources)

[See full citation list in original report]
