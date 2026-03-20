# Data Quality Validation Report

**Date:** 2026-03-20
**Database:** Supabase project `llfkxnsfczludgigknbs`

---

## Check 1: Row Counts

| Table | Rows |
|-------|------|
| companies | 545 |
| network | 618 |
| portfolio | 142 |
| actions_queue | 115 |
| content_digests | 22 |
| thesis_threads | 8 |
| **Total** | **1,450** |

**Status:** PASS -- All tables populated.

---

## Check 2: Embedding Coverage

| Table | Embedded | Total | Coverage |
|-------|----------|-------|----------|
| companies | 545 | 545 | 100% |
| network | 544 | 618 | 88.0% |
| portfolio | 142 | 142 | 100% |
| content_digests | 22 | 22 | 100% |
| thesis_threads | 8 | 8 | 100% |
| actions_queue | 115 | 115 | 100% |

**Status:** WARNING -- 74 network rows missing embeddings.

**Breakdown of missing embeddings (74 rows):**
- 50 rows with empty `source` field (likely older records missing text for embedding generation)
- 20 rows from `parallel_enrichment_2026-03-20` (newly enriched founders, jobs still pending)
- 4 rows from other sources

**Root cause:** The 20 enrichment rows have embedding jobs queued (see Check 6). The 50 empty-source rows may lack sufficient text content for the `embedding_input_network` function to generate meaningful input.

---

## Check 3: Null Notion Page IDs

| Table | Missing notion_page_id | Total | % Missing |
|-------|----------------------|-------|-----------|
| companies | 0 | 545 | 0% |
| network | 90 | 618 | 14.6% |
| portfolio | 0 | 142 | 0% |

**Status:** WARNING -- 90 network rows have no Notion page ID.

**Root cause:** All 90 are from `parallel_enrichment_2026-03-20`. These are founder records inserted directly into Postgres during portfolio founder enrichment. They were never synced back to Notion.

**Note:** The enrichment batch actually inserted 110 records total (not 90), but 20 of those also lack embeddings. All 110 lack Notion page IDs.

---

## Check 4: Research File Coverage

| Metric | Count |
|--------|-------|
| Total portfolio companies | 142 |
| With research_file_path | 20 |
| Coverage | 14.1% |

**Status:** INFO -- 20 out of 142 portfolio companies have linked research files. This matches the 20 deep-research files in `portfolio-research/`. Remaining 122 companies have no dedicated research file yet.

---

## Check 5: Cross-Reference Integrity

| Relationship | Linked Count | Total Possible | Coverage |
|-------------|-------------|----------------|----------|
| Companies with people linked | 376 | 545 | 69.0% |
| People with companies linked | 500 | 618 | 80.9% |
| Portfolio with founders linked | 70 | 142 | 49.3% |

**Status:** WARNING -- Portfolio founder linkage at 49.3%.

**Analysis:**
- **Companies -> People:** 376/545 (69%) have `current_people_ids` populated. The 169 without are likely companies where no known contacts exist in the network table.
- **People -> Companies:** 500/618 (81%) have `current_company_ids` populated. The 118 without are either independent operators, between roles, or data gaps.
- **Portfolio -> Founders:** 70/142 (49%) have `led_by_ids` populated. This is the biggest gap -- over half of portfolio companies lack linked founder records. The recent parallel enrichment added 110 founder records, but the `led_by_ids` array on portfolio rows may not have been updated to reference them.

---

## Check 6: Embedding Queue Status

| Metric | Count |
|--------|-------|
| Pending jobs (pgmq.read) | 0 |
| Total messages in queue | 70 |
| Read count on all messages | 0 |

**Status:** WARNING -- 70 embedding jobs sitting in queue, never processed.

**Details:**
- All 70 messages were enqueued at `2026-03-20 09:59:20 UTC` (during the parallel enrichment batch)
- All have `read_ct = 0` (never picked up by a consumer)
- Message payload structure: `{id, table: "network", schema: "public", contentFunction: "embedding_input_network", embeddingColumn: "embedding"}`
- The `pgmq.read()` returning 0 pending means the visibility timeout has not expired yet, or there's a mismatch between `read` parameters and the queue state

**Root cause:** The embedding worker (Edge Function or cron) has not processed these jobs. Either it's not running, not polling frequently enough, or it encountered an error and stopped.

---

## Check 7: Intelligence Functions

| Function | Result | Status |
|----------|--------|--------|
| `hybrid_search('AI startup fintech', ...)` | 5 results | PASS |
| `action_scores` view/table | 92 rows | PASS |
| `entity_relationships` view/table | 929 rows | PASS |

