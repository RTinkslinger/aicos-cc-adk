# Companies DB + Network DB Schema Audit
*Date: 2026-03-20*
*Sources: Notion schema docs (Session 004, schemas/network-db.md, CONTEXT.md, DATA-ARCHITECTURE.md), Supabase SQL queries (llfkxnsfczludgigknbs)*

---

## VERIFIED AGAINST LIVE NOTION — 2026-03-20

**Verification method:** Queried live Notion schemas via `notion-fetch` on `collection://` data source URLs, queried live Postgres via `information_schema.columns`, and performed three-way cross-reference.

**Live schema counts:**
- Companies DB: **49 properties** (matches audit count)
- Network DB: **42 properties** (audit listed 44 — 2 system fields `url` and `createdTime` are NOT exposed in live schema)
- Companies Postgres: **32 columns** (matches audit)
- Network Postgres: **34 columns** (matches audit)

### Corrections from Live Verification

**Companies DB — 8 corrections:**

| # | Audit Claim | Live Reality | Impact |
|---|-------------|-------------|--------|
| 1 | Field "Corp Dev DB" (relation) | Actual Notion name is **"Corp Dev"**. Target DB: `59c31a93-110d-4e80-a5ca-84c43f585ae2` | Name correction only — column still needed |
| 2 | Field "Finance DB" (relation) | Actual Notion name is **"💰 Finance DB"**. Target DB: `9b59fd98-919d-4043-993d-eb7772659dd6` (different ID than assumed) | Name + target DB correction |
| 3 | Field "Network DB" (relation) | Actual Notion name is **"🌐 Network DB"** | Name correction only |
| 4 | Field "Portfolio DB" (relation) | Actual Notion name is **"Portfolio Interaction Notes"** (relation -> Portfolio DB `4dba9b7f`) | Name correction — different semantic meaning |
| 5 | Field "Tasks Tracker" listed as separate relation (#44) | **DOES NOT EXIST** in live Notion. Only "Pending Tasks" exists. | Remove from gap list — reduces actionable gaps by 1 |
| 6 | Field "Description/Notes" listed as field #49, HIGH priority | **DOES NOT EXIST** in live Notion (was inferred from CONTEXT.md "Description" field) | Remove from gap list — reduces actionable gaps by 1. Optional PG-only enrichment. |
| 7 | `last_round_timing` Postgres column noted as "no clear Notion match" | **"Last Round Timing"** (select, 11 options) EXISTS in live Notion and maps perfectly | Not a gap — already fully mapped |
| 8 | — (not in audit) | **"Meeting Notes"** (relation -> Meeting Notes DB `0dc61edf`) EXISTS in live Notion | Audit missed this field — adds 1 to actionable gaps |

**Net effect on Companies gaps:** Original 24 actionable → remove 2 (Tasks Tracker, Description/Notes) + add 1 (Meeting Notes) - 2 more corrections (Last Round Timing was already mapped, not a gap) = **21 actionable Notion-to-PG gaps** + 1 optional PG-only enrichment (description)

**Network DB — 3 corrections:**

| # | Audit Claim | Live Reality | Impact |
|---|-------------|-------------|--------|
| 1 | Listed "url" and "createdTime" as system fields (#41, #42) | NOT exposed in live Notion schema | Reduce total Notion field count from 44 to 42 |
| 2 | Fields Email, Phone, IDS Notes, Relationship Status, Last Interaction, Source listed as "may exist in Notion" | Confirmed **NOT in Notion** as of 2026-03-20 | Still valuable as PG-only enrichment columns |
| 3 | Batch, Company Stage, Sector Classification listed as "view-only" | Confirmed as **rollup** type in live schema (correctly skipped) | No change |

**Net effect on Network gaps:** Original 18 actionable → no change (the 6 fields confirmed not-in-Notion were already listed as needing PG columns) = **18 actionable gaps** (5 HIGH, 7 MEDIUM, 6 LOW). But 6 of these are now explicitly marked as PG-only enrichment rather than Notion sync targets.

### Revised Coverage Scorecard

| Metric | Companies DB | Network DB |
|--------|-------------|------------|
| Notion fields (live verified) | 49 | 42 |
| Postgres columns (live verified) | 32 | 34 |
| Notion fields mapped to Postgres | 20 (was 19 — Last Round Timing now counted) | 23 |
| Notion fields missing from PG (actionable) | **21** (Notion sync targets) | **12** (Notion-sourced only) |
| PG-only enrichment columns to add | 0 (description optional — see SQL) | **6** (email, phone, ids_notes, relationship_status, last_interaction, source) |
| Notion fields SKIP (formula/rollup/system/deprecated) | 8 | 7 (3 rollup + 1 system + 3 deprecated) |
| PG-only columns (existing enrichment + infra) | 13 | 11 |

### Final Migration SQL

Written to: `sql/companies-network-migration.sql`

- Companies: 21 new columns + 6 indexes (final: 53 columns)
- Network: 12 new Notion columns + 6 PG-only enrichment columns + 8 indexes (final: 52 columns)
- All idempotent (IF NOT EXISTS)
- No SQL executed — prepare only

---

## Companies DB

### Notion Schema (COMPLETE -- 49 fields)

Sourced from Session 004 deep-dive (full schema extraction from Notion) + CONTEXT.md + DATA-ARCHITECTURE.md.

| # | Property Name | Type | Options/Values | Notes |
|---|--------------|------|----------------|-------|
| 1 | **Name** | title | — | Company name (title field) |
| 2 | **Pipeline Status** | status | TO_DO: Screen, Mining, NA; IN_PROGRESS: Passive Screening, Active Screening, Evaluating, Parked, Tracking_7, Tracking_30, Tracking_90, Tracking_180, To Pass, To Win and Close; COMPLETE: Won & Closing, Portfolio, Pass, Surface, Top Up, Passed Last Track For Next, Pass Forever, Process Miss, Missed without screen, Struggling to Win, Lost, Anti Folio, Acquired/Shut Down/Defunct | Full deal funnel |
| 3 | **Deal Status** | status | Likely Fast, Slow, Forming, Muted (speed); Early, Late (timing); High, Med, Low (pull); DeVC Concept Prospect, DeVC Lean In Prospect, DeVC forming round, In Strike Zone, Closing + Option, Closing + Late, Portfolio | 3D matrix: Speed x Timing x Pull |
| 4 | **Deal Status @ Discovery** | status | (same values as Deal Status) | Snapshot at discovery time |
| 5 | **Sector** | select | SaaS, B2B, Consumer, Financial Services, Frontier, VC, Financial Services (alt) | High-level sector |
| 6 | **Sector Tags** | multi_select | ~150 granular tags | Ultra-specific sector classification |
| 7 | **Type** | select | SMB, Mid Market, Enterprise, VC, Micro VC, Startup | Company classification |
| 8 | **Priority** | select | P0, P1, P2 | Deal priority |
| 9 | **Venture Funding** | select | Pre-Seed, Seed, Series A, Series B, Series C, Growth, Listed, Bootstrapped, Raising, Angels | Funding stage |
| 10 | **Founding Timeline** | select | (timeline values) | When company was founded |
| 11 | **Smart Money?** | select | Tier 1, Tier 1.5, Smart Money | Cap table quality classification |
| 12 | **HIL Review?** | select | To Review, Reviewed | Human-in-the-Loop review tracking |
| 13 | **JTBD** | multi_select | 1PE Pending, 1PE Done, 2PE Pending, 2PE Done, MPE Pending, MPE Done, BRCs Pending, BRCs Done, DE Pending, DE Done | "Pair of Eyes" evaluation + BRC + Deal Execution |
| 14 | **Sells To** | multi_select | Consumers, Brands, Enterprise, SMB, etc. (19 values) | Customer type |
| 15 | **Batch** | multi_select | YC S23-W26, SPC India/USA, Localhost India, Lossfunk 1-6, EF India | Accelerator batch tracking |
| 16 | **Last Round $M** | number | — | Last round amount in millions |
| 17 | **Money Committed** | number | — | Money committed to deal |
| 18 | **Website** | url | — | Company website |
| 19 | **Vault Link** | url | — | Link to vault/data room |
| 20 | **Deck if link** | url | — | Pitch deck link |
| 21 | **Action Due?** | date | — | Next action due date |
| 22 | **Surface to collective** | date | — | When to surface deal to DeVC collective |
| 23 | **AIF/USA** | formula | — | Computed field |
| 24 | **Money In** | formula | — | Computed field |
| 25 | **Ownership %** | formula | — | Computed field |
| 26 | **AIF/USA (rollup)** | rollup | — | Rollup from Portfolio DB |
| 27 | **Money In (rollup)** | rollup | — | Rollup from Portfolio DB |
| 28 | **Ownership % (rollup)** | rollup | — | Rollup from Portfolio DB |
| 29 | **Current People** | relation -> Network DB | — | Who currently works at this company |
| 30 | **Angels** | relation -> Network DB | — | Angels who invested in this company |
| 31 | **Alums** | relation -> Network DB | — | Former employees now in the network |
| 32 | **MPI Connect** | relation -> Network DB | — | Z47/MPI connections to this company |
| 33 | **Domain Eval?** | relation -> Network DB | — | IC/expert who can evaluate the domain |
| 34 | **Piped From** | relation -> Network DB | — | Who sourced/piped this deal |
| 35 | **Met by?** | relation -> Network DB | — | Which GP/team member first met founder |
| 36 | **Shared with** | relation -> Network DB | — | Who the deal was shared with for evaluation |
| 37 | **YC Partner** | relation -> Network DB | — | YC partner for YC batch companies |
| 38 | **Network DB** | relation -> Network DB | — | Generic catch-all Network DB link |
| 39 | **Investors (VCs, Micros)** | relation -> Companies DB (self) | — | VC firms that invested in this company |
| 40 | **Known Portfolio** | relation -> Companies DB (self) | — | Portfolio companies (for VC firm records) |
| 41 | **Finance DB** | relation -> Finance DB | — | Link to financial data |
| 42 | **Corp Dev DB** | relation -> Corp Dev DB | — | Link to corporate development tracking |
| 43 | **Portfolio DB** | relation -> Portfolio DB | — | Link to portfolio tracking (hidden in some views) |
| 44 | **Tasks Tracker** | relation -> Tasks Tracker | — | Related tasks |
| 45 | **Pending Tasks** | relation -> Tasks Tracker | — | Open action items (may overlap with #44) |
| 46 | **DeVC IP POC** | person | — | DeVC investment professional point of contact |
| 47 | **Created by** | created_by | — | System field |
| 48 | **Last edited time** | last_edited_time | — | System field |
| 49 | **Description/Notes** | rich_text | — | Company description (inferred from CONTEXT.md "Description" field) |

> **Note on field #41-45:** The exact relation target DBs for Finance DB, Corp Dev DB, Portfolio DB, and Tasks Tracker relations were identified in Session 004 but some target DBs have not been fully explored. Fields #44 and #45 may be the same relation or two separate task-related relations.

---

### Current Postgres Schema (COMPLETE -- 32 columns)

From Supabase query on `llfkxnsfczludgigknbs`, table `companies`:

| # | Column Name | Data Type | Nullable | Default | Notes |
|---|------------|-----------|----------|---------|-------|
| 1 | id | integer | NO | nextval('companies_id_seq') | PK, auto-increment |
| 2 | notion_page_id | text | YES | — | Links to Notion page |
| 3 | name | text | NO | — | Company name |
| 4 | deal_status | text | YES | '' | Maps to Notion Deal Status |
| 5 | deal_status_at_discovery | text | YES | '' | Maps to Notion Deal Status @ Discovery |
| 6 | pipeline_status | text | YES | '' | Maps to Notion Pipeline Status |
| 7 | type | text | YES | '' | Maps to Notion Type |
| 8 | sector | text | YES | '' | Maps to Notion Sector |
| 9 | sector_tags | text[] | YES | '{}' | Maps to Notion Sector Tags (multi_select) |
| 10 | priority | text | YES | '' | Maps to Notion Priority |
| 11 | founding_timeline | text | YES | '' | Maps to Notion Founding Timeline |
| 12 | venture_funding | text | YES | '' | Maps to Notion Venture Funding |
| 13 | last_round_amount | real | YES | — | Maps to Notion Last Round $M |
| 14 | last_round_timing | text | YES | '' | Timing of last round (no clear Notion match) |
| 15 | smart_money | text | YES | '' | Maps to Notion Smart Money? |
| 16 | hil_review | text | YES | '' | Maps to Notion HIL Review? |
| 17 | jtbd | text[] | YES | '{}' | Maps to Notion JTBD (multi_select) |
| 18 | sells_to | text[] | YES | '{}' | Maps to Notion Sells To (multi_select) |
| 19 | batch | text[] | YES | '{}' | Maps to Notion Batch (multi_select) |
| 20 | website | text | YES | '' | Maps to Notion Website |
| 21 | deck_link | text | YES | '' | Maps to Notion Deck if link |
| 22 | vault_link | text | YES | '' | Maps to Notion Vault Link |
| 23 | agent_ids_notes | text | YES | '' | AI CoS enrichment: agent IDS notes |
| 24 | content_connections | jsonb | YES | '[]' | AI CoS enrichment: content pipeline connections |
| 25 | thesis_thread_links | jsonb | YES | '[]' | AI CoS enrichment: thesis thread links |
| 26 | signal_history | jsonb | YES | '[]' | AI CoS enrichment: signal history |
| 27 | computed_conviction_score | real | YES | — | AI CoS enrichment: computed conviction |
| 28 | enrichment_metadata | jsonb | YES | '{}' | AI CoS enrichment: general metadata |
| 29 | created_at | timestamptz | YES | now() | Record creation time |
| 30 | updated_at | timestamptz | YES | now() | Last update time |
| 31 | last_synced_at | timestamptz | YES | — | Last Notion sync time |
| 32 | notion_last_edited | timestamptz | YES | — | Notion last edited timestamp |

---

### Gap Analysis: Notion fields NOT in Postgres

| # | Notion Property | Notion Type | Suggested Postgres Column | Suggested PG Type | Priority | Notes |
|---|----------------|-------------|--------------------------|-------------------|----------|-------|
| 1 | **Money Committed** | number | `money_committed` | REAL | HIGH | Financial data needed for portfolio analysis |
| 2 | **Action Due?** | date | `action_due` | DATE | HIGH | Powers action scoring time_sensitivity factor |
| 3 | **Surface to collective** | date | `surface_to_collective` | DATE | MEDIUM | DeVC collective timing |
| 4 | **Current People** | relation -> Network | `current_people_ids` | TEXT[] (notion page IDs) | HIGH | Critical for BRC graph queries |
| 5 | **Angels** | relation -> Network | `angel_ids` | TEXT[] | MEDIUM | Co-investment analysis |
| 6 | **Alums** | relation -> Network | `alum_ids` | TEXT[] | LOW | Career pattern analysis |
| 7 | **MPI Connect** | relation -> Network | `mpi_connect_ids` | TEXT[] | MEDIUM | Z47 relationship mapping |
| 8 | **Domain Eval?** | relation -> Network | `domain_eval_ids` | TEXT[] | LOW | Evaluation assignment |
| 9 | **Piped From** | relation -> Network | `piped_from_ids` | TEXT[] | MEDIUM | Attribution tracking |
| 10 | **Met by?** | relation -> Network | `met_by_ids` | TEXT[] | MEDIUM | GP contact tracking |
| 11 | **Shared with** | relation -> Network | `shared_with_ids` | TEXT[] | LOW | Evaluation sharing |
| 12 | **YC Partner** | relation -> Network | `yc_partner_ids` | TEXT[] | LOW | YC relationship mapping |
| 13 | **Network DB** | relation -> Network | `network_ids` | TEXT[] | LOW | Generic catch-all |
| 14 | **Investors (VCs, Micros)** | relation -> Companies (self) | `investor_company_ids` | TEXT[] | HIGH | Market intelligence graph |
| 15 | **Known Portfolio** | relation -> Companies (self) | `known_portfolio_ids` | TEXT[] | HIGH | VC portfolio mapping |
| 16 | **Finance DB** | relation -> Finance DB | `finance_notion_ids` | TEXT[] | LOW | Cross-DB link |
| 17 | **Corp Dev DB** | relation -> Corp Dev DB | `corp_dev_notion_ids` | TEXT[] | LOW | Cross-DB link |
| 18 | **Portfolio DB** | relation -> Portfolio DB | `portfolio_notion_ids` | TEXT[] | MEDIUM | Portfolio link |
| 19 | **Tasks Tracker** | relation -> Tasks | `task_notion_ids` | TEXT[] | LOW | Task link |
| 20 | **Pending Tasks** | relation -> Tasks | `pending_task_ids` | TEXT[] | LOW | Open items link |
| 21 | **DeVC IP POC** | person | `devc_ip_poc` | TEXT | MEDIUM | POC assignment |
| 22 | **AIF/USA** | formula | — | — | SKIP | Computed from Portfolio DB rollups -- recompute in PG if needed |
| 23 | **Money In** | formula | — | — | SKIP | Computed from Portfolio DB rollups |
| 24 | **Ownership %** | formula | — | — | SKIP | Computed from Portfolio DB rollups |
| 25 | **AIF/USA (rollup)** | rollup | — | — | SKIP | Rollup from Portfolio DB |
| 26 | **Money In (rollup)** | rollup | — | — | SKIP | Rollup from Portfolio DB |
| 27 | **Ownership % (rollup)** | rollup | — | — | SKIP | Rollup from Portfolio DB |
| 28 | **Created by** | created_by | — | — | SKIP | System field, not useful in PG |
| 29 | **Last edited time** | last_edited_time | — | — | SKIP | Captured via notion_last_edited |
| 30 | **Description/Notes** | rich_text | `description` | TEXT | HIGH | Company description needed for agent reasoning |

**Summary:** 30 Notion fields missing from Postgres. Of these: 6 are SKIP (formulas/rollups/system), leaving **24 actionable gaps**. 6 are HIGH priority, 7 are MEDIUM, 11 are LOW.

---

### Gap Analysis: Postgres columns NOT in Notion (AI CoS enrichment)

| # | Postgres Column | Type | Purpose | Keep? |
|---|----------------|------|---------|-------|
| 1 | id | integer | PG primary key | YES -- internal PG identity |
| 2 | notion_page_id | text | Notion page link | YES -- sync key |
| 3 | last_round_timing | text | Timing context for last round | YES -- may be derived from Notion Deal Status or enriched externally |
| 4 | agent_ids_notes | text | Agent-generated IDS notes | YES -- agent enrichment (not in Notion) |
| 5 | content_connections | jsonb | Content pipeline connections | YES -- agent enrichment |
| 6 | thesis_thread_links | jsonb | Thesis thread links | YES -- agent enrichment |
| 7 | signal_history | jsonb | Signal history over time | YES -- agent enrichment (IDS trail) |
| 8 | computed_conviction_score | real | Computed conviction score | YES -- agent enrichment |
| 9 | enrichment_metadata | jsonb | General enrichment metadata | YES -- agent enrichment |
| 10 | created_at | timestamptz | PG record creation | YES -- internal tracking |
| 11 | updated_at | timestamptz | PG last update | YES -- internal tracking |
| 12 | last_synced_at | timestamptz | Last Notion sync | YES -- sync tracking |
| 13 | notion_last_edited | timestamptz | Notion last edit time | YES -- change detection |

**All 13 Postgres-only columns are valid and should be kept.** They serve either sync infrastructure (4 columns) or agent enrichment (6 columns) roles, which are by design Postgres-only per the 3-actor sovereignty model.

---

## Network DB

### Notion Schema (COMPLETE -- 44 fields)

Sourced from `docs/notion/schemas/network-db.md` (definitive reference, Session 040 interview). 41 base schema columns + 3 view-only columns.

| # | Property Name | Type | Options/Values | Notes |
|---|--------------|------|----------------|-------|
| | **A. Identity & Basic Info** | | | |
| 1 | **Name** | title | — | Person's name |
| 2 | **Linkedin** | url | — | Primary unique identifier / dedup key |
| 3 | **Current Role** | select | ~40 values: Founder CEO, CTO, VC Partner, Angel Investor, etc. | LinkedIn job title equivalent |
| 4 | **Current Co** | relation -> Companies DB | multi-value | Current company/companies |
| 5 | **Past Cos** | relation -> Companies DB | multi-value | Notable past companies |
| 6 | **Home Base** | multi_select | Bangalore, NCR, Mumbai, Bay Area, East Coast, Singapore, Chennai, Pune, etc. | Prominent operating locations |
| 7 | **Local Network** | multi_select | India, US, NA | Firm-level geographic team classification |
| 8 | **Schools** | relation -> Companies DB | multi-value | Educational institutions (stored as Companies DB entities) |
| | **B. Investor Profile & Activity** | | | |
| 9 | **Investorship** | multi_select | Syndicate, VC, Occasional, Super Angel, Freq Angel, Na | Investing style/frequency |
| 10 | **Investing Activity** | select | High, Med, Low, Na | Recent investing frequency |
| 11 | **Angel Folio** | relation -> Companies DB | multi-value | Companies angel-invested in (sparse) |
| 12 | **In Folio Of** | multi_select | MPI, Cash, NA, DeVC Core, DeVC, DeVC Ext | Who has backed this person as a founder |
| 13 | **Folio Franchise** | multi_select | India Consumer, B2B Comm, SaaS, AI, Commerce, Health, Fintech, Climate, Defense, Aerospace, etc. | Sectors known for investing in |
| 14 | **Prev Foundership** | multi_select | Active Founder 5M+, Past Founder 5M+, Past 0 to 1, Exited Founder, Active Early Stage, NA | Founder history classification |
| 15 | **Operating Franchise** | multi_select | Consumer, Commerce, SaaS, DeepTech, Health, Fintech, Creator, B2B Comm, Consumer Tech, etc. | Sectors they know how to build/operate in |
| | **C. Relationship & Engagement** | | | |
| 16 | **R/Y/G** | select | Red, Yellow, Green, Unclear | Relationship health (firm-level) |
| 17 | **E/E Priority** | select | P0, P1, P2, P3 | Engagement & Escalation priority |
| 18 | **DeVC Relationship** | multi_select | DeVC Core, Core Target, DeVC Ext, Ext Target, DeVC Community, Comm Target, DeVC LP, LP Target, NA, Tier 1 VC, Micro VC, MPI IP, Founder, Met | Position in DeVC ecosystem funnel |
| 19 | **DeVC POC** | person | Notion user references | Point of contact on DeVC team |
| 20 | **Engagement Playbook** | multi_select | Programmatic Dealflow, Solo Capitalist | How to engage this person |
| 21 | **Collective Flag** | multi_select | Solo GP, Micro VC GP, Founder Angel, Operator Angel, LP cheque candidate | Archetype within DeVC Collective |
| | **D. Value & Attribution** | | | |
| 22 | **Leverage** | multi_select | Evaluation, Coverage, Underwriting | Value they bring to deal process |
| 23 | **Sourcing Attribution** | relation -> Portfolio DB | multi-value | Portfolio companies they sourced |
| 24 | **Participation Attribution** | relation -> Portfolio DB | multi-value | Portfolio deals they co-invested in |
| 25 | **Led by?** | relation -> Portfolio DB | multi-value | Portfolio companies they led investment in |
| 26 | **Sourcing/Flow/HOTS** | select | High, Med, Low, Na | Quality of information access |
| 27 | **Customer For** | multi_select | Ad-tech, Mar-tech, Commerce Enablement, AI Infra, Lo/No Code, Dev Tools, Data Stack, Productivity, B2B Comm, Biz Apps, NA | SaaS categories they could be a buyer for |
| 28 | **Piped to DeVC** | relation -> Companies DB | multi-value | Companies referred into DeVC pipeline |
| | **E. Events & Touchpoints** | | | |
| 29 | **Big Events Invite** | checkbox-style | Yes / empty | Shortlist for big events |
| 30 | **C+E Speaker** | relation -> Events DB | multi-value | Events spoken at |
| 31 | **C+E Attendance** | relation -> Events DB | multi-value | Events attended |
| 32 | **Meeting Notes** | relation -> Meeting Notes DB | multi-value | Meeting notes entries |
| 33 | **Tasks Pending** | relation -> Tasks Tracker | multi-value | Open action items with this person |
| 34 | **Network Tasks?** | relation -> separate tracker | multi-value | **DEPRECATED** -- use Tasks Pending |
| 35 | **Unstructured Leads** | relation -> separate DB | multi-value | **LEGACY** -- placeholder workaround |
| | **F. Sector & Market** | | | |
| 36 | **SaaS Buyer Type** | multi_select | SMB, Mid Market, Enterprise, NA | Market segment classification |
| 37 | **YC Partner Portfolio** | relation -> Companies DB | multi-value | YC partner relationship (for YC alumni) |
| 38 | **Sector Classification** | select/formula | Sector labels | **VIEW-ONLY** (not in base schema) |
| 39 | **Company Stage** | select/formula | Stage labels | **VIEW-ONLY** (not in base schema) |
| 40 | **Batch** | text/formula | e.g. "YCS25", "SPC US" | **VIEW-ONLY** (not in base schema) |
| | **G. System & Deprecated** | | | |
| 41 | **url** | system | Notion page URL | System-generated |
| 42 | **createdTime** | system | Creation timestamp | System-generated |
| 43 | **Last edited time** | system | Last modification | System-generated |
| 44 | **Venture Partner? (old)** | relation -> Portfolio DB | multi-value | **DEPRECATED** |

---

### Current Postgres Schema (COMPLETE -- 34 columns)

From Supabase query on `llfkxnsfczludgigknbs`, table `network`:

| # | Column Name | Data Type | Nullable | Default | Notes |
|---|------------|-----------|----------|---------|-------|
| 1 | id | integer | NO | nextval('network_id_seq') | PK, auto-increment |
| 2 | notion_page_id | text | YES | — | Links to Notion page |
| 3 | person_name | text | NO | — | Maps to Notion Name |
| 4 | role_title | text | YES | — | Maps to Notion Current Role |
| 5 | home_base | text[] | YES | '{}' | Maps to Notion Home Base (multi_select) |
| 6 | linkedin | text | YES | — | Maps to Notion Linkedin |
| 7 | ryg | text | YES | — | Maps to Notion R/Y/G |
| 8 | e_e_priority | text | YES | — | Maps to Notion E/E Priority |
| 9 | sourcing_flow_hots | text | YES | — | Maps to Notion Sourcing/Flow/HOTS |
| 10 | investing_activity | text | YES | — | Maps to Notion Investing Activity |
| 11 | devc_relationship | text[] | YES | '{}' | Maps to Notion DeVC Relationship (multi_select) |
| 12 | collective_flag | text[] | YES | '{}' | Maps to Notion Collective Flag (multi_select) |
| 13 | engagement_playbook | text[] | YES | '{}' | Maps to Notion Engagement Playbook (multi_select) |
| 14 | leverage | text[] | YES | '{}' | Maps to Notion Leverage (multi_select) |
| 15 | customer_for | text[] | YES | '{}' | Maps to Notion Customer For (multi_select) |
| 16 | investorship | text[] | YES | '{}' | Maps to Notion Investorship (multi_select) |
| 17 | prev_foundership | text[] | YES | '{}' | Maps to Notion Prev Foundership (multi_select) |
| 18 | folio_franchise | text[] | YES | '{}' | Maps to Notion Folio Franchise (multi_select) |
| 19 | operating_franchise | text[] | YES | '{}' | Maps to Notion Operating Franchise (multi_select) |
| 20 | big_events_invite | text[] | YES | '{}' | Maps to Notion Big Events Invite (checkbox-style) |
| 21 | in_folio_of | text[] | YES | '{}' | Maps to Notion In Folio Of (multi_select) |
| 22 | local_network_tags | text[] | YES | '{}' | Maps to Notion Local Network (multi_select) |
| 23 | saas_buyer_type | text[] | YES | '{}' | Maps to Notion SaaS Buyer Type (multi_select) |
| 24 | current_company_ids | text[] | YES | '{}' | Maps to Notion Current Co (relation -> Companies) |
| 25 | past_company_ids | text[] | YES | '{}' | Maps to Notion Past Cos (relation -> Companies) |
| 26 | agent_interaction_summaries | jsonb | YES | '[]' | AI CoS enrichment: interaction summaries |
| 27 | meeting_context | jsonb | YES | '[]' | AI CoS enrichment: meeting context |
| 28 | content_connections | jsonb | YES | '[]' | AI CoS enrichment: content pipeline connections |
| 29 | signal_history | jsonb | YES | '[]' | AI CoS enrichment: signal history |
| 30 | enrichment_metadata | jsonb | YES | '{}' | AI CoS enrichment: general metadata |
| 31 | created_at | timestamptz | YES | now() | Record creation time |
| 32 | updated_at | timestamptz | YES | now() | Last update time |
| 33 | last_synced_at | timestamptz | YES | — | Last Notion sync time |
| 34 | notion_last_edited | timestamptz | YES | — | Notion last edit timestamp |

---

### Gap Analysis: Notion fields NOT in Postgres

| # | Notion Property | Notion Type | Suggested Postgres Column | Suggested PG Type | Priority | Notes |
|---|----------------|-------------|--------------------------|-------------------|----------|-------|
| 1 | **Schools** | relation -> Companies DB | `school_ids` | TEXT[] | MEDIUM | Alumni network analysis |
| 2 | **Angel Folio** | relation -> Companies DB | `angel_folio_ids` | TEXT[] | MEDIUM | Co-investment analysis |
| 3 | **Sourcing Attribution** | relation -> Portfolio DB | `sourcing_attribution_ids` | TEXT[] | HIGH | Attribution tracking |
| 4 | **Participation Attribution** | relation -> Portfolio DB | `participation_attribution_ids` | TEXT[] | HIGH | Co-investment tracking |
| 5 | **Led by?** | relation -> Portfolio DB | `led_by_ids` | TEXT[] | HIGH | Lead investor relationships |
| 6 | **Piped to DeVC** | relation -> Companies DB | `piped_to_devc_ids` | TEXT[] | MEDIUM | Pipeline attribution |
| 7 | **YC Partner Portfolio** | relation -> Companies DB | `yc_partner_portfolio_ids` | TEXT[] | LOW | YC mapping |
| 8 | **C+E Speaker** | relation -> Events DB | `ce_speaker_ids` | TEXT[] | LOW | Event participation |
| 9 | **C+E Attendance** | relation -> Events DB | `ce_attendance_ids` | TEXT[] | LOW | Event participation |
| 10 | **Meeting Notes** | relation -> Meeting Notes DB | `meeting_note_ids` | TEXT[] | MEDIUM | Meeting history lookup |
| 11 | **Tasks Pending** | relation -> Tasks Tracker | `task_pending_ids` | TEXT[] | MEDIUM | Open action items |
| 12 | **DeVC POC** | person | `devc_poc` | TEXT | MEDIUM | Point of contact |
| 13 | **Email** | — | `email` | TEXT | HIGH | Noted as MISSING in schema doc -- important for enrichment |
| 14 | **Phone** | — | `phone` | TEXT | MEDIUM | Noted as MISSING in schema doc -- important for outreach |
| 15 | **IDS Notes** | rich_text | `ids_notes` | TEXT | HIGH | IDS notation per person -- critical for agent reasoning |
| 16 | **Relationship Status** | select | `relationship_status` | TEXT | MEDIUM | Mentioned in CONTEXT.md as key field |
| 17 | **Last Interaction** | date | `last_interaction` | DATE | HIGH | Powers staleness detection and action scoring |
| 18 | **Source** | select | `source` | TEXT | LOW | How this person entered the network |
| 19 | **Network Tasks?** | relation | — | — | SKIP | Deprecated |
| 20 | **Unstructured Leads** | relation | — | — | SKIP | Legacy |
| 21 | **Venture Partner? (old)** | relation | — | — | SKIP | Deprecated |
| 22 | **Sector Classification** | view-only | — | — | SKIP | View-only (formula/linked) |
| 23 | **Company Stage** | view-only | — | — | SKIP | View-only (formula/linked) |
| 24 | **Batch** | view-only | — | — | SKIP | View-only (formula/linked) |
| 25 | **url** | system | — | — | SKIP | Captured via notion_page_id |
| 26 | **createdTime** | system | — | — | SKIP | System field |
| 27 | **Last edited time** | system | — | — | SKIP | Captured via notion_last_edited |

**Summary:** 27 Notion fields missing from Postgres. Of these: 9 are SKIP (deprecated/view-only/system), leaving **18 actionable gaps**. 5 are HIGH priority, 7 are MEDIUM, 6 are LOW.

**Important:** Fields #13 (Email), #14 (Phone), #15 (IDS Notes), #16 (Relationship Status), #17 (Last Interaction), and #18 (Source) are listed in CONTEXT.md as "Key fields" for Network DB but were noted as gaps in the Network DB schema doc. They may exist in Notion but are underpopulated, or they may need to be created. Verify against live Notion schema.

---

### Gap Analysis: Postgres columns NOT in Notion (AI CoS enrichment)

| # | Postgres Column | Type | Purpose | Keep? |
|---|----------------|------|---------|-------|
| 1 | id | integer | PG primary key | YES -- internal PG identity |
| 2 | notion_page_id | text | Notion page link | YES -- sync key |
| 3 | agent_interaction_summaries | jsonb | Agent-generated interaction summaries | YES -- agent enrichment |
| 4 | meeting_context | jsonb | Meeting context for pre-meeting briefs | YES -- agent enrichment |
| 5 | content_connections | jsonb | Content pipeline connections | YES -- agent enrichment |
| 6 | signal_history | jsonb | Signal history over time | YES -- agent enrichment (IDS trail) |
| 7 | enrichment_metadata | jsonb | General enrichment metadata | YES -- agent enrichment |
| 8 | created_at | timestamptz | PG record creation | YES -- internal tracking |
| 9 | updated_at | timestamptz | PG last update | YES -- internal tracking |
| 10 | last_synced_at | timestamptz | Last Notion sync | YES -- sync tracking |
| 11 | notion_last_edited | timestamptz | Notion last edit time | YES -- change detection |

**All 11 Postgres-only columns are valid and should be kept.** They serve sync infrastructure (4 columns) or agent enrichment (5 columns) roles.

---

## Cross-DB Summary

### Coverage Scorecard

| Metric | Companies DB | Network DB |
|--------|-------------|------------|
| Notion fields (total) | 49 | 44 |
| Postgres columns (total) | 32 | 34 |
| Notion fields mapped to Postgres | 19 | 25 |
| Notion fields missing from PG (actionable) | 24 | 18 |
| -- HIGH priority gaps | 6 | 5 |
| -- MEDIUM priority gaps | 7 | 7 |
| -- LOW priority gaps | 11 | 6 |
| Notion fields SKIP (formula/rollup/system/deprecated) | 6 | 9 |
| PG-only columns (enrichment + infra) | 13 | 11 |

### Biggest Gaps by Impact

**Companies DB -- most impactful missing fields:**
1. `description` (rich_text) -- agents need company description for reasoning
2. `money_committed` (number) -- financial analysis
3. `action_due` (date) -- action scoring time_sensitivity
4. `current_people_ids` (relation) -- BRC graph queries, people-company graph
5. `investor_company_ids` / `known_portfolio_ids` (self-relations) -- market intelligence graph

**Network DB -- most impactful missing fields:**
1. `last_interaction` (date) -- staleness detection, relationship_temp scoring factor
2. `ids_notes` (text) -- IDS notation per person, critical for agent reasoning
3. `sourcing_attribution_ids` / `participation_attribution_ids` / `led_by_ids` -- attribution analysis
4. `email` / `phone` -- contact info for outreach (noted as missing even in Notion)

---

## Migration SQL (DRAFT)

### Companies DB -- HIGH priority columns

```sql
-- HIGH priority: Financial & operational fields
ALTER TABLE companies ADD COLUMN IF NOT EXISTS money_committed REAL;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS action_due DATE;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS surface_to_collective DATE;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '';

-- HIGH priority: Relation fields (stored as Notion page ID arrays)
ALTER TABLE companies ADD COLUMN IF NOT EXISTS current_people_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS investor_company_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS known_portfolio_ids TEXT[] DEFAULT '{}';

-- MEDIUM priority: Relation fields
ALTER TABLE companies ADD COLUMN IF NOT EXISTS angel_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS mpi_connect_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS piped_from_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS met_by_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS portfolio_notion_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS devc_ip_poc TEXT DEFAULT '';

-- LOW priority: Remaining relation fields
ALTER TABLE companies ADD COLUMN IF NOT EXISTS alum_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS domain_eval_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS shared_with_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS yc_partner_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS network_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS finance_notion_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS corp_dev_notion_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS task_notion_ids TEXT[] DEFAULT '{}';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS pending_task_ids TEXT[] DEFAULT '{}';
```

### Network DB -- HIGH priority columns

```sql
-- HIGH priority: Core fields for agent reasoning
ALTER TABLE network ADD COLUMN IF NOT EXISTS ids_notes TEXT DEFAULT '';
ALTER TABLE network ADD COLUMN IF NOT EXISTS last_interaction DATE;
ALTER TABLE network ADD COLUMN IF NOT EXISTS email TEXT DEFAULT '';
ALTER TABLE network ADD COLUMN IF NOT EXISTS phone TEXT DEFAULT '';

-- HIGH priority: Attribution relation fields
ALTER TABLE network ADD COLUMN IF NOT EXISTS sourcing_attribution_ids TEXT[] DEFAULT '{}';
ALTER TABLE network ADD COLUMN IF NOT EXISTS participation_attribution_ids TEXT[] DEFAULT '{}';
ALTER TABLE network ADD COLUMN IF NOT EXISTS led_by_ids TEXT[] DEFAULT '{}';

-- MEDIUM priority: Relation & classification fields
ALTER TABLE network ADD COLUMN IF NOT EXISTS school_ids TEXT[] DEFAULT '{}';
ALTER TABLE network ADD COLUMN IF NOT EXISTS angel_folio_ids TEXT[] DEFAULT '{}';
ALTER TABLE network ADD COLUMN IF NOT EXISTS piped_to_devc_ids TEXT[] DEFAULT '{}';
ALTER TABLE network ADD COLUMN IF NOT EXISTS meeting_note_ids TEXT[] DEFAULT '{}';
ALTER TABLE network ADD COLUMN IF NOT EXISTS task_pending_ids TEXT[] DEFAULT '{}';
ALTER TABLE network ADD COLUMN IF NOT EXISTS devc_poc TEXT DEFAULT '';
ALTER TABLE network ADD COLUMN IF NOT EXISTS relationship_status TEXT DEFAULT '';
ALTER TABLE network ADD COLUMN IF NOT EXISTS source TEXT DEFAULT '';

-- LOW priority: Event & other relation fields
ALTER TABLE network ADD COLUMN IF NOT EXISTS ce_speaker_ids TEXT[] DEFAULT '{}';
ALTER TABLE network ADD COLUMN IF NOT EXISTS ce_attendance_ids TEXT[] DEFAULT '{}';
ALTER TABLE network ADD COLUMN IF NOT EXISTS yc_partner_portfolio_ids TEXT[] DEFAULT '{}';
```

### Indexes for new columns

```sql
-- Companies: index for common lookups
CREATE INDEX IF NOT EXISTS idx_companies_action_due ON companies(action_due) WHERE action_due IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_companies_pipeline_status ON companies(pipeline_status);

-- Network: index for common lookups
CREATE INDEX IF NOT EXISTS idx_network_last_interaction ON network(last_interaction) WHERE last_interaction IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_network_ryg ON network(ryg);
CREATE INDEX IF NOT EXISTS idx_network_e_e_priority ON network(e_e_priority);
CREATE INDEX IF NOT EXISTS idx_network_linkedin ON network(linkedin) WHERE linkedin IS NOT NULL;
```

---

## Appendix: Field Name Mapping Reference

### Companies DB: Notion -> Postgres column name mapping

| Notion Property | Postgres Column | Status |
|----------------|----------------|--------|
| Name | name | MAPPED |
| Pipeline Status | pipeline_status | MAPPED |
| Deal Status | deal_status | MAPPED |
| Deal Status @ Discovery | deal_status_at_discovery | MAPPED |
| Sector | sector | MAPPED |
| Sector Tags | sector_tags | MAPPED |
| Type | type | MAPPED |
| Priority | priority | MAPPED |
| Venture Funding | venture_funding | MAPPED |
| Founding Timeline | founding_timeline | MAPPED |
| Smart Money? | smart_money | MAPPED |
| HIL Review? | hil_review | MAPPED |
| JTBD | jtbd | MAPPED |
| Sells To | sells_to | MAPPED |
| Batch | batch | MAPPED |
| Last Round $M | last_round_amount | MAPPED |
| Website | website | MAPPED |
| Deck if link | deck_link | MAPPED |
| Vault Link | vault_link | MAPPED |
| Money Committed | — | MISSING |
| Action Due? | — | MISSING |
| Surface to collective | — | MISSING |
| Description/Notes | — | MISSING |
| Current People | — | MISSING |
| Angels | — | MISSING |
| Alums | — | MISSING |
| MPI Connect | — | MISSING |
| Domain Eval? | — | MISSING |
| Piped From | — | MISSING |
| Met by? | — | MISSING |
| Shared with | — | MISSING |
| YC Partner | — | MISSING |
| Network DB | — | MISSING |
| Investors (VCs, Micros) | — | MISSING |
| Known Portfolio | — | MISSING |
| Finance DB | — | MISSING |
| Corp Dev DB | — | MISSING |
| Portfolio DB | — | MISSING |
| Tasks Tracker | — | MISSING |
| Pending Tasks | — | MISSING |
| DeVC IP POC | — | MISSING |

### Network DB: Notion -> Postgres column name mapping

| Notion Property | Postgres Column | Status |
|----------------|----------------|--------|
| Name | person_name | MAPPED |
| Linkedin | linkedin | MAPPED |
| Current Role | role_title | MAPPED |
| Current Co | current_company_ids | MAPPED |
| Past Cos | past_company_ids | MAPPED |
| Home Base | home_base | MAPPED |
| Local Network | local_network_tags | MAPPED |
| Investorship | investorship | MAPPED |
| Investing Activity | investing_activity | MAPPED |
| In Folio Of | in_folio_of | MAPPED |
| Folio Franchise | folio_franchise | MAPPED |
| Prev Foundership | prev_foundership | MAPPED |
| Operating Franchise | operating_franchise | MAPPED |
| R/Y/G | ryg | MAPPED |
| E/E Priority | e_e_priority | MAPPED |
| DeVC Relationship | devc_relationship | MAPPED |
| Engagement Playbook | engagement_playbook | MAPPED |
| Collective Flag | collective_flag | MAPPED |
| Leverage | leverage | MAPPED |
| Sourcing/Flow/HOTS | sourcing_flow_hots | MAPPED |
| Customer For | customer_for | MAPPED |
| Big Events Invite | big_events_invite | MAPPED |
| SaaS Buyer Type | saas_buyer_type | MAPPED |
| Schools | — | MISSING |
| Angel Folio | — | MISSING |
| Sourcing Attribution | — | MISSING |
| Participation Attribution | — | MISSING |
| Led by? | — | MISSING |
| Piped to DeVC | — | MISSING |
| YC Partner Portfolio | — | MISSING |
| C+E Speaker | — | MISSING |
| C+E Attendance | — | MISSING |
| Meeting Notes | — | MISSING |
| Tasks Pending | — | MISSING |
| DeVC POC | — | MISSING |
| Email | — | MISSING (also missing in Notion per schema doc) |
| Phone | — | MISSING (also missing in Notion per schema doc) |
| IDS Notes | — | MISSING |
| Relationship Status | — | MISSING |
| Last Interaction | — | MISSING |
| Source | — | MISSING |
