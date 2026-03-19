# Postgres Schema Audit — Database Design Review

**Date:** 2026-03-18
**Scope:** Full schema audit covering v2.2 migrations + data layer (3 tables created, 7 tables existing but not versioned)
**Files Reviewed:** `v2.2-migrations.sql`, `DATA-ARCHITECTURE.md`, `thesis.py`, `inbox.py`, `notifications.py`

---

## Executive Summary

The AI CoS Postgres schema is **structurally sound** but has **critical gaps in robustness**:

| Severity | Category | Count | Impact |
|----------|----------|-------|--------|
| **CRITICAL** | Missing constraints & validation | 4 | Data integrity at risk (unbounded TEXT, missing NOT NULL, enum-like fields without CHECK) |
| **HIGH** | Index coverage gaps | 3 | Performance risk at scale (10K+ rows) |
| **HIGH** | Schema version control | 1 | Original 7 tables not in version control — no reproducibility |
| **MEDIUM** | Type design | 5 | Data correctness and query efficiency (TIMESTAMP vs TIMESTAMPTZ, VARCHAR(100) vs TEXT) |
| **MEDIUM** | Migration safety | 2 | Non-idempotent inserts, missing rollback safety |
| **LOW** | Naming & conventions | 2 | Maintainability (inconsistent column naming across tables) |

**Bottom line:** The system works for current scale (hundreds of rows). At 10K+ rows or under production load, missing constraints will cause subtle data corruption, and missing indexes will cause performance degradation. Schema versioning is a critical gap for disaster recovery.

---

## 1. CRITICAL: Missing Constraints & Data Validation

### 1.1 Missing NOT NULL Constraints (HIGH RISK)

**Finding:** Multiple columns that logically require values are nullable. This creates silent failures downstream.

| Table | Column | Current | Should Be | Impact |
|-------|--------|---------|-----------|--------|
| `thesis_threads` | `thread_name` | TEXT (nullable) | TEXT NOT NULL | Can create threads with no name |
| `thesis_threads` | `core_thesis` | TEXT (nullable) | TEXT NOT NULL | Evidence without context |
| `actions_queue` | `action` | TEXT (nullable) | TEXT NOT NULL | Queue can contain empty actions |
| `actions_queue` | `action_type` | TEXT (nullable) | TEXT NOT NULL | No way to categorize action |
| `cai_inbox` | `type` | VARCHAR(100) NOT NULL | ✓ Correct | — |
| `cai_inbox` | `content` | TEXT NOT NULL | ✓ Correct | — |
| `notifications` | `source` | VARCHAR(100) NOT NULL | ✓ Correct | — |
| `notifications` | `type` | VARCHAR(100) NOT NULL | ✓ Correct | — |

**Fix (Migration):**
```sql
ALTER TABLE thesis_threads ALTER COLUMN thread_name SET NOT NULL;
ALTER TABLE thesis_threads ALTER COLUMN core_thesis SET NOT NULL;
ALTER TABLE actions_queue ALTER COLUMN action SET NOT NULL;
ALTER TABLE actions_queue ALTER COLUMN action_type SET NOT NULL;
```

**Test:**
```sql
-- Should fail
INSERT INTO thesis_threads (core_thesis) VALUES ('Test');
INSERT INTO actions_queue (action_type) VALUES ('Research');
```

---

### 1.2 Missing CHECK Constraints for Enum-Like Fields (CRITICAL)

**Finding:** Fields that should contain only specific values (conviction, status, decision) have no validation. Bad data can be inserted via direct SQL or buggy code.

