# Three-Agent Architecture Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build 3 Claude Agent SDK agents (Web, Content, Sync) in a shared monorepo at `mcp-servers/agents/`, deployable to `/opt/agents/` on the droplet.

**Architecture:** FastMCP servers wrapping ClaudeSDKClient agents. Inter-agent communication via MCP HTTP tool calls. Sync Agent is the gateway (port 8000, mcp.3niac.com). Web Agent is the leaf (port 8001). Content Agent orchestrates pipeline (port 8002). All agents share a single Python venv and claude-agent-sdk CLI binary.

**Tech Stack:** claude-agent-sdk 0.1.48, FastMCP 2.x, Playwright, httpx, psycopg2, yt-dlp, SQLite WAL

**Spec:** `docs/superpowers/specs/2026-03-15-three-agent-architecture-design.md` (LOCKED)

**Existing code to migrate:**
- `mcp-servers/ai-cos-mcp/lib/` → `agents/sync/lib/` (notion_client, thesis_db, actions_db, preferences, change_detection)
- `mcp-servers/ai-cos-mcp/runners/` → replaced by Content Agent + Sync Agent
- `mcp-servers/ai-cos-mcp/server.py` → replaced by Sync Agent server.py
- `mcp-servers/web-agent/lib/` → `agents/web/lib/` (browser, scrape, search, fingerprint, quality, strategy, stealth, sessions)
- `mcp-servers/web-agent/` → replaced by Web Agent (new tools.py, agent.py, hooks.py, server.py)
- `mcp-servers/ai-cos-mcp/lib/extraction.py` → `agents/web/lib/extraction.py`
- `mcp-servers/ai-cos-mcp/lib/scoring.py` → `agents/content/lib/scoring.py`
- `mcp-servers/ai-cos-mcp/lib/publishing.py` → `agents/content/lib/publishing.py`

---

## Chunk 0: Foundation

### Task 0.1: Project Scaffold

**Files:**
- Create: `mcp-servers/agents/pyproject.toml`
- Create: `mcp-servers/agents/shared/__init__.py`
- Create: `mcp-servers/agents/shared/types.py`
- Create: `mcp-servers/agents/shared/mcp_client.py`
- Create: `mcp-servers/agents/shared/logging.py`
- Create: `mcp-servers/agents/.env.example`
- Create: `mcp-servers/agents/web/__init__.py`
- Create: `mcp-servers/agents/content/__init__.py`
- Create: `mcp-servers/agents/sync/__init__.py`

- [ ] **Step 1: Create project directory structure**

```bash
cd mcp-servers && mkdir -p agents/{shared,web/lib,web/tests,content/lib,content/tests,sync/lib,sync/tests,data,cookies,logs,cron}
touch agents/{shared,web,web/lib,web/tests,content,content/lib,content/tests,sync,sync/lib,sync/tests}/__init__.py
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[project]
name = "aicos-agents"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "claude-agent-sdk==0.1.48",
    "fastmcp>=2.0.0",
    "playwright>=1.49",
    "httpx>=0.27",
    "aiohttp>=3.9",
    "psycopg2-binary>=2.9",
    "python-dotenv>=1.0",
    "python-json-logger>=2.0",
    "yt-dlp>=2024.1",
    "youtube-transcript-api>=1.0",
    "pybreaker>=1.2",
]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
testpaths = ["web/tests", "content/tests", "sync/tests"]
asyncio_mode = "auto"
```

- [ ] **Step 3: Write shared/types.py — shared response schemas**

```python
"""Shared types across all agents. Import from here, not from individual agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DigestData:
    """Schema for content analysis output. Content Agent produces, Sync Agent consumes."""
    title: str
    slug: str
    url: str
    channel: str
    content_type: str = ""
    duration: str = ""
    relevance_score: str = "Medium"
    net_newness: dict[str, Any] = field(default_factory=dict)
    connected_buckets: list[str] = field(default_factory=list)
    essence_notes: dict[str, Any] = field(default_factory=dict)
    thesis_connections: list[dict[str, Any]] = field(default_factory=list)
    portfolio_connections: list[dict[str, Any]] = field(default_factory=list)
    proposed_actions: list[dict[str, Any]] = field(default_factory=list)
    contra_signals: list[dict[str, Any]] = field(default_factory=list)
    rabbit_holes: list[dict[str, Any]] = field(default_factory=list)
    watch_sections: list[dict[str, Any]] = field(default_factory=list)
    new_thesis_suggestions: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""
    upload_date: str | None = None
    request_id: str = ""  # Idempotency key (C2)


@dataclass
class ActionProposal:
    """Single proposed action from content analysis."""
    action: str
    priority: str = "P2"
    action_type: str = "content"
    assigned_to: str = "Aakash"
    reasoning: str = ""
    thesis_connections: list[str] = field(default_factory=list)
    company: str | None = None
    score: float = 0.0
    classification: str = "context_only"
    request_id: str = ""  # Idempotency key (C2)


@dataclass
class ThesisEvidence:
    """Evidence to append to a thesis thread."""
    thesis_name: str
    evidence: str
    direction: str = "for"  # "for", "against", "mixed"
    source: str = "Content Pipeline"
    conviction: str | None = None
    new_key_questions: list[str] | None = None
    answered_questions: list[str] | None = None
    investment_implications: str | None = None
    key_companies: str | None = None
    request_id: str = ""  # Idempotency key (C2)
```

