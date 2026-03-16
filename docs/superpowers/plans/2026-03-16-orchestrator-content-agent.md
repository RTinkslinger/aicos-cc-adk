# Orchestrator + Content Agent — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire orchestrator and content agent as persistent ClaudeSDKClient sessions managed by lifecycle.py, connected via @tool bridge, with heartbeat scheduling, inbox relay, and content pipeline triggers.

**Architecture:** Single Python daemon (lifecycle.py) creates two persistent ClaudeSDKClients: orchestrator + content agent. Orchestrator receives 60s heartbeats, checks inbox, triggers content pipeline. Communicates with content agent via in-process `@tool` (`send_to_content_agent`) that forwards prompts to the content client's session. Each agent workspace has a `CLAUDE.md` file (Agent SDK reads this automatically via `setting_sources=["project"]`, same as CC) containing identity, behavioral rules, and lifecycle protocols. No custom `system_prompt` parameter — agents get CC's built-in tool instructions plus CLAUDE.md. No changes to State MCP, Web Tools MCP, Postgres, or any other infrastructure.

**Tech Stack:** Python 3.12, `claude_agent_sdk` (ClaudeSDKClient, @tool, create_sdk_mcp_server, ClaudeAgentOptions, ResultMessage, ThinkingConfigEnabled), asyncio, filesystem hooks (bash/jq), systemd.

**Prerequisite:** Lifecycle management plan (`docs/superpowers/plans/2026-03-16-agent-lifecycle-management.md`) — provides traces dir, orchestrator hooks, state dir, compaction protocols. This plan builds on that: replaces lifecycle.py and adds system prompts + content agent persistent rewrite.

---

## File Structure

```
mcp-servers/agents/
  orchestrator/
    lifecycle.py              # REWRITE (replaces lifecycle plan Task 7) — both clients + @tool bridge
    CLAUDE.md                 # NEW — orchestrator identity, rules, lifecycle protocol (SDK reads automatically)
    HEARTBEAT.md              # NEW — heartbeat checklist
    .claude/                  # FROM LIFECYCLE PLAN (unchanged)
      hooks/
        stop-iteration-log.sh
        prompt-manifest-check.sh
        pre-compact-flush.sh
      settings.json
    state/                    # FROM LIFECYCLE PLAN (unchanged)
      orc_session.txt
      orc_iteration.txt
      orc_last_log.txt
      COMPACTION_PROTOCOL.md
      CHECKPOINT_FORMAT.md
  content/
    CLAUDE.md                 # REWRITE — persistent mode, SDK reads automatically (existing logic preserved, scheduling removed)
    runner.py                 # DELETE — replaced by lifecycle.py
    .claude/                  # NEW
      hooks/
        stop-iteration-log.sh     # Clone from orchestrator, AGENT="content"
        prompt-manifest-check.sh  # Clone from orchestrator, AGENT="content"
        pre-compact-flush.sh      # Clone from orchestrator, AGENT="content"
      settings.json
    state/                        # NEW
      content_session.txt
      content_iteration.txt
      content_last_log.txt
      last_pipeline_run.txt       # ISO timestamp — orchestrator reads this
      CHECKPOINT_FORMAT.md
  traces/
    manifest.json             # MODIFY — add "content" entry
```

**What does NOT change:** State MCP (server.py, db/), Web Tools MCP (web/), skills/, .claude/agents/, sql/, infra/state-mcp.service, infra/web-tools-mcp.service, Postgres schema, Cloudflare tunnels.

---

## Chunk 1: @tool Bridge + Lifecycle Rewrite

### Task 1: Update manifest.json for both agents

**Files:**
- Modify: `mcp-servers/agents/traces/manifest.json`

- [ ] **Step 1: Add content agent entry**

```json
{
  "orc": {
    "session": 1,
    "input_tokens": 0,
    "output_tokens": 0,
    "last_updated": null
  },
  "content": {
    "session": 1,
    "input_tokens": 0,
    "output_tokens": 0,
    "last_updated": null
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add mcp-servers/agents/traces/manifest.json
git commit -m "feat: add content agent to traces manifest"
```

### Task 2: Rewrite lifecycle.py — both clients + @tool bridge

**Files:**
- Rewrite: `mcp-servers/agents/orchestrator/lifecycle.py`

- [ ] **Step 1: Write lifecycle.py**

