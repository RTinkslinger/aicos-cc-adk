# Notion -> Postgres Data Sync Plan

*Date: 2026-03-20*
*Databases: Companies, Network, Portfolio*
*Target: Supabase AI COS Mumbai (llfkxnsfczludgigknbs), PG17*

---

## Executive Summary

One-time bulk import of 3 Notion databases into Postgres, followed by an ongoing sync strategy. All three databases have `has_more: true` at 100 rows per view query, meaning pagination is required. The Portfolio DB has exactly 100 rows; Companies and Network DBs have significantly more.

---

## Phase 1: Schema Migration (Execute First)

### Execution Order

1. **Companies + Network ALTER TABLE** -- `sql/companies-network-migration.sql`
   - Adds 21 columns to `companies` (already has 32 -> becomes 53)
   - Adds 18 columns to `network` (already has 34 -> becomes 52)
   - Adds indexes on both tables
   - Idempotent (IF NOT EXISTS)

2. **Portfolio CREATE TABLE** -- `sql/portfolio-migration.sql`
   - Creates `portfolio` table from scratch (78 columns)
   - Adds 16 indexes
   - Adds `updated_at` trigger
   - Idempotent (CREATE TABLE IF NOT EXISTS)

### Validation After Schema Migration

```sql
-- Verify column counts
SELECT count(*) FROM information_schema.columns WHERE table_name = 'companies';  -- expect 53
SELECT count(*) FROM information_schema.columns WHERE table_name = 'network';    -- expect 52
SELECT count(*) FROM information_schema.columns WHERE table_name = 'portfolio';  -- expect 78

-- Verify tables still empty
SELECT count(*) FROM companies;   -- expect 0
SELECT count(*) FROM network;     -- expect 0
SELECT count(*) FROM portfolio;   -- expect 0
```

---

## Phase 2: Data Import Strategy

### Notion MCP Data Format Reference

Based on live queries against all 3 databases, the Notion MCP returns data in these formats:

| Notion Type | MCP Return Format | Example | Transformation |
|-------------|-------------------|---------|----------------|
| **title** | Plain string | `"Kintsugi"` | Direct insert |
| **rich_text** | Plain string | `"$1M ARR Realised as on Feb'25"` | Direct insert |
| **select** | Plain string | `"Portfolio"`, `"Green"` | Direct insert |
| **status** | Plain string | `"Portfolio"`, `"Likely Fast \| Late \| Low"` | Direct insert (pipe-delimited for multi-dimensional) |
| **multi_select** | JSON array string | `'["AI","Healthcare"]'` | Parse JSON -> PG `TEXT[]` |
| **number** | Native int or float | `240000` (int), `3.3` (float), `0.012199...` (float) | Direct insert; empty = NULL |
| **date** | Key pattern `date:<Name>:start` | `"2026-02-10"` (ISO date string) | Cast to DATE; absence = NULL |
| **checkbox** | JSON array with `"Yes"` | `'["Yes"]'` (Big Events Invite) | `'Yes' IN array` -> boolean true |
| **url** | Plain string | `"https://..."` | Direct insert; empty string = NULL |
| **relation** | JSON array of Notion page URLs | `'["https://www.notion.so/UUID1","https://www.notion.so/UUID2"]'` | Parse JSON, extract UUIDs -> PG `TEXT[]` |
| **person** | JSON array of user:// URIs | `'["user://3a14f1fb-d1e4-47ea-805d-edeca3193186"]'` | Parse JSON, extract UUIDs -> PG `TEXT[]` or `TEXT` |
| **formula** | Opaque reference | `"formulaResult://DB_ID/PAGE_ID/PROP_ID"` | **SKIP** |
| **rollup** | `"<omitted />"` | `"<omitted />"` | **SKIP** |
| **last_edited_time** | ISO timestamp | `"2025-11-29T10:33:53.052Z"` | Cast to TIMESTAMPTZ |
| **page URL** | `url` key in every row | `"https://www.notion.so/UUID"` | Extract UUID for `notion_page_id` |

### Key Extraction Functions

```
-- Extract page UUID from Notion URL
-- Input:  "https://www.notion.so/23829bccb6fc81f0ad62ecd94d5b6540"
-- Output: "23829bcc-b6fc-81f0-ad62-ecd94d5b6540"
-- Method: Take last path segment, insert hyphens at positions 8-4-4-4-12

-- Extract UUIDs from relation array
-- Input:  '["https://www.notion.so/UUID1","https://www.notion.so/UUID2"]'
-- Output: TEXT[] {'UUID1-with-hyphens', 'UUID2-with-hyphens'}

-- Extract user UUIDs from person array
-- Input:  '["user://3a14f1fb-d1e4-47ea-805d-edeca3193186"]'
-- Output: TEXT[] {'3a14f1fb-d1e4-47ea-805d-edeca3193186'}

-- Parse multi_select JSON array
-- Input:  '["AI","Healthcare"]'
-- Output: TEXT[] {'AI', 'Healthcare'}
```

### Pagination Strategy

The Notion MCP `notion-query-database-view` returns max 100 rows per call with `has_more: true/false`. However, **the Notion MCP does not expose a cursor/pagination parameter** -- each view query returns a fixed set of rows.

**Workaround: Use multiple views.** Each database has 5-20 views with different filters. Query each view and deduplicate by page URL.

**Better approach: Use `notion-fetch` on individual pages.** For databases with 100+ rows:
1. Query all available views -> collect all unique page URLs
2. For any pages missing fields (views hide some columns), fetch individual pages via `notion-fetch`
3. Deduplicate by `notion_page_id`

**Alternative for large databases:** Use filtered views (e.g., by Pipeline Status, by R/Y/G) to ensure all rows are captured.

**Row count estimates:**
| Database | Rows in Default View | Views Available | Estimated Total Rows |
|----------|---------------------|-----------------|---------------------|
| Companies | 100 (has_more=true) | 10 views | 500-2000+ |
| Network | 100 (has_more=true) | 9 views | 500-2000+ |
| Portfolio | 100 (has_more=true) | 20 views | 100-200 |

### View Coverage Issue

**Critical finding:** Different views expose different field sets. No single view contains all fields.

| Database | Fields in Best View | Fields in Schema | Missing from Best View |
|----------|-------------------|------------------|----------------------|
| Companies | 49 | 49 total (41 data fields) | `Meeting Notes`, `🌐 Network DB` (hidden in all queried views) |
| Network | 40 | 42 total (35 data fields) | `Tasks Pending`, `Meeting Notes`, `Leverage` (hidden in queried view) |
| Portfolio | 94 | 94 total (69 data fields) | `Meeting Notes` (hidden) |

**Impact:** Fields hidden from all views cannot be bulk-imported via view queries. Options:
1. **Fetch individual pages** for missing relation fields (expensive: 1 API call per row)
2. **Accept NULL** for hidden fields in initial import, populate incrementally later
3. **Create a custom Notion view** that shows all fields, then query it

