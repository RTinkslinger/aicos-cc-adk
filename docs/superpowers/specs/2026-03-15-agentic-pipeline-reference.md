# Agentic Pipeline Reference

**Date:** 2026-03-15
**Purpose:** Define what "pipeline" means in an agentic architecture. Catalog all pipelines. Identify what's still stuck in script mindset.

---

## Script Pipeline vs Agent Pipeline

### Script Pipeline (old world)
```
cron → Python orchestrator → call API → process result → write to DB → publish
```
- Every step is a Python function
- The orchestrator is Python code with for-loops and try/except
- Retries are Python loops with exponential backoff
- Error tracking is external (Python lists, counters, logs)
- The pipeline "knows" its steps — hardcoded in code
- Monitoring = check Python exit codes + query DB for missing rows

### Agent Pipeline (new world)
```
trigger → Agent receives task/prompt → Agent reasons → Agent calls tools → Agent handles errors → Agent returns result
```
- Every DECISION is an agent decision (what to do, how to retry, what went wrong)
- The orchestrator IS the agent's reasoning (Claude's extended thinking)
- Retries are the agent deciding "that failed, let me try differently"
- Error tracking is in the agent's conversation context (it SEES every tool call and result)
- The pipeline "knows" its steps via system prompt instructions
- Monitoring = check agent output (ResultMessage) + structured logs + observable outcomes

### The correct split: Infrastructure vs Intelligence

| Concern | Owner | Why |
|---------|-------|-----|
| **Timer triggers** (5-min, 10-min) | Infrastructure (Python/cron) | Agents don't wake themselves up |
| **Loop management** (for each video) | Infrastructure (Python) | Looping is mechanical, not intelligent |
| **Timeout enforcement** | Infrastructure (asyncio.wait_for) | Hard limits need hard enforcement |
| **Health monitoring** | Infrastructure (bash/cron) | Agent checking agents is circular |
| **Backups** | Infrastructure (pg_dump/cron) | Operational, not intelligent |
| **Content analysis** | Agent (ClaudeSDKClient) | Requires reasoning, context, judgment |
| **Tool selection** | Agent | Which method to use, when to retry |
| **Error handling** | Agent | Reason about what went wrong, adapt |
| **Completeness tracking** | Agent | It has conversation context showing all calls |
| **Conflict resolution** | Agent | Requires judgment about which data wins |
| **Action generation** | Agent | Requires understanding context + implications |

**Key principle:** Python handles plumbing. Agents handle thinking. Never use Python to verify agent decisions — that's the agent's job.

---

## Agent Queues

Agents can maintain and use queues through their tools:

1. **Input queue:** Web Agent extraction results → Content Agent receives them via MCP tool call. Not a traditional queue — it's a tool response.
2. **Write-ahead queue:** `sync_queue` Postgres table. Infrastructure-level retry for failed Notion writes. This is NOT an agent queue — it's a system reliability mechanism.
3. **Change events queue:** `change_events` Postgres table. Sync Agent processes unprocessed events. The agent queries this via its tools and reasons about what to do.

**Agent-native queue pattern:** An agent can:
- Query a "what's pending?" tool → get items to process
- Process each item using its reasoning + tools
- Mark items as processed via a tool call
- Handle failures by reasoning about them (retry, skip, escalate)

This is different from a Python loop draining a queue — the agent DECIDES how to handle each item.

---

## All Pipelines in Our System

### 1. Content Pipeline (5-min timer)

| Step | Script Version | Agent Version |
|------|---------------|---------------|
| Trigger | cron → pipeline.sh | asyncio timer in server.py |
| Extract | Python extraction.py (yt-dlp) | Content Agent calls Web Agent `extract_youtube` |
| Filter | Python keyword heuristic | Agent reasoning about relevance (or keep as pre-filter) |
| Analyze | Python Claude API call (single-shot) | Agent SDK autonomous reasoning with tools |
| Publish | Python publishing.py | Agent calls `publish_digest` tool |
| DB write | Python notion_client.py direct | Agent calls Sync Agent `write_digest` via MCP |
| Verify | Python hooks tracking tool calls | Agent's own conversation context |

**What's still script-mindset in our code:**
- `content/server.py:run_content_pipeline()` — Python orchestrator with for-loop
- `content/hooks.py:verify_pipeline_completion` — Python tracking agent's work