- [ ] **Step 4: Write shared/logging.py — structured JSON logging (C4)**

```python
"""Structured JSON logging for all agents. Trace ID propagation."""
from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar

from pythonjsonlogger import json as jsonlogger

# Trace ID for cross-agent request correlation
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


def get_trace_id() -> str:
    return _trace_id.get() or ""


def set_trace_id(trace_id: str | None = None) -> str:
    tid = trace_id or uuid.uuid4().hex[:16]
    _trace_id.set(tid)
    return tid


class AgentJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["trace_id"] = get_trace_id()
        log_record["agent"] = getattr(record, "agent", "unknown")


def setup_logger(agent_name: str, log_file: str | None = None) -> logging.Logger:
    logger = logging.getLogger(agent_name)
    logger.setLevel(logging.INFO)

    formatter = AgentJsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "agent"},
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
```

- [ ] **Step 5: Write shared/mcp_client.py — inter-agent MCP client with circuit breaker (C3)**

```python
"""HTTP MCP client for inter-agent communication. Includes circuit breaker + timeouts."""
from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pybreaker

from .logging import get_trace_id

# Circuit breakers per target agent (C3: open after 5 failures, reset 60s)
_breakers: dict[str, pybreaker.CircuitBreaker] = {}


def _get_breaker(agent_name: str) -> pybreaker.CircuitBreaker:
    if agent_name not in _breakers:
        _breakers[agent_name] = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=60, name=f"cb_{agent_name}",
        )
    return _breakers[agent_name]


async def call_agent_tool(
    agent_url: str,
    tool_name: str,
    arguments: dict[str, Any],
    timeout_s: float = 30.0,
    agent_name: str = "unknown",
) -> dict[str, Any]:
    """Call an MCP tool on another agent via HTTP.

    Args:
        agent_url: e.g. "http://localhost:8000/mcp"
        tool_name: e.g. "cos_get_thesis_threads"
        arguments: tool arguments dict
        timeout_s: per-tool timeout (C3)
        agent_name: for circuit breaker key

    Returns:
        Tool result dict

    Raises:
        pybreaker.CircuitBreakerError: if circuit is open
        httpx.TimeoutException: if call exceeds timeout
    """
    breaker = _get_breaker(agent_name)

    # Propagate trace ID
    if "trace_id" not in arguments:
        tid = get_trace_id()
        if tid:
            arguments["trace_id"] = tid

    @breaker
    async def _call():
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.post(
                agent_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                    "id": 1,
                },
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise RuntimeError(f"MCP error: {result['error']}")
            return result.get("result", {})

    return await _call()
```

- [ ] **Step 6: Write .env.example**

```bash
# Shared credentials for all agents
ANTHROPIC_API_KEY=sk-ant-...
NOTION_TOKEN=ntn_...
DATABASE_URL=postgresql://user:pass@localhost:5432/aicos
FIRECRAWL_API_KEY=fc-...
YOUTUBE_PLAYLIST_URL=https://youtube.com/playlist?list=...
YOUTUBE_COOKIES_PATH=/opt/agents/cookies/youtube.txt
AICOS_DIGESTS_REPO=/opt/aicos-digests
VERCEL_DEPLOY_HOOK=https://api.vercel.com/v1/integrations/deploy/...
CONTEXT_MD_PATH=/opt/agents/CONTEXT.md
QUEUE_DIR=/opt/agents/data/queue
```

- [ ] **Step 7: Verify structure**

```bash
cd mcp-servers/agents && find . -type f | head -20
```
Expected: All files created in correct locations.

- [ ] **Step 8: Commit**

```bash
git add mcp-servers/agents/
git commit -m "feat: scaffold 3-agent monorepo with shared types, logging, MCP client"
```

---

## Chunk 1: Sync Agent (Gateway)

The Sync Agent is the critical path — other agents depend on it. This chunk migrates existing `ai-cos-mcp` code into the new structure and adds write-receiver + proxy tools.

### Task 1.1: Migrate Sync Agent libs

**Files:**
- Copy+adapt: `mcp-servers/ai-cos-mcp/lib/notion_client.py` → `agents/sync/lib/notion_client.py`
- Copy+adapt: `mcp-servers/ai-cos-mcp/lib/thesis_db.py` → `agents/sync/lib/thesis_db.py`
- Copy+adapt: `mcp-servers/ai-cos-mcp/lib/actions_db.py` → `agents/sync/lib/actions_db.py`
- Copy+adapt: `mcp-servers/ai-cos-mcp/lib/preferences.py` → `agents/sync/lib/preferences.py`
- Copy+adapt: `mcp-servers/ai-cos-mcp/lib/change_detection.py` → `agents/sync/lib/change_detection.py`
- Copy+adapt: `mcp-servers/ai-cos-mcp/lib/dedup.py` → `agents/sync/lib/dedup.py` (if needed)
- Create: `agents/sync/lib/rate_limiter.py`

