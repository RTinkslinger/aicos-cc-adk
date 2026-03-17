# Three-Agent Architecture — Unified Design Spec

**Date:** 2026-03-15
**Status:** LOCKED — post-audit, user-approved (2026-03-15)
**Replaces:** `2026-03-15-web-agent-v2-design.md` (standalone WebAgent spec, now obsolete)
**SDK:** claude-agent-sdk 0.1.48 (Python), bundled CLI 2.1.71

---

## 1. Decision Log

All architectural decisions from 3 rounds of clarifying questions:

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | YouTube extraction ownership | **Web Agent extracts**, Content Agent analyzes | yt-dlp fetches from the web — Web Agent's domain. Clean separation of concerns. |
| 2 | Agent communication model | **MCP tool calls** + write-ahead queue fallback | Most agentic, scalable, typed, auditable. Write-ahead queue (already built) for reliability. |
| 3 | MCP topology | **Sync Agent as gateway** (mcp.3niac.com) | CC connects wherever. CAI/agents go through Sync Agent. Extract Orchestrator when Events Agent arrives. |
| 4 | digest.wiki publishing | **Content Agent publishes directly** | Content artifact, not a DB record. Sync Agent handles Notion/Postgres only. |
| 5 | All agents on Agent SDK | **Mandatory** — ClaudeSDKClient with custom tools, hooks, thinking | "When we say agent we mean only claude agent sdk built custom agents." |
| 6 | Sync Agent runtime | **Long-running systemd MCP server** with internal sync timer | Always available for MCP calls. Periodic sync internally. |
| 7 | Content Agent analysis model | **Autonomous reasoning with tools** | Agent SDK strength: tools for thesis lookup, preference check, scoring during analysis. |
| 8 | Pipeline trigger | **Content Agent on 5-min schedule**, calls Web Agent for extraction | Content Agent orchestrates its own pipeline. |
| 9 | Web Agent spec | **Rewrite from scratch** in 3-agent context | Standalone spec is obsolete. |
| 10 | Venv strategy | **Single shared venv** | Shared CLI binary (237MB disk, once). Simpler deployment. |
| 11 | Build order | **All 3 in parallel** (unified spec first) | Unified spec ensures consistent contracts, then parallel implementation. |
| 12 | Content sources | **Extensible by design** | New sources = new @tool functions + updated system prompt. No structural changes. |
| 13 | CC↔CAI sync | **Hooks stay**, Sync Agent provides read tools. Defer full solve. | Not part of v1. |
| 14 | Droplet | **Already Tier 1** (2 vCPU, 4GB RAM, $24/mo) | User confirmed. |
| 15 | Table read/write | **Sync Agent ONLY** reads/writes Notion + Postgres | User mandate. No exceptions. |

---

## 2. Architecture Overview

### Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  CALLERS                                                      │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌────────┐         │
│  │Claude.ai│  │ Claude  │  │  Future  │  │  Cron  │         │
│  │  (CAI)  │  │  Code   │  │  Agents  │  │        │         │
│  └────┬────┘  └────┬────┘  └────┬─────┘  └───┬────┘         │
│       │            │            │             │               │
│  mcp.3niac.com    .mcp.json    MCP           MCP             │
└───────┼────────────┼────────────┼─────────────┼───────────────┘
        │            │            │             │
┌───────▼────────────┼────────────▼─────────────▼───────────────┐
│  SYNC AGENT (Gateway)  port 8000, mcp.3niac.com               │
│                                                                │
│  OWNS: All Notion + Postgres read/write                        │
│  EXPOSES: State tools (thesis, actions, preferences, context)  │
│           Write-receiver tools (digest, actions, thesis)       │
│           Sync ops (manual triggers)                           │
│           Proxy tools → Web Agent                              │
│  INTERNAL: Bidirectional sync on 10-min timer                  │
│           Change detection → action generation                 │
│           Write-ahead queue + retry                            │
│                                                                │
│  Agent SDK: ClaudeSDKClient for autonomous sync reasoning      │
│  (decides how to handle conflicts, generate actions from       │
│   changes, reason about sync failures)                         │
└────────────┬──────────────────────┬────────────────────────────┘
             │                      │
     MCP calls              MCP calls
             │                      │
┌────────────▼────────────┐  ┌──────▼──────────────────────────┐
│  CONTENT AGENT          │  │  WEB AGENT                      │
│  port 8002              │  │  port 8001, web.3niac.com       │
│                         │  │                                  │
│  OWNS: Content analysis,│  │  OWNS: All web interaction       │
│  thesis reasoning,      │  │  Browser (Playwright), scraping, │
│  action scoring,        │  │  search, YouTube extraction,     │
│  digest publishing      │  │  auth/sessions, strategy cache,  │
│                         │  │  URL monitoring, stealth          │
│  CALLS: Web Agent       │──┤                                  │
│    (extraction)         │  │  CALLS: Nothing (leaf agent)     │
│  CALLS: Sync Agent      │  │                                  │
│    (all DB writes)      │  │  Agent SDK: ClaudeSDKClient for  │
│                         │  │  autonomous web task reasoning    │
│  Agent SDK: ClaudeSDKClient│ │  (tool selection, retry logic,  │
│  for autonomous content │  │   approach planning, strategy)    │
│  analysis reasoning     │  │                                  │
└─────────────────────────┘  └──────────────────────────────────┘
          │                           │
          │ git push                  │ SQLite WAL
          ▼                           ▼
┌──────────────┐              ┌──────────────┐
│ digest.wiki  │              │ strategy.db  │
│ (Vercel SSG) │              │ (UCB bandit) │
└──────────────┘              └──────────────┘

