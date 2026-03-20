# Cross-DB Relations Map: Portfolio, Companies, Network
*Date: 2026-03-20*
*Sources: Live Notion schemas via `collection://` data source URLs, live Postgres via `information_schema`, existing schema audit*

---

## Collection ID Registry

| Collection ID | Database Name | Postgres Table |
|---------------|---------------|----------------|
| `4dba9b7f-e623-41a5-9cb7-2af5976280ee` | Portfolio DB | **NONE** (no table exists) |
| `1edda9cc-df8b-41e1-9c08-22971495aa43` | Companies DB | `companies` (32 cols) |
| `6462102f-112b-40e9-8984-7cb1e8fe5e8b` | Network DB | `network` (34 cols) |
| `0dc61edf-2fab-47e2-8225-c677477f29b9` | Meeting Notes DB | — |
| `1b829bcc-b6fc-80fc-9da8-000b4927455b` | Tasks Tracker DB | — |
| `59c31a93-110d-4e80-a5ca-84c43f585ae2` | Unknown DB (inaccessible — likely Corp Dev or Introductions) | — |
| `9b59fd98-919d-4043-993d-eb7772659dd6` | Finance DB | — |
| `a9b347af-3e71-450e-9138-9e86114155c3` | C+E Events DB | — |
| `22729bcc-b6fc-8116-84fe-000b7d107368` | Network Tasks DB (alt tracker) | — |
| `9fef782f-d200-461f-874f-b14361bf2449` | Unstructured Leads DB | — |

---

## Complete Relation Graph

### Portfolio DB (94 fields, 7 relations, 9 rollups)

```
Portfolio DB (4dba9b7f)
│
├── Company Name ────────→ Companies DB (1edda9cc)     [limit=1, one-to-one]
│     Reverse in Companies: "Portfolio Interaction Notes"
│
├── Led by? ─────────────→ Network DB (6462102f)       [many-to-many]
│     Reverse in Network: "Led by?"
│
├── Sourcing Attribution ─→ Network DB (6462102f)       [many-to-many]
│     Reverse in Network: "Sourcing Attribution"
│
├── Participation Attr. ──→ Network DB (6462102f)       [many-to-many]
│     Reverse in Network: "Participation Attribution"
│
├── Venture Partner? (old) → Network DB (6462102f)      [DEPRECATED]
│     Reverse in Network: "Venture Partner? (old)"
│
├── Meeting Notes ────────→ Meeting Notes DB (0dc61edf) [many-to-many]
│
└── Introduced to? ───────→ Unknown DB (59c31a93)       [many-to-many]
      Inaccessible — likely Corp Dev or Introductions DB

Rollups (pull data through relations):
  Angels ──────────── via Company Name → Companies DB → Angels field
  Co-Investors ────── via Company Name → Companies DB → (investor info)
  Founders ────────── via Company Name → Companies DB → Current People
  Founding timeline ─ via Company Name → Companies DB → Founding Timeline
  Funding to date ─── via Company Name → Companies DB → Venture Funding
  Pending Tasks ───── via Company Name → Companies DB → Pending Tasks
  Sector ──────────── via Company Name → Companies DB → Sector
  Sector Tags ─────── via Company Name → Companies DB → Sector Tags
  Vault link ──────── via Company Name → Companies DB → Vault Link
```

### Companies DB (49 fields, 17 relations, 3 rollups)

