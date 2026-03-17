# AI CoS Agent Architecture v2.2 — Design Spec

**Date:** 2026-03-15
**Status:** APPROVED — ready for implementation
**Supersedes:** `2026-03-15-three-agent-architecture-design.md` (v1), `2026-03-15-three-agent-architecture-v2-stub.md` (stub)
**SDK:** claude-agent-sdk 0.1.48 (Python), bundled CLI 2.1.71

---

## 1. Design Principles

1. **Fully Agentic First.** Agents reason, decide, and act via instructions + tools. Token/API costs are not a design constraint. Optimize for cost later by selectively moving proven workflows to fixed code. Never the reverse.

2. **Extensible by Instruction, Not by Code.** New content sources, scoring criteria, output formats = instruction/skill changes. Code changes only for genuinely new capabilities (new tools) or new rendering (frontend).

3. **Agent Behavior = Instructions (.md files).** Each agent's behavior is governed by its `system_prompt.md`. Python handles infrastructure (timers, connections, tool implementations). The agent's reasoning — driven by instructions — handles everything else.

4. **Postgres Access is Universal, Locality Determines Method.** `shared/db/` serves State MCP for CAI. Local agents use Bash + psql directly. Skills teach agents the DB schema.

5. **Flag-Based Sync.** Agents write to Postgres with `notion_synced = false`. Sync Agent's periodic cycle pushes unsynced rows to Notion. No separate sync_queue table. The database IS the queue.

6. **Infrastructure vs Intelligence.** Python handles plumbing: timers, connections, tool implementations, health checks, process lifecycle. Agents handle thinking: what to fetch, how to process, when to retry, what to write. Never use Python to verify agent decisions.

7. **CAI is a Relay, Not an Executor.** CAI captures Aakash's intent, writes to the inbox, and moves on. Heavy lifting happens async on the droplet. Communication is through shared Postgres state, not direct calls.

8. **Agent = Model + Instructions + MCPs + Skills + System Tools + Hooks.** Mirrors Claude Code architecture exactly. Agent SDK is the same harness as CC.

---

## 2. Taxonomy

### Core Concepts

| Term | Definition | CC Parallel |
|------|-----------|------------|
| **Agent** | ClaudeSDKClient with instructions, tools, hooks, reasoning. Runs as a process on the droplet. | Claude in a project |
| **Instructions** | `system_prompt.md` — identity, rules, domain knowledge. Primary config layer. | CLAUDE.md |
| **MCP** | Tool server providing capabilities via tools. Stateful or stateless. | Playwright MCP, Notion MCP |
| **Tool** | Callable capability on an MCP or built-in. Agent calls by name. | Read, Write, mcp__notion__search |
| **Skill** | Markdown instruction file loaded on demand. Intelligence as text. Agent decides when to load. | CC skills (.claude/skills/) |
| **Hook** | Lifecycle callback on agent events. Runs in app process, zero context cost. | CC hooks |
| **Session** | One agent reasoning conversation. Prompt → tool calls → result. | CC conversation |
| **Scheduled Session** | Timer-triggered session. asyncio timer fires → agent gets prompt → agent reasons. | (no CC parallel) |

### Implementation Patterns

| Pattern | What It Means |
|---------|--------------|
| **In-Process Tool** | `@tool` + `create_sdk_mcp_server()`. Python function in agent's process. |
| **External MCP Tool** | HTTP call to another MCP server. SDK handles natively. |
| **Gateway** | Tool on State MCP that wraps `shared/db/` for remote callers (CAI). |
| **Async Task** | Submit/poll/retrieve pattern for long-running work (like Parallel MCP). |

### Tool Naming Convention

SDK standard: `mcp__<server_key>__<tool_name>`

---

## 3. Consumer Tiers

| | CAI | CC | Custom Agents (droplet) |
|--|-----|-----|------------------------|
| **Where** | Anthropic cloud | Aakash's Mac | Droplet (always on) |
| **Interface** | Persistent chat | Terminal session | No chat UI |
| **Built-in tools** | None | Full | Full (same as CC) |
| **MCPs** | Yes (HTTP only) | Yes (local + HTTP) | Yes (local + HTTP) |
| **Skills** | No | Yes | Yes |
| **Availability** | Always on | When terminal open | Always on |

**CAI is the only persistent conversational interface.** It's always available and is Aakash's gateway to everything on the droplet. But CAI is MCP-only — no skills, no Bash, no built-in tools. The droplet compensates.

