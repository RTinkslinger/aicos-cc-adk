# Exhaustive Code Review — 2026-03-17
*6 parallel review agents, 202 active files scanned*

## Summary

| Area | Critical | Important | Minor/Suggestions |
|------|----------|-----------|-------------------|
| Orchestrator + lifecycle | 0 | 4 | 6 |
| State MCP | 2 | 5 | 4 |
| Web Tools MCP | 4 | 8 | 7 |
| Deploy + infra | 4 | 7 | 5 |
| Skills + docs coherence | 5 | 7 | 6 |
| Root config + scripts | 4 | 10 | 8 |
| **TOTAL** | **19** | **41** | **36** |

---

## Critical Findings (19)

### Skills + Docs Coherence (5 critical)

**C-SD1. `cai_inbox` table schema: 3-way mismatch**
- postgres-schema skill: `message_type`, `priority`, `retry_count`, `error`
- DATA-ARCHITECTURE.md: `content`, `processed`, `created_at`
- Actual code (state/db/inbox.py + SQL migration): `type`, `content`, `metadata`, `processed`, `processed_at`, `created_at`
- inbox-handling skill queries `message_type` and `priority` — columns that don't exist
- **Impact:** Content Agent will write broken SQL at runtime

**C-SD2. `notifications` table schema: 3-way mismatch**
- postgres-schema skill: `notification_type`, `title`, `body`, `source_agent`
- DATA-ARCHITECTURE.md: `content`, `type`, `read`, `created_at`
- Actual code (state/db/notifications.py + SQL migration): `source`, `type`, `content`, `metadata`, `read`, `created_at`
- change-interpretation skill uses wrong column names in example INSERTs
- Content Agent CLAUDE.md omits required `source` column

**C-SD3. `content_digests` still lists dropped columns in skill**
- postgres-schema skill shows `notion_synced`, `last_synced_at`, `notion_page_id`
- These were dropped in v3 (TRACES iteration 12)
- Publishing skill references `notion_synced=FALSE`

**C-SD4. `content_digests.status` values inconsistent**
- postgres-schema skill + DATA-ARCHITECTURE.md: `pending`
- Content Agent CLAUDE.md + actual usage: `queued`
- Pipeline won't process items if wrong status value written

**C-SD5. `thesis_threads` column name: `name` vs `thread_name`**
- Content Agent CLAUDE.md queries `SELECT name, conviction, status...`
- Actual DB column is `thread_name` (confirmed in thesis.py + TRACES iteration 9)

### Web Tools MCP (4 critical)

**C-WEB1. Task store memory leak — no cleanup of completed tasks**
- File: `web/task_store.py`
- `_tasks` dict grows unboundedly. No TTL, no eviction, no size cap.

**C-WEB2. `asyncio.create_task` fire-and-forget without reference**
- File: `web/server.py:121`
- Task can be garbage collected before completion. No cancellation on shutdown.

**C-WEB3. `datetime.utcnow()` deprecated**
- File: `web/task_store.py:19,46,55`
- Deprecated since Python 3.12. Use `datetime.now(timezone.utc)`.

**C-WEB4. Browser `evaluate` accepts arbitrary JS from MCP callers**
- File: `web/lib/browser.py:197-203`
- No validation on JS code. Acceptable if trust model is documented.

### Deploy + Infra (4 critical)

**C-DEP1. Main rsync has no `--delete` — deleted files persist on droplet**
- File: `deploy.sh:21-28`
- Old code files accumulate silently on droplet. Drift risk.

**C-DEP2. deploy.sh runs from wrong working directory if invoked from project root**
- File: `deploy.sh:21`
- Uses relative paths but no `cd "$(dirname "$0")"` guard.

**C-DEP3. Stale v1 `systemd/` + `cron/` dirs still in repo, synced then deleted every deploy**
- Files: `systemd/install.sh`, `cron/health_check.sh`
- v1 install.sh is a footgun if accidentally run on droplet.

**C-DEP4. `scripts/preflight.sh` references old v1 service names, dead in v3**
- Checks `sync-agent`, `web-agent`, `content-agent` — none exist in v3.

### Root Config + Scripts (4 critical)

**C-ROOT1. CLAUDE.md: SyncAgent described as "live" in 3 places, "disabled" in 1**
- Lines 215, 220, 225 say live. Line 231 says disabled. Every CC session gets contradiction.

**C-ROOT2. CLAUDE.md: Source-of-truth file count wrong (says 9, actual 10+README)**
- Line 21. PRIOR-ART.md was added, DROPLET-RUNBOOK moved in.

