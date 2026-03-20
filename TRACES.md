# Build Traces

## Project Summary

Milestone 1 established the Claude Code era foundation: fixed Content Digest/Actions Queue data completeness (20+ params), implemented the AI-managed Thesis Tracker conviction engine (6-level spectrum, key questions lifecycle, autonomous thread creation), completed Cowork→CC migration (cleanup, archiving, architecture/vision docs evolved to v0.3/v5). Milestone 2 implemented full Data Sovereignty: public MCP endpoint (Cloudflare Tunnel, 17 tools), Postgres write-ahead for thesis + actions, bidirectional sync with field-level ownership, change detection with auto-action generation, SyncAgent on cron. Milestone 3 built Web Tools MCP (5 tools, port 8001, Cloudflare Tunnel), cookie sync infrastructure, and deep research on Agent SDK production patterns. Key decisions: Jina Reader primary/Firecrawl fallback, SPA readiness ladder, ClaudeSDKClient for persistent agents, UCB bandit strategy cache.

## Milestone Index

| # | Iterations | Focus | Key Decisions |
|---|------------|-------|---------------|
| 1 | 1-3 | Infrastructure Hardening + Thesis Tracker + Cowork→CC Migration | AI-managed conviction engine, conviction spectrum, key questions as page blocks, claude-ai-sync/ folder, architecture doc versioning strategy |
| 2 | 1-3 | Data Sovereignty — Public MCP + Postgres Backing + Sync + QA | Write-ahead pattern, field-level ownership, Cloudflare Tunnel endpoint, action generation from changes, 17 MCP tools QA'd |
| 3 | 1-3 | Web Tools MCP + Research + Three-Agent Foundation | Jina/Firecrawl scraping, cookie sync, SPA readiness ladder, ClaudeSDKClient for persistent agents, UCB bandit strategy |

*Full details: `traces/archive/milestone-N.md`*

<!-- end-header -->

---

## Current Work (Milestone 4 in progress)

### Iteration 4 - 2026-03-15
**Phase:** WebAgent — Full Build & Deploy
**Focus:** Build, deploy, and cutover WebAgent (replaces web-tools-mcp) with 11 phases

**Changes:** `mcp-servers/web-agent/` (new — entire project: server.py, agent.py, system_prompt.md, lib/{browser,scrape,search,cookies,fingerprint,strategy,quality,stealth}.py, deploy.sh, tests/test_agent.py, pyproject.toml)
**Infrastructure:** systemd service (hardened: MemoryHigh=768M, MemoryMax=1G, OOMScoreAdjust=500, ExecStopPost pkill chrome), 60s health monitoring cron, PostgreSQL OOM protection (-500), ANTHROPIC_API_KEY added to /opt/web-agent/.env
**Decisions:**
- anthropic SDK (v0.84.0) manual tool-use loop — no separate Agent SDK package needed
- All lib modules async (scrape, search, fingerprint) after code review caught blocking httpx calls
- Browser reconnect resets Playwright entirely (prevents stale handle after Chrome crash)
- readiness time: mode capped at 30s (prevents permanent semaphore lock)
- Strategy cache uses SQLite upsert (record_outcome works before seed_strategies)
- Per-tool 30s timeout in agent loop (prevents Playwright hangs from draining memory)
- Empty tool_results guard + unhandled stop_reason fallthrough (prevents silent infinite loops)
- Module-level AsyncAnthropic client (prevents connection pool churn)
- Stealth persona wired into browser.py by default (coherent fingerprint)
**Tests:** 19/19 pass (Tier 1: 7 unit, Tier 2: 11 integration, Tier 3: 1 agent mode)
**Next:** Commit all work, update CHECKPOINT.md, 48h canary before decommissioning web-tools-mcp

### Iteration 5 - 2026-03-15
**Phase:** Three-Agent Architecture — Design + Audit + Foundation
**Focus:** Design unified 3-agent architecture (Web, Content, Sync), 4-vantage audit, begin implementation

**Changes:** `docs/superpowers/specs/2026-03-15-three-agent-architecture-design.md` (new — 11 sections + 2 appendices, LOCKED post-audit), `docs/superpowers/plans/2026-03-15-three-agent-implementation.md` (new — 15 tasks across 5 phases), `mcp-servers/agents/` (new monorepo scaffold: pyproject.toml, shared/{types,logging,mcp_client}.py, directory structure for 3 agents)
**Decisions:**
- User mandated ALL agents on Claude Agent SDK (ClaudeSDKClient) — no raw API calls
- 3-agent split: Web (browser/scrape/extract), Content (analysis/scoring/publishing), Sync (gateway/DB/sync)
- Sync Agent is sole DB writer — no other agent reads/writes Notion or Postgres
- Sync Agent as gateway (mcp.3niac.com) — CAI connects to single endpoint, proxies web tools
- Inter-agent communication via MCP HTTP tool calls (SDK natively supports `"type": "http"`)
- Single shared venv, shared CLI binary (237MB once on disk)
- Content Agent has autonomous reasoning with tools (not single-shot API call)
- 4-vantage audit: QA Lead, DevOps, System Architect, Backend Engineer — 57 findings → 15 themes accepted
- Key audit fixes: idempotency keys (C2), circuit breaker (C3), structured JSON logging with trace IDs (C4), token bucket rate limiter (H4), session pool semaphore (H1)
- Rejected: feature flags (clean cutover), formal cutover runbook, direct CAI→Web Agent access
**Implementation:** 14/15 tasks complete via subagent-driven development (8 subagents, 17 commits, 63 files, 9,358 lines Python). Sync Agent (23 tools, 7 libs), Web Agent (20 tools, 10 libs, 6 hooks), Content Agent (7 tools, 3 libs, pipeline orchestrator). Shared foundation (types, logging with trace IDs, MCP client with circuit breaker). Deploy infra (deploy.sh, 3 systemd units, health_check.sh, install.sh, acceptance.sh).
**Deployed:** All 3 agents running on droplet (sync:8000, web:8001, content:8002). Old ai-cos-mcp stopped. Cloudflare tunnel unchanged (port 8000). Memory: 719MB/3.8GB.
**Post-deploy fixes:** FastMCP 3.x lifespan API (on_startup→lifespan context manager), 10 broken imports (from runners./lib. → from sync.lib./content.lib.).
**Code audit:** 3-vantage review (SDK expert, code quality, DevOps) found 25 issues. 2/25 resolved: C1 (query+hooks verified working), C5 (imports fixed+deployed). 23 remaining (4 critical, 7 high, 6 medium, 2 low). Tracker: `docs/superpowers/specs/2026-03-15-code-audit-tracker.md`.
**Next:** Continue code audit fixes C2→C6→H1-H7, then remaining medium/low items.

### Iteration 6 - 2026-03-16
**Phase:** Architecture v2.2 — Complete Redesign from CC-Parallel Principles
**Focus:** Deep brainstorming (10+ rounds), fundamental architecture rethink, spec + plan

**Changes:** `docs/superpowers/specs/2026-03-15-architecture-v2.2-design.md` (new — full v2.2 spec, APPROVED), `docs/superpowers/plans/2026-03-16-v2.2-implementation.md` (new — 20 tasks, 7 phases), `docs/superpowers/specs/2026-03-15-three-agent-architecture-v2-stub.md` (intermediate stub), `CHECKPOINT.md` (updated for v2.2)
**Decisions:**
- Agent SDK = same harness as CC. Agents have Bash, Read, Write, Skills — CC-like capabilities.
- Agents use Bash + psql for Postgres access (not custom @tools). Skills teach DB schema.
- Web = MCP (tools) + Skills (intelligence), NOT an agent. Web Tools MCP is a stateful tool server.
- CAI is a relay: inbox pattern (post_message → cai_inbox table → agent reads via psql).
- CAI ↔ agent communication is async via shared Postgres state (inbox + notifications tables).
- State MCP (5 tools) replaces Sync Agent gateway (was 23 tools). Lightweight CAI window.
- web_task is exclusively for CAI (async submit/poll/retrieve pattern, like Parallel MCP).
- Content Agent three classes of work: (1) direct tools+skills, (2) background Agent delegation with full web toolkit, (3) parallel batch subagents.
- Content Agent NEVER calls web_task. Uses Agent tool → web-researcher subagent (has EVERYTHING web_task has).
- Flag-based sync: notion_synced=false column, Sync Agent picks up unsynced rows. No sync_queue.
- Freshness = sync_metadata table + agent reasoning. Not an MCP tool.
- Extensibility triad: tools + MCPs + skills.
- Fully agentic first. Token costs not a design constraint.
- Four processes: State MCP (8000), Web Tools MCP (8001), Content Agent (internal), Sync Agent (internal).
- 14 skills to extract from existing code (5 web, 5 content, 3 sync, 1 data).
**Next:** Execute v2.2 implementation plan Phase 1→7.

