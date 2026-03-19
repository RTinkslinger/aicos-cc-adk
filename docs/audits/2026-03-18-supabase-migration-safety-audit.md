# Supabase Migration Safety Audit
**Date:** 2026-03-18
**Scope:** Schema compatibility, data transfer safety, connection pool sizing, pre/post-migration validation
**Status:** BLOCKING ISSUES FOUND — Do not proceed to cutover until Findings 1-5 are resolved

---

## Audit Findings Summary

**Critical:** 5 findings (must fix before cutover)
**High:** 4 findings (should fix, but have workarounds)
**Medium:** 3 findings (nice-to-have improvements)

---

## CRITICAL FINDINGS

### 1. SERIAL Columns Will Fail on Supabase Without Action
**Severity:** CRITICAL
**Dimension:** 2. SERIAL → identity columns

**Issue:**
The baseline schema uses `SERIAL PRIMARY KEY` on 11 tables (thesis_threads, actions_queue, action_outcomes, companies, network, etc.). While `pg_dump --format=directory` will preserve SERIAL definitions and their sequence values, Supabase **strongly recommends** converting to `GENERATED ALWAYS AS IDENTITY` (PostgreSQL 10+). The reason: SERIAL is syntactic sugar that creates a separate sequence object — it's less resilient to concurrent inserts and harder to manage in managed environments.

Additionally, if Supabase ever has to re-export or re-import your DB, SERIAL sequences can drift out of sync.

**Evidence from schema:**
```sql
CREATE TABLE thesis_threads (id SERIAL PRIMARY KEY, ...);
CREATE TABLE actions_queue (id SERIAL PRIMARY KEY, ...);
-- [repeat × 11 tables]
```

**Risk in migration plan:**
- Section 2.4: `pg_restore` will create sequences for SERIAL columns
- But sequences are not automatically resynced post-restore
- If a sequence gets ahead of inserted rows, future INSERTs will fail with duplicate key errors

**Fix Required:**
Before running `pg_dump` on the source droplet:
```sql
-- Convert all SERIAL columns to GENERATED ALWAYS AS IDENTITY
ALTER TABLE thesis_threads ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;
ALTER TABLE actions_queue ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;
-- [repeat for all 11 tables]
```

Then run `pg_dump`. The dump will include `GENERATED ALWAYS AS IDENTITY` definitions, which are cleaner and more portable.

**Alternative (less preferred):** Let pg_dump export SERIAL as-is, then in Supabase, run:
```sql
SELECT setval(pg_get_serial_sequence('thesis_threads', 'id'),
  (SELECT MAX(id) FROM thesis_threads));
-- [repeat for each table's sequence]
```

**Recommendation:** Use the first approach (convert to IDENTITY on source). It's cleaner and prevents future drift issues.

---

### 2. Pool Configuration Will Exhaust Supabase Connection Limits
**Severity:** CRITICAL
**Dimension:** 12. Pool config for Supabase

**Issue:**
Current `connection.py` sets `min_size=2, max_size=5`:

```python
_pool = await asyncpg.create_pool(db_url, min_size=2, max_size=5)
```

The plan (Step 4.4) says to reduce to `max_size=3`, but the math is incomplete:
- 3 processes (state-mcp, web-tools-mcp, orchestrator) × 3 max_size = **9 minimum connections**
- Supabase Micro plan (Pro tier minimum) has **60 max connections** total
- PostgREST uses ~10-15 connections internally
- Safe margin: reserve 40% of connections for system services
- **Safe pool size: 9 connections is 15% of 60 = OK**

BUT there's a hidden risk: `min_size=2` means each process will **immediately open 2 connections on startup**, totaling 6 connections just sitting idle. Then as load increases, they expand to 3 each = 9 total.

**Evidence from research document:**
> "If heavily using PostgREST API, keep pool size under 40% of max_connections. Otherwise, up to 80% is fine."

**Risk:**
- If Supabase compute size downgrades (Nano has only 60 connections), even 9 becomes risky
- Orchestrator subprocess (`psql` calls) open **additional** connections outside the asyncpg pool — could spike over 15 total