**C-ROOT3. .mcp.json uses Cloudflare Tunnel URLs, MCP-TOOLS-INVENTORY says Tailscale**
- Actual: `https://mcp.3niac.com/mcp`. Doc says: `http://aicos-droplet:8000/mcp`.

**C-ROOT4. CLAUDE.md: "17 MCP tools" count is stale**
- Line 226. Actual: 5 (State) + 11 (Web) = 16 tools.

### State MCP (2 critical)

**C-STATE1. Test fixture column names wrong (`name` vs `thread_name`)**
- File: `state/tests/test_state_mcp.py:37,43`
- Tests pass but don't validate actual data contract.

**C-STATE2. Connection pool race condition on concurrent `get_pool()`**
- File: `state/db/connection.py:16-23`
- No lock on check-then-create pattern. Can leak pool on startup.

---

## Important Findings (41)

### Orchestrator + Lifecycle (4)

| # | Issue | File |
|---|-------|------|
| I-ORC1 | Race condition: restart while background reader active | lifecycle.py:374-380, 452-454 |
| I-ORC2 | Contradictory watch_list.json ownership (3 conflicting instructions) | content/CLAUDE.md sections 4, 7, 15 |
| I-ORC3 | Fire-and-forget asyncio.create_task not tracked/cancelled on shutdown | lifecycle.py:257 |
| I-ORC4 | Manifest read-modify-write not guarded against concurrent async access | lifecycle.py:122-149 |

### State MCP (5)

| # | Issue | File |
|---|-------|------|
| I-STATE1 | Missing DATABASE_URL produces unhelpful KeyError | state/db/connection.py:19 |
| I-STATE2 | Direction validation after pool acquisition (wasted connection) | state/db/thesis.py:56-117 |
| I-STATE3 | No input length validation on text fields | state/server.py (all write tools) |
| I-STATE4 | post_message hardcodes type to "message" | state/server.py:166 |
| I-STATE5 | get_state tool doesn't expose inbox section (docs say it does) | state/server.py:46-85 |

### Web Tools MCP (8)

| # | Issue | File |
|---|-------|------|
| I-WEB1 | input_validation allows empty URL scheme (`//evil.com`) | web/hooks.py:102 |
| I-WEB2 | Tests reference removed/renamed functions (web_screenshot, web_task) | web/tests/test_tools.py:113,234 |
| I-WEB3 | Strategy record_outcome always passes latency_ms=0 | web/hooks.py:170 |
| I-WEB4 | health_check tool returns "web-agent", GET endpoint returns "web-tools-mcp" | web/tools.py:153 |
| I-WEB5 | New httpx.AsyncClient per scrape/search call (no connection reuse) | web/lib/scrape.py:27,55 + search.py:26 |
| I-WEB6 | `_flatten_a11y` is dead code | web/lib/browser.py:292-303 |
| I-WEB7 | Strategy DB init race on concurrent first access | web/lib/strategy.py |
| I-WEB8 | No timeout cleanup for browser contexts on agent task cancellation | web/agent.py:107 |

### Deploy + Infra (7)