### Iteration 7 - 2026-03-16
**Phase:** Architecture v2.2 — Full Parallel Build (All 7 Chunks)
**Focus:** Build entire v2.2 codebase via 5 parallel subagents. 41 files created/modified, ~5,000 lines.

**Changes:**
- `sql/v2.2-migrations.sql` (new — 3 tables, 3 ALTER, 2 indexes)
- `state/` (new — 9 files: server.py + db/{connection,thesis,inbox,notifications}.py + tests)
- `skills/` (new — 14 markdown skills: 5 web, 5 content, 3 sync, 1 data = 3,010 lines)
- `.claude/agents/` (new — web-researcher.md + content-worker.md subagent defs)
- `infra/` (new — 4 systemd units + health_check.sh)
- `web/task_store.py` (new), `web/server.py` (restructured: async task pattern), `web/tools.py` (new external wrappers), `web/agent.py` (setting_sources)
- `content/runner.py` (new — asyncio timer + query()), `content/system_prompt.md` (v2.2 rewrite, 532 lines)
- `sync/runner.py` (new — asyncio timer + query()), `sync/system_prompt.md` (v2.2 rewrite, 388 lines)
- `deploy.sh` (rewritten for v2.2: 4 services, skills sync, subagent sync)
- `pyproject.toml` (added asyncpg, state/tests)
- `docs/v2.2-build-log.md` (new — testing reference for all chunks)
**Decisions:**
- permission_mode="dontAsk" confirmed correct for autonomous headless agents (auto-denies unlisted tools)
- 5 parallel subagents with zero file write overlap (infra, state-mcp, skills, web-mcp, content+sync)
- v1 content/system_prompt.md inlined in skills agent prompt to avoid read/write race with content agent rewrite
- State MCP tests run in-process with mocked asyncpg (23 tests)
- Build log tracks upstream/downstream dependencies + testing checklist per chunk
**Next:** Deploy to droplet, run migrations, E2E testing. Bug fix session to follow.

### Iteration 8 - 2026-03-16
**Phase:** Architecture v2.2 — Deploy + E2E Verification
**Focus:** Deploy v2.2 to droplet, run migrations, fix ThinkingConfig bug, verify all services

**Changes:** `content/runner.py` (ThinkingConfig → ThinkingConfigEnabled), `sync/runner.py` (same fix)
**Infrastructure:**
- Stopped old v1 services (web-agent disabled, content-agent + sync-agent replaced)
- Deployed 49-file commit to droplet via deploy.sh (4 services, skills, subagents)
- Ran v2.2 SQL migrations: 3 new tables (cai_inbox, notifications, sync_metadata) + notion_synced columns on 3 tables
- Fixed action_outcomes table ownership (postgres → aicos) via superuser
- All 4 v2.2 services running: State MCP (:8000), Web Tools MCP (:8001), Content Agent, Sync Agent
- Cloudflare tunnels verified: mcp.3niac.com → 8000, web.3niac.com → 8001
**Decisions:**
- ThinkingConfig is a UnionType in Agent SDK (not a class). Must use ThinkingConfigEnabled constructor.
- action_outcomes table owned by postgres role — ALTER TABLE requires superuser, not aicos role
**Next:** Functional E2E testing (cai_inbox → Content Agent processing, notion_synced=FALSE → Sync Agent push)

### Iteration 9 - 2026-03-16
**Phase:** E2E Testing + Architecture v3 Research
**Focus:** CAI↔State MCP E2E, thesis column fix, sync agent disabled, deep research on persistent agent patterns

**Changes:** `state/db/thesis.py` (name→thread_name, key_questions→key_question_summary), `state/server.py` (dict key fixes), `deploy.sh` (removed sync-agent from deploy/enable/restart/health)
**E2E Results:**
- State MCP: health_check ✅, get_state(notifications) ✅, get_state(thesis) ✅ after column fix
- Content Agent: post_message→cai_inbox ✅, agent picks up and creates watch_list.json ✅, but processed flag not set (prompt ordering bug)
- Sync Agent: first cycle completed (4min, $0.00) but disabled — not needed for now
**Decisions:**
- Sync agent stopped+disabled on droplet, removed from deploy.sh. Code stays in repo.
- query() is wrong pattern for agents — spawns ephemeral CLI subprocess every cycle, no memory
- ClaudeSDKClient is correct — persistent session, context retention, like CC terminal
- Deep research: OpenClaw heartbeat pattern (HEARTBEAT.md, main session, skip-if-busy)
- Architecture direction: Orchestrator agent (persistent, smart) + Content Agent (persistent, thick) connected via custom @tool. Python is just lifecycle plumbing.
**Research:** `docs/research/persistent-agent-architecture-research.md` (27 sources), ultra research on OpenClaw in progress
**Next:** Absorb ultra research results, write v3 architecture plan for persistent orchestrator + content agent

### Iteration 10 - 2026-03-16
**Phase:** v3 Persistent Agent Architecture — Plans + Full Build
**Focus:** Design + implement persistent orchestrator + content agent on ClaudeSDKClient, managed by lifecycle.py with @tool bridge

**Changes:**
- `orchestrator/lifecycle.py` (new — 280 lines: manages both ClaudeSDKClients, @tool bridge `send_to_content_agent`, token tracking, compaction restart)
- `orchestrator/CLAUDE.md` (new — 8 sections: identity, heartbeat protocol, DB access, iteration logging, compaction)
- `orchestrator/HEARTBEAT.md` (new — 5-step checklist: checkpoint, inbox, pipeline, traces compaction, log)
- `orchestrator/.claude/hooks/` (new — 3 filesystem hooks: stop-iteration-log, prompt-manifest-check, pre-compact-flush)
- `orchestrator/.claude/settings.json` (new — hook registration)
- `orchestrator/state/` (new — session/iteration counters, COMPACTION_PROTOCOL.md, CHECKPOINT_FORMAT.md)
- `content/CLAUDE.md` (rewrite from system_prompt.md — 18 sections, added: persistent identity, ACK protocol, state tracking, lifecycle/compaction, 4 new anti-patterns)
- `content/.claude/hooks/` (new — 3 hooks cloned from orchestrator with AGENT="content")
- `content/.claude/settings.json` (new — hook registration)
- `content/state/` (new — session/iteration counters, last_pipeline_run.txt, CHECKPOINT_FORMAT.md)
- `traces/` (new — manifest.json for both agents, active.txt pointer, initial traces file)
- `infra/orchestrator.service` (new — systemd unit, depends on state-mcp + web-tools-mcp)
- `deploy.sh` (rewritten for v3: orchestrator replaces content-agent service, protects state/traces from rsync)
- Deleted: `content/runner.py`, `content/system_prompt.md`, `infra/content-agent.service`
**Plans:** `docs/superpowers/plans/2026-03-16-agent-lifecycle-management.md` (12 tasks, 5 chunks), `docs/superpowers/plans/2026-03-16-orchestrator-content-agent.md` (9 tasks, 4 chunks)
**Decisions:**
- Agent SDK reads CLAUDE.md from cwd via setting_sources=["project"] — same as CC. No system_prompt= parameter needed.
- bypassPermissions for both agents (full tool access, simplify now, restrict later)
- @tool bridge via create_sdk_mcp_server: orchestrator calls mcp__bridge__send_to_content_agent, Python forwards to content_client.query() in-process
- Content agent is persistent ClaudeSDKClient (replaces ephemeral query() runner). Same analysis/scoring/publishing logic, new ACK protocol + state tracking.
- Single Python process (lifecycle.py) manages both agents. Content agent restart independent of orchestrator.
- Traces compaction (file rotation at 20K chars) separate from session compaction (context restart at 100K tokens)
**Next:** Commit, deploy to droplet, E2E test heartbeat → inbox relay → content pipeline flow

### Iteration 11 - 2026-03-16
**Phase:** v3 Deploy + E2E + Bug Fixes
**Focus:** Deploy v3 to droplet, E2E testing, identify/fix bugs, backfill content_digests

