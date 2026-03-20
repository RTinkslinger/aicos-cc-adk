# Datum Agent — lifecycle.py Integration Plan
*Created: 2026-03-20*

This plan describes how to integrate the Datum Agent as the third managed ClaudeSDKClient in `mcp-servers/agents/orchestrator/lifecycle.py`. It follows the exact patterns established by the Content Agent.

---

## 1. Scope of Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `orchestrator/lifecycle.py` | Modify | Add Datum Agent state, bridge tool, options builder, lifecycle hooks |
| `orchestrator/CLAUDE.md` | Modify | Add `send_to_datum_agent` to capabilities table |
| `orchestrator/HEARTBEAT.md` | Modify | Add datum_* inbox routing rules |

---

## 2. ClientState Additions

Add three new fields to the `ClientState` class, mirroring the content agent pattern:

```python
class ClientState:
    content_client: Any = None
    content_needs_restart: bool = False
    content_busy: bool = False

    datum_client: Any = None           # NEW
    datum_needs_restart: bool = False   # NEW
    datum_busy: bool = False            # NEW
```

**Location:** Line ~41-44, immediately after the content fields.

---

## 3. Constants

Add workspace and log path constants alongside the existing ones:

```python
DATUM_WORKSPACE = AGENTS_ROOT / "datum"
DATUM_LIVE_LOG = DATUM_WORKSPACE / "live.log"
```

**Location:** Line ~32, after `CONTENT_LIVE_LOG`.

---

## 4. Bridge Tool: send_to_datum_agent

Add a second `@tool` inside `create_bridge_server()`, following the exact same pattern as `send_to_content_agent`.

```python
async def _read_datum_response():
    """Background task: read datum agent response, track tokens, detect compaction."""
    try:
        async for msg in clients.datum_client.receive_response():
            if isinstance(msg, AssistantMessage):
                _log_assistant_message(DATUM_LIVE_LOG, msg)
            elif isinstance(msg, ResultMessage):
                update_manifest_tokens("datum", msg.usage)
                _log_result_message(DATUM_LIVE_LOG, msg)
                logger.info(
                    "Bridge: datum done — turns=%d, cost=$%.4f",
                    msg.num_turns,
                    msg.total_cost_usd or 0,
                )
                if msg.result and "COMPACT_NOW" in msg.result:
                    clients.datum_needs_restart = True
                    logger.info("Bridge: datum agent signaled COMPACT_NOW")
    except Exception as e:
        logger.error("Bridge: error reading datum response: %s", e)
    finally:
        clients.datum_busy = False
        _live_log(DATUM_LIVE_LOG, "--- idle (ready for next prompt) ---")

@tool(
    "send_to_datum_agent",
    "Send entity data to the persistent Datum Agent for dedup, enrichment, and storage. "
    "Returns immediately — datum agent works in background. "
    "If datum agent is busy, returns a busy message.",
    {"prompt": str},
)
async def send_to_datum_agent(args: dict[str, Any]) -> dict[str, Any]:
    if clients.datum_client is None:
        return {
            "content": [{"type": "text", "text": "Error: Datum agent not connected"}],
            "is_error": True,
        }

    if clients.datum_busy:
        return {
            "content": [{"type": "text", "text": "Datum agent is still processing previous work. Will check again next heartbeat."}],
        }

    prompt = args["prompt"]
    logger.info("Bridge: forwarding to datum agent (%d chars)", len(prompt))
    _live_log(DATUM_LIVE_LOG, f">>> PROMPT: {prompt[:200]}")
    clients.datum_busy = True
    try:
        await clients.datum_client.query(prompt)
        asyncio.create_task(_read_datum_response())
    except Exception as e:
        clients.datum_busy = False
        logger.error("Bridge: failed to send to datum agent: %s", e)
        return {
            "content": [{"type": "text", "text": f"Error sending to datum agent: {e}"}],
            "is_error": True,
        }

    return {
        "content": [{"type": "text", "text": "Prompt sent to datum agent. Working in background."}],
    }
```

**Key difference from content:** The `_read_datum_response` background task reads from `clients.datum_client` and writes to `DATUM_LIVE_LOG`.

