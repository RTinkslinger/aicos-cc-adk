# Checkpoint
*Written: 2026-03-19 ~01:00*

## Current Task
Execute Supabase migration — plan is FINAL (dual-audited, user-approved). Need to create Supabase project, then run 6-phase migration.

## Progress
- [x] Exhaustive code review: 92 findings, 51 fixed and deployed (13 Critical + 38 High/Medium)
- [x] Database architecture audit: 3 parallel audits (schema, queries, data flow)
- [x] DB1: Baseline schema exported → `sql/v1.0-baseline-schema.sql` (11 tables, 20+ indexes)
- [x] DB5: Evidence append NULL-safe (COALESCE in ELSE branches)
- [x] DB access inventory: 14 access points, all use DATABASE_URL env var, zero hardcoded hosts
- [x] Supabase migration research: pg_dump format, pooler modes, pgvector, sslmode, gotchas
- [x] Migration plan written: `docs/superpowers/plans/2026-03-18-supabase-migration.md`
- [x] Dual audit: systems architect (15 findings) + database architect (12 findings)
- [x] 10 parallel verification agents: 4 valid findings, 6 false positives
- [x] Plan updated with all 4 verified fixes (sslmode, single-phase, pool sizing, TIMESTAMPTZ)
- [x] Pool config updated: `state/db/connection.py` → min_size=1, max_size=3
- [x] Milestone 3 compacted, iterations 18-19 logged
- [x] All code committed, pushed to main, deployed to droplet
- [ ] **CREATE SUPABASE PROJECT** (user action — Pro plan, us-east-1)
- [ ] **EXECUTE MIGRATION** (6 phases in the plan)
- [ ] WebFront Phase 1: Action triage build

## Key Decisions (not yet persisted)
- Single-phase cutover (not two-phase) — DB is only 934 rows, full dump+restore takes seconds
- `?sslmode=require` mandatory on all Supabase URLs
- Pool sizing: min_size=1, max_size=3 (already applied to connection.py)
- TIMESTAMP→TIMESTAMPTZ fix runs on droplet BEFORE dump (Phase 1 of migration)
- Vercel env vars deferred to WebFront Phase 1 (digest.wiki is pure SSG, no DB access)
- Session pooler URL (not direct connection) — droplet is IPv4-only
- 6 audit findings dismissed as false positives: psql+pooler compat, restart ordering, systemd env, partial indexes, Vercel env timing, service deadlock

## Next Steps — EXACT MIGRATION SEQUENCE

**The full plan is at `docs/superpowers/plans/2026-03-18-supabase-migration.md`**

### User must do first:
1. Go to https://supabase.com → Create account → Create project
2. Select Pro plan ($25/mo), region us-east-1
3. Enable pgvector: Dashboard → Database → Extensions → search "vector" → enable
4. Get session pooler connection string: Project Settings → Database → Connection string → Session pooler (port 5432)
5. Format: `postgres://postgres.[REF]:[PASS]@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require`

### Then execute (can use team of agents for parallel phases):

**Phase 1: TIMESTAMP fix on droplet (no downtime, 2 min)**
```bash
ssh root@aicos-droplet
source /opt/agents/.env
psql "$DATABASE_URL" -c "
ALTER TABLE cai_inbox ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE cai_inbox ALTER COLUMN processed_at TYPE TIMESTAMPTZ USING processed_at AT TIME ZONE 'UTC';
ALTER TABLE notifications ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE sync_metadata ALTER COLUMN last_sync_at TYPE TIMESTAMPTZ USING last_sync_at AT TIME ZONE 'UTC';
ALTER TABLE sync_metadata ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE content_digests ALTER COLUMN processing_date TYPE TIMESTAMPTZ USING processing_date AT TIME ZONE 'UTC';
ALTER TABLE content_digests ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
"
```

**Phase 2: Backup (1 min)**
```bash
pg_dump "$DATABASE_URL" --format=directory --jobs=4 --no-owner --no-privileges --no-subscriptions --file=/opt/backups/pre-supabase-migration
```

**Phase 3: Canary test (5 min)**
Test psql + asyncpg against Supabase WITHOUT touching production.

**Phase 4: Single-phase cutover (~30s downtime)**
Stop services → fresh dump → restore with --clean → switch DATABASE_URL → restart.

**Phase 5: Monitor 24-48h**

**Phase 6: Decommission old Postgres (1-2 weeks later)**

### Deploy the pool config change:
```bash
cd mcp-servers/agents && bash deploy.sh
```
(Pool config change from max_size=5→3 needs to be deployed before migration)

## Context
- Branch: `main`, clean working tree
- Live DB: 934 rows across 11 tables (tiny — full dump/restore takes seconds)
- Systemd units all have `EnvironmentFile=-/opt/agents/.env` (confirmed on droplet)
- All 3 services healthy: state-mcp:8000, web-tools-mcp:8001, orchestrator
- Pool config already changed in code but NOT YET deployed (needs `deploy.sh`)
- Supabase research: `docs/research/2026-03-18-supabase-migration-research.md`
- DB access inventory: `docs/audits/2026-03-18-db-access-inventory.md`
- Migration safety audit: `docs/audits/2026-03-18-supabase-migration-safety-audit.md`
- Code review report: `docs/audits/2026-03-18-exhaustive-code-review.md`
- digest.wiki: Vercel auto-deploy working, latest build READY
- Uncommitted files: pool config change (connection.py), updated migration plan, research doc, audit reports