**Migration changes to apply to ALL lib files:**
1. Replace `from dotenv import load_dotenv; load_dotenv()` → remove (env loaded by server.py)
2. Replace `DATABASE_URL = os.getenv(...)` → accept `DATABASE_URL` as module-level variable set by server.py init
3. Add `request_id` parameter to all write functions for idempotency (C2)
4. Add duplicate check: `SELECT 1 FROM table WHERE request_id = %s` before insert
5. Add `from shared.logging import get_trace_id` for structured logging
6. No functional logic changes — same SQL, same Notion API calls

- [ ] **Step 1: Copy lib files**

```bash
cd mcp-servers/agents
cp ../ai-cos-mcp/lib/notion_client.py sync/lib/
cp ../ai-cos-mcp/lib/thesis_db.py sync/lib/
cp ../ai-cos-mcp/lib/actions_db.py sync/lib/
cp ../ai-cos-mcp/lib/preferences.py sync/lib/
cp ../ai-cos-mcp/lib/change_detection.py sync/lib/
cp ../ai-cos-mcp/lib/dedup.py sync/lib/
```

- [ ] **Step 2: Apply migration changes to each file** (per list above)

- [ ] **Step 3: Write sync/lib/rate_limiter.py — Notion token bucket (H4)**

```python
"""Token bucket rate limiter for Notion API. 2.5 req/s (conservative)."""
from __future__ import annotations

import asyncio
import time


class TokenBucketRateLimiter:
    def __init__(self, rate: float = 2.5, burst: int = 5):
        self.rate = rate
        self.burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
            self._last_refill = now

            if self._tokens < 1:
                wait = (1 - self._tokens) / self.rate
                await asyncio.sleep(wait)
                self._tokens = 0
            else:
                self._tokens -= 1


notion_limiter = TokenBucketRateLimiter(rate=2.5, burst=5)
```

- [ ] **Step 4: Write basic tests for migrated libs**

```bash
# Test that imports work and basic functions are callable
cd mcp-servers/agents && python3 -c "from sync.lib.thesis_db import create_thread; print('thesis_db OK')"
cd mcp-servers/agents && python3 -c "from sync.lib.preferences import get_preferences; print('preferences OK')"
```

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/agents/sync/lib/
git commit -m "feat(sync): migrate lib files from ai-cos-mcp with idempotency + rate limiter"
```

### Task 1.2: Sync Agent Tools (FastMCP)

**Files:**
- Create: `agents/sync/tools.py`

This file contains ALL @tool definitions for the Sync Agent FastMCP server. There are 3 categories:
1. **State read tools** (9 tools — migrated from current server.py)
2. **Write-receiver tools** (5 tools — NEW, for Content Agent)
3. **Sync operation tools** (6 tools — migrated from current server.py)
4. **Proxy tools** (3 tools — NEW, forward to Web Agent)

- [ ] **Step 1: Create tools.py with all tool definitions**

Reference: `mcp-servers/ai-cos-mcp/server.py` lines 23-474 for existing tool implementations.
Reference: Spec §5 "FastMCP Tools Exposed" for the full tool list.

Key patterns for new write-receiver tools:
```python
# Pattern for write-receiver tools (new)
@mcp.tool()
async def write_digest(digest_data: dict, request_id: str) -> dict:
    """Create digest entry in Notion Content Digest DB.
    Called by Content Agent after analysis. Idempotent via request_id."""
    # 1. Check idempotency
    if _check_request_id("digests", request_id):
        return {"status": "duplicate", "request_id": request_id}
    # 2. Rate limit
    await notion_limiter.acquire()
    # 3. Write to Notion
    from sync.lib.notion_client import create_digest_entry
    result = create_digest_entry(**digest_data)
    # 4. Record request_id
    _record_request_id("digests", request_id)
    return {"status": "created", "notion_page_id": result.get("id"), "request_id": request_id}
```

Key pattern for proxy tools:
```python
# Pattern for proxy tools (forward to Web Agent)
@mcp.tool()
async def web_task(task: str, url: str = "", output_schema: dict | None = None) -> dict:
    """Proxy to Web Agent's web_task tool. For CAI access via gateway."""
    from shared.mcp_client import call_agent_tool
    return await call_agent_tool(
        "http://localhost:8001/mcp", "web_task",
        {"task": task, "url": url, "output_schema": output_schema},
        timeout_s=120.0, agent_name="web",
    )
```

- [ ] **Step 2: Write tests for tools**

Test file: `agents/sync/tests/test_tools.py`
- Test idempotency: call write_digest twice with same request_id → second returns "duplicate"
- Test rate limiter integration
- Test proxy tool error handling (Web Agent down → circuit breaker)

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/sync/tools.py mcp-servers/agents/sync/tests/
git commit -m "feat(sync): all MCP tools — state reads, write-receivers, sync ops, proxies"
```

### Task 1.3: Sync Agent Server + Agent + Hooks

**Files:**
- Create: `agents/sync/server.py`
- Create: `agents/sync/agent.py`
- Create: `agents/sync/hooks.py`
- Create: `agents/sync/system_prompt.md`