**Bridge server registration:** The `create_sdk_mcp_server` call gains the second tool:
```python
return create_sdk_mcp_server(
    name="bridge", version="1.0.0",
    tools=[send_to_content_agent, send_to_datum_agent]
)
```

---

## 5. Agent Options Builder: build_datum_options

New function, following `build_content_options` pattern but with Datum-specific parameters:

```python
def build_datum_options():
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ThinkingConfigEnabled

    datum_tool_hook = _make_tool_hook(DATUM_LIVE_LOG)

    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill",
            "mcp__web__web_browse", "mcp__web__web_scrape", "mcp__web__web_search",
            "mcp__web__fingerprint", "mcp__web__check_strategy",
            "mcp__web__manage_session", "mcp__web__validate",
        ],
        mcp_servers={"web": {"type": "http", "url": "http://localhost:8001/mcp"}},
        hooks={"PostToolUse": [HookMatcher(hooks=[datum_tool_hook])]},
        setting_sources=["project"],
        thinking=ThinkingConfigEnabled(type="enabled", budget_tokens=5000),
        effort="high",
        max_turns=30,
        max_budget_usd=2.0,
        cwd=str(DATUM_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        },
    )
```

**Differences from Content Agent options:**
- No `Agent` tool or subagent definitions (datum does not spawn subagents)
- No YouTube extraction tools (not needed for entity processing)
- Lower `max_budget_usd` (2.0 vs 5.0) — entity ops are shorter
- Lower `max_turns` (30 vs 50) — simpler processing flow
- Lower thinking budget (5000 vs 10000) — dedup decisions are focused
- No `FIRECRAWL_API_KEY` in env (web tools MCP handles API keys internally)

---

## 6. Datum Client Lifecycle Functions

Mirror the content client lifecycle exactly:

```python
async def start_datum_client():
    from claude_agent_sdk import ClaudeSDKClient
    client = ClaudeSDKClient(options=build_datum_options())
    await client.__aenter__()
    return client

async def stop_datum_client():
    if clients.datum_client:
        try:
            await clients.datum_client.__aexit__(None, None, None)
        except Exception as e:
            logger.warning("Error stopping datum client: %s", e)
        clients.datum_client = None

async def restart_datum_client():
    logger.info("Restarting datum agent session")
    await stop_datum_client()
    bump_session("datum")
    reset_manifest_tokens("datum", read_session_num("datum"))
    clients.datum_client = await start_datum_client()
    clients.datum_needs_restart = False
```

---

## 7. _state_dir Helper Update

The `_state_dir` function needs a third case for datum:

```python
def _state_dir(agent: str) -> Path:
    if agent == "orc":
        return ORC_WORKSPACE / "state"
    elif agent == "content":
        return CONTENT_WORKSPACE / "state"
    elif agent == "datum":
        return DATUM_WORKSPACE / "state"
    else:
        raise ValueError(f"Unknown agent: {agent}")
```

---

## 8. run_agent() Modifications

### 8a. Start Datum Client (after Content Client start)

```python
# Start datum agent
reset_manifest_tokens("datum", read_session_num("datum"))
clients.datum_client = await start_datum_client()
clients.datum_needs_restart = False
_live_log(DATUM_LIVE_LOG, f"=== Datum agent started — session #{read_session_num('datum')} ===")
logger.info("Datum agent started — session #%d", read_session_num("datum"))
```

### 8b. Compaction Check in Heartbeat Loop

Add datum compaction check alongside content:

```python
if clients.content_needs_restart:
    await restart_content_client()
if clients.datum_needs_restart:      # NEW
    await restart_datum_client()     # NEW
```

### 8c. Stop Datum Client in Finally Block

```python
finally:
    await stop_content_client()
    await stop_datum_client()        # NEW
```

### 8d. Stop Datum in main() Shutdown

```python
await stop_content_client()
await stop_datum_client()            # NEW
```

---

## 9. Orchestrator allowed_tools Update

Add the datum bridge tool to the orchestrator's allowed_tools:

```python
allowed_tools=[
    "Bash", "Read", "Write", "Edit", "Glob", "Grep",
    "mcp__bridge__send_to_content_agent",
    "mcp__bridge__send_to_datum_agent",    # NEW
],
```

---

## 10. Orchestrator CLAUDE.md Update

Add datum bridge to the capabilities table:

