# Checkpoint
*Written: 2026-03-06 11:30 IST*

## Current Task
Complete Data Sovereignty implementation — all phases through SyncAgent orchestration.

## Progress
- [x] Phase 1: Public MCP endpoint (Cloudflare Tunnel, streamable-http, Claude.ai connector)
- [x] Phase 1g: `.mcp.json` for Claude Code MCP connection
- [x] Phase 1h: CLAUDE.md MCP Tool Routing section + conviction guardrail
- [x] Phase 2: Thesis Postgres backing (thesis_threads table, write-ahead, seed 7 threads, sync_queue)
- [x] Phase 3: Actions Queue bidirectional (actions_queue table, seed 100 actions, Outcome-only pull from Notion)
- [x] Phase 4: Change detection engine (change_events table, field-level diffs for thesis + actions)
- [x] Phase 4c: SyncAgent runner (runners/sync_agent.py — thesis + actions + retry queue)
- [x] Phase 4: SyncAgent cron (*/10 on droplet, logs to sync_agent.log)
- [x] Phase 5 deferred: companies + network tables exist, sync deferred indefinitely
- [x] Claude.ai memory v7.1.0 (19 entries, MCP routing + conviction guardrail) — pasted
- [x] Fix: Actions sync only pulls Outcome from Notion, NOT Status
- [x] All committed: f01f737 (fix), 0f8f63f (main data sovereignty commit)
- [ ] TRACES.md: Iteration 2 not yet written (this session's data sovereignty work)
- [ ] Full QA of MCP tool responses from Claude.ai (Build Roadmap task exists)
- [ ] CLAUDE.md Build Roadmap recipe still has wrong Source field options

## Key Decisions (not yet persisted)
- **Actions field ownership**: Status = droplet-owned (MCP tools / Action Frontend), Outcome = Notion-owned (human feedback). Persisted in code but not in CLAUDE.md or DATA-SOVEREIGNTY.md explicitly.
- **SyncAgent cron at 10 min** — separate from 5-min content pipeline. Handles thesis status pull + actions outcome pull + retry queue drain.
- **`current_role` is a reserved word in Postgres** — network table uses quoted `"current_role"`. Logged in mental note but not LEARNINGS.md.

## Next Steps
1. Write TRACES.md Iteration 2 for this session
2. Update CLAUDE.md Build Roadmap Source field options (from LEARNINGS.md)
3. QA all 15 MCP tool responses from Claude.ai
4. Consider adding SyncAgent to content pipeline cron wrapper for unified logging
5. Portfolio DB needs integration sharing before it can be synced

## Context
- **Postgres tables (7):** thesis_threads (7 rows), actions_queue (100 rows), companies (0), network (0), change_events (0), sync_queue (0), action_outcomes (0)
- **MCP tools (15):** health_check, cos_load_context, cos_score_action, cos_get_preferences, cos_create_thesis_thread, cos_update_thesis, cos_get_thesis_threads, cos_get_recent_digests, cos_get_actions, cos_sync_thesis_status, cos_seed_thesis_db, cos_retry_sync_queue, cos_sync_actions, cos_full_sync, cos_get_changes
- **Cron:** pipeline */5, sync_agent */10
- **Commits this session:** f547331, 0f8f63f, f01f737
- Sprint: 2, Milestone 2, Iteration 1 written (Iteration 2 pending)