- [ ] **Step 1: Write server.py — FastMCP server on port 8000**

```python
"""Sync Agent — Gateway MCP server.
THE ONLY agent that reads/writes Notion + Postgres.
Port 8000, mcp.3niac.com via Cloudflare Tunnel.
"""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv(Path(__file__).parent.parent / ".env")

mcp = FastMCP(
    "sync-agent",
    instructions="AI CoS Sync Agent. Gateway for all state operations. Thesis, Actions, Preferences, Sync.",
)

# Import all tools (they register with @mcp.tool())
from sync.tools import *  # noqa: F401,F403

# Internal sync timer (10-min cycle)
async def _sync_loop():
    from sync.lib.change_detection import full_sync_cycle
    while True:
        try:
            await full_sync_cycle()
        except Exception as e:
            logger.error(f"Sync cycle failed: {e}")
        await asyncio.sleep(600)  # 10 minutes

# Start sync loop on server startup
@mcp.on_startup()
async def startup():
    asyncio.create_task(_sync_loop())

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

- [ ] **Step 2: Write agent.py — ClaudeSDKClient for autonomous sync reasoning**

Reference: Spec §5 "SDK Configuration" for the full ClaudeAgentOptions.
This is used ONLY for complex sync operations (change interpretation, action generation), NOT for regular tool handling.

- [ ] **Step 3: Write hooks.py — audit logging + metrics**

```python
"""Sync Agent hooks. PostToolUse: audit log. Stop: sync metrics."""
from shared.logging import setup_logger, get_trace_id

logger = setup_logger("sync-agent", "/opt/agents/logs/sync.log")

async def sync_audit_log(result_data, tool_use_id, context):
    logger.info("tool_complete", extra={
        "event_type": "tool_call",
        "tool_name": result_data.get("tool_name"),
        "duration_ms": result_data.get("duration_ms", 0),
        "trace_id": get_trace_id(),
    })
    return {}

async def emit_sync_metrics(result_data, tool_use_id, context):
    logger.info("session_complete", extra={
        "event_type": "session_end",
        "total_cost_usd": result_data.get("cost_usd", 0),
        "turns_used": result_data.get("num_turns", 0),
    })
    return {}
```

- [ ] **Step 4: Write system_prompt.md**

Sync agent instructions: identity, sync strategy, conflict resolution rules, write-ahead pattern, action generation logic. Reference spec §5.

- [ ] **Step 5: Test server starts**

```bash
cd mcp-servers/agents && python3 -m sync.server &
sleep 3
curl -s http://localhost:8000/health_check | python3 -m json.tool
kill %1
```
Expected: health_check returns JSON with server=ok.

- [ ] **Step 6: Commit**

```bash
git add mcp-servers/agents/sync/
git commit -m "feat(sync): complete Sync Agent — server, agent, hooks, system prompt"
```

---

## Chunk 2: Web Agent

Web Agent is a leaf agent — no outbound agent calls. Can be built in parallel with Chunk 1.

### Task 2.1: Migrate Web Agent libs

**Files:**
- Copy+adapt: `mcp-servers/web-agent/lib/browser.py` → `agents/web/lib/browser.py`
- Copy+adapt: `mcp-servers/web-agent/lib/scrape.py` → `agents/web/lib/scrape.py`
- Copy+adapt: `mcp-servers/web-agent/lib/search.py` → `agents/web/lib/search.py`
- Copy+adapt: `mcp-servers/web-agent/lib/fingerprint.py` → `agents/web/lib/fingerprint.py`
- Copy+adapt: `mcp-servers/web-agent/lib/quality.py` → `agents/web/lib/quality.py`
- Copy+adapt: `mcp-servers/web-agent/lib/strategy.py` → `agents/web/lib/strategy.py`
- Copy+adapt: `mcp-servers/web-agent/lib/stealth.py` → `agents/web/lib/stealth.py`
- Copy+adapt: `mcp-servers/web-agent/lib/cookies.py` → `agents/web/lib/sessions.py`
- Copy+adapt: `mcp-servers/ai-cos-mcp/lib/extraction.py` → `agents/web/lib/extraction.py`
- Create: `agents/web/lib/monitor.py`

**Migration changes:**
1. strategy.py: Add `threading.Lock()` for write operations (M2)
2. extraction.py: Remove CONTEXT.md loading (not Web Agent's job), keep yt-dlp + transcript
3. sessions.py: Merge cookies.py + add storageState management
4. All files: Add structured logging imports

- [ ] **Step 1: Copy and adapt all lib files** (per list above)
- [ ] **Step 2: Add threading.Lock to strategy.py writes**
- [ ] **Step 3: Write monitor.py stub** (URL watch registration, asyncio background tasks)
- [ ] **Step 4: Verify imports**

```bash
cd mcp-servers/agents && python3 -c "from web.lib.browser import BrowserManager; print('browser OK')"
cd mcp-servers/agents && python3 -c "from web.lib.extraction import extract_and_save; print('extraction OK')"
```

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/agents/web/lib/
git commit -m "feat(web): migrate lib files with strategy lock + extraction"
```