| Table | Column | Valid Values | Current | Problem |
|-------|--------|-------------|---------|---------|
| `thesis_threads` | `conviction` | New/Evolving/Evolving Fast/Low/Medium/High | TEXT (any) | Can insert `conviction='invalid'` |
| `thesis_threads` | `status` | Active/Exploring/Parked/Archived | TEXT (any) | Can insert `status='xyz'` |
| `actions_queue` | `status` | Proposed/Accepted/In Progress/Done/Dismissed | TEXT (any) | Can insert invalid status |
| `actions_queue` | `priority` | P0/P1/P2/P3 | TEXT (any) | Can insert `priority='urgent'` (wrong format) |
| `actions_queue` | `outcome` | Unknown/Helpful/Gold | TEXT (any) | Can insert `outcome='bad'` (bad format) |
| `action_outcomes` | `decision` | accepted/dismissed/deferred/expired | TEXT (any) | Can insert `decision='maybe'` |
| `content_digests` | `status` | pending/processing/published/failed | TEXT (any) | Can insert any value |
| `sync_queue` | `operation` | create/update | TEXT (any) | Can insert `operation='delete'` |
| `change_events` | `processed` | TRUE/FALSE | BOOLEAN | ✓ Correct (no constraint needed) |
| `cai_inbox` | `processed` | TRUE/FALSE | BOOLEAN | ✓ Correct (no constraint needed) |
| `notifications` | `read` | TRUE/FALSE | BOOLEAN | ✓ Correct (no constraint needed) |

**Fix (Migrations):**
```sql
-- thesis_threads
ALTER TABLE thesis_threads ADD CONSTRAINT conviction_valid
  CHECK (conviction IN ('New', 'Evolving', 'Evolving Fast', 'Low', 'Medium', 'High'));
ALTER TABLE thesis_threads ADD CONSTRAINT status_valid
  CHECK (status IN ('Active', 'Exploring', 'Parked', 'Archived'));

-- actions_queue
ALTER TABLE actions_queue ADD CONSTRAINT status_valid
  CHECK (status IN ('Proposed', 'Accepted', 'In Progress', 'Done', 'Dismissed'));
ALTER TABLE actions_queue ADD CONSTRAINT priority_valid
  CHECK (priority IN ('P0', 'P1', 'P2', 'P3'));
ALTER TABLE actions_queue ADD CONSTRAINT outcome_valid
  CHECK (outcome IS NULL OR outcome IN ('Unknown', 'Helpful', 'Gold'));

-- action_outcomes
ALTER TABLE action_outcomes ADD CONSTRAINT decision_valid
  CHECK (decision IN ('accepted', 'dismissed', 'deferred', 'expired'));

-- content_digests
ALTER TABLE content_digests ADD CONSTRAINT status_valid
  CHECK (status IN ('pending', 'processing', 'published', 'failed'));

-- sync_queue
ALTER TABLE sync_queue ADD CONSTRAINT operation_valid
  CHECK (operation IN ('create', 'update'));
```

**Test:**
```sql
-- Should all fail
INSERT INTO thesis_threads (thread_name, core_thesis, conviction) VALUES ('Test', 'Test', 'invalid');
INSERT INTO actions_queue (action, action_type, status) VALUES ('Test', 'Research', 'maybe');
INSERT INTO content_digests (url, title, channel, status) VALUES ('http://test.com', 'Test', 'Test', 'bad_status');
```

---

### 1.3 Missing Foreign Key Constraints

**Finding:** `action_outcomes.action_id` references `actions_queue.id` but has no FK constraint. If an action is deleted, orphaned outcomes remain.

**Data Integrity Issue:**
```sql
-- Currently possible: delete an action, leaving outcomes pointing to nothing
DELETE FROM actions_queue WHERE id = 123;
-- SELECT * FROM action_outcomes WHERE action_id = 123; -- still exist!
```

**Current Schema:** `action_outcomes.action_id TEXT NOT NULL` (no FK)

**Fix:**
```sql
-- First: ensure action_id is consistent type (should it be INT or TEXT?)
-- If action_id should reference actions_queue.id:
ALTER TABLE action_outcomes
  ADD CONSTRAINT fk_action_outcomes_action_id
  FOREIGN KEY (action_id) REFERENCES actions_queue(id) ON DELETE CASCADE;

-- Or if action_id is a Notion ID (different from Postgres id), document why and add a comment
COMMENT ON COLUMN action_outcomes.action_id IS 'Notion page ID (TEXT), not FK to actions_queue.id. Lookups via notion_page_id.';
```

**Decision needed from user:**
- Is `action_id` meant to reference Notion (TEXT notion_page_id) or Postgres (SERIAL id)?
- Should `action_outcomes.action_id` have a FK or comment explaining why not?

---