```
Companies DB (1edda9cc)
│
│  ── Relations to Network DB (6462102f) ── [9 relations]
├── Current People ───────→ Network DB     [many-to-many]
│     Reverse in Network: "Current Co"
├── Angels ───────────────→ Network DB     [many-to-many]
│     Reverse in Network: "Angel Folio"
├── Alums ────────────────→ Network DB     [many-to-many]
│     Reverse in Network: (back-populated)
├── MPI Connect ──────────→ Network DB     [many-to-many]
├── Domain Eval? ─────────→ Network DB     [many-to-many]
├── Piped From ───────────→ Network DB     [many-to-many]
│     Reverse in Network: "Piped to DeVC"
├── Met by? ──────────────→ Network DB     [many-to-many]
├── Shared with ──────────→ Network DB     [many-to-many]
├── YC Partner ───────────→ Network DB     [many-to-many]
│     Reverse in Network: "YC Partner Portfolio"
├── 🌐 Network DB ────────→ Network DB     [many-to-many, generic catch-all]
│
│  ── Self-relations within Companies DB (1edda9cc) ── [2 relations]
├── Investors (VCs, Micros) → Companies DB (self)  [many-to-many]
├── Known Portfolio ────────→ Companies DB (self)  [many-to-many]
│
│  ── Relations to Portfolio DB (4dba9b7f) ── [1 relation]
├── Portfolio Interaction Notes → Portfolio DB  [many-to-many]
│     Reverse in Portfolio: "Company Name"
│
│  ── Relations to other DBs ── [5 relations]
├── Meeting Notes ────────→ Meeting Notes DB (0dc61edf)
├── Pending Tasks ────────→ Tasks Tracker DB (1b829bcc)
├── Corp Dev ─────────────→ Unknown DB (59c31a93)       [inaccessible]
├── 💰 Finance DB ─────────→ Finance DB (9b59fd98)
│
Rollups (pull data through relations):
  AIF/USA (Rollup) ──── via Portfolio Interaction Notes → Portfolio DB → AIF/USA
  Money In (Rollup) ─── via Portfolio Interaction Notes → Portfolio DB → Money In
  Ownership % (Rollup) ─ via Portfolio Interaction Notes → Portfolio DB → Ownership %
```

### Network DB (42 fields, 16 relations, 3 rollups)

```
Network DB (6462102f)
│
│  ── Relations to Companies DB (1edda9cc) ── [6 relations]
├── Current Co ───────────→ Companies DB   [many-to-many]
│     Reverse in Companies: "Current People"
├── Past Cos ─────────────→ Companies DB   [many-to-many]
│     Reverse in Companies: "Alums"
├── Schools ──────────────→ Companies DB   [many-to-many]
│     Schools stored as Companies DB entities
├── Angel Folio ──────────→ Companies DB   [many-to-many]
│     Reverse in Companies: "Angels"
├── Piped to DeVC ────────→ Companies DB   [many-to-many]
│     Reverse in Companies: "Piped From"
├── YC Partner Portfolio ──→ Companies DB   [many-to-many]
│     Reverse in Companies: "YC Partner"
│
│  ── Relations to Portfolio DB (4dba9b7f) ── [4 relations]
├── Sourcing Attribution ──→ Portfolio DB   [many-to-many]
│     Reverse in Portfolio: "Sourcing Attribution"
├── Participation Attr. ───→ Portfolio DB   [many-to-many]
│     Reverse in Portfolio: "Participation Attribution"
├── Led by? ───────────────→ Portfolio DB   [many-to-many]
│     Reverse in Portfolio: "Led by?"
├── Venture Partner? (old) → Portfolio DB   [DEPRECATED]
│     Reverse in Portfolio: "Venture Partner? (old)"
│
│  ── Relations to other DBs ── [6 relations]
├── Meeting Notes ─────────→ Meeting Notes DB (0dc61edf)
├── Tasks Pending ─────────→ Tasks Tracker DB (1b829bcc)
├── Network Tasks? ────────→ Alt Tasks DB (22729bcc)    [DEPRECATED]
├── C+E Speaker ───────────→ C+E Events DB (a9b347af)
├── C+E Attendance ────────→ C+E Events DB (a9b347af)
├── Unstructured Leads ────→ Leads DB (9fef782f)        [LEGACY]
│
Rollups (pull data through relations):
  Batch ──────────────── via Current Co → Companies DB → Batch
  Company Stage ──────── via Current Co → Companies DB → (stage field)
  Sector Classification ─ via Current Co → Companies DB → Sector
```

---

## Bidirectional Relation Pairs (All 3 DBs)

