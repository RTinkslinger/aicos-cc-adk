# Supabase Migration Plan (FINAL — Dual-Audited)
*Date: 2026-03-18*
*Status: APPROVED — ready to execute*
*Audits: Systems architect (15 findings) + Database architect (12 findings) → 4 valid, 6 false positives*

---

## Overview

Migrate Postgres from self-hosted droplet (PostgreSQL 16, 934 rows across 11 tables) to Supabase managed Postgres. Single-phase cutover (~30s downtime). Old DB stays live for rollback.

---

## Pre-Requisites

- [ ] Supabase account created (Pro plan, $25/mo — free plan pauses after 1 week)
- [ ] Supabase project provisioned (region: us-east-1 to match DO droplet)
- [ ] pgvector extension enabled via Dashboard (Database → Extensions → search "vector")
- [ ] Session pooler connection string obtained (IPv4 compatible)
- [ ] Connection string format: `postgres://postgres.[REF]:[PASS]@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require`

**Important:** Always use `?sslmode=require` in the connection string. Without it, connections can fall back to unencrypted.

---

## Phase 1: Pre-Migration Schema Fix (on droplet, services running)

Fix TIMESTAMP → TIMESTAMPTZ inconsistency BEFORE dump. 7 columns across 4 tables. No data value change (both servers are UTC), but encodes the assumption in the schema.

```bash
ssh root@aicos-droplet
source /opt/agents/.env

psql "$DATABASE_URL" << 'SQL'
-- Fix TIMESTAMP → TIMESTAMPTZ (7 columns, 4 tables)
ALTER TABLE cai_inbox ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE cai_inbox ALTER COLUMN processed_at TYPE TIMESTAMPTZ USING processed_at AT TIME ZONE 'UTC';
ALTER TABLE notifications ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE sync_metadata ALTER COLUMN last_sync_at TYPE TIMESTAMPTZ USING last_sync_at AT TIME ZONE 'UTC';
ALTER TABLE sync_metadata ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE content_digests ALTER COLUMN processing_date TYPE TIMESTAMPTZ USING processing_date AT TIME ZONE 'UTC';
ALTER TABLE content_digests ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
SQL

echo "TIMESTAMP → TIMESTAMPTZ migration complete"
```

**Verify:** `psql "$DATABASE_URL" -c "\d cai_inbox" | grep timestamp`
All should show `timestamp with time zone`.

---

## Phase 2: Pre-Migration Backup (on droplet, services running)

```bash
# Full backup (keep as rollback insurance — do NOT delete)
mkdir -p /opt/backups
pg_dump "$DATABASE_URL" --format=directory --jobs=4 \
  --no-owner --no-privileges --no-subscriptions \
  --verbose --file=/opt/backups/pre-supabase-migration \
  2>&1 | tee /opt/backups/dump.log

# Record baseline metrics
psql "$DATABASE_URL" -c "
  SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname;
" | tee /opt/backups/baseline-rowcounts.txt

psql "$DATABASE_URL" -c "
  SELECT sequencename, last_value FROM pg_sequences WHERE schemaname = 'public';
" | tee /opt/backups/baseline-sequences.txt
```

---

## Phase 3: Canary Test (test Supabase WITHOUT touching production)

```bash
SUPABASE_URL="postgres://postgres.[REF]:[PASS]@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

# 3.1: Test basic psql connectivity
psql "$SUPABASE_URL" -c "SELECT 1 AS connection_test;"

# 3.2: Test asyncpg pool (State MCP pattern)
DATABASE_URL="$SUPABASE_URL" /opt/agents/.venv/bin/python3 -c "
import asyncio, asyncpg, os
async def test():
    pool = await asyncpg.create_pool(os.environ['DATABASE_URL'], min_size=1, max_size=3)
    result = await pool.fetchval('SELECT 1')
    print(f'asyncpg pool: OK (result={result})')
    await pool.close()
asyncio.run(test())
"

# 3.3: Test exact psql patterns from orchestrator has_work()
psql "$SUPABASE_URL" -t -A -c "SELECT count(*) FROM cai_inbox WHERE processed = FALSE"
# Should work — this is the exact query from lifecycle.py:403
```

---

## Phase 4: Single-Phase Cutover (~30s downtime)

**Why single-phase:** DB is 934 rows. Full dump+restore takes seconds. No need for two-phase (initial dump + final sync). This eliminates all race conditions.

### Pre-Cutover Go/No-Go Checklist
- [ ] All Phase 3 canary tests pass
- [ ] pgvector enabled on Supabase
- [ ] Supabase connection string has `?sslmode=require`
- [ ] Old Postgres still running (rollback insurance)
- [ ] Pool config updated: `min_size=1, max_size=3` (already done in code)

### Execute Cutover