**CC is not a primary consumer** of what we're building. If Aakash wants to give CC access to droplet tools, he configures it himself.

---

## 4. Communication Pattern

```
CAI → Agents:  post_message (State MCP) → cai_inbox table → Agent reads via psql
Agents → CAI:  Agent writes to notifications table via psql → CAI reads via get_state (State MCP)
```

Both flow through Postgres. State MCP is CAI's window into shared state. No direct connections, no webhooks, no persistent sessions between CAI and agents.

---

## 5. Full Inventory

### Layer 1: MCPs (Tool Servers on Droplet)

#### State MCP (port 8000, mcp.3niac.com) — for CAI only

| # | Tool | Params | Direction | Purpose |
|---|------|--------|-----------|---------|
| 1 | `get_state` | `include?: ["thesis","notifications"]` | CAI reads | Thesis threads (name, conviction, status) + pending notifications |
| 2 | `create_thesis_thread` | `name, core_thesis` | CAI writes | Insert to Postgres (notion_synced=false) |
| 3 | `update_thesis` | `thesis_name, evidence, direction?` | CAI writes | Update Postgres (notion_synced=false) |
| 4 | `post_message` | `type, content, metadata?` | CAI → Agents | Write to cai_inbox table |
| 5 | `health_check` | — | Infra | Liveness + DB connectivity |

Implementation: Python FastMCP server. Tool handlers import `shared/db/`. No agent brain.

#### Web Tools MCP (port 8001, web.3niac.com) — for CAI (async tasks) + Content Agent (tools)

**CAI surface (async task pattern — like Parallel MCP):**

| # | Tool | Params | Purpose |
|---|------|--------|---------|
| 1 | `web_task_submit` | `task, url?, output_schema?` | Start background ClaudeSDKClient with web skills. Returns `{task_id, status}` immediately. |
| 2 | `web_task_status` | `task_id` | Lightweight poll: `{task_id, status, elapsed_s, cost_usd?}` |
| 3 | `web_task_result` | `task_id` | Full result when status="complete" |

**Content Agent + subagent surface (direct tools):**

| # | Tool | Params | Purpose |
|---|------|--------|---------|
| 4 | `web_browse` | `url, action?, readiness_mode?` | Playwright navigation (SPA, JS-heavy) |
| 5 | `web_scrape` | `url, use_firecrawl?` | Jina Reader + Firecrawl with fallback |
| 6 | `web_search` | `query, limit?` | Firecrawl search |
| 7 | `extract_youtube` | `playlist_url?, video_urls?, since_days?` | YouTube extraction via yt-dlp + cookies |
| 8 | `extract_transcript` | `video_id` | Single video transcript |
| 9 | `fingerprint` | `url` | Site classification |
| 10 | `check_strategy` | `domain` | UCB bandit query |
| 11 | `manage_session` | `action, domain, state_json?` | storageState save/load/check |
| 12 | `validate` | `content, url, expected_type?` | Content quality scoring |
| 13 | `cookie_status` | — | Cookie freshness |
| 14 | `watch_url` | `url, interval_min?, notify?` | URL monitoring (Phase 2) |

**Shared:**

| 15 | `health_check` | — | Liveness + Playwright status |

**Internal (web_task brain — SDK @tools for ClaudeSDKClient):**

| # | Tool | Purpose |
|---|------|---------|
| 1 | `browse` | Playwright navigation + readiness ladder |
| 2 | `scrape` | Jina Reader + Firecrawl |
| 3 | `search` | Firecrawl search |
| 4 | `screenshot` | Visual page capture |
| 5 | `interact` | Click, fill, evaluate JS |
| 6 | `fingerprint` | Site classification |
| 7 | `check_strategy` | UCB bandit query |
| 8 | `manage_session` | storageState ops |
| 9 | `validate` | Content quality scoring |

Manages: Playwright browser, SQLite strategy cache (`/opt/agents/data/strategy.db`), storageState JSONs, cookie files.

---

### Layer 2: Skills (Intelligence as Markdown)

#### Web Skills — loaded by web_task brain + Content Agent + web-researcher subagent