STATE LAYER (Sync Agent ONLY access):
┌──────────────────────────────────────────────┐
│  Notion (8 DBs)  │  Postgres (7 tables)      │
│  Human interface  │  Machine brain            │
└──────────────────────────────────────────────┘
```

### Design Principles

1. **Agent = ClaudeSDKClient** — Every agent is a Claude Agent SDK agent. No raw API calls. No manual tool loops.
2. **Sync Agent owns all state** — No agent reads/writes Notion or Postgres except Sync Agent. Other agents request writes via MCP tool calls.
3. **MCP-native communication** — Agents talk to each other via MCP tool calls. The SDK supports external HTTP MCP servers natively (`"type": "http"` in `mcp_servers` config). Source: `09-mcp-integration.md`.
4. **Extensible by addition** — New content sources = new @tools + updated system prompt. New agents = new MCP servers registered with existing agents. No structural changes.
5. **Shared venv, shared CLI** — Single Python venv, single claude-agent-sdk CLI binary on disk. Each agent spawns its own CLI process but shares the 237MB binary. Source: `06-hosting-and-deployment.md`.
6. **Never fail silently** — Write-ahead queue for DB writes. Auth escalation ladder for web access. PostToolUse hooks for audit. Stop hooks for verification.

---

## 3. Web Agent

### Role

Universal web master — capable of everything a human can do on the web, and more. Handles browser automation, scraping, search, YouTube extraction, authentication, strategy learning, and proactive monitoring.

**Leaf agent** — does not call other agents. Only receives requests.

### SDK Configuration

```python
ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    fallback_model="claude-opus-4-6",
    permission_mode="dontAsk",
    system_prompt=web_system_prompt,        # Custom string, ~4KB
    mcp_servers={"web": web_tools_server},  # In-process @tools only
    allowed_tools=[
        "mcp__web__browse", "mcp__web__scrape", "mcp__web__search",
        "mcp__web__screenshot", "mcp__web__interact", "mcp__web__fingerprint",
        "mcp__web__check_strategy", "mcp__web__manage_session",
        "mcp__web__validate", "mcp__web__cookie_status", "mcp__web__watch_url",
    ],
    disallowed_tools=["Bash", "Write", "Edit", "Read"],
    thinking=ThinkingConfig(type="enabled", budget_tokens=8000),
    effort="high",
    max_turns=20,
    max_budget_usd=2.00,
    env={"ANTHROPIC_API_KEY": "...", "FIRECRAWL_API_KEY": "..."},
    cwd="/opt/agents",
    hooks={
        "PreToolUse": [HookMatcher(hooks=[rate_limit_check, input_validation])],
        "PostToolUse": [HookMatcher(hooks=[record_strategy_outcome, log_audit])],
        "Stop": [HookMatcher(hooks=[emit_metrics])],
        "UserPromptSubmit": [HookMatcher(hooks=[inject_strategy_hints])],
    },
)
```

### FastMCP Tools Exposed (port 8001)

These are the tools callers (Content Agent, CC, CAI via proxy) can invoke:

| Tool | Mode | Description |
|------|------|-------------|
| `web_task(task, url?, output_schema?, timeout_s?, effort?)` | Agent | Full SDK reasoning — multi-step web tasks |
| `web_scrape(url, use_firecrawl?)` | Direct | Extract content, no LLM cost |
| `web_browse(url, action?, readiness_mode?)` | Direct | Playwright browse, no LLM cost |
| `web_search(query, limit?)` | Direct | Firecrawl search, no LLM cost |
| `web_screenshot(url)` | Direct | Visual capture |
| `extract_youtube(playlist_url?, video_urls?, since_days?)` | Direct | YouTube extraction via yt-dlp + transcripts |
| `extract_transcript(video_id)` | Direct | Single video transcript fetch |
| `cookie_status()` | Direct | Cookie health check |
| `fingerprint(url)` | Direct | Site classification |
| `watch_url(url, interval_minutes, notify_method?)` | Direct | Register URL monitoring |
| `health_check()` | Direct | Web Agent health |

**Direct vs Agent mode:** Direct tools execute Python functions with zero LLM cost. Agent tools (`web_task`) invoke a ClaudeSDKClient session with reasoning.

### Internal @tool Functions (for Agent SDK reasoning)

These are registered via `create_sdk_mcp_server()` and used by the ClaudeSDKClient during `web_task`:

| Tool | Description |
|------|-------------|
| `browse` | Playwright: navigate, snapshot, readiness ladder |
| `scrape` | Jina Reader + Firecrawl async extraction |
| `search` | Firecrawl async search |
| `screenshot` | Visual page capture |
| `interact` | Click, fill, submit, select, navigate |
| `fingerprint` | Site framework/CMS/type classification |
| `check_strategy` | Query UCB bandit cache for best approach |
| `manage_session` | storageState persist/load, cookie injection |
| `validate` | Content quality scoring |

### Hooks

| Hook | Matcher | What It Does |
|------|---------|-------------|
| `PreToolUse` | all | Rate limiting per domain (max 10 req/min/domain). Input validation (URL format, size limits). |
| `PostToolUse` | `browse\|scrape\|search` | Auto-record strategy outcome to SQLite UCB cache: domain, method, success, latency. |
| `Stop` | all | Log final result metrics: total cost, turns used, tools called, success. |
| `UserPromptSubmit` | all | Inject context: cookie freshness status, UCB strategy hint for target domain, domain-specific knowledge. |

### Auth Escalation Ladder

```
Step 1: storageState (persistent session) → fastest, zero cost
Step 2: Cookie sync files (/opt/agents/cookies/{domain}.txt) → inject into Playwright
Step 3: Fresh cookie sync from Mac → trigger cookie-sync.sh
Step 4: Browserbase isolated session → separate identity, last resort before human
Step 5: Escalate to human → 2FA, CAPTCHA, new account setup
```

### Strategy Learning

- **Record:** PostToolUse hooks auto-log every web operation outcome (domain, method, success, latency) to SQLite WAL at `/opt/agents/data/strategy.db`
- **Query:** Agent calls `check_strategy(origin)` before choosing method. UCB bandit algorithm balances exploration vs exploitation.
- **Seed:** `fingerprint(url)` auto-seeds candidate strategies based on site type (SPA, static, auth-required, bot-hostile).

### System Prompt Outline (~4KB)

1. Identity: Universal web master agent
2. Tool selection framework: when to scrape vs browse vs search
3. Auth strategy: check storageState → cookies → Browserbase → escalate
4. Quality validation: always validate before returning, retry on poor score
5. Strategy learning: check cache → use best method → outcomes auto-recorded
6. Structured output: match caller's schema when `output_schema` provided
7. Anti-patterns: never return empty content, never skip validation, never guess
8. Escalation rules: when to use Opus fallback, when to escalate to human

### Files

```
agents/web/
├── server.py           # FastMCP server (port 8001), dual-mode routing
├── agent.py            # ClaudeSDKClient config, session pool
├── tools.py            # All @tool definitions + create_sdk_mcp_server
├── hooks.py            # PreToolUse, PostToolUse, Stop, UserPromptSubmit
├── system_prompt.md    # Web mastery instructions
├── lib/
│   ├── browser.py      # Async Playwright: lifecycle, readiness ladder, context pool
│   ├── scrape.py       # Async Jina Reader + Firecrawl extraction
│   ├── search.py       # Async Firecrawl search
│   ├── fingerprint.py  # Site framework/CMS classification
│   ├── quality.py      # Content quality scoring
│   ├── strategy.py     # SQLite WAL UCB bandit cache
│   ├── stealth.py      # Persona profiles (coherent UA/viewport/locale)
│   ├── sessions.py     # storageState persistence, cookie loading, auth ladder
│   ├── monitor.py      # URL watch, change detection, notifications
│   └── extraction.py   # YouTube extraction (yt-dlp + transcript fetch)
└── tests/
    ├── test_tools.py
    ├── test_hooks.py
    └── test_agent.py
