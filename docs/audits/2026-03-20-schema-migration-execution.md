# Schema Migration Execution Report

**Date:** 2026-03-20
**Supabase Project:** AI COS Mumbai (`llfkxnsfczludgigknbs`, ap-south-1)
**SQL Files Executed:**
1. `sql/companies-network-migration.sql` — ALTER TABLE for companies + network
2. `sql/portfolio-migration.sql` — CREATE TABLE for portfolio

**Status: PASS — All statements executed successfully. Zero errors.**

---

## Pre-Flight State

| Table | Columns | Indexes |
|-------|---------|---------|
| companies | 32 | 5 (pkey, notion_page_id_key, deal_status, name, sector) |
| network | 34 | 4 (pkey, notion_page_id_key, name, ryg) |
| portfolio | (does not exist) | N/A |

---

## Execution Log

### Batch 1A: Companies — Scalar Fields
**Statements:** 4 ALTER TABLE + 4 COMMENT
- `money_committed` (REAL)
- `action_due` (DATE)
- `surface_to_collective` (DATE)
- `devc_ip_poc` (TEXT DEFAULT '')

**Result:** Success

### Batch 1B: Companies — Network DB Relation Arrays (Part 1)
**Statements:** 6 ALTER TABLE + 6 COMMENT
- `current_people_ids` (TEXT[] DEFAULT '{}')
- `angel_ids` (TEXT[] DEFAULT '{}')
- `alum_ids` (TEXT[] DEFAULT '{}')
- `mpi_connect_ids` (TEXT[] DEFAULT '{}')
- `domain_eval_ids` (TEXT[] DEFAULT '{}')
- `piped_from_ids` (TEXT[] DEFAULT '{}')

**Result:** Success

### Batch 1C: Companies — Network DB Relation Arrays (Part 2) + Self-Relations
**Statements:** 6 ALTER TABLE + 6 COMMENT
- `met_by_ids` (TEXT[] DEFAULT '{}')
- `shared_with_ids` (TEXT[] DEFAULT '{}')
- `yc_partner_ids` (TEXT[] DEFAULT '{}')
- `network_ids` (TEXT[] DEFAULT '{}')
- `investor_company_ids` (TEXT[] DEFAULT '{}')
- `known_portfolio_ids` (TEXT[] DEFAULT '{}')

**Result:** Success

### Batch 1D: Companies — Cross-DB Relation Arrays
**Statements:** 5 ALTER TABLE + 5 COMMENT
- `finance_notion_ids` (TEXT[] DEFAULT '{}')
- `corp_dev_notion_ids` (TEXT[] DEFAULT '{}')
- `portfolio_notion_ids` (TEXT[] DEFAULT '{}')
- `meeting_note_ids` (TEXT[] DEFAULT '{}')
- `pending_task_ids` (TEXT[] DEFAULT '{}')

**Result:** Success

**Verification:** Companies column count = 53 (32 original + 21 new)

### Batch 2: Companies — Indexes
**Statements:** 6 CREATE INDEX IF NOT EXISTS
- `idx_companies_action_due` — B-tree, partial (WHERE action_due IS NOT NULL)
- `idx_companies_surface_to_collective` — B-tree, partial (WHERE IS NOT NULL)
- `idx_companies_pipeline_status` — B-tree
- `idx_companies_current_people_ids` — GIN, partial (WHERE != '{}')
- `idx_companies_investor_company_ids` — GIN, partial (WHERE != '{}')
- `idx_companies_known_portfolio_ids` — GIN, partial (WHERE != '{}')

**Result:** Success (all 6 created)

### Batch 3A: Network — Notion Relation Fields (Part 1)
**Statements:** 6 ALTER TABLE + 6 COMMENT
- `school_ids` (TEXT[] DEFAULT '{}')
- `angel_folio_ids` (TEXT[] DEFAULT '{}')
- `sourcing_attribution_ids` (TEXT[] DEFAULT '{}')
- `participation_attribution_ids` (TEXT[] DEFAULT '{}')
- `led_by_ids` (TEXT[] DEFAULT '{}')
- `piped_to_devc_ids` (TEXT[] DEFAULT '{}')

**Result:** Success

### Batch 3B: Network — Notion Relation Fields (Part 2) + Person Field
**Statements:** 6 ALTER TABLE + 6 COMMENT
- `yc_partner_portfolio_ids` (TEXT[] DEFAULT '{}')
- `ce_speaker_ids` (TEXT[] DEFAULT '{}')
- `ce_attendance_ids` (TEXT[] DEFAULT '{}')
- `meeting_note_ids` (TEXT[] DEFAULT '{}')
- `task_pending_ids` (TEXT[] DEFAULT '{}')
- `devc_poc` (TEXT DEFAULT '')