**Fix Required:**
1. **Update connection.py** to use smaller pool:
```python
_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=2)
```
This gives: 3 processes × 2 = 6 max connections, leaving 54 for other services (very safe).

2. **Update migration plan Step 4.4** to specify `min_size=1, max_size=2` (not just max_size=3)

3. **Add monitoring to droplet runbook:**
```bash
# After cutover, monitor connection count
psql "$SUPABASE_URL" -c "SELECT count(*) FROM pg_stat_activity;"
# Should stay well under 40 connections even under load
```

**Alternative:** Upgrade Supabase to Small ($20/mo) which has 90 connections, then max_size=3 is completely safe.

---

### 3. Connection String Lacks `sslmode=require` — Will Accept Unencrypted Fallback
**Severity:** CRITICAL
**Dimension:** 7. Connection string with asyncpg

**Issue:**
The migration plan Step 4.3 shows:
```bash
DATABASE_URL="postgres://postgres.[REF]:[PASS]@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
```

This connection string has **no SSL/TLS mode specified**. By default, asyncpg will:
1. Try SSL first
2. If SSL fails, fall back to unencrypted
3. This is a security risk over the internet

Supabase allows non-SSL connections for backward compatibility, but does not recommend it.

**Evidence from research document:**
> "SSL enforcement can be toggled on via Dashboard. When enforced, `sslmode=verify-full` is recommended."

**Fix Required:**
Update all connection strings to include `?sslmode=require`:
```bash
DATABASE_URL="postgres://postgres.[REF]:[PASS]@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
```

**Where to update:**
1. Migration plan Step 4.3 (droplet .env)
2. Migration plan Step 5.3 (Vercel env vars) — add to WebFront DATABASE_URL
3. Add to migration plan Step 3.1 test script (test connection with SSL)

**Test before cutover:**
```bash
psql "postgres://postgres.[REF]:[PASS]@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require" -c "SELECT 1;"
```
Should connect successfully. If it fails with SSL error, check Supabase dashboard for SSL enforcement status.

---

### 4. No Safeguard Against Duplicate Inserts During Final Sync — Race Condition Risk
**Severity:** CRITICAL
**Dimension:** 11. Concurrent writes during cutover

**Issue:**
Migration plan Step 4.2 (final sync):
```bash
pg_dump "$DATABASE_URL" --data-only --no-owner --no-privileges \
  --table=cai_inbox --table=notifications \
  --file=/opt/backups/final-sync.sql

psql "$SUPABASE_URL" < /opt/backups/final-sync.sql
```

**The problem:** Between the `pg_dump` and `psql` restore, the old DB continues running. If the Content Agent writes a new message to `cai_inbox` (id=101) on the droplet AFTER the dump completes but BEFORE the restore on Supabase:
1. Supabase will have rows 1-100 (from the main restore in Step 2.4)
2. Droplet has rows 1-101
3. The final-sync.sql will try to INSERT id=101 into Supabase
4. But if Supabase's sequence was already advanced during the main restore, it might auto-generate id=101 when the Content Agent first writes to Supabase — **causing a duplicate key conflict**

Even worse: if the restore succeeds, you now have duplicate messages (one from old DB, one from new DB), or the Supabase version wins and the old DB's message is silently lost.

**Evidence from audit:**
> "Data drift during cutover — LOW probability, but missing message mitigation: keep old Postgres alive 24h after cutover"

**Fix Required:**
Replace the simple final-sync approach with an **upsert-safe pattern:**