```

---

## 4. Content Agent

### Role

Content pipeline orchestrator and analyst. Processes content from any source (YouTube in v1, extensible to RSS, URLs, meetings, etc.). Uses Agent SDK autonomous reasoning with tools to produce rich analysis: thesis connections, action proposals, conviction assessments.

**Calls Web Agent** for extraction. **Calls Sync Agent** for all DB writes.

### SDK Configuration

```python
ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    permission_mode="dontAsk",
    system_prompt=content_system_prompt,  # Content analysis instructions + CONTEXT.md sections
    mcp_servers={
        "tools": content_tools_server,    # In-process: scoring, publishing, formatting
        "sync": {                         # External: Sync Agent for reads + writes
            "type": "http",
            "url": "http://localhost:8000/mcp",
        },
    },
    allowed_tools=[
        # In-process tools
        "mcp__tools__score_action",
        "mcp__tools__publish_digest",
        "mcp__tools__load_context_sections",
        # Sync Agent tools (reads)
        "mcp__sync__cos_get_thesis_threads",
        "mcp__sync__cos_get_preferences",
        # Sync Agent tools (writes)
        "mcp__sync__write_digest",
        "mcp__sync__write_actions",
        "mcp__sync__update_thesis",
        "mcp__sync__create_thesis_thread",
        "mcp__sync__log_preference",
    ],
    disallowed_tools=["Bash", "Write", "Edit", "Read"],
    thinking=ThinkingConfig(type="enabled", budget_tokens=10000),
    output_format={"type": "json", "schema": DIGEST_DATA_SCHEMA},
    effort="high",
    max_turns=15,
    max_budget_usd=1.50,
    env={"ANTHROPIC_API_KEY": "..."},
    cwd="/opt/agents",
    hooks={
        "PostToolUse": [HookMatcher(hooks=[log_analysis_audit])],
        "Stop": [HookMatcher(hooks=[verify_pipeline_completion, emit_metrics])],
    },
)
```

### FastMCP Tools Exposed (port 8002)

| Tool | Description |
|------|-------------|
| `analyze_content(extraction_data, content_type?)` | Run analysis on extracted data (invokes Agent SDK reasoning) |
| `trigger_pipeline()` | Manual pipeline trigger |
| `pipeline_status()` | Check pipeline state (last run, queue depth, errors) |
| `health_check()` | Content Agent health |

### Internal @tool Functions (for Agent SDK reasoning)

| Tool | Type | Description |
|------|------|-------------|
| `score_action(bucket_impact, conviction_change, time_sensitivity, action_novelty, effort_vs_impact)` | In-process | 5-factor weighted scoring model |
| `publish_digest(digest_data)` | In-process | Git push to aicos-digests → Vercel deploy |
| `load_context_sections()` | In-process | Load CONTEXT.md sections (IDS methodology, key people, playbooks) |

Plus Sync Agent tools accessed via external MCP (see SDK config above).

### Pipeline Flow

```
Content Agent (5-min timer in Python orchestrator)
  │
  ├─1→ HTTP call to Web Agent: extract_youtube(playlist_url, since_days=3)
  │     └─→ Returns: {videos: [{video_id, title, channel, transcript, relevance}]}
  │
  ├─2→ Filter: skip non-relevant, skip no-transcript
  │
  └─3→ For each relevant video:
        │
        ├─→ Invoke ClaudeSDKClient agent session:
        │     Prompt: "Analyze this video transcript. Use your tools to look up
        │              existing thesis threads, check preference history, and score
        │              all proposed actions. Produce DigestData JSON. Then publish
        │              the digest and submit all data to Sync Agent."
        │
        │     Agent autonomously:
        │       ├─→ cos_get_thesis_threads() → reads active theses from Sync Agent
        │       ├─→ cos_get_preferences() → reads preference history from Sync Agent
        │       ├─→ Reasons about thesis connections, conviction assessments
        │       ├─→ score_action() → scores each proposed action (in-process)
        │       ├─→ publish_digest() → pushes to digest.wiki (in-process)
        │       ├─→ write_digest() → sends to Sync Agent for Notion entry
        │       ├─→ write_actions() → sends to Sync Agent for Actions Queue
        │       ├─→ update_thesis() → sends thesis evidence to Sync Agent
        │       ├─→ create_thesis_thread() → new threads via Sync Agent (if warranted)
        │       └─→ log_preference() → logs outcomes via Sync Agent
        │
        └─→ Stop hook verifies all steps completed
```

### Hooks

| Hook | What It Does |
|------|-------------|
| `PostToolUse` | Audit log: which tools called, success/failure, latency. |
| `Stop` | **verify_pipeline_completion:** Check that for each analyzed video, all expected submissions were made (digest published, Sync Agent notified, thesis updated). Flag missing steps. **emit_metrics:** Cost, turns, video count. |

### System Prompt Outline

1. Identity: AI CoS Content Analyst — processes content for Aakash Kumar (MD at Z47 + DeVC)
2. Domain context: IDS methodology, 4 priority buckets, thesis tracker, portfolio context (loaded from CONTEXT.md sections via `load_context_sections` tool)
3. Analysis framework: thesis connections with conviction assessments, portfolio relevance, contra signals, rabbit holes, proposed actions with scoring
4. Tool usage rules: MUST look up thesis threads before analyzing. MUST check preferences before proposing actions. MUST score every action. MUST publish and submit to Sync Agent.
5. Output schema: DigestData JSON with all fields (matches existing schema)
6. Quality bars: relevance score thresholds, net newness categories, action classification
7. Conviction guardrail: Provide evidence and reasoning. Never set conviction without strong evidence.
8. Extensibility note: New content sources will add new tools. Adapt analysis approach per content type.

### Files

```
agents/content/
├── server.py           # FastMCP server (port 8002), pipeline scheduling
├── agent.py            # ClaudeSDKClient config, analysis session management
├── tools.py            # @tool definitions + create_sdk_mcp_server
├── hooks.py            # PostToolUse, Stop callbacks
├── system_prompt.md    # Content analysis instructions
├── lib/
│   ├── scoring.py      # Action scoring model (5-factor weighted)
│   ├── publishing.py   # digest.wiki: JSON → git push → Vercel deploy
│   └── formatting.py   # Notion field formatting utilities
└── tests/
    ├── test_tools.py
    ├── test_hooks.py
    └── test_agent.py