### Task 2.2: Web Agent Tools + Hooks

**Files:**
- Create: `agents/web/tools.py`
- Create: `agents/web/hooks.py`

- [ ] **Step 1: Write tools.py — all @tool definitions**

11 FastMCP tools (spec §3 "FastMCP Tools Exposed") + 9 internal @tools (spec §3 "Internal @tool Functions").

FastMCP tools pattern (dual-mode routing):
```python
@mcp.tool()
async def web_scrape(url: str, use_firecrawl: bool = False) -> dict:
    """Direct extraction. No agent reasoning. Zero token cost."""
    from web.lib.scrape import scrape_url
    result = await scrape_url(url, use_firecrawl=use_firecrawl)
    return {"content": result["content"], "content_length": len(result.get("content", "")), "url": url}

@mcp.tool()
async def web_task(task: str, url: str = "", output_schema: dict | None = None,
                   timeout_s: int = 120, effort: str = "high") -> dict:
    """Full agent reasoning. Claude figures out approach, tools, retries."""
    from web.agent import run_agent_task
    return await asyncio.wait_for(
        run_agent_task(task, url, output_schema, effort),
        timeout=timeout_s,  # C3: overall timeout
    )
```

Internal @tools for Agent SDK (registered via create_sdk_mcp_server):
```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("browse", "Navigate to URL with Playwright", {"url": str, "readiness_mode": str})
async def browse_tool(args):
    from web.lib.browser import browse_url
    result = await browse_url(args["url"], readiness_mode=args.get("readiness_mode", "auto"))
    return {"content": [{"type": "text", "text": result["content"]}]}

# ... 8 more internal tools

web_sdk_server = create_sdk_mcp_server(
    name="web", version="1.0.0",
    tools=[browse_tool, scrape_tool, search_tool, screenshot_tool, interact_tool,
           fingerprint_tool, check_strategy_tool, manage_session_tool, validate_tool],
)
```

- [ ] **Step 2: Write hooks.py — rate limiting, strategy recording, metrics**

Reference: Spec §3 "Hooks" for all 4 hook types.
Key: PostToolUse `record_strategy_outcome` calls `strategy.py` to log domain/method/success/latency.

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/web/tools.py mcp-servers/agents/web/hooks.py
git commit -m "feat(web): tools (11 FastMCP + 9 SDK) and hooks (rate limit, strategy, metrics)"
```

### Task 2.3: Web Agent Server + Agent + System Prompt

**Files:**
- Create: `agents/web/server.py`
- Create: `agents/web/agent.py`
- Create: `agents/web/system_prompt.md`

- [ ] **Step 1: Write server.py — FastMCP on port 8001, dual-mode routing**

Same pattern as Sync Agent server.py but port 8001, no sync loop.

- [ ] **Step 2: Write agent.py — ClaudeSDKClient config with session pool**

```python
"""Web Agent — ClaudeSDKClient configuration and session management."""
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, ThinkingConfig, HookMatcher
from web.tools import web_sdk_server
from web.hooks import rate_limit_check, input_validation, record_strategy_outcome, log_audit, emit_metrics, inject_strategy_hints

_session_semaphore = asyncio.Semaphore(2)  # H1: max 2 concurrent sessions

async def run_agent_task(task: str, url: str, output_schema: dict | None, effort: str) -> dict:
    async with _session_semaphore:
        options = ClaudeAgentOptions(
            model="claude-sonnet-4-6",
            fallback_model="claude-opus-4-6",
            permission_mode="dontAsk",
            system_prompt=_load_system_prompt(),
            mcp_servers={"web": web_sdk_server},
            allowed_tools=[...],  # per spec §3
            disallowed_tools=["Bash", "Write", "Edit", "Read"],
            thinking=ThinkingConfig(type="enabled", budget_tokens=8000),
            effort=effort,
            max_turns=20,
            max_budget_usd=2.00,
            env={"ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"]},
            cwd="/opt/agents",
            hooks={...},  # per spec §3
        )
        # ... invoke session, collect result
```

- [ ] **Step 3: Write system_prompt.md** (~4KB, spec §3 "System Prompt Outline")

- [ ] **Step 4: Test server starts**

```bash
cd mcp-servers/agents && python3 -m web.server &
sleep 3
curl -s http://localhost:8001/health_check | python3 -m json.tool
kill %1
```

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/agents/web/
git commit -m "feat(web): complete Web Agent — server, agent, hooks, system prompt"
```

### Task 2.4: Web Agent Tests

**Files:**
- Create: `agents/web/tests/test_tools.py`
- Create: `agents/web/tests/test_hooks.py`
- Create: `agents/web/tests/test_agent.py`

- [ ] **Step 1: Write test_tools.py** — unit tests for all FastMCP tools
- [ ] **Step 2: Write test_hooks.py** — verify rate limiting, strategy recording
- [ ] **Step 3: Write test_agent.py** — integration test: web_task with real URL
- [ ] **Step 4: Run tests**