**Recommended:** Option 2 for initial bulk import. The hidden fields (`Meeting Notes`, `🌐 Network DB`, `Tasks Pending`, `Leverage`) are LOW priority relations. Import what views expose, then backfill incrementally.

---

## Phase 3: Field Mapping Tables

### 3A. Companies DB (Notion -> Postgres)

| Notion Field | Notion Type | PG Column | PG Type | Transformation | View Exposed? |
|-------------|-------------|-----------|---------|----------------|---------------|
| `url` (page URL) | system | `notion_page_id` | TEXT | Extract UUID from URL, insert hyphens | YES |
| `Name` | title | `name` | TEXT NOT NULL | Direct | YES |
| `Pipeline Status` | status | `pipeline_status` | TEXT | Direct | YES |
| `Deal Status` | status | `deal_status` | TEXT | Direct (pipe-delimited) | YES |
| `Deal Status @ Discovery` | status | `deal_status_at_discovery` | TEXT | Direct | YES |
| `Sector` | select | `sector` | TEXT | Direct | YES |
| `Sector Tags` | multi_select | `sector_tags` | TEXT[] | Parse JSON array | YES |
| `Type` | select | `type` | TEXT | Direct | YES |
| `Priority` | select | `priority` | TEXT | Direct | YES |
| `Venture Funding` | select | `venture_funding` | TEXT | Direct | YES |
| `Founding Timeline` | select | `founding_timeline` | TEXT | Direct | YES |
| `Smart Money?` | select | `smart_money` | TEXT | Direct | YES |
| `HIL Review?` | select | `hil_review` | TEXT | Direct | YES |
| `JTBD` | multi_select | `jtbd` | TEXT[] | Parse JSON array | YES |
| `Sells To` | multi_select | `sells_to` | TEXT[] | Parse JSON array | YES |
| `Batch` | multi_select | `batch` | TEXT[] | Parse JSON array | YES |
| `Last Round $M` | number | `last_round_amount` | REAL | Direct (float/int) | YES |
| `Money Committed` | number | `money_committed` | REAL | Direct | YES |
| `Website` | url | `website` | TEXT | Direct; empty string -> NULL | YES |
| `Vault Link` | url | `vault_link` | TEXT | Direct; empty string -> NULL | YES |
| `Deck if link` | url | `deck_link` | TEXT | Direct; empty string -> NULL | YES |
| `Last Round Timing` | select | `last_round_timing` | TEXT | Direct | YES |
| `Action Due?` | date | `action_due` | DATE | From `date:Action Due?:start` key | YES |
| `Surface to collective` | date | `surface_to_collective` | DATE | From `date:Surface to collective:start` key | YES |
| `Current People` | relation | `current_people_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `Angels` | relation | `angel_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `Alums` | relation | `alum_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `MPI Connect` | relation | `mpi_connect_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `Domain Eval?` | relation | `domain_eval_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `Piped From` | relation | `piped_from_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `Met by?` | relation | `met_by_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `Shared with` | relation | `shared_with_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `YC Partner` | relation | `yc_partner_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `Investors (VCs, Micros)` | relation | `investor_company_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `Known Portfolio` | relation | `known_portfolio_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `💰 Finance DB` | relation | `finance_notion_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `Corp Dev` | relation | `corp_dev_notion_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES (view 1) |
| `Portfolio Interaction Notes` | relation | `portfolio_notion_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `Pending Tasks` | relation | `pending_task_ids` | TEXT[] | Parse JSON array, extract UUIDs | YES |
| `DeVC IP POC` | person | `devc_ip_poc` | TEXT | Parse JSON, extract first user UUID | YES |
| `Last edited time` | last_edited_time | `notion_last_edited` | TIMESTAMPTZ | Direct ISO timestamp | YES |
| `🌐 Network DB` | relation | `network_ids` | TEXT[] | Parse JSON array, extract UUIDs | **NO** |
| `Meeting Notes` | relation | `meeting_note_ids` | TEXT[] | Parse JSON array, extract UUIDs | **NO** |
| `AIF/USA` | formula | -- | -- | SKIP | -- |
| `Money In` | formula | -- | -- | SKIP | -- |
| `Ownership %` | formula | -- | -- | SKIP | -- |
| `AIF/USA (Rollup)` | rollup | -- | -- | SKIP | -- |
| `Money In (Rollup)` | rollup | -- | -- | SKIP | -- |
| `Ownership % (Rollup)` | rollup | -- | -- | SKIP | -- |
| `Created by` | system | -- | -- | SKIP | -- |

### 3B. Network DB (Notion -> Postgres)