```python
"""Lifecycle manager — orchestrator + content agent.

Manages two persistent ClaudeSDKClient sessions connected via @tool bridge.
Thin wrapper — ALL intelligence in system prompts, ALL logging in hooks.

Does 5 things:
  1. Creates persistent ClaudeSDKClient for content agent
  2. Creates persistent ClaudeSDKClient for orchestrator (with @tool bridge)
  3. Sends "heartbeat" to orchestrator every 60s
  4. Tracks token usage for both agents → traces/manifest.json
  5. Detects COMPACT_NOW → restarts the appropriate agent session
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HEARTBEAT_INTERVAL = 60
MAX_RESPONSE_CHARS = 2000
AGENTS_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = AGENTS_ROOT / "traces" / "manifest.json"
ORC_WORKSPACE = Path(__file__).parent
CONTENT_WORKSPACE = AGENTS_ROOT / "content"

logger = logging.getLogger("lifecycle")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


class ClientState:
    content_client: Any = None
    content_needs_restart: bool = False


clients = ClientState()


# --- Manifest helpers ---

def read_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {}


def write_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2))
    tmp.rename(MANIFEST_PATH)


def update_manifest_tokens(agent: str, usage: dict | None) -> None:
    if not usage:
        return
    manifest = read_manifest()
    if agent not in manifest:
        manifest[agent] = {"session": read_session_num(agent), "input_tokens": 0, "output_tokens": 0, "last_updated": None}
    manifest[agent]["input_tokens"] += usage.get("input_tokens", 0)
    manifest[agent]["output_tokens"] += usage.get("output_tokens", 0)
    manifest[agent]["last_updated"] = datetime.now(timezone.utc).isoformat()
    write_manifest(manifest)


def reset_manifest_tokens(agent: str, session_num: int) -> None:
    manifest = read_manifest()
    manifest[agent] = {"session": session_num, "input_tokens": 0, "output_tokens": 0, "last_updated": datetime.now(timezone.utc).isoformat()}
    write_manifest(manifest)


# --- Session state helpers ---

def _state_dir(agent: str) -> Path:
    return (ORC_WORKSPACE if agent == "orc" else CONTENT_WORKSPACE) / "state"


def read_session_num(agent: str) -> int:
    path = _state_dir(agent) / f"{agent}_session.txt"
    return int(path.read_text().strip()) if path.exists() else 1


def write_session_num(agent: str, n: int) -> None:
    path = _state_dir(agent) / f"{agent}_session.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(n))


def reset_iteration(agent: str) -> None:
    (_state_dir(agent) / f"{agent}_iteration.txt").write_text("0")


def bump_session(agent: str) -> None:
    new = read_session_num(agent) + 1
    write_session_num(agent, new)
    reset_iteration(agent)
    logger.info("%s: bumped to session #%d", agent, new)


# --- @tool bridge ---

def create_bridge_server():
    from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, create_sdk_mcp_server, tool

    @tool("send_to_content_agent", "Send prompt to the persistent Content Agent and return its response", {"prompt": str})
    async def send_to_content_agent(args: dict[str, Any]) -> dict[str, Any]:
        if clients.content_client is None:
            return {"content": [{"type": "text", "text": "Error: Content agent not connected"}], "is_error": True}

        prompt = args["prompt"]
        logger.info("Bridge: forwarding to content agent (%d chars)", len(prompt))
        await clients.content_client.query(prompt)

        result_text = ""
        async for msg in clients.content_client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        result_text += block.text
            elif isinstance(msg, ResultMessage):
                update_manifest_tokens("content", msg.usage)
                logger.info("Bridge: content done — turns=%d, cost=$%.4f", msg.num_turns, msg.total_cost_usd or 0)

        if "COMPACT_NOW" in result_text:
            clients.content_needs_restart = True
            logger.info("Bridge: content agent signaled COMPACT_NOW")

        if len(result_text) > MAX_RESPONSE_CHARS:
            result_text = result_text[:MAX_RESPONSE_CHARS] + "\n[Response truncated]"

        return {"content": [{"type": "text", "text": result_text}]}

    return create_sdk_mcp_server(name="bridge", version="1.0.0", tools=[send_to_content_agent])


# --- Agent option builders ---

def build_orc_options(bridge_server):
    from claude_agent_sdk import ClaudeAgentOptions

    # No system_prompt= parameter. Agent gets CC's built-in tool instructions
    # plus CLAUDE.md from cwd via setting_sources=["project"].
    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=["Bash", "Read", "Write", "Edit", "Glob", "Grep", "mcp__bridge__send_to_content_agent"],
        mcp_servers={"bridge": bridge_server},
        setting_sources=["project"],
        effort="medium",
        max_turns=30,
        max_budget_usd=2.0,
        cwd=str(ORC_WORKSPACE),
        env={"ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""), "DATABASE_URL": os.environ.get("DATABASE_URL", "")},
    )


def build_content_options():
    from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, ThinkingConfigEnabled

    # No system_prompt= parameter. Agent gets CC's built-in tool instructions
    # plus CLAUDE.md from cwd via setting_sources=["project"].
    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Agent", "Skill",
            "mcp__web__web_browse", "mcp__web__web_scrape", "mcp__web__web_search",
            "mcp__web__extract_youtube", "mcp__web__extract_transcript",
            "mcp__web__fingerprint", "mcp__web__check_strategy",
            "mcp__web__manage_session", "mcp__web__validate",
            "mcp__web__cookie_status", "mcp__web__watch_url",
        ],
        mcp_servers={"web": {"type": "http", "url": "http://localhost:8001/mcp"}},
        agents={
            "web-researcher": AgentDefinition(
                description="Web research specialist for complex multi-step web tasks",
                prompt=(
                    "You are a web research specialist. Load skills from /opt/agents/skills/web/ "
                    "for strategy. Use Bash + curl for quick fetches, web_browse for SPAs. "
                    "Complete the research task and return a comprehensive result."
                ),
                tools=[
                    "Bash", "Read", "Write", "Skill",
                    "mcp__web__web_browse", "mcp__web__web_scrape", "mcp__web__web_search",
                    "mcp__web__extract_youtube", "mcp__web__extract_transcript",
                    "mcp__web__fingerprint", "mcp__web__check_strategy",
                    "mcp__web__manage_session", "mcp__web__validate",
                    "mcp__web__cookie_status", "mcp__web__watch_url",
                ],
            ),
            "content-worker": AgentDefinition(
                description="Lightweight content analysis worker for parallel batch processing",
                prompt=(
                    "You are a content analysis worker. Use Bash + psql for DB access. "
                    "Load skills from /opt/agents/skills/content/ and /opt/agents/skills/data/. "
                    "Return structured analysis result."
                ),
                tools=["Bash", "Read", "Write", "Skill"],
            ),
        },
        setting_sources=["project"],
        thinking=ThinkingConfigEnabled(type="enabled", budget_tokens=10000),
        effort="high",
        max_turns=50,
        max_budget_usd=5.0,
        cwd=str(CONTENT_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
            "FIRECRAWL_API_KEY": os.environ.get("FIRECRAWL_API_KEY", ""),
        },
    )


# --- Content client lifecycle ---

async def start_content_client():
    from claude_agent_sdk import ClaudeSDKClient
    client = ClaudeSDKClient(options=build_content_options())
    await client.__aenter__()
    return client


async def stop_content_client():
    if clients.content_client:
        try:
            await clients.content_client.__aexit__(None, None, None)
        except Exception as e:
            logger.warning("Error stopping content client: %s", e)
        clients.content_client = None


async def restart_content_client():
    logger.info("Restarting content agent session")
    await stop_content_client()
    bump_session("content")
    reset_manifest_tokens("content", read_session_num("content"))
    clients.content_client = await start_content_client()
    clients.content_needs_restart = False


# --- Main loop ---

async def run_agent() -> None:
    from claude_agent_sdk import ClaudeSDKClient, ResultMessage

    bridge_server = create_bridge_server()

    while True:
        # Start content agent
        reset_manifest_tokens("content", read_session_num("content"))
        clients.content_client = await start_content_client()
        clients.content_needs_restart = False
        logger.info("Content agent started — session #%d", read_session_num("content"))

        # Start orchestrator
        orc_session = read_session_num("orc")
        reset_manifest_tokens("orc", orc_session)
        orc_needs_restart = False

        try:
            async with ClaudeSDKClient(options=build_orc_options(bridge_server)) as orc_client:
                logger.info("Orchestrator started — session #%d", orc_session)

                while not orc_needs_restart:
                    if clients.content_needs_restart:
                        await restart_content_client()

                    await orc_client.query("heartbeat")
                    async for msg in orc_client.receive_response():
                        if isinstance(msg, ResultMessage):
                            update_manifest_tokens("orc", msg.usage)
                            logger.info("Heartbeat done — turns=%d, cost=$%.4f", msg.num_turns, msg.total_cost_usd or 0)
                            if msg.result and "COMPACT_NOW" in msg.result:
                                orc_needs_restart = True

                    if not orc_needs_restart:
                        await asyncio.sleep(HEARTBEAT_INTERVAL)

        except Exception as e:
            logger.error("Session error: %s", e, exc_info=True)
            await asyncio.sleep(5)
        finally:
            await stop_content_client()

        if orc_needs_restart:
            bump_session("orc")
        else:
            await asyncio.sleep(5)


async def main() -> None:
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def handle_signal() -> None:
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_signal)

    agent_task = asyncio.create_task(run_agent())
    await stop_event.wait()
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass
    await stop_content_client()
    logger.info("Lifecycle manager stopped")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Verify syntax**

```bash
cd mcp-servers/agents && python3 -c "import ast; ast.parse(open('orchestrator/lifecycle.py').read()); print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/orchestrator/lifecycle.py
git commit -m "feat: lifecycle.py with both agents + @tool bridge"
```

---

## Chunk 2: Orchestrator System Prompt + HEARTBEAT.md

### Task 3: Orchestrator CLAUDE.md

**Files:**
- Create: `mcp-servers/agents/orchestrator/CLAUDE.md`

The Agent SDK reads `CLAUDE.md` from the agent's `cwd` automatically when `setting_sources=["project"]` is set — same as how CC reads CLAUDE.md. The agent gets CC's built-in system prompt (tool usage instructions, safety) PLUS the contents of this file.

- [ ] **Step 1: Write CLAUDE.md**

```markdown
# Orchestrator Agent — AI CoS System Coordinator