| # | File | Content | Source |
|---|------|---------|--------|
| 1 | `skills/web/strategy.md` | When to scrape vs browse vs search. Domain patterns. UCB bandit interpretation. Readiness ladder. | Extract from existing code + system prompt |
| 2 | `skills/web/anti-detection.md` | Persona profiles, stealth, fingerprint coherence, timing. | Extract from web/lib/stealth.py |
| 3 | `skills/web/auth-escalation.md` | 5-step auth ladder: storageState → cookies → fresh sync → Browserbase → human. | Extract from existing system prompt |
| 4 | `skills/web/content-validation.md` | Quality scoring, login wall detection, empty content, retry-on-poor-score. | Extract from web/lib/quality.py |
| 5 | `skills/web/youtube-extraction.md` | Playlist handling, dedup, transcript fallback, cookie requirements. | Extract from web/lib/extraction.py |

#### Content Skills — loaded by Content Agent

| # | File | Content | Source |
|---|------|---------|--------|
| 6 | `skills/content/analysis.md` | IDS methodology, content analysis framework, thesis connections, portfolio relevance. | Extract from CONTEXT.md + system prompt |
| 7 | `skills/content/scoring.md` | 5-factor scoring formula + weights + thresholds (≥7 surface, 4-6 low-confidence, <4 context). Agent calculates directly. | Extract from lib/scoring.py |
| 8 | `skills/content/thesis-reasoning.md` | Conviction spectrum, key questions lifecycle, evidence assessment, contra signals. | Extract from CONTEXT.md |
| 9 | `skills/content/publishing.md` | Digest JSON format, git push workflow, Vercel auto-deploy, schema requirements. | Extract from content/lib/publishing.py |
| 10 | `skills/content/inbox-handling.md` | CAI Inbox message types, routing rules, watch list management. | NEW |

#### Sync Skills — loaded by Sync Agent

| # | File | Content | Source |
|---|------|---------|--------|
| 11 | `skills/sync/conflict-resolution.md` | Human-owned fields win (Status, Outcome). AI-vs-AI: timestamp wins. Conflict logging. | Extract from spec §11 |
| 12 | `skills/sync/notion-patterns.md` | Notion API patterns, property formatting, rate limits, field ownership. | Extract from docs/notion/ |
| 13 | `skills/sync/change-interpretation.md` | Change event interpretation, action generation rules, notification triggers. | Extract from sync/lib/change_detection.py |

#### Data Skills — loaded by all agents

| # | File | Content | Source |
|---|------|---------|--------|
| 14 | `skills/data/postgres-schema.md` | All table schemas, column types, query patterns, $DATABASE_URL, write convention (notion_synced=false). | NEW — derived from existing DB |

---

### Layer 3: Agent System Prompts

#### Content Agent — `content/system_prompt.md`

- **Identity:** AI CoS Content Analyst for Aakash Kumar (MD at Z47 + DeVC)
- **Inbox protocol:** Check cai_inbox table every 1-min cycle. Process by type. Mark processed.
- **Content cycle:** Every 5-min cycle: check watch list sources, fetch new content, analyze, score, publish, write to Postgres.
- **Watch list:** Maintain `/opt/agents/data/watch_list.json`. Add/remove via inbox messages.
- **Analysis:** Load content skills. Connect to thesis threads. Score every item.
- **Publishing:** Load publishing skill. Git push to aicos-digests.
- **DB access:** Bash + psql. Follow data/postgres-schema skill.
- **Web access:** Bash + curl/Jina/Firecrawl for stateless. Web Tools MCP for Playwright-dependent ops. Load web skills for strategy.
- **Delegation:** Class 2 (complex web research) → spawn web-researcher via Agent tool (run_in_background). Class 3 (parallel batch) → spawn content-worker subagents.
- **Notifications:** Write to notifications table for significant events.
- **Conviction guardrail:** Provide evidence. Never set conviction autonomously.

#### Sync Agent — `sync/system_prompt.md`

- **Identity:** AI CoS Sync Agent. Background worker. Postgres ↔ Notion.
- **Sync cycle:** Every 10 min: find unsynced rows, push to Notion, pull human-owned field changes.
- **Notion access:** Bash + python3 scripts (complex API).
- **Conflict resolution:** Load sync/conflict-resolution skill.
- **Change detection:** Detect changes, log to change_events. Load sync/change-interpretation skill.
- **Notifications:** Write to notifications table for significant sync events.
- **DB access:** Bash + psql. Follow data/postgres-schema skill.
- **Sync metadata:** Update sync_metadata table after each cycle.

---

### Layer 4: Agent Configurations

#### Content Agent