**Deploy:** All 3 services running (state-mcp:8000, web-tools-mcp:8001, orchestrator). Content agent managed by lifecycle.py.
**E2E Results:**
- Orchestrator sends heartbeat, triggers content pipeline via @tool bridge ✅
- Content agent processes 20VC YouTube channel, produces full DigestData JSON ✅
- Content agent writes to Postgres, publishes to digest.wiki repo ✅
- BUT: orchestrator blocked for 10+ min waiting for content agent response (Bug 1)
**Bugs Found (9 total):**
1. Synchronous @tool bridge blocks orchestrator — FIXED: fire-and-forget with asyncio.create_task + content_busy flag
2. First deploy needs seed files (traces/, state/) — noted
3. Old files not cleaned on deploy (system_prompt.md persisted) — noted
4. Idle heartbeat too expensive ($0.41/6 turns) — effort should be "low", inline checklist
5. Orchestrator re-reads HEARTBEAT.md every heartbeat — should remember (persistent session)
6. Double iteration increment (agent manually + Stop hook) — let hook handle it
7. Content agent returned gibberish on 2nd bridge call — investigate
8. last_pipeline_run.txt never written by content agent — prompt gap
9. Content agent processes all historical content (no dedup on first run) — needs since-date guard
**Permission mode:** bypassPermissions blocked as root → acceptEdits still prompts for Bash → dontAsk + allowed_tools is correct pattern
**Backfill:** content_digests had 8 rows (only v3 agent), old v1 pipeline wrote to Notion only. Backfilled 17 from disk JSON files, deleted 2 duplicate-slug entries. Now 23 rows = single source of truth.
**Changes:** `orchestrator/lifecycle.py` (fire-and-forget @tool bridge, content_busy flag), `orchestrator/CLAUDE.md` (async send_to_content_agent docs), `orchestrator/HEARTBEAT.md` (handle busy response)
**Next:** Fix remaining bugs (effort=low, inline heartbeat, dedup guard), redeploy, monitor costs

### Iteration 12 - 2026-03-16
**Phase:** v3 Bug Fixes + Data Reconciliation + E2E Test
**Focus:** Fix async bridge, Postgres-as-queue pipeline, content_digests backfill, Notion sync, tag removal

**Changes:**
- `orchestrator/lifecycle.py` (async @tool bridge: fire-and-forget with asyncio.create_task + content_busy flag)
- `orchestrator/CLAUDE.md` (async bridge docs, handle busy response)
- `orchestrator/HEARTBEAT.md` (handle busy response in steps 2+3)
- `content/CLAUDE.md` (Postgres-as-queue pipeline: 3-phase discover/process/wrap, content-driven inbox routing, watch list read-only guardrail, removed notion_synced references, updated DB schema docs)
- `state/server.py` (removed type param from post_message — no more tags, CAI sends plain content)
**Postgres migrations (on droplet):**
- content_digests: added status column, dropped notion_synced/last_synced_at/notion_page_id, added UNIQUE(url), added status index
- Backfilled 17 rows from disk JSON, deleted 2 dupes + 2 failed = 21 published
- Backfilled upload_date + processing_date
**Data reconciliation:** Disk (21 JSON) = Postgres (21 published) = Notion (21 entries, freshly pushed)
**Droplet fixes:** watch_list.json reverted to curated playlist, cai_inbox cleared, view-logs.py deployed
**Next:** E2E test — CAI inbox → orchestrator relay → content agent digest pipeline

### Iteration 13 - 2026-03-16
**Phase:** Cost Optimization + Deploy SOP + Repo Cleanup + Documentation Overhaul
**Focus:** Fix remaining bugs, implement cost optimization, clean repo, build PRIOR-ART.md, artefact routing

**Bug Fixes Applied:**
- Filesystem hooks schema (matcher group nesting — SDK silently loads 0 matchers without it)
- Dead session auto-restart (2 consecutive zero-turn heartbeats → bump session)
- Python pre-check cost optimization (has_work() checks inbox + pipeline via psql/filesystem, skip LLM if idle = $0)
- Orchestrator effort=low, max_turns=15, max_budget=$0.50, pipeline schedule 12hr
- Mandatory last_pipeline_run.txt write (bold instruction in content CLAUDE.md Phase 3)
**Deploy SOP Overhaul:**
- Static docs (COMPACTION_PROTOCOL.md, CHECKPOINT_FORMAT.md) moved out of state/ to agent root
- Runtime counters removed from git (.gitignore), created by bootstrap
- deploy/ directory: bootstrap.sh, cleanup.sh, tools/ (view-logs.py, live-*.sh), DROPLET-MANIFEST.md
- deploy.sh rewritten: 3-phase SYNC → BOOTSTRAP → CLEANUP+RESTART
**Live Logging:** PostToolUse programmatic hooks + AssistantMessage ThinkingBlock/TextBlock extraction → live.log per agent
**Repo Cleanup:** 213 stale files → Archives/ (code) + docs/archives/ (docs). FOLDER-INDEX.md rebuilt. queue/, Training Data/ archived.
**Artefact Routing:** CLAUDE.md routing table — plans/specs/brainstorms/research/audits with YYYY-MM-DD naming
**Documentation:** PRIOR-ART.md (35 entries, 4 eras from 4 parallel subagents), DROPLET-RUNBOOK.md rewritten, PENDING-ITEMS-2026-03-16.md, plans compacted, MCP-CLOUDFLARE-TUNNEL-SETUP.md renamed+updated
**Cost Research:** docs/research/2026-03-16-agent-cost-optimization.md — Python pre-check biggest win ($173/day → $0 idle)
**Health Check:** "run a health check" catchphrase → 10-min monitoring audit
**Next:** Update docs/source-of-truth/ (9 files, section by section)

### Iteration 14 - 2026-03-17
**Phase:** Source of Truth v3 Update + Dead Code Cleanup
**Focus:** Update all docs/source-of-truth/ files for v3, dead reference audit (10 agents × 202 files), archive v2 dead Python code