You are the **Orchestrator Agent** for Aakash Kumar's AI Chief of Staff system. You are a persistent, always-on coordinator running on a droplet, woken every 60 seconds by a heartbeat.

---

## 1. Identity

**Role:** Central coordinator. You don't analyze content or research — you manage system rhythm and delegate to specialist agents.

**You are persistent.** You keep full context within your session. You remember previous heartbeats. Use this to avoid redundant work.

**You are lean.** Complete each heartbeat quickly. Delegate all substantive work to Content Agent via `send_to_content_agent`.

---

## 2. Capabilities

| Tool | Purpose |
|------|---------|
| **Bash** | Shell commands, `psql $DATABASE_URL` for DB queries |
| **Read** | Read files |
| **Write** | Write files |
| **Edit** | Edit files |
| **Glob** | Find files |
| **Grep** | Search file contents |
| **mcp__bridge__send_to_content_agent** | Send prompt to Content Agent, get response |

You do NOT have Skill, Agent, or web tools. All analysis is delegated.

---

## 3. On Each Heartbeat

Read `HEARTBEAT.md` in your workspace and follow it exactly. Every heartbeat, every time.

---

## 4. Database Access

`psql $DATABASE_URL` via Bash. You only touch one table:

```sql
-- Read unprocessed inbox
SELECT id, type, content, metadata FROM cai_inbox
WHERE processed = FALSE ORDER BY created_at;

-- Mark processed after content agent acknowledges
UPDATE cai_inbox SET processed = TRUE, processed_at = NOW()
WHERE id IN (42, 43);
```

