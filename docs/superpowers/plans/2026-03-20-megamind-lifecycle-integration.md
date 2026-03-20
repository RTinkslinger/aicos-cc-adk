# Megamind Lifecycle Integration Plan
*Created: 2026-03-20*

Plan for integrating Megamind into `lifecycle.py` — the lifecycle manager that runs on the
droplet and manages all persistent agent sessions.

**This is a plan document. No code changes here. Implementation is Phase 2.**

---

## 1. Current State

`lifecycle.py` manages 3 agents:
- **Orchestrator** — heartbeat-driven coordinator (ClaudeSDKClient, `context` manager)
- **Content Agent** — content analysis and pipeline (ClaudeSDKClient, fire-and-forget via bridge)
- **Datum Agent** — entity ingestion and enrichment (ClaudeSDKClient, fire-and-forget via bridge)

The Orchestrator communicates with Content and Datum via `@tool` bridge tools:
- `send_to_content_agent` — sends prompt, returns immediately, reads response in background
- `send_to_datum_agent` — same pattern

---

## 2. Changes Required in lifecycle.py

### 2.1 New Constants

```python
MEGAMIND_WORKSPACE = AGENTS_ROOT / "megamind"
MEGAMIND_LIVE_LOG = MEGAMIND_WORKSPACE / "live.log"
```

### 2.2 ClientState Extension

Add 3 fields to the `ClientState` class:

```python
class ClientState:
    # ... existing content and datum fields ...

    megamind_client: Any = None
    megamind_needs_restart: bool = False
    megamind_busy: bool = False
```

### 2.3 New Bridge Tool: send_to_megamind_agent

Inside `create_bridge_server()`, add a third tool following the exact pattern of
`send_to_content_agent` and `send_to_datum_agent`:

1. **Background reader** `_read_megamind_response()`:
   - Reads AssistantMessage and ResultMessage from the megamind client
   - Logs to MEGAMIND_LIVE_LOG
   - Tracks tokens via `update_manifest_tokens("megamind", ...)`
   - Detects COMPACT_NOW -> sets `clients.megamind_needs_restart = True`
   - Sets `clients.megamind_busy = False` in finally block

2. **Bridge tool** `send_to_megamind_agent`:
   - Description: "Send strategic work to the persistent Megamind Agent for depth grading,
     cascade processing, or strategic assessment. Returns immediately — works in background."
   - Input: `{"prompt": str}`
   - Checks `clients.megamind_client is None` -> error
   - Checks `clients.megamind_busy` -> busy message
   - Calls `await clients.megamind_client.query(prompt)`
   - Spawns `asyncio.create_task(_read_megamind_response())`
   - Returns immediately with "Prompt sent to megamind agent."

3. **Update tool list** in `create_sdk_mcp_server`:
   ```python
   tools=[send_to_content_agent, send_to_datum_agent, send_to_megamind_agent]
   ```

### 2.4 New Options Builder: build_megamind_options()

```python
def build_megamind_options():
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ThinkingConfigEnabled

    megamind_tool_hook = _make_tool_hook(MEGAMIND_LIVE_LOG)

    return ClaudeAgentOptions(
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        permission_mode="dontAsk",
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill",
        ],
        hooks={"PostToolUse": [HookMatcher(hooks=[megamind_tool_hook])]},
        setting_sources=["project"],
        thinking=ThinkingConfigEnabled(type="enabled", budget_tokens=10000),
        effort="high",
        max_turns=25,
        max_budget_usd=3.0,
        cwd=str(MEGAMIND_WORKSPACE),
        env={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        },
    )
```

Key differences from other agents:
- No web tools (Megamind reasons over structured data, not raw content)
- No Agent tool (no subagent delegation)
- No MCP servers (no web-tools-mcp connection)
- Thinking budget: 10000 tokens (same as Content Agent — strategic reasoning benefits from extended thinking)
- Max turns: 25 (depth grading: 5-8, cascade: 10-15, assessment: 15-20)
- Max budget: $3.00 (higher than Datum, lower than Content)

### 2.5 Megamind Client Lifecycle Functions

Add 3 functions following the Datum Agent pattern:

```python
async def start_megamind_client():
    from claude_agent_sdk import ClaudeSDKClient
    client = ClaudeSDKClient(options=build_megamind_options())
    await client.__aenter__()
    return client

async def stop_megamind_client():
    if clients.megamind_client:
        try:
            await clients.megamind_client.__aexit__(None, None, None)
        except Exception as e:
            logger.warning("Error stopping megamind client: %s", e)
        clients.megamind_client = None

async def restart_megamind_client():
    logger.info("Restarting megamind agent session")
    await stop_megamind_client()
    bump_session("megamind")
    reset_manifest_tokens("megamind", read_session_num("megamind"))
    clients.megamind_client = await start_megamind_client()
    clients.megamind_needs_restart = False
```

### 2.6 _state_dir Update

Add megamind case to the `_state_dir` helper:

```python
def _state_dir(agent: str) -> Path:
    if agent == "orc":
        return ORC_WORKSPACE / "state"
    elif agent == "content":
        return CONTENT_WORKSPACE / "state"
    elif agent == "datum":
        return DATUM_WORKSPACE / "state"
    elif agent == "megamind":
        return MEGAMIND_WORKSPACE / "state"
    else:
        raise ValueError(f"Unknown agent: {agent}")
```

### 2.7 run_agent() Main Loop Updates

In the main loop, add Megamind startup, restart check, and cleanup:

**Startup (after Datum Agent start):**
```python
# Start megamind agent
reset_manifest_tokens("megamind", read_session_num("megamind"))
clients.megamind_client = await start_megamind_client()
clients.megamind_needs_restart = False
_live_log(MEGAMIND_LIVE_LOG, f"=== Megamind started — session #{read_session_num('megamind')} ===")
logger.info("Megamind started — session #%d", read_session_num("megamind"))
```

**Restart check (in heartbeat loop, after datum restart check):**
```python
if clients.megamind_needs_restart:
    await restart_megamind_client()
```

**Cleanup (in finally block):**
```python
finally:
    await stop_content_client()
    await stop_datum_client()
    await stop_megamind_client()
```

Also add `await stop_megamind_client()` to the `main()` function cleanup.

### 2.8 Orchestrator allowed_tools Update

Add the new bridge tool to the Orchestrator's allowed_tools in `build_orc_options`:

```python
allowed_tools=[
    "Bash", "Read", "Write", "Edit", "Glob", "Grep",
    "mcp__bridge__send_to_content_agent",
    "mcp__bridge__send_to_datum_agent",
    "mcp__bridge__send_to_megamind_agent",  # NEW
],
```

---

## 3. Changes Required in Orchestrator

### 3.1 Orchestrator CLAUDE.md

Add `send_to_megamind_agent` to the capabilities table:

```markdown
| **mcp__bridge__send_to_megamind_agent** | Send strategic work to Megamind (depth grading, cascade, assessment) |
```

### 3.2 Orchestrator HEARTBEAT.md

Add 3 new steps after existing inbox check and pipeline trigger:

**Step 2.5: Agent Action Depth Grading Check**

```bash
psql $DATABASE_URL -t -A -c "
  SELECT id, action_text, relevance_score, thesis_connection, action_type
  FROM actions_queue
  WHERE assigned_to = 'Agent'
    AND status = 'Proposed'
    AND id NOT IN (SELECT action_id FROM depth_grades)
  ORDER BY relevance_score DESC
  LIMIT 5"
```

If results: compose depth grading prompt, call `send_to_megamind_agent`. If Megamind busy,
skip and retry next heartbeat.

**Step 2.6: Approved Depth Execution Check**

```bash
psql $DATABASE_URL -t -A -c "
  SELECT dg.id, dg.action_id, dg.approved_depth, dg.execution_prompt, dg.execution_agent
  FROM depth_grades dg
  WHERE dg.execution_status = 'approved'
  ORDER BY dg.created_at
  LIMIT 3"
```

If results: route each approved grade's `execution_prompt` to the specified agent
(content or datum). Update `execution_status = 'executing'`.

**Step 2.7: Cascade Trigger Check**

```bash
psql $DATABASE_URL -t -A -c "
  SELECT dg.id, dg.action_id, aq.action_text, aq.thesis_connection
  FROM depth_grades dg
  JOIN actions_queue aq ON dg.action_id = aq.id
  WHERE dg.execution_status = 'completed'
    AND dg.id NOT IN (SELECT trigger_source_id FROM cascade_events WHERE trigger_type = 'depth_completed')
  LIMIT 1"
```

