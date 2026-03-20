# Portfolio DB Schema Audit
*Date: 2026-03-20*
*Sources: Live Notion schema via `notion-fetch` on data source `4dba9b7f-e623-41a5-9cb7-2af5976280ee`, Live Postgres via `information_schema.columns` on Supabase `llfkxnsfczludgigknbs`, Notion view query (100 rows)*

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Notion fields (live verified) | **94** |
| Postgres table exists? | **No** (greenfield CREATE TABLE) |
| Notion fields mapped to PG columns | **69** |
| Notion fields skipped (formula) | **9** |
| Notion fields skipped (rollup) | **9** |
| Notion fields skipped (system) | **2** (last_edited_by; last_edited_time IS included) |
| Notion fields included (title + text + select + multi_select + number + date + relation + person + timestamp) | **69** |
| PG-only enrichment columns added | **8** (id, notion_page_id, research_file_path, enrichment_metadata, signal_history, created_at, updated_at, last_synced_at) |
| **Final PG column count** | **78** |
| Notion row count | **100** portfolio companies |
| Indexes created | **16** (1 unique on notion_page_id + 15 btree/GIN) |

**Migration SQL:** `sql/portfolio-migration.sql` (CREATE TABLE, not ALTER TABLE -- table does not exist yet)

---

## Verification Method

1. Queried live Notion data source schema via `notion-fetch` on `4dba9b7f-e623-41a5-9cb7-2af5976280ee` -- returned full 94-field schema
2. Queried Postgres `information_schema.columns WHERE table_name = 'portfolio'` -- returned empty (table does not exist)
3. Confirmed existing tables: `action_outcomes`, `actions_queue`, `cai_inbox`, `change_events`, `companies`, `content_digests`, `network`, `notifications`, `sync_metadata`, `sync_queue`, `thesis_threads` -- no `portfolio`
4. Queried Portfolio DB default view (`view://bb57f1d8-a105-4f33-b6f8-5299331f71f9`) -- returned 100 rows with 72 visible fields per row (some fields omitted by view filters)
5. Cross-referenced schema types against actual data values to validate type mappings

---

## Notion Schema (COMPLETE -- 94 fields)

### Title (1)

| # | Property Name | Notion Type | PG Column | PG Type | Notes |
|---|--------------|-------------|-----------|---------|-------|
| 1 | **Portfolio Co** | title | `portfolio_co` | TEXT NOT NULL | Company name in portfolio |

### Text (5)

| # | Property Name | Notion Type | PG Column | PG Type | Notes |
|---|--------------|-------------|-----------|---------|-------|
| 2 | External Signal | text | `external_signal` | TEXT | Free-text signal notes |
| 3 | High Impact | text | `high_impact` | TEXT | High impact contributions |
| 4 | Key Questions | text | `key_questions` | TEXT | Active questions to track |
| 5 | Note on deployment | text | `note_on_deployment` | TEXT | Capital deployment notes |
| 6 | Scale of Business | text | `scale_of_business` | TEXT | Revenue/scale description |

### Select (28)