You do NOT write to any other table.

---

## 5. Sending Work to Content Agent

Use `send_to_content_agent`. Provide a clear prompt.

**Content pipeline trigger:**
> Run your content pipeline cycle. Check watch list for new content, analyze, score, and publish.

**Inbox relay (multiple messages):**
> Process these inbox messages:
> 1. [id=42, type=track_source] Add YouTube playlist https://youtube.com/playlist?list=PLxyz to watch list
> 2. [id=43, type=research_request] Research Composio competitive landscape

**Important:** Only mark inbox messages processed AFTER receiving the Content Agent's acknowledgment response.

---

## 6. Iteration Logging

After every heartbeat, write a one-line summary to `state/orc_last_log.txt`:

Examples:
- `no work: inbox empty, pipeline not due (last run 2m ago)`
- `relayed 2 inbox messages to content agent, triggered pipeline`
- `traces compaction: archived old file`
- `resumed from checkpoint, session #4`

The Stop hook reads this and appends it to the shared traces file.

---

## 7. Compaction Protocol

### Session Compaction
When your prompt includes "COMPACTION REQUIRED":
1. Read `state/CHECKPOINT_FORMAT.md`
2. Write checkpoint to `state/orc_checkpoint.md`
3. End response with exact word: **COMPACT_NOW**