```bash
# BEFORE CUTOVER (in Step 4.1 — immediately after stopping services)
source /opt/agents/.env

# Capture the current max IDs from the droplet (snapshot at halt time)
MAX_INBOX_ID=$(psql "$DATABASE_URL" -t -A -c "SELECT COALESCE(MAX(id), 0) FROM cai_inbox;")
MAX_NOTIF_ID=$(psql "$DATABASE_URL" -t -A -c "SELECT COALESCE(MAX(id), 0) FROM notifications;")

echo "Snapshot at cutover: cai_inbox max_id=$MAX_INBOX_ID, notifications max_id=$MAX_NOTIF_ID"

# Dump only NEW rows (id > what's already in Supabase from the main restore)
pg_dump "$DATABASE_URL" --data-only --no-owner --no-privileges \
  --table=cai_inbox --table=notifications \
  --file=/opt/backups/final-sync.sql

# AFTER RESTORE (in Step 4.2)
# Restore using ON CONFLICT DO UPDATE to handle any race-condition duplicates
# (This requires modifying the SQL dump to include ON CONFLICT clauses, OR)
# (Simpler: delete the old DB's rows from Supabase first, then insert final-sync)

# Safest approach:
# 1. Before final-sync INSERT, DELETE from Supabase any rows with id > known_safe_id
# 2. Then INSERT final-sync (only new rows)

psql "$SUPABASE_URL" << EOF
-- Delete any rows that may have been written during dump/restore window
DELETE FROM cai_inbox WHERE id > $MAX_INBOX_ID;
DELETE FROM notifications WHERE id > $MAX_NOTIF_ID;
EOF

# Now restore the final dump (safe — no duplicates possible)
psql "$SUPABASE_URL" < /opt/backups/final-sync.sql
```

**Better yet:** Stop all services FIRST (Step 4.1 stays the same), capture the max IDs, then proceed with dump/restore. This eliminates the race window entirely.

**Recommendation:** Add to migration plan:
- Clarify that Step 4.1 (stop services) must complete BEFORE Step 4.2 (dump)
- Capture max IDs at halt time
- Use the DELETE-before-INSERT pattern to guarantee safety

---

### 5. Partial Indexes and WHERE Clauses May Not Transfer Correctly — Unclear in Plan
**Severity:** CRITICAL
**Dimension:** 6. Partial indexes

**Issue:**
The schema has 3 partial indexes:

```sql
CREATE INDEX idx_content_digests_status ON content_digests (status)
    WHERE status IN ('queued', 'processing');

CREATE INDEX idx_cai_inbox_unprocessed ON cai_inbox (processed, created_at)
    WHERE processed = FALSE;

CREATE INDEX idx_notifications_unread ON notifications (read, created_at)
    WHERE read = FALSE;

CREATE INDEX idx_sync_queue_next_retry ON sync_queue (next_retry_at)
    WHERE attempts < 5;
```

These **will transfer correctly** via `pg_dump/restore` — but the migration plan does NOT verify this. The plan has no step to check that partial indexes exist post-restore.

**Evidence from schema lines 261-288:**
All partial indexes use simple WHERE clauses (no functions, no casts), so they'll transfer fine.

**Risk:**
If someone manually re-recreates the schema on Supabase (instead of using pg_dump), they might forget the WHERE clauses, creating full indexes instead of partial — wasting disk space and hurting query performance.

**Fix Required:**
Add a verification step to migration plan Step 2.5 (post-restore verification):

```bash
# Verify partial indexes exist and have correct WHERE clauses
psql "$SUPABASE_URL" -c "
SELECT
  indexname,
  tablename,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexdef LIKE '%WHERE%'
ORDER BY tablename, indexname;
"
```

Expected output: 4 indexes with WHERE clauses visible in `indexdef` column.

**If partial indexes are missing:**
```sql
-- Recreate them
CREATE INDEX idx_content_digests_status ON content_digests (status)
    WHERE status IN ('queued', 'processing');
-- [etc.]
```

---

## HIGH FINDINGS

### 6. TIMESTAMP vs TIMESTAMPTZ Inconsistency — Will Transfer But Cause Future Bugs
**Severity:** HIGH
**Dimension:** 4. TIMESTAMP vs TIMESTAMPTZ

**Issue:**
The schema mixes TIMESTAMP (no timezone) and TIMESTAMPTZ (with timezone):

**TIMESTAMP (wrong):**
- `cai_inbox.created_at` — line 191
- `cai_inbox.processed_at` — line 190
- `notifications.created_at` — line 202
- `sync_metadata.last_sync_at` — line 209
- `sync_metadata.updated_at` — line 212
- `content_digests.processing_date` — line 104
- `content_digests.created_at` — line 105

