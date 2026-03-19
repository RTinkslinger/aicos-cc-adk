# Database Architecture Audit
*Date: 2026-03-18*
*Scope: Postgres schema, queries, data flow, Supabase migration readiness*
*Auditors: 3 parallel agents (schema, queries, data flow)*

---

## Summary

6 Critical, 5 High, ~10 Medium findings. Key themes: missing schema versioning, race conditions on concurrent access, inbox message loss risk, missing constraints and indexes, Supabase migration gaps.

---

## CRITICAL

### DB1: Schema Not Version-Controlled
Only `v2.2-migrations.sql` exists (creates 3 tables + adds columns). The original 7 tables (thesis_threads, actions_queue, action_outcomes, content_digests, companies, network, sync_queue) have no SQL definition in git.
**Impact:** Fresh DB setup impossible. Supabase migration has no schema source.
**Fix:** `pg_dump --schema-only` from live DB → `sql/v1.0-baseline-schema.sql`

### DB2: Inbox Relay Message Loss
Orchestrator marks `cai_inbox.processed=TRUE` after calling `send_to_content_agent` ("Prompt sent"). If content agent crashes before processing, message is lost — never retried.
**Impact:** CAI messages (research requests, thesis updates) can disappear silently.
**Fix:** Mark processed only after content agent returns ACK with processed message IDs.

### DB3: Postgres-as-Queue Race Condition
Content pipeline selects `WHERE status='pending'` without `FOR UPDATE SKIP LOCKED`. Two concurrent processes can claim the same row.
**Impact:** Duplicate analysis, wasted compute, potential duplicate Notion pushes.
**Fix:** Use `FOR UPDATE SKIP LOCKED` in pipeline queries.

### DB4: Missing NOT NULL + CHECK Constraints
Key columns accept any value:
- `thread_name`, `core_thesis`, `action` — can be NULL
- `conviction` — accepts any string (should be New/Evolving/Evolving Fast/Low/Medium/High)
- `status` fields — no validation
- `priority` — should be P0-P3
- `outcome` — should be Unknown/Helpful/Gold
**Fix:** Add constraints in v2.3-migrations.sql

### DB5: Concurrent Evidence Append Loses Data
The CASE-based append pattern:
```sql
SET evidence_for = CASE
    WHEN COALESCE(evidence_for, '') = '' THEN $2
    ELSE evidence_for || E'\n' || $2
END
```
Two concurrent UPDATEs both read old `evidence_for`, both compute new value, last write wins — one evidence line silently dropped.
**Fix:** Replace CASE with direct concatenation: `SET evidence_for = COALESCE(evidence_for, '') || E'\n' || $2` (single atomic operation in Postgres).

### DB6: No Backup/Recovery Documented
Droplet Postgres has no backup strategy. Supabase provides 30-day PITR but it's not in runbooks.
**Fix:** Document Supabase PITR in DROPLET-RUNBOOK.md. Run `pg_dump` before Supabase migration.

---

## HIGH

### DB7: Missing Indexes
No indexes on frequently-queried WHERE columns:
- `content_digests.status` (pipeline scanning)
- `thesis_threads.status` (active thread queries)
- `actions_queue.status` + `priority` (action triage)
- `action_outcomes.action_id` (FK lookups)
**Fix:** Create partial indexes in v2.3-migrations.sql

### DB8: TIMESTAMP vs TIMESTAMPTZ Inconsistency
- `cai_inbox`, `notifications`, `sync_metadata` use TIMESTAMP (no timezone)
- All other tables use TIMESTAMPTZ
**Fix:** ALTER columns to TIMESTAMPTZ

### DB9: Unbounded get_threads() Query
Returns ALL thesis threads with full evidence_for/evidence_against text. No LIMIT.
**Fix:** Add LIMIT 50 and truncate evidence fields to 500 chars in get_threads()

### DB10: Connection Pool Sizing for Supabase
max_size=5 per process × 3 processes = 15 connections minimum. Supabase free tier has limited connections.
**Fix:** Reduce to max_size=3 per process for Supabase

### DB11: Notifications Table Grows Unbounded
No archival, no expiration, no cleanup. Reads are marked but never deleted.
**Fix:** Add retention cleanup (DELETE read notifications > 7 days)

---

## MEDIUM

- Notifications schema mismatch between code and docs (source column)
- sync_metadata not seeded for cai_inbox/notifications tables
- change_events table unused (SyncAgent disabled)
- No migration runner (manual psql, no Alembic)
- subprocess psql in has_work() has no query-level timeout
- Content agent first-run dedup inefficient (processes all historical content)

---

## Supabase Migration Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Missing schema tables | HIGH | Complete failure | Create baseline schema SQL first |
| Connection pooling exhaustion | HIGH | Downtime | Reduce pool sizes, set max_connections |
| DATABASE_URL format | HIGH | Silent failures | Supabase requires `?sslmode=require` |
| Message loss during cutover | MEDIUM | Lost inbox | Keep old Postgres alive 24h after cutover |
| Concurrent access races | MEDIUM | Data corruption | Deploy isolation fixes before migration |

---

## Fix Priority Order

### Before Supabase Migration (MUST DO)
1. DB1: Export baseline schema from live DB
2. DB4: Add NOT NULL + CHECK constraints
3. DB5: Fix concurrent evidence append (atomic)
4. DB7: Add missing indexes
5. DB8: Fix TIMESTAMP → TIMESTAMPTZ
6. DB10: Reduce pool sizes

### During Supabase Migration
7. DB6: pg_dump before migration, document PITR
8. Validate sslmode=require in connection string
9. Test full pipeline against Supabase staging

### After Migration (Next Sprint)
10. DB2: Inbox relay idempotency (requires CLAUDE.md + code change)
11. DB3: FOR UPDATE SKIP LOCKED (requires content agent prompt change)
12. DB9: Add LIMIT to get_threads()
13. DB11: Notification retention cleanup
