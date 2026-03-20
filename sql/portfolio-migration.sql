-- =============================================================================
-- Portfolio DB: CREATE TABLE + Schema Migration
-- =============================================================================
-- Generated: 2026-03-20
-- Source: Three-way cross-reference of LIVE Notion schema (94 fields),
--         LIVE Postgres (table does not exist yet), and view query (100 rows).
--
-- Rule: Final PG schema = MAX(current Postgres + full Notion). No drops.
-- Strategy: Idempotent (CREATE TABLE IF NOT EXISTS, ADD COLUMN IF NOT EXISTS).
-- Action: DO NOT EXECUTE without review. This is PREPARE ONLY.
--
-- Notion Portfolio DB ID: 4dba9b7f-e623-41a5-9cb7-2af5976280ee
-- Notion Database URL: https://www.notion.so/edbc9d0cfa16436da3d5f317a86a4d1e
-- Row count at audit time: 100 portfolio companies
-- =============================================================================


-- =============================================================================
-- FIELD MAPPING DECISIONS
-- =============================================================================
--
-- INCLUDED (69 columns from Notion + 8 PG-only = 77 total + id = 78):
--   1 title, 5 text, 28 select, 6 multi_select, 23 number, 2 date,
--   7 relation, 2 person, 1 last_edited_time
--   + 8 PG-only columns (sync infra + enrichment)
--
-- SKIPPED — Formulas (9): Computed in Notion, can recompute in PG if needed.
--   Bottoms-Up Reserve, Est. Capital In, FMV Last Round, Last round raise,
--   Money In, P&L, Top-Down Reserve, Top-Down Reserve OLD, Total raise to date
--
-- SKIPPED — Rollups (9): Derived from relations, resolved via JOINs in PG.
--   Angels, Co-Investors, Founders, Founding timeline, Funding to date,
--   Pending Tasks, Sector, Sector Tags, Vault link
--
-- SKIPPED — System (2): Metadata only.
--   Last edited by (last_edited_by — Notion internal user tracking)
--   (Note: Last updated / last_edited_time IS included as notion_last_edited)
--
-- ADDED — PG-only enrichment (8):
--   id (serial PK), notion_page_id, research_file_path,
--   enrichment_metadata (JSONB), signal_history (JSONB),
--   created_at, updated_at, last_synced_at
-- =============================================================================