**Status:** PASS -- All intelligence layer functions operational.

---

## Check 8: Founder Enrichment Status

| Metric | Count |
|--------|-------|
| Network rows from `parallel_enrichment_2026-03-20` | 110 (corrected from initial 90 query) |
| Network rows with LinkedIn URL | 540 / 618 (87.4%) |
| Enriched rows with embeddings | 90 / 110 (81.8%) |
| Enriched rows with Notion page ID | 0 / 110 (0%) |

**Status:** WARNING -- Enrichment batch partially complete. 20 rows still missing embeddings, all 110 missing Notion sync.

---

## Check 9 (Supplementary): Sync Freshness

| Table | Last Updated (UTC) | Freshness |
|-------|-------------------|-----------|
| network | 2026-03-20 09:59 | Current (today) |
| companies | 2026-03-20 09:37 | Current (today) |
| portfolio | 2026-03-20 09:58 | Current (today) |
| actions_queue | 2026-03-20 09:07 | Current (today) |
| content_digests | 2026-03-16 13:10 | 4 days stale |
| thesis_threads | 2026-03-16 13:20 | 4 days stale |

**Status:** WARNING -- `content_digests` and `thesis_threads` last updated 4 days ago (March 16). This may be expected if no new content was processed or thesis updates made, but worth verifying.

---

## Check 10 (Supplementary): Connection Pool Health

At time of audit, active connections:

| User | State | Count |
|------|-------|-------|
| postgres | idle | 11 |
| authenticator | idle | 4 |
| pgbouncer | idle | 2 |
| supabase_admin | idle | 2 |
| supabase_admin | null | 2 |
| postgres | active | 1 |
| supabase_storage_admin | idle | 1 |
| **Total** | | **23** |

**Status:** WARNING -- Connection pool was fully exhausted at the start of this audit (11 parallel queries caused `FATAL: 53300: remaining connection slots are reserved for roles with the SUPERUSER attribute`). This indicates the database is running near its connection limit. The free-tier Supabase instance has limited connection slots.

---

## Summary

| Check | Status | Details |
|-------|--------|---------|
| Row counts | PASS | 1,450 total rows across 6 tables |
| Embedding coverage | WARNING | 74 network rows missing (88% coverage) |
| Notion page IDs | WARNING | 110 enrichment rows have no Notion page ID |
| Research files | INFO | 20/142 portfolio companies have research files |
| Cross-references | WARNING | Portfolio founder linkage at 49% |
| Embedding queue | WARNING | 70 jobs queued but unprocessed |
| Intelligence functions | PASS | hybrid_search, action_scores, entity_relationships all working |
| Founder enrichment | WARNING | 110 founders added, 20 lack embeddings, all lack Notion sync |
| Sync freshness | WARNING | content_digests + thesis_threads 4 days stale |
| Connection pool | WARNING | Near capacity; 11 parallel queries caused exhaustion |

---

## Recommended Fixes

### Critical (data integrity)

1. **Process the 70 pending embedding jobs.** The embedding worker is not consuming from the `embedding_jobs` queue. Check if the Edge Function or cron job responsible for dequeuing and generating embeddings is running. Until resolved, 20 enriched founder records and ~50 older network records will be invisible to semantic search.

2. **Sync 110 enriched founders to Notion.** All `parallel_enrichment_2026-03-20` network rows lack `notion_page_id`. Either create corresponding Notion pages in the Network DB, or if these are meant to be Postgres-only records, document that decision. Currently they're orphaned from the Notion layer.

3. **Update `led_by_ids` on portfolio rows** to reference the newly enriched founder records. The parallel enrichment added 110 founders but portfolio companies' `led_by_ids` arrays were not updated to point to them. This is why portfolio founder linkage sits at only 49%.

### Important (completeness)

4. **Investigate the 50 network rows with empty source and no embedding.** These predate the enrichment batch. Determine if they have enough text content for embedding generation, or if they need manual enrichment.

5. **Verify content pipeline is running.** `content_digests` and `thesis_threads` haven't been updated since March 16 (4 days). Check orchestrator/content agent on the droplet.

### Monitoring (ongoing)

6. **Connection pool management.** The free-tier Supabase instance hit connection limits with just 11 parallel queries. Consider:
   - Reducing idle connections from droplet services
   - Using connection pooling (PgBouncer transaction mode) if not already
   - Avoiding burst parallel queries from validation scripts

7. **Expand research file coverage.** 20/142 portfolio companies have research files. Not urgent, but a gap for the intelligence layer's context richness.
