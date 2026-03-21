# Datum Agent Lifecycle Integration — M4 Loop 4
*Implemented: 2026-03-20*
*Author: Claude Opus 4.6*

---

## Summary

Integrated the Datum Agent as the third managed ClaudeSDKClient in `lifecycle.py`, following the exact patterns established by the Content Agent. The Orchestrator can now route `datum_*` inbox messages to the Datum Agent via the `send_to_datum_agent` bridge tool.

---

## Changes Made

### 1. `mcp-servers/agents/orchestrator/lifecycle.py`

Following the 16-section integration plan (`docs/superpowers/plans/2026-03-20-datum-lifecycle-integration.md`) exactly:

| Section | Change |
|---------|--------|
| Constants | Added `DATUM_WORKSPACE`, `DATUM_LIVE_LOG` |
| ClientState | Added `datum_client`, `datum_needs_restart`, `datum_busy` fields |
| `_state_dir()` | Added `"datum"` case returning `DATUM_WORKSPACE / "state"` |
| `build_datum_options()` | New function — Sonnet 4.6, dontAsk, 30 turns, $2.0 budget, 5K thinking tokens, Web Tools MCP, no Agent/subagents |
| Datum lifecycle | Added `start_datum_client()`, `stop_datum_client()`, `restart_datum_client()` |
| Bridge server | Added `_read_datum_response()` background task + `send_to_datum_agent` @tool |
| Bridge registration | `create_sdk_mcp_server` now includes both `send_to_content_agent` and `send_to_datum_agent` |
| Orc allowed_tools | Added `mcp__bridge__send_to_datum_agent` |
| `run_agent()` | Datum client started after content, compaction check in heartbeat loop, stopped in finally |
| `main()` | `stop_datum_client()` added to shutdown sequence |

Key design decisions preserved from the plan:
- **On-demand activation only** — Datum Agent has no heartbeat/pipeline cycle; it activates only when the Orchestrator forwards `datum_*` inbox messages
- **Fire-and-forget pattern** — `send_to_datum_agent` returns immediately; `_read_datum_response` runs as a background task via `asyncio.create_task`
- **Busy flag** prevents double invocation; orchestrator retries on next heartbeat
- **COMPACT_NOW detection** in response reader triggers `restart_datum_client()`

### 2. `mcp-servers/agents/orchestrator/CLAUDE.md`

- Added `mcp__bridge__send_to_datum_agent` to capabilities table (Section 2)
- Added Section 5b: "Sending Work to Datum Agent" with routing rules, batching guidance, and prompt format
- Updated anti-patterns (Section 8): added rules for datum routing (#2, #9, #10)

### 3. `mcp-servers/agents/orchestrator/HEARTBEAT.md`

- Rewrote Step 2 (Inbox Check) with routing table: `datum_*` types go to Datum Agent, everything else to Content Agent
- Added datum batching rule (3+ datum_* messages = single batched prompt)
- Processing steps now handle both agent groups independently (datum and content can both be invoked in the same heartbeat)

### 4. `mcp-servers/agents/datum/CLAUDE.md` (Minor Issue #1 fix)

- Fixed ACK example in Section 4 Step 6: changed generic column names (`name, company, role, linkedin_url, city`) to actual column names (`person_name, role_title, linkedin, home_base, e_e_priority`)

### 5. `mcp-servers/agents/skills/datum/datum-processing.md` (Minor Issue #2 fix)

- Fixed text input parsing example to use actual column names (`person_name`, `role_title`) instead of generic names
- Added "Parsed Field -> DB Column Mapping (Person)" table mapping extracted fields to actual column names
- Fixed extraction patterns to reference actual columns (`person_name`, `role_title`, `linkedin`, `home_base`)

### 6. `mcp-servers/agents/deploy.sh`

- Updated header comment to mention datum agent
- Added `live-datum.sh` to deploy output log commands

### 7. `mcp-servers/agents/deploy/tools/live-datum.sh` (NEW)

- Created live log viewer for datum agent (follows `live-content.sh` pattern exactly)

---

## Verification

- `python3 -c "import ast; ast.parse(open('lifecycle.py').read())"` — PASS (clean parse)
- All 12 implementation steps from the integration plan completed in order
- `datum/state/` directory with session/iteration files already exists from Phase 0
- No new systemd service needed — datum runs inside existing orchestrator process
- No new env vars needed — uses same `DATABASE_URL` and `ANTHROPIC_API_KEY`
- `deploy.sh` rsync already covers `datum/` directory (no exclusion needed)

---

## What's Next

- **Deploy and test** — `deploy.sh` to push to droplet, then send a `datum_person` inbox message to verify end-to-end routing
- **Content Pipeline integration** — Content Agent needs modification to emit `datum_entity` inbox messages when it discovers entities during content analysis (Phase 5 in design spec)
- **WebFront Datum Tab** — Phase 4 in design spec, deferred