```bash
cd mcp-servers/agents && python3 -m pytest web/tests/ -v
```

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/agents/web/tests/
git commit -m "test(web): unit + integration tests for Web Agent"
```

---

## Chunk 3: Content Agent

Content Agent depends on Sync Agent (for writes) and Web Agent (for extraction).

### Task 3.1: Migrate Content Agent libs

**Files:**
- Copy+adapt: `mcp-servers/ai-cos-mcp/lib/scoring.py` → `agents/content/lib/scoring.py`
- Copy+adapt: `mcp-servers/ai-cos-mcp/lib/publishing.py` → `agents/content/lib/publishing.py`
- Create: `agents/content/lib/formatting.py` (extract from current content_agent.py)

**Migration changes:**
1. scoring.py: No changes (pure logic, no DB access)
2. publishing.py: No changes (git push + Vercel deploy)
3. formatting.py: Extract _format_* functions from current content_agent.py

- [ ] **Step 1: Copy and create lib files**
- [ ] **Step 2: Verify imports**
- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/content/lib/
git commit -m "feat(content): migrate scoring, publishing, formatting libs"
```

### Task 3.2: Content Agent Tools + Hooks

**Files:**
- Create: `agents/content/tools.py`
- Create: `agents/content/hooks.py`

- [ ] **Step 1: Write tools.py — 4 FastMCP tools + 3 internal @tools**

FastMCP tools: `analyze_content`, `trigger_pipeline`, `pipeline_status`, `health_check`
Internal @tools: `score_action`, `publish_digest`, `load_context_sections`

Key: `analyze_content` invokes ClaudeSDKClient with Sync Agent + Web Agent as external MCP servers.

- [ ] **Step 2: Write hooks.py — pipeline completion verification + metrics**

Key: Stop hook `verify_pipeline_completion` checks that for each analyzed video, all expected Sync Agent calls were made.

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/content/tools.py mcp-servers/agents/content/hooks.py
git commit -m "feat(content): tools and hooks for Content Agent"
```

### Task 3.3: Content Agent Server + Agent + System Prompt

**Files:**
- Create: `agents/content/server.py`
- Create: `agents/content/agent.py`
- Create: `agents/content/system_prompt.md`

- [ ] **Step 1: Write server.py — FastMCP on port 8002 with 5-min pipeline timer**

Key difference from other agents: includes asyncio timer that triggers the content pipeline every 5 minutes.

```python
async def _pipeline_loop():
    while True:
        try:
            await run_content_pipeline()
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
        await asyncio.sleep(300)  # 5 minutes
```

- [ ] **Step 2: Write agent.py — ClaudeSDKClient with Sync + Web Agent MCP config**

```python
options = ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    mcp_servers={
        "tools": content_sdk_server,  # In-process: scoring, publishing
        "sync": {"type": "http", "url": "http://localhost:8000/mcp"},  # Sync Agent
    },
    allowed_tools=[
        "mcp__tools__score_action", "mcp__tools__publish_digest", "mcp__tools__load_context_sections",
        "mcp__sync__cos_get_thesis_threads", "mcp__sync__cos_get_preferences",
        "mcp__sync__write_digest", "mcp__sync__write_actions",
        "mcp__sync__update_thesis", "mcp__sync__create_thesis_thread", "mcp__sync__log_preference",
    ],
    thinking=ThinkingConfig(type="enabled", budget_tokens=10000),
    max_budget_usd=1.50,
    # ...
)
```

- [ ] **Step 3: Write system_prompt.md** — content analysis instructions (spec §4 "System Prompt Outline")

Reference: current `mcp-servers/ai-cos-mcp/runners/prompts/content_analysis.md` for the analysis prompt structure. Adapt for Agent SDK (tool usage rules, autonomous reasoning instructions).

- [ ] **Step 4: Write pipeline orchestrator** in server.py

```python
async def run_content_pipeline():
    """Content pipeline: extract → analyze → publish → sync."""
    # 1. Call Web Agent for YouTube extraction
    from shared.mcp_client import call_agent_tool
    extraction = await call_agent_tool(
        "http://localhost:8001/mcp", "extract_youtube",
        {"since_days": 3}, timeout_s=90.0, agent_name="web",
    )
    # 2. Filter relevant videos with transcripts
    # 3. For each video, invoke Agent SDK analysis session
    # 4. Agent autonomously handles thesis lookup, scoring, publishing, Sync Agent writes
```

- [ ] **Step 5: Test server starts**
- [ ] **Step 6: Commit**

```bash
git add mcp-servers/agents/content/
git commit -m "feat(content): complete Content Agent — server, agent, hooks, system prompt, pipeline"
```

### Task 3.4: Content Agent Tests

- [ ] **Step 1: Write test_tools.py** — unit tests
- [ ] **Step 2: Write test_hooks.py** — pipeline completion verification
- [ ] **Step 3: Write test_agent.py** — integration test with mock Sync Agent
- [ ] **Step 4: Run tests**
- [ ] **Step 5: Commit**

---

## Chunk 4: Deployment & Integration

### Task 4.1: Deploy Infrastructure

**Files:**
- Create: `agents/deploy.sh`
- Create: systemd unit files (3)
- Create: `agents/cron/health_check.sh`

- [ ] **Step 1: Write deploy.sh**

```bash
#!/bin/bash
set -e
DROPLET="aicos-droplet"
REMOTE_DIR="/opt/agents"