These are the Notion two-way relations where both sides are visible. Each pair shows the field name in each DB.

### Portfolio DB <-> Companies DB

| Portfolio DB Field | Companies DB Field | Semantics |
|---|---|---|
| **Company Name** (limit=1) | **Portfolio Interaction Notes** | Each portfolio entry links to exactly 1 company; a company can have multiple portfolio entries |

### Portfolio DB <-> Network DB

| Portfolio DB Field | Network DB Field | Semantics |
|---|---|---|
| **Led by?** | **Led by?** | People who led investment in this portfolio company |
| **Sourcing Attribution** | **Sourcing Attribution** | People who sourced this portfolio deal |
| **Participation Attribution** | **Participation Attribution** | People who co-invested |
| **Venture Partner? (old)** | **Venture Partner? (old)** | DEPRECATED |

### Companies DB <-> Network DB

| Companies DB Field | Network DB Field | Semantics |
|---|---|---|
| **Current People** | **Current Co** | People currently at this company |
| **Alums** | **Past Cos** | Former employees |
| **Angels** | **Angel Folio** | Angel investors in the company |
| **Piped From** | **Piped to DeVC** | Deal sourcing attribution |
| **YC Partner** | **YC Partner Portfolio** | YC partner relationships |
| **🌐 Network DB** | *(generic, no named reverse)* | Generic catch-all link |
| **Domain Eval?** | *(no named reverse)* | One-way from Companies to Network |
| **MPI Connect** | *(no named reverse)* | One-way from Companies to Network |
| **Met by?** | *(no named reverse)* | One-way from Companies to Network |
| **Shared with** | *(no named reverse)* | One-way from Companies to Network |

### Companies DB <-> Companies DB (Self-Relations)

| Field A | Field B | Semantics |
|---|---|---|
| **Investors (VCs, Micros)** | **Known Portfolio** | VC firm ↔ portfolio company mapping |

### Companies DB <-> Network DB (via Schools)

| Companies DB Field | Network DB Field | Semantics |
|---|---|---|
| *(auto-populated reverse)* | **Schools** | Educational institutions stored as Companies DB entities |

---

## Notion vs Postgres: Relation Column Sync Status

### Companies Table (Postgres)

| Notion Relation | Target DB | Postgres Column | Exists? | Type | Status |
|---|---|---|---|---|---|
| **Current People** → Network | Network DB | `current_people_ids` | PLANNED | TEXT[] | In migration SQL |
| **Angels** → Network | Network DB | `angel_ids` | PLANNED | TEXT[] | In migration SQL |
| **Alums** → Network | Network DB | `alum_ids` | PLANNED | TEXT[] | In migration SQL |
| **MPI Connect** → Network | Network DB | `mpi_connect_ids` | PLANNED | TEXT[] | In migration SQL |
| **Domain Eval?** → Network | Network DB | `domain_eval_ids` | PLANNED | TEXT[] | In migration SQL |
| **Piped From** → Network | Network DB | `piped_from_ids` | PLANNED | TEXT[] | In migration SQL |
| **Met by?** → Network | Network DB | `met_by_ids` | PLANNED | TEXT[] | In migration SQL |
| **Shared with** → Network | Network DB | `shared_with_ids` | PLANNED | TEXT[] | In migration SQL |
| **YC Partner** → Network | Network DB | `yc_partner_ids` | PLANNED | TEXT[] | In migration SQL |
| **🌐 Network DB** → Network | Network DB | `network_ids` | PLANNED | TEXT[] | In migration SQL |
| **Investors (VCs, Micros)** → Companies | Companies (self) | `investor_company_ids` | PLANNED | TEXT[] | In migration SQL |
| **Known Portfolio** → Companies | Companies (self) | `known_portfolio_ids` | PLANNED | TEXT[] | In migration SQL |
| **Portfolio Interaction Notes** → Portfolio | Portfolio DB | `portfolio_notion_ids` | PLANNED | TEXT[] | In migration SQL |
| **Meeting Notes** → Meeting Notes | Meeting Notes DB | `meeting_note_ids` | PLANNED | TEXT[] | In migration SQL |
| **Pending Tasks** → Tasks Tracker | Tasks Tracker DB | `pending_task_ids` | PLANNED | TEXT[] | In migration SQL |
| **Corp Dev** → Unknown DB | Unknown DB | `corp_dev_notion_ids` | PLANNED | TEXT[] | In migration SQL |
| **💰 Finance DB** → Finance | Finance DB | `finance_notion_ids` | PLANNED | TEXT[] | In migration SQL |

