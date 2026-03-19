# Checkpoint
*Written: 2026-03-19 07:00*

## Current Task
Supabase migration fully complete. Old PG decommissioned. Build sequence revised. Ready for WebFront Phase 1.

## Progress
- [x] Supabase migration: PG16 droplet → PG17 Supabase Oregon → PG17 Supabase Mumbai (31ms, 16x faster)
- [x] 17/17 query+response tests passed (3 parallel test agents: reads, writes, endpoints)
- [x] 4-agent post-migration audit: schema 10/10, security secure-by-default, performance CRITICAL (fixed via Mumbai), code 3 FAIL + 3 WARN (all fixed)
- [x] Audit fixes: connection.py (statement_cache_size=0, command_timeout=30), 3 skill files (schema drift), NULL sequences reset
- [x] Old PostgreSQL decommissioned: stopped+disabled, 530MB recovered, 5 dead dirs + 3 crons + 5 systemd units removed
- [x] All docs updated: 15 files cleaned of old localhost PG refs
- [x] Deep research: 12 Supabase AI/agent capabilities, 3 unlocks identified
- [x] Supabase unlocks analysis: Auto Embeddings (invisible infra, Voyage AI), PostgREST+Realtime (WebFront pattern), Storage (deferred)
- [x] WebFront Phase 1 execution plan written (4 weeks, includes IRGI Phase A)
- [x] Committed (db0256d), pushed to origin/main, deployed to droplet
- [x] Delete Oregon Supabase project (bkxjvymaiknokybtupfm) — DONE
- [x] Vercel env vars set on aicos-digests (SUPABASE_URL, publishable key, secret key)
- [ ] Execute WebFront Phase 1

## Supabase (LIVE)
- Project: **AI COS Mumbai** (`llfkxnsfczludgigknbs`), ap-south-1
- Pooler: `aws-1-ap-south-1.pooler.supabase.com:5432` (session mode)
- PG17, pgvector 0.8.0, 934 rows, 11 tables, 37 indexes
- Password: `supabase@1987` (`%40` URL-encoded)
- Old Oregon project `bkxjvymaiknokybtupfm` still exists — delete from Supabase dashboard

## Supabase Keys (new 2026 format)
- Publishable: stored in Vercel env `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY` (client-safe, enforces RLS)
- Secret: stored in Vercel env `SUPABASE_SECRET_KEY` (server-only, bypasses RLS)
- Use `vercel env pull` to get values locally
- NOT using legacy anon/service_role JWT keys — deprecated
- Research: `docs/research/2026-03-19-supabase-new-keys-and-agent-mastery.md`

## Key Decisions (not yet persisted)
All decisions persisted to:
- `docs/superpowers/brainstorms/2026-03-19-supabase-unlocks-and-build-sequence.md` — architectural constraint (agents = orchestration, extensions = invisible infra only)
- `docs/superpowers/plans/2026-03-19-webfront-phase1-execution.md` — full Phase 1 plan
- Source-of-truth docs updated (ARCHITECTURE, DATA-ARCHITECTURE, WEBFRONT, DROPLET-RUNBOOK)
- TRACES.md iterations 21-22 logged

Key decisions summary:
- Supabase extensions (pgmq, pg_cron, pg_net) ONLY for invisible Auto Embeddings infra — agents never interact
- Embedding provider: Voyage AI `voyage-3.5` (1024 dims) — Anthropic has no native embedding model
- IRGI Phase A piggybacked onto WebFront Phase 1 (no separate sprint)
- PostgREST + Realtime = the WebFront implementation pattern
- Supabase Storage deferred to Phase 2.5
- Pooler hostnames vary by region: aws-0 for us-west-2, aws-1 for ap-south-1 (always get from dashboard)

## Next Steps
1. **User action:** Delete Oregon Supabase project from dashboard (bkxjvymaiknokybtupfm)
2. **WebFront Phase 1 — Week 1 Foundation:**
   - RLS policies: `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO service_role;`
   - Vercel env vars: SUPABASE_URL + keys on aicos-digests project
   - Install `@supabase/ssr` + `@supabase/supabase-js` in `aicos-digests/`
   - Create server-side Supabase client utility
3. **WebFront Phase 1 — Week 2:** /actions page, Server Actions, Realtime
4. **WebFront Phase 1 — Week 3:** IRGI Phase A (vector columns, Auto Embeddings, FTS, hybrid search)
5. Full plan: `docs/superpowers/plans/2026-03-19-webfront-phase1-execution.md`

## Context
- Droplet services: state-mcp:8000, web-tools-mcp:8001, orchestrator — all healthy on Mumbai Supabase
- Old PG on droplet: stopped+disabled (data files still on disk at /var/lib/postgresql/ for emergency)
- Backups at /opt/backups/ on droplet (pre-migration dumps, Oregon dump, etc.)
- Orchestrator detecting "pipeline overdue" every heartbeat — known issue (separate from migration), burns $0.25-0.51/cycle
- PG17 client tools installed on droplet (needed because pg_dump 16 can't dump PG17)
- Milestone 4 in progress (iterations 4-22 logged in TRACES.md)