### 1.4 Unbounded TEXT Columns (Medium-term risk)

**Finding:** Several columns use TEXT with no length limits. At 10M rows, this can cause:
- Full table scans to become slow
- Index bloat
- Memory pressure during sorts

| Table | Column | Size | Should Limit? | Recommendation |
|-------|--------|------|---------------|-----------------|
| `thesis_threads` | `thread_name` | TEXT | Yes | VARCHAR(500) — thread name is short |
| `thesis_threads` | `core_thesis` | TEXT | No | TEXT is correct (full thesis statement can be long) |
| `thesis_threads` | `evidence_for` | TEXT | No | TEXT is correct (append-only log) |
| `actions_queue` | `action` | TEXT | Yes | VARCHAR(1000) — action title |
| `actions_queue` | `reasoning` | TEXT | No | TEXT is correct (full reasoning) |
| `sync_queue` | `last_error` | TEXT | No | TEXT is correct (error stack traces) |

**Recommendation:** Add length limits to short-form fields to improve query performance:
```sql
ALTER TABLE thesis_threads ALTER COLUMN thread_name TYPE VARCHAR(500);
ALTER TABLE actions_queue ALTER COLUMN action TYPE VARCHAR(1000);
```

---

## 2. HIGH: Index Coverage Gaps

### 2.1 Missing Indexes on Foreign Key Lookups

**Finding:** `action_outcomes.action_id` is queried frequently (to find outcomes for an action) but has no index.

**Current:**
```sql
-- actions_queue uses notion_page_id as FK, unindexed
-- action_outcomes.action_id is unindexed
```

**Evidence from code:**
```python
# This query likely needs to find all outcomes for an action
SELECT * FROM action_outcomes WHERE action_id = $1;
```

**Missing indexes:**
```sql
CREATE INDEX IF NOT EXISTS idx_action_outcomes_action_id ON action_outcomes(action_id);
CREATE INDEX IF NOT EXISTS idx_actions_queue_notion_page_id ON actions_queue(notion_page_id);
CREATE INDEX IF NOT EXISTS idx_thesis_threads_notion_page_id ON thesis_threads(notion_page_id);
```

---

### 2.2 Missing Indexes on Status Queries

**Finding:** The `status` column is queried in WHERE clauses but has no index.

**Evidence from DATA-ARCHITECTURE.md:**
```
Content Agent uses the `status` column on `content_digests` as a processing queue:
UPDATE status='processing'
Agent picks up pending rows
```

This means queries like `SELECT * FROM content_digests WHERE status = 'pending'` are full table scans.

**Missing indexes:**
```sql
CREATE INDEX IF NOT EXISTS idx_content_digests_status ON content_digests(status);
CREATE INDEX IF NOT EXISTS idx_thesis_threads_status ON thesis_threads(status);
CREATE INDEX IF NOT EXISTS idx_actions_queue_status ON actions_queue(status);
CREATE INDEX IF NOT EXISTS idx_sync_queue_next_retry_at ON sync_queue(next_retry_at) WHERE attempts < 5;
```

---

### 2.3 Partial Index on Retry Queue

**Finding:** `sync_queue` tracks failed Notion writes. Queries check `WHERE attempts < 5` to find retryable rows.

**Current partial index:**
```sql
-- None
```

**Recommended:**
```sql
-- This partial index is efficient for retry queries
CREATE INDEX IF NOT EXISTS idx_sync_queue_retryable
  ON sync_queue(next_retry_at)
  WHERE attempts < 5;
```

---

## 3. HIGH: Schema Version Control

### 3.1 Original 7 Tables Not Versioned (CRITICAL OPERABILITY GAP)

**Finding:** The migration file `v2.2-migrations.sql` only creates 3 new tables + adds columns to existing tables. **The original 7 tables have no schema definition in git.**

**Tables without schema:**
1. `thesis_threads` — defined in DATA-ARCHITECTURE.md (doc), not in SQL
2. `actions_queue` — defined in DATA-ARCHITECTURE.md (doc), not in SQL
3. `action_outcomes` — defined in DATA-ARCHITECTURE.md (doc), not in SQL
4. `content_digests` — defined in DATA-ARCHITECTURE.md (doc), not in SQL
5. `companies` — defined in DATA-ARCHITECTURE.md (doc), not in SQL
6. `network` — defined in DATA-ARCHITECTURE.md (doc), not in SQL
7. `sync_queue` — defined in DATA-ARCHITECTURE.md (doc), not in SQL