If results: compose cascade trigger prompt, call `send_to_megamind_agent`.

---

## 4. Activation Pattern

Megamind follows the same activation pattern as Datum Agent — **on-demand, not heartbeat-driven**.

The Orchestrator wakes Megamind when:
1. New agent-assigned actions exist that need depth grading (Step 2.5)
2. Approved depth grades need execution routing (Step 2.6)
3. Completed work needs cascade processing (Step 2.7)
4. CAI inbox contains strategy_* message types
5. Daily strategic assessment is due (24h since last strategic_assessments record)

Megamind does NOT run on its own timer. It sleeps until the Orchestrator sends work.

---

## 5. Deploy Sequence

Deployment uses the existing `deploy.sh` script (3-phase: sync, bootstrap, cleanup).
The megamind directory will sync automatically since it's under `mcp-servers/agents/`.

Steps:
1. Merge lifecycle.py changes to main
2. Merge Orchestrator CLAUDE.md + HEARTBEAT.md changes to main
3. Run `deploy.sh` from Mac
4. Verify on droplet:
   - `ssh root@aicos-droplet`
   - `ls /opt/agents/megamind/` — confirm files synced
   - `journalctl -u orchestrator -f` — watch for megamind startup log
   - `tail -f /opt/agents/megamind/live.log` — verify live logging works

---

## 6. Testing Plan

### Test 1: Megamind Starts Successfully

- Deploy and check logs for: "Megamind started — session #1"
- Verify `state/megamind_session.txt` = 1
- Verify `traces/manifest.json` has megamind entry

### Test 2: Depth Grading Flow

1. Create an agent-assigned action in actions_queue:
   ```sql
   INSERT INTO actions_queue (action_text, action_type, priority, status, assigned_to, relevance_score, thesis_connection, source, created_at, updated_at)
   VALUES ('Test: Research AI agent frameworks', 'Research', 'P1', 'Proposed', 'Agent', 7.0, 'Agentic AI Infrastructure', 'test', NOW(), NOW());
   ```
2. Wait for next heartbeat (60s)
3. Verify: Orchestrator detects ungraded action, sends to Megamind
4. Verify: depth_grades record created with strategic_score and reasoning
5. Verify: execution_status = 'pending' (manual trust level)

### Test 3: Cascade Flow

1. Manually set a depth_grade to execution_status = 'completed'
2. Wait for next heartbeat
3. Verify: Orchestrator detects completed work, sends cascade trigger to Megamind
4. Verify: cascade_events record created with convergence_pass = TRUE

### Test 4: Strategic Assessment

1. Send via CAI inbox: `{"type": "strategy_assessment", "content": "Run daily strategic assessment"}`
2. Verify: Orchestrator routes to Megamind
3. Verify: strategic_assessments record created with convergence_ratio

### Test 5: Compaction

1. Let Megamind process 20+ prompts to approach 100K token threshold
2. Verify: prompt-manifest-check.sh injects COMPACTION REQUIRED
3. Verify: Megamind writes checkpoint and returns COMPACT_NOW
4. Verify: lifecycle.py restarts Megamind session

---

## 7. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Megamind startup slows overall system | Megamind starts in parallel with existing agents. No sequential dependency. |
| Megamind errors crash lifecycle.py | Same error isolation as Content/Datum: try/except around all client operations. |
| Megamind monopolizes Orchestrator attention | Depth grading check is LIMIT 5. Cascade check is LIMIT 1. Assessment is max once per day. |
| Budget runaway | $3.00 max_budget_usd per session. $10/day depth budget cap enforced by Megamind itself. |
| Token context exhaustion | Same compaction protocol as other agents (100K threshold, checkpoint + restart). |

---

## 8. NOT In Scope (This Phase)

- WebFront pages (/strategy, /strategy/depth, /strategy/cascades) — Phase 5
- Trust ramp automation — Phase 6
- ENIAC integration (when ENIAC becomes its own agent) — future
- Sync Agent restart with Megamind context — future
- Multi-agent orchestration (Megamind directly calling other agents) — explicitly out of scope, Orchestrator handles all routing
