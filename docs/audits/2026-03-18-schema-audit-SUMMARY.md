# Schema Audit — Quick Reference (Executive Summary)

**Full report:** `2026-03-18-postgres-schema-audit.md` (9 sections, 300+ lines)

---

## What's Good

- **Correct use of JSONB** for structured data (metadata, digests, snapshots)
- **Write-ahead pattern** is sound (Postgres first, Notion second, fallback to queue)
- **Partial indexes** correct approach for retry queue
- **IF NOT EXISTS guards** make migration idempotent
- **Three new tables** (sync_metadata, cai_inbox, notifications) are well-designed

---

## Critical Issues (Fix Before Scaling)

### 1. Missing NOT NULL (4 fields)
```sql
-- Currently allow NULL, should not:
ALTER TABLE thesis_threads ALTER COLUMN thread_name SET NOT NULL;
ALTER TABLE thesis_threads ALTER COLUMN core_thesis SET NOT NULL;
ALTER TABLE actions_queue ALTER COLUMN action SET NOT NULL;
ALTER TABLE actions_queue ALTER COLUMN action_type SET NOT NULL;
```

### 2. Missing CHECK Constraints (Enum fields)
Status, conviction, priority, outcome fields can contain invalid values:
```sql
-- Example (6 more needed):
ALTER TABLE thesis_threads ADD CONSTRAINT conviction_valid
  CHECK (conviction IN ('New', 'Evolving', 'Evolving Fast', 'Low', 'Medium', 'High'));
```
**Impact:** Bad data can be inserted via SQL; downstream queries break silently.

### 3. No Schema Version Control
Original 7 tables have no SQL definition in git — only documented in DATA-ARCHITECTURE.md.
- **Risk:** Database is not reproducible if droplet is lost
- **Fix:** Export current schema to `v1.0-initial-schema.sql`

---

## High Issues (Fix Next Sprint)

### 4. Missing Indexes
- `action_outcomes.action_id` (FK lookups)
- `content_digests.status` (queue scanning)
- `thesis_threads.status` (filtering)
- `actions_queue.status` (filtering)

**Impact:** Full table scans at 10K+ rows.

### 5. TIMESTAMP vs TIMESTAMPTZ Inconsistency
`cai_inbox`, `notifications`, `sync_metadata` use TIMESTAMP (no TZ). Should be TIMESTAMPTZ.

**Impact:** Time comparisons may be wrong if TZ info is lost.

---

## Medium Issues (Cleanup)

| Issue | Tables | Fix |
|-------|--------|-----|
| Inconsistent column naming | actions_queue vs thesis_threads | Standardize on `last_synced_at` or `last_local_edit_at` |
| No column comments | All tables | Add COMMENT ON COLUMN for field ownership (Notion vs Droplet) |
| VARCHAR(100) for table names | sync_metadata | Reduce to VARCHAR(63) (PG limit) |
| Unbounded TEXT | thread_name, action | Add VARCHAR(500) / VARCHAR(1000) limits |
| No rollback docs | v2.2 migration | Document rollback procedure |

---

## Time to Fix

| Severity | Item | Time | Do Before |
|----------|------|------|-----------|
| **CRITICAL** | NOT NULL + CHECK constraints | 25 min | Next deploy |
| **HIGH** | Export v1.0 schema | 30 min | Disaster recovery setup |
| **HIGH** | Add indexes (6) | 15 min | Performance testing |
| **MEDIUM** | TIMESTAMP → TIMESTAMPTZ | 10 min | Before load test |
| **LOW** | Naming standardization | 20 min | Documentation refactor |

**Total: ~2 hours for all fixes.**

---

## Immediate Action Items

1. **Review** the full audit: `2026-03-18-postgres-schema-audit.md`
2. **Decide** on the FK constraint issue: is `action_outcomes.action_id` a Notion ID or should it FK to `actions_queue.id`?
3. **Approve** the migration in `Section 9: Full Recommended Migration`
4. **Export** current schema as `v1.0-initial-schema.sql` to git
5. **Run** the testing checklist in `Section 8`

---

## Risk Assessment

| Scenario | Current Risk | After Fixes |
|----------|--------------|-------------|
| Scale to 10K rows | HIGH (missing indexes, unbounded TEXT) | LOW |
| Database corruption from bad enum values | HIGH (no CHECK) | ZERO (CHECK enforces) |
| Disaster recovery | CRITICAL (no schema versioning) | SAFE (versioned SQL) |
| Timezone bugs | MEDIUM (inconsistent TIMESTAMP types) | ZERO (all TIMESTAMPTZ) |

---

## No Breaking Changes

All fixes are **backwards compatible**:
- ✓ NOT NULL defaults to existing values
- ✓ CHECK constraints only reject NEW bad data
- ✓ Type conversions (TIMESTAMP → TIMESTAMPTZ) are automatic
- ✓ New indexes don't change queries
- ✓ Comments are metadata only

**Can be deployed with zero downtime.**