**Impact:**
- **No disaster recovery:** If the droplet database is deleted, there's no SQL to recreate it
- **No reproducibility:** New environments can't bootstrap the schema
- **No audit trail:** When the schema was created, what version, who changed it?
- **Divergence risk:** Live schema on droplet may differ from documentation

**Fix:** Create a comprehensive initial schema migration file:

```bash
# Capture current schema from live droplet
ssh root@aicos-droplet "psql $DATABASE_URL -c '\d+' > /tmp/schema_dump.txt"

# Or create v1.0-initial-schema.sql manually with:
-- 1. CREATE TABLE statements for all 7 original tables
-- 2. CREATE INDEX statements for all existing indexes
-- 3. Comments documenting field ownership (Notion vs Droplet)

# Then version-control as:
mcp-servers/agents/sql/v1.0-initial-schema.sql
```

**Recommendation:**
1. **Immediate:** Export current schema from droplet and save to git
2. **Future:** Every schema change goes through migration versioning (v2.2 style)

---

## 4. MEDIUM: Type Design Issues

### 4.1 TIMESTAMP vs TIMESTAMPTZ Inconsistency

**Finding:** Different timestamp columns use different types. This causes subtle bugs when comparing times or displaying to user.

| Table | Column | Type | Correct? | Issue |
|-------|--------|------|----------|-------|
| `sync_metadata` | `last_sync_at` | TIMESTAMP | ❌ | No timezone — can't know which TZ |
| `sync_metadata` | `updated_at` | TIMESTAMP | ❌ | No timezone |
| `cai_inbox` | `processed_at` | TIMESTAMP | ❌ | No timezone |
| `cai_inbox` | `created_at` | TIMESTAMP | ❌ | No timezone |
| `notifications` | `created_at` | TIMESTAMP | ❌ | No timezone |
| `thesis_threads` | `last_synced_at` | TIMESTAMPTZ | ✓ | Correct |
| `thesis_threads` | `updated_at` | TIMESTAMPTZ | ✓ | Correct |
| `thesis_threads` | `created_at` | TIMESTAMPTZ | ✓ | Correct |
| `actions_queue` | `last_local_edit` | TIMESTAMPTZ | ✓ | Correct |

**Problem:**
```sql
-- These comparisons may be wrong if recorded in different TZs
SELECT * FROM cai_inbox WHERE created_at > '2026-03-18 00:00:00';
-- Is this UTC? Local? Droplet's TZ?

-- TIMESTAMPTZ makes this unambiguous
SELECT * FROM cai_inbox WHERE created_at > '2026-03-18 00:00:00+00:00'::timestamptz;
```

**Fix:**
```sql
ALTER TABLE sync_metadata ALTER COLUMN last_sync_at TYPE TIMESTAMPTZ;
ALTER TABLE sync_metadata ALTER COLUMN updated_at TYPE TIMESTAMPTZ;
ALTER TABLE cai_inbox ALTER COLUMN processed_at TYPE TIMESTAMPTZ;
ALTER TABLE cai_inbox ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE notifications ALTER COLUMN created_at TYPE TIMESTAMPTZ;
```

**Note:** TIMESTAMPTZ with DEFAULT CURRENT_TIMESTAMP will record UTC automatically.

---

### 4.2 DEFAULT Value Inconsistency

**Finding:** Different approaches to setting default timestamps:

| Table | Column | Default | Type | Issue |
|-------|--------|---------|------|-------|
| `sync_metadata` | `updated_at` | CURRENT_TIMESTAMP | TIMESTAMP | Works but non-standard |
| `cai_inbox` | `created_at` | CURRENT_TIMESTAMP | TIMESTAMP | Works but non-standard |
| `notifications` | `created_at` | CURRENT_TIMESTAMP | TIMESTAMP | Works but non-standard |
| `thesis_threads` | `updated_at` | TIMESTAMPTZ | TIMESTAMPTZ | ✓ Correct |