```markdown
| **mcp__bridge__send_to_datum_agent** | Send entity data to Datum Agent |
```

---

## 11. Orchestrator HEARTBEAT.md Update

Add routing rules for datum_* inbox message types:

```markdown
## Inbox Routing

For each unprocessed inbox message, route by type:

| Type Pattern | Route To | Bridge Tool |
|-------------|----------|-------------|
| datum_person | Datum Agent | send_to_datum_agent |
| datum_company | Datum Agent | send_to_datum_agent |
| datum_entity | Datum Agent | send_to_datum_agent |
| datum_image | Datum Agent | send_to_datum_agent |
| datum_meeting_entities | Datum Agent | send_to_datum_agent |
| track_source, research_request, general, ... | Content Agent | send_to_content_agent |

### Datum Batching Rule
If there are 3+ datum_* messages in the inbox, batch them into a single prompt
to the Datum Agent rather than sending one-by-one. Format:

> Process entity batch (3 inbox messages):
> 1. [id=42, type=datum_person] Rahul Sharma, CTO at Composio
> 2. [id=43, type=datum_company] Track Composio - AI agent tooling
> 3. [id=44, type=datum_entity] Entity batch from content pipeline
```

---

## 12. Key Design Decision: On-Demand Activation

The Datum Agent differs from the Content Agent in one important way:

**Content Agent** is both heartbeat-triggered (pipeline cycle) AND inbox-triggered.
**Datum Agent** is inbox-triggered ONLY. It has no heartbeat/pipeline cycle.

This means:
- The Orchestrator does NOT send "heartbeat" prompts to the Datum Agent
- The Datum Agent only wakes when the Orchestrator forwards datum_* inbox messages
- Between messages, the Datum Agent is idle (no token cost)
- The `has_work()` pre-check already covers this — datum_* inbox messages increment the unprocessed count

---

## 13. Manifest Tracking

The manifest.json gains a "datum" entry alongside "orc" and "content":

```json
{
  "orc": { "session": 1, "input_tokens": 0, "output_tokens": 0, "last_updated": null },
  "content": { "session": 1, "input_tokens": 0, "output_tokens": 0, "last_updated": null },
  "datum": { "session": 1, "input_tokens": 0, "output_tokens": 0, "last_updated": null }
}
```

No code change needed — `update_manifest_tokens("datum", ...)` auto-creates the entry.

---

## 14. Deployment Impact

### deploy.sh
The `deploy.sh` rsync already syncs the entire `mcp-servers/agents/` directory. No change needed — the `datum/` directory will be included automatically.

### systemd
No new service needed. The Datum Agent runs inside the existing `lifecycle.py` process, managed by the orchestrator service.

### Environment
No new env vars needed. The Datum Agent uses the same `DATABASE_URL` and `ANTHROPIC_API_KEY` as the other agents.

---

## 15. Implementation Order

1. Add constants (DATUM_WORKSPACE, DATUM_LIVE_LOG)
2. Add ClientState fields (datum_client, datum_needs_restart, datum_busy)
3. Update _state_dir helper
4. Add build_datum_options function
5. Add start_datum_client, stop_datum_client, restart_datum_client
6. Add send_to_datum_agent @tool + _read_datum_response in create_bridge_server
7. Update create_sdk_mcp_server tools list
8. Update build_orc_options allowed_tools
9. Update run_agent: start datum, compaction check, stop datum
10. Update main: stop datum on shutdown
11. Update orchestrator CLAUDE.md: add datum bridge capability
12. Update HEARTBEAT.md: add datum routing rules

---

## 16. Testing Plan

| Test | Expected Result |
|------|----------------|
| Send datum_person inbox message | Orchestrator routes to Datum Agent, entity created in network table |
| Send duplicate entity | Dedup detects match, merges instead of creating duplicate |
| Send while datum is busy | Orchestrator receives "busy" message, retries next heartbeat |
| Datum agent hits 100K tokens | Compaction hook fires, agent writes checkpoint, COMPACT_NOW triggers restart |
| Datum agent crashes | `datum_client` becomes None, next `send_to_datum_agent` returns error, orchestrator logs warning |
| Batch of 5 datum_* messages | Orchestrator batches them, Datum Agent processes sequentially |