```bash
ssh root@aicos-droplet
source /opt/agents/.env
SUPABASE_URL="postgres://postgres.[REF]:[PASS]@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

# 4.1: Stop all services
systemctl stop orchestrator web-tools-mcp state-mcp
echo "Services stopped at $(date -Iseconds)"

# 4.2: Fresh dump (captures FINAL state at halt time)
pg_dump "$DATABASE_URL" --format=directory --jobs=4 \
  --no-owner --no-privileges --no-subscriptions \
  --verbose --file=/opt/backups/final-dump \
  2>&1 | tee /opt/backups/final-dump.log

# 4.3: Restore to Supabase (--clean drops + recreates everything)
pg_restore \
  --clean --if-exists \
  --dbname="$SUPABASE_URL" \
  --jobs=4 \
  --no-owner --no-privileges \
  --verbose \
  /opt/backups/final-dump \
  2>&1 | tee /opt/backups/restore.log

# 4.4: Post-restore verification
psql "$SUPABASE_URL" -c "VACUUM VERBOSE ANALYZE;" 2>/dev/null

# Verify row counts match
psql "$SUPABASE_URL" -c "SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname;"
# Compare with /opt/backups/baseline-rowcounts.txt

# Verify indexes exist (including partial indexes)
psql "$SUPABASE_URL" -c "SELECT indexname FROM pg_indexes WHERE schemaname='public' ORDER BY indexname;" | wc -l
# Should be 20+ indexes

# Verify pgvector
psql "$SUPABASE_URL" -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# 4.5: Update DATABASE_URL
OLD_DATABASE_URL="$DATABASE_URL"  # save for rollback
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=\"$SUPABASE_URL\"|" /opt/agents/.env

# 4.6: Restart services
systemctl start state-mcp
sleep 3
curl -sf http://localhost:8000/health && echo " state-mcp: OK" || echo " state-mcp: FAILED"

systemctl start web-tools-mcp
sleep 3
curl -sf http://localhost:8001/health && echo " web-tools-mcp: OK" || echo " web-tools-mcp: FAILED"

systemctl start orchestrator
sleep 2
systemctl is-active orchestrator && echo " orchestrator: OK" || echo " orchestrator: FAILED"

echo "Cutover complete at $(date -Iseconds)"
```

---

## Phase 5: Post-Cutover Verification (24-48 hours)

### 5.1: Monitor services
```bash
# Watch for connection errors
journalctl -u orchestrator -f
journalctl -u state-mcp -f

# Check connection count on Supabase
psql "$SUPABASE_URL" -c "SELECT count(*) FROM pg_stat_activity;"
```

**Success metrics:**
- Zero connection errors in logs
- State MCP health endpoint returns `db: connected`
- Orchestrator heartbeat runs normally (check `live-orc.sh`)
- Content pipeline processes next video successfully

### 5.2: End-to-end pipeline test
- Add a video to YouTube playlist
- Wait for content agent to process (heartbeat → pipeline → digest)
- Verify: content_digests row in Supabase, JSON file in aicos-digests, digest.wiki updated

---

## Phase 6: Decommission Old Postgres (after 1-2 weeks stable)

```bash
# Final backup
pg_dump "$OLD_DATABASE_URL" > /opt/backups/final-decommission-backup.sql

# Stop old Postgres
systemctl stop postgresql
systemctl disable postgresql
```

---

## Rollback Plan

**At any point before Phase 6:**
1. Stop services: `systemctl stop orchestrator web-tools-mcp state-mcp`
2. Revert .env: `sed -i "s|^DATABASE_URL=.*|DATABASE_URL=\"$OLD_DATABASE_URL\"|" /opt/agents/.env`
3. Restart: `systemctl start state-mcp web-tools-mcp orchestrator`
4. Old DB is untouched — instant rollback

**If rolling back after data was written to Supabase:**
```bash
# Capture Supabase writes first
pg_dump "$SUPABASE_URL" --data-only --no-owner > /opt/backups/supabase-writes.sql
# Then revert DATABASE_URL and restart
```

---

## Changes from Draft Plan (Post-Audit)

| Change | Reason |
|--------|--------|
| Added `?sslmode=require` to all URLs | Prevents unencrypted fallback (Critical) |
| Simplified to single-phase cutover | DB is 934 rows — no two-phase needed. Eliminates race condition |
| Pool: min_size=1, max_size=3 | min_size=2 wastes idle connections; max_size=3 is optimal for peak 2-3 |
| Added TIMESTAMP→TIMESTAMPTZ pre-migration | Encodes UTC assumption in schema |
| Removed Phase 5.3 (Vercel env vars) | digest.wiki is pure SSG, no DB access. Deferred to WebFront Phase 1 |
| Added pre-cutover go/no-go checklist | Prevents accidental cutover with incomplete tests |
| 6 findings dismissed as false positives | psql+pooler compat, restart ordering, systemd env, partial indexes all verified safe |