**TIMESTAMPTZ (correct):**
- All other tables use TIMESTAMPTZ

**Will it transfer?** YES — pg_dump will preserve TIMESTAMP columns as-is.

**Why it's a problem:**
- TIMESTAMP assumes local time (confusing on droplets with UTC-set systems)
- TIMESTAMPTZ is always recommended for data that crosses time zones or systems
- When querying "events from last 24 hours", TIMESTAMP can give wrong results if system timezone changes
- If you ever need to analyze these events in a different timezone, TIMESTAMP loses the info

**Evidence from audit:**
> "DB8: TIMESTAMP vs TIMESTAMPTZ Inconsistency — Fix: ALTER columns to TIMESTAMPTZ"

**Fix Required:**
During the migration, convert all TIMESTAMP columns to TIMESTAMPTZ. Two approaches:

**Approach 1 (safest — pre-migration):**
Create a migration script (`v2.3-migrations.sql`) on the source droplet:
```sql
ALTER TABLE cai_inbox ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE cai_inbox ALTER COLUMN processed_at TYPE TIMESTAMPTZ USING COALESCE(processed_at, now()) AT TIME ZONE 'UTC';
ALTER TABLE notifications ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE sync_metadata ALTER COLUMN last_sync_at TYPE TIMESTAMPTZ USING COALESCE(last_sync_at, now()) AT TIME ZONE 'UTC';
ALTER TABLE sync_metadata ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE content_digests ALTER COLUMN processing_date TYPE TIMESTAMPTZ USING processing_date AT TIME ZONE 'UTC';
ALTER TABLE content_digests ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
```

Run this on droplet, then pg_dump will include the corrected TIMESTAMPTZ definitions.

**Approach 2 (post-migration):**
After restoring to Supabase, run the same migration on Supabase (lower risk, but leaves old-style data briefly).

**Recommendation:** Use Approach 1. It's safer and ensures the dump reflects the corrected schema.

---

### 7. JSONB Columns — Will Transfer But No Validation in Plan
**Severity:** HIGH
**Dimension:** 5. JSONB columns

**Issue:**
The schema has JSONB columns on multiple tables:
- `thesis_threads.key_questions_json` — line 35
- `actions_queue.scoring_factors`, `triage_history` — lines 63-64
- `action_outcomes.scoring_factors` — line 81
- `companies.content_connections`, `thesis_thread_links`, `signal_history`, `enrichment_metadata` — lines 134-138
- `network.agent_interaction_summaries`, `meeting_context`, `content_connections`, `signal_history`, `enrichment_metadata` — lines 172-176
- `cai_inbox.metadata` — line 188
- `notifications.metadata` — line 200
- `sync_queue.payload` — line 221
- `change_events` — not a JSONB, but referenced

**Will JSONB transfer?** YES — pg_dump will preserve JSONB data as valid JSON binary format.

**Potential issue:** If any JSONB cells contain invalid JSON, pg_dump will fail or restore corrupted data.

**Evidence from research:**
> "Data types: JSONB — any Supabase limitations? — No, fully supported"

**Fix Required:**
Add a pre-migration validation step. In migration plan Step 2.1 (pre-migration backup), add:

```bash
# Validate JSONB columns — catch corruption before migration
psql "$DATABASE_URL" -c "
WITH jsonb_tables AS (
  SELECT table_name, column_name
  FROM information_schema.columns
  WHERE data_type = 'jsonb'
)
SELECT
  table_name,
  column_name,
  COUNT(*) as total_rows,
  SUM(CASE WHEN column_name IS NOT NULL THEN 1 ELSE 0 END) as non_null
FROM information_schema.columns c
JOIN (SELECT * FROM jsonb_tables) jt USING (table_name, column_name)
GROUP BY table_name, column_name;
"

# If any rows show non-null JSONB, validate a sample:
psql "$DATABASE_URL" -c "
SELECT COUNT(*)
FROM thesis_threads
WHERE key_questions_json IS NOT NULL
  AND NOT (key_questions_json::text LIKE '%\"open\"%');
" || echo "WARNING: Invalid JSONB found in thesis_threads.key_questions_json"
```