| # | Property Name | Options | PG Column | Notes |
|---|--------------|---------|-----------|-------|
| 7 | $500K candidate? | Yes, Maybe, No | `five_hundred_k_candidate` | Follow-on sizing |
| 8 | AIF/USA | AIF, USA | `aif_usa` | Fund entity |
| 9 | BU Follow-On Tag | Yes, PR, 0%, 2%, 5% | `bu_follow_on_tag` | Bottom-up follow-on allocation |
| 10 | Check-In Cadence | Monthly, Quarterly, Alternate Month, Bi-Annual, Ad-Hoc, NA | `check_in_cadence` | Meeting frequency |
| 11 | Current Stage | pre-product, early product, post product, early revenue, scaling revenue, Exited/Shutdown | `current_stage` | Current company stage |
| 12 | Deep Dive | Yes, No, NA | `deep_dive` | Deep dive completed? |
| 13 | EF/EO | FF, EF, EO | `ef_eo` | Engagement format |
| 14 | Follow On Decision | No Decision, Token/Zero, PR, SPR | `follow_on_decision` | Follow-on strategy |
| 15 | Follow-on Decision | Wait for 3 months, Closing, No for participation in strategic round | `follow_on_decision_alt` | NOTE: Separate Notion field from #14 |
| 16 | HC Priority | P0 (fire emoji), P1, P2, P3, P4, NA | `hc_priority` | Health check priority |
| 17 | Health | Green, Yellow, Red, NA | `health` | Company health status |
| 18 | IP Pull | High, Medium, Low | `ip_pull` | IP attractiveness |
| 19 | Investment Timeline | Q4 2022 through Q1 2026 (17 quarters) | `investment_timeline` | When investment was made |
| 20 | Likely Follow On Decision? | Pro-Rata, Super Pro-Rata, Notional/No | `likely_follow_on_decision` | Expected follow-on path |
| 21 | Next 3 months IC Candidate | Yes | `next_3m_ic_candidate` | IC pipeline flag |
| 22 | Ops Prio | P0 (fire emoji), P1, P2, NA | `ops_prio` | Operational priority |
| 23 | Outcome Category | Cat A/B/C x Marketplace/Consumer Tech/Consumer/B2B/SaaS, Custom | `outcome_category` | Return category classification |
| 24 | Raised Follow-on funding? | Yes | `raised_follow_on_funding` | Has company raised follow-on? |
| 25 | Referenceability | High, Medium, Low | `referenceability` | Portfolio reference value |
| 26 | Revenue Generating | No, Yes | `revenue_generating` | Has revenue? |
| 27 | Round 1 Type | Pre-Seed, Seed, Seed+, Pre-Series A, Series A, A+, B, C, D | `round_1_type` | Entry round type |
| 28 | Round 2 Type | (same as Round 1) | `round_2_type` | Second round type |
| 29 | Round 3 Type | (same as Round 1) | `round_3_type` | Third round type |
| 30 | Spikey | 1, 0.5, 0 | `spikey` | Differentiation score |
| 31 | Stage @ entry | pre-product, early product, post product, early revenue, scaling revenue | `stage_at_entry` | Stage when Z47/DeVC invested |
| 32 | Tier 1 and Marquee seed cap table | Yes, No | `tier_1_marquee_cap_table` | Cap table quality |
| 33 | Today | Fund Priority, Funnel, Deadpool, NA, Exited, Capital Return | `today` | Current portfolio status |
| 34 | UW Decision | Core Cheque, Community Pool, Syndicate | `uw_decision` | Underwriting decision type |

### Multi-Select (6)

| # | Property Name | Sample Options | PG Column | PG Type | Notes |
|---|--------------|---------------|-----------|---------|-------|
| 35 | FY23-24 Compliance | K1 - Done, Pending, Audited Fin AIF - Done, NA | `fy23_24_compliance` | TEXT[] | Tax/compliance tracking |
| 36 | Follow On Outcome | Follow-on as desired, Pass for DeVC, Under allocation, Reduced, Process miss, Out of strike zone, WIP | `follow_on_outcome` | TEXT[] | Actual follow-on result |
| 37 | Follow-on Work Priority | NA, P0, P1, P2 | `follow_on_work_priority` | TEXT[] | Follow-on work urgency |
| 38 | Next Round Status | H2 25, H2 24, Raising, H1 26, Raised | `next_round_status` | TEXT[] | Next fundraise timeline |
| 39 | PStatus | In Closing/Paperwork, Onboarding, Tracking - Raise NA/3/6/9/12 months, Find Home/Wind Down, Acquired/Shut Down | `pstatus` | TEXT[] | Portfolio status tags |
| 40 | Timing of Involvement? | Early to round formation, On-going conversation, Anchored, Late, etc. (12 options) | `timing_of_involvement` | TEXT[] | When Z47/DeVC got involved |

### Number (23)

