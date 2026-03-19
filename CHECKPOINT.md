# Checkpoint
*Written: 2026-03-19 ~06:30*

## Current Task
Supabase migration DONE. Build sequence revised. Ready to execute WebFront Phase 1.

## Supabase (LIVE)
- Project: **AI COS Mumbai** (`llfkxnsfczludgigknbs`)
- Region: **ap-south-1** (Mumbai), 31ms from droplet
- PostgreSQL 17.6, pgvector 0.8.0
- Pooler: `aws-1-ap-south-1.pooler.supabase.com:5432` (session mode)
- All 3 services healthy (state-mcp, web-tools-mcp, orchestrator)

## Cleanup Pending
- [ ] Delete Oregon Supabase project (`bkxjvymaiknokybtupfm`) from dashboard
- [ ] Decommission droplet local Postgres (1-2 weeks monitoring)

## Next: WebFront Phase 1
Full plan: `docs/superpowers/plans/2026-03-19-webfront-phase1-execution.md`

**Week 1 — Foundation:** RLS policies, Vercel env vars, @supabase/ssr in aicos-digests
**Week 2 — Action Triage:** /actions page, Server Actions, Realtime, Related Actions on digests
**Week 3 — Semantic Search (IRGI Phase A):** Vector columns, Auto Embeddings (Voyage AI), FTS, hybrid search
**Week 4 — Polish + Ship**

## Key Architectural Decisions (this session)
- Supabase extensions (pgmq, pg_cron, pg_net) = invisible infrastructure for Auto Embeddings ONLY
- Agents never interact with queues/cron/triggers — they are pure consumers of embeddings
- Embedding provider: Voyage AI `voyage-3.5` (1024 dims) — Anthropic has no native embedding model
- PostgREST + Realtime = the implementation pattern for WebFront (not a separate feature)
- Supabase Storage deferred to Phase 2.5 (current git push flow works)
- IRGI Phase A piggybacked onto WebFront Phase 1 (no separate sprint needed)

## Documents Updated This Session
- `docs/superpowers/plans/2026-03-19-webfront-phase1-execution.md` (NEW — full Phase 1 plan)
- `docs/superpowers/brainstorms/2026-03-19-supabase-unlocks-and-build-sequence.md` (NEW — capability analysis)
- `docs/audits/2026-03-19-supabase-migration-audit.md` (NEW — 4-agent post-migration audit)
- `docs/research/2026-03-19-supabase-agent-capabilities.md` (NEW — deep research, 12 capabilities)
- `docs/source-of-truth/ARCHITECTURE.md` (updated — Supabase live, Auto Embeddings)
- `docs/source-of-truth/DATA-ARCHITECTURE.md` (updated — semantic search layer, Voyage AI)
- `docs/source-of-truth/WEBFRONT.md` (updated — Supabase live, revised roadmap, connection map)
- `mcp-servers/agents/state/db/connection.py` (fixed — statement_cache_size=0, command_timeout=30)
- 3 skill files fixed (postgres-schema.md, inbox-handling.md, change-interpretation.md)