**Assessment:** The Python orchestrator (trigger + for-loop) is CORRECT infrastructure. The completion tracking hook is WRONG — that's the agent's job.

### 2. Sync Cycle (10-min timer)

| Step | Script Version | Agent Version |
|------|---------------|---------------|
| Trigger | cron → sync_agent.py | asyncio timer in server.py |
| Thesis sync | Python sequential calls | Sync Agent reasons about what to sync |
| Actions sync | Python sequential calls | Sync Agent reasons about conflicts |
| Queue drain | Python loop with try/except | Sync Agent reasons about retries |
| Change processing | Python rule-based generation | Sync Agent reasons about what actions to generate |

**What's still script-mindset in our code:**
- `sync/server.py:_sync_loop()` — Python calling tools sequentially
- `sync/tools.py:cos_full_sync()` — Python calling sub-tools in order

**Assessment:** The sequential sync calls are borderline. For simple "pull status, push changes," Python is efficient and correct. For complex changes (conviction → High, status transitions), the agent.py SDK reasoning is the right approach. Current hybrid is acceptable.

### 3. Web Task (on-demand)

| Step | Agent Version |
|------|---------------|
| Trigger | MCP tool call from caller |
| Reasoning | Agent SDK autonomous tool selection |
| Execution | Agent calls browse/scrape/search tools |
| Retry | Agent reasons about failures |
| Result | Structured output to caller |

**Assessment:** This is fully agentic already. No script-mindset issues.

### 4. Health Monitoring (1-min cron)

**Assessment:** Correctly infrastructure. A bash script checking HTTP endpoints. Not agentic — and shouldn't be.

### 5. Postgres Backup (daily cron)

**Assessment:** Correctly infrastructure. pg_dump is operational, not intelligent.

---

## Script-Mindset Debt Inventory

Items in our codebase that are stuck in script thinking when they should be agentic:

| # | File | Issue | Should Be |
|---|------|-------|-----------|
| 1 | `content/hooks.py:verify_pipeline_completion` | Python tracks which tools agent called | DELETE — agent tracks its own completeness |
| 2 | `content/hooks.py:_tools_by_session` (C4 dict) | Python state accumulation across hooks | DELETE — no state needed |
| 3 | `content/server.py` relevance filtering | Python keyword heuristic pre-filters videos | KEEP (efficiency pre-filter) or MOVE to agent reasoning |
| 4 | `sync/tools.py` sequential sync calls | Python calls sync steps in fixed order | ACCEPTABLE — simple operations don't need reasoning |
| 5 | Various try/except in tools.py | Python catches errors, returns error dicts | ACCEPTABLE — infrastructure error handling, not decision-making |

**Items correctly in infrastructure (should NOT be agentic):**
- Timer triggers (asyncio loops in server.py)
- asyncio.wait_for timeout enforcement
- Write-ahead queue (Postgres sync_queue)
- Health check cron (bash script)
- deploy.sh, systemd units, log rotation

---

## Action Items (post-audit)

After completing all 25 audit issues, return to this document and:
1. ~~Resolve items 1-2 (delete verify_pipeline_completion + tracking state)~~ DONE in C4 fix
2. Evaluate item 3 (relevance filtering — keep as pre-filter or move to agent?)
3. Scan for any NEW script-mindset patterns introduced during audit fixes
4. Update the design spec (§4 Content Agent) to remove completion hook references

### URGENT: Migrate psycopg2 → asyncpg

**Priority: Do immediately after completing audit review.**

psycopg2 is synchronous — every `_get_conn()` + `cur.execute()` call BLOCKS the asyncio event loop. This is the ONLY scenario where the agent server can truly hang (all other hangs are handled by agent-level timeouts).

- **Scope:** 39 connection opens across 5 files (thesis_db, actions_db, preferences, change_detection, tools.py)
- **Migration:** Replace `psycopg2.connect()` → `await asyncpg.connect()`, `cur.execute()` → `await conn.fetch()`
- **Alternative:** Wrap all psycopg2 calls in `await loop.run_in_executor(None, blocking_func)` (less clean but lower risk)
- **Test impact:** All DB-dependent tests need update
- **Blocks:** Nothing — can be done independently after audit