-- =============================================================================
-- PART 1: CREATE TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS portfolio (

    -- -------------------------------------------------------------------------
    -- PG Infrastructure Columns
    -- -------------------------------------------------------------------------
    id                          SERIAL PRIMARY KEY,
    notion_page_id              TEXT UNIQUE,           -- Notion page UUID for sync

    -- -------------------------------------------------------------------------
    -- Title Field
    -- -------------------------------------------------------------------------
    -- Notion: Portfolio Co (title)
    portfolio_co                TEXT NOT NULL,

    -- -------------------------------------------------------------------------
    -- Relation Fields (stored as Notion page ID arrays)
    -- -------------------------------------------------------------------------
    -- Notion: Company Name (relation -> Companies DB 1edda9cc, limit=1)
    company_name_id             TEXT,                  -- Single relation, stored as page ID
    -- Notion: Led by? (relation -> Network DB 6462102f)
    led_by_ids                  TEXT[] DEFAULT '{}',
    -- Notion: Sourcing Attribution (relation -> Network DB 6462102f)
    sourcing_attribution_ids    TEXT[] DEFAULT '{}',
    -- Notion: Participation Attribution (relation -> Network DB 6462102f)
    participation_attribution_ids TEXT[] DEFAULT '{}',
    -- Notion: Venture Partner? (old) (relation -> Network DB 6462102f)
    venture_partner_old_ids     TEXT[] DEFAULT '{}',
    -- Notion: Meeting Notes (relation -> Meeting Notes DB 0dc61edf)
    meeting_notes_ids           TEXT[] DEFAULT '{}',
    -- Notion: Introduced to? (relation -> unknown DB 59c31a93)
    introduced_to_ids           TEXT[] DEFAULT '{}',

    -- -------------------------------------------------------------------------
    -- Person Fields (stored as Notion user ID arrays)
    -- -------------------------------------------------------------------------
    -- Notion: IP Assigned (person)
    ip_assigned                 TEXT[] DEFAULT '{}',
    -- Notion: MD Assigned (person)
    md_assigned                 TEXT[] DEFAULT '{}',

    -- -------------------------------------------------------------------------
    -- Select Fields (single-value enums stored as TEXT)
    -- -------------------------------------------------------------------------
    -- Notion: $500K candidate? (select: Yes, Maybe, No)
    five_hundred_k_candidate    TEXT DEFAULT '',
    -- Notion: AIF/USA (select: AIF, USA)
    aif_usa                     TEXT DEFAULT '',
    -- Notion: BU Follow-On Tag (select: Yes, PR, 0%, 2%, 5%)
    bu_follow_on_tag            TEXT DEFAULT '',
    -- Notion: Check-In Cadence (select: Monthly, Quarterly, Alternate Month, Bi-Annual, Ad-Hoc, NA)
    check_in_cadence            TEXT DEFAULT '',
    -- Notion: Current Stage (select: pre-product, early product, post product, early revenue, scaling revenue, Exited/Shutdown)
    current_stage               TEXT DEFAULT '',
    -- Notion: Deep Dive (select: Yes, No, NA)
    deep_dive                   TEXT DEFAULT '',
    -- Notion: EF/EO (select: FF, EF, EO)
    ef_eo                       TEXT DEFAULT '',
    -- Notion: Follow On Decision (select: No Decision, Token/Zero, PR, SPR)
    follow_on_decision          TEXT DEFAULT '',
    -- Notion: Follow-on Decision (select: Wait for 3 months, Closing, No for participation in strategic round)
    -- NOTE: This is a SEPARATE field from "Follow On Decision" above (different Notion property)
    follow_on_decision_alt      TEXT DEFAULT '',
    -- Notion: HC Priority (select: P0, P1, P2, P3, P4, NA — emoji stripped)
    hc_priority                 TEXT DEFAULT '',
    -- Notion: Health (select: Green, Yellow, Red, NA)
    health                      TEXT DEFAULT '',
    -- Notion: IP Pull (select: High, Medium, Low)
    ip_pull                     TEXT DEFAULT '',
    -- Notion: Investment Timeline (select: Q4 2022 through Q1 2026)
    investment_timeline         TEXT DEFAULT '',
    -- Notion: Likely Follow On Decision? (select: Pro-Rata, Super Pro-Rata, Notional/No)
    likely_follow_on_decision   TEXT DEFAULT '',
    -- Notion: Next 3 months IC Candidate (select: Yes)
    next_3m_ic_candidate        TEXT DEFAULT '',
    -- Notion: Ops Prio (select: P0, P1, P2, NA — emoji stripped)
    ops_prio                    TEXT DEFAULT '',
    -- Notion: Outcome Category (select: Cat A/B/C x Marketplace/Consumer Tech/Consumer/B2B/SaaS, Custom)
    outcome_category            TEXT DEFAULT '',
    -- Notion: Raised Follow-on funding? (select: Yes)
    raised_follow_on_funding    TEXT DEFAULT '',
    -- Notion: Referenceability (select: High, Medium, Low)
    referenceability            TEXT DEFAULT '',
    -- Notion: Revenue Generating (select: No, Yes)
    revenue_generating          TEXT DEFAULT '',
    -- Notion: Round 1 Type (select: Pre-Seed through Series D)
    round_1_type                TEXT DEFAULT '',
    -- Notion: Round 2 Type (select: Pre-Seed through Series D)
    round_2_type                TEXT DEFAULT '',
    -- Notion: Round 3 Type (select: Pre-Seed through Series D)
    round_3_type                TEXT DEFAULT '',
    -- Notion: Spikey (select: 1, 0.5, 0)
    spikey                      TEXT DEFAULT '',
    -- Notion: Stage @ entry (select: pre-product, early product, post product, early revenue, scaling revenue)
    stage_at_entry              TEXT DEFAULT '',
    -- Notion: Tier 1 and Marquee seed cap table (select: Yes, No)
    tier_1_marquee_cap_table    TEXT DEFAULT '',
    -- Notion: Today (select: Fund Priority, Funnel, Deadpool, NA, Exited, Capital Return)
    today                       TEXT DEFAULT '',
    -- Notion: UW Decision (select: Core Cheque, Community Pool, Syndicate)
    uw_decision                 TEXT DEFAULT '',

    -- -------------------------------------------------------------------------
    -- Multi-Select Fields (stored as TEXT arrays)
    -- -------------------------------------------------------------------------
    -- Notion: FY23-24 Compliance (multi_select: K1 - Done, Pending, Audited Fin AIF - Done, NA)
    fy23_24_compliance          TEXT[] DEFAULT '{}',
    -- Notion: Follow On Outcome (multi_select: Follow-on as desired, Pass for DeVC, Follow-on under allocation, etc.)
    follow_on_outcome           TEXT[] DEFAULT '{}',
    -- Notion: Follow-on Work Priority (multi_select: NA, P0, P1, P2)
    follow_on_work_priority     TEXT[] DEFAULT '{}',
    -- Notion: Next Round Status (multi_select: H2 25, H2 24, Raising, H1 26, Raised)
    next_round_status           TEXT[] DEFAULT '{}',
    -- Notion: PStatus (multi_select: In Closing / Paperwork, Onboarding, Tracking - Raise NA/3/6/9/12 months, etc.)
    pstatus                     TEXT[] DEFAULT '{}',
    -- Notion: Timing of Involvement? (multi_select: Early to round formation, On-going conversation, etc.)
    timing_of_involvement       TEXT[] DEFAULT '{}',

    -- -------------------------------------------------------------------------
    -- Number Fields — Dollar amounts stored as NUMERIC for precision
    -- -------------------------------------------------------------------------
    -- Notion: Entry Cheque (number, dollar, precision_0)
    entry_cheque                NUMERIC,
    -- Notion: Entry Round Raise (number, dollar)
    entry_round_raise           NUMERIC,
    -- Notion: Entry Round Valuation (number, dollar, precision_0)
    entry_round_valuation       NUMERIC,
    -- Notion: Last Round Valuation (number, dollar)
    last_round_valuation        NUMERIC,
    -- Notion: FMV Carried (number, dollar)
    fmv_carried                 NUMERIC,
    -- Notion: BU Reserve Defend (number, dollar)
    bu_reserve_defend           NUMERIC,
    -- Notion: BU Reserve No Defend (number, dollar, precision_0)
    bu_reserve_no_defend        NUMERIC,
    -- Notion: Earmarked Reserves (number, dollar)
    earmarked_reserves          NUMERIC,
    -- Notion: Reserve Committed (number, dollar)
    reserve_committed           NUMERIC,
    -- Notion: Reserve Deployed (number, dollar, precision_0)
    reserve_deployed            NUMERIC,
    -- Notion: Fresh Committed (number, dollar)
    fresh_committed             NUMERIC,
    -- Notion: Cash In Bank (number, dollar)
    cash_in_bank                NUMERIC,
    -- Notion: Room to deploy? (number, dollar)
    room_to_deploy              NUMERIC,
    -- Notion: Round 2 Raise (number, dollar)
    round_2_raise               NUMERIC,
    -- Notion: Round 2 Val (number, dollar)
    round_2_val                 NUMERIC,
    -- Notion: Round 3 Raise (number, dollar)
    round_3_raise               NUMERIC,
    -- Notion: Round 3 Val (number, dollar)
    round_3_val                 NUMERIC,
    -- Notion: Best case outcome (number, dollar, precision_0)
    best_case_outcome           NUMERIC,
    -- Notion: Good Case outcome (number, dollar, precision_0)
    good_case_outcome           NUMERIC,
    -- Notion: Likely Outcome (number, dollar)
    likely_outcome              NUMERIC,

    -- -------------------------------------------------------------------------
    -- Number Fields — Percentages stored as REAL (0.0 to 1.0)
    -- -------------------------------------------------------------------------
    -- Notion: Ownership % (number, percent)
    ownership_pct               REAL,
    -- Notion: Dilution IF Defend (number, percent)
    dilution_if_defend          REAL,
    -- Notion: Dilution IF NO Defend (number, percent)
    dilution_if_no_defend       REAL,

    -- -------------------------------------------------------------------------
    -- Text Fields
    -- -------------------------------------------------------------------------
    -- Notion: External Signal (text)
    external_signal             TEXT DEFAULT '',
    -- Notion: High Impact (text)
    high_impact                 TEXT DEFAULT '',
    -- Notion: Key Questions (text)
    key_questions               TEXT DEFAULT '',
    -- Notion: Note on deployment (text)
    note_on_deployment          TEXT DEFAULT '',
    -- Notion: Scale of Business (text)
    scale_of_business           TEXT DEFAULT '',

    -- -------------------------------------------------------------------------
    -- Date Fields
    -- -------------------------------------------------------------------------
    -- Notion: Action Due Date (date)
    action_due_date             DATE,
    -- Notion: Fumes Date (date)
    fumes_date                  DATE,

    -- -------------------------------------------------------------------------
    -- Timestamp Fields (from Notion system properties)
    -- -------------------------------------------------------------------------
    -- Notion: Last updated (last_edited_time)
    notion_last_edited          TIMESTAMPTZ,

    -- -------------------------------------------------------------------------
    -- PG-Only Enrichment Columns
    -- -------------------------------------------------------------------------
    -- Path to the company's research MD file on disk (populated by research file agent)
    research_file_path          TEXT,
    -- Agent-generated enrichment metadata (JSONB for flexible schema)
    enrichment_metadata         JSONB DEFAULT '{}'::jsonb,
    -- Signal history from content pipeline and agent observations
    signal_history              JSONB DEFAULT '[]'::jsonb,

    -- -------------------------------------------------------------------------
    -- Sync Infrastructure
    -- -------------------------------------------------------------------------
    created_at                  TIMESTAMPTZ DEFAULT now(),
    updated_at                  TIMESTAMPTZ DEFAULT now(),
    last_synced_at              TIMESTAMPTZ
);

