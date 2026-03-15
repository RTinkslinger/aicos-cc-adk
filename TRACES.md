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
**Next:** Task 4.3 — Deploy to droplet and cutover. Requires SSH session.

---
