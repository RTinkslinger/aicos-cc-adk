# IRGI Phase A: Hybrid Search Infrastructure -- Execution Report

**Date:** 2026-03-20
**Executor:** Claude Opus 4.6 via Supabase MCP (`execute_sql`)
**Project:** llfkxnsfczludgigknbs (ap-south-1 Mumbai, PG17)
**SQL Source:** `sql/irgi-phase-a.sql`
**Status:** ALL BATCHES EXECUTED SUCCESSFULLY

---

## Pre-Flight State

### Extensions (before)
| Extension | Status |
|-----------|--------|
| vector | 0.8.0 (pre-existing) |
| pgmq | NOT INSTALLED |
| pg_cron | NOT INSTALLED |
| pg_net | NOT INSTALLED |
| hstore | NOT INSTALLED |

### Tables (12 total, 4 targeted)
| Table | Columns | Rows |
|-------|---------|------|
| content_digests | 16 | ~22 |
| thesis_threads | 19 | ~8 |
| actions_queue | 25 | ~115 |
| companies | 53 | 0 |

### Existing Infrastructure
- **Indexes:** 66 (no FTS or vector)
- **Functions (public/util):** 2 (`rls_auto_enable`, `update_portfolio_updated_at`)
- **Triggers:** 1 (`trg_portfolio_updated_at` on portfolio)
- **Schemas:** No `util` schema

---

## Execution Log

### Batch 1: Enable Extensions
**Status:** PASS (all 4 created)

| Extension | Version | Schema |
|-----------|---------|--------|
| pgmq | 1.5.1 | pgmq |
| pg_net | 0.20.0 | extensions |
| pg_cron | 1.6.4 | pg_cron |
| hstore | 1.8 | extensions |

### Batch 2: Util Schema + Functions + Vector Columns + HNSW Indexes
**Status:** PASS

**Util schema** created. **3 utility functions** created:
- `util.project_url()` -- retrieves Supabase URL from Vault
- `util.invoke_edge_function()` -- pg_net async HTTP POST to Edge Functions
- `util.clear_column()` -- trigger to NULL a column on UPDATE

**4 vector columns** added (`embedding vector(1024)`):
- `content_digests.embedding`
- `thesis_threads.embedding`
- `actions_queue.embedding`
- `companies.embedding`

**4 HNSW indexes** created (cosine distance):
- `idx_content_digests_embedding`
- `idx_thesis_threads_embedding`
- `idx_actions_queue_embedding`
- `idx_companies_embedding`

### Batch 3: FTS tsvector Columns + GIN Indexes
**Status:** PASS (with one fix)

**4 generated tsvector columns** added (`fts tsvector GENERATED ALWAYS AS ... STORED`):
- `content_digests.fts` -- title + channel + content_type
- `thesis_threads.fts` -- thread_name + core_thesis + key_companies + investment_implications
- `actions_queue.fts` -- action + reasoning + thesis_connection + action_type
- `companies.fts` -- name + sector + agent_ids_notes

**Error encountered & fixed:**
- `companies` FTS initially included `coalesce(array_to_string(jtbd, ' '), '')` which failed with `42P17: generation expression is not immutable`
- Root cause: `array_to_string()` on `text[]` is not marked IMMUTABLE in PG17, so it cannot be used in a GENERATED ALWAYS column
- Fix: Removed `jtbd` from the FTS generated column. `jtbd` is still covered by the embedding (semantic) path via `embedding_input_companies()` which is a regular function, not a generated column

**4 GIN indexes** created:
- `idx_content_digests_fts`
- `idx_thesis_threads_fts`
- `idx_actions_queue_fts`
- `idx_companies_fts`

### Batch 4: Embedding Input Functions
**Status:** PASS (with one fix)

**Error encountered & fixed:**
- All 4 functions initially used `row` as parameter name (e.g., `embedding_input_content_digests(row content_digests)`)
- PG17 treats `row` as a reserved keyword, causing `42601: syntax error at or near "row"`
- Fix: Renamed parameter from `row` to `rec` in all 4 functions

**4 embedding input functions** created and tested:
- `embedding_input_content_digests(rec)` -- title + channel + content_type + digest_data JSONB fields
- `embedding_input_thesis_threads(rec)` -- thread_name + core_thesis + evidence + companies + implications + questions
- `embedding_input_actions_queue(rec)` -- action + action_type + reasoning + thesis_connection + source_content
- `embedding_input_companies(rec)` -- name + sector + deal_status + jtbd + agent_ids_notes