**Current state: 0 of 17 relation columns exist. All 17 are in the migration SQL.**

### Network Table (Postgres)

| Notion Relation | Target DB | Postgres Column | Exists? | Type | Status |
|---|---|---|---|---|---|
| **Current Co** → Companies | Companies DB | `current_company_ids` | **YES** | TEXT[] | Synced |
| **Past Cos** → Companies | Companies DB | `past_company_ids` | **YES** | TEXT[] | Synced |
| **Schools** → Companies | Companies DB | `school_ids` | PLANNED | TEXT[] | In migration SQL |
| **Angel Folio** → Companies | Companies DB | `angel_folio_ids` | PLANNED | TEXT[] | In migration SQL |
| **Piped to DeVC** → Companies | Companies DB | `piped_to_devc_ids` | PLANNED | TEXT[] | In migration SQL |
| **YC Partner Portfolio** → Companies | Companies DB | `yc_partner_portfolio_ids` | PLANNED | TEXT[] | In migration SQL |
| **Sourcing Attribution** → Portfolio | Portfolio DB | `sourcing_attribution_ids` | PLANNED | TEXT[] | In migration SQL |
| **Participation Attribution** → Portfolio | Portfolio DB | `participation_attribution_ids` | PLANNED | TEXT[] | In migration SQL |
| **Led by?** → Portfolio | Portfolio DB | `led_by_ids` | PLANNED | TEXT[] | In migration SQL |
| **Meeting Notes** → Meeting Notes | Meeting Notes DB | `meeting_note_ids` | PLANNED | TEXT[] | In migration SQL |
| **Tasks Pending** → Tasks Tracker | Tasks Tracker DB | `task_pending_ids` | PLANNED | TEXT[] | In migration SQL |
| **C+E Speaker** → Events | Events DB | `ce_speaker_ids` | PLANNED | TEXT[] | In migration SQL |
| **C+E Attendance** → Events | Events DB | `ce_attendance_ids` | PLANNED | TEXT[] | In migration SQL |
| **Venture Partner? (old)** → Portfolio | Portfolio DB | — | SKIP | — | DEPRECATED |
| **Network Tasks?** → Alt Tasks | Alt Tasks DB | — | SKIP | — | DEPRECATED |
| **Unstructured Leads** → Leads | Leads DB | — | SKIP | — | LEGACY |

**Current state: 2 of 16 relation columns exist (`current_company_ids`, `past_company_ids`). 11 are in the migration SQL. 3 are SKIP (deprecated/legacy).**

### Portfolio Table (Postgres)

| Notion Relation | Target DB | Postgres Column | Exists? | Type | Status |
|---|---|---|---|---|---|
| **Company Name** → Companies | Companies DB | — | **MISSING** | — | No portfolio table exists |
| **Led by?** → Network | Network DB | — | **MISSING** | — | No portfolio table exists |
| **Sourcing Attribution** → Network | Network DB | — | **MISSING** | — | No portfolio table exists |
| **Participation Attribution** → Network | Network DB | — | **MISSING** | — | No portfolio table exists |
| **Venture Partner? (old)** → Network | Network DB | — | SKIP | — | DEPRECATED |
| **Meeting Notes** → Meeting Notes | Meeting Notes DB | — | **MISSING** | — | No portfolio table exists |
| **Introduced to?** → Unknown | Unknown DB | — | **MISSING** | — | No portfolio table exists |

**Current state: The `portfolio` table does not exist in Postgres. None of the 7 relations are represented.**