**Result:** Success

### Batch 3C: Network — PG-Only Enrichment Columns
**Statements:** 6 ALTER TABLE + 6 COMMENT
- `ids_notes` (TEXT DEFAULT '')
- `last_interaction` (DATE)
- `email` (TEXT DEFAULT '')
- `phone` (TEXT DEFAULT '')
- `relationship_status` (TEXT DEFAULT '')
- `source` (TEXT DEFAULT '')

**Result:** Success

**Verification:** Network column count = 52 (34 original + 18 new)

### Batch 4: Network — Indexes
**Statements:** 8 CREATE INDEX IF NOT EXISTS
- `idx_network_last_interaction` — B-tree, partial (WHERE IS NOT NULL)
- `idx_network_ryg` — B-tree (no-op: already existed)
- `idx_network_e_e_priority` — B-tree
- `idx_network_linkedin` — B-tree, partial (WHERE IS NOT NULL)
- `idx_network_email` — B-tree, partial (WHERE IS NOT NULL AND != '')
- `idx_network_sourcing_attribution` — GIN, partial (WHERE != '{}')
- `idx_network_participation_attribution` — GIN, partial (WHERE != '{}')
- `idx_network_led_by` — GIN, partial (WHERE != '{}')

**Result:** Success (7 new + 1 no-op)

### Batch 5: Portfolio — CREATE TABLE
**Statement:** 1 CREATE TABLE IF NOT EXISTS (83 columns)
- 1 title, 7 relations, 2 person, 28 select, 6 multi_select, 20 numeric, 3 real, 5 text, 2 date, 1 timestamptz, 1 text (research_file_path), 2 JSONB, 3 sync infra, 1 serial PK, 1 unique text

**Result:** Success

**Verification:** Portfolio column count = 83

### Batch 6: Portfolio — Indexes
**Statements:** 16 CREATE INDEX IF NOT EXISTS
- `idx_portfolio_portfolio_co` — B-tree
- `idx_portfolio_company_name_id` — B-tree
- `idx_portfolio_health` — B-tree
- `idx_portfolio_today` — B-tree
- `idx_portfolio_hc_priority` — B-tree
- `idx_portfolio_ops_prio` — B-tree
- `idx_portfolio_current_stage` — B-tree
- `idx_portfolio_investment_timeline` — B-tree
- `idx_portfolio_action_due_date` — B-tree
- `idx_portfolio_fumes_date` — B-tree
- `idx_portfolio_aif_usa` — B-tree
- `idx_portfolio_last_synced_at` — B-tree
- `idx_portfolio_updated_at` — B-tree
- `idx_portfolio_pstatus` — GIN
- `idx_portfolio_next_round_status` — GIN
- `idx_portfolio_follow_on_work_priority` — GIN

**Result:** Success (all 16 created; plus 2 automatic: pkey + notion_page_id unique)

### Batch 7: Portfolio — Trigger
**Statements:** CREATE OR REPLACE FUNCTION + DROP TRIGGER IF EXISTS + CREATE TRIGGER
- Function: `update_portfolio_updated_at()` — sets `updated_at = now()` on BEFORE UPDATE
- Trigger: `trg_portfolio_updated_at` on portfolio

**Result:** Success

---

## Final State

| Table | Columns (before -> after) | Indexes (before -> after) |
|-------|---------------------------|---------------------------|
| companies | 32 -> 53 (+21) | 5 -> 11 (+6) |
| network | 34 -> 52 (+18) | 4 -> 11 (+7 new, 1 no-op) |
| portfolio | N/A -> 83 (new table) | N/A -> 18 (16 explicit + pkey + unique) |

### Totals
- **New columns added:** 21 (companies) + 18 (network) + 83 (portfolio, new table) = **122 total**
- **New indexes created:** 6 (companies) + 7 (network) + 18 (portfolio) = **31 total**
- **Triggers created:** 1 (`trg_portfolio_updated_at`)
- **Functions created:** 1 (`update_portfolio_updated_at()`)
- **Errors encountered:** 0
- **Skipped (already existed):** 1 index (`idx_network_ryg`)

### Notes
- The portfolio SQL file's summary comment stated 78 columns (77+id). The actual CREATE TABLE has 83 columns. The discrepancy is due to an undercount in the comment's categorization — all columns match the SQL statement exactly.
- No existing columns were dropped or modified (per the MAX rule).
- All new columns have appropriate defaults (empty arrays, empty strings, or NULL) ensuring no impact on existing rows.
- All statements were idempotent (IF NOT EXISTS / IF EXISTS).
