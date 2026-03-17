# Plans Archive

Compacted 2026-03-16. Original plans consolidated into summaries. Cross-referenced against TRACES.md iterations 7-12 and actual codebase state.

---

## Plan 1: Architecture v2.2 Implementation (2026-03-16)

**Status:** MOSTLY COMPLETED (superseded in parts by v3 persistent architecture)
**Original file:** `2026-03-16-v2.2-implementation.md`

**Summary:** Replace v1 three-agent architecture with v2.2: State MCP (5 tools for CAI), Web Tools MCP (restructured with async task pattern), Content Agent (Bash+skills, CC-like with `query()`), Sync Agent (background Notion sync). Four processes on droplet. 20 tasks across 7 phases.

**Key decisions:**
- Agents use Bash + psql for DB access (not custom @tools). Skills teach DB schema.
- Web = MCP (tools) + Skills (intelligence), NOT an agent. Stateful tool server.
- CAI is a relay: inbox pattern (post_message -> cai_inbox table -> agent reads via psql)
- State MCP (5 tools) replaces Sync Agent gateway. Lightweight CAI window.
- web_task is exclusively for CAI (async submit/poll/retrieve pattern)
- Content Agent three classes of work: (1) direct tools+skills, (2) Agent delegation, (3) parallel batch
- Flag-based sync: notion_synced=false column. No sync_queue.
- 14 skills extracted from existing code (5 web, 5 content, 3 sync, 1 data)

**What was built (iterations 7-8):**
- Postgres migrations: 3 new tables (cai_inbox, notifications, sync_metadata), notion_synced columns
- State MCP: server.py + db modules (connection, thesis, inbox, notifications) + tests
- All 14 skills (5 web, 5 content, 3 sync, 1 data = 3,010 lines)
- Subagent definitions (web-researcher.md, content-worker.md)
- Infra: 4 systemd units + health_check.sh
- Web Tools MCP restructured: async task pattern (task_store.py), external tool wrappers
- Content agent: runner.py (query() pattern) + system_prompt.md (532 lines)
- Sync agent: runner.py + system_prompt.md (388 lines)
- deploy.sh rewritten for v2.2
- All 4 services deployed and running

**What changed from plan:**
- Content/Sync runners used ephemeral `query()` calls -- replaced in v3 by persistent ClaudeSDKClient
- Sync Agent was disabled after E2E testing (iteration 9) -- not needed for current system
- ThinkingConfig -> ThinkingConfigEnabled (SDK uses UnionType, not a class)
- action_outcomes table ownership required superuser fix (postgres role, not aicos)
- Content agent runner.py and content-agent.service later deleted in v3

---

## Plan 2: Agent Lifecycle Management (2026-03-16)

**Status:** COMPLETED
**Original file:** `2026-03-16-agent-lifecycle-management.md`

**Summary:** Replace ephemeral `query()` runners with persistent `ClaudeSDKClient`-based agents managed by a thin Python lifecycle daemon. Filesystem hooks for iteration logging, manifest-based compaction detection, and emergency checkpoint before SDK auto-compaction. Traces infrastructure for shared logging across agents.

**Key decisions:**
- orchestrator/ is the agent workspace root (cwd for ClaudeSDKClient)
- .claude/hooks/ inside workspace, loaded via setting_sources=["project"]
- traces/ shared across all agents, state/ per-agent inside workspace
- manifest.json is the ONLY file Python writes (besides active.txt)
- All state files written by agents (via tools) or hooks (via shell scripts)
- Two compaction systems: traces (file rotation at 20K chars) and session (restart at 100K tokens)

**What was built (iteration 10):**
- traces/ directory: manifest.json (both agents), active.txt, initial traces file, archive/
- orchestrator/state/: session + iteration counters
- orchestrator/.claude/hooks/: 3 hooks (stop-iteration-log, prompt-manifest-check, pre-compact-flush)
- orchestrator/.claude/settings.json: hook registration
- content/.claude/hooks/: 3 cloned hooks with AGENT="content"
- content/.claude/settings.json: hook registration
- content/state/: session + iteration counters + last_pipeline_run.txt
- infra/orchestrator.service: systemd unit

**What changed from plan:**
- COMPACTION_PROTOCOL.md and CHECKPOINT_FORMAT.md were NOT created on disk (plan Tasks 9-10). Compaction protocol was inlined into orchestrator CLAUDE.md and content CLAUDE.md instead.
- deploy.sh was rewritten more extensively (3-phase: sync/bootstrap/cleanup pattern) instead of the incremental edits planned

---

## Plan 3: Orchestrator + Content Agent (2026-03-16)

**Status:** COMPLETED (with iteration on async bridge)
**Original file:** `2026-03-16-orchestrator-content-agent.md`

**Summary:** Wire orchestrator and content agent as persistent ClaudeSDKClient sessions managed by lifecycle.py, connected via @tool bridge (send_to_content_agent). Orchestrator receives 60s heartbeats, checks inbox, triggers content pipeline. No system_prompt parameter -- agents get CLAUDE.md via setting_sources.

**Key decisions:**
- Agent SDK reads CLAUDE.md from cwd via setting_sources=["project"] -- same as CC
- @tool bridge via create_sdk_mcp_server: orchestrator calls mcp__bridge__send_to_content_agent
- Single Python process (lifecycle.py) manages both agents
- Content agent restart independent of orchestrator
- permission_mode="dontAsk" + allowed_tools for autonomous headless agents

**What was built (iterations 10-12):**
- orchestrator/lifecycle.py: 530 lines, manages both ClaudeSDKClients, @tool bridge, token tracking, compaction, pre-check optimization, live logging (PostToolUse hooks)
- orchestrator/CLAUDE.md: 8 sections (identity, heartbeat, DB access, bridge docs, compaction)
- orchestrator/HEARTBEAT.md: 5-step checklist
- content/CLAUDE.md: 18 sections (full rewrite from system_prompt.md -- persistent mode, ACK protocol, Postgres-as-queue pipeline, state tracking, lifecycle)
- Deleted: content/runner.py, content/system_prompt.md, infra/content-agent.service
- deploy.sh: rewritten for v3 (orchestrator replaces content-agent service)

**What changed from plan:**
- @tool bridge became async (fire-and-forget with asyncio.create_task + content_busy flag) after E2E showed orchestrator blocked 10+ min waiting for content response (iteration 11, Bug 1)
- lifecycle.py gained pre-check optimization: `has_work()` checks inbox + pipeline schedule in Python before waking LLM (saves ~$0.41/idle heartbeat)
- effort="low" + max_turns=15 + max_budget_usd=0.50 for orchestrator (plan had "medium"/30/$2.00)
- Pipeline interval changed to 12 hours (plan assumed 5 minutes)
- Live logging added (PostToolUse hooks + AssistantMessage extraction to live.log files) -- not in original plan
- Dead session detection added (consecutive zero-turn heartbeats trigger restart)
- Content CLAUDE.md added watch_list.json as read-only guardrail (plan had watch list as modifiable)
- state/server.py removed `type` param from post_message (CAI sends plain content, no tags)