```python
ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    system_prompt=read_file("content/system_prompt.md"),
    permission_mode="dontAsk",
    allowed_tools=[
        # CC built-in tools
        "Bash", "Read", "Write", "Grep", "Glob",
        # Subagent spawning
        "Agent",
        # Skill loading
        "Skill",
        # Web Tools MCP (all direct tools)
        "mcp__web__web_browse", "mcp__web__web_scrape",
        "mcp__web__web_search", "mcp__web__extract_youtube",
        "mcp__web__extract_transcript", "mcp__web__fingerprint",
        "mcp__web__check_strategy", "mcp__web__manage_session",
        "mcp__web__validate", "mcp__web__cookie_status",
        "mcp__web__watch_url",
    ],
    mcp_servers={
        "web": {"type": "http", "url": "http://localhost:8001/mcp"},
    },
    agents={
        "web-researcher": AgentDefinition(
            description="Full-capability web research specialist for complex multi-step tasks",
            prompt=read_file(".claude/agents/web-researcher.md"),
            tools=[
                "Bash", "Read", "Write", "Skill",
                "mcp__web__web_browse", "mcp__web__web_scrape",
                "mcp__web__web_search", "mcp__web__extract_youtube",
                "mcp__web__extract_transcript", "mcp__web__fingerprint",
                "mcp__web__check_strategy", "mcp__web__manage_session",
                "mcp__web__validate", "mcp__web__cookie_status",
                "mcp__web__watch_url",
            ],
        ),
        "content-worker": AgentDefinition(
            description="Lightweight content analysis worker for parallel batch processing",
            prompt="Analyze the given content using skills and psql. Score relevance, identify thesis connections.",
            tools=["Bash", "Read", "Write", "Skill"],
        ),
    },
    setting_sources=["project"],
    thinking={"type": "enabled", "budget_tokens": 10000},
    effort="high",
    cwd="/opt/agents",
    env={"ANTHROPIC_API_KEY": "...", "DATABASE_URL": "...", "FIRECRAWL_API_KEY": "..."},
)
```

Scheduled sessions: **1-min** inbox check + **5-min** content cycle

#### Sync Agent

```python
ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    system_prompt=read_file("sync/system_prompt.md"),
    permission_mode="dontAsk",
    allowed_tools=[
        "Bash", "Read", "Write", "Grep", "Glob",
        "Skill",
    ],
    setting_sources=["project"],
    thinking={"type": "enabled", "budget_tokens": 5000},
    effort="medium",
    cwd="/opt/agents",
    env={"ANTHROPIC_API_KEY": "...", "DATABASE_URL": "...", "NOTION_TOKEN": "..."},
)
```

Scheduled sessions: **10-min** sync cycle

#### web-researcher subagent — `.claude/agents/web-researcher.md`

```markdown
---
name: web-researcher
description: Full-capability web research specialist for complex, multi-step
  web tasks requiring strategy, authentication, and deep browsing
tools:
  - Bash
  - Read
  - Write
  - Skill
  - mcp__web__web_browse
  - mcp__web__web_scrape
  - mcp__web__web_search
  - mcp__web__extract_youtube
  - mcp__web__extract_transcript
  - mcp__web__fingerprint
  - mcp__web__check_strategy
  - mcp__web__manage_session
  - mcp__web__validate
  - mcp__web__cookie_status
  - mcp__web__watch_url
---

You are a web research specialist with the full web toolkit.

Load web skills (skills/web/) for strategy, anti-detection, auth escalation,
and content validation. Use Bash + curl/Jina for quick fetches. Use web_browse
for SPAs. Use check_strategy before approaching unfamiliar domains. Always
validate content quality before returning.

Complete the research task thoroughly and return a comprehensive result.
```

#### content-worker subagent — `.claude/agents/content-worker.md`

```markdown
---
name: content-worker
description: Lightweight content analysis worker for parallel batch processing
tools:
  - Bash
  - Read
  - Write
  - Skill
---

You are a content analysis worker. Analyze the given content using skills and
Bash + psql for DB access. Score relevance, identify thesis connections,
generate action proposals. Load content skills for methodology. Load
data/postgres-schema skill for DB conventions.

Return structured analysis result.
```

---

### Layer 5: Shared Infrastructure

#### Postgres Tables

