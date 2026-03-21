# M12 Data Enrichment — Loops 1-6 Audit Report
*Date: 2026-03-20*
*Machine: M12 Data Enrichment (permanent)*
*Target: Supabase `llfkxnsfczludgigknbs` (Mumbai)*

---

## Executive Summary

Completed 6 loops of the Data Enrichment machine. Key achievements:
- **Column rename**: `current_role` -> `role_title` across DB + 4 functions + 11 code files
- **Embedding enrichment**: Updated 3 embedding_input functions to include more fields + page_content
- **Entity connections**: 0 -> 19,421 (was pre-seeded at 13,348, added 6,073 structural connections)
- **Portfolio-thesis links**: 61 -> 176 connections (39/142 portfolio entries now thesis-linked)
- **Network dedup**: Removed 6 confirmed duplicates (3,531 -> 3,525 rows)

---

## Loop 1: Rename network.current_role -> role_title (COMPLETE)

**Problem:** `current_role` is a PostgreSQL reserved identifier. Causes parser errors when unquoted.

**Actions:**
1. `ALTER TABLE network RENAME COLUMN "current_role" TO role_title;` -- succeeded
2. Updated 4 DB functions:
   - `embedding_input_network()` -- column reference
   - `hybrid_search()` -- snippet generation (2 references)
   - `upsert_network_batch()` -- INSERT/ON CONFLICT columns
   - `fill_network_from_notion()` -- UPDATE column
3. PostgreSQL auto-updated triggers (embed_network_on_update, clear_network_embedding_on_update)
4. Updated 11 live code/schema files:
   - `mcp-servers/agents/sql/v1.0-baseline-schema.sql`
   - `sql/search-intelligence-fixes.sql`
   - `sql/obligations-build.sql`
   - `sql/datum-agent-migrations.sql`
   - `sql/data/live-schema-reference.md`
   - `mcp-servers/agents/datum/CLAUDE.md`
   - `mcp-servers/agents/cindy/CLAUDE.md`
   - `mcp-servers/agents/skills/cindy/people-linking.md`
   - `mcp-servers/agents/skills/cindy/whatsapp-parsing.md`
   - `mcp-servers/agents/skills/datum/datum-processing.md`
   - `mcp-servers/agents/skills/datum/dedup-algorithm.md`
   - `docs/source-of-truth/MACHINERIES.md`
   - `docs/superpowers/specs/2026-03-20-obligations-intelligence-design.md`
   - `docs/superpowers/specs/2026-03-20-cindy-design.md`
   - `docs/superpowers/plans/2026-03-20-notion-postgres-data-sync.md`

**Discovery:** Role data was NOT all 'postgres' as reported. 3,059/3,525 have real role titles. Only 497 NULL.

**NOT updated (historical data, already executed):** ~160 SQL batch files in `sql/data/` (fill-batches, fill-final, fill-v2, call-batch, fn-batches, batch-*, json-batches). These are historical migration data files that will never be re-executed.

---

## Loop 2: Feed page_content into embeddings (PARTIAL)

**Problem:** 88.5% of companies are empty shells — embeddings only capture name + sector + deal_status.

**Actions:**
1. Added `page_content TEXT` column to companies, network, portfolio
2. Updated embedding_input functions to include page_content (truncated to 2000 chars):
   - `embedding_input_companies()` -- added website, page_content
   - `embedding_input_network()` -- added linkedin, ids_notes, page_content
   - `embedding_input_portfolio()` -- added outcome_category, key_questions, page_content
3. Updated triggers to watch page_content changes for re-embedding
4. Generated bulk SQL migration files:
   - `sql/data/page-content-companies.sql` (419 records, 759KB)
   - `sql/data/page-content-network.sql` (290 records, 126KB)

**Remaining work:** Execute the bulk SQL files via Supabase SQL Editor or psql. Too large for MCP tool (50KB+ per batch). Portfolio research file loading also needed.

---

## Loop 3: Verify embeddings (COMPLETE)