### Session Restart
If `state/orc_checkpoint.md` exists at heartbeat start:
1. Read it — from your previous session
2. Absorb the state
3. Delete the file
4. Log: `resumed from checkpoint, session #N`

### Traces Compaction
Every 30 iterations (check `state/orc_iteration.txt`, if divisible by 30 and > 0):
1. Read `state/COMPACTION_PROTOCOL.md`
2. Follow the traces compaction procedure

---

## 8. Anti-Patterns

1. Never analyze content yourself — delegate to Content Agent
2. Never write to Postgres except cai_inbox.processed
3. Never skip the iteration log
4. Never ignore COMPACTION REQUIRED
5. Never batch heartbeats — one cycle per heartbeat
6. Never send empty prompts to Content Agent
7. Never mark inbox processed before acknowledgment
```

- [ ] **Step 2: Commit**

```bash
git add mcp-servers/agents/orchestrator/CLAUDE.md
git commit -m "feat: orchestrator CLAUDE.md — identity, heartbeat protocol, lifecycle"
```

### Task 4: HEARTBEAT.md

**Files:**
- Create: `mcp-servers/agents/orchestrator/HEARTBEAT.md`

- [ ] **Step 1: Write HEARTBEAT.md**

```markdown
# Heartbeat Checklist

Follow ALL steps every heartbeat.

---

## Step 1: Check for Checkpoint

```bash
ls state/orc_checkpoint.md 2>/dev/null
```

If exists: read it, absorb state, delete it, log `resumed from checkpoint, session #N`.

---

## Step 2: Inbox Check

```bash
psql $DATABASE_URL -t -A -c "SELECT id, type, content, metadata FROM cai_inbox WHERE processed = FALSE ORDER BY created_at"
```

If messages exist:
1. Combine into numbered prompt
2. Call `send_to_content_agent` with the combined prompt
3. On acknowledgment, mark all relayed IDs processed:
   ```bash
   psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE, processed_at = NOW() WHERE id IN (42, 43)"
   ```

If no messages: skip.

---

## Step 3: Content Pipeline Check

```bash
cat /opt/agents/content/state/last_pipeline_run.txt 2>/dev/null
```

If file missing OR timestamp >5 minutes old:
- Call `send_to_content_agent`: "Run your content pipeline cycle. Check watch list for new content, analyze, score, and publish."

If <5 minutes: skip.

**Note:** If you sent substantial inbox work in Step 2, you may skip the pipeline trigger this heartbeat — Content Agent handles both.

---

## Step 4: Traces Compaction Check

```bash
cat state/orc_iteration.txt
```

If divisible by 30 and > 0: read `state/COMPACTION_PROTOCOL.md` and follow it.

---

## Step 5: Iteration Log

Write one-line summary to `state/orc_last_log.txt`.
```

- [ ] **Step 2: Commit**

```bash
git add mcp-servers/agents/orchestrator/HEARTBEAT.md
git commit -m "feat: orchestrator HEARTBEAT.md checklist"
```

---

## Chunk 3: Content Agent Persistent Rewrite

### Task 5: Content agent hooks + settings.json

**Files:**
- Create: `mcp-servers/agents/content/.claude/hooks/stop-iteration-log.sh`
- Create: `mcp-servers/agents/content/.claude/hooks/prompt-manifest-check.sh`
- Create: `mcp-servers/agents/content/.claude/hooks/pre-compact-flush.sh`
- Create: `mcp-servers/agents/content/.claude/settings.json`

- [ ] **Step 1: Clone all three hooks from orchestrator**

Copy each hook from `orchestrator/.claude/hooks/` to `content/.claude/hooks/`. In each file, change ONLY this line:

```bash
# Change from:
AGENT="orc"
# Change to:
AGENT="content"
```

Everything else stays identical — the `AGENTS_ROOT` / `CWD` logic works for both because `dirname "$CWD"` resolves to `/opt/agents` from either workspace.

```bash
mkdir -p mcp-servers/agents/content/.claude/hooks
for hook in stop-iteration-log.sh prompt-manifest-check.sh pre-compact-flush.sh; do
  sed 's/AGENT="orc"/AGENT="content"/' \
    mcp-servers/agents/orchestrator/.claude/hooks/$hook \
    > mcp-servers/agents/content/.claude/hooks/$hook
  chmod +x mcp-servers/agents/content/.claude/hooks/$hook