| Notion Field | Notion Type | PG Column | PG Type | Transformation | View Exposed? |
|-------------|-------------|-----------|---------|----------------|---------------|
| `url` (page URL) | system | `notion_page_id` | TEXT | Extract UUID from URL | YES |
| `Name` | title | `person_name` | TEXT NOT NULL | Direct | YES |
| `Linkedin` | url | `linkedin` | TEXT | Direct | YES |
| `Current Role` | select | `current_role` | TEXT | Direct | YES |
| `Current Co` | relation | `current_company_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `Past Cos` | relation | `past_company_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `Home Base` | multi_select | `home_base` | TEXT[] | Parse JSON array | YES |
| `Local Network` | multi_select | `local_network_tags` | TEXT[] | Parse JSON array | YES |
| `Investorship` | multi_select | `investorship` | TEXT[] | Parse JSON array | YES |
| `Investing Activity` | select | `investing_activity` | TEXT | Direct | YES |
| `Angel Folio` | relation | `angel_folio_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `In Folio Of` | multi_select | `in_folio_of` | TEXT[] | Parse JSON array | YES |
| `Folio Franchise` | multi_select | `folio_franchise` | TEXT[] | Parse JSON array | YES |
| `Prev Foundership` | multi_select | `prev_foundership` | TEXT[] | Parse JSON array | YES |
| `Operating Franchise` | multi_select | `operating_franchise` | TEXT[] | Parse JSON array | YES |
| `R/Y/G` | select | `ryg` | TEXT | Direct | YES |
| `E/E Priority` | select | `e_e_priority` | TEXT | Direct | YES |
| `DeVC Relationship` | multi_select | `devc_relationship` | TEXT[] | Parse JSON array | YES |
| `DeVC POC` | person | `devc_poc` | TEXT | Parse JSON, extract first user UUID | YES |
| `Engagement Playbook` | multi_select | `engagement_playbook` | TEXT[] | Parse JSON array | YES |
| `Collective Flag` | multi_select | `collective_flag` | TEXT[] | Parse JSON array | YES |
| `Sourcing Attribution` | relation | `sourcing_attribution_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `Participation Attribution` | relation | `participation_attribution_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `Led by?` | relation | `led_by_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `Sourcing/Flow/HOTS` | select | `sourcing_flow_hots` | TEXT | Direct | YES |
| `Customer For` | multi_select | `customer_for` | TEXT[] | Parse JSON array | YES |
| `Big Events Invite` | checkbox-style | `big_events_invite` | TEXT[] | Parse JSON array (returns `["Yes"]`) | YES |
| `Piped to DeVC` | relation | `piped_to_devc_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `SaaS Buyer Type` | multi_select | `saas_buyer_type` | TEXT[] | Parse JSON array | YES |
| `Schools` | relation | `school_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `YC Partner Portfolio` | relation | `yc_partner_portfolio_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `C+E Speaker` | relation | `ce_speaker_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `C+E Attendance` | relation | `ce_attendance_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `Last edited time` | last_edited_time | `notion_last_edited` | TIMESTAMPTZ | Direct ISO timestamp | YES |
| `Meeting Notes` | relation | `meeting_note_ids` | TEXT[] | Parse JSON, extract UUIDs | **NO** |
| `Tasks Pending` | relation | `task_pending_ids` | TEXT[] | Parse JSON, extract UUIDs | **NO** |
| `Leverage` | multi_select | `leverage` | TEXT[] | Parse JSON array | **NO** |
| `Batch` | rollup | -- | -- | SKIP | -- |
| `Company Stage` | rollup | -- | -- | SKIP | -- |
| `Sector Classification` | rollup | -- | -- | SKIP | -- |
| `Network Tasks?` | deprecated | -- | -- | SKIP | -- |
| `Unstructured Leads` | deprecated | -- | -- | SKIP | -- |
| `Venture Partner? (old)` | deprecated | -- | -- | SKIP | -- |

### 3C. Portfolio DB (Notion -> Postgres)

| Notion Field | Notion Type | PG Column | PG Type | Transformation | View Exposed? |
|-------------|-------------|-----------|---------|----------------|---------------|
| `url` (page URL) | system | `notion_page_id` | TEXT | Extract UUID from URL | YES |
| `Portfolio Co` | title | `portfolio_co` | TEXT NOT NULL | Direct | YES |
| `Company Name` | relation (limit=1) | `company_name_id` | TEXT | Parse JSON, extract single UUID | YES |
| `Led by?` | relation | `led_by_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `Sourcing Attribution` | relation | `sourcing_attribution_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `Participation Attribution` | relation | `participation_attribution_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `Venture Partner? (old)` | relation | `venture_partner_old_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `Introduced to?` | relation | `introduced_to_ids` | TEXT[] | Parse JSON, extract UUIDs | YES |
| `IP Assigned` | person | `ip_assigned` | TEXT[] | Parse JSON, extract user UUIDs | YES |
| `MD Assigned` | person | `md_assigned` | TEXT[] | Parse JSON, extract user UUIDs | YES |
| `$500K candidate?` | select | `five_hundred_k_candidate` | TEXT | Direct | YES |
| `AIF/USA` | select | `aif_usa` | TEXT | Direct | YES |
| `BU Follow-On Tag` | select | `bu_follow_on_tag` | TEXT | Direct | YES |
| `Check-In Cadence` | select | `check_in_cadence` | TEXT | Direct | YES |
| `Current Stage` | select | `current_stage` | TEXT | Direct | YES |
| `Deep Dive` | select | `deep_dive` | TEXT | Direct | YES |
| `EF/EO` | select | `ef_eo` | TEXT | Direct | YES |
| `Follow On Decision` | select | `follow_on_decision` | TEXT | Direct | YES |
| `Follow-on Decision` | select | `follow_on_decision_alt` | TEXT | Direct (separate field!) | YES |
| `HC Priority` | select | `hc_priority` | TEXT | Direct (strip emoji prefix) | YES |
| `Health` | select | `health` | TEXT | Direct | YES |
| `IP Pull` | select | `ip_pull` | TEXT | Direct | YES |
| `Investment Timeline` | select | `investment_timeline` | TEXT | Direct | YES |
| `Likely Follow On Decision?` | select | `likely_follow_on_decision` | TEXT | Direct | YES |
| `Next 3 months IC Candidate` | select | `next_3m_ic_candidate` | TEXT | Direct | YES |
| `Ops Prio` | select | `ops_prio` | TEXT | Direct (strip emoji prefix) | YES |
| `Outcome Category` | select | `outcome_category` | TEXT | Direct | YES |
| `Raised Follow-on funding?` | select | `raised_follow_on_funding` | TEXT | Direct | YES |
| `Referenceability` | select | `referenceability` | TEXT | Direct | YES |
| `Revenue Generating` | select | `revenue_generating` | TEXT | Direct | YES |
| `Round 1 Type` | select | `round_1_type` | TEXT | Direct | YES |
| `Round 2 Type` | select | `round_2_type` | TEXT | Direct | YES |
| `Round 3 Type` | select | `round_3_type` | TEXT | Direct | YES |
| `Spikey` | select | `spikey` | TEXT | Direct | YES |
| `Stage @ entry` | select | `stage_at_entry` | TEXT | Direct | YES |
| `Tier 1 and Marquee seed cap table` | select | `tier_1_marquee_cap_table` | TEXT | Direct | YES |
| `Today` | select | `today` | TEXT | Direct | YES |
| `UW Decision` | select | `uw_decision` | TEXT | Direct | YES |
| `FY23-24 Compliance` | multi_select | `fy23_24_compliance` | TEXT[] | Parse JSON array | YES |
| `Follow On Outcome` | multi_select | `follow_on_outcome` | TEXT[] | Parse JSON array | YES |
| `Follow-on Work Priority` | multi_select | `follow_on_work_priority` | TEXT[] | Parse JSON array | YES |
| `Next Round Status` | multi_select | `next_round_status` | TEXT[] | Parse JSON array | YES |
| `PStatus` | multi_select | `pstatus` | TEXT[] | Parse JSON array | YES |
| `Timing of Involvement?` | multi_select | `timing_of_involvement` | TEXT[] | Parse JSON array | YES |
| `Entry Cheque` | number | `entry_cheque` | NUMERIC | Direct (int/float) | YES |
| `Entry Round Raise` | number | `entry_round_raise` | NUMERIC | Direct | YES |
| `Entry Round Valuation` | number | `entry_round_valuation` | NUMERIC | Direct | YES |
| `Last Round Valuation` | number | `last_round_valuation` | NUMERIC | Direct | YES |
| `FMV Carried` | number | `fmv_carried` | NUMERIC | Direct | YES |
| `BU Reserve Defend` | number | `bu_reserve_defend` | NUMERIC | Direct | YES |
| `BU Reserve No Defend` | number | `bu_reserve_no_defend` | NUMERIC | Direct | YES |
| `Earmarked Reserves` | number | `earmarked_reserves` | NUMERIC | Direct | YES |
| `Reserve Committed` | number | `reserve_committed` | NUMERIC | Direct | YES |
| `Reserve Deployed` | number | `reserve_deployed` | NUMERIC | Direct | YES |
| `Fresh Committed` | number | `fresh_committed` | NUMERIC | Direct | YES |
| `Cash In Bank` | number | `cash_in_bank` | NUMERIC | Direct | YES |
| `Room to deploy?` | number | `room_to_deploy` | NUMERIC | Direct | YES |
| `Round 2 Raise` | number | `round_2_raise` | NUMERIC | Direct | YES |
| `Round 2 Val` | number | `round_2_val` | NUMERIC | Direct | YES |
| `Round 3 Raise` | number | `round_3_raise` | NUMERIC | Direct | YES |
| `Round 3 Val` | number | `round_3_val` | NUMERIC | Direct | YES |
| `Best case outcome` | number | `best_case_outcome` | NUMERIC | Direct | YES |
| `Good Case outcome` | number | `good_case_outcome` | NUMERIC | Direct | YES |
| `Likely Outcome` | number | `likely_outcome` | NUMERIC | Direct | YES |
| `Ownership %` | number (percent) | `ownership_pct` | REAL | Direct (already 0.0-1.0) | YES |
| `Dilution IF Defend` | number (percent) | `dilution_if_defend` | REAL | Direct | YES |
| `Dilution IF NO Defend` | number (percent) | `dilution_if_no_defend` | REAL | Direct | YES |
| `External Signal` | text | `external_signal` | TEXT | Direct | YES |
| `High Impact` | text | `high_impact` | TEXT | Direct | YES |
| `Key Questions` | text | `key_questions` | TEXT | Direct | YES |
| `Note on deployment` | text | `note_on_deployment` | TEXT | Direct | YES |
| `Scale of Business` | text | `scale_of_business` | TEXT | Direct | YES |
| `Action Due Date` | date | `action_due_date` | DATE | From `date:Action Due Date:start` key | YES |
| `Fumes Date` | date | `fumes_date` | DATE | From `date:Fumes Date:start` key | YES (sparse) |
| `Last updated` | last_edited_time | `notion_last_edited` | TIMESTAMPTZ | Direct ISO timestamp | YES |
| `Meeting Notes` | relation | `meeting_notes_ids` | TEXT[] | Parse JSON, extract UUIDs | **NO** |
| All 9 formulas | formula | -- | -- | SKIP | -- |
| All 9 rollups | rollup | -- | -- | SKIP | -- |
| `Last edited by` | system | -- | -- | SKIP | -- |

---

## Phase 4: Transformation Functions

### UUID Extraction from Notion URLs

Notion page URLs come in format: `https://www.notion.so/HEXSTRING` where HEXSTRING is 32 hex chars (UUID without hyphens).