| # | Property Name | Format | PG Column | PG Type | Notes |
|---|--------------|--------|-----------|---------|-------|
| 41 | Entry Cheque | dollar | `entry_cheque` | NUMERIC | Initial investment amount |
| 42 | Entry Round Raise | dollar | `entry_round_raise` | NUMERIC | Total entry round size |
| 43 | Entry Round Valuation | dollar | `entry_round_valuation` | NUMERIC | Valuation at entry |
| 44 | Last Round Valuation | dollar | `last_round_valuation` | NUMERIC | Most recent round val |
| 45 | FMV Carried | dollar | `fmv_carried` | NUMERIC | Fair market value on books |
| 46 | BU Reserve Defend | dollar | `bu_reserve_defend` | NUMERIC | Bottom-up reserve (defend scenario) |
| 47 | BU Reserve No Defend | dollar | `bu_reserve_no_defend` | NUMERIC | Bottom-up reserve (no-defend) |
| 48 | Earmarked Reserves | dollar | `earmarked_reserves` | NUMERIC | Earmarked follow-on capital |
| 49 | Reserve Committed | dollar | `reserve_committed` | NUMERIC | Committed reserve amount |
| 50 | Reserve Deployed | dollar | `reserve_deployed` | NUMERIC | Already deployed reserves |
| 51 | Fresh Committed | dollar | `fresh_committed` | NUMERIC | New commitments |
| 52 | Cash In Bank | dollar | `cash_in_bank` | NUMERIC | Company's cash position |
| 53 | Room to deploy? | dollar | `room_to_deploy` | NUMERIC | Remaining deployment capacity |
| 54 | Round 2 Raise | dollar | `round_2_raise` | NUMERIC | Second round size |
| 55 | Round 2 Val | dollar | `round_2_val` | NUMERIC | Second round valuation |
| 56 | Round 3 Raise | dollar | `round_3_raise` | NUMERIC | Third round size |
| 57 | Round 3 Val | dollar | `round_3_val` | NUMERIC | Third round valuation |
| 58 | Best case outcome | dollar | `best_case_outcome` | NUMERIC | Best-case exit value |
| 59 | Good Case outcome | dollar | `good_case_outcome` | NUMERIC | Good-case exit value |
| 60 | Likely Outcome | dollar | `likely_outcome` | NUMERIC | Expected exit value |
| 61 | Ownership % | percent | `ownership_pct` | REAL | Current ownership (0.0-1.0) |
| 62 | Dilution IF Defend | percent | `dilution_if_defend` | REAL | Dilution if pro-rata defended |
| 63 | Dilution IF NO Defend | percent | `dilution_if_no_defend` | REAL | Dilution if not defended |

### Date (2)

| # | Property Name | PG Column | PG Type | Notes |
|---|--------------|-----------|---------|-------|
| 64 | Action Due Date | `action_due_date` | DATE | Next action deadline |
| 65 | Fumes Date | `fumes_date` | DATE | Runway exhaustion estimate |

### Relation (7)

| # | Property Name | Target DB | PG Column | PG Type | Notes |
|---|--------------|-----------|-----------|---------|-------|
| 66 | Company Name | Companies DB (`1edda9cc`) | `company_name_id` | TEXT | Single relation (limit=1) |
| 67 | Led by? | Network DB (`6462102f`) | `led_by_ids` | TEXT[] | Lead investor(s) |
| 68 | Sourcing Attribution | Network DB (`6462102f`) | `sourcing_attribution_ids` | TEXT[] | Who sourced the deal |
| 69 | Participation Attribution | Network DB (`6462102f`) | `participation_attribution_ids` | TEXT[] | Who participated |
| 70 | Venture Partner? (old) | Network DB (`6462102f`) | `venture_partner_old_ids` | TEXT[] | Legacy VP field |
| 71 | Meeting Notes | Meeting Notes DB (`0dc61edf`) | `meeting_notes_ids` | TEXT[] | Linked meeting notes |
| 72 | Introduced to? | Unknown DB (`59c31a93`) | `introduced_to_ids` | TEXT[] | Introductions made |

### Person (2)

| # | Property Name | PG Column | PG Type | Notes |
|---|--------------|-----------|---------|-------|
| 73 | IP Assigned | `ip_assigned` | TEXT[] | Notion user IDs (format: `user://UUID`) |
| 74 | MD Assigned | `md_assigned` | TEXT[] | Notion user IDs |

### System / Timestamp (2)

| # | Property Name | Notion Type | PG Column | Notes |
|---|--------------|-------------|-----------|-------|
| 75 | Last updated | last_edited_time | `notion_last_edited` | Included for sync staleness detection |
| 76 | Last edited by | last_edited_by | *SKIPPED* | System metadata only |

### Formula (9) -- SKIPPED