echo "Deploying agents to $DROPLET:$REMOTE_DIR..."

# 1. Rsync (exclude .env, .venv, data/, logs/)
rsync -avz --exclude='.env' --exclude='.venv' --exclude='__pycache__' \
  --exclude='data/' --exclude='logs/' --exclude='cookies/' \
  ./ root@${DROPLET}:${REMOTE_DIR}/

# 2. Install deps
ssh root@${DROPLET} "cd ${REMOTE_DIR} && /root/.local/bin/uv sync"

# 3. Sync CONTEXT.md
CONTEXT_SRC="$(dirname "$(dirname "$(dirname "$(pwd)")")")/CONTEXT.md"
[ -f "$CONTEXT_SRC" ] && rsync -avz "$CONTEXT_SRC" root@${DROPLET}:${REMOTE_DIR}/CONTEXT.md

# 4. Create directories
ssh root@${DROPLET} "mkdir -p ${REMOTE_DIR}/{data/queue/processed,data/sessions,logs,cookies}"

# 5. Restart services (sync first — gateway)
ssh root@${DROPLET} "systemctl restart sync-agent && sleep 2 && systemctl restart content-agent && systemctl restart web-agent"

# 6. Health check all 3
for port in 8000 8001 8002; do
  ssh root@${DROPLET} "curl -sf http://localhost:${port}/health_check > /dev/null" && echo "Port ${port}: OK" || echo "Port ${port}: FAILED"
done
```

- [ ] **Step 2: Write systemd unit files**

Template for each agent:
```ini
[Unit]
Description=AI CoS <Agent Name>
After=network.target postgresql.service

[Service]
Type=simple
WorkingDirectory=/opt/agents
EnvironmentFile=-/opt/agents/.env
ExecStart=/opt/agents/.venv/bin/python3 -m <module>.server
Restart=always
RestartSec=5
WatchdogSec=120
MemoryMax=<limit>
ExecStopPost=/usr/bin/pkill -f chrome  # Web Agent only

[Install]
WantedBy=multi-user.target
```

Memory limits (H8): sync-agent=512M, content-agent=768M, web-agent=1G

- [ ] **Step 3: Write health_check.sh cron script**

Check all 3 agents every 60s, restart on failure, max 1 restart per 5 minutes.

- [ ] **Step 4: Write Postgres backup cron (H5)**

```bash
# Daily pg_dump at 02:00 UTC, 7-day retention
0 2 * * * pg_dump $DATABASE_URL | gzip > /opt/backups/postgres/aicos-$(date +\%Y\%m\%d).sql.gz && find /opt/backups/postgres/ -mtime +7 -delete
```

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/agents/deploy.sh mcp-servers/agents/cron/
git commit -m "feat: deployment infrastructure — deploy.sh, systemd units, health checks, backups"
```

### Task 4.2: Integration Tests

**Files:**
- Create: `agents/tests/test_integration.py`

- [ ] **Step 1: Write e2e pipeline test**

Test: Content Agent → Web Agent (extract) → Content Agent (analyze) → Sync Agent (write)

- [ ] **Step 2: Write proxy test**

Test: Call web_scrape via Sync Agent (port 8000) → verify result from Web Agent

- [ ] **Step 3: Write failure scenario tests (H7)**

Test matrix:
- Sync Agent down → Content Agent queues locally
- Web Agent down → circuit breaker opens
- Notion 429 → rate limiter pauses writes
- Duplicate request_id → idempotent response

- [ ] **Step 4: Write acceptance.sh — automated success criteria (spec §9)**

Script that runs all 20 success criteria and reports pass/fail.

- [ ] **Step 5: Run all tests**

```bash
cd mcp-servers/agents && python3 -m pytest -v
```

- [ ] **Step 6: Commit**

```bash
git add mcp-servers/agents/tests/
git commit -m "test: integration tests, failure scenarios, acceptance criteria"
```

### Task 4.3: Deploy & Cutover

- [ ] **Step 1: Deploy to droplet**

```bash
cd mcp-servers/agents && ./deploy.sh
```

- [ ] **Step 2: Verify all services running**

```bash
ssh root@aicos-droplet "systemctl status sync-agent content-agent web-agent --no-pager"
```

- [ ] **Step 3: Run acceptance.sh on droplet**

```bash
ssh root@aicos-droplet "cd /opt/agents && bash tests/acceptance.sh"
```

- [ ] **Step 4: Update Cloudflare tunnels**

Verify mcp.3niac.com → localhost:8000 (Sync Agent, unchanged port)

- [ ] **Step 5: Stop old services**

```bash
ssh root@aicos-droplet "systemctl stop ai-cos-mcp web-agent-old || true"
```

Old services remain installed for rollback but stopped.

- [ ] **Step 6: Verify from CAI**

Call cos_get_thesis_threads via mcp.3niac.com — should return thesis data.

- [ ] **Step 7: Commit all remaining changes**