If any JSONB is malformed, fix it on the source before dumping:
```sql
-- Example: if a JSONB cell is corrupted, replace with valid default
UPDATE thesis_threads
SET key_questions_json = '{"open": [], "answered": []}'::jsonb
WHERE key_questions_json IS NOT NULL
  AND NOT (key_questions_json::text LIKE '%\"open\"%');
```

**Recommendation:** Add the validation steps to the plan. JSONB transfer works fine, but validation is good insurance.

---

### 8. Schema Has No Integrity Constraints — Will Transfer But Queries Can Return Invalid Data
**Severity:** HIGH
**Dimension:** 1. Schema compatibility

**Issue:**
The baseline schema has NO CHECK constraints or NOT NULL constraints on key columns:
- `thread_name`, `core_thesis` can be NULL (lines 26-27)
- `action` can be NULL (line 49)
- `conviction` accepts any string — no validation it's "New", "Evolving", "High", etc.
- `status` fields (`actions_queue.status`, `content_digests.status`) — no validation
- `priority` accepts any string — should be "P0"/"P1"/"P2"/"P3"

**Will it transfer?** YES — no constraints means the schema will transfer without issues.

**Why it's a problem:**
- Code assumes these columns have valid values
- Invalid data silently makes it through, causing bugs downstream
- Example: if `conviction` = "XYZ", filtering threads by `WHERE conviction = 'High'` silently excludes it

**Evidence from audit:**
> "DB4: Missing NOT NULL + CHECK Constraints — Add constraints in v2.3-migrations.sql"

**Fix Required:**
Create `v2.3-migrations.sql` with constraints:

```sql
-- Add NOT NULL to key columns
ALTER TABLE thesis_threads
  ALTER COLUMN thread_name SET NOT NULL,
  ALTER COLUMN core_thesis SET NOT NULL;

ALTER TABLE actions_queue
  ALTER COLUMN action SET NOT NULL;

-- Add CHECK constraints for enums
ALTER TABLE thesis_threads
  ADD CONSTRAINT chk_conviction CHECK (conviction IN ('New', 'Evolving', 'Evolving Fast', 'Low', 'Medium', 'High'));

ALTER TABLE actions_queue
  ADD CONSTRAINT chk_status CHECK (status IN ('Proposed', 'Accepted', 'Dismissed', 'In Progress', 'Done'));

ALTER TABLE content_digests
  ADD CONSTRAINT chk_content_status CHECK (status IN ('queued', 'processing', 'complete', 'error'));
```