```python
def extract_notion_uuid(url: str) -> str:
    """Extract UUID from Notion page URL.
    Input:  'https://www.notion.so/23829bccb6fc81f0ad62ecd94d5b6540'
    Output: '23829bcc-b6fc-81f0-ad62-ecd94d5b6540'
    """
    hex_id = url.rstrip('/').split('/')[-1]
    # Handle URLs that may have title slugs: take last 32 hex chars
    hex_id = hex_id[-32:]
    return f"{hex_id[:8]}-{hex_id[8:12]}-{hex_id[12:16]}-{hex_id[16:20]}-{hex_id[20:]}"
```

### Relation Field Parsing

```python
import json

def parse_relation_ids(value: str) -> list[str]:
    """Parse relation field into list of UUIDs.
    Input:  '["https://www.notion.so/UUID1","https://www.notion.so/UUID2"]'
    Output: ['uuid1-with-hyphens', 'uuid2-with-hyphens']
    """
    if not value or value in ('', '[]'):
        return []
    urls = json.loads(value)
    return [extract_notion_uuid(url) for url in urls]
```

### Person Field Parsing

```python
def parse_person_ids(value: str) -> list[str]:
    """Parse person field into list of user UUIDs.
    Input:  '["user://3a14f1fb-d1e4-47ea-805d-edeca3193186"]'
    Output: ['3a14f1fb-d1e4-47ea-805d-edeca3193186']
    """
    if not value or value in ('', '[]'):
        return []
    users = json.loads(value)
    return [u.replace('user://', '') for u in users]
```

### Multi-Select Field Parsing

```python
def parse_multi_select(value: str) -> list[str]:
    """Parse multi_select field into list of strings.
    Input:  '["AI","Healthcare"]'
    Output: ['AI', 'Healthcare']
    """
    if not value or value in ('', '[]'):
        return []
    return json.loads(value)
```

### Date Field Extraction

```python
def extract_date(row: dict, notion_field_name: str) -> str | None:
    """Extract date from Notion's split key format.
    Notion returns dates as: date:<FieldName>:start = '2026-02-10'
    Also includes:          date:<FieldName>:is_datetime = 0|1
    """
    key = f"date:{notion_field_name}:start"
    value = row.get(key)
    if not value or value == '':
        return None
    return value  # Already ISO format: 'YYYY-MM-DD'
```

### Number Field Handling

```python
def parse_number(value) -> float | None:
    """Handle Notion number field edge cases.
    - Empty/missing fields: None (NULL in PG)
    - Integer values: 240000 (type: int)
    - Float values: 3.3 (type: float)
    - Zero: 0 (valid, preserve)
    """
    if value is None or value == '' or value == '<omitted />':
        return None
    return float(value)
```

### Empty String Normalization

```python
def normalize_text(value: str) -> str | None:
    """Normalize text fields.
    Empty strings -> NULL for url/optional fields, '' for text fields.
    """
    if value is None or value == '<omitted />' or value.startswith('formulaResult://'):
        return None
    return value
```

---

## Phase 5: Error Handling

### NULL Values and Missing Fields

