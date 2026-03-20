# Cindy Lifecycle Integration Plan
*Created: 2026-03-20*

Plan for adding Cindy as the 5th managed ClaudeSDKClient in `lifecycle.py`.
This document describes what needs to change — it does NOT implement the changes.

---

## 1. Changes to lifecycle.py

### 1.1 New Constants

```python
CINDY_WORKSPACE = AGENTS_ROOT / "cindy"
CINDY_LIVE_LOG = CINDY_WORKSPACE / "live.log"
```

### 1.2 ClientState — Add Cindy Fields

```python
class ClientState:
    content_client: Any = None
    content_needs_restart: bool = False
    content_busy: bool = False

    datum_client: Any = None
    datum_needs_restart: bool = False
    datum_busy: bool = False

    megamind_client: Any = None
    megamind_needs_restart: bool = False
    megamind_busy: bool = False

    cindy_client: Any = None           # NEW
    cindy_needs_restart: bool = False   # NEW
    cindy_busy: bool = False            # NEW
```

### 1.3 New `_state_dir` Entry

```python
def _state_dir(agent: str) -> Path:
    ...
    elif agent == "cindy":
        return CINDY_WORKSPACE / "state"
    ...
```

### 1.4 New `build_cindy_options()` Function

```python
def build_cindy_options():
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ThinkingConfigEnabled

    cindy_tool_hook = _make_tool_hook(CINDY_LIVE_LOG)

    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill",
        ],
        hooks={"PostToolUse": [HookMatcher(hooks=[cindy_tool_hook])]},
        setting_sources=["project"],
        thinking=ThinkingConfigEnabled(type="enabled", budget_tokens=8000),
        effort="high",
        max_turns=35,
        max_budget_usd=3.0,
        cwd=str(CINDY_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        },
    )
```

**Budget rationale:**
- `max_budget_usd=3.0`: Higher than Datum (2.0) — Granola transcript analysis is token-heavy.
  Lower than Content Agent (5.0) — no web fetching. Same as Megamind (3.0).
- `max_turns=35`: Granola: 10-15 turns. WhatsApp batch: 15-25 turns. Email: 5-10 turns.
  Calendar: 5-8 turns.
- `thinking=8000`: IDS signal extraction benefits from extended thinking. Higher than Datum
  (5000), lower than Content/Megamind (10000).
- No web tools. Cindy reasons over interaction data. Web enrichment delegated to Datum Agent.

### 1.5 New Cindy Client Lifecycle Functions

Follow exact pattern of content/datum/megamind:

```python
async def start_cindy_client():
    from claude_agent_sdk import ClaudeSDKClient
    client = ClaudeSDKClient(options=build_cindy_options())
    await client.__aenter__()
    return client

async def stop_cindy_client():
    if clients.cindy_client:
        try:
            await clients.cindy_client.__aexit__(None, None, None)
        except Exception as e:
            logger.warning("Error stopping cindy client: %s", e)
        clients.cindy_client = None

async def restart_cindy_client():
    logger.info("Restarting cindy agent session")
    await stop_cindy_client()
    bump_session("cindy")
    reset_manifest_tokens("cindy", read_session_num("cindy"))
    clients.cindy_client = await start_cindy_client()
    clients.cindy_needs_restart = False
```

### 1.6 New Bridge Tool: `send_to_cindy_agent`

```python
async def _read_cindy_response():
    """Background task: read cindy agent response, track tokens, detect compaction."""
    try:
        async for msg in clients.cindy_client.receive_response():
            if isinstance(msg, AssistantMessage):
                _log_assistant_message(CINDY_LIVE_LOG, msg)
            elif isinstance(msg, ResultMessage):
                update_manifest_tokens("cindy", msg.usage)
                _log_result_message(CINDY_LIVE_LOG, msg)
                logger.info(
                    "Bridge: cindy done — turns=%d, cost=$%.4f",
                    msg.num_turns,
                    msg.total_cost_usd or 0,
                )
                if msg.result and "COMPACT_NOW" in msg.result:
                    clients.cindy_needs_restart = True
                    logger.info("Bridge: cindy agent signaled COMPACT_NOW")
    except Exception as e:
        logger.error("Bridge: error reading cindy response: %s", e)
    finally:
        clients.cindy_busy = False
        _live_log(CINDY_LIVE_LOG, "--- idle (ready for next prompt) ---")

@tool(
    "send_to_cindy_agent",
    "Send communication data to the persistent Cindy Agent for processing. "
    "Handles email, WhatsApp, Granola, and Calendar signals. "
    "Returns immediately — Cindy works in background. "
    "If Cindy is busy, returns a busy message.",
    {"prompt": str},
)
async def send_to_cindy_agent(args: dict[str, Any]) -> dict[str, Any]:
    # Same pattern as send_to_content_agent / send_to_datum_agent / send_to_megamind_agent
    ...
```

### 1.7 Update `create_bridge_server` Return

```python
return create_sdk_mcp_server(
    name="bridge", version="1.0.0",
    tools=[
        send_to_content_agent,
        send_to_datum_agent,
        send_to_megamind_agent,
        send_to_cindy_agent,      # NEW
    ]
)
```

### 1.8 Update `build_orc_options` allowed_tools