**Test results:** All 3 functions with data returned valid text output. Companies has 0 rows (function created and ready).

### Batch 5: Hybrid Search + Convenience Functions
**Status:** PASS

**3 search functions** created:
- `hybrid_search()` -- cross-table RRF-blended vector + FTS search with filters (table, status, date range)
- `search_content_digests()` -- single-table convenience search
- `search_thesis_threads()` -- single-table convenience search

**Smoke test:** `hybrid_search('agentic AI', <dummy_vector>, 5)` returned 5 FTS results across content_digests, thesis_threads, and actions_queue. No semantic results (expected -- embeddings are NULL until Edge Function pipeline is active).

### Batch 6: Backfill Helper
**Status:** PASS

- `util.backfill_embeddings()` created. Queues all non-embedded rows into pgmq for processing.

### Batch 7: Embedding Queue + Triggers + pg_cron
**Status:** PASS

**pgmq queue:** `embedding_jobs` created at 2026-03-20 09:25:32 UTC

**2 pipeline functions** created:
- `util.queue_embeddings()` -- trigger function to enqueue embedding jobs
- `util.process_embeddings()` -- reads queue, batches, invokes Edge Function

**pg_cron job:** `process-embeddings` scheduled every 10 seconds (job ID: 1)

**12 triggers** created (3 per table x 4 tables):

| Table | Insert Trigger | Update Trigger | Clear Trigger |
|-------|---------------|----------------|---------------|
| content_digests | AFTER INSERT | AFTER UPDATE (title, channel, content_type, digest_data) | BEFORE UPDATE (same cols) |
| thesis_threads | AFTER INSERT | AFTER UPDATE (thread_name, core_thesis, evidence_for, evidence_against, key_companies, investment_implications, key_questions_json) | BEFORE UPDATE (same cols) |
| actions_queue | AFTER INSERT | AFTER UPDATE (action, action_type, reasoning, thesis_connection, source_content) | BEFORE UPDATE (same cols) |
| companies | AFTER INSERT | AFTER UPDATE (name, sector, deal_status, jtbd, agent_ids_notes) | BEFORE UPDATE (same cols) |

---

## Final Verification Summary

| Component | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Extensions | 5 | 5 | PASS |
| Vector columns | 4 | 4 | PASS |
| HNSW indexes | 4 | 4 | PASS |
| FTS tsvector columns | 4 | 4 | PASS |
| GIN FTS indexes | 4 | 4 | PASS |
| Embedding input functions | 4 | 4 | PASS |
| Search functions | 3 | 3 | PASS |
| Util schema functions | 6 | 6 | PASS |
| Triggers | 12 | 12 | PASS |
| pgmq queue | 1 | 1 | PASS |
| pg_cron job | 1 | 1 | PASS |

**Total new DB objects: 43** (4 extensions + 1 schema + 10 functions + 4 columns + 4 tsvector columns + 8 indexes + 12 triggers + 1 queue + 1 cron job - some counting overlap with functions in different schemas)

---

## Errors & Fixes Applied

| # | Error | Root Cause | Fix |
|---|-------|-----------|-----|
| 1 | `42P17: generation expression is not immutable` on companies FTS | `array_to_string(jtbd, ' ')` is STABLE not IMMUTABLE in PG17 | Removed `jtbd` from generated FTS column; jtbd covered by semantic embedding instead |
| 2 | `42601: syntax error at or near "row"` on all 4 embedding_input functions | `row` is a reserved keyword in PG17 | Renamed parameter from `row` to `rec` |

Both fixes have been applied back to the source SQL file (`sql/irgi-phase-a.sql`).

---

## Remaining Manual Steps (NOT executed)

These require secrets/credentials and should be done by the user:

1. **Add project URL to Vault:**
   ```sql
   SELECT vault.create_secret(
     'https://llfkxnsfczludgigknbs.supabase.co',
     'project_url'
   );
   ```

2. **Deploy the `embed` Edge Function** (requires Supabase CLI + Voyage AI API key):
   ```bash
   supabase functions deploy embed
   supabase secrets set VOYAGE_API_KEY=<key>
   ```

3. **Run backfill** (after Edge Function is deployed):
   ```sql
   SELECT * FROM util.backfill_embeddings();
   ```

4. **Verify embeddings populate** (~30s after backfill):
   ```sql
   SELECT id, title, embedding IS NOT NULL AS has_embedding
   FROM content_digests;
   ```