| # | Table | Status | Written by | Read by |
|---|-------|--------|-----------|---------|
| 1 | `thesis_threads` | Existing | Content Agent, CAI (State MCP) | Content Agent, Sync Agent, CAI |
| 2 | `actions` | Existing | Content Agent | Sync Agent, Content Agent |
| 3 | `content_digests` | Existing | Content Agent | Sync Agent, Content Agent |
| 4 | `action_outcomes` | Existing | Content Agent | Content Agent |
| 5 | `change_events` | Existing | Sync Agent | Sync Agent |
| 6 | `sync_metadata` | **NEW** | Sync Agent | Any agent (psql) |
| 7 | `cai_inbox` | **NEW** | CAI (State MCP) | Content Agent |
| 8 | `notifications` | **NEW** | Content Agent, Sync Agent | CAI (State MCP) |

All applicable tables have `notion_synced` boolean column.

#### shared/db/ — State MCP implementation ONLY

| Module | Purpose |
|--------|---------|
| `connection.py` | asyncpg pool for State MCP |
| `thesis_db.py` | Thesis CRUD for State MCP tools |
| `inbox.py` | CAI Inbox read/write |
| `notifications.py` | Notifications read/write |

NOT used by agents — agents use Bash + psql.

#### Filesystem Data

| Path | Purpose | Managed by |
|------|---------|-----------|
| `/opt/agents/data/watch_list.json` | Content sources tracking | Content Agent |
| `/opt/agents/data/strategy.db` | SQLite UCB bandit cache | Web Tools MCP |
| `/opt/agents/data/sessions/` | Playwright storageState | Web Tools MCP |
| `/opt/agents/cookies/` | Domain cookies (synced from Mac) | Cookie sync cron |
| `/opt/agents/logs/` | Structured JSON logs | Each process |
| `/opt/agents/skills/` | All skill markdown files | Deployed via deploy.sh |
| `/opt/agents/CONTEXT.md` | Domain context | deploy.sh |
| `/opt/agents/.claude/agents/` | Subagent definitions | deploy.sh |

#### Processes on Droplet

| # | Process | Type | Port | systemd unit |
|---|---------|------|------|-------------|
| 1 | State MCP | Tool server | 8000 | `state-mcp.service` |
| 2 | Web Tools MCP | Tool server + async runner | 8001 | `web-tools-mcp.service` |
| 3 | Content Agent | Agent (scheduled) | — | `content-agent.service` |
| 4 | Sync Agent | Agent (scheduled) | — | `sync-agent.service` |

Content Agent and Sync Agent have no ports — internal only, triggered by timers.

#### Cloudflare Tunnels

| DNS | Routes to | Consumer |
|-----|----------|---------|
| mcp.3niac.com | localhost:8000 | CAI → State MCP |
| web.3niac.com | localhost:8001 | CAI → Web Tools MCP |

#### Cron / Infrastructure

| Job | Interval | Purpose |
|-----|----------|---------|
| Health check | 60s | curl /health on ports 8000, 8001. Restart on failure. |
| Postgres backup | daily 02:00 UTC | pg_dump, 7-day retention |
| Cookie sync | daily 06:00 (Mac) | Safari cookies → droplet |
| Log rotation | daily | logrotate for /opt/agents/logs/ |

---

### Layer 6: Access Matrix

| Capability | CAI | Content Agent | Sync Agent | Web Tools MCP |
|-----------|-----|--------------|------------|---------------|
| State MCP tools | Yes (5 tools) | No | No | No |
| Web Tools MCP (async) | Yes (3 tools) | No | No | — |
| Web Tools MCP (direct) | No | Yes (12 tools) | No | — |
| Bash | No | Yes | Yes | No |
| Read/Write/Grep/Glob | No | Yes | Yes | No |
| Agent tool (subagents) | No | Yes | No | No |
| Skill tool | No | Yes | Yes | No |
| Web Skills | No | Yes | No | Yes (web_task) |
| Content Skills | No | Yes | No | No |
| Sync Skills | No | No | Yes | No |
| Data Skills | No | Yes | Yes | No |
| Postgres (psql) | No (via State MCP) | Yes (Bash) | Yes (Bash) | No (via shared/db/) |
| Notion API | No | No | Yes (exclusive) | No |
| CAI Inbox write | Yes (post_message) | No | No | No |
| CAI Inbox read | No | Yes (psql) | No | No |
| Notifications write | No | Yes (psql) | Yes (psql) | No |
| Notifications read | Yes (get_state) | No | No | No |

---

## 6. Content Agent — Three Classes of Work

**Class 1: Direct — agent uses tools + skills**
- Bash + curl/Jina/Firecrawl for stateless web ops
- Web Tools MCP for stateful ops (Playwright, strategy, sessions)
- Web + Content skills loaded on demand
- Bash + psql for all DB access