```

---

## 5. Sync Agent (Gateway)

### Role

System state keeper and gateway. THE ONLY agent that reads/writes Notion and Postgres. Serves as the unified MCP endpoint for CAI and external agents. Runs bidirectional sync on internal timer. Proxies web tools to Web Agent so CAI has single-endpoint access.

Uses Agent SDK reasoning for autonomous decisions: conflict resolution during sync, action generation from change events, intelligent retry strategies.

### SDK Configuration

```python
ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    permission_mode="dontAsk",
    system_prompt=sync_system_prompt,
    mcp_servers={
        "tools": sync_tools_server,  # In-process: all DB operations
    },
    allowed_tools=[
        "mcp__tools__notion_read", "mcp__tools__notion_write",
        "mcp__tools__pg_query", "mcp__tools__pg_write",
        "mcp__tools__detect_changes", "mcp__tools__generate_actions",
    ],
    disallowed_tools=["Bash", "Write", "Edit", "Read"],
    thinking=ThinkingConfig(type="enabled", budget_tokens=5000),
    effort="medium",
    max_turns=10,
    max_budget_usd=0.50,
    env={"ANTHROPIC_API_KEY": "...", "NOTION_TOKEN": "...", "DATABASE_URL": "..."},
    cwd="/opt/agents",
    hooks={
        "PostToolUse": [HookMatcher(hooks=[sync_audit_log])],
        "Stop": [HookMatcher(hooks=[emit_sync_metrics])],
    },
)
```

**Note:** The Sync Agent uses Agent SDK reasoning primarily for its autonomous sync operations (change interpretation, conflict resolution, action generation). The gateway MCP tools (serving CAI and Content Agent) are handled by the FastMCP server directly — they don't invoke Agent SDK reasoning. Only the periodic sync cycle and complex operations trigger Agent SDK sessions.

### FastMCP Tools Exposed (port 8000, mcp.3niac.com)

#### State Read Tools (for CAI, CC, other agents)

| Tool | Description | Migrated From |
|------|-------------|---------------|
| `health_check()` | System + DB connectivity | current `health_check` |
| `cos_load_context()` | Domain context (CONTEXT.md) | current `cos_load_context` |
| `cos_get_thesis_threads(include_key_questions?)` | Active thesis threads | current `cos_get_thesis_threads` |
| `cos_get_recent_digests(limit?)` | Recent content digests | current `cos_get_recent_digests` |
| `cos_get_actions(status?, limit?)` | Actions queue | current `cos_get_actions` |
| `cos_get_preferences(limit?)` | Preference history | current `cos_get_preferences` |
| `cos_score_action(...)` | 5-factor action scoring | current `cos_score_action` |
| `cos_sync_status()` | Sync health dashboard | current `cos_sync_status` |
| `cos_get_changes(limit?)` | Change events | current `cos_get_changes` |

#### Write-Receiver Tools (for Content Agent and future agents)

| Tool | Description | New |
|------|-------------|-----|
| `write_digest(digest_data)` | Create digest entry in Notion Content Digest DB | Yes |
| `write_actions(actions)` | Create action entries in Notion Actions Queue + Postgres | Yes |
| `update_thesis(thesis_name, evidence, direction, ...)` | Update thesis with evidence (write-ahead) | Replaces direct `cos_update_thesis` |
| `create_thesis_thread(name, core_thesis, ...)` | Create new thesis thread (write-ahead) | Replaces direct `cos_create_thesis_thread` |
| `log_preference(action, outcome, score, ...)` | Log to action_outcomes table | Yes |

#### Sync Operation Tools (manual trigger)

| Tool | Description |
|------|-------------|
| `cos_sync_thesis_status()` | Pull thesis Status from Notion |
| `cos_sync_actions()` | Bidirectional actions sync |
| `cos_full_sync()` | Full sync cycle |
| `cos_retry_sync_queue()` | Drain retry queue |
| `cos_process_changes()` | Generate actions from changes |
| `cos_seed_thesis_db()` | One-time seed |

#### Proxy Tools (forward to Web Agent for CAI access)

| Tool | Proxies To |
|------|-----------|
| `web_task(task, url?, ...)` | Web Agent `web_task` |
| `web_scrape(url, ...)` | Web Agent `web_scrape` |
| `web_search(query, ...)` | Web Agent `web_search` |

Proxy implementation: Sync Agent makes HTTP MCP call to `localhost:8001/mcp`, forwards request, returns response. Thin pass-through.

### Internal Sync Cycle (10-min timer)

```
Every 10 minutes (asyncio timer inside long-running process):
  │
  ├─1→ Thesis status sync: Notion → Postgres (human-owned Status field)
  ├─2→ Actions bidirectional sync: pull Outcome from Notion, push local creates
  ├─3→ Change detection: diff Notion vs Postgres, log to change_events
  ├─4→ Sync queue drain: retry failed Notion pushes (exponential backoff)
  └─5→ Process changes: generate actions from change events
        │
        └─→ For complex changes (conviction → High, status transitions):
              invoke Agent SDK reasoning session to determine
              appropriate actions and priority
```

### Write-Ahead Pattern (unchanged from current)

```
Write request received (from Content Agent or any caller)
    │
    ├─→ Write to Postgres FIRST (always succeeds or raises)
    │
    └─→ Push to Notion
         ├── Success → mark synced
         └── Failure → enqueue to sync_queue
                        (exponential backoff: 2^attempts minutes)
                        (max 5 attempts before considered failed)
```

### Files

```
agents/sync/
├── server.py           # FastMCP server (port 8000, gateway), proxy routes
├── agent.py            # ClaudeSDKClient config (for autonomous sync reasoning)
├── tools.py            # @tool definitions (DB operations, change detection)
├── hooks.py            # PostToolUse (sync audit), Stop (metrics)
├── system_prompt.md    # Sync agent instructions
├── lib/
│   ├── notion_client.py    # Notion API wrapper (all CRUD operations)
│   ├── thesis_db.py        # Postgres thesis operations
│   ├── actions_db.py       # Postgres actions operations
│   ├── preferences.py      # Preference store (action_outcomes)
│   ├── change_detection.py # Change detection engine + action generation
│   └── proxy.py            # Web Agent proxy client (HTTP MCP calls)
└── tests/
    ├── test_tools.py
    ├── test_sync.py
    └── test_proxy.py