---

## Gap Summary

### Gap 1: No `portfolio` table in Postgres

The Portfolio DB has 94 Notion fields including 7 relations and 9 rollups. It is the **financial tracking layer** for investments (entry cheques, reserves, follow-on decisions, ownership %, FMV, health status, fund priorities).

**Impact:** Portfolio DB is a hub for:
- Companies DB links (via "Company Name" — 1:1)
- Network DB links (via 3 attribution relations — who sourced, co-invested, led)
- Financial computations (rollups pull Sector, Angels, Founders, etc. from Companies DB)

Without a `portfolio` table, Postgres cannot:
- Run graph queries across Person → Portfolio → Company
- Track investment attribution (who sourced which deal)
- Compute portfolio-level analytics (reserve calculations, follow-on decisions)
- Join portfolio health data with company pipeline data

**Recommendation:** Create a `portfolio` table with at minimum:
```sql
-- DRAFT — DO NOT EXECUTE
CREATE TABLE IF NOT EXISTS portfolio (
    id SERIAL PRIMARY KEY,
    notion_page_id TEXT UNIQUE,
    portfolio_co TEXT NOT NULL,              -- title field
    company_notion_id TEXT,                  -- relation: Company Name (limit=1)
    health TEXT DEFAULT '',                  -- select: Green/Yellow/Red/NA
    today TEXT DEFAULT '',                   -- select: Fund Priority/Funnel/Deadpool/etc.
    aif_usa TEXT DEFAULT '',                 -- select: AIF/USA
    hc_priority TEXT DEFAULT '',             -- select: P0-P4
    current_stage TEXT DEFAULT '',           -- select: pre-product to scaling
    entry_cheque REAL,                       -- number
    ownership_pct REAL,                      -- number
    money_in REAL,                           -- formula (store computed)
    fmv_carried REAL,                        -- number
    earmarked_reserves REAL,                 -- number
    reserve_committed REAL,                  -- number
    reserve_deployed REAL,                   -- number
    -- Relation columns (Notion page IDs)
    led_by_ids TEXT[] DEFAULT '{}',          -- relation -> Network DB
    sourcing_attribution_ids TEXT[] DEFAULT '{}', -- relation -> Network DB
    participation_attribution_ids TEXT[] DEFAULT '{}', -- relation -> Network DB
    meeting_note_ids TEXT[] DEFAULT '{}',    -- relation -> Meeting Notes DB
    introduced_to_ids TEXT[] DEFAULT '{}',   -- relation -> Unknown DB
    -- Enrichment
    enrichment_metadata JSONB DEFAULT '{}',
    signal_history JSONB DEFAULT '[]',
    -- Infrastructure
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_synced_at TIMESTAMPTZ,
    notion_last_edited TIMESTAMPTZ
);
```

### Gap 2: No foreign key constraints between tables

**Current state:** Zero FK constraints exist between `companies` and `network` tables.

**Analysis:** FK constraints are NOT recommended for these tables because:
1. Relation columns store **Notion page IDs** (UUIDs), not Postgres PKs
2. Not all Notion pages may be synced to Postgres (partial sync)
3. Notion relations can reference pages that haven't been synced yet
4. The sync process would fail on INSERT if FK constraints required the referenced row to exist

**Recommendation:** Use **soft references** (TEXT[] columns storing Notion page IDs) with **application-level joins** via `notion_page_id`. Example:
```sql
-- Join companies with their current people (via Notion page IDs)
SELECT c.name, n.person_name
FROM companies c
CROSS JOIN LATERAL unnest(c.current_people_ids) AS pid
JOIN network n ON n.notion_page_id = pid;
```

### Gap 3: Relation columns in Companies table (0/17 exist)

All 17 relation columns are in the migration SQL at `sql/companies-network-migration.sql`. None have been executed.

### Gap 4: Relation columns in Network table (2/13 exist)

Only `current_company_ids` and `past_company_ids` exist. The remaining 11 are in the migration SQL.

---

## Cross-Reference Matrix