-- Comments on the table
COMMENT ON TABLE portfolio IS 'Portfolio companies from Notion Portfolio DB (4dba9b7f). 100 rows at audit time. Synced via SyncAgent.';


-- =============================================================================
-- PART 2: INDEXES
-- =============================================================================

-- Primary lookup: Notion page ID (for sync operations)
-- Already UNIQUE constraint above, which creates an index automatically.

-- Portfolio company name (for text search and display)
CREATE INDEX IF NOT EXISTS idx_portfolio_portfolio_co ON portfolio (portfolio_co);

-- Company relation (FK-like lookup to companies table)
CREATE INDEX IF NOT EXISTS idx_portfolio_company_name_id ON portfolio (company_name_id);

-- Health monitoring (filter by health status)
CREATE INDEX IF NOT EXISTS idx_portfolio_health ON portfolio (health);

-- Today status (primary portfolio triage view)
CREATE INDEX IF NOT EXISTS idx_portfolio_today ON portfolio (today);

-- HC Priority (portfolio company priority ranking)
CREATE INDEX IF NOT EXISTS idx_portfolio_hc_priority ON portfolio (hc_priority);

-- Ops Priority (operational priority ranking)
CREATE INDEX IF NOT EXISTS idx_portfolio_ops_prio ON portfolio (ops_prio);