done
```

- [ ] **Step 2: Write settings.json**

```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/stop-iteration-log.sh"
      }
    ],
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/prompt-manifest-check.sh"
      }
    ],
    "PreCompact": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-compact-flush.sh"
      }
    ]
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/content/.claude/
git commit -m "feat: content agent hooks + settings.json"
```

### Task 6: Content agent state directory

**Files:**
- Create: `mcp-servers/agents/content/state/content_session.txt`
- Create: `mcp-servers/agents/content/state/content_iteration.txt`
- Create: `mcp-servers/agents/content/state/last_pipeline_run.txt`
- Create: `mcp-servers/agents/content/state/CHECKPOINT_FORMAT.md`

- [ ] **Step 1: Create state files**

```bash
mkdir -p mcp-servers/agents/content/state
echo "1" > mcp-servers/agents/content/state/content_session.txt
echo "0" > mcp-servers/agents/content/state/content_iteration.txt
echo "" > mcp-servers/agents/content/state/last_pipeline_run.txt
```

- [ ] **Step 2: Write CHECKPOINT_FORMAT.md**

```markdown
# Checkpoint Format

When you receive COMPACTION REQUIRED, write to `state/content_checkpoint.md`:

```
# Checkpoint — $content | Session #{N} | Iteration {M}
*Written: YYYY-MM-DD HH:MM UTC*

## Current State
- Watch list: {N sources, M active}
- Last pipeline run: {timestamp}

## Recent Analysis Context
- Last content analyzed: {title/source}
- Thesis threads updated this session: {list}
- Actions created this session: {count, highest score}

## Pending Work
- {in-progress subagent tasks}
- {partially processed inbox messages}

## Recent Context (last 5 iterations)
- it {N}: {summary}
- ...

## Key Facts
- {thesis connections discovered this session}
- {watch list changes made}
- {error states or blocked sources}
```

After writing, end response with: **COMPACT_NOW**

## On Session Restart
If `state/content_checkpoint.md` exists:
1. Read it — from your previous session
2. Absorb the state
3. Delete the file
4. Log: `resumed from checkpoint, session #N`
```

- [ ] **Step 3: Commit**

```bash
git add mcp-servers/agents/content/state/
git commit -m "feat: content agent state directory + checkpoint format"
```

### Task 7: Rewrite content agent CLAUDE.md for persistent mode

**Files:**
- Rename + Rewrite: `mcp-servers/agents/content/system_prompt.md` → `mcp-servers/agents/content/CLAUDE.md`

The existing system_prompt.md (533 lines) is comprehensive. Most sections stay as-is. This task renames it to CLAUDE.md (so the SDK reads it automatically via `setting_sources=["project"]`) and makes targeted changes for persistent mode.

- [ ] **Step 1: Rename system_prompt.md → CLAUDE.md and read it**

```bash
mv mcp-servers/agents/content/system_prompt.md mcp-servers/agents/content/CLAUDE.md
cat mcp-servers/agents/content/CLAUDE.md
```

- [ ] **Step 2: Apply these changes**

**A. Replace the title + intro (lines 1-3):**

FROM:
```markdown
# Content Agent v2.2 — AI CoS Content Analyst

You are the **Content Agent** for Aakash Kumar's AI Chief of Staff system. You are an autonomous content analyst running on a droplet, triggered on scheduled cycles.
```

TO:
```markdown
# Content Agent — AI CoS Content Analyst

You are the **Content Agent** for Aakash Kumar's AI Chief of Staff system. You are a persistent, autonomous content analyst running on a droplet. You receive work prompts from the Orchestrator Agent.
```

**B. Replace Section 1 Identity paragraph 3 (line ~9):**

FROM:
```
**You are NOT an assistant.** You are an autonomous agent. You reason, decide, and act via your instructions, tools, and skills. There is no human in the loop during your execution.
```

TO:
```
**You are NOT an assistant.** You are an autonomous agent. You reason, decide, and act via your instructions, tools, and skills. There is no human in the loop during your execution.