| # | Issue | File |
|---|-------|------|
| I-DEP1 | EnvironmentFile dash prefix — missing .env silently ignored | infra/*.service |
| I-DEP2 | ExecStopPost pkill chrome kills ALL chrome on system | infra/web-tools-mcp.service:15 |
| I-DEP3 | state-mcp.service missing StandardOutput/StandardError directives | infra/state-mcp.service |
| I-DEP4 | health_check.sh cron not installed by deploy.sh | infra/health_check.sh |
| I-DEP5 | --delete on skills/ and .claude/agents/ but not on main code rsync | deploy.sh:50-52 vs 21 |
| I-DEP6 | No failure handling for orchestrator start (just sleep 5) | deploy.sh:107-109 |
| I-DEP7 | cleanup.sh doesn't remove old units from /etc/systemd/system/ | deploy/cleanup.sh:25-27 |

### Skills + Docs Coherence (7)

| # | Issue | File |
|---|-------|------|
| I-SD1 | DATA-ARCHITECTURE.md lists sync_queue table (stale v1) | DATA-ARCHITECTURE.md Table 7 |
| I-SD2 | sync_metadata schema: 3 different versions across 3 files | postgres-schema.md, DATA-ARCHITECTURE.md, v2.2-migrations.sql |
| I-SD3 | action_outcomes schema: skill vs DATA-ARCHITECTURE fundamentally different designs | postgres-schema.md vs DATA-ARCHITECTURE.md |
| I-SD4 | actions_queue schema: type mismatch (INTEGER vs REAL) + missing columns | postgres-schema.md vs DATA-ARCHITECTURE.md |
| I-SD5 | Content Agent CLAUDE.md watch_list ownership contradicts inbox-handling skill | content/CLAUDE.md vs inbox-handling.md |
| I-SD6 | Scoring model: ARCHITECTURE says 7-factor, implementation is 5-factor | ARCHITECTURE.md vs scoring.md |
| I-SD7 | Sync Agent references in all 3 sync skills without disabled note | sync skills |

### Root Config + Scripts (10)

| # | Issue | File |
|---|-------|------|
| I-ROOT1 | CONTEXT.md references /opt/ai-cos-mcp/ paths (stale v1) | CONTEXT.md:415 |
| I-ROOT2 | CONTEXT.md last updated 2026-03-07 — 10 days of architecture changes | CONTEXT.md:2 |
| I-ROOT3 | claude-ai-sync/ describes v2 architecture (17 tools, SyncAgent live) | claude-ai-sync/memory-entries.md |
| I-ROOT4 | state.json: stale tasks, architecture, decisions | .claude/sync/state.json |
| I-ROOT5 | project.json: stale description | .claude/sync/project.json |
| I-ROOT6 | settings.local.json: web-tools-mcp not in enabledMcpjsonServers | .claude/settings.local.json:44-46 |
| I-ROOT7 | Scripts have pervasive "Cowork" references | scripts/*.py, scripts/*.sh |
| I-ROOT8 | publish_digest.py: wrong URL (aicos-digests.vercel.app vs digest.wiki) | scripts/publish_digest.py:157 |
| I-ROOT9 | publish_digest.py + auto_push.sh: wrong project directory name | scripts/publish_digest.py:36, auto_push.sh:13 |
| I-ROOT10 | agents/ planned path in CLAUDE.md doesn't exist | CLAUDE.md:104-107 |

---

## Minor / Suggestions (36)

### Orchestrator (6)
- Inconsistent COMPACT_NOW detection between agents
- Redundant datetime import inside has_work()
- subprocess imported inside function
- ClientState uses class variables as instance state
- Live log files grow unbounded
- ACK protocol implies orchestrator reads it, but it doesn't

### State MCP (4)
- No test for post_message/create_thesis_thread/update_thesis server tools
- /health GET doesn't check DB (liveness only, not readiness)
- Duplicate RETURNING clauses in thesis.py (5x)
- Starlette import inside request handler

### Web Tools MCP (7)
- No max concurrent tasks guard on web_task_submit
- Monitor module is a stub (watch_url does nothing)
- Stealth personas could be richer (timezone, locale)
- cookie_status reads entire cookie files without size guard
- Test coverage gaps (task_store, quality, strategy, sessions, agent)
- Consider __slots__ on WebTask dataclass
- VTT dedup is well-done (positive note)

### Deploy (5)
- live-*.sh have hardcoded /opt/agents paths (fine for droplet)
- view-logs.py swallows all exceptions
- DROPLET-MANIFEST minor inconsistency on cookies/ ownership
- Cleanup doesn't remove stale units from /etc/systemd/system/
- Consider deploy version marker file

### Skills + Docs (6)
- postgres-schema "8 tables" count outdated
- key_questions vs key_question_summary in thesis-reasoning skill
- Publishing skill stale Sync Agent post-publishing flow
- content_digests schema missing status + slug dedup columns in skill
- DigestData net_newness schema differs (flat string vs object)
- Notion patterns skill has Python examples (v2 era)

### Root Config (8)
- stop-check.sh ROADMAP.md staleness check likely a no-op
- sequential-files.txt only has CLAUDE.md (missing CONTEXT.md)
- youtube_extractor.py outputs to archived queue/ directory
- content_digest_pdf.py imports reportlab without guard
- agents/ planned path section in CLAUDE.md stale
- dedup_utils.py datetime.utcnow() deprecated
- action_scorer.py missing 2 of 7 documented factors (intentional simplification)
- Cowork references in subagent-prompts/

---

## Positive Highlights

- **lifecycle.py pre-check idle optimization** — $0 cost when idle, biggest cost saver
- **Fire-and-forget bridge pattern** — orchestrator doesn't block on content analysis
- **Hook design** — clean, consistent, robust shell scripts with graceful degradation
- **Dual-layer web tool design** — FastMCP (free) + SDK agent (reasoning) is architecturally sound
- **UCB bandit strategy learning** — zero-human-intervention quality improvement
- **Readiness ladder** in browser.py — handles real-world SPA diversity
- **Parameterized queries throughout** — zero SQL injection risk in State MCP
- **CLAUDE.md files for agents** — among the best agent system prompts reviewed
- **Atomic manifest writes** — crash-safe via tmp+rename pattern