-- Current Stage (stage-based filtering)
CREATE INDEX IF NOT EXISTS idx_portfolio_current_stage ON portfolio (current_stage);

-- Investment Timeline (temporal analysis)
CREATE INDEX IF NOT EXISTS idx_portfolio_investment_timeline ON portfolio (investment_timeline);

-- Action Due Date (time-sensitive actions)
CREATE INDEX IF NOT EXISTS idx_portfolio_action_due_date ON portfolio (action_due_date);

-- Fumes Date (runway urgency)
CREATE INDEX IF NOT EXISTS idx_portfolio_fumes_date ON portfolio (fumes_date);

-- AIF/USA (fund segmentation)
CREATE INDEX IF NOT EXISTS idx_portfolio_aif_usa ON portfolio (aif_usa);

-- Sync infrastructure
CREATE INDEX IF NOT EXISTS idx_portfolio_last_synced_at ON portfolio (last_synced_at);
CREATE INDEX IF NOT EXISTS idx_portfolio_updated_at ON portfolio (updated_at);

-- GIN index for array fields commonly used in WHERE clauses
CREATE INDEX IF NOT EXISTS idx_portfolio_pstatus ON portfolio USING GIN (pstatus);
CREATE INDEX IF NOT EXISTS idx_portfolio_next_round_status ON portfolio USING GIN (next_round_status);
CREATE INDEX IF NOT EXISTS idx_portfolio_follow_on_work_priority ON portfolio USING GIN (follow_on_work_priority);