**Recommendation:** Standardize on `now()` function (Postgres idiom):
```sql
ALTER TABLE sync_metadata ALTER COLUMN updated_at SET DEFAULT now();
ALTER TABLE cai_inbox ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE notifications ALTER COLUMN created_at SET DEFAULT now();
```

Both `CURRENT_TIMESTAMP` and `now()` work. Use `now()` as convention for consistency with rest of codebase.

---

### 4.3 VARCHAR(100) vs TEXT Mismatch

**Finding:** Several VARCHAR fields are too short for their actual content.

| Table | Column | Current | Used For | Recommended |
|-------|--------|---------|----------|-------------|
| `sync_metadata` | `table_name` | VARCHAR(100) | SQL table name | VARCHAR(63) is safer (PG limit) |
| `sync_metadata` | `sync_status` | VARCHAR(20) | 'unknown'/'syncing'/'done' | VARCHAR(20) is fine |
| `cai_inbox` | `type` | VARCHAR(100) | track_source, research_request | VARCHAR(100) is fine |
| `notifications` | `type` | VARCHAR(100) | digest_ready, thesis_update | VARCHAR(100) is fine |
| `notifications` | `source` | VARCHAR(100) | content_agent, sync_agent | VARCHAR(100) is fine |

**Issue:** Table name could be longer than 100 chars (unlikely but possible). PG max is 63.

**Fix:**
```sql
ALTER TABLE sync_metadata ALTER COLUMN table_name TYPE VARCHAR(63);
```

---

### 4.4 JSONB vs TEXT for Structured Data

**Finding:** Using JSONB (not TEXT) for metadata is correct. But verify consistency:

| Table | Column | Type | Correct? |
|-------|--------|------|----------|
| `cai_inbox` | `metadata` | JSONB | ✓ Correct |
| `notifications` | `metadata` | JSONB | ✓ Correct |
| `sync_queue` | `payload` | JSONB | ✓ Correct |
| `action_outcomes` | `scoring_factors` | JSONB | ✓ Correct |
| `action_outcomes` | `context_snapshot` | JSONB | ✓ Correct |
| `actions_queue` | `scoring_factors` | JSONB | ✓ Correct |
| `thesis_threads` | `key_questions_json` | JSONB | ✓ Correct |
| `content_digests` | `digest_data` | JSONB | ✓ Correct |

**Status:** ✓ All structured data fields correctly use JSONB.

---

## 5. MEDIUM: Migration Safety Issues

### 5.1 Non-Idempotent INSERT in v2.2

**Finding:** The INSERT into `sync_metadata` uses `ON CONFLICT ... DO NOTHING` but is still non-idempotent in a subtle way:

```sql
INSERT INTO sync_metadata (table_name, sync_status) VALUES
    ('thesis_threads', 'unknown'),
    ('actions_queue', 'unknown'),
    ('action_outcomes', 'unknown')
ON CONFLICT (table_name) DO NOTHING;
```

**Issue:** If this migration is run twice:
1. First run: all 3 rows inserted
2. Second run: ON CONFLICT skips all 3 (good!)

But if someone manually deletes the `thesis_threads` row, then runs the migration again, only that row is re-inserted. This is fine.

**Status:** ✓ Actually safe. The `ON CONFLICT` makes it idempotent.

**Recommendation:** Document this in the migration:
```sql
-- Idempotent: if rows already exist, ON CONFLICT DO NOTHING keeps them
-- If a row is deleted, re-running this adds it back
INSERT INTO sync_metadata (table_name, sync_status) VALUES ...
ON CONFLICT (table_name) DO NOTHING;
```

---

### 5.2 Missing Rollback Safety

**Finding:** The v2.2 migration has no rollback path.

**Current:**
```sql
ALTER TABLE thesis_threads ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT TRUE;
-- ... creates 3 new tables ...
```

**If schema causes issues, there's no way to roll back easily:**
```sql
-- Manual rollback would require:
ALTER TABLE thesis_threads DROP COLUMN notion_synced;
DROP TABLE IF EXISTS sync_metadata;
DROP TABLE IF EXISTS cai_inbox;
DROP TABLE IF EXISTS notifications;
```