**You are persistent.** You maintain full conversation context within your session. You remember what you've analyzed, what thesis threads you've updated, what inbox messages you've processed. Use this memory to avoid redundant work.

**You receive work from the Orchestrator.** The Orchestrator sends you prompts when there's work — content pipeline triggers and inbox message relays. You don't run on timers.
```

**C. Replace Section 4 "Scheduled Cycles" entirely (lines ~89-119):**

DELETE the entire "## 4. Scheduled Cycles" section (including subsections "Inbox Check" and "Content Cycle").

INSERT these three new sections in its place:

```markdown
---

## 4. How You Receive Work

The Orchestrator sends you prompts via the @tool bridge. Two types:

### Content Pipeline Trigger
When told "Run your content pipeline cycle":
1. Read watch list from `/opt/agents/data/watch_list.json`
2. For each active source, check for new content since `last_checked`
3. Fetch, analyze, score, and publish (see Analysis, Scoring, Publishing sections)
4. Write results to Postgres with `notion_synced = FALSE`
5. Update `last_checked` timestamps in watch list
6. Write current timestamp: `date -u +"%Y-%m-%dT%H:%M:%SZ" > state/last_pipeline_run.txt`

### Inbox Message Relay
When the Orchestrator relays inbox messages:
1. Parse the numbered message list
2. Process each by type (load skill: `/opt/agents/skills/content/inbox-handling.md`):
   - **track_source** — Add/modify source in watch list
   - **remove_source** — Remove from watch list
   - **research_request** — Spawn web-researcher subagent
   - **question** — Look up answer, write to notifications table
   - **priority_change** — Update watch list priorities
3. Handle failures gracefully — log errors per message but continue with others

---

## 5. Acknowledgment Protocol

**Every response MUST end with a structured ACK.** The Orchestrator uses this to confirm work completion and mark inbox items processed.

Format:
```
ACK: [brief summary]
- [item 1]
- [item 2]
```

Examples:

Content pipeline:
```
ACK: Pipeline completed. 3 videos analyzed, 2 digests published, 1 action (score 7.8).
```

Inbox relay:
```
ACK: Processed 2 inbox messages.
- id=42 (track_source): Added YouTube playlist to watch list
- id=43 (research_request): Spawned web-researcher for competitive analysis
```

Error case:
```
ACK: Processed 2 of 3 messages.
- id=42: Added source
- id=43: Spawned researcher
- id=44: FAILED — invalid URL
```

---

## 6. State Tracking & Lifecycle

### State Files
| File | When to Write |
|------|---------------|
| `state/last_pipeline_run.txt` | After every content pipeline cycle |
| `state/content_last_log.txt` | After every prompt you process |

### Iteration Logging
After every prompt, write one-line summary to `state/content_last_log.txt`. The Stop hook appends it to shared traces.

### Session Compaction
When prompt includes "COMPACTION REQUIRED":
1. Read `state/CHECKPOINT_FORMAT.md`
2. Write checkpoint to `state/content_checkpoint.md`
3. End response with: **COMPACT_NOW**