-- =============================================================================
-- PART 3: FORMULA FIELD NOTES (NOT CREATED — reference only)
-- =============================================================================
-- These 9 Notion formula fields are computed server-side in Notion.
-- If needed in PG, implement as views or materialized views.
--
-- Bottoms-Up Reserve = f(BU Reserve Defend, BU Reserve No Defend, BU Follow-On Tag)
-- Est. Capital In    = f(Entry Cheque, Reserve Deployed, Fresh Committed)
-- FMV Last Round     = f(Ownership %, Last Round Valuation)
-- Last round raise   = f(Entry Round Raise, Round 2 Raise, Round 3 Raise)
-- Money In           = f(Entry Cheque, Reserve Deployed)
-- P&L                = f(FMV Carried, Money In)
-- Top-Down Reserve   = f(Earmarked Reserves, Reserve Deployed)
-- Top-Down Reserve OLD = (deprecated version of above)
-- Total raise to date = f(Entry Round Raise, Round 2 Raise, Round 3 Raise)
--
-- Example view (uncomment if needed):
-- CREATE OR REPLACE VIEW portfolio_computed AS
-- SELECT *,
--     (entry_cheque + COALESCE(reserve_deployed, 0)) AS money_in,
--     (fmv_carried - (entry_cheque + COALESCE(reserve_deployed, 0))) AS p_and_l,
--     (ownership_pct * last_round_valuation) AS fmv_last_round,
--     (COALESCE(entry_round_raise, 0) + COALESCE(round_2_raise, 0) + COALESCE(round_3_raise, 0)) AS total_raise_to_date,
--     (earmarked_reserves - COALESCE(reserve_deployed, 0)) AS top_down_reserve,
--     (COALESCE(entry_cheque, 0) + COALESCE(reserve_deployed, 0) + COALESCE(fresh_committed, 0)) AS est_capital_in
-- FROM portfolio;


-- =============================================================================
-- PART 4: ROLLUP FIELD NOTES (NOT CREATED — reference only)
-- =============================================================================
-- These 9 Notion rollup fields aggregate data from related databases.
-- In PG, resolve via JOINs to the companies and network tables.
--
-- Angels           -> rollup from Companies DB (angel investors)
-- Co-Investors     -> rollup from Companies DB (co-investment partners)
-- Founders         -> rollup from Companies DB (founding team)
-- Founding timeline -> rollup from Companies DB (when founded)
-- Funding to date  -> rollup from Companies DB (total funding raised)
-- Pending Tasks    -> rollup from Tasks Tracker (open tasks for this company)
-- Sector           -> rollup from Companies DB (high-level sector)
-- Sector Tags      -> rollup from Companies DB (granular sector tags)
-- Vault link       -> rollup from Companies DB (data room link)


-- =============================================================================
-- PART 5: TRIGGER FOR updated_at
-- =============================================================================
-- Reuse the same pattern as companies/network tables

CREATE OR REPLACE FUNCTION update_portfolio_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_portfolio_updated_at ON portfolio;
CREATE TRIGGER trg_portfolio_updated_at
    BEFORE UPDATE ON portfolio
    FOR EACH ROW
    EXECUTE FUNCTION update_portfolio_updated_at();