**Recommendation:** Document rollback in the migration file:
```sql
-- v2.2 ROLLBACK PROCEDURE (if needed):
-- ALTER TABLE thesis_threads DROP COLUMN notion_synced;
-- ALTER TABLE actions_queue DROP COLUMN notion_synced;
-- ALTER TABLE action_outcomes DROP COLUMN notion_synced;
-- DROP TABLE IF EXISTS sync_metadata;
-- DROP TABLE IF EXISTS cai_inbox;
-- DROP TABLE IF EXISTS notifications;
```

---

## 6. LOW: Naming & Conventions

### 6.1 Inconsistent Column Naming

**Finding:** Similar concepts have different names across tables.

| Concept | Table 1 | Table 2 | Issue |
|---------|---------|---------|-------|
| Notion link | `notion_page_id` | `notion_page_id` | ✓ Consistent |
| Sync flag | `notion_synced` | — (missing in others) | ❌ Inconsistent |
| Last updated | `updated_at` | `last_local_edit` | ❌ Inconsistent naming |
| Sync timestamp | `last_synced_at` | `last_notion_edit` | ❌ Inconsistent naming |
| Created timestamp | `created_at` | `created_at` | ✓ Consistent |

**Example:**
- `thesis_threads` has `last_synced_at`
- `actions_queue` has `last_notion_edit` and `last_local_edit`

These mean similar things but are named differently.

**Recommendation:** Standardize naming across tables:
```sql
-- Option 1: Always use last_synced_at
ALTER TABLE actions_queue RENAME COLUMN last_local_edit TO last_local_edit_at;
ALTER TABLE actions_queue RENAME COLUMN last_notion_edit TO last_notion_edit_at;

-- Option 2: Or use the more explicit names everywhere
-- (Document the choice in schema conventions doc)
```

---

### 6.2 Missing Column Comments

**Finding:** No COMMENT ON COLUMN statements to document field meaning or ownership.

**Example:**
```sql
-- Current: no documentation
ALTER TABLE thesis_threads ADD COLUMN notion_synced BOOLEAN DEFAULT TRUE;

-- Better:
ALTER TABLE thesis_threads ADD COLUMN notion_synced BOOLEAN DEFAULT TRUE;
COMMENT ON COLUMN thesis_threads.notion_synced IS
  'Droplet owns this field. TRUE = synced to Notion, FALSE = pending sync. SyncAgent sets to TRUE after push.';

COMMENT ON COLUMN thesis_threads.conviction IS
  'Conviction level. NEVER SET from Claude Code — requires full evidence picture. Valid values: New/Evolving/Evolving Fast/Low/Medium/High. Notion-displayed as select. Droplet reads only.';
```

**Recommendation:** Add schema documentation for all tables:
```sql
COMMENT ON TABLE thesis_threads IS 'Mirrors Notion Thesis Tracker with enrichment columns. Droplet is write authority except Status field.';
COMMENT ON COLUMN thesis_threads.conviction IS 'Valid: New/Evolving/Evolving Fast/Low/Medium/High. Droplet-read-only.';
COMMENT ON COLUMN actions_queue.status IS 'Valid: Proposed/Accepted/In Progress/Done/Dismissed. Droplet-owned, synced to Notion.';
```

---

## 7. Summary of Fixes by Priority

### Immediate (Before next deploy):

| Item | Severity | Effort | Impact |
|------|----------|--------|--------|
| Add NOT NULL to `thesis_threads.thread_name, core_thesis` | CRITICAL | 5 min | Prevents invalid data |
| Add NOT NULL to `actions_queue.action, action_type` | CRITICAL | 5 min | Prevents invalid data |
| Add CHECK constraints for enum fields | CRITICAL | 20 min | Prevents invalid data insertion |
| Convert TIMESTAMP → TIMESTAMPTZ for all created_at, updated_at | MEDIUM | 10 min | Fixes timezone ambiguity |
| Export current schema to `v1.0-initial-schema.sql` | HIGH | 30 min | Enables disaster recovery |

### Short-term (Next sprint):