| # | Property Name | Likely Computation | Notes |
|---|--------------|-------------------|-------|
| 77 | Bottoms-Up Reserve | f(BU Reserve Defend, BU Reserve No Defend, BU Follow-On Tag) | Can recompute in PG view |
| 78 | Est. Capital In | f(Entry Cheque, Reserve Deployed, Fresh Committed) | Can recompute in PG view |
| 79 | FMV Last Round | f(Ownership %, Last Round Valuation) | Can recompute in PG view |
| 80 | Last round raise | f(Entry Round Raise, Round 2 Raise, Round 3 Raise) | Can recompute in PG view |
| 81 | Money In | f(Entry Cheque, Reserve Deployed) | Can recompute in PG view |
| 82 | P&L | f(FMV Carried, Money In) | Can recompute in PG view |
| 83 | Top-Down Reserve | f(Earmarked Reserves, Reserve Deployed) | Can recompute in PG view |
| 84 | Top-Down Reserve OLD | (deprecated version of Top-Down Reserve) | Legacy |
| 85 | Total raise to date | f(Entry Round Raise, Round 2 Raise, Round 3 Raise) | Can recompute in PG view |

### Rollup (9) -- SKIPPED

| # | Property Name | Source | Notes |
|---|--------------|--------|-------|
| 86 | Angels | Rollup from related DB | Resolve via JOIN in PG |
| 87 | Co-Investors | Rollup from related DB | Resolve via JOIN in PG |
| 88 | Founders | Rollup from related DB | Resolve via JOIN in PG |
| 89 | Founding timeline | Rollup from related DB | Resolve via JOIN in PG |
| 90 | Funding to date | Rollup from related DB | Resolve via JOIN in PG |
| 91 | Pending Tasks | Rollup from related DB | Resolve via JOIN in PG |
| 92 | Sector | Rollup from Companies DB | Resolve via JOIN on company_name_id |
| 93 | Sector Tags | Rollup from Companies DB | Resolve via JOIN on company_name_id |
| 94 | Vault link | Rollup from Companies DB | Resolve via JOIN on company_name_id |

---

## Postgres Schema (Current State)

**Table `portfolio` does not exist.** This is a greenfield CREATE TABLE migration.

Existing tables in the database for reference:
- `companies` (32 columns) -- Companies DB mirror
- `network` (34 columns) -- Network DB mirror
- `thesis_threads`, `content_digests`, `actions_queue` -- other Notion DB mirrors
- `sync_metadata`, `sync_queue`, `change_events` -- sync infrastructure
- `cai_inbox`, `notifications`, `action_outcomes` -- agent infrastructure

---

## Cross-Reference Table

Since the Postgres table does not exist, all Notion fields are "MISSING IN PG" by definition. The mapping below documents the complete field-to-column plan.

| # | Notion Field | Notion Type | PG Column | PG Type | Status |
|---|-------------|-------------|-----------|---------|--------|
| 1 | Portfolio Co | title | `portfolio_co` | TEXT NOT NULL | TO CREATE |
| 2 | External Signal | text | `external_signal` | TEXT | TO CREATE |
| 3 | High Impact | text | `high_impact` | TEXT | TO CREATE |
| 4 | Key Questions | text | `key_questions` | TEXT | TO CREATE |
| 5 | Note on deployment | text | `note_on_deployment` | TEXT | TO CREATE |
| 6 | Scale of Business | text | `scale_of_business` | TEXT | TO CREATE |
| 7-34 | (28 select fields) | select | (28 TEXT columns) | TEXT | TO CREATE |
| 35-40 | (6 multi_select fields) | multi_select | (6 TEXT[] columns) | TEXT[] | TO CREATE |
| 41-63 | (23 number fields) | number | (20 NUMERIC + 3 REAL) | NUMERIC/REAL | TO CREATE |
| 64-65 | (2 date fields) | date | (2 DATE columns) | DATE | TO CREATE |
| 66-72 | (7 relation fields) | relation | (1 TEXT + 6 TEXT[]) | TEXT/TEXT[] | TO CREATE |
| 73-74 | (2 person fields) | person | (2 TEXT[] columns) | TEXT[] | TO CREATE |
| 75 | Last updated | last_edited_time | `notion_last_edited` | TIMESTAMPTZ | TO CREATE |
| 76 | Last edited by | last_edited_by | -- | -- | SKIP (system) |
| 77-85 | (9 formula fields) | formula | -- | -- | SKIP (computed) |
| 86-94 | (9 rollup fields) | rollup | -- | -- | SKIP (use JOINs) |
| -- | -- | -- | `id` | SERIAL PK | PG-ONLY |
| -- | -- | -- | `notion_page_id` | TEXT UNIQUE | PG-ONLY |
| -- | -- | -- | `research_file_path` | TEXT | PG-ONLY |
| -- | -- | -- | `enrichment_metadata` | JSONB | PG-ONLY |
| -- | -- | -- | `signal_history` | JSONB | PG-ONLY |
| -- | -- | -- | `created_at` | TIMESTAMPTZ | PG-ONLY |
| -- | -- | -- | `updated_at` | TIMESTAMPTZ | PG-ONLY |
| -- | -- | -- | `last_synced_at` | TIMESTAMPTZ | PG-ONLY |