**Class 2: Complex delegation — background agent (run_in_background: true)**
- Agent tool → web-researcher subagent with FULL web toolkit
- Subagent inherits Web Tools MCP, has all tools + skills
- Runs independently, Content Agent continues other work
- Functionally identical to web_task brain

**Class 3: Parallel batch — multiple lightweight subagents**
- Agent tool → N × content-worker subagents
- Each has: Bash, Read, Write, Skill, psql access
- Parallel execution for batch content analysis

**Content Agent NEVER calls web_task.** web_task exists exclusively for CAI.

---

## 7. CAI Interaction Patterns

### Reading state
```
CAI → State MCP: get_state() → thesis threads + notifications
```

### Writing thesis data
```
CAI → State MCP: create_thesis_thread(name, core_thesis)
CAI → State MCP: update_thesis(thesis_name, evidence, direction)
Both write to Postgres with notion_synced=false
```

### Relaying tasks to agents
```
CAI → State MCP: post_message({type: "track_source", content: "@person on X", ...})
→ cai_inbox table
→ Content Agent picks up on 1-min cycle
→ Content Agent processes, writes results to Postgres
→ Sync Agent syncs to Notion
→ Next CAI get_state() reflects updates
```

### Complex web tasks
```
CAI → Web Tools MCP: web_task_submit({task: "Research company X funding"})
→ Returns {task_id: "wt_abc123", status: "started"} immediately
→ CAI tells Aakash: "Started research, I'll check back"
→ Later: CAI → web_task_status("wt_abc123") → {status: "complete"}
→ CAI → web_task_result("wt_abc123") → full result
```

---

## 8. What Changed from v1

| v1 | v2.2 |
|----|------|
| Sync Agent = DB gatekeeper (23 tools) | State MCP = lightweight CAI gateway (5 tools) |
| Sync Agent proxies web tools | CAI calls Web Tools MCP directly |
| Content Agent calls Sync Agent for all writes | Content Agent writes Postgres directly (Bash + psql) |
| Custom @tools for every DB operation | Agents use Bash + skills (CC-like) |
| Web Agent = agent + tool server (mixed) | Web Tools MCP = tool server. Web intelligence = skills. |
| Agent communication via MCP tool calls | CAI → Inbox → Agent → Notifications → CAI (async, decoupled) |
| 63 files, 9,358 lines Python tools | Skills + system prompts are primary deliverables |
| Python orchestrators with for-loops | Agent reasoning drives everything |
| Extensible by code (new @tools) | Extensible by instructions + skills + tools |
| web_task for everyone | web_task exclusively for CAI (async pattern) |
| Agents blocked from Bash/Read/Write | Agents have full CC built-in tools |

---

## 9. Build Order

### Phase 1: Infrastructure
- New Postgres tables (sync_metadata, cai_inbox, notifications, notion_synced columns)
- skills/ directory structure on droplet
- .claude/agents/ directory with subagent definitions

### Phase 2: State MCP
- FastMCP server with 5 tools
- shared/db/ modules (asyncpg)
- Cloudflare tunnel on mcp.3niac.com (repoint from old Sync Agent)

### Phase 3: Web Tools MCP
- Restructure from existing web agent code
- Add external surface for check_strategy, manage_session, validate
- Add async task pattern (web_task_submit/status/result)
- Keep internal SDK @tools for web_task brain
- Cloudflare tunnel on web.3niac.com

### Phase 4: Skills
- Extract all 14 skills from existing code, system prompts, and docs
- Deploy to /opt/agents/skills/

### Phase 5: Content Agent
- New system_prompt.md (the brain)
- Agent config with Bash, Agent, Skill, Web Tools MCP
- Subagent definitions (web-researcher, content-worker)
- Infrastructure: timer for 1-min inbox + 5-min content cycle
- Test: inbox processing, content analysis, publishing, web delegation

### Phase 6: Sync Agent
- New system_prompt.md
- Agent config with Bash, Skill
- Infrastructure: timer for 10-min sync cycle
- Notion sync scripts (python3)
- Test: flag-based sync, conflict resolution, notifications

### Phase 7: Integration
- End-to-end: CAI → inbox → Content Agent → Postgres → Sync Agent → Notion
- CAI → web_task_submit → result
- Content Agent delegation → web-researcher → result
- Cutover from old services
- Monitoring, health checks, log rotation