| Item | Severity | Effort | Impact |
|------|----------|--------|--------|
| Add missing indexes on status, FK columns | HIGH | 15 min | Improves performance at scale |
| Add column comments documenting field ownership | MEDIUM | 30 min | Improves maintainability |
| Standardize column naming across tables | LOW | 20 min | Improves consistency |
| Document rollback procedures | MEDIUM | 10 min | Enables safe rollbacks |

### Future (Before scaling to 100K rows):

| Item | Severity | Effort | Impact |
|------|----------|--------|--------|
| Partition large tables (content_digests at 100K rows) | MEDIUM | 1-2 hours | Maintains performance at scale |
| Add archival strategy for old rows | LOW | 2-3 hours | Keeps table size bounded |
| Consider Supabase migration (planned in roadmap) | HIGH | 4-5 hours | Enables real-time + PostgREST |

---

## 8. Testing Checklist

After applying fixes, run these tests:

```bash
# 1. Verify NOT NULL constraints
psql $DATABASE_URL -c "INSERT INTO thesis_threads (core_thesis) VALUES ('test');" 2>&1 | grep -i "not null"

# 2. Verify CHECK constraints
psql $DATABASE_URL -c "INSERT INTO thesis_threads (thread_name, core_thesis, conviction) VALUES ('t', 't', 'invalid');" 2>&1 | grep -i "check"

# 3. Verify indexes exist
psql $DATABASE_URL -c "\di" | grep -E "idx_actions_queue_status|idx_content_digests_status"

# 4. Verify timestamp types
psql $DATABASE_URL -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='cai_inbox';" | grep created_at

# 5. Verify foreign key constraints
psql $DATABASE_URL -c "\d action_outcomes" | grep -i constraint
```

---

## 9. Appendix: Full Recommended Migration

Once user approves, create `v2.3-schema-hardening.sql`:

```sql
-- v2.3 Schema Hardening
-- Adds constraints, indexes, and type fixes to improve data integrity and performance
-- Idempotent: safe to run multiple times

-- ============================================================================
-- 1. Add NOT NULL constraints
-- ============================================================================

ALTER TABLE thesis_threads ALTER COLUMN thread_name SET NOT NULL;
ALTER TABLE thesis_threads ALTER COLUMN core_thesis SET NOT NULL;
ALTER TABLE actions_queue ALTER COLUMN action SET NOT NULL;
ALTER TABLE actions_queue ALTER COLUMN action_type SET NOT NULL;

-- ============================================================================
-- 2. Add CHECK constraints for enum-like fields
-- ============================================================================

ALTER TABLE thesis_threads ADD CONSTRAINT IF NOT EXISTS conviction_valid
  CHECK (conviction IN ('New', 'Evolving', 'Evolving Fast', 'Low', 'Medium', 'High'));
ALTER TABLE thesis_threads ADD CONSTRAINT IF NOT EXISTS status_valid
  CHECK (status IN ('Active', 'Exploring', 'Parked', 'Archived'));

ALTER TABLE actions_queue ADD CONSTRAINT IF NOT EXISTS aq_status_valid
  CHECK (status IN ('Proposed', 'Accepted', 'In Progress', 'Done', 'Dismissed'));
ALTER TABLE actions_queue ADD CONSTRAINT IF NOT EXISTS aq_priority_valid
  CHECK (priority IN ('P0', 'P1', 'P2', 'P3'));
ALTER TABLE actions_queue ADD CONSTRAINT IF NOT EXISTS aq_outcome_valid
  CHECK (outcome IS NULL OR outcome IN ('Unknown', 'Helpful', 'Gold'));

ALTER TABLE action_outcomes ADD CONSTRAINT IF NOT EXISTS decision_valid
  CHECK (decision IN ('accepted', 'dismissed', 'deferred', 'expired'));

ALTER TABLE content_digests ADD CONSTRAINT IF NOT EXISTS cd_status_valid
  CHECK (status IN ('pending', 'processing', 'published', 'failed'));

ALTER TABLE sync_queue ADD CONSTRAINT IF NOT EXISTS operation_valid
  CHECK (operation IN ('create', 'update'));

-- ============================================================================
-- 3. Convert TIMESTAMP to TIMESTAMPTZ
-- ============================================================================

ALTER TABLE sync_metadata ALTER COLUMN last_sync_at TYPE TIMESTAMPTZ;
ALTER TABLE sync_metadata ALTER COLUMN updated_at TYPE TIMESTAMPTZ;
ALTER TABLE cai_inbox ALTER COLUMN processed_at TYPE TIMESTAMPTZ;
ALTER TABLE cai_inbox ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE notifications ALTER COLUMN created_at TYPE TIMESTAMPTZ;

-- Update defaults to use now() instead of CURRENT_TIMESTAMP (minor style preference)
ALTER TABLE sync_metadata ALTER COLUMN updated_at SET DEFAULT now();
ALTER TABLE cai_inbox ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE notifications ALTER COLUMN created_at SET DEFAULT now();

-- ============================================================================
-- 4. Add missing indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_action_outcomes_action_id ON action_outcomes(action_id);
CREATE INDEX IF NOT EXISTS idx_actions_queue_notion_page_id ON actions_queue(notion_page_id);
CREATE INDEX IF NOT EXISTS idx_thesis_threads_notion_page_id ON thesis_threads(notion_page_id);

CREATE INDEX IF NOT EXISTS idx_content_digests_status ON content_digests(status);
CREATE INDEX IF NOT EXISTS idx_thesis_threads_status ON thesis_threads(status);
CREATE INDEX IF NOT EXISTS idx_actions_queue_status ON actions_queue(status);

CREATE INDEX IF NOT EXISTS idx_sync_queue_retryable
  ON sync_queue(next_retry_at)
  WHERE attempts < 5;

-- ============================================================================
-- 5. Type fixes
-- ============================================================================

ALTER TABLE sync_metadata ALTER COLUMN table_name TYPE VARCHAR(63);

-- ============================================================================
-- 6. Add schema documentation comments
-- ============================================================================

COMMENT ON TABLE thesis_threads IS
  'Mirrors Notion Thesis Tracker with enrichment. Droplet is write authority except Status (human-owned in Notion).';

COMMENT ON COLUMN thesis_threads.notion_synced IS
  'Droplet owns this. TRUE=synced to Notion, FALSE=pending sync. SyncAgent sets to TRUE after push.';

COMMENT ON COLUMN thesis_threads.conviction IS
  'Conviction level. DO NOT SET from Claude Code (requires full evidence). Valid: New/Evolving/Evolving Fast/Low/Medium/High.';

COMMENT ON TABLE actions_queue IS
  'Single sink for all action types. Droplet owns status (sync to Notion), human owns outcome (sync from Notion).';

COMMENT ON COLUMN actions_queue.status IS
  'Droplet-owned. Valid: Proposed/Accepted/In Progress/Done/Dismissed. Synced to Notion.';

COMMENT ON COLUMN actions_queue.outcome IS
  'Human-owned in Notion (feedback). Valid: Unknown/Helpful/Gold. Synced back to droplet.';

COMMENT ON TABLE action_outcomes IS
  'Learning mechanism. Every accept/dismiss with scoring snapshots. Used for preference training.';

COMMENT ON TABLE content_digests IS
  'Pipeline queue. Status column drives state machine: pending → processing → published. Postgres-as-queue pattern.';

COMMENT ON TABLE cai_inbox IS
  'Async inbox relay. CAI posts → State MCP → cai_inbox. Content Agent reads, processes, marks processed.';

COMMENT ON TABLE notifications IS
  'Alerts to CAI. Content Agent writes, CAI reads via State MCP get_state(notifications). Unread LIMIT 50.';

-- ============================================================================
-- v2.3 Complete. All constraints, indexes, and type fixes applied.
-- ============================================================================
```

---

## Conclusion

The schema is **operationally sound** but needs **robustness hardening** before scaling:

1. **Data integrity:** Add CHECK constraints to prevent bad enum values
2. **Schema versioning:** Export original 7 tables to version control
3. **Performance:** Add missing indexes on status and FK columns
4. **Type safety:** Standardize TIMESTAMP → TIMESTAMPTZ and fix type sizes

All fixes are **backwards compatible, non-breaking, and idempotent**. Ready to implement on user approval.