```

---

## 6. Inter-Agent Communication & Data Flow

### Communication Pattern

Agents communicate via MCP tool calls over HTTP. The SDK natively supports external HTTP MCP servers (`"type": "http"` in `mcp_servers` config). Source: `09-mcp-integration.md`.

```
Content Agent ──MCP──→ Sync Agent (reads: thesis, preferences. writes: digest, actions, thesis)
Content Agent ──MCP──→ Web Agent  (extraction: YouTube, transcripts)
Sync Agent    ──MCP──→ Web Agent  (proxy: web_task, web_scrape, web_search for CAI)
Web Agent     ──────→ (no outbound agent calls — leaf agent)
```

### Tool Naming Convention

All MCP tools follow: `mcp__<server_name>__<tool_name>` (Source: `09-mcp-integration.md`)

| Server Key | Agent | Example Tool |
|-----------|-------|-------------|
| `sync` | Sync Agent | `mcp__sync__cos_get_thesis_threads` |
| `web` | Web Agent | `mcp__web__extract_youtube` |
| `tools` | In-process | `mcp__tools__score_action` |

### Context Cost Management

"Each MCP server adds ALL its tool schemas to every request." (Source: `09-mcp-integration.md`)

Mitigation: Use `allowed_tools` to restrict visible tools:
- Content Agent sees ~12 tools (3 in-process + 9 from Sync Agent)
- Web Agent sees ~11 tools (all in-process, no external MCP)
- Sync Agent sees ~6 tools (all in-process, for sync reasoning only)

### Key Data Flows

#### Flow 1: Content Pipeline (every 5 min)

```
[Timer] → Content Agent server.py
    → HTTP call to Web Agent: extract_youtube()
    → Filter relevant videos with transcripts
    → For each video:
        → Agent SDK session with tools:
            → cos_get_thesis_threads (Sync Agent)
            → cos_get_preferences (Sync Agent)
            → score_action (in-process)
            → Analysis reasoning → DigestData JSON
            → publish_digest (in-process → digest.wiki)
            → write_digest (Sync Agent → Notion)
            → write_actions (Sync Agent → Notion + Postgres)
            → update_thesis (Sync Agent → Postgres + Notion)
            → log_preference (Sync Agent → Postgres)
```

#### Flow 2: Ad-hoc Web Task (from CAI)

```
[CAI] → mcp.3niac.com (Sync Agent)
    → web_task proxy → Web Agent port 8001
    → Web Agent ClaudeSDKClient reasons with tools
    → Returns structured result
    → Sync Agent passes through to CAI
```

#### Flow 3: Sync Cycle (every 10 min)

```
[Timer] → Sync Agent internal
    → Thesis status: Notion → Postgres (pull Status field)
    → Actions: bidirectional (push local, pull Outcome)
    → Change detection: diff → change_events table
    → Queue drain: retry failed Notion pushes
    → Process changes: → Agent SDK reasoning for complex changes
        → Generate proposed actions → write to Actions Queue
```

#### Flow 4: Future Events Agent (illustrative)

```
[Event: meeting completed] → Events Agent
    → Get Granola transcript (Granola MCP)
    → Call Content Agent: analyze_content(transcript, type="meeting")
    → Content Agent reasons: thesis connections, actions
    → Content Agent → Sync Agent: write actions, update thesis
    → Events Agent → Web Agent: enrich contact info
    → Events Agent → Sync Agent: update Network DB
