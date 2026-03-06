# Milestone 2: Data Sovereignty — Full Implementation
**Iterations:** 1-3 | **Dates:** 2026-03-06

## Summary
Established the Data Sovereignty architecture: public MCP endpoint via Cloudflare Tunnel, Postgres write-ahead backing for Thesis Tracker and Actions Queue, bidirectional sync with field-level ownership, change detection engine with auto-action generation, SyncAgent on 10-min cron, and unified sync status dashboard. All 17 MCP tools QA'd end-to-end from Claude.ai. Three bugs found and fixed during QA (date format, sync_queue schema, cron persistence).

## Key Decisions
- Cloudflare Tunnel + dedicated domain (3niac.com) for public MCP endpoint — zero-trust, auto-TLS
- Write-ahead pattern: Postgres first → Notion push → sync_queue on failure (exponential backoff)
- Actions field ownership: Status = droplet-owned, Outcome = Notion-owned (human feedback)
- `date:Field:start` shorthand incompatible with some DBs under `data_source_id` — use standard `{"date": {"start": ...}}`
- Action generation from changes: conviction→High = research, status parked = deprioritize, Gold outcome = pattern analysis
- Companies/Network/Portfolio sync deferred indefinitely (Phase 5)

## Iteration Details

### Iteration 1 - 2026-03-06
**Phase:** Phase 1: Public MCP Endpoint + Thesis Write Tools
**Focus:** Cloudflare Tunnel setup, thesis/digest/actions MCP tools, Claude.ai connector

**Changes:** `server.py` (added 5 MCP tools: thesis CRUD, digests, actions; switched to streamable-http transport), `notion_client.py` (added fetch_recent_digests, fetch_actions, upload_date param, Status default for thesis), `DATA-SOVEREIGNTY.md` (updated SoT map, added Layer 0 + 6-phase build plan), `CUSTOM-MCP-SETUP-HTTP.md` (new — full setup guide for Claude.ai custom MCP via Cloudflare Tunnel), `CLAUDE.md` (fixed Build Roadmap recipe with emoji-prefixed select values), `LEARNINGS.md` (2 new patterns)
**Decisions:** Cloudflare Tunnel + dedicated domain (3niac.com) for public MCP endpoint → zero-trust, no inbound ports, auto-TLS. FastMCP 3.1.0 streamable-http works out of the box with MCP spec 2025-06-18. All thesis writes now route through ai-cos-mcp (droplet = single write authority).
**Infra:** cloudflared installed on droplet, named tunnel `aicos-mcp`, DNS route `mcp.3niac.com`, systemd service enabled. Claude.ai connected as remote MCP connector.

---

### Iteration 2 - 2026-03-06
**Phase:** Data Sovereignty — Phases 1 (completion) through 4
**Focus:** Postgres backing for thesis + actions, bidirectional sync, change detection, SyncAgent

**Changes:** `lib/thesis_db.py` (new — Postgres CRUD for thesis_threads, sync_queue ops), `lib/actions_db.py` (new — Postgres CRUD for actions_queue, Outcome-only Notion pull), `lib/change_detection.py` (new — field-level diff engine), `runners/sync_agent.py` (new — orchestrates all sync), `server.py` (write-ahead pattern for thesis tools, 6 new MCP tools: sync_thesis_status, seed_thesis_db, retry_sync_queue, sync_actions, full_sync, get_changes), `notion_client.py` (seed function, status sync, actions sync/push, outcome field in fetch_actions), `.mcp.json` (new — Claude Code MCP connection), `CLAUDE.md` (MCP Tool Routing section, conviction guardrail, updated server docs), `DATA-SOVEREIGNTY.md` (revised phases, Companies/Network/Portfolio deferred), `claude-ai-sync/memory-entries.md` (v7.1.0 — MCP routing + conviction guardrail)
**Decisions:** Write-ahead pattern (Postgres first → Notion push → queue on failure). Actions field ownership: Status = droplet-owned, Outcome = Notion-owned (human feedback). SyncAgent on 10-min cron. Companies/Network/Portfolio sync deferred indefinitely.
**Infra:** 7 Postgres tables, 15 MCP tools, SyncAgent cron */10, thesis seeded (7), actions seeded (100).

---

### Iteration 3 - 2026-03-06
**Phase:** Data Sovereignty — Phase 4 completion + Full MCP QA
**Focus:** QA all MCP tools from Claude.ai, fix bugs found, build Phase 4b (action generation) + 4d (sync status dashboard)

**Changes:** `lib/notion_client.py` (fixed date property format for thesis create: `date:Field:start` → `{"date": {"start": ...}}`), `lib/change_detection.py` (added `generate_actions_from_changes()` with 4 rules, `get_sync_status()` dashboard, fixed sync_queue queries), `runners/sync_agent.py` (added `process_changes()` step to full_sync loop), `server.py` (2 new MCP tools: `cos_sync_status`, `cos_process_changes`), `deploy.sh` (SyncAgent cron preserved across deploys)
**Decisions:** `date:Field:start` shorthand incompatible with Thesis Tracker `data_source_id` (works for Content Digest). Action generation rules: conviction→High triggers research, status parked triggers deprioritize, Gold outcome triggers pattern analysis.
**Bugs fixed:** (1) Thesis create Notion push silent failure — date format, (2) sync_queue queries used nonexistent `status` column, (3) deploy.sh wiped SyncAgent cron on every deploy.
**Infra:** 17 MCP tools (was 15), all QA'd from Claude.ai. Data sovereignty fully complete (Phases 1-4, Phase 5 deferred).