Shows how each DB connects to the other two, counting **active (non-deprecated) relations only**.

|  | → Portfolio DB | → Companies DB | → Network DB | → Other DBs |
|---|---|---|---|---|
| **Portfolio DB** | — | 1 (Company Name) | 3 (Led by, Sourcing, Participation) | 2 (Meeting Notes, Introduced to?) |
| **Companies DB** | 1 (Portfolio Interaction Notes) | 2 (self: Investors, Known Portfolio) | 9 (Current People, Angels, Alums, MPI, Domain Eval, Piped From, Met by, Shared with, YC Partner, Network DB) | 4 (Meeting Notes, Pending Tasks, Corp Dev, Finance) |
| **Network DB** | 3 (Sourcing Attr, Participation Attr, Led by) | 6 (Current Co, Past Cos, Schools, Angel Folio, Piped to DeVC, YC Partner Portfolio) | — | 4 (Meeting Notes, Tasks Pending, C+E Speaker, C+E Attendance) |

**Totals:**
- Portfolio DB: 6 outbound relations (1 to Companies, 3 to Network, 2 to other)
- Companies DB: 16 outbound relations (1 to Portfolio, 2 self, 9 to Network, 4 to other)
- Network DB: 13 outbound relations (3 to Portfolio, 6 to Companies, 4 to other)

**Companies DB is the most connected** — it is the central node in the relation graph, linking heavily to Network DB (9 relations) and serving as the bridge between Portfolio and Network.

---

## Recommended Migration Priority

### Phase 1: Execute existing migration SQL
The `sql/companies-network-migration.sql` already covers all Companies and Network relation gaps. Execute it to add the 28 planned columns.

### Phase 2: Create `portfolio` table
Design and create the `portfolio` table. This unlocks:
- Full three-way graph queries (Person → Portfolio → Company)
- Investment attribution tracking
- Portfolio health analytics in Postgres

### Phase 3: Index relation columns
After populating data, add GIN indexes on frequently queried relation arrays:
```sql
-- DRAFT — DO NOT EXECUTE
CREATE INDEX IF NOT EXISTS idx_companies_current_people ON companies USING GIN (current_people_ids);
CREATE INDEX IF NOT EXISTS idx_companies_investor_cos ON companies USING GIN (investor_company_ids);
CREATE INDEX IF NOT EXISTS idx_network_current_co ON network USING GIN (current_company_ids);
CREATE INDEX IF NOT EXISTS idx_network_sourcing_attr ON network USING GIN (sourcing_attribution_ids);
CREATE INDEX IF NOT EXISTS idx_portfolio_company ON portfolio (company_notion_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_led_by ON portfolio USING GIN (led_by_ids);
```

### Phase 4: Sync agent updates
Update the SyncAgent to populate relation columns during Notion → Postgres sync. Relation fields in Notion return arrays of page IDs, which map directly to TEXT[] columns.

---

## Notes

1. **DB `59c31a93-110d-4e80-a5ca-84c43f585ae2`** is inaccessible via the Notion API connection. It is referenced by Portfolio DB ("Introduced to?") and Companies DB ("Corp Dev"). Likely a private workspace DB (Corp Dev or Introductions tracker). Low priority for Postgres sync.

2. **Rollups are NOT synced to Postgres.** They are computed from relations in Notion. If needed in Postgres, they should be recomputed via SQL joins rather than synced directly. The 3 Companies DB rollups (AIF/USA, Money In, Ownership %) all pull from Portfolio DB — they will be computable once the `portfolio` table exists.

3. **The `limit=1` on Portfolio DB → Companies DB ("Company Name")** means each portfolio entry is linked to exactly one company. This is a many-to-one relationship (many portfolio entries per company). In Postgres, this should be a single TEXT column (`company_notion_id`), not an array.

4. **Generic "🌐 Network DB" relation on Companies DB** appears to be a catch-all link field. It may overlap with the more specific relations (Current People, Angels, etc.). Consider whether it needs a separate Postgres column or can be ignored.