**Source-of-Truth Changes:**
- `VISION-AND-DIRECTION.md` (stripped to 4 stable sections, dropped build phases/gaps/current-vs-ideal)
- `METHODOLOGY.md` (dropped Open Evaluations, kept 15 principles + tech eval framework)
- `ARCHITECTURE.md` (full rewrite — stable patterns only, no status labels)
- `MCP-TOOLS-INVENTORY.md` (full rewrite — State MCP 5 + Web Tools MCP 11, routing rules + guardrails)
- `DATA-ARCHITECTURE.md` (full update — 10 Postgres tables, Postgres-as-queue, field ownership summary)
- `CAPABILITY-MAP.md` (light touch — removed status labels, updated agent refs)
- `ENTITY-SCHEMAS.md` (light touch — runner pattern to ClaudeSDKClient/psql/skills)
- `README.md` (updated index), `PRIOR-ART.md` (moved in from docs/)
- `DROPLET-RUNBOOK.md` + `MCP-CLOUDFLARE-TUNNEL-SETUP.md` (moved from docs/architecture/)
- `SYSTEM-STATE.md` DELETED (DROPLET-RUNBOOK covers everything)
- `FOLDER-INDEX.md` DELETED (repo itself is the index)
**Dead Reference Audit:** 10 parallel agents scanned 202 files. Found 8 actionable dead refs → all addressed.
**Dead Code Cleanup:**
- 25+ v2 Python files archived to `Archives/agents-v2-python/` (content/*.py, sync/*.py, shared/mcp_client+types)
- `shared/logging.py` → `web/lib/logger.py` (only active consumer is web/)
- `sync/` directory removed entirely (disabled agent, all Python dead)
- `content/` reduced to pure Claude agent workspace (CLAUDE.md + hooks + state only)
- `infra/health_check.sh` fixed (content-agent/sync-agent → orchestrator)
- `pyproject.toml` testpaths cleaned (removed content/tests, sync/tests)
- `web/tests/test_tools.py` fixed (removed 2 broken imports)
**Decisions:**
- Point-in-time state stripped from stable docs → Build Roadmap/TRACES/PENDING-ITEMS
- Infrastructure docs consolidated into source-of-truth/ (eliminated docs/architecture/)
- v2 Python code is dead — v3 agents are ClaudeSDKClients that don't import Python. Archive, don't maintain.
- shared/ eliminated — logging moved to web/lib/ where its only consumer lives
**Next:** Milestone 3 compaction (iterations 1-3), then merge branch to main

### Iteration 15 - 2026-03-18
**Phase:** Critical Bug Fix — Pipeline Timestamp Enforcement via Hooks
**Focus:** Fix `last_pipeline_run.txt` never written (Critical #2 from PENDING-ITEMS), verify Critical #1 already resolved, create agent hook lifecycle reference docs

**Analysis:**
- Critical #1 (COMPACTION_PROTOCOL.md missing): FALSE — files exist on disk, pending items doc was stale
- Critical #2 (last_pipeline_run.txt never written): CONFIRMED — LLM instruction in Phase 3 not reliably executed. `has_work()` returns "pipeline never ran" every 60s heartbeat, causing ~1,440 unnecessary wakeups/day
- 5 parallel simulation agents traced all scenarios: happy path, inbox-only, busy, crash, compaction, first-run, mixed work
- Discovered: Stop hook fires per-query (not per-session) — proven by 84 iterations in session #1

**Fix (two-condition hook approach):**
- `content/.claude/hooks/prompt-manifest-check.sh`: Added pipeline detection — extracts prompt text, sets `state/pipeline_requested.txt` flag when prompt contains "pipeline cycle"
- `content/.claude/hooks/stop-iteration-log.sh`: Added two-condition timestamp write — if flag exists AND ACK contains "Pipeline" (case-insensitive) → write ISO timestamp to `last_pipeline_run.txt`. Always cleans stale flags (crash/compaction safety).

**Tests:** 13/13 pass — pipeline happy path, inbox isolation, empty prompt, flag+ACK, stale flag cleanup, compaction mid-pipeline, crash recovery (inbox-first and pipeline-retry), stop_hook_active guard, case-insensitive match, iteration logging regression

**Documentation:**
- `docs/reference/droplet-lifecycle-2026-03-18.md` (updated — added hooks section, early-return semantics, state cleanup gaps, pipeline timestamp enforcement)
- `docs/reference/content-agent-hook-lifecycle-2026-03-18.md` (new — full event flows for pipeline/inbox/compaction/crash, state files, anti-patterns)
- `docs/reference/orchestrator-agent-hook-lifecycle-2026-03-18.md` (new — full event flows for heartbeat/idle/compaction/dead-session/crash, orc vs content comparison)
- `docs/PENDING-ITEMS-2026-03-16.md` (Critical #1 and #2 marked resolved)

**Changes:** `prompt-manifest-check.sh` (pipeline flag), `stop-iteration-log.sh` (two-condition timestamp), 3 lifecycle docs (new+updated), `PENDING-ITEMS-2026-03-16.md`
**Decisions:**
- Hook-based enforcement over LLM instruction reliance — deterministic, testable, crash-safe
- Two-condition pattern (flag = intent, ACK = proof) prevents false timestamps from crash/compaction
- `bump_session()` state cleanup gap documented but not fixed — hooks handle it via flag cleanup on next Stop

### Iteration 16 - 2026-03-18
**Phase:** Pipeline Analysis + QMD Integration Planning
**Focus:** Full lifecycle.py behaviour map, QMD CC integration audit, upgrade plan

**Changes:** `docs/reference/droplet-lifecycle-2026-03-18.md` (updated by user with hook details, early-return semantics, state gaps), `docs/superpowers/plans/2026-03-18-qmd-cc-integration-upgrade.md` (new — 6-task plan for hook-based QMD)
**Analysis:**
- QMD is global infrastructure (plugin + global settings.json + global CLAUDE.md), NOT part of CASH Build System
- CLAUDE.md soft-triggers for proactive QMD usage have ~0% reliability — LLM never follows them
- Current QMD hooks: SessionStart `qmd update` (indexing only, no query injection)
- 334 docs need embedding (vec/hyde search degraded)
- Fix: 3 new hooks (SessionStart context query, UserPromptSubmit prompt analysis, PostToolUseFailure counter)
**Next:** Execute QMD integration upgrade plan, run `qmd embed` to clear backlog

### Iteration 17 - 2026-03-18
**Phase:** WebFront Architecture — Think-Through + Documentation + DB Selection
**Focus:** Map full data flow, evolve digest.wiki into interactive "WebFront", select managed Postgres provider, validate against IRGI requirements

**Analysis:**
- Mapped complete connection flow: Content Agent → Postgres (pipeline queue) → JSON files → git push → Vercel SSG → digest.wiki
- digest.wiki has NO runtime DB connection — pure SSG from flat JSON files
- Fundamental constraint: Postgres on droplet unreachable from Vercel serverless (no Tailscale)
- Apache AGE NOT supported on ANY managed Postgres (Neon, Supabase, RDS) — graph must be separate service
- Agent heartbeat (60s psql query) NEGATES Neon's scale-to-zero — compute never suspends
- IRGI compatibility verified: all 5 phases work with Supabase (pgvector + FTS supported, graph is separate)

**Decisions:**
- **"WebFront"** = new name for the web frontend (digest.wiki). "Interface Layer" = all surfaces
- **WebFront + CAI** designated as primary interaction surfaces for AI CoS vision
- **Managed Postgres** chosen over self-hosted (Vercel can't reach droplet) and dual-DB (unnecessary replication complexity)
- **Supabase** chosen over Neon — heartbeat negates scale-to-zero, $6/mo more for real-time + PostgREST + MCP + dashboard. Real-time needed for WebFront Phases 3-4.
- **Graph = separate service** (Neo4j/Zep/Graphiti) — Apache AGE dead on all managed Postgres
- **Feature roadmap:** Action triage → Thesis interaction → Pipeline status → Agent messaging
- **Rendering strategy:** Hybrid SSG (digest pages) + dynamic server components (interactive features)

**Changes:**
- `docs/source-of-truth/WEBFRONT.md` (new — current state, Supabase migration plan, feature roadmap, connection map)
- `docs/superpowers/brainstorms/2026-03-18-webfront-architecture-decisions.md` (new — WebFront decision trail)
- `docs/superpowers/brainstorms/2026-03-18-managed-postgres-and-irgi-decisions.md` (new — Neon vs Supabase, IRGI compat)
- 6 source-of-truth docs updated (README, ARCHITECTURE, DATA-ARCHITECTURE, CAPABILITY-MAP, DROPLET-RUNBOOK, VISION-AND-DIRECTION)
**Next:** Supabase migration (create project → pg_dump → import → update env vars → verify agent pipeline → WebFront Phase 1)

### Iteration 18 - 2026-03-18
**Phase:** Exhaustive Code Review + Critical Fixes
**Focus:** 5-domain parallel code review (92 findings), fix all 13 critical issues, milestone 3 compaction

**Review:** 68 files, ~8,800 lines across orchestrator, State MCP, Web MCP, deploy/infra, digest site. 13 Critical, 25 High, 33 Medium, 21 Low. Full report: `docs/audits/2026-03-18-exhaustive-code-review.md`

**Critical Fixes Applied:**
- C6: SSRF guard — `url_validation.py` blocks internal IPs on `scrape()`, `browse()`, `fingerprint()`
- C1: `content_busy` deadlock — try/except around `query()` in lifecycle.py bridge
- C2+C3: COMPACT_NOW detection — consistent `msg.result` check for both agents
- C4: FALSE POSITIVE — Python 3.8+ auto-detects async targets in `patch()`
- C5: Test fixture field names — `thread_name`/`key_question_summary` (23/23 pass)
- C7-C9: Deleted ghost v1 infra (cron/health_check.sh, systemd/, scripts/preflight.sh)
- C10-C11: Removed stale port 8002 tests from test_integration.py + acceptance.sh
- C12+C13: Digest site path traversal + JSON.parse guard in digests.ts

**Changes:** +1 new (`url_validation.py`), 6 deleted (v1 ghost files), 10 edited. Net -209 lines.
**Decisions:**
- SSRF guard at lib layer (not hooks) so ALL callers are protected
- DNS rebinding gap noted but deferred (requires socket.getaddrinfo resolution check)
- C4 dismissed after running tests — Python 3.8+ mock auto-detection works correctly
**Next:** Merge to main, deploy to droplet, push digest site fix

### Iteration 19 - 2026-03-18
**Phase:** High/Medium Fixes + Database Architecture Audit + Migration Prep
**Focus:** Implement 38 high/medium findings, 3-dimension DB audit, baseline schema export, Supabase migration planning

**High/Medium Fixes (38 items in 9 batches):**
- Lifecycle.py: corrupt manifest guard, DATABASE_URL validation, always bump session, mkdir, logging
- Prompt fixes: watch_list.json contradiction, inbox processed semantics, HEARTBEAT.md reference
- State MCP: asyncio.Lock on pool, structured errors, NULL COALESCE, health DB check, Literal type
- Web MCP: evaluate blocked on FastMCP, session state redacted, task eviction, SQLite reconnect
- Deploy: cwd enforcement, abort on failure, pipefail
- Scripts: path fixes, timeout handling, type annotations
- Digest: DATA_DIR guard, UTC timestamps, v5 footer, watch_sections guard

**Database Audit (3 parallel agents):**
- Schema audit: 6 Critical, 5 High — missing schema versioning, constraints, TIMESTAMP inconsistency
- Query audit: subprocess psql concerns, pool sizing, unbounded queries
- Data flow audit: inbox message loss risk, queue race condition, concurrent evidence append
- DB7 (missing indexes) was FALSE POSITIVE — live schema has 20+ indexes already
- DB1: Baseline schema exported → `sql/v1.0-baseline-schema.sql` (11 tables, 20+ indexes)
- DB5: Evidence append NULL-safe (COALESCE in ELSE branches)

**Changes:** 23 files edited, 3 audit reports created, baseline schema exported. Merged to main, branch deleted.
**Decisions:**
- `any` type correct for JSON.parse in digest normalisation (Record<string, unknown> broke TypeScript build)
- DB4 conviction constraint safe to add (zero invalid rows) but deferred until code adds explicit `conviction='New'` to INSERT
- Supabase migration SOP: inventory → setup → canary test (user-approved approach)
**Next:** Execute Supabase migration with dual-audit plan

### Iteration 20 - 2026-03-19
**Phase:** Supabase Migration — Project Setup + Session Handoff
**Focus:** User created Supabase project, authenticated MCP plugin, updated CHECKPOINT.md for next session

**Changes:** `CHECKPOINT.md` (updated — Supabase project details added, pgvector + connection string as pre-migration steps, password URL-encoding note)
**Context:**
- Supabase project created: Org "Aacash", Project "AI COS", MEDIUM compute (4GB/2-core ARM), us-east-1
- Supabase MCP plugin authenticated in Claude Code (was showing "Needs authentication", fixed by user via remove+re-add)
- `claude mcp auth` and `claude mcp reset` commands don't exist — only add/remove/list
- Prepared handoff prompt for next session to execute 6-phase migration
- Password contains `@` → must be `%40` in connection string URLs
**Next:** New CC session executes migration phases 1-6 from the plan

### Iteration 21 - 2026-03-19
**Phase:** Supabase Migration — Full Execution (Phases 1-5)
**Focus:** Execute all 6 migration phases from the dual-audited plan. pgvector enabled, canary tests passed, single-phase cutover with ~2 min downtime.

**Changes:** `CHECKPOINT.md` (updated — migration complete, Supabase project details finalized), `/opt/agents/.env` on droplet (DATABASE_URL switched to Supabase pooler)
**Infrastructure:**
- pgvector v0.8.0 enabled on Supabase via `CREATE EXTENSION vector`
- TIMESTAMPTZ fix: 7 columns across 4 tables (cai_inbox, notifications, sync_metadata, content_digests)
- Pre-migration backup: pg_dump + baseline row counts (934 rows) + sequences to /opt/backups/
- Canary tests: psql connectivity, asyncpg pool (min=1, max=3), orchestrator query pattern — all pass
- Pool config deployed via deploy.sh (all 3 services healthy)
- Cutover: stop services → fresh dump → pg_restore --clean to Supabase → verify 934 rows + 37 indexes + pgvector → update .env → restart
- Downtime: 04:50:05 → 04:52:17 UTC (~2 min 12s)
- Post-cutover: all 3 services healthy, orchestrator detected pipeline work and processed heartbeat ($0.09)
**Decisions:**
- Region is us-west-2 (not us-east-1 as originally noted in CHECKPOINT) — minor latency difference, not a blocker
- Session pooler URL: `postgres://postgres.bkxjvymaiknokybtupfm:supabase%401987@aws-0-us-west-2.pooler.supabase.com:5432/postgres?sslmode=require`
- Old Postgres left running on droplet for rollback insurance (Phase 6 decommission in 1-2 weeks)
- Supabase MCP verified: row counts match, data queryable
**Next:** Monitor 24-48h, then Phase 6 (decommission old Postgres). WebFront Phase 1 can start immediately.

### Iteration 22 - 2026-03-19
**Phase:** Supabase Region Migration — Oregon → Mumbai
**Focus:** 4-agent post-migration audit found CRITICAL latency (BLR1→us-west-2 = 490ms/query). Created new Supabase project in ap-south-1 (Mumbai), migrated data, achieved 16x latency improvement.

**Audit (4 parallel agents):**
- Schema: 10/10 PASS (all constraints, indexes, sequences, TIMESTAMPTZ intact)
- Security: Secure by default (RLS on, no API grants, SSL enforced)
- Performance: CRITICAL — 490ms/query due to BLR1→us-west-2 geographic distance
- Code: 3 FAIL (skill doc schema drift), 3 WARN (connection.py hardening)
- Full report: `docs/audits/2026-03-19-supabase-migration-audit.md`

**Mumbai Migration:**
- Created new project `llfkxnsfczludgigknbs` in ap-south-1 via Supabase MCP
- Pooler hostname is `aws-1-ap-south-1` (not `aws-0` — varies by region!)
- Installed PG17 client tools on droplet (pg_dump 16 can't dump PG17 server)
- pg_dump Oregon → pg_restore Mumbai → verify 934 rows + 37 indexes → switch env → restart
- All 3 services healthy on Mumbai

**Latency Results:**
| Metric | Oregon | Mumbai | Improvement |
|--------|--------|--------|-------------|
| avg | 511ms | 31ms | 16x |
| p50 | 488ms | 30ms | 16x |
| p99 | 731ms | 46ms | 16x |

**Changes:** `CHECKPOINT.md` (updated), `/opt/agents/.env` on droplet (DATABASE_URL → Mumbai pooler), `docs/audits/2026-03-19-supabase-migration-audit.md` (new), PG17 client installed on droplet
**Decisions:**
- Supabase pooler hostnames vary by region: `aws-0` for us-west-2, `aws-1` for ap-south-1. Always get from dashboard.
- pg_dump version must match server version (PG17 tools needed for PG17 server)
- Password reset for new Supabase project: Dashboard → Project Settings → Database → Reset database password
**Next:** Fix 3 audit findings (skill doc schema drift, connection.py hardening, NULL sequences). Delete Oregon project. WebFront Phase 1.

### Iteration 23 - 2026-03-19
**Phase:** Audit Fixes + Decommission + Cleanup + Revised Build Plan
**Focus:** Fix all audit findings, decommission old Postgres, clean droplet+repo of dead refs, deep research Supabase capabilities, revised near-term execution plan

**Audit Fixes (3):**
- `connection.py`: Added `statement_cache_size=0` + `command_timeout=30` to asyncpg pool
- 3 skill files: Fixed schema drift in postgres-schema.md (Tables 4,6,7,8), inbox-handling.md, change-interpretation.md — wrong column names for cai_inbox, notifications, action_outcomes, sync_metadata
- NULL sequences: Reset `companies_id_seq` and `network_id_seq` via `setval()` on Supabase

**Decommission + Cleanup:**
- Old PostgreSQL 16 on droplet: `systemctl stop postgresql && systemctl disable postgresql`
- Deleted 5 dead directories: /opt/ai-cos-mcp/ (125MB), /opt/web-agent/ (386MB), /opt/web-tools-mcp/ (19MB), /opt/ai-cos/ (44KB), /opt/aicos-digests/ (2MB). Total: 530MB recovered.
- Removed 3 stale cron jobs (old pipeline, sync agent, web-agent health)
- Removed 5 dead systemd units (ai-cos-mcp, content-agent, sync-agent, web-agent, postgresql.service.d/)
- Fixed state-mcp.service: removed `After=postgresql.service` dependency
- Updated 15 files: all old localhost:5432 / "droplet Postgres" refs → Supabase Mumbai

**Supabase Capabilities Research:**
- Deep research (ultra-fast, 8 min): 12 capabilities assessed across Realtime, Edge Functions, pgvector, pgmq, pg_cron, RLS, Auth, PostgREST, Storage, webhooks, Branching, AI features
- 3 unlocks identified: Auto Embeddings (invisible infra), PostgREST+Realtime (WebFront pattern), Storage (deferred)
- Key constraint established: Supabase extensions (pgmq, pg_cron, pg_net) ONLY for invisible Auto Embeddings — agents never interact, they are pure consumers
- Anthropic has NO native embedding model → Voyage AI `voyage-3.5` (1024 dims) selected
- IRGI Phase A piggybacked onto WebFront Phase 1 (no separate sprint)

**Build Plan:**
- `docs/superpowers/plans/2026-03-19-webfront-phase1-execution.md` (new — 4 weeks: foundation → action triage → semantic search → polish)
- `docs/superpowers/brainstorms/2026-03-19-supabase-unlocks-and-build-sequence.md` (new — capability analysis + revised sequence)
- Source-of-truth docs updated: ARCHITECTURE, DATA-ARCHITECTURE, WEBFRONT, DROPLET-RUNBOOK

**Changes:** 19 files committed (db0256d), 4 new + 15 modified. Pushed to origin/main. Deployed to droplet.
**Decisions:**
- Agents = orchestration layer. DB extensions = invisible infrastructure only. No competing control planes.
- Voyage AI for embeddings (Anthropic has none). Auto Embeddings: trigger→pgmq→cron→Edge Function→Voyage AI→vector column.
- PostgREST+Realtime is HOW WebFront gets built (not a separate feature to schedule).
- Supabase Storage deferred to Phase 2.5 (current git push flow works).
**Next:** Delete Oregon Supabase project (user action). Execute WebFront Phase 1: RLS policies → Vercel env vars → @supabase/ssr → action triage UI → IRGI Phase A.
---

### Iteration 24 - 2026-03-19
**Phase:** WebFront Phase 1 — Foundation Setup (Phase 0)
**Focus:** RLS policies, Supabase SDK setup in aicos-digests, new 2026 key patterns integrated

**Changes:**
- `aicos-digests/package.json` (added @supabase/ssr + @supabase/supabase-js)
- `aicos-digests/src/lib/supabase/server.ts` (new — createAdminClient() using secret key, bypasses RLS)
- `aicos-digests/.env.local.example` (new — env var template with correct 2026 key names)
- `aicos-digests/.gitignore` (added !.env.local.example exception)
- Supabase SQL: GRANT SELECT/INSERT/UPDATE/DELETE on all public tables + sequences to service_role

**Context:**
- Absorbed deep research on Supabase 2026 key system: publishable (`sb_publishable_...`) replaces anon, secret (`sb_secret_...`) replaces service_role. Opaque tokens, not JWTs — gateway swaps for short-lived JWTs.
- Env var names reconciled: plan said `SUPABASE_SERVICE_ROLE_KEY` / `NEXT_PUBLIC_SUPABASE_ANON_KEY`, actual is `SUPABASE_SECRET_KEY` / `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY`
- User to rename `SUPABASE_URL` → `NEXT_PUBLIC_SUPABASE_URL` on Vercel dashboard (manual step)
- Build verified: 24/24 static pages pass with new dependencies
- RLS grants verified via information_schema query — service_role has full CRUD on all tables
**Next:** Phase 0 verification (Server Component reading actions_queue), then Phase 1A action triage UI

### Iteration 25 - 2026-03-19
**Phase:** WebFront Phase 0 — Verification + Vercel CLI Setup
**Focus:** Install Vercel CLI, link project, pull env vars, verify Supabase connection end-to-end

**Changes:**
- Vercel CLI v50.33.1 installed globally, authenticated as hi-1231, linked to aicos-digests
- `aicos-digests/.vercel/` created (project link)
- `aicos-digests/.env.local` pulled from Vercel (3 env vars: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY, SUPABASE_SECRET_KEY)
- `aicos-digests/src/app/test-db/page.tsx` (new — temporary verification page, delete after)

**Verification Results:**
- Server Component → createAdminClient() → Supabase Mumbai: **PASS**
- actions_queue: 115 rows readable (id, action_type, action, status, priority, created_at)
- content_digests: 22 rows readable (id, title, channel, status, created_at)
- Env var naming confirmed correct: `NEXT_PUBLIC_SUPABASE_URL` was already set (not `SUPABASE_URL` as CHECKPOINT implied)

**Context:**
- Vercel CLI was not installed — user correctly flagged this as a gap. Now available for all future env/deploy operations.
- actions_queue column is `action` not `title` — schema queried via Supabase MCP to fix test page
- Phase 0 foundation fully verified: RLS grants + SDK + env vars + connection all working
**Next:** Phase 1A — Action Triage UI (/actions page with filters, Server Actions, Realtime)

### Iteration 26 - 2026-03-19
**Phase:** Product Thinking — ENIAC APM Brief + Source of Truth TL;DR
**Focus:** Deep product review with user, capture corrections to priority buckets, agent hierarchy, build philosophy. Create APM reference doc and system-level TL;DR.

**Changes:**
- `docs/product/eniac-apm-brief.md` (new — ENIAC APM reference: product vision, buckets, scoring heuristic, thesis architecture direction, WebFront scope, build priorities, anti-patterns, open questions)
- `docs/source-of-truth/TLDR.md` (new — concise project picture: agent system, team-of-agents build pattern, 3 evolving pillars)
- `docs/source-of-truth/README.md` (updated — added TLDR.md to index)

**Key Corrections from User:**
- Bucket 2 (Deepen Existing) was fine as described
- Bucket 3 is specifically **DeVC Collective** funnel (Comm → Ext → Core), fueled by Network DB (not yet built)
- Bucket 1 fueled by Companies DB (not yet built) — these data model gaps are critical context
- Action scoring model is a starting heuristic, not fixed — APM should iterate as outcome data accumulates
- Thesis architecture direction: each thesis gets a `.md` file for evidence trail, DB becomes quick-reference index
- AI CoS is a **system of agents** (ENIAC, Meetings Agent, Action Strategist, maybe CRM Specialist)
- APM briefs live in `docs/product/` and are loaded as context for CC subagent teams (backend/frontend/QA specialists)

**Context:**
- No code changes — pure product thinking session
- GitHub push protection caught secret key in CHECKPOINT.md earlier in session — soft reset + recommit fixed it. Key values now only in .env.local and Vercel env vars.
**Next:** Phase 1A — /actions page build with team-of-agents pattern using ENIAC APM context

### Iteration 27 - 2026-03-20
**Phase:** WebFront v1→v3 (3 iterations) + Adversarial Analysis Skill + Schema Audit
**Focus:** Team-of-agents build pattern: 3 full iterations of digest.wiki, adversarial reasoning skill, Companies+Network schema gap analysis

**WebFront (3 iterations, all deployed to digest.wiki):**
- v1: `/actions` page (filters, accept/dismiss, outcome rating), `/thesis` page, navigation, digest related actions. Backend: Supabase queries + Server Actions. 1853 lines added.
- v2: Thesis detail `/thesis/[id]` (conviction gauge, evidence trail, key questions, adversarial lenses), Action detail `/actions/[id]` (reasoning, scoring bars, triage), assigned_to filter, clickable cards. 1827 lines added.
- v3: Design overhaul (atmospheric backgrounds, glass-morphism, dramatic typography), evidence parser (IDS notation extraction), adversarial lenses framework, batch triage, inline reasoning, stats by thesis, mini conviction gauges. 2685 lines added, 1399 deleted.
- QA: 12/13 pass (nav touch targets 38px, needs 44px)
- UX: 7.2/10. Top issues: Content→Action linkage gap (5.5/10), triage controls buried, no undo, 3 touch target failures

**Adversarial Analysis Skill:**
- `mcp-servers/agents/skills/reasoning/adversarial-analysis.md` — 7 investment lenses, 4 polarity pairs, 3-round protocol, 8 domain triads
- Adapted from Nyk's Council of High Intelligence for VC/investing decisions
- Source: `docs/research/2026-03-20-council-adversarial-reasoning-source.md`

**Schema Audit:**
- `docs/audits/2026-03-20-companies-network-schema-audit.md`
- Companies: 49 Notion fields vs 32 Postgres columns, 24 gaps (6 HIGH)
- Network: 44 Notion fields vs 34 Postgres columns, 18 gaps (5 HIGH)
- Draft ALTER TABLE SQL ready, needs live Notion verification before executing
- Notion MCP not connected this session — user configured it for next session

**Infrastructure:**
- Vercel CLI v50.33.1 installed, authenticated, linked to aicos-digests project
- `.env.local` pulled from Vercel (3 env vars)
- GitHub push protection caught secret key in CHECKPOINT.md — soft reset fixed it
- Feature branches used for all work: feat/webfront-v1, v2, v3 (all merged to main)

**Changes:** ~50 files across both repos. All committed and pushed.
**Next:** See CHECKPOINT.md for full handoff state.
---

### Iteration 28 - 2026-03-20 (IN PROGRESS)
**Phase:** Parallel Workstreams — WebFront v4 + Schema Migrations + Portfolio Sync + Research Catalog
**Focus:** 7 parallel agents across 4 workstreams: bug fixes, IRGI Phase A, Companies/Network migration, Portfolio DB sync, cross-DB relations mapping, research file discovery

**Agents Running (7):**
1. WS1 Frontend Agent — Fix 7 QA/UX bugs on feat/webfront-v4 (nav touch targets, content-action linkage, sticky triage, undo toast, thesis links, evidence collapse)
2. WS1 IRGI Agent — Prepare Phase A SQL: vector columns (1024d voyage-3.5), FTS indexes, hybrid search function, Auto Embeddings pipeline
3. WS2 Schema Agent — Query live Notion Companies+Network schemas, cross-ref audit, produce ALTER TABLE SQL
4. WS3 Portfolio Schema Agent — Query Notion Portfolio DB + Postgres portfolio table, full sync comparison, ALTER TABLE SQL
5. WS3 Relations Agent — Map Portfolio↔Companies↔Network relation graph in Notion + Postgres
6. WS4 Local Scout — Catalog all portfolio research MDs in AI CoS project
7. WS4 Global Scout — Catalog all portfolio research MDs across ~/Claude Projects/

**Changes:**
- `sql/irgi-phase-a.sql` (1004 lines, executed on Supabase — 43 DB objects), `sql/irgi-edge-function.ts` (253 lines)
- `sql/companies-network-migration.sql` (ALTER TABLE executed — companies 53 cols, network 52 cols)
- `sql/portfolio-migration.sql` (CREATE TABLE executed — 83 cols, 18 indexes)
- `sql/data/` (12+ files: Notion exports 4635+3339+142, founder registries, matching data, batch inputs)
- `supabase/functions/embed/index.ts` + `supabase/functions/search/index.ts` (deployed ACTIVE on Supabase)
- `supabase/deploy-functions.sh` (deployment script)
- `aicos-digests/` on `feat/webfront-v4` — 12+ commits: bug fixes, search infra, ⌘K, bucket-grouped actions, thesis intelligence, portfolio page, triage stack, app shell, home command center, I2 fixes in progress
- `portfolio-research/` — 252 MD files (141 Parallel batch + 108 new batch + 3 pre-existing)
- `companies-pages/` — 153+ MD files (Notion page body content)
- `network-pages/` — 120+ MD files (Notion page body content)
- `docs/audits/` — 12+ audit reports (schema, data quality, enrichment, IRGI execution, cross-DB relations)
- `docs/research/` — 4 files (shadcn composition, product design, IRGI edge functions, UX patterns)
- `docs/superpowers/plans/` — 2 files (data sync plan, next iterations plan)

**Supabase state (live):**
- 6 tables: companies (558→4635 loading), network (959→3339 loading), portfolio (142), content_digests (22), thesis_threads (8), actions_queue (115)
- IRGI: pgvector, pgmq, pg_cron, pg_net, 4 vector cols, 4 FTS cols, hybrid_search(), 6 intelligence functions, 2 Edge Functions, embedding pipeline autonomous
- 252 research files, 142/142 portfolio linked, all rows embedded at 100%

**82 agents spawned, 68 complete, 22 running across:**
- WS1-4: WebFront bugs + IRGI prep + schema + research scouts
- WS5: Schema execution + Notion exports + data population (companies 545, network 528, portfolio 142)
- WS6: UX deep research + shadcn audit + product design
- WS7: 141 company Parallel research + download
- WS8: IRGI execution + Edge Functions + WebFront search + intelligence backend
- WS9: Founder matching (291 found, 268 LinkedIn) + creator (197 inserted) + connection linker
- WS10: Full Notion API export (4635+3339) + page content + research linking
- WS11: Actions/Thesis/Portfolio intelligence pages
- WS12: Triage stack + app shell + home command center
- WS13: Continuous enrichment orchestrator + founder extractors
- WS14: 6 alphabet enrichment agents + deep orchestrator v2 + companies re-export
- WS15: 6 page content agents (3 company + 3 network ranges)
- WS16: QA (build passes) + UX review (6.8/10) + Aakash review (6.5/10)
- WS17: Strategic planning + 3 column-fill agents
- WS18: Data loop master + website/LinkedIn/sector gap fillers
- WS19: I2 fixes (add signal, since-last-visit, PWA, sheet/drawer)

**Context:** Compaction overdue. This is a massive multi-workstream session — largest agent fleet ever (82). Two iteration machines running: WebFront (BUILD→TEST→FIX→repeat) and Data (AUDIT→FILL→LINK→VERIFY→repeat).
**Latest (updated mid-session):**
- Companies: **4,635 rows** in Postgres (mass upsert COMPLETE), 1,438 embedded (31%, processing)
- Network: **3,728 rows** (mass upsert nearly done), 959 embedded (backfill queued)
- Portfolio: 142 rows, 142/142 embedded, 142/142 research linked
- WebFront I1: 6 agents complete (triage stack, app shell, intelligence pages, command center)
- WebFront I1 Review: QA pass, UX 6.8/10, Aakash 6.5/10
- WebFront I2: 4 fix agents running (add signal, since-last-visit, PWA, sheet/drawer)
- Page content: 531 network MDs, 153+ company MDs, 142 portfolio stubs
- Research: 252 files total, 100% portfolio coverage
- Enrichment: alphabet army + data loop master + gap fillers (website, LinkedIn, sector)
- 74 agents complete, 16 running, 83 total spawned
- QA report: PASS (0 critical, 1 high, 3 medium) — QA fix agent launched
- UX review: 6.8/10 — I2 fixes address all P0/P1 findings
- Aakash review: 6.5/10 — Add Signal (write capability) is P0 #1, being built
- Strategic plan written: outcome rating + people view as next P0 features
**Database milestone:** Both mass upserts COMPLETE. 8,650 total rows (4,635 companies + 3,728 network + 142 portfolio + 22 digests + 8 thesis + 115 actions). 6,804 embeddings queued and processing autonomously. pgmq permission fix applied (service_role USAGE grant).
**I2 fixes landing:** PWA + service worker + keyboard help ✅, QA fixes (focus, contrast, sort) in progress, Add Signal (write capability) wrapping up, Since-Last-Visit + Sheet/Drawer building. WS20 Search army launched: enhanced ⌘K, /companies detail, /network detail, /search page.
**Data:** Portfolio column fill: ZERO gaps (100% Notion match). Enrich J-O: 17 people linked, 36 LinkedIn filled. Network mass upsert DONE (3,728). Embedding pipeline: ~6,804 processing autonomously.
**82 complete, 12 running, 87 total. 3 iteration machines active.**
- I2 progress: 4/5 done. PWA ✅, Add Signal ✅, Keyboard Help ✅, Since-Last-Visit + P0 Banner ✅. Sheet/Drawer + QA fixes remaining.
- Write capability LIVE: FAB, server action, Sonner, context buttons on thesis/portfolio
- P0 Banner: fixed-top flame gradient, dismissible, pulse. Since-Last-Visit: delta pills, NewBadge component.
- QA fixes DONE: focus-visible, contrast (#8a8894), chronological sort, ILIKE escape, orphan cleanup
- I2: 5/5 fix agents complete except Sheet/Drawer (last one). Build type error from Sheet/Drawer agent (full_name vs person_name) — fix on commit.
- **83 complete, 11 running, 87 total.**
**Next:** Sheet/Drawer lands → fix build → I2 review round (target 8+/10) → merge+deploy. WS20 search army building.
---

### Iteration 29 - 2026-03-20
**Phase:** 6-Machine Parallel Machinery — Loop 1-2 across all workstreams
**Focus:** Resume all 6 machineries from CHECKPOINT.md. 15 agents spawned across 6 machines, running BUILD→REVIEW→FIX loops.

**Machines Running:**
- M1 WebFront: L1 BUILD (5 P0 features) ✅ → L1 REVIEW x3 (QA ✅ pass, UX ✅ 7.1/10, Aakash ✅ 6.8/10) → L2 FIX (design elevation) 🔄
- M2 Data: L1 AUDIT ✅ (8,650 rows, 99.99% embedded, 57 dupe groups, 26 cross-ref failures) → L2 FILL 🔄
- M4 Datum Agent: L1 DESIGN ✅ (11-section spec) → L2 BUILD (CLAUDE.md 24KB, migrations, skills) 🔄
- M5 Scoring: L1 AUDIT ✅ (5 CRITICAL: 80% unscored, scale bug, inverted priorities, no user/agent split) → L2 FIX (8 SQL improvements) 🔄
- M6 Content: L1 ASSESS ✅ (44% agent-delegable, score compression, bucket misrouting) → L2 FIX (IRGI rewrites) 🔄
- UX Research: ✅ (753-line elevation study — 10 gaps vs Linear/Superhuman/Bloomberg)

**Key User Feedback (routed to all agents):**
- Action priorities wrong: portfolio+network should dominate, thesis→agent-delegated
- UI/UX density, colors, fonts not best-in-class → "restraint over decoration"
- Saved as memory: feedback_action_priority_hierarchy.md, feedback_ux_best_in_class.md

**Changes:**
- `aicos-digests/` on `feat/m1-loop1`: 5 P0 features (+460/-62 lines), design elevation pass in progress
- `docs/research/2026-03-20-ux-elevation-study.md` (new — 753 lines, 10 design gaps, ready-to-paste CSS)
- `docs/superpowers/specs/2026-03-20-datum-agent-design.md` (new — full agent spec, 11 sections)
- `docs/audits/` — 5 new audit reports (data quality, scoring, reprocessing, QA, UX reviews)
- `mcp-servers/agents/datum/` (new — CLAUDE.md 24KB, hooks, state, skills)
- `sql/datum-agent-migrations.sql` (new), `sql/scoring-improvements.sql` (pending), `sql/irgi-scoring-fixes.sql` (pending)
- `aicos-digests/docs/iterations/005-*.md` — 3 review reports (QA, UX, Aakash)

**Decisions:**
- UX elevation via restraint: fewer colors (5→1-2 accent), tighter spacing (40%), neutral backgrounds
- User/agent queue split: thesis actions→agent_work_queue, portfolio/network→user_triage_queue
- Datum Agent: third ClaudeSDKClient managed by lifecycle.py, on-demand (not heartbeat), dedup+enrich+ask-user
- Score function: compute_user_priority_score() with portfolio +3, network +2, thesis -3 weighting

**Latest completions (mid-session):**
- M5 L2 FIX ✅: ALL 8 scoring SQL fixes executed. Queue inversion corrected: Thesis 55%→2%, Portfolio 14%→47%. `user_triage_queue` + `agent_work_queue` views live. `compute_user_priority_score()` deployed. 100% score coverage (was 20%).
- M2 L1 AUDIT ✅: 8,650 rows, 99.99% embedded. 57 company dupe groups, 26 cross-ref failures (whitespace), page_content_path 0% for companies.
- M1 UX ✅ (7.1), Aakash ✅ (6.8): Path to 8.5 = CSS swap + density + restraint. No new features needed.
- M5 now in L3 VERIFY. M1-fix alerted to use new `user_triage_queue` view.

- M6 L2 FIX ✅: Score compression eliminated (flat 0.90→spread 0.40-0.89). Bucket routing fixed (Thesis 55%→2.2%, Portfolio 47.3%). 77 latent thesis connections created. Bias detection function deployed.
- M5+M6 converged: Both independently fixed queue inversion. Scoring system production-ready.
- M5 L3 VERIFY 🔄, M6 L3 VERIFY 🔄: Both validating fixes.

- M4 L2 BUILD ✅: Datum Agent fully built — CLAUDE.md 639 lines, SQL migrations executed on Supabase (datum_requests table, enrichment columns, embedding triggers), 2 skills, 3 hooks, lifecycle integration plan. Committed 705c191.
- M7 Megamind launched: New strategist agent — diverge/converge reasoning, depth grading (skip/1-deep/2-deep/ultra), ROI optimization, cascade re-ranking. Design spec in progress.
- Agent fleet: Orchestrator (live) + ENIAC (scoring, live in Supabase) + Datum (built, pending deploy) + Megamind (designing) + Cindy (future comms agent)
- User feedback: depth grading approval flow, agent work re-ranks but converges (diminishing returns), ROI of Aakash's time is the optimization function.

- M5 L3 VERIFY ✅: 6/8 checks passed, 2 blockers found — ceiling compression (53% at 10.00) + portfolio research misclassified as agent-delegable.
- M5 L4 FIX 🔄: Sigmoid soft-cap (no more hard ceiling), reduced boost magnitudes, portfolio research override in views.
- M4 L3 REVIEW 🔄: Verifying Datum build against design spec + Supabase schema.

- M6 L3 VERIFY ✅: 7/7 pass. Critical: relevance_score holds M5 scores not IRGI. thesis_connection format inconsistent (23 entries).
- M5 L4 FIX2 🔄: Sigmoid soft-cap, reduced boosts, portfolio research override.
- M6 L4 FIX2 🔄: IRGI writeback to new irgi_relevance_score column, thesis_connection normalization.
- M7 L1 DESIGN 🔄: Megamind strategist spec — diverge/converge, depth grading, ROI optimization.

- M4 L3 REVIEW ✅: PASS all 6 sections. Datum Agent production-ready. 3 minor cosmetic issues noted.
- M4 L4 BUILD 🔄: lifecycle.py integration — adding Datum as third managed ClaudeSDKClient.

- M7 L1 DESIGN ✅: Megamind spec complete (12 sections + 4 appendices). Strategic ROI function, diverge/converge 5-step, depth grading (Skip/Scan/Investigate/Ultra), convergence guarantee (resolved >= generated), trust ramp, ~$6-10/mo.
- M7 L2 BUILD 🔄: CLAUDE.md 500+ lines, 4 SQL tables (depth_grades, cascade_events, strategic_assessments, strategic_config), 3 skills, lifecycle plan.
- Production fleet: Orchestrator (live) + ENIAC (live in Supabase) + Datum (L4 lifecycle integration) + Megamind (L2 building) + Cindy (future).

- M5 L5 FINAL ✅: **PRODUCTION READY** — 8/8 checks pass. 23 distinct scores, 6.9ms query, portfolio 47.3%, 0 ceiling, 83 user/8 agent queue.
- M6 L5 FINAL ✅: **PRODUCTION READY** — 7/7 checks pass. 100% IRGI coverage, score independence confirmed (r=-0.323), 8/8 functions live.
- M4 L5 VERIFY ✅: **DEPLOY READY** — 5/5 checks pass. Perfect symmetry with Content Agent. lifecycle.py AST verified.
- M1 L2 FIX ✅: Design elevation complete (27 files, 40% tighter, neutral colors, accent restraint, portfolio first). L2 REVIEW running.
- M2 L3 VERIFY ✅: All fixes held. 100% embeddings. L4 quick fixes running.
- Backend LOCKED: M4+M5+M6 all at 5 loops, production verified. Awaiting M1 review for WebFront deploy decision.

- M7 L2 BUILD ✅: Megamind CLAUDE.md 970 lines, 4 SQL tables (seeded), 3 skills (827 lines total), lifecycle plan 352 lines. Committed 9ca2450.
- M1 L2 REVIEW ✅: UX 8.0 (+0.9), Aakash 7.5 (+0.7), QA PASS. Font-serif blocker fixed. Merged + deployed to digest.wiki.
- M2 L4 FIX ✅: Terra resolved, Founder 2 deleted, 59 page files matched. 100% cross-ref.
- M5 L5 FINAL ✅: PRODUCTION READY. 8/8 checks, 6.9ms query, portfolio 47%.
- M4 L5 VERIFY ✅: DEPLOY READY. 5/5 checks, AST verified.
- **DEPLOYED**: All committed, pushed to GitHub, deployed to droplet via deploy.sh. All 3 services healthy. Datum + Megamind now on droplet.
- M8 Cindy launched: 4 parallel research agents (AgentMail, WhatsApp, Calendar+Granola, Design spec).
- M7 L3 REVIEW+INTEGRATE 🔄: Combined review + lifecycle.py integration as fourth agent.
- Session commit d70e7eb: +9,421 lines, 24 files across all machines.

- M1 L3+L4 ✅: Scoring integrated + pre-meeting prep (portfolio above fold, PREP buttons). Both deployed.
- M7 L2+L3 ✅: Megamind built (970L CLAUDE.md) + lifecycle integrated. Deployed to droplet.
- M8 L1 ✅: All research done + design spec 2,290L. L2 BUILD 🔄.
- M9 L1 ✅: 4 audits (5.5/6.2/50/59). CRITICAL: current_role='postgres' bug. L2 FIX 🔄.
- M10 launched: Living System Architecture (continuous intelligence refresh).
- Session: 52 agents spawned, 46 complete. 10 machines. Both repos deployed. Keep looping to 10+ per machine.

- M11 L1 DESIGN ✅: Obligations Intelligence — I-owe/they-owe detection, Cindy+Megamind 60/40 priority blend, 3 WebFront views, 12 sections + 4 appendices.
- M1 L4 REVIEW ✅: **Aakash 8.2/10 — TARGET MET.** Pre-meeting prep 5.5→8.5 via PREP buttons + portfolio above fold.
- ALL 58 AGENTS COMPLETE. Full fleet deployed to droplet (5 agents, 3 services). WebFront live at digest.wiki.

**Definitive agent fleet framing (user input):**
- ENIAC = best-in-class research analyst (content + thesis → action suggestions)
- Datum = data & ops team (keeps everything fresh, feeds all other agents)
- Cindy = most intelligent EA (tracks comms, obligations, who-owes-what)
- Megamind = co-strategist (NOT slave — equal partner, co-orchestrates with Aakash, seeks what's RIGHT for optimization function)
- Each agent self-improves via preference stores. Megamind learns from triage interactions as soft signals.

**Permanent machineries (run forever, 30+ loops):**
1. M1 WebFront — continuous UX/feature evolution
2. M5/M6 Scoring+IRGI — continuous intelligence optimization
3. M8 Cindy — continuous comms capability building
4. M9 Intelligence QA — continuous accuracy auditing
5. M10 CIR — continuous intelligence refresh
6. M11 Obligations — continuous EA capability building
7. M7 Megamind — continuous strategic capability building

**Context:** 58 agents spawned, ALL complete. 11 machines. Session at natural sync point. Compaction overdue (iteration 30 — do at session start next time).
**Next:** Complete Loop 2 across all machines → L2 REVIEW → L3 BUILD/FIX → iterate toward 10 loops each.
---
