# Checkpoint
*Written: 2026-03-16 04:00 IST*

## Current Task
Architecture v2.2: Full build complete. All 7 chunks implemented. Ready for deploy + testing.

## Progress
- [x] Three-agent v1 build (63 files, deployed — will be replaced)
- [x] Code audit v1 (25/25 resolved — superseded by v2.2)
- [x] Architecture v2.2 brainstorming (deep, 10+ rounds of clarification)
- [x] v2.2 design spec written: `docs/superpowers/specs/2026-03-15-architecture-v2.2-design.md`
- [x] Phase 1: Infrastructure (SQL migrations, subagent defs, systemd units, deploy.sh)
- [x] Phase 2: State MCP (5 tools, asyncpg, 9 files, 23 tests)
- [x] Phase 3: Web Tools MCP (async task pattern, 3 new external tools, restructured)
- [x] Phase 4: Skills (14 skills extracted, 3,010 lines of agent intelligence)
- [x] Phase 5: Content Agent (runner.py + 532-line system prompt)
- [x] Phase 6: Sync Agent (runner.py + 388-line system prompt)
- [ ] Phase 7: Integration (deploy to droplet, run migrations, E2E testing)

## What Was Built (41 files)

### New files (34)
- `sql/v2.2-migrations.sql` — 3 new tables + notion_synced columns
- `state/` — 9 files (server.py, db/{connection,thesis,inbox,notifications}.py, tests)
- `skills/` — 14 markdown files (5 web, 5 content, 3 sync, 1 data)
- `.claude/agents/` — 2 subagent definitions (web-researcher, content-worker)
- `infra/` — 4 systemd units + health_check.sh
- `web/task_store.py` — async task state management
- `content/runner.py` — asyncio timer + query() launcher
- `sync/runner.py` — asyncio timer + query() launcher

### Modified files (7)
- `web/server.py` — async task tools, external wrappers, renamed to web-tools-mcp
- `web/tools.py` — removed old web_task, added check_strategy/manage_session/validate
- `web/agent.py` — added setting_sources=["project"]
- `content/system_prompt.md` — complete v2.2 rewrite (532 lines)
- `sync/system_prompt.md` — complete v2.2 rewrite (388 lines)
- `deploy.sh` — rewritten for 4 v2.2 services
- `pyproject.toml` — added asyncpg, state/tests

## Next Steps (for new/continued session)
1. Read this CHECKPOINT.md
2. Read `docs/v2.2-build-log.md` for testing checklists
3. Deploy to droplet: `cd mcp-servers/agents && ./deploy.sh`
4. Run SQL migrations: `ssh root@aicos-droplet "psql $DATABASE_URL < /opt/agents/sql/v2.2-migrations.sql"`
5. Verify all 4 services: `systemctl status state-mcp web-tools-mcp content-agent sync-agent`
6. Run E2E tests per build log checklists
7. Bug fix any issues found during testing

## Key Notes for Testing
- `permission_mode="dontAsk"` is correct for autonomous agents
- State MCP replaces old sync-agent on port 8000 — Cloudflare tunnel stays
- Web Tools MCP keeps port 8001 — Cloudflare tunnel stays
- Content Agent + Sync Agent have no ports (internal only, timer-driven)
- Old v1 services (sync-agent, web-agent, content-agent) need to be stopped first
- See `docs/v2.2-build-log.md` for full testing checklists per chunk
