# Build Traces

## Project Summary

Milestone 1 established the Claude Code era foundation: fixed Content Digest/Actions Queue data completeness (20+ params), implemented the AI-managed Thesis Tracker conviction engine (6-level spectrum, key questions lifecycle, autonomous thread creation), completed Cowork→CC migration (cleanup, archiving, architecture/vision docs evolved to v0.3/v5). Milestone 2 implemented full Data Sovereignty: public MCP endpoint (Cloudflare Tunnel, 17 tools), Postgres write-ahead for thesis + actions, bidirectional sync with field-level ownership, change detection with auto-action generation, SyncAgent on cron. Key decisions: write-ahead pattern, Actions field ownership (Status=droplet, Outcome=Notion), `date:` shorthand incompatible with some data_source_id DBs, Companies/Network/Portfolio sync deferred.

## Milestone Index

| # | Iterations | Focus | Key Decisions |
|---|------------|-------|---------------|
| 1 | 1-3 | Infrastructure Hardening + Thesis Tracker + Cowork→CC Migration | AI-managed conviction engine, conviction spectrum, key questions as page blocks, claude-ai-sync/ folder, architecture doc versioning strategy |
| 2 | 1-3 | Data Sovereignty — Public MCP + Postgres Backing + Sync + QA | Write-ahead pattern, field-level ownership, Cloudflare Tunnel endpoint, action generation from changes, 17 MCP tools QA'd |

*Full details: `traces/archive/milestone-N.md`*

<!-- end-header -->

---

## Current Work (Milestone 3 in progress)

### Iteration 1 - 2026-03-15
**Phase:** Web Tools MCP Server — Build & Deploy
**Focus:** Scaffold, build, and deploy web-tools-mcp with 5 tools

**Changes:** `mcp-servers/web-tools-mcp/server.py` (new — 5 tools), `pyproject.toml`, `deploy.sh`, `tests/test_tools.py`, `.mcp.json` (added endpoint), `LEARNINGS.md` (3 patterns)
**Infrastructure:** systemd service on port 8001, Cloudflare Tunnel at web.3niac.com, Google Chrome 146 installed, dpkg /etc/environment fix
**Decisions:**
- Jina search (s.jina.ai) requires API key → removed, Firecrawl-only search
- cloudflared reads /etc/cloudflared/config.yml (not ~/.cloudflared/) when running as systemd service
- /etc/environment had stale `PATH=/root/.deno/bin` breaking all dpkg — fixed
**Next:** Cookie sync infra (Chunk 6), integration test with auth URLs (Chunk 7), reference docs deploy (Chunk 8)

### Iteration 2 - 2026-03-15
**Phase:** Web Tools MCP Server — Cookie Sync + SPA Fix
**Focus:** Cookie pipeline Mac→droplet, fix empty content on JS-heavy SPAs

**Changes:** `server.py` (added `wait_after_ms` param to web_browse), `~/.ai-cos/scripts/cookie-sync.sh` (deployed + fixed rsync flag + root@ prefix + added x.com/substack.com domains), `.mcp.json` (already done iter 1), `LEARNINGS.md` (2 new patterns)
**Infrastructure:** Firecrawl .env configured, browser_cookie3 installed on Mac, daily cron at 6am, /opt/ai-cos/cookies/ on droplet with 5 domain cookie files
**Decisions:**
- SPA empty content root cause: `networkidle` fires before React hydration → added `wait_after_ms=3000` default delay
- macOS rsync lacks `--chmod` flag → removed from cookie-sync.sh
- Tailscale SSH requires explicit `root@` in rsync target
**Next:** Reference docs deploy (Chunk 8), commit all work, update plan

### Iteration 3 - 2026-03-15
**Phase:** Research — Agent SDK + Web Intelligence Mastery
**Focus:** Deep research (6 ultra reports) on Agent SDK production patterns, multi-agent orchestration, MCP integration, SPA/PWA extraction, agent adaptation, and anti-detection

**Changes:** `docs/research/2026-03-15-agent-web-mastery/` (7 new files — index + 6 report summaries)
**Decisions:**
- Architecture clarified: web-tools-mcp = Layer 3 (hands), WebAgent (Agent SDK) = Layer 4 (brain). Agent-as-MCP-tool pattern for cross-surface access.
- ClaudeSDKClient (not query()) for long-lived agents. SDK MCP for in-process tools, external MCP for remote.
- Kill static waits → readiness ladder: deterministic selector > MutationObserver > LCP > framework markers > time fallback
- Strategy cache + UCB bandit for adaptive site learning. MCP Strategy Registry for cross-agent knowledge sharing.
**Next:** WebAgent build plan (Agent SDK), then commit all web-tools-mcp work

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
---