| Scenario | Handling |
|----------|---------|
| Field absent from row | INSERT as NULL (PG columns have DEFAULT or allow NULL) |
| Empty string `""` | For URL columns: NULL. For TEXT columns: empty string `''` |
| Formula references `formulaResult://...` | SKIP (don't insert) |
| Rollup omissions `<omitted />` | SKIP (don't insert) |
| Relation `"[]"` (empty array) | Insert as `'{}'::TEXT[]` |
| Number field empty | NULL |
| Date field absent (no `date:X:start` key) | NULL |

### Data Quality Guards

1. **Required fields:** `name` (companies), `person_name` (network), `portfolio_co` (portfolio) must be non-empty. Skip row if title is empty.
2. **Duplicate detection:** Use `notion_page_id` as unique key. ON CONFLICT (notion_page_id) DO UPDATE for upsert behavior.
3. **UUID format validation:** All extracted UUIDs must match pattern `[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}`.
4. **Array length guards:** Relation arrays can have 0-20+ entries. No length limit needed (PG TEXT[] is unbounded).

---

## Phase 6: SQL INSERT Templates

### 6A. Companies INSERT (Upsert)

```sql
INSERT INTO companies (
    -- Sync infrastructure
    notion_page_id, last_synced_at, notion_last_edited,
    -- Title
    name,
    -- Select fields
    pipeline_status, deal_status, deal_status_at_discovery, sector, type,
    priority, venture_funding, founding_timeline, smart_money, hil_review,
    last_round_timing,
    -- Multi-select fields
    sector_tags, jtbd, sells_to, batch,
    -- Number fields
    last_round_amount, money_committed,
    -- URL fields
    website, vault_link, deck_link,
    -- Date fields
    action_due, surface_to_collective,
    -- Relation fields (Notion page ID arrays)
    current_people_ids, angel_ids, alum_ids, mpi_connect_ids,
    domain_eval_ids, piped_from_ids, met_by_ids, shared_with_ids,
    yc_partner_ids, network_ids, investor_company_ids, known_portfolio_ids,
    finance_notion_ids, corp_dev_notion_ids, portfolio_notion_ids,
    pending_task_ids, meeting_note_ids,
    -- Person field
    devc_ip_poc
)
VALUES (
    $1,                     -- notion_page_id (TEXT, extracted from url)
    now(),                  -- last_synced_at
    $2,                     -- notion_last_edited (TIMESTAMPTZ)
    $3,                     -- name (TEXT NOT NULL)
    $4, $5, $6, $7, $8,    -- select fields
    $9, $10, $11, $12, $13,
    $14,
    $15, $16, $17, $18,     -- multi_select (TEXT[])
    $19, $20,               -- number (REAL)
    $21, $22, $23,          -- url (TEXT)
    $24, $25,               -- date (DATE)
    $26, $27, $28, $29,     -- relation arrays (TEXT[])
    $30, $31, $32, $33,
    $34, $35, $36, $37,
    $38, $39, $40,
    $41, $42,
    $43                     -- person (TEXT)
)
ON CONFLICT (notion_page_id) DO UPDATE SET
    last_synced_at = now(),
    notion_last_edited = EXCLUDED.notion_last_edited,
    name = EXCLUDED.name,
    pipeline_status = EXCLUDED.pipeline_status,
    deal_status = EXCLUDED.deal_status,
    deal_status_at_discovery = EXCLUDED.deal_status_at_discovery,
    sector = EXCLUDED.sector,
    type = EXCLUDED.type,
    priority = EXCLUDED.priority,
    venture_funding = EXCLUDED.venture_funding,
    founding_timeline = EXCLUDED.founding_timeline,
    smart_money = EXCLUDED.smart_money,
    hil_review = EXCLUDED.hil_review,
    last_round_timing = EXCLUDED.last_round_timing,
    sector_tags = EXCLUDED.sector_tags,
    jtbd = EXCLUDED.jtbd,
    sells_to = EXCLUDED.sells_to,
    batch = EXCLUDED.batch,
    last_round_amount = EXCLUDED.last_round_amount,
    money_committed = EXCLUDED.money_committed,
    website = EXCLUDED.website,
    vault_link = EXCLUDED.vault_link,
    deck_link = EXCLUDED.deck_link,
    action_due = EXCLUDED.action_due,
    surface_to_collective = EXCLUDED.surface_to_collective,
    current_people_ids = EXCLUDED.current_people_ids,
    angel_ids = EXCLUDED.angel_ids,
    alum_ids = EXCLUDED.alum_ids,
    mpi_connect_ids = EXCLUDED.mpi_connect_ids,
    domain_eval_ids = EXCLUDED.domain_eval_ids,
    piped_from_ids = EXCLUDED.piped_from_ids,
    met_by_ids = EXCLUDED.met_by_ids,
    shared_with_ids = EXCLUDED.shared_with_ids,
    yc_partner_ids = EXCLUDED.yc_partner_ids,
    network_ids = EXCLUDED.network_ids,
    investor_company_ids = EXCLUDED.investor_company_ids,
    known_portfolio_ids = EXCLUDED.known_portfolio_ids,
    finance_notion_ids = EXCLUDED.finance_notion_ids,
    corp_dev_notion_ids = EXCLUDED.corp_dev_notion_ids,
    portfolio_notion_ids = EXCLUDED.portfolio_notion_ids,
    pending_task_ids = EXCLUDED.pending_task_ids,
    meeting_note_ids = EXCLUDED.meeting_note_ids,
    devc_ip_poc = EXCLUDED.devc_ip_poc;
```

### 6B. Network INSERT (Upsert)

```sql
INSERT INTO network (
    -- Sync infrastructure
    notion_page_id, last_synced_at, notion_last_edited,
    -- Title
    person_name,
    -- URL
    linkedin,
    -- Select fields
    current_role, ryg, e_e_priority, sourcing_flow_hots, investing_activity,
    -- Multi-select fields
    home_base, local_network_tags, investorship, devc_relationship,
    collective_flag, engagement_playbook, leverage, customer_for,
    big_events_invite, in_folio_of, saas_buyer_type, folio_franchise,
    operating_franchise, prev_foundership,
    -- Relation fields
    current_company_ids, past_company_ids, school_ids, angel_folio_ids,
    sourcing_attribution_ids, participation_attribution_ids, led_by_ids,
    piped_to_devc_ids, yc_partner_portfolio_ids,
    ce_speaker_ids, ce_attendance_ids, meeting_note_ids, task_pending_ids,
    -- Person field
    devc_poc
)
VALUES (
    $1,              -- notion_page_id
    now(),           -- last_synced_at
    $2,              -- notion_last_edited
    $3,              -- person_name (TEXT NOT NULL)
    $4,              -- linkedin
    $5, $6, $7, $8, $9,  -- select fields
    $10, $11, $12, $13,  -- multi_select arrays
    $14, $15, $16, $17,
    $18, $19, $20, $21,
    $22, $23,
    $24, $25, $26, $27,  -- relation arrays
    $28, $29, $30,
    $31, $32,
    $33, $34, $35, $36,
    $37               -- person (TEXT)
)
ON CONFLICT (notion_page_id) DO UPDATE SET
    last_synced_at = now(),
    notion_last_edited = EXCLUDED.notion_last_edited,
    person_name = EXCLUDED.person_name,
    linkedin = EXCLUDED.linkedin,
    current_role = EXCLUDED.current_role,
    ryg = EXCLUDED.ryg,
    e_e_priority = EXCLUDED.e_e_priority,
    sourcing_flow_hots = EXCLUDED.sourcing_flow_hots,
    investing_activity = EXCLUDED.investing_activity,
    home_base = EXCLUDED.home_base,
    local_network_tags = EXCLUDED.local_network_tags,
    investorship = EXCLUDED.investorship,
    devc_relationship = EXCLUDED.devc_relationship,
    collective_flag = EXCLUDED.collective_flag,
    engagement_playbook = EXCLUDED.engagement_playbook,
    leverage = EXCLUDED.leverage,
    customer_for = EXCLUDED.customer_for,
    big_events_invite = EXCLUDED.big_events_invite,
    in_folio_of = EXCLUDED.in_folio_of,
    saas_buyer_type = EXCLUDED.saas_buyer_type,
    folio_franchise = EXCLUDED.folio_franchise,
    operating_franchise = EXCLUDED.operating_franchise,
    prev_foundership = EXCLUDED.prev_foundership,
    current_company_ids = EXCLUDED.current_company_ids,
    past_company_ids = EXCLUDED.past_company_ids,
    school_ids = EXCLUDED.school_ids,
    angel_folio_ids = EXCLUDED.angel_folio_ids,
    sourcing_attribution_ids = EXCLUDED.sourcing_attribution_ids,
    participation_attribution_ids = EXCLUDED.participation_attribution_ids,
    led_by_ids = EXCLUDED.led_by_ids,
    piped_to_devc_ids = EXCLUDED.piped_to_devc_ids,
    yc_partner_portfolio_ids = EXCLUDED.yc_partner_portfolio_ids,
    ce_speaker_ids = EXCLUDED.ce_speaker_ids,
    ce_attendance_ids = EXCLUDED.ce_attendance_ids,
    meeting_note_ids = EXCLUDED.meeting_note_ids,
    task_pending_ids = EXCLUDED.task_pending_ids,
    devc_poc = EXCLUDED.devc_poc;
```

### 6C. Portfolio INSERT (Upsert)

```sql
INSERT INTO portfolio (
    -- Sync infrastructure
    notion_page_id, last_synced_at, notion_last_edited,
    -- Title
    portfolio_co,
    -- Relation fields
    company_name_id, led_by_ids, sourcing_attribution_ids,
    participation_attribution_ids, venture_partner_old_ids,
    meeting_notes_ids, introduced_to_ids,
    -- Person fields
    ip_assigned, md_assigned,
    -- Select fields (28)
    five_hundred_k_candidate, aif_usa, bu_follow_on_tag, check_in_cadence,
    current_stage, deep_dive, ef_eo, follow_on_decision, follow_on_decision_alt,
    hc_priority, health, ip_pull, investment_timeline,
    likely_follow_on_decision, next_3m_ic_candidate, ops_prio,
    outcome_category, raised_follow_on_funding, referenceability,
    revenue_generating, round_1_type, round_2_type, round_3_type,
    spikey, stage_at_entry, tier_1_marquee_cap_table, today, uw_decision,
    -- Multi-select fields (6)
    fy23_24_compliance, follow_on_outcome, follow_on_work_priority,
    next_round_status, pstatus, timing_of_involvement,
    -- Number fields - dollar amounts (20)
    entry_cheque, entry_round_raise, entry_round_valuation,
    last_round_valuation, fmv_carried, bu_reserve_defend, bu_reserve_no_defend,
    earmarked_reserves, reserve_committed, reserve_deployed,
    fresh_committed, cash_in_bank, room_to_deploy,
    round_2_raise, round_2_val, round_3_raise, round_3_val,
    best_case_outcome, good_case_outcome, likely_outcome,
    -- Number fields - percentages (3)
    ownership_pct, dilution_if_defend, dilution_if_no_defend,
    -- Text fields (5)
    external_signal, high_impact, key_questions, note_on_deployment, scale_of_business,
    -- Date fields (2)
    action_due_date, fumes_date
)
VALUES (
    $1,              -- notion_page_id
    now(),           -- last_synced_at
    $2,              -- notion_last_edited
    $3,              -- portfolio_co (TEXT NOT NULL)
    $4, $5, $6,      -- relation fields
    $7, $8,
    $9, $10,
    $11, $12,        -- person fields
    $13, $14, $15, $16,  -- select fields
    $17, $18, $19, $20, $21,
    $22, $23, $24, $25,
    $26, $27, $28,
    $29, $30, $31,
    $32, $33, $34, $35,
    $36, $37, $38, $39, $40,
    $41, $42, $43, $44,  -- multi_select arrays
    $45, $46,
    $47, $48, $49,       -- number - dollars
    $50, $51, $52, $53,
    $54, $55, $56,
    $57, $58, $59,
    $60, $61, $62, $63,
    $64, $65, $66,
    $67, $68, $69,       -- number - pct
    $70, $71, $72, $73, $74,  -- text
    $75, $76              -- date
)
ON CONFLICT (notion_page_id) DO UPDATE SET
    last_synced_at = now(),
    notion_last_edited = EXCLUDED.notion_last_edited,
    portfolio_co = EXCLUDED.portfolio_co,
    company_name_id = EXCLUDED.company_name_id,
    led_by_ids = EXCLUDED.led_by_ids,
    sourcing_attribution_ids = EXCLUDED.sourcing_attribution_ids,
    participation_attribution_ids = EXCLUDED.participation_attribution_ids,
    venture_partner_old_ids = EXCLUDED.venture_partner_old_ids,
    meeting_notes_ids = EXCLUDED.meeting_notes_ids,
    introduced_to_ids = EXCLUDED.introduced_to_ids,
    ip_assigned = EXCLUDED.ip_assigned,
    md_assigned = EXCLUDED.md_assigned,
    five_hundred_k_candidate = EXCLUDED.five_hundred_k_candidate,
    aif_usa = EXCLUDED.aif_usa,
    bu_follow_on_tag = EXCLUDED.bu_follow_on_tag,
    check_in_cadence = EXCLUDED.check_in_cadence,
    current_stage = EXCLUDED.current_stage,
    deep_dive = EXCLUDED.deep_dive,
    ef_eo = EXCLUDED.ef_eo,
    follow_on_decision = EXCLUDED.follow_on_decision,
    follow_on_decision_alt = EXCLUDED.follow_on_decision_alt,
    hc_priority = EXCLUDED.hc_priority,
    health = EXCLUDED.health,
    ip_pull = EXCLUDED.ip_pull,
    investment_timeline = EXCLUDED.investment_timeline,
    likely_follow_on_decision = EXCLUDED.likely_follow_on_decision,
    next_3m_ic_candidate = EXCLUDED.next_3m_ic_candidate,
    ops_prio = EXCLUDED.ops_prio,
    outcome_category = EXCLUDED.outcome_category,
    raised_follow_on_funding = EXCLUDED.raised_follow_on_funding,
    referenceability = EXCLUDED.referenceability,
    revenue_generating = EXCLUDED.revenue_generating,
    round_1_type = EXCLUDED.round_1_type,
    round_2_type = EXCLUDED.round_2_type,
    round_3_type = EXCLUDED.round_3_type,
    spikey = EXCLUDED.spikey,
    stage_at_entry = EXCLUDED.stage_at_entry,
    tier_1_marquee_cap_table = EXCLUDED.tier_1_marquee_cap_table,
    today = EXCLUDED.today,
    uw_decision = EXCLUDED.uw_decision,
    fy23_24_compliance = EXCLUDED.fy23_24_compliance,
    follow_on_outcome = EXCLUDED.follow_on_outcome,
    follow_on_work_priority = EXCLUDED.follow_on_work_priority,
    next_round_status = EXCLUDED.next_round_status,
    pstatus = EXCLUDED.pstatus,
    timing_of_involvement = EXCLUDED.timing_of_involvement,
    entry_cheque = EXCLUDED.entry_cheque,
    entry_round_raise = EXCLUDED.entry_round_raise,
    entry_round_valuation = EXCLUDED.entry_round_valuation,
    last_round_valuation = EXCLUDED.last_round_valuation,
    fmv_carried = EXCLUDED.fmv_carried,
    bu_reserve_defend = EXCLUDED.bu_reserve_defend,
    bu_reserve_no_defend = EXCLUDED.bu_reserve_no_defend,
    earmarked_reserves = EXCLUDED.earmarked_reserves,
    reserve_committed = EXCLUDED.reserve_committed,
    reserve_deployed = EXCLUDED.reserve_deployed,
    fresh_committed = EXCLUDED.fresh_committed,
    cash_in_bank = EXCLUDED.cash_in_bank,
    room_to_deploy = EXCLUDED.room_to_deploy,
    round_2_raise = EXCLUDED.round_2_raise,
    round_2_val = EXCLUDED.round_2_val,
    round_3_raise = EXCLUDED.round_3_raise,
    round_3_val = EXCLUDED.round_3_val,
    best_case_outcome = EXCLUDED.best_case_outcome,
    good_case_outcome = EXCLUDED.good_case_outcome,
    likely_outcome = EXCLUDED.likely_outcome,
    ownership_pct = EXCLUDED.ownership_pct,
    dilution_if_defend = EXCLUDED.dilution_if_defend,
    dilution_if_no_defend = EXCLUDED.dilution_if_no_defend,
    external_signal = EXCLUDED.external_signal,
    high_impact = EXCLUDED.high_impact,
    key_questions = EXCLUDED.key_questions,
    note_on_deployment = EXCLUDED.note_on_deployment,
    scale_of_business = EXCLUDED.scale_of_business,
    action_due_date = EXCLUDED.action_due_date,
    fumes_date = EXCLUDED.fumes_date;
```

---

## Phase 7: Import Execution Plan

### Step-by-Step Execution Order

```
1. RUN schema migrations (Phase 1)
   ├── sql/companies-network-migration.sql
   └── sql/portfolio-migration.sql

2. IMPORT Portfolio DB (smallest, 100-200 rows)
   ├── Query view://bb57f1d8-a105-4f33-b6f8-5299331f71f9 (default view, 94 fields)
   ├── Query additional views if has_more=true
   ├── Deduplicate by page URL
   ├── Transform each row using functions from Phase 4
   └── Execute upsert (Phase 6C template)

3. IMPORT Companies DB (medium, 500-2000+ rows)
   ├── Query view://12429bcc-b6fc-80ca-bbb1-000ce04a37ae (49 fields, widest)
   ├── Query additional views for remaining rows:
   │   ├── view://10e29bcc-b6fc-8029-8e0f-000c420c8e1b (different filter)
   │   ├── view://12829bcc-b6fc-80dc-8e4c-000c629257c6
   │   ├── view://54bef418-53e4-4919-aac8-e4941972f913
   │   ├── view://13629bcc-b6fc-80c3-a273-000c4bde05f6
   │   ├── ... (10 views total)
   ├── Union results from view://10e29bcc for Corp Dev field
   ├── Deduplicate by page URL
   ├── Transform each row
   └── Execute upsert (Phase 6A template)

4. IMPORT Network DB (large, 500-2000+ rows)
   ├── Query view://2638c865-9881-4b0a-80e1-63e2c78dff18 (40 fields)
   ├── Query additional views:
   │   ├── view://15229bcc-b6fc-80fd-9bf1-000ce8449936
   │   ├── view://5da69433-9e8f-4705-a83c-95949c68b619
   │   ├── ... (9 views total)
   ├── Deduplicate by page URL
   ├── Transform each row
   └── Execute upsert (Phase 6B template)

5. VALIDATE (Phase 8)
```

### Per-Database Import Loop (Pseudocode)

```python
all_rows = {}  # keyed by notion_page_id

for view_url in view_urls:
    result = notion_query_database_view(view_url)
    for row in result['results']:
        page_id = extract_notion_uuid(row['url'])
        if page_id in all_rows:
            # Merge: keep non-empty values from new row
            existing = all_rows[page_id]
            for key, value in row.items():
                if value and value != '' and value != '<omitted />' \
                   and not str(value).startswith('formulaResult://'):
                    existing[key] = value
        else:
            all_rows[page_id] = row

# Transform and insert
for page_id, row in all_rows.items():
    transformed = transform_row(row, field_mapping)
    execute_upsert(transformed)
```

---

## Phase 8: Post-Import Validation

### Row Count Verification

```sql
-- Compare PG counts against Notion
SELECT 'companies' as tbl, count(*) FROM companies WHERE notion_page_id IS NOT NULL
UNION ALL
SELECT 'network', count(*) FROM network WHERE notion_page_id IS NOT NULL
UNION ALL
SELECT 'portfolio', count(*) FROM portfolio WHERE notion_page_id IS NOT NULL;
```

Cross-reference against Notion: query all views, count unique page URLs.

### Data Quality Checks

```sql
-- Companies: verify no empty names
SELECT count(*) FROM companies WHERE name IS NULL OR name = '';

-- Network: verify no empty person_names
SELECT count(*) FROM network WHERE person_name IS NULL OR person_name = '';

-- Portfolio: verify no empty portfolio_co
SELECT count(*) FROM portfolio WHERE portfolio_co IS NULL OR portfolio_co = '';

-- Verify notion_page_id uniqueness (should return 0)
SELECT count(*) - count(DISTINCT notion_page_id) as duplicates FROM companies WHERE notion_page_id IS NOT NULL;
SELECT count(*) - count(DISTINCT notion_page_id) as duplicates FROM network WHERE notion_page_id IS NOT NULL;
SELECT count(*) - count(DISTINCT notion_page_id) as duplicates FROM portfolio WHERE notion_page_id IS NOT NULL;

-- Verify relation cross-references are valid
-- (companies.current_people_ids should reference network.notion_page_id values)
SELECT c.name, unnest(c.current_people_ids) as person_id
FROM companies c
WHERE c.current_people_ids != '{}'
LIMIT 10;

-- Check for orphaned relation IDs
SELECT count(*) as orphaned_people_refs
FROM companies c, unnest(c.current_people_ids) as pid
WHERE NOT EXISTS (SELECT 1 FROM network n WHERE n.notion_page_id = pid);

-- Portfolio -> Companies link integrity
SELECT p.portfolio_co, p.company_name_id
FROM portfolio p
WHERE p.company_name_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM companies c WHERE c.notion_page_id = p.company_name_id);
```

### Sample Spot-Checks

```sql
-- Verify specific known row: "Mello" in Companies DB
SELECT name, pipeline_status, priority, money_committed, sector,
       array_length(current_people_ids, 1) as people_count,
       action_due
FROM companies
WHERE name = 'Mello';
-- Expected: Pipeline=Portfolio, Priority=P0, Money=100000, Sector=Consumer, people=2, action_due=2025-07-30

-- Verify specific known row: "Kintsugi" in Portfolio DB
SELECT portfolio_co, today, entry_cheque, ownership_pct, health
FROM portfolio
WHERE portfolio_co = 'Kintsugi';
-- Expected: Today=Fund Priority, Entry=40000, Ownership=0.0122, Health=Green
```

---

## Phase 9: Ongoing Sync Strategy

### Recommended: Timestamp-Based Incremental Sync

**Trigger:** Manual or scheduled (cron on droplet, every 4-6 hours).

**Algorithm:**
1. Query each view (all views for full coverage)
2. For each row, check `Last edited time` against `notion_last_edited` in Postgres
3. If Notion timestamp > PG timestamp, upsert the row
4. Update `last_synced_at` on every touched row

**Detection query (PG side):**
```sql
-- Find rows that may be stale (not synced in 24h)
SELECT notion_page_id, name, notion_last_edited, last_synced_at
FROM companies
WHERE last_synced_at < now() - interval '24 hours'
   OR last_synced_at IS NULL
ORDER BY notion_last_edited DESC NULLS LAST;
```

### Alternative: Webhook/Event-Based (Future)

Notion does not offer native webhooks. Options:
- **Notion API polling** (not via MCP -- requires direct API access on droplet)
- **SyncAgent** (already exists in repo but disabled): `mcp-servers/agents/` contains sync agent code that could be adapted

### Sync Limitations

1. **View-hidden fields** (`Meeting Notes`, `🌐 Network DB`, `Tasks Pending`, `Leverage`) cannot be synced via view queries. They require individual page fetches or custom Notion views that expose them.
2. **Notion MCP pagination** returns max 100 rows per view. Large databases require querying multiple views.
3. **Deletion detection:** If a page is deleted from Notion, the sync will not detect it (no tombstone). Periodic full-scan comparison needed.
4. **Notion -> PG only:** This plan covers one-way sync. PG-only enrichment columns are never written back to Notion.

---

## Appendix A: View URL Registry

### Companies DB (10 views)
```
view://10e29bcc-b6fc-8029-8e0f-000c420c8e1b  (29 fields, has Corp Dev)
view://12429bcc-b6fc-80ca-bbb1-000ce04a37ae  (49 fields, widest)
view://12829bcc-b6fc-80dc-8e4c-000c629257c6
view://12929bcc-b6fc-8039-914b-000c76fe117d
view://12b29bcc-b6fc-80b8-a822-000c50702704
view://13429bcc-b6fc-80b1-aa40-000c42282734
view://13629bcc-b6fc-80c3-a273-000c4bde05f6
view://1167015a-e8f5-4f5f-b278-f4f41b74cf9a
view://18c29bcc-b6fc-80f6-806a-000c5f15a196
view://54bef418-53e4-4919-aac8-e4941972f913
```

### Network DB (9 views)
```
view://2638c865-9881-4b0a-80e1-63e2c78dff18  (40 fields, tested)
view://15229bcc-b6fc-80fd-9bf1-000ce8449936
view://15329bcc-b6fc-80c5-9b68-000cb8558fac
view://1cb29bcc-b6fc-8021-860e-000c9c1585c7
view://1d029bcc-b6fc-80ec-947f-000c4b61234b
view://1e329bcc-b6fc-808e-86ff-000c26b40494
view://27029bcc-b6fc-8081-b378-000c62ae2ad9
view://2c729bcc-b6fc-806c-8c08-000cf248bb84
view://5da69433-9e8f-4705-a83c-95949c68b619
```

### Portfolio DB (20 views)
```
view://bb57f1d8-a105-4f33-b6f8-5299331f71f9  (94 fields, default, tested)
view://12729bcc-b6fc-8007-9eec-000c66a75e09
view://12729bcc-b6fc-8035-8418-000c3f686b2f
view://12829bcc-b6fc-8073-9554-000c8c2a6535
view://12829bcc-b6fc-807e-a571-000caabac68f
view://12829bcc-b6fc-80a8-b8e4-000c674b32b3
view://12829bcc-b6fc-80ff-b157-000cfaae93d6
view://12929bcc-b6fc-80e2-b045-000c7b581836
view://12e29bcc-b6fc-802d-9ba6-000c55ddecad
view://12e29bcc-b6fc-8044-8fdd-000cfc9a416f
view://12e29bcc-b6fc-8078-b062-000c6042194a
view://12e29bcc-b6fc-808d-85ad-000c6b7ab637
view://12e29bcc-b6fc-8098-af94-000c11116c94
view://12e29bcc-b6fc-80c8-977e-000cb783df9d
view://12e29bcc-b6fc-80e0-b185-000cbac46012
view://12e29bcc-b6fc-80f4-852a-000c623e8813
view://13f29bcc-b6fc-80c9-8a97-000cd8a261d2
view://17629bcc-b6fc-8022-93dc-000cb458064f
view://1a629bcc-b6fc-80cb-8db2-000c54a3a878
view://1f729bcc-b6fc-8005-bb0b-000c3d5f9660
```

---

## Appendix B: Notion User ID Registry

Person fields contain `user://UUID` references. For human-readable names:

| User UUID | Likely Person |
|-----------|---------------|
| `3a14f1fb-d1e4-47ea-805d-edeca3193186` | (appears in MD Assigned, DeVC IP POC -- likely Aakash or senior MD) |
| `5bdd202e-47f0-4c71-800e-9538efabefff` | (appears in DeVC IP POC) |
| `88cda0ab-5ec0-4093-8956-704b568f2e21` | (appears in IP Assigned, DeVC POC) |
| `1e4d872b-594c-8145-b8df-000245081d59` | (appears in DeVC IP POC) |

To resolve these to names, use `notion-get-users` tool.