**When to run:**
- Pre-migration (recommended): Run on source droplet BEFORE pg_dump, then dump includes the constraints
- Post-migration: Run on Supabase after restore (less risky, but you'll briefly have invalid data in prod)

**Recommendation:** Run pre-migration. It ensures the dump is clean and forces data validation.

---

### 9. Missing Indexes on Critical Columns — Transfer Fine But Queries Will Be Slow
**Severity:** HIGH
**Dimension:** 3. Index transfer

**Issue:**
The schema has 20 indexes, but several critical query columns lack indexes:
- `actions_queue.company_notion_id` — no index (FK lookup)
- `action_outcomes.action_id` — no index (FK lookup, if it exists)
- Compound indexes missing on query patterns like `(status, created_at)` for sorting

**Will indexes transfer?** YES — all 20 indexes will transfer via pg_dump/restore.

**Why it matters for Supabase:**
Supabase bills by compute time. Missing indexes mean slow queries = higher CPU = higher costs. Also, orchestrator and content agent have subprocess `psql` calls that will hang on slow queries.

**Evidence from audit:**
> "DB7: Missing Indexes — Create partial indexes in v2.3-migrations.sql"

**Fix Required:**
Create missing indexes in `v2.3-migrations.sql`:

```sql
-- FK lookups
CREATE INDEX idx_actions_company_notion_id ON actions_queue (company_notion_id);
CREATE INDEX idx_actions_source_digest_notion_id ON actions_queue (source_digest_notion_id);

-- Compound indexes for common query patterns
CREATE INDEX idx_thesis_threads_status_created ON thesis_threads (status, created_at DESC);
CREATE INDEX idx_actions_status_priority ON actions_queue (status, priority);
```

**When to run:**
- Post-migration (after restore completes), before restarting services
- These indexes are non-blocking and can be created while Supabase is in use

**Recommendation:** Create them post-migration in Step 2.5 (post-restore verification), as part of schema optimization.

---

## MEDIUM FINDINGS

### 10. `pg_dump` Dump Format — Should Specify Consistency Level
**Severity:** MEDIUM
**Dimension:** 8. pg_dump order

**Issue:**
The migration plan Step 2.1 specifies:
```bash
pg_dump "$DATABASE_URL" --format=directory --jobs=4 \
  --no-owner --no-privileges --no-subscriptions
```

This uses `--jobs=4`, which enables **parallel dump**. Parallel dump does NOT use `--single-transaction`, meaning the dump may see inconsistent snapshots across tables.

Example: Table A is dumped at time T1, Table B is dumped at T2. If data changed between T1 and T2, the restore might have FK violations (B references A rows that weren't in A's dump).

**Will it work for us?** Probably YES — because:
1. Droplet services are stopped before dumping (Step 4.1)
2. No concurrent writes = consistent snapshot anyway
3. Small database (< 10 GB based on audit) = dump completes in seconds

**But it's not guaranteed in the plan.**

**Fix Required:**
Add a note to migration plan Step 2.1:

```bash
# Note: Services are stopped before dumping (Step 4.1), so parallel dump is safe.
# If you ever do a live dump (without stopping services), use:
#   pg_dump --format=directory --jobs=1 --single-transaction ...
# to guarantee consistency.
```

**Recommendation:** OPTIONAL fix — only matters if you attempt hot backup while services are running.

---

### 11. No Sequence Value Reset After Restore — Could Cause Duplicate Key Errors on First Insert
**Severity:** MEDIUM
**Dimension:** 2. SERIAL → identity columns

**Issue:**
The migration plan Step 2.5 (post-restore verification) includes:

```bash
psql "$SUPABASE_URL" -c "
  SELECT sequencename, last_value
  FROM pg_sequences
  WHERE schemaname = 'public';
"
```

This CHECKS sequence values but doesn't FIX them if they're wrong. If a sequence's `last_value` is behind the max ID in the table (e.g., sequence says 100 but table has rows up to 120), the next INSERT will fail with a duplicate key error.

**Will pg_restore set sequences correctly?** Usually YES — pg_dump includes `SELECT setval()` commands for each sequence. But it's fragile.

**Fix Required:**
After the verification query in Step 2.5, add a RESET-ALL step:

```bash
# Re-sync all sequences to match max table IDs
psql "$SUPABASE_URL" -c "
DO \$\$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT
      schemaname,
      sequencename,
      tablename,
      attname
    FROM pg_class
    WHERE relkind = 'S'
  LOOP
    EXECUTE format('SELECT setval(%L, (SELECT COALESCE(MAX(%I), 0) FROM %I))',
      r.sequencename, r.attname, r.tablename);
  END LOOP;
END \$\$;
"
```

Or simpler — per-table approach for our 11 tables:

```bash
# v1: Manual (safest)
psql "$SUPABASE_URL" -c "SELECT setval('thesis_threads_id_seq', (SELECT MAX(id) FROM thesis_threads));"
psql "$SUPABASE_URL" -c "SELECT setval('actions_queue_id_seq', (SELECT MAX(id) FROM actions_queue));"
# [repeat for all 11 tables]
```

**Recommendation:** Add the per-table approach to Step 2.5 post-restore verification. It's explicit, easy to audit, and guarantees sequences are correct.

---

### 12. Vercel Env Vars Missing in Plan — WebFront Cannot Connect to Supabase
**Severity:** MEDIUM
**Dimension:** 7. Connection string with asyncpg

**Issue:**
The migration plan Step 5.3 says:

```bash
# When ready to connect WebFront to Supabase:
# Vercel Dashboard → Project Settings → Environment Variables
# Add: DATABASE_URL = <Supabase session pooler URL>
# Add: NEXT_PUBLIC_SUPABASE_URL = https://[REF].supabase.co
# Add: NEXT_PUBLIC_SUPABASE_ANON_KEY = <anon key from Supabase dashboard>
```

**Issue:** This step is vague and happens AFTER the old services are already cutover to Supabase. If WebFront doesn't connect, it won't provide an early warning signal before full cutover.

**Fix Required:**
1. Move the Vercel env var step to Phase 3 (canary testing) — set them up with the Supabase URL BEFORE cutover, but don't deploy
2. Add explicit instructions for getting the Supabase creds:
   ```bash
   # Get from Supabase Dashboard:
   # 1. Settings → Database → Connection info
   # 2. Get the SESSION MODE pooler URL: postgres://postgres.[REF]:...@aws-0-...pooler.supabase.com:5432/postgres
   # 3. Add ?sslmode=require to the URL
   # 4. Copy to DATABASE_URL
   # 5. Settings → API → Project URL → copy to NEXT_PUBLIC_SUPABASE_URL
   # 6. Settings → API → Project API keys → copy anon key to NEXT_PUBLIC_SUPABASE_ANON_KEY
   ```

3. Add a Vercel deployment test:
   ```bash
   # After setting env vars, trigger a deployment preview
   vercel deploy --prod
   # Test WebFront reads from Supabase
   curl https://digest.wiki/api/check-db
   ```

**Recommendation:** Clarify and move Vercel step earlier in the plan (Phase 3 instead of Phase 5).

---

## Summary Table

| Finding | Severity | Dimension | Must Fix? | Timeline |
|---------|----------|-----------|-----------|----------|
| 1. SERIAL → IDENTITY | CRITICAL | 2 | YES | Pre-migration |
| 2. Pool size will exhaust limits | CRITICAL | 12 | YES | Pre-migration |
| 3. Missing sslmode=require | CRITICAL | 7 | YES | Pre-migration |
| 4. Race condition in final sync | CRITICAL | 11 | YES | Pre-migration |
| 5. Partial indexes unverified | CRITICAL | 6 | YES (verify step) | Post-migration |
| 6. TIMESTAMP vs TIMESTAMPTZ | HIGH | 4 | SHOULD | Pre-migration |
| 7. JSONB validation missing | HIGH | 5 | SHOULD | Pre-migration |
| 8. Missing constraints | HIGH | 1 | SHOULD | Pre-migration |
| 9. Missing indexes | HIGH | 3 | SHOULD | Post-migration |
| 10. pg_dump consistency | MEDIUM | 8 | OPTIONAL | Both |
| 11. Sequence reset missing | MEDIUM | 2 | SHOULD | Post-migration |
| 12. Vercel env vars vague | MEDIUM | 7 | SHOULD | Phase 3 |

---

## Recommended Actions Before Cutover

**BLOCKING (DO NOT PROCEED WITHOUT):**
1. Convert SERIAL to GENERATED ALWAYS AS IDENTITY (Finding 1)
2. Reduce asyncpg pool to min_size=1, max_size=2 (Finding 2)
3. Add `?sslmode=require` to connection strings (Finding 3)
4. Update final sync logic with DELETE-before-INSERT (Finding 4)
5. Add partial index verification step (Finding 5)

**STRONGLY RECOMMENDED (before cutover):**
6. Convert TIMESTAMP to TIMESTAMPTZ (Finding 6)
7. Add JSONB validation (Finding 7)
8. Add NOT NULL + CHECK constraints (Finding 8)
9. Add missing indexes (Finding 9)
10. Add sequence reset step (Finding 11)

**NICE-TO-HAVE (can do post-migration):**
11. Document pg_dump single-transaction mode (Finding 10)
12. Clarify Vercel env var setup (Finding 12)

---

## Sign-Off

**Do NOT proceed to Phase 4 (Cutover) until:**
- [ ] Findings 1, 2, 3, 4, 5 are resolved
- [ ] Audit is re-run to confirm fixes
- [ ] Final diff of migration plan reflects all changes