---

## Design Decisions

### 1. NUMERIC vs REAL for Dollar Amounts
Dollar amounts use `NUMERIC` (arbitrary precision) rather than `REAL` (float32) to avoid floating-point precision issues with financial data. The companies table uses `REAL` for `last_round_amount` -- this is a known inconsistency that could be addressed in a future migration.

### 2. Percentage Fields as REAL
Ownership and dilution percentages are stored as `REAL` (0.0 to 1.0 range), matching the format Notion returns. This is consistent with how percentages work in financial calculations.

### 3. Two "Follow On Decision" Fields
Notion has two distinct fields: "Follow On Decision" (options: No Decision, Token/Zero, PR, SPR) and "Follow-on Decision" (options: Wait for 3 months, Closing, No for participation in strategic round). These are mapped to `follow_on_decision` and `follow_on_decision_alt` respectively.

### 4. Company Name as Single ID
`Company Name` relation has `limit=1` in Notion, so it maps to a single `TEXT` column (`company_name_id`) rather than `TEXT[]`. This acts as a foreign key to the companies table (via `notion_page_id`).

### 5. Formula and Rollup Fields Skipped
All 9 formula and 9 rollup fields are skipped from the table. The SQL includes a commented-out view definition showing how to recompute formulas in PG. Rollups are resolved via JOINs to `companies` and `network` tables.

### 6. Convention Alignment with Existing Tables
Column naming, default values, index patterns, and PG-only enrichment columns (`enrichment_metadata`, `signal_history`, `created_at`, `updated_at`, `last_synced_at`, `notion_page_id`) follow the same conventions as the `companies` and `network` tables.

---

## Data Observations (from 100 Live Rows)

- **Relation values** are stored as JSON arrays of Notion page URLs: `["https://www.notion.so/UUID"]`
- **Person values** use format: `["user://UUID"]`
- **Multi-select values** are JSON arrays of strings: `["Option A","Option B"]`
- **Formula values** return opaque references: `formulaResult://DB_ID/PAGE_ID/PROP_ID` (not actual values -- confirms skip decision)
- **Rollup values** return `<omitted />` in view queries (confirms skip decision)
- **Empty number fields** return empty string `""`, not null -- sync agent should handle this
- **Date fields** exposed as `date:Field Name:start` in view results (e.g., `date:Action Due Date:start`)
- All 100 rows have populated: `Portfolio Co`, `Today`, `Entry Cheque`, `Entry Round Valuation`, `Health`
- Many financial columns sparse: `Cash In Bank`, `Round 2/3 Raise/Val`, `Likely Outcome` often empty

---

## Migration SQL Location

`sql/portfolio-migration.sql`

- **Type:** CREATE TABLE (not ALTER -- table is greenfield)
- **Idempotent:** Uses `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`
- **Total columns:** 78 (69 from Notion + 8 PG-only + 1 PK)
- **Indexes:** 16 (1 unique + 12 btree + 3 GIN)
- **Includes:** `updated_at` trigger, formula view template (commented), full documentation comments
- **Status:** PREPARE ONLY -- do not execute without review

---

## Related Databases (for JOIN Planning)

| DB Name | Data Source ID | PG Table | Relation Fields |
|---------|---------------|----------|-----------------|
| Companies DB | `1edda9cc-df8b-41e1-9c08-22971495aa43` | `companies` | `company_name_id` |
| Network DB | `6462102f-112b-40e9-8984-7cb1e8fe5e8b` | `network` | `led_by_ids`, `sourcing_attribution_ids`, `participation_attribution_ids`, `venture_partner_old_ids` |
| Meeting Notes DB | `0dc61edf-2fab-47e2-8225-c677477f29b9` | (not yet in PG) | `meeting_notes_ids` |
| Unknown DB | `59c31a93-110d-4e80-a5ca-84c43f585ae2` | (not yet in PG) | `introduced_to_ids` |
