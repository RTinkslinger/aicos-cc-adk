# WebAgent v2 — Agent SDK Design Spec

**Date:** 2026-03-15
**Status:** Draft — awaiting user review
**Replaces:** web-tools-mcp (manual anthropic SDK tool-use loop)

---

## 1. Objective

A single autonomous agent that is the **universal web master** — capable of everything a human can do on the web, and more. Exposed as a universal MCP endpoint at `web.3niac.com/mcp` (port 8001). Internally powered by Claude Agent SDK with custom in-process tools, hooks for learning/guardrails, adaptive model selection, persistent browser sessions, and proactive monitoring.

**Design principle:** Never fail at a task unless every possible path has been exhausted.

---

## 2. Callers

Universal MCP endpoint — any system with MCP access can call it:

| Caller | How | Example |
|--------|-----|---------|
| Claude Code | MCP via `.mcp.json` | "scrape this URL and summarize" |
| Claude.ai | MCP via settings | "fetch my X bookmarks with high engagement" |
| ContentAgent | MCP tool call | "extract transcript from this YouTube URL" |
| SyncAgent | MCP tool call | "check if this Notion page's source URL has changed" |
| Cron jobs | HTTP POST to MCP endpoint | Proactive URL monitoring |
| External webhooks | HTTP POST to MCP endpoint | Triggered scrapes |

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────┐
│  CALLERS (CC, CAI, agents, cron, webhooks)              │
│  via MCP: web.3niac.com/mcp (port 8001)                │
└──────────────────────┬──────────────────────────────────┘
                       │ MCP (streamable-http)
┌──────────────────────▼──────────────────────────────────┐
│  LAYER 1: FastMCP Server (server.py)                    │
│                                                         │
│  Dual-mode routing:                                     │
│  ┌──────────────────┐  ┌─────────────────────────────┐  │
│  │ Direct tools     │  │ Agent tools                 │  │
│  │ (bypass=True)    │  │ (SDK agent reasoning)       │  │
│  │ No LLM cost      │  │                             │  │
│  │                  │  │ web_task → SDK session pool  │  │
│  │ web_scrape       │  │   adaptive thinking         │  │
│  │ web_browse       │  │   structured output         │  │
│  │ web_search       │  │   hooks + permissions       │  │
│  │ cookie_status    │  │   strategy learning         │  │
│  │ health_check     │  │                             │  │
│  └──────┬───────────┘  └──────────┬──────────────────┘  │
│         │                         │                      │
│  ┌──────▼─────────────────────────▼──────────────────┐  │
│  │  LAYER 2: Custom @tool functions (tools.py)       │  │
│  │  Registered via create_sdk_mcp_server()           │  │
│  │  In-process — zero IPC overhead                   │  │
│  │                                                   │  │
│  │  browse         - Playwright, readiness ladder    │  │
│  │  scrape         - Jina/Firecrawl async            │  │
│  │  search         - Firecrawl async                 │  │
│  │  fingerprint    - Site framework/CMS detection    │  │
│  │  screenshot     - Visual page capture             │  │
│  │  interact       - Click/fill/submit/navigate      │  │
│  │  manage_session - storageState persist/load        │  │
│  │  check_strategy - Query UCB bandit cache          │  │
│  │  validate       - Content quality scoring         │  │
│  │  cookie_status  - Cookie freshness check          │  │
│  │  watch_url      - Register URL monitoring         │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────▼────────────────────────────┐  │
│  │  LAYER 3: Core Libraries (lib/)                   │  │
│  │                                                   │  │
│  │  browser.py    - Playwright lifecycle, readiness   │  │
│  │  scrape.py     - Extraction engines (async)       │  │
│  │  search.py     - Search engines (async)           │  │
│  │  fingerprint.py - Site classification (async)     │  │
│  │  quality.py    - Content validation               │  │
│  │  strategy.py   - SQLite WAL UCB bandit            │  │
│  │  stealth.py    - Persona profiles                 │  │
│  │  sessions.py   - storageState + cookie manager    │  │
│  │  monitor.py    - URL watch, change detection      │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Layer 1 (server.py):** FastMCP server on port 8001. Routes incoming MCP calls. Direct tools bypass the SDK agent entirely (zero LLM cost). Agent tools (`web_task`) go through the SDK session pool with full reasoning.

**Layer 2 (tools.py):** All custom tool functions defined with `@tool` decorator and bundled via `create_sdk_mcp_server()`. These run in-process. When the SDK agent reasons about a task, it calls these tools. Direct-mode callers also call the same functions (skipping the agent).