```bash
git add -A && git commit -m "feat: three-agent architecture deployed and verified"
```

---

## File Map (Complete)

```
mcp-servers/agents/
├── pyproject.toml                          # Task 0.1
├── .env.example                            # Task 0.1
├── deploy.sh                               # Task 4.1
├── shared/
│   ├── __init__.py                         # Task 0.1
│   ├── types.py                            # Task 0.1
│   ├── mcp_client.py                       # Task 0.1
│   └── logging.py                          # Task 0.1
├── sync/
│   ├── __init__.py                         # Task 0.1
│   ├── server.py                           # Task 1.3
│   ├── agent.py                            # Task 1.3
│   ├── tools.py                            # Task 1.2
│   ├── hooks.py                            # Task 1.3
│   ├── system_prompt.md                    # Task 1.3
│   ├── lib/
│   │   ├── __init__.py                     # Task 0.1
│   │   ├── notion_client.py               # Task 1.1 (migrated)
│   │   ├── thesis_db.py                    # Task 1.1 (migrated)
│   │   ├── actions_db.py                   # Task 1.1 (migrated)
│   │   ├── preferences.py                  # Task 1.1 (migrated)
│   │   ├── change_detection.py             # Task 1.1 (migrated)
│   │   ├── dedup.py                        # Task 1.1 (migrated)
│   │   └── rate_limiter.py                 # Task 1.1 (new)
│   └── tests/
│       ├── __init__.py                     # Task 0.1
│       ├── test_tools.py                   # Task 1.2
│       └── test_sync.py                    # Task 1.3
├── web/
│   ├── __init__.py                         # Task 0.1
│   ├── server.py                           # Task 2.3
│   ├── agent.py                            # Task 2.3
│   ├── tools.py                            # Task 2.2
│   ├── hooks.py                            # Task 2.2
│   ├── system_prompt.md                    # Task 2.3
│   ├── lib/
│   │   ├── __init__.py                     # Task 0.1
│   │   ├── browser.py                      # Task 2.1 (migrated)
│   │   ├── scrape.py                       # Task 2.1 (migrated)
│   │   ├── search.py                       # Task 2.1 (migrated)
│   │   ├── fingerprint.py                  # Task 2.1 (migrated)
│   │   ├── quality.py                      # Task 2.1 (migrated)
│   │   ├── strategy.py                     # Task 2.1 (migrated + lock)
│   │   ├── stealth.py                      # Task 2.1 (migrated)
│   │   ├── sessions.py                     # Task 2.1 (new, merged cookies + storageState)
│   │   ├── monitor.py                      # Task 2.1 (new stub)
│   │   └── extraction.py                   # Task 2.1 (migrated from ai-cos-mcp)
│   └── tests/
│       ├── __init__.py                     # Task 0.1
│       ├── test_tools.py                   # Task 2.4
│       ├── test_hooks.py                   # Task 2.4
│       └── test_agent.py                   # Task 2.4
├── content/
│   ├── __init__.py                         # Task 0.1
│   ├── server.py                           # Task 3.3
│   ├── agent.py                            # Task 3.3
│   ├── tools.py                            # Task 3.2
│   ├── hooks.py                            # Task 3.2
│   ├── system_prompt.md                    # Task 3.3
│   ├── lib/
│   │   ├── __init__.py                     # Task 0.1
│   │   ├── scoring.py                      # Task 3.1 (migrated)
│   │   ├── publishing.py                   # Task 3.1 (migrated)
│   │   └── formatting.py                   # Task 3.1 (extracted)
│   └── tests/
│       ├── __init__.py                     # Task 0.1
│       ├── test_tools.py                   # Task 3.4
│       ├── test_hooks.py                   # Task 3.4
│       └── test_agent.py                   # Task 3.4
├── data/                                   # Created at deploy time
│   ├── strategy.db
│   ├── sessions/
│   └── queue/
├── cookies/                                # Synced from Mac
├── logs/                                   # Created at deploy time
├── cron/
│   └── health_check.sh                     # Task 4.1
└── tests/
    ├── test_integration.py                 # Task 4.2
    └── acceptance.sh                       # Task 4.2
```

## Dependency Graph

```
Task 0.1 (Foundation) ──→ Task 1.1 (Sync libs)  ──→ Task 1.2 (Sync tools) ──→ Task 1.3 (Sync server)
                      └──→ Task 2.1 (Web libs)   ──→ Task 2.2 (Web tools)  ──→ Task 2.3 (Web server) ──→ Task 2.4 (Web tests)
                                                                                       │
Task 1.3 + Task 2.3 ──→ Task 3.1 (Content libs)  ──→ Task 3.2 (Content tools) ──→ Task 3.3 (Content server) ──→ Task 3.4 (Content tests)
                                                                                                                          │
All agents ──→ Task 4.1 (Deploy infra) ──→ Task 4.2 (Integration tests) ──→ Task 4.3 (Deploy & cutover)
```

**Parallelizable:** Tasks 1.x and 2.x can run in parallel after Task 0.1.
**Sequential:** Tasks 3.x must wait for both 1.x and 2.x. Tasks 4.x must wait for all.