```

---

## 7. Infrastructure & File Structure

### Monorepo Layout

```
/opt/agents/                        # Droplet deployment root
├── pyproject.toml                  # Shared deps: claude-agent-sdk, fastmcp, playwright,
│                                   #   httpx, aiohttp, psycopg2, yt-dlp, etc.
├── .venv/                          # Single shared venv (CLI binary here: 237MB once)
├── .env                            # Shared credentials (ANTHROPIC_API_KEY, NOTION_TOKEN,
│                                   #   DATABASE_URL, FIRECRAWL_API_KEY, etc.)
├── shared/
│   ├── __init__.py
│   ├── types.py                    # Shared response schemas (DigestData, Action, etc.)
│   └── mcp_client.py              # HTTP MCP client helper for inter-agent calls
│
├── web/                            # Web Agent (see §3)
│   ├── server.py, agent.py, tools.py, hooks.py
│   ├── system_prompt.md
│   ├── lib/ (browser, scrape, search, etc.)
│   └── tests/
│
├── content/                        # Content Agent (see §4)
│   ├── server.py, agent.py, tools.py, hooks.py
│   ├── system_prompt.md
│   ├── lib/ (scoring, publishing, formatting)
│   └── tests/
│
├── sync/                           # Sync Agent / Gateway (see §5)
│   ├── server.py, agent.py, tools.py, hooks.py
│   ├── system_prompt.md
│   ├── lib/ (notion_client, thesis_db, actions_db, etc.)
│   └── tests/
│
├── data/                           # Shared persistent data
│   ├── strategy.db                 # SQLite WAL (Web Agent strategy cache)
│   ├── sessions/                   # storageState JSONs (Web Agent)
│   └── queue/                      # Extraction queue (Content Agent)
│       ├── processed/
│       └── processed_videos.json
│
├── cookies/                        # Auth cookies (Netscape format, synced from Mac)
│   ├── youtube.txt
│   ├── x.txt
│   └── ...
│
├── logs/
│   ├── web.log
│   ├── content.log
│   └── sync.log
│
├── deploy.sh                       # Unified: rsync → uv sync → restart services → verify
└── CONTEXT.md                      # Domain context (synced from Mac)
```

**Mac-side mirror:** `mcp-servers/agents/` in the AI CoS repo. deploy.sh rsyncs to `/opt/agents/`.

### Systemd Services (3)

| Service | Unit File | Port | Restart | Memory Limit |
|---------|----------|------|---------|-------------|
| `web-agent` | `/etc/systemd/system/web-agent.service` | 8001 | always | 1GB |
| `content-agent` | `/etc/systemd/system/content-agent.service` | 8002 | always | 768MB |
| `sync-agent` | `/etc/systemd/system/sync-agent.service` | 8000 | always | 768MB |

All services use `EnvironmentFile=-/opt/agents/.env` and `ExecStopPost=/usr/bin/pkill -f chrome` (Web Agent only).

### Cloudflare Tunnels

| Tunnel | Routes To | DNS |
|--------|----------|-----|
| `aicos-mcp` | localhost:8000 | mcp.3niac.com (Sync Agent gateway) |
| `aicos-web` | localhost:8001 | web.3niac.com (Web Agent direct) |

### Monitoring

- **Health check cron** (60s): curl each agent's `/health_check`, restart on failure
- **Log rotation**: logrotate for `/opt/agents/logs/*.log`
- **Systemd watchdog**: `WatchdogSec=120` for process liveness

### Deployment (deploy.sh)

```bash
# From Mac: mcp-servers/agents/
./deploy.sh

# Steps:
# 1. rsync code (exclude .env, .venv, __pycache__, data/, logs/)
# 2. uv sync (shared venv)
# 3. Sync CONTEXT.md
# 4. Restart all 3 services (graceful: sync-agent first, then content, then web)
# 5. Health check all 3 endpoints
# 6. Install/update cron jobs
```

### Rollback

- `web-tools-mcp` stays available at `/opt/web-tools-mcp/` for Web Agent rollback
- Current `ai-cos-mcp` stays at `/opt/ai-cos-mcp/` for Sync Agent rollback
- Rollback: stop new services, start old services, update tunnel routes

---

## 8. Build Phases

### Phase 0: Foundation (shared)

| Task | Files | Description |
|------|-------|-------------|
| 0.1 | `pyproject.toml` | All shared deps |
| 0.2 | `shared/types.py` | Shared schemas: DigestData, Action, ThesisUpdate, etc. |
| 0.3 | `shared/mcp_client.py` | HTTP MCP client helper for inter-agent calls |
| 0.4 | `.env.example` | Template for credentials |
| 0.5 | `deploy.sh` | Unified deploy script |

### Phase 1: Sync Agent (gateway — unblocks other agents)

| Task | Files | Description |
|------|-------|-------------|
| 1.1 | `sync/lib/` | Migrate: notion_client, thesis_db, actions_db, preferences, change_detection |
| 1.2 | `sync/tools.py` | All @tool definitions (state reads, write-receivers, sync ops, proxies) |
| 1.3 | `sync/server.py` | FastMCP server on port 8000, proxy routing |
| 1.4 | `sync/agent.py` | ClaudeSDKClient config for autonomous sync reasoning |
| 1.5 | `sync/hooks.py` | Audit logging, metrics |
| 1.6 | `sync/system_prompt.md` | Sync agent instructions |
| 1.7 | `sync/tests/` | All tests |
| 1.8 | systemd unit | `sync-agent.service` |

### Phase 2: Web Agent (independent)

| Task | Files | Description |
|------|-------|-------------|
| 2.1 | `web/lib/` | Browser, scrape, search, fingerprint, quality, strategy, stealth, sessions, monitor, extraction |
| 2.2 | `web/tools.py` | All @tool definitions + create_sdk_mcp_server |
| 2.3 | `web/hooks.py` | Rate limiting, strategy recording, metrics |
| 2.4 | `web/agent.py` | ClaudeSDKClient config, session pool |
| 2.5 | `web/server.py` | FastMCP server on port 8001, dual-mode routing |
| 2.6 | `web/system_prompt.md` | Web mastery instructions |
| 2.7 | `web/tests/` | All tests |
| 2.8 | systemd unit | `web-agent.service` |

### Phase 3: Content Agent (depends on Phase 1 + 2)

| Task | Files | Description |
|------|-------|-------------|
| 3.1 | `content/lib/` | Scoring, publishing, formatting |
| 3.2 | `content/tools.py` | @tool definitions + Sync/Web Agent MCP config |
| 3.3 | `content/hooks.py` | Pipeline completion verification, metrics |
| 3.4 | `content/agent.py` | ClaudeSDKClient config for autonomous analysis |
| 3.5 | `content/server.py` | FastMCP server on port 8002, pipeline scheduler |
| 3.6 | `content/system_prompt.md` | Content analysis instructions |
| 3.7 | `content/tests/` | All tests |
| 3.8 | systemd unit | `content-agent.service` |

### Phase 4: Integration

| Task | Description |
|------|-------------|
| 4.1 | End-to-end: Content Agent → Web Agent → Sync Agent pipeline test |
| 4.2 | CAI → Sync Agent → Web Agent proxy test |
| 4.3 | Sync cycle under load (Content Agent writing while sync runs) |
| 4.4 | Deploy to droplet, cutover from old services |
| 4.5 | Monitoring: health cron, log rotation, alerting |
| 4.6 | Rollback verification |

### Dependency Graph

```
Phase 0 (Foundation) ──→ Phase 1 (Sync Agent)  ──→ Phase 3 (Content Agent)
                     └──→ Phase 2 (Web Agent)  ──┘       │
                                                          ▼
                                                   Phase 4 (Integration)
```

Phase 1 and 2 are **parallelizable** after Phase 0. Phase 3 depends on both (needs Sync Agent for writes, Web Agent for extraction). Phase 4 depends on all three.

---

## 9. Success Criteria

### Per-Agent

| # | Agent | Criterion | Pass Threshold |
|---|-------|-----------|----------------|
| 1 | Web | `health_check` returns 200 | <2s |
| 2 | Web | `web_scrape` returns content for 5/6 public test URLs | content_length > 1000 |
| 3 | Web | `extract_youtube` returns transcript for a known video | transcript.success == true |
| 4 | Web | `web_task` completes multi-step task | status=complete, <60s, <$1 |
| 5 | Web | Strategy learning records outcomes | 10 outcomes in strategy.db |
| 6 | Content | `analyze_content` produces valid DigestData JSON | Schema validation passes |
| 7 | Content | Pipeline processes extraction end-to-end | Digest published + Sync Agent called |
| 8 | Content | Agent uses thesis tools during analysis | cos_get_thesis_threads called |
| 9 | Content | Agent uses preference tools during analysis | cos_get_preferences called |
| 10 | Sync | `health_check` returns 200 with DB status | <2s |
| 11 | Sync | `write_digest` creates Notion entry | Notion page ID returned |
| 12 | Sync | `write_actions` creates Actions Queue entries | Entries visible in Notion |
| 13 | Sync | Sync cycle completes without errors | Full sync in <30s |
| 14 | Sync | Write-ahead: Notion failure → queued for retry | sync_queue populated |
| 15 | Sync | Web proxy: `web_scrape` via Sync Agent works | Content returned from Web Agent |

### System-Level

| # | Criterion | Pass Threshold |
|---|-----------|----------------|
| 16 | Full pipeline: YouTube → digest.wiki + Notion | End-to-end in <5 min |
| 17 | CAI can call web_task via mcp.3niac.com | Result returned |
| 18 | All 3 services survive simultaneous restart | Back up in <30s |
| 19 | Memory: all 3 agents + Postgres + Chrome | <3.5GB total |
| 20 | Rollback to old services | Working in <60s |

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Agent SDK CLI process overhead** | Each agent session spawns a CLI subprocess (~100-200MB RSS) | Shared venv/binary (237MB on disk once). Session pool with reuse. Direct-mode tools bypass SDK entirely. |
| **Inter-agent MCP latency** | Content Agent → Sync Agent adds HTTP roundtrip | localhost:8000 — sub-millisecond. Batch writes where possible. |
| **Token cost of autonomous analysis** | Content Agent reasoning with tools costs more than single-shot API | max_budget_usd=$1.50/analysis. Effort="high" only for analysis. Compare cost vs. quality in first 50 runs. |
| **Sync Agent as single point of failure** | Gateway down → CAI loses access, Content Agent can't write | Systemd auto-restart. Write-ahead queue absorbs failures. Health cron detects in 60s. |
| **Context window bloat** | 12 tool schemas per Content Agent session | allowed_tools whitelist (verified pattern from SDK docs). Only needed tools visible. |
| **Chrome OOM on 4GB droplet** | Playwright + 3 agents + Postgres | Semaphore(2) on browser contexts. MemoryMax=1GB on Web Agent. ExecStopPost pkill chrome. |
| **Cookie/session expiry** | Web Agent auth failures | 5-step escalation ladder. storageState persistence. Cookie freshness monitoring. |
| **Strategy cache corruption** | Wrong method selection | SQLite WAL mode. Graceful fallback to default strategy on read error. |
| **Notion API rate limits** | Write failures during heavy pipeline runs | Exponential backoff in sync_queue. Max 5 retries. SyncAgent batches writes. |
| **SDK version changes** | Breaking API | Pin `claude-agent-sdk==0.1.48` in pyproject.toml. Test before upgrading. |

---

## 11. Production Hardening (Audit-Driven)

Requirements added after 4-vantage audit (QA Lead, DevOps Lead, System Architect, Backend Engineer — 57 findings consolidated to 15 themes, user-approved 2026-03-15).

### Conflict Resolution (C1 — all 4 reviewers)

- **Human-owned fields always win:** Status (thesis), Outcome (actions) — Notion is source of truth for these fields.
- **AI-vs-AI writes:** `last_modified_at` timestamp — newer wins.
- **All conflicts logged** to `change_events` table with `conflict=true` flag for audit.
- No CRDTs or version vectors — unnecessary at current scale.

### Idempotency & Write Safety (C2 — 3 reviewers)

- **All write-receiver tools** (`write_digest`, `write_actions`, `update_thesis`, `create_thesis_thread`, `log_preference`) require `request_id` parameter.
- `request_id` = SHA256(content_hash + timestamp). Sync Agent checks for existing `request_id` before writing.
- **Notion API:** Use `Idempotency-Key` header on all Notion push requests.
- **Dead letter table:** `sync_queue_dead_letter` — items failing after 5 retry attempts move here. Never silently dropped.

### Timeouts & Circuit Breaker (C3 — 4 reviewers)

- **Per-tool timeouts:** `extract_youtube`=90s, `write_digest`=30s, `web_scrape`=60s, `cos_get_thesis_threads`=10s.
- **SDK session timeout:** Wrap all `ClaudeSDKClient` sessions in `asyncio.wait_for(timeout=120s)`.
- **Retry strategy:** Exponential backoff (1s, 2s, 4s, max 3 retries) for transient failures.
- **Circuit breaker** in `shared/mcp_client.py`: Open after 5 consecutive failures per target agent. Reset after 60s. When open, fail fast with descriptive error.
- **Systemd WatchdogSec=120** on all services — catches hung processes.

### Observability & Tracing (C4 — 4 reviewers)

- **Structured JSON logging** via `python-json-logger` in all agents.
- **Log schema:** `{timestamp, agent, event_type, tool_name, duration_ms, cost_usd, status, error_msg, trace_id}`
- **Trace ID:** Content Agent generates UUID at pipeline start. Passed as `trace_id` parameter through all downstream MCP calls (Web Agent extraction, Sync Agent writes).
- **Cost tracking:** PostToolUse hooks log `cost_usd_this_tool` + cumulative budget. Alert if single analysis > $0.50.

### Session Pool (H1 — 2 reviewers)

- **Pool size:** `asyncio.Semaphore(2)` per agent (Web Agent: 2 concurrent sessions, Content Agent: 2, Sync Agent: 2).
- **TTL:** 5-minute session lifetime. Expired sessions cleaned up gracefully.
- **Crash cleanup:** `__aexit__` kills orphaned CLI processes on shutdown.

### Sync Agent SPOF Mitigation (H2 — 2 reviewers)

- Content Agent detects Sync Agent unavailability within **10 seconds** (fast health check endpoint).
- On failure: Content Agent **queues writes locally** (in-memory list + periodic file flush to `data/pending_writes/`).
- On Sync Agent recovery: Content Agent drains local queue to Sync Agent.
- Systemd auto-restart typically recovers in <30s.

### Tool Input Validation (H3 — 1 reviewer)

- **JSON Schema validation** on all write-receiver tools in Sync Agent.
- Invalid payloads rejected with `{"error": "validation_failed", "details": [{"field": "...", "issue": "..."}]}`.
- Conviction field validated: only accepts `New|Evolving|Evolving Fast|Low|Medium|High`.

### Notion Rate Limiter (H4 — 2 reviewers)

- **Token bucket rate limiter** in Sync Agent: 2.5 requests/second (conservative, Notion allows ~3/s).
- Excess writes queue internally. Alert if internal queue > 50 items for > 2 minutes.
- HTTP 429 from Notion → pause all writes for 60s, then retry with halved rate.

### Postgres Backup (H5 — 2 reviewers)

- **Daily `pg_dump`** at 02:00 UTC to `/opt/backups/postgres/` (7-day rolling retention).
- Restore test quarterly (documented in droplet runbook).
- RPO=24h, RTO=2h.

### Failure Acceptance Tests (H7 — 2 reviewers)

- Every success criterion (§9) gets a paired failure test.
- Test matrix: 3 agents × 5 failure modes (agent down, MCP timeout, Notion 429, Postgres full, Chrome crash).
- Automated in `tests/acceptance.sh` (Phase 4 deliverable).

### Resource Limits (H8 — 1 reviewer)

- **cgroup limits:** Web Agent=1GB, Content Agent=768MB, Sync Agent=512MB.
- **Load test before deploy:** Concurrent Content Agent pipeline + CAI web_task. Verify peak < 3.5GB.
- **OOM monitoring:** Alert on kernel OOM messages.

### SQLite Strategy Cache (M2 — 2 reviewers)

- Add `threading.Lock()` wrapper around SQLite writes in `web/lib/strategy.py`.
- Daily integrity check. On corruption, delete and re-learn (documented recovery time: 48h).

### SDK Upgrade Protocol (M5 — 2 reviewers)

- All major deps pinned in `pyproject.toml` (`claude-agent-sdk==0.1.48`, etc.).
- Upgrade procedure: (1) test in isolated env, (2) run all success criteria, (3) staged rollout — one agent first, monitor 24h, (4) full rollout.
- Document in CLAUDE.md's Agent SDK Build Rules section.

### Rejected Audit Items

| Item | Reason for Rejection |
|------|---------------------|
| Feature flags for staged rollout | Clean cutover preferred. Old services available for rollback. |
| Formal cutover runbook | Existing rollback plan (old services stay available) is sufficient. |
| Direct CAI → Web Agent access | Keep single gateway (Sync Agent). Simpler CAI configuration. |

---

## Appendix A: Past vs New Inventory

| # | Task | Current Owner | Code Location | New Owner | New Mechanism |
|---|------|--------------|---------------|-----------|---------------|
| 1 | YouTube poll | Content Pipeline cron | `lib/extraction.py` | Content Agent (timer) → Web Agent (tool) | `extract_youtube` MCP tool |
| 2 | Transcript fetch | Content Pipeline | `lib/extraction.py` | Web Agent | `extract_transcript` MCP tool |
| 3 | Cookie health | Content Pipeline | `lib/extraction.py` | Web Agent | `cookie_status` MCP tool |
| 4 | Relevance filter | Content Pipeline | `lib/extraction.py` | Content Agent | Agent SDK reasoning (replaces keyword heuristic) |
| 5 | Content analysis | ContentAgent | `runners/content_agent.py` | Content Agent | Agent SDK autonomous reasoning with tools |
| 6 | Thesis lookup | Pre-hydrated prompt | `_format_thesis_threads_from_notion()` | Content Agent → Sync Agent | `cos_get_thesis_threads` MCP tool |
| 7 | Preference loading | Pre-hydrated prompt | `get_preference_summary()` | Content Agent → Sync Agent | `cos_get_preferences` MCP tool |
| 8 | Action scoring | Post-analysis | `lib/scoring.py` | Content Agent | `score_action` @tool (during analysis) |
| 9 | Notion digest write | ContentAgent direct | `lib/notion_client.py` | Content Agent → Sync Agent | `write_digest` MCP tool |
| 10 | Notion action write | ContentAgent direct | `lib/notion_client.py` | Content Agent → Sync Agent | `write_actions` MCP tool |
| 11 | Notion thesis update | ContentAgent direct | `lib/notion_client.py` | Content Agent → Sync Agent | `update_thesis` MCP tool |
| 12 | Preference logging | ContentAgent direct | `lib/preferences.py` | Content Agent → Sync Agent | `log_preference` MCP tool |
| 13 | digest.wiki publish | ContentAgent | `lib/publishing.py` | Content Agent direct | `publish_digest` @tool |
| 14 | Thesis status sync | SyncAgent cron | `runners/sync_agent.py` | Sync Agent (internal timer) | Same logic, long-running process |
| 15 | Actions sync | SyncAgent cron | `runners/sync_agent.py` | Sync Agent (internal timer) | Same logic |
| 16 | Change detection | SyncAgent | `lib/change_detection.py` | Sync Agent | Same logic + Agent SDK reasoning for complex changes |
| 17 | Sync queue drain | SyncAgent | `lib/thesis_db.py` | Sync Agent | Same logic |
| 18 | Action generation | SyncAgent | `lib/change_detection.py` | Sync Agent | Agent SDK reasoning for intelligent action generation |
| 19 | MCP tools (17) | ai-cos-mcp server | `server.py` | Sync Agent | Absorbs all 17 tools + adds write-receiver + proxy tools |
| 20 | Web scraping | web-agent v1 | `mcp-servers/web-agent/` | Web Agent | Full rebuild on Agent SDK |
| 21 | Browser automation | web-agent v1 | `mcp-servers/web-agent/` | Web Agent | Same Playwright patterns, Agent SDK wrapper |
| 22 | Web search | web-agent v1 | `mcp-servers/web-agent/` | Web Agent | Same Firecrawl patterns |
| 23 | Strategy learning | web-agent v1 | `mcp-servers/web-agent/` | Web Agent | Same UCB bandit, Agent SDK hooks |
| 24 | URL monitoring | Not built | — | Web Agent | watch_url tool + background asyncio |
| 25 | CC↔CAI sync | Hooks | `.claude/sync/` | Hooks (unchanged) | Deferred |

## Appendix B: Verified Technical Facts

| Claim | Verified | Source |
|-------|----------|--------|
| Agent SDK supports external HTTP MCP servers | Yes | `09-mcp-integration.md`: `"type": "http"` config |
| All agents can share single CLI binary via shared venv | Yes | `06-hosting-and-deployment.md`: bundled in pip package |
| dontAsk + allowed_tools works as root | Yes | Tested on droplet (previous session) |
| Multiple Claude processes in one container is supported | Yes | `06-hosting-and-deployment.md`: Pattern 4 |
| Hooks run in application process, not agent context | Yes | `05-hooks.md`: "no context cost" |
| Tool naming: `mcp__<server>__<tool>` | Yes | `09-mcp-integration.md` |
| Each MCP server adds ALL tool schemas to context | Yes | `09-mcp-integration.md`: context cost warning |
| `allowed_tools` restricts visible tools | Yes | `09-mcp-integration.md` + `04-permissions.md` |
| Droplet is Tier 1 (2 vCPU, 4GB RAM) | Yes | User confirmed |
| claude-agent-sdk 0.1.48 installed on droplet | Yes | Previous session verification |
| Current memory: sufficient for 3 agents | Yes | 3.2GB free on 4GB droplet |
| query() supports mcp_servers for custom tools | Yes | `03-custom-tools.md` |
| PostToolUse hooks return {} (no decisions) | Yes | `05-hooks.md` |
| PreToolUse can deny or modify tool input | Yes | `05-hooks.md` |