**Layer 3 (lib/):** Pure Python libraries with no SDK dependency. Async throughout. Reusable by any caller. This is where Playwright, httpx, SQLite, and all I/O lives.

---

## 4. Agent SDK Components — Exhaustive Checklist

Every component of the Agent SDK and whether/how it's used:

### Core API

| Component | Status | Usage |
|-----------|--------|-------|
| `query()` | **Used** | For stateless direct tool calls in bypass mode |
| `ClaudeSDKClient` | **Used** | Pool of persistent sessions for agent-mode tasks (web_task) |
| `ClaudeAgentOptions` | **Used** | Central configuration object for all SDK interactions |

### Tools

| Component | Status | Usage |
|-----------|--------|-------|
| `@tool` decorator | **Used** | All 11 custom tool functions registered with name, description, schema |
| `create_sdk_mcp_server()` | **Used** | Bundle all @tool functions into single in-process MCP server |
| `mcp_servers` config | **Used** | Register the SDK MCP server in ClaudeAgentOptions |
| `allowed_tools` | **Used** | Whitelist: `mcp__web__browse`, `mcp__web__scrape`, etc. |
| `disallowed_tools` | **Used** | Block: `Bash`, `Write`, `Edit`, `Read` (agent uses only our tools) |
| `tools` preset | **Not used** | We don't use Claude Code's built-in tools |
| Tool `readOnlyHint` | **Used** | Mark read-only tools (scrape, search, fingerprint) for parallel execution |

### Permissions

| Component | Status | Usage |
|-----------|--------|-------|
| `permission_mode="dontAsk"` | **Used** | Autonomous operation — no human prompts, deny unlisted tools |
| `can_use_tool` callback | **Used** | Dynamic validation layer — rate limiting, argument validation |

### Hooks

| Component | Status | Usage |
|-----------|--------|-------|
| `PreToolUse` hook | **Used** | Input validation, guardrails, rate limiting per domain |
| `PostToolUse` hook | **Used** | Auto-record strategy outcomes to SQLite UCB cache |
| `Stop` hook | **Used** | Log final result, emit cost/usage metrics |
| `UserPromptSubmit` hook | **Used** | Inject context: cookie freshness, strategy hints, domain knowledge |
| `SubagentStart/Stop` | **Not used (v1)** | For future multi-agent orchestration |
| `PreCompact` | **Not used (v1)** | Sessions are short-lived enough |
| `Notification` | **Not used (v1)** | No notification consumers yet |
| `PermissionRequest` | **Not used** | dontAsk mode means no permission requests |

### Model & Reasoning

| Component | Status | Usage |
|-----------|--------|-------|
| `model` | **Used** | `claude-sonnet-4-6` as primary |
| `fallback_model` | **Used** | `claude-opus-4-6` for complex tasks that fail on Sonnet |
| `thinking` | **Required** | Adaptive thinking for multi-step planning — approach selection, retry reasoning, tool sequencing, strategy optimization |
| `effort` | **Used** | `"medium"` for simple tasks, `"high"` for complex multi-step |
| `max_turns` | **Used** | 20 default, configurable per request |
| `max_budget_usd` | **Used** | $2.00 default ceiling per web_task |

### Output

| Component | Status | Usage |
|-----------|--------|-------|
| `output_format` (structured output) | **Required** | Typed JSON responses for downstream consumers. Callers pass `output_schema` to web_task. ContentAgent, SyncAgent, and any MCP caller get machine-readable results |
| `include_partial_messages` (streaming) | **Used** | Real-time progress for long-running tasks |

### Sessions

| Component | Status | Usage |
|-----------|--------|-------|
| `resume` | **Used** | Pool sessions resume across requests |
| `fork_session` | **Available** | For branching exploratory tasks |
| `continue_conversation` | **Used** | Multi-turn within a session |
| Session persistence | **Used** | SDK persists sessions to disk by default |

### System Prompt

| Component | Status | Usage |
|-----------|--------|-------|
| `system_prompt` (custom string) | **Used** | Custom web mastery prompt — NOT Claude Code preset |
| `setting_sources` | **Not used** | No CLAUDE.md loading — agent gets custom prompt only |

### Infrastructure

| Component | Status | Usage |
|-----------|--------|-------|
| `env` | **Used** | Pass ANTHROPIC_API_KEY, FIRECRAWL_API_KEY |
| `cwd` | **Used** | `/opt/web-agent` |
| `cli_path` | **Not used** | Uses bundled CLI |
| `sandbox` | **Not used** | Dedicated droplet, not shared environment |
| `plugins` | **Not used** | All capabilities via custom tools |
| `AgentDefinition` (subagents) | **Not used (v1)** | Future: ContentAgent/SyncAgent as subagents |
| `file_checkpointing` | **Not used** | Agent doesn't modify files |
| `betas` | **Available** | Enable 1M context if needed for large page extractions |

