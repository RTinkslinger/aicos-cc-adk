# Build Traces

## Project Summary

Milestone 1 established the Claude Code era foundation: fixed Content Digest/Actions Queue data completeness (20+ params), implemented the AI-managed Thesis Tracker conviction engine (6-level spectrum, key questions lifecycle, autonomous thread creation), completed Cowork→CC migration (cleanup, archiving, architecture/vision docs evolved to v0.3/v5). Key architectural decisions: Thesis Tracker as AI-managed conviction engine (human only controls Status), conviction spectrum with maturity+strength axes, architecture docs strategy (originals preserved, living references at docs/architecture/ level).

## Milestone Index

| # | Iterations | Focus | Key Decisions |
|---|------------|-------|---------------|
| 1 | 1-3 | Infrastructure Hardening + Thesis Tracker + Cowork→CC Migration | AI-managed conviction engine, conviction spectrum, key questions as page blocks, claude-ai-sync/ folder, architecture doc versioning strategy |

*Full details: `traces/archive/milestone-N.md`*

---

## Current Work (Milestone 2 in progress)

### Iteration 1 - 2026-03-06
**Phase:** Phase 1: Public MCP Endpoint + Thesis Write Tools
**Focus:** Cloudflare Tunnel setup, thesis/digest/actions MCP tools, Claude.ai connector

**Changes:** `server.py` (added 5 MCP tools: thesis CRUD, digests, actions; switched to streamable-http transport), `notion_client.py` (added fetch_recent_digests, fetch_actions, upload_date param, Status default for thesis), `DATA-SOVEREIGNTY.md` (updated SoT map, added Layer 0 + 6-phase build plan), `CUSTOM-MCP-SETUP-HTTP.md` (new — full setup guide for Claude.ai custom MCP via Cloudflare Tunnel), `CLAUDE.md` (fixed Build Roadmap recipe with emoji-prefixed select values), `LEARNINGS.md` (2 new patterns)
**Decisions:** Cloudflare Tunnel + dedicated domain (3niac.com) for public MCP endpoint → zero-trust, no inbound ports, auto-TLS. FastMCP 3.1.0 streamable-http works out of the box with MCP spec 2025-06-18. All thesis writes now route through ai-cos-mcp (droplet = single write authority).
**Infra:** cloudflared installed on droplet, named tunnel `aicos-mcp`, DNS route `mcp.3niac.com`, systemd service enabled. Claude.ai connected as remote MCP connector.
**Next:** Test cos_get_recent_digests + cos_get_actions from Claude.ai. Phase 1 steps 1g (Claude Code MCP config) + 1h (prompt updates) remaining.

---

### Iteration 2 - 2026-03-06
**Phase:** Data Sovereignty — Phases 1 (completion) through 4
**Focus:** Postgres backing for thesis + actions, bidirectional sync, change detection, SyncAgent

**Changes:** `lib/thesis_db.py` (new — Postgres CRUD for thesis_threads, sync_queue ops), `lib/actions_db.py` (new — Postgres CRUD for actions_queue, Outcome-only Notion pull), `lib/change_detection.py` (new — field-level diff engine), `runners/sync_agent.py` (new — orchestrates all sync), `server.py` (write-ahead pattern for thesis tools, 6 new MCP tools: sync_thesis_status, seed_thesis_db, retry_sync_queue, sync_actions, full_sync, get_changes), `notion_client.py` (seed function, status sync, actions sync/push, outcome field in fetch_actions), `.mcp.json` (new — Claude Code MCP connection), `CLAUDE.md` (MCP Tool Routing section, conviction guardrail, updated server docs), `DATA-SOVEREIGNTY.md` (revised phases, Companies/Network/Portfolio deferred), `claude-ai-sync/memory-entries.md` (v7.1.0 — MCP routing + conviction guardrail)
**Decisions:** Write-ahead pattern (Postgres first → Notion push → queue on failure). Actions field ownership: Status = droplet-owned, Outcome = Notion-owned (human feedback). SyncAgent on 10-min cron. Companies/Network/Portfolio sync deferred indefinitely.
**Infra:** 7 Postgres tables, 15 MCP tools, SyncAgent cron */10, thesis seeded (7), actions seeded (100).
**Next:** QA all MCP tools from Claude.ai. Update CLAUDE.md Source field options.

---