**Embedding coverage:**
| Table | Total | With Embedding | Coverage |
|-------|-------|---------------|----------|
| companies | 4,565 | 4,565 | 100% |
| network | 3,525 | 3,525 | 100% |
| portfolio | 142 | 142 | 100% |
| thesis_threads | 8 | 8 | 100% |

**Quality check:** Composio -> Perfios (0.92 similarity) is semantically correct. Unnamed companies cluster at 0.99+ (expected — empty shells have identical embeddings).

---

## Loop 4: Seed entity_connections (COMPLETE)

**Before:** 13,348 connections (pre-seeded from earlier run, NOT empty as reported)

**New connections added:**
- 3,064 `current_employee` (network -> company, from current_company_ids)
- 2,902 `past_employee` (network -> company, from past_company_ids)

**Final state: 19,421 connections**
| Connection Type | Source -> Target | Count | Avg Strength |
|----------------|-----------------|-------|-------------|
| vector_similar | company -> company | 6,867 | 0.82 |
| current_employee | network -> company | 3,062 | 0.95 |
| past_employee | network -> company | 2,898 | 0.70 |
| vector_similar | network -> company | 2,119 | 0.79 |
| vector_similar | company -> thesis | 2,000 | 0.72 |
| vector_similar | network -> network | 1,998 | 0.85 |
| thesis_relevance | portfolio -> thesis | 176 | 0.55 |
| portfolio_investment | portfolio -> company | 142 | 0.90 |
| thesis_relevance | action -> thesis | 138 | 0.82 |
| co_occurrence | thesis -> thesis | 18 | 0.70 |
| vector_similar | network -> thesis | 3 | 0.71 |

---

## Loop 5: Portfolio-thesis connections (COMPLETE)

**Before:** 61 portfolio-thesis connections
**After:** 176 portfolio-thesis connections
**Coverage:** 39/142 portfolio entries linked to at least one thesis (was 6)

Threshold used: 0.50 cosine similarity between portfolio and thesis embeddings. Portfolio embeddings are thin (few fields), so high similarity is rare. Once page_content is loaded, similarity should improve significantly.

---

## Loop 6: Network dedup (PARTIAL)

**Duplicate analysis:**
- 73 name-duplicate groups (161 total rows)
- 15 LinkedIn-duplicate groups (different names sharing same LinkedIn URL)
- 3 confirmed true duplicates (same name + same LinkedIn): merged and deleted
- 3 name-variant duplicates (same person, spelling difference): merged and deleted
- **6 total duplicates removed** (3,531 -> 3,525)

**Not auto-merged (67 groups):** Common Indian names (Naman Jain x4, Mohit Kumar x3, Deepak Sharma x3, etc.) where same-name people are likely different individuals. Would need LinkedIn or Notion page verification to safely merge.

---

## Remaining Loops (for next session)

### L7: Extract remaining Notion page content
- 526 company page files exist on disk, only 3 loaded to DB
- Need to execute `sql/data/page-content-companies.sql` and `sql/data/page-content-network.sql`

### L8: Web enrichment for companies
- 4,219/4,565 companies (92.4%) missing website
- Can use web_search MCP tool for top companies

### L9: Verify all enrichment quality metrics
- Re-run similarity tests after page_content loading
- Compare before/after embedding quality

### L10: Final audit + report
- Comprehensive quality scores
- Compare with baseline from M2 audits

---

## Schema Changes Made

```sql
-- Column rename
ALTER TABLE network RENAME COLUMN "current_role" TO role_title;

-- New columns
ALTER TABLE companies ADD COLUMN page_content TEXT;
ALTER TABLE network ADD COLUMN page_content TEXT;
ALTER TABLE portfolio ADD COLUMN page_content TEXT;

-- Updated functions (4)
-- embedding_input_companies(), embedding_input_network(), embedding_input_portfolio(), hybrid_search()
-- upsert_network_batch(), fill_network_from_notion()

-- Updated triggers (4)
-- embed_companies_on_update, clear_companies_embedding_on_update
-- embed_network_on_update, clear_network_embedding_on_update
```