---

## 5. Interaction Levels

The agent handles the full spectrum of web interaction:

| Level | Capability | Tools Used |
|-------|-----------|-----------|
| **Read** | Extract text, scrape content, get markdown | `scrape`, `browse(snapshot)` |
| **Navigate** | Follow links, paginate, scroll infinite feeds | `browse`, `interact(click)` |
| **Interact** | Fill forms, submit data, select dropdowns | `interact(fill, submit, select)` |
| **Authenticate** | Cookie injection, session persistence, storageState | `manage_session` |
| **Automate** | Multi-step flows (book, purchase, post, configure) | Agent reasoning chains multiple tools |
| **Monitor** | Watch URLs for changes, scheduled scrapes | `watch_url`, background tasks |
| **Analyze** | Fingerprint sites, classify content, score quality | `fingerprint`, `validate` |
| **Learn** | Remember what works per site, adapt strategy | `check_strategy`, PostToolUse hooks |
| **Stealth** | Coherent personas, anti-detection, human-like behavior | `lib/stealth.py` persona profiles |

---

## 6. Auth Escalation Ladder

**Principle:** Never fail. Try every path before giving up.

```
Step 1: storageState (persistent session)
  → Fastest, zero cost. Check if valid session exists for domain.
  → If valid → use it
  → If expired/missing → Step 2

Step 2: Cookie sync files (Netscape format from Mac)
  → Load from /opt/ai-cos/cookies/{domain}.txt
  → Inject into Playwright context
  → If login succeeds → save storageState for future use → done
  → If cookies stale/fail → Step 3

Step 3: Fresh cookie sync + rebuild
  → Trigger cookie-sync.sh on Mac (if accessible)
  → Retry with fresh cookies
  → Save storageState on success
  → If fail → Step 4

Step 4: Browserbase isolated session
  → Spin up Browserbase managed browser
  → Inject cookies, attempt access
  → Separate identity, no risk to real accounts
  → If blocked → Step 5

Step 5: Escalate to human
  → 2FA required, CAPTCHA, new account setup
  → Report what's needed, provide URL, wait for resolution
```

---

## 7. Strategy Learning System

### Record (PostToolUse hooks — automatic)

Every web operation (browse, scrape, search) auto-records outcome:
- Domain (origin)
- Method used (jina, firecrawl, browse_auto, browse_time, etc.)
- Success (bool) — based on content quality score
- Latency (ms)
- Timestamp

Stored in SQLite WAL at `/opt/web-agent/strategy.db` via upsert.

### Query (check_strategy tool — agent-initiated)

Agent calls `check_strategy(origin)` before choosing method. UCB bandit algorithm selects strategy balancing exploration vs exploitation.

### Seed (fingerprint tool — auto-seed)

When `fingerprint(url)` runs, it auto-seeds candidate strategies based on site type:
- SPA → [jina, browse_auto, browse_time]
- Static → [jina, browse_fast]
- Auth required → adds [browse_with_cookies]
- Bot-hostile → adds [browserbase]

---

## 8. Proactive Monitoring

### Registration

`watch_url(url, interval_minutes, notify_method)` registers a URL for periodic monitoring.

### Execution

Background asyncio task in `lib/monitor.py`:
- On each interval: scrape URL, hash content, compare to last hash
- If changed: store diff, emit notification

### Notification methods

- Log to file (default)
- Webhook POST to specified URL
- Store in SQLite for next query() to pick up

---

## 9. Dual-Mode Routing

### Agent mode (default)

```python
@mcp.tool()
async def web_task(
    task: str,
    url: str = "",
    output_schema: dict | None = None,
    timeout_s: int = 120,
    effort: str = "high",
) -> dict:
    """Full agent reasoning. Claude figures out approach, tools, retries."""
    # → Routes to ClaudeSDKClient session pool
    # → Agent reasons with adaptive thinking
    # → Returns structured output if schema provided
```

### Direct mode (bypass — no LLM cost)

```python
@mcp.tool()
async def web_scrape(url: str, use_firecrawl: bool = False) -> dict:
    """Direct extraction. No agent reasoning. Zero token cost."""
    # → Calls lib/scrape.py directly
    # → Returns raw result
```

### How callers choose