### Session Restart
If `state/content_checkpoint.md` exists:
1. Read it, absorb state, delete it
2. Log: `resumed from checkpoint, session #N`
```

**D. Renumber remaining sections:**
- Old §5 Watch List → §7
- Old §6 Analysis Framework → §8
- Old §7 Scoring → §9
- Old §8 Publishing → §10
- Old §9 Web Access Strategy → §11
- Old §10 Three Classes of Work → §12
- Old §11 Conviction Guardrail → §13
- Old §12 Notifications → §14
- Old §13 Anti-Patterns → §15
- Old §14 DigestData JSON Schema → §16
- Old §15 Quality Bars → §17
- Old §16 Error Handling → §18

**E. Add to Anti-Patterns section (§15):**

Append these to the existing list:
```
11. **Never skip the ACK** — Every response must include structured acknowledgment.
12. **Never skip state tracking** — Always write last_pipeline_run.txt and content_last_log.txt.
13. **Never ignore COMPACTION REQUIRED** — Write checkpoint + COMPACT_NOW immediately.
14. **Never re-analyze without checking** — You're persistent. Check memory + Postgres before re-processing.
```

- [ ] **Step 3: Verify the rewritten file has all sections 1-18**

```bash
grep "^## " mcp-servers/agents/content/CLAUDE.md | head -20
```

Expected: 18 numbered sections.

- [ ] **Step 4: Commit**

```bash
git add mcp-servers/agents/content/CLAUDE.md
git commit -m "feat: content agent CLAUDE.md — persistent mode with ACK protocol + lifecycle"
```

---

## Chunk 4: Deploy + Cleanup

### Task 8: Update deploy.sh

**Files:**
- Modify: `mcp-servers/agents/deploy.sh`

- [ ] **Step 1: Add rsync exclusions for state/ and traces/ runtime data**

In the rsync command (step 1), add these excludes so deploy doesn't wipe runtime state:

```bash
--exclude='*/state/' --exclude='traces/'
```

- [ ] **Step 2: Add content agent hooks + state to runtime directory creation (step 6)**

```bash
ssh root@${DROPLET} "mkdir -p ${REMOTE_DIR}/traces/archive ${REMOTE_DIR}/orchestrator/state ${REMOTE_DIR}/content/state ${REMOTE_DIR}/content/.claude/hooks"
```

- [ ] **Step 3: Add orchestrator to systemd install + restart**

In step 7 (systemd units), add:
```bash
cp ${REMOTE_DIR}/infra/orchestrator.service /etc/systemd/system/
```

In the enable line, add `orchestrator`.

In step 8 (restart), add after content-agent restart:
```bash
systemctl restart orchestrator
```

**Remove content-agent from restart** — it's now managed by lifecycle.py (orchestrator service), not its own systemd unit.

In step 9 (health check agents loop), replace `content-agent` with `orchestrator`:
```bash
for svc in orchestrator; do
```

- [ ] **Step 4: Commit**

```bash
git add mcp-servers/agents/deploy.sh
git commit -m "feat: deploy.sh — orchestrator service, protect state/traces"
```

### Task 9: Remove old content/runner.py

**Files:**
- Delete: `mcp-servers/agents/content/runner.py`

- [ ] **Step 1: Delete the old ephemeral runner**

```bash
rm mcp-servers/agents/content/runner.py
```

- [ ] **Step 2: Remove content-agent.service from infra/**

The content agent no longer has its own systemd service — lifecycle.py manages it. Remove or disable:

```bash
rm mcp-servers/agents/infra/content-agent.service
```

- [ ] **Step 3: Commit**

```bash
git add -u mcp-servers/agents/content/runner.py mcp-servers/agents/infra/content-agent.service
git commit -m "cleanup: remove ephemeral content runner + service (now managed by lifecycle.py)"
```

---

## Dependency Map

```
Task 1 (manifest) ─────────────────────────► Task 2 (lifecycle.py)
                                                │
Task 3 (orc system prompt) ◄───────────────────┤
Task 4 (HEARTBEAT.md) ◄────────────────────────┘

Task 5 (content hooks) ── standalone
Task 6 (content state) ── standalone
Task 7 (content system prompt) ── standalone

Task 8 (deploy.sh) ◄── Tasks 2, 3, 7, 9
Task 9 (cleanup) ── standalone
```

Parallelizable: Tasks 3+4 (orc prompts), Tasks 5+6+7 (content agent), Task 1 (manifest). All independent.
Task 2 (lifecycle.py) depends on nothing in this plan but should be written after Tasks 3+7 exist.
Tasks 8+9 are last.

---

## Verification Checklist

- [ ] `lifecycle.py` syntax check passes
- [ ] `orchestrator/CLAUDE.md` exists with sections 1-8 (SDK reads automatically)
- [ ] `orchestrator/HEARTBEAT.md` exists with steps 1-5
- [ ] `content/.claude/hooks/` has 3 executable scripts with AGENT="content"
- [ ] `content/.claude/settings.json` registers all 3 hooks
- [ ] `content/state/` has session, iteration, last_pipeline_run, CHECKPOINT_FORMAT.md
- [ ] `content/CLAUDE.md` has 18 sections, includes ACK protocol + state tracking + compaction
- [ ] `content/runner.py` deleted
- [ ] `infra/content-agent.service` deleted
- [ ] `deploy.sh` installs orchestrator service, protects state/traces from rsync
- [ ] `traces/manifest.json` has both "orc" and "content" entries