```python
allowed_tools=[
    "Bash", "Read", "Write", "Edit", "Glob", "Grep",
    "mcp__bridge__send_to_content_agent",
    "mcp__bridge__send_to_datum_agent",
    "mcp__bridge__send_to_megamind_agent",
    "mcp__bridge__send_to_cindy_agent",       # NEW
],
```

### 1.9 Update `run_agent()` Main Loop

Add Cindy startup/shutdown alongside other agents:

```python
# Start cindy agent (after megamind, before orchestrator)
reset_manifest_tokens("cindy", read_session_num("cindy"))
clients.cindy_client = await start_cindy_client()
clients.cindy_needs_restart = False
_live_log(CINDY_LIVE_LOG, f"=== Cindy started — session #{read_session_num('cindy')} ===")
logger.info("Cindy started — session #%d", read_session_num("cindy"))
```

Add to heartbeat loop:
```python
if clients.cindy_needs_restart:
    await restart_cindy_client()
```

Add to finally block:
```python
finally:
    await stop_content_client()
    await stop_datum_client()
    await stop_megamind_client()
    await stop_cindy_client()       # NEW
```

---

## 2. Changes to Orchestrator CLAUDE.md

### 2.1 Add to Capabilities Table

```markdown
| **mcp__bridge__send_to_cindy_agent** | Send communication data to Cindy Agent (email, WhatsApp, Granola, Calendar) |
```

### 2.2 Add Section 5d: Sending Work to Cindy Agent

Follows the exact pattern of 5b (Datum) and 5c (Megamind):
- Fire-and-forget pattern
- Mark inbox messages processed only after "Prompt sent" confirmation
- If busy, skip and retry next heartbeat

### 2.3 Update Anti-Patterns

Add:
- Never send `cindy_*` messages to Content Agent or Datum Agent — route to Cindy Agent
- Never send non-cindy messages to Cindy Agent — she only processes communication data
- Route `cindy_signal` messages to Megamind (not Cindy — these are outbound signals from Cindy)

---

## 3. Changes to Orchestrator HEARTBEAT.md

### 3.1 New Step: Cindy Communication Processing

Insert between existing routing steps:

```markdown
## Step 2.8: Cindy Communication Processing

### Check for Cindy inbox messages
```bash
psql $DATABASE_URL -t -A -c "
  SELECT id, type, content
  FROM cai_inbox
  WHERE type LIKE 'cindy_%'
    AND type != 'cindy_signal'
    AND processed = FALSE
  ORDER BY created_at
  LIMIT 5"
```

If results: batch by type, send to Cindy via `send_to_cindy_agent`.
If Cindy busy: skip, retry next heartbeat.

### Route Cindy signals to Megamind
```bash
psql $DATABASE_URL -t -A -c "
  SELECT id, content, metadata
  FROM cai_inbox
  WHERE type = 'cindy_signal'
    AND processed = FALSE
  ORDER BY created_at
  LIMIT 3"
```

If results: route to Megamind for strategic assessment.
```

### 3.2 New Scheduled Triggers

```markdown
### Granola poll (every 30 min)
Check state/last_granola_poll.txt. If 30+ min since last poll:
  Write cindy_granola_poll to cai_inbox.
  Update state/last_granola_poll.txt.

### Calendar poll (every 30 min)
Same pattern with state/last_calendar_poll.txt and cindy_calendar_poll.

### Context gap detection (daily at 8 PM IST)
Write cindy_gap_scan to cai_inbox. Cindy scans past 24h calendar events for gaps.
```

---

## 4. Message Routing Summary (Updated)

```
cai_inbox.type          → Route to
-------------------------------------------
datum_*                 → Datum Agent
content_*               → Content Agent
strategy_*              → Megamind Agent
cindy_*                 → Cindy Agent (EXCEPT cindy_signal)
cindy_signal            → Megamind Agent
general / research      → Content Agent (default)
```

---

## 5. Deploy Sequence

1. **Deploy cindy/ workspace** via `deploy.sh` (syncs to droplet)
2. **Update lifecycle.py** with all changes above
3. **Update Orchestrator CLAUDE.md + HEARTBEAT.md** with new routing
4. **Restart orchestrator service**: `systemctl restart orchestrator`
5. **Verify**: Check live logs for Cindy startup confirmation
6. **Test**: Insert test `cindy_calendar` message in cai_inbox, verify Cindy processes it

---

## 6. Rollback Plan

If Cindy causes issues after deployment:
1. Comment out Cindy startup in `run_agent()` (4 lines)
2. Comment out `send_to_cindy_agent` in bridge tools list
3. Restart orchestrator
4. Cindy inbox messages will accumulate unprocessed — no data loss
5. Fix and redeploy when ready

---

## 7. Monitoring

### Live Logs
```bash
ssh -t root@aicos-droplet tail -f /opt/agents/cindy/live.log
# or
ssh -t root@aicos-droplet /opt/agents/live-cindy.sh  # after creating helper
```

### Health Check
```bash
# Check Cindy is processing
psql $DATABASE_URL -c "SELECT COUNT(*) FROM interactions WHERE created_at > NOW() - INTERVAL '24 hours';"

# Check for unprocessed Cindy messages (should be 0 if healthy)
psql $DATABASE_URL -c "SELECT COUNT(*) FROM cai_inbox WHERE type LIKE 'cindy_%' AND type != 'cindy_signal' AND processed = FALSE;"

# Check context gaps created
psql $DATABASE_URL -c "SELECT status, COUNT(*) FROM context_gaps GROUP BY status;"
```