- **Simple, known operation** → call `web_scrape`, `web_browse`, `web_search` directly
- **Complex, ambiguous, or multi-step** → call `web_task` with natural language description
- **Need structured data** → call `web_task` with `output_schema`

---

## 10. System Prompt Design

Custom string (not Claude Code preset). Focused on web mastery judgment:

**Contents (~4KB):**
1. Identity and role (universal web master)
2. Tool selection framework (when to scrape vs browse vs search)
3. Auth strategy (check storageState → cookies → Browserbase → escalate)
4. Quality validation (always validate before returning, retry on poor score)
5. Strategy learning (check cache → use best → outcomes auto-recorded)
6. Structured output compliance (match caller's schema)
7. Anti-patterns (never return empty content, never skip validation, never guess — verify)
8. Escalation rules (when to use fallback model, when to escalate to human)

---

## 11. File Structure

```
mcp-servers/web-agent/
├── pyproject.toml              # claude-agent-sdk, fastmcp, playwright, httpx, aiohttp
├── server.py                   # FastMCP endpoint — dual-mode routing
├── agent.py                    # ClaudeSDKClient pool, session lifecycle, query dispatch
├── tools.py                    # All @tool definitions + create_sdk_mcp_server
├── hooks.py                    # PreToolUse, PostToolUse, Stop, UserPromptSubmit callbacks
├── system_prompt.md            # Agent expertise (web mastery instructions)
├── deploy.sh                   # rsync + syntax check + systemd restart + health check
├── lib/
│   ├── __init__.py
│   ├── browser.py              # Async Playwright: lifecycle, readiness ladder, context pooling
│   ├── scrape.py               # Async Jina Reader + Firecrawl extraction
│   ├── search.py               # Async Firecrawl search
│   ├── fingerprint.py          # Async site framework/CMS/type classification
│   ├── quality.py              # Content quality scoring (login walls, errors, emptiness)
│   ├── strategy.py             # SQLite WAL UCB bandit cache
│   ├── stealth.py              # Persona profiles (coherent UA/viewport/locale/timezone)
│   ├── sessions.py             # storageState persistence, cookie loading, auth escalation
│   └── monitor.py              # URL watch registration, change detection, notifications
└── tests/
    ├── test_tools.py           # Unit tests for all @tool functions
    ├── test_hooks.py           # Hook behavior verification
    ├── test_agent.py           # Integration: SDK agent with real URLs
    └── test_monitor.py         # Proactive monitoring tests
```

---

## 12. Build Phases

| Phase | Name | What | Files | Depends On |
|-------|------|------|-------|-----------|
| **1** | Foundation | pyproject.toml, all lib/ modules | pyproject.toml, lib/*.py | Nothing |
| **2** | Tools | @tool definitions, create_sdk_mcp_server | tools.py | Phase 1 |
| **3** | Hooks | All hook callbacks (PreToolUse, PostToolUse, Stop, UserPromptSubmit) | hooks.py | Phase 2 |
| **4** | System Prompt | Web mastery instructions compiled from research | system_prompt.md | Research docs |
| **5** | Agent | ClaudeSDKClient pool, session management, query dispatch | agent.py | Phases 2-4 |
| **6** | Server | FastMCP endpoint, dual-mode routing, structured output support | server.py | Phase 5 |
| **7** | Deploy | deploy.sh, systemd unit, Cloudflare tunnel, cutover from old web-agent | deploy.sh | Phase 6 |
| **8** | Test | All test suites: unit, integration, agent mode | tests/*.py | Phase 7 |
| **9** | Monitor | Proactive URL monitoring, watch_url tool, background tasks | lib/monitor.py, tool addition | Phase 8 |

---

## 13. Infrastructure

- **Droplet:** Current 4GB, design flexible (verified: 669MB used, 3.2GB available)
- **Port:** 8001 (same as current)
- **Tunnel:** Cloudflare at web.3niac.com/mcp (no change needed)
- **Auth:** ANTHROPIC_API_KEY in /opt/web-agent/.env, passed via systemd EnvironmentFile
- **Persistence:** SQLite WAL at /opt/web-agent/strategy.db, storageState JSONs at /opt/web-agent/sessions/
- **Cookies:** /opt/ai-cos/cookies/ (5 domains, daily sync from Mac)
- **systemd:** Hardened unit (MemoryHigh=768M, MemoryMax=1G, OOMScoreAdjust=500, ExecStopPost pkill chrome)
- **Monitoring:** 60s health check cron (curl MCP endpoint, restart on failure)
- **Rollback:** web-tools-mcp service stays stopped but available at /opt/web-tools-mcp/

---

## 14. Verified Technical Facts

All claims below are verified against source code or test output (per feedback rule):

| Claim | Verified | Evidence |
|-------|----------|---------|
| Agent SDK works as root with dontAsk mode | Yes | Test output: `RESULT: SDK_ROOT_TEST_OK` |
| bypassPermissions blocked as root | Yes | Error: `--dangerously-skip-permissions cannot be used with root/sudo privileges` |
| ANTHROPIC_API_KEY must be in env | Yes | Without: `Not logged in`. With: works. |
| Bundled CLI at 227MB on disk | Yes | `du -sh` on droplet |
| Current memory: 669MB used, 3.2GB available | Yes | `free -h` on droplet |
| web-agent RSS: 64MB, ai-cos-mcp: 68MB | Yes | `systemctl show --property=MemoryCurrent` |
| claude-agent-sdk 0.1.48 installed | Yes | `uv pip install` output |
| Chrome 146.0.7680.80 on droplet | Yes | `google-chrome --version` |
| Custom tools work with query() via mcp_servers | Yes | Official docs confirm |
| ClaudeSDKClient required for hooks | Yes | Python README: "Unlike query(), ClaudeSDKClient additionally enables custom tools and hooks" |

---

## 15. Test URLs

| # | URL | Tests | Expected |
|---|-----|-------|----------|
| 1 | `simonwillison.net/2024/Dec/19/one-shot-python-tools/` | scrape, fingerprint | Jina direct, article, non-SPA |
| 2 | `linear.app/features` | browse, fingerprint | SPA (Next.js), readiness ladder |
| 3 | `amazon.com/dp/B0DKHZTGQS` | browse, stealth | Bot-hostile, graceful fail or Browserbase |
| 4 | `discord.com/safety` | scrape | Cloudflare, Jina best penetration |
| 5 | `docs.anthropic.com/en/docs/about-claude/models` | browse, fingerprint | Next.js SPA, readiness ladder |
| 6 | `example.com/nonexistent-page-404` | scrape, validate | 404 detection |
| 7 | `x.com/home` | browse, auth, session | Cookies + storageState, SPA |
| 8 | `x.com/i/bookmarks` | browse, auth, interact | Auth + scroll + extract |
| 9 | `linkedin.com/in/kumaraakash/recent-activity/all/` | browse, stealth | Bot-hostile, graceful fail |
| 10 | `substack.com/inbox/post/190905077` | browse, auth | Cookies or Jina |

---

## 16. Success Criteria

| # | Criterion | Pass Threshold |
|---|-----------|----------------|
| 1 | health_check | Returns 200 in <2s |
| 2 | Direct scrape (Jina) | content_length > 1000 for 5/6 public URLs |
| 3 | Direct browse (Playwright) | content_length > 200 for 5/6 public URLs within 15s |
| 4 | Authenticated browse | storageState or cookies loaded for x.com, youtube.com, substack.com |
| 5 | Agent mode (web_task) | status="complete", output non-empty, <60s, <$1 cost |
| 6 | Structured output | Returns valid JSON matching provided schema |
| 7 | Fingerprinting | Correctly classifies >= 8/10 test URLs |
| 8 | Strategy learning | After 10 outcomes, UCB selects winner >80% |
| 9 | Quality validation | Rejects login walls (score <40), accepts good content (>=70) |
| 10 | Endpoint identity | web.3niac.com/mcp returns serverInfo.name = "web-agent" |
| 11 | Rollback | web-tools-mcp starts on port 8001 within 10s |
| 12 | Monitoring cron | Restarts service within 60s of simulated crash |
| 13 | Adaptive model | Falls back to Opus when Sonnet fails on complex task |
| 14 | Extended thinking | Agent uses thinking for multi-step task planning |

---

## 17. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| SDK CLI subprocess overhead per query | Latency, memory | Session pool reuses connections; direct mode bypasses SDK entirely |
| Token cost on complex web_task | $$$ | max_budget_usd=$2, max_turns=20, effort="medium" default |
| Chrome OOM on 4GB droplet | Crash | Semaphore(2) on concurrent contexts, MemoryMax=1G systemd |
| Cookie/session expiry | Auth failures | 5-step escalation ladder, storageState persistence |
| Strategy cache corruption | Wrong method selection | SQLite WAL mode, graceful fallback to default strategy |
| Browserbase cost | Per-session charges | Last resort only (step 4 of auth ladder) |
| SDK version changes | Breaking API | Pin claude-agent-sdk version in pyproject.toml |
