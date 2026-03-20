-- =============================================================================
-- Companies DB + Network DB: Schema Migration
-- =============================================================================
-- Generated: 2026-03-20
-- Source: Three-way cross-reference of LIVE Notion schemas, LIVE Postgres schemas,
--         and prior audit (2026-03-20-companies-network-schema-audit.md)
--
-- Rule: Final PG schema = MAX(current Postgres + full Notion). No drops.
-- Strategy: Idempotent (IF NOT EXISTS / ADD COLUMN IF NOT EXISTS).
-- Action: DO NOT EXECUTE without review. This is PREPARE ONLY.
-- =============================================================================


-- =============================================================================
-- PART 1: COMPANIES TABLE
-- =============================================================================
-- Live Notion: 49 properties
-- Live Postgres: 32 columns
-- After migration: 32 existing + 20 new = 52 columns
--
-- Skipped Notion fields (computed/system — recompute in PG if needed):
--   AIF/USA (formula), Money In (formula), Ownership % (formula)
--   AIF/USA (Rollup) (rollup), Money In (Rollup) (rollup), Ownership % (Rollup) (rollup)
--   Created by (system), Last edited time (system — already captured as notion_last_edited)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1A. COMPANIES: Fields that exist in Notion but NOT in Postgres
-- -----------------------------------------------------------------------------

-- Money Committed (Notion: number, format: dollar)
-- Financial data needed for portfolio analysis and deal scoring
ALTER TABLE companies ADD COLUMN IF NOT EXISTS money_committed REAL;
COMMENT ON COLUMN companies.money_committed IS 'Notion: Money Committed (number/dollar). Money committed to deal in $M.';

-- Action Due? (Notion: date, format: DD/MM/YYYY)
-- Powers action scoring time_sensitivity factor
ALTER TABLE companies ADD COLUMN IF NOT EXISTS action_due DATE;
COMMENT ON COLUMN companies.action_due IS 'Notion: Action Due? (date). Next action due date — drives time_sensitivity scoring.';

-- Surface to collective (Notion: date)
-- DeVC collective timing
ALTER TABLE companies ADD COLUMN IF NOT EXISTS surface_to_collective DATE;
COMMENT ON COLUMN companies.surface_to_collective IS 'Notion: Surface to collective (date). When to surface deal to DeVC collective.';

-- Current People (Notion: relation -> Network DB 6462102f)
-- Critical for BRC graph queries and people-company graph
ALTER TABLE companies ADD COLUMN IF NOT EXISTS current_people_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.current_people_ids IS 'Notion: Current People (relation -> Network DB). Notion page IDs of people currently at this company.';

-- Angels (Notion: relation -> Network DB 6462102f)
-- Co-investment analysis
ALTER TABLE companies ADD COLUMN IF NOT EXISTS angel_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.angel_ids IS 'Notion: Angels (relation -> Network DB). Angel investors in this company.';

-- Alums (Notion: relation -> Network DB 6462102f)
-- Career pattern analysis
ALTER TABLE companies ADD COLUMN IF NOT EXISTS alum_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.alum_ids IS 'Notion: Alums (relation -> Network DB). Former employees now in the network.';

-- MPI Connect (Notion: relation -> Network DB 6462102f)
-- Z47 relationship mapping
ALTER TABLE companies ADD COLUMN IF NOT EXISTS mpi_connect_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.mpi_connect_ids IS 'Notion: MPI Connect (relation -> Network DB). Z47/MPI connections to this company.';

-- Domain Eval? (Notion: relation -> Network DB 6462102f)
-- Evaluation assignment
ALTER TABLE companies ADD COLUMN IF NOT EXISTS domain_eval_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.domain_eval_ids IS 'Notion: Domain Eval? (relation -> Network DB). IC/expert who can evaluate the domain.';

-- Piped From (Notion: relation -> Network DB 6462102f)
-- Attribution tracking
ALTER TABLE companies ADD COLUMN IF NOT EXISTS piped_from_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.piped_from_ids IS 'Notion: Piped From (relation -> Network DB). Who sourced/piped this deal.';

-- Met by? (Notion: relation -> Network DB 6462102f)
-- GP contact tracking
ALTER TABLE companies ADD COLUMN IF NOT EXISTS met_by_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.met_by_ids IS 'Notion: Met by? (relation -> Network DB). Which GP/team member first met founder.';

-- Shared with (Notion: relation -> Network DB 6462102f)
-- Evaluation sharing
ALTER TABLE companies ADD COLUMN IF NOT EXISTS shared_with_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.shared_with_ids IS 'Notion: Shared with (relation -> Network DB). Who the deal was shared with for evaluation.';

-- YC Partner (Notion: relation -> Network DB 6462102f)
-- YC relationship mapping
ALTER TABLE companies ADD COLUMN IF NOT EXISTS yc_partner_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.yc_partner_ids IS 'Notion: YC Partner (relation -> Network DB). YC partner for YC batch companies.';

-- 🌐 Network DB (Notion: relation -> Network DB 6462102f)
-- Generic catch-all Network DB link
-- NOTE: Audit called this "Network DB" — live Notion name is "🌐 Network DB"
ALTER TABLE companies ADD COLUMN IF NOT EXISTS network_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.network_ids IS 'Notion: 🌐 Network DB (relation -> Network DB). Generic catch-all Network link.';

-- Investors (VCs, Micros) (Notion: relation -> Companies DB self 1edda9cc)
-- Market intelligence graph
ALTER TABLE companies ADD COLUMN IF NOT EXISTS investor_company_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.investor_company_ids IS 'Notion: Investors (VCs, Micros) (self-relation -> Companies DB). VC firms that invested in this company.';

-- Known Portfolio (Notion: relation -> Companies DB self 1edda9cc)
-- VC portfolio mapping
ALTER TABLE companies ADD COLUMN IF NOT EXISTS known_portfolio_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.known_portfolio_ids IS 'Notion: Known Portfolio (self-relation -> Companies DB). Portfolio companies (for VC firm records).';

-- 💰 Finance DB (Notion: relation -> Finance DB 9b59fd98-919d-4043-993d-eb7772659dd6)
-- NOTE: Audit called this "Finance DB" — live Notion name is "💰 Finance DB", target DB is 9b59fd98 (NOT the ID in audit)
ALTER TABLE companies ADD COLUMN IF NOT EXISTS finance_notion_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.finance_notion_ids IS 'Notion: 💰 Finance DB (relation -> 9b59fd98-919d-4043-993d-eb7772659dd6). Cross-DB link to financial data.';

-- Corp Dev (Notion: relation -> Corp Dev DB 59c31a93-110d-4e80-a5ca-84c43f585ae2)
-- NOTE: Audit called this "Corp Dev DB" — live Notion name is "Corp Dev"
ALTER TABLE companies ADD COLUMN IF NOT EXISTS corp_dev_notion_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.corp_dev_notion_ids IS 'Notion: Corp Dev (relation -> 59c31a93-110d-4e80-a5ca-84c43f585ae2). Corporate development tracking.';

-- Portfolio Interaction Notes (Notion: relation -> Portfolio DB 4dba9b7f)
-- NOTE: Audit called this "Portfolio DB" — live Notion name is "Portfolio Interaction Notes"
ALTER TABLE companies ADD COLUMN IF NOT EXISTS portfolio_notion_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.portfolio_notion_ids IS 'Notion: Portfolio Interaction Notes (relation -> Portfolio DB 4dba9b7f). Link to portfolio interaction tracking.';

-- Meeting Notes (Notion: relation -> Meeting Notes DB 0dc61edf-2fab-47e2-8225-c677477f29b9)
-- AUDIT MISSED THIS FIELD — discovered in live Notion schema
ALTER TABLE companies ADD COLUMN IF NOT EXISTS meeting_note_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.meeting_note_ids IS 'Notion: Meeting Notes (relation -> 0dc61edf-2fab-47e2-8225-c677477f29b9). Meeting notes linked to this company. MISSED BY ORIGINAL AUDIT.';

-- Pending Tasks (Notion: relation -> Tasks Tracker 1b829bcc)
-- NOTE: Audit listed both "Tasks Tracker" and "Pending Tasks" — live Notion only has "Pending Tasks"
ALTER TABLE companies ADD COLUMN IF NOT EXISTS pending_task_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN companies.pending_task_ids IS 'Notion: Pending Tasks (relation -> Tasks Tracker 1b829bcc). Open action items. Only relation to Tasks Tracker in live schema.';

-- DeVC IP POC (Notion: person)
-- POC assignment
ALTER TABLE companies ADD COLUMN IF NOT EXISTS devc_ip_poc TEXT DEFAULT '';
COMMENT ON COLUMN companies.devc_ip_poc IS 'Notion: DeVC IP POC (person). DeVC investment professional point of contact.';


-- -----------------------------------------------------------------------------
-- 1B. COMPANIES: Audit corrections — fields that do NOT need migration
-- -----------------------------------------------------------------------------
--
-- "Last Round Timing" — Audit noted Postgres column last_round_timing had "no clear Notion match".
-- CORRECTION: Live Notion HAS "Last Round Timing" (select, 11 options) → already mapped to last_round_timing. No action needed.
--
-- "Tasks Tracker" — Audit listed as separate field (#44).
-- CORRECTION: Live Notion does NOT have "Tasks Tracker" as a separate relation. Only "Pending Tasks" exists. Single column covers both.
--
-- "Description/Notes" — Audit listed as field #49 (inferred from CONTEXT.md).
-- CORRECTION: Live Notion does NOT have this field. Not adding to Postgres since it doesn't exist in the source.
-- If a description field is needed for agents, it should be added as a PG-only enrichment column (see 1C below).
--


-- -----------------------------------------------------------------------------
-- 1C. COMPANIES: Optional PG-only enrichment column for description
-- -----------------------------------------------------------------------------
-- The audit recommended a 'description' column for agent reasoning.
-- While the Notion field doesn't exist, agents may still want to store
-- enriched company descriptions. Uncomment if desired.
--
-- ALTER TABLE companies ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '';
-- COMMENT ON COLUMN companies.description IS 'PG-only enrichment: Agent-generated company description (no Notion source).';


-- -----------------------------------------------------------------------------
-- 1D. COMPANIES: Indexes for new columns
-- -----------------------------------------------------------------------------

-- Action due date: powers time-sensitive action scoring queries
CREATE INDEX IF NOT EXISTS idx_companies_action_due ON companies(action_due) WHERE action_due IS NOT NULL;

-- Surface to collective: DeVC timing queries
CREATE INDEX IF NOT EXISTS idx_companies_surface_to_collective ON companies(surface_to_collective) WHERE surface_to_collective IS NOT NULL;

-- Pipeline status: most common filter in deal funnel queries (if not already indexed)
CREATE INDEX IF NOT EXISTS idx_companies_pipeline_status ON companies(pipeline_status);

-- GIN indexes for array columns used in graph queries
CREATE INDEX IF NOT EXISTS idx_companies_current_people_ids ON companies USING GIN(current_people_ids) WHERE current_people_ids != '{}';
CREATE INDEX IF NOT EXISTS idx_companies_investor_company_ids ON companies USING GIN(investor_company_ids) WHERE investor_company_ids != '{}';
CREATE INDEX IF NOT EXISTS idx_companies_known_portfolio_ids ON companies USING GIN(known_portfolio_ids) WHERE known_portfolio_ids != '{}';


-- =============================================================================
-- PART 2: NETWORK TABLE
-- =============================================================================
-- Live Notion: 42 properties
-- Live Postgres: 34 columns
-- After migration: 34 existing + 12 new = 46 columns
--
-- Skipped Notion fields (computed/deprecated/system):
--   Batch (rollup), Company Stage (rollup), Sector Classification (rollup)
--   Last edited time (system — already captured as notion_last_edited)
--   Network Tasks? (deprecated relation -> 22729bcc)
--   Unstructured Leads (legacy relation -> 9fef782f)
--   Venture Partner? (old) (deprecated relation -> Portfolio DB)
--
-- Audit-listed fields NOT in live Notion (PG-only enrichment candidates):
--   Email, Phone, IDS Notes, Relationship Status, Last Interaction, Source
--   These are listed separately in section 2B below.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 2A. NETWORK: Fields that exist in live Notion but NOT in Postgres
-- -----------------------------------------------------------------------------

-- Schools (Notion: relation -> Companies DB 1edda9cc)
-- Alumni network analysis — schools stored as Companies DB entities
ALTER TABLE network ADD COLUMN IF NOT EXISTS school_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.school_ids IS 'Notion: Schools (relation -> Companies DB). Educational institutions (stored as Companies DB entities).';

-- Angel Folio (Notion: relation -> Companies DB 1edda9cc)
-- Co-investment analysis
ALTER TABLE network ADD COLUMN IF NOT EXISTS angel_folio_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.angel_folio_ids IS 'Notion: Angel Folio (relation -> Companies DB). Companies angel-invested in.';

-- Sourcing Attribution (Notion: relation -> Portfolio DB 4dba9b7f)
-- Attribution tracking
ALTER TABLE network ADD COLUMN IF NOT EXISTS sourcing_attribution_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.sourcing_attribution_ids IS 'Notion: Sourcing Attribution (relation -> Portfolio DB). Portfolio companies they sourced.';

-- Participation Attribution (Notion: relation -> Portfolio DB 4dba9b7f)
-- Co-investment tracking
ALTER TABLE network ADD COLUMN IF NOT EXISTS participation_attribution_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.participation_attribution_ids IS 'Notion: Participation Attribution (relation -> Portfolio DB). Portfolio deals they co-invested in.';

-- Led by? (Notion: relation -> Portfolio DB 4dba9b7f)
-- Lead investor relationships
ALTER TABLE network ADD COLUMN IF NOT EXISTS led_by_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.led_by_ids IS 'Notion: Led by? (relation -> Portfolio DB). Portfolio companies they led investment in.';

-- Piped to DeVC (Notion: relation -> Companies DB 1edda9cc)
-- Pipeline attribution
ALTER TABLE network ADD COLUMN IF NOT EXISTS piped_to_devc_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.piped_to_devc_ids IS 'Notion: Piped to DeVC (relation -> Companies DB). Companies referred into DeVC pipeline.';

-- YC Partner Portfolio (Notion: relation -> Companies DB 1edda9cc)
-- YC mapping
ALTER TABLE network ADD COLUMN IF NOT EXISTS yc_partner_portfolio_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.yc_partner_portfolio_ids IS 'Notion: YC Partner Portfolio (relation -> Companies DB). YC partner relationship for YC alumni.';

-- C+E Speaker (Notion: relation -> Events DB a9b347af-3e71-450e-9138-9e86114155c3)
-- Event participation
ALTER TABLE network ADD COLUMN IF NOT EXISTS ce_speaker_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.ce_speaker_ids IS 'Notion: C+E Speaker (relation -> Events DB a9b347af). Events spoken at.';

-- C+E Attendance (Notion: relation -> Events DB a9b347af-3e71-450e-9138-9e86114155c3)
-- Event participation
ALTER TABLE network ADD COLUMN IF NOT EXISTS ce_attendance_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.ce_attendance_ids IS 'Notion: C+E Attendance (relation -> Events DB a9b347af). Events attended.';

-- Meeting Notes (Notion: relation -> Meeting Notes DB 0dc61edf-2fab-47e2-8225-c677477f29b9)
-- Meeting history lookup
ALTER TABLE network ADD COLUMN IF NOT EXISTS meeting_note_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.meeting_note_ids IS 'Notion: Meeting Notes (relation -> Meeting Notes DB 0dc61edf). Meeting notes entries.';

-- Tasks Pending (Notion: relation -> Tasks Tracker 1b829bcc)
-- Open action items with this person
ALTER TABLE network ADD COLUMN IF NOT EXISTS task_pending_ids TEXT[] DEFAULT '{}';
COMMENT ON COLUMN network.task_pending_ids IS 'Notion: Tasks Pending (relation -> Tasks Tracker 1b829bcc). Open action items.';

-- DeVC POC (Notion: person)
-- Point of contact on DeVC team
ALTER TABLE network ADD COLUMN IF NOT EXISTS devc_poc TEXT DEFAULT '';
COMMENT ON COLUMN network.devc_poc IS 'Notion: DeVC POC (person). Point of contact on DeVC team.';


-- -----------------------------------------------------------------------------
-- 2B. NETWORK: PG-only enrichment columns (NOT in live Notion)
-- -----------------------------------------------------------------------------
-- The original audit listed these as potentially in Notion but needing verification.
-- Live Notion confirms: Email, Phone, IDS Notes, Relationship Status, Last Interaction,
-- and Source do NOT exist as Notion properties.
--
-- However, per the MAX rule (keep everything), these are valuable for agent reasoning
-- and should be added as PG-only enrichment columns. They can be populated by agents
-- or future Notion property additions.

-- IDS Notes: critical for agent reasoning (IDS notation per person)
ALTER TABLE network ADD COLUMN IF NOT EXISTS ids_notes TEXT DEFAULT '';
COMMENT ON COLUMN network.ids_notes IS 'PG-only enrichment: IDS notation per person. Not in Notion (verified 2026-03-20). Critical for agent reasoning.';

-- Last Interaction: powers staleness detection and action scoring
ALTER TABLE network ADD COLUMN IF NOT EXISTS last_interaction DATE;
COMMENT ON COLUMN network.last_interaction IS 'PG-only enrichment: Last interaction date. Not in Notion (verified 2026-03-20). Powers staleness detection.';

-- Email: contact info for outreach
ALTER TABLE network ADD COLUMN IF NOT EXISTS email TEXT DEFAULT '';
COMMENT ON COLUMN network.email IS 'PG-only enrichment: Email address. Not in Notion (verified 2026-03-20). For outreach and matching.';

-- Phone: contact info for outreach
ALTER TABLE network ADD COLUMN IF NOT EXISTS phone TEXT DEFAULT '';
COMMENT ON COLUMN network.phone IS 'PG-only enrichment: Phone number. Not in Notion (verified 2026-03-20). For outreach.';

-- Relationship Status: overall relationship classification
ALTER TABLE network ADD COLUMN IF NOT EXISTS relationship_status TEXT DEFAULT '';
COMMENT ON COLUMN network.relationship_status IS 'PG-only enrichment: Relationship status. Not in Notion (verified 2026-03-20). Broader than R/Y/G.';

-- Source: how this person entered the network
ALTER TABLE network ADD COLUMN IF NOT EXISTS source TEXT DEFAULT '';
COMMENT ON COLUMN network.source IS 'PG-only enrichment: How this person entered the network. Not in Notion (verified 2026-03-20).';


-- -----------------------------------------------------------------------------
-- 2C. NETWORK: Indexes for new columns
-- -----------------------------------------------------------------------------

-- Last interaction: staleness detection queries
CREATE INDEX IF NOT EXISTS idx_network_last_interaction ON network(last_interaction) WHERE last_interaction IS NOT NULL;

-- R/Y/G: relationship health filter (if not already indexed)
CREATE INDEX IF NOT EXISTS idx_network_ryg ON network(ryg);

-- E/E Priority: engagement priority filter (if not already indexed)
CREATE INDEX IF NOT EXISTS idx_network_e_e_priority ON network(e_e_priority);

-- LinkedIn: dedup key and lookup (if not already indexed)
CREATE INDEX IF NOT EXISTS idx_network_linkedin ON network(linkedin) WHERE linkedin IS NOT NULL;

-- Email: contact lookup
CREATE INDEX IF NOT EXISTS idx_network_email ON network(email) WHERE email IS NOT NULL AND email != '';

-- GIN indexes for attribution array columns used in graph queries
CREATE INDEX IF NOT EXISTS idx_network_sourcing_attribution ON network USING GIN(sourcing_attribution_ids) WHERE sourcing_attribution_ids != '{}';
CREATE INDEX IF NOT EXISTS idx_network_participation_attribution ON network USING GIN(participation_attribution_ids) WHERE participation_attribution_ids != '{}';
CREATE INDEX IF NOT EXISTS idx_network_led_by ON network USING GIN(led_by_ids) WHERE led_by_ids != '{}';


-- =============================================================================
-- PART 3: SUMMARY
-- =============================================================================
--
-- COMPANIES TABLE:
--   Existing columns kept: 32 (no drops per MAX rule)
--   New columns from Notion: 21
--     - 1 number field (money_committed)
--     - 2 date fields (action_due, surface_to_collective)
--     - 1 person field (devc_ip_poc)
--     - 17 relation fields (various -> Network DB, Companies DB self, Portfolio DB, Meeting Notes DB, etc.)
--   New indexes: 6
--   Final column count: 53
--
-- NETWORK TABLE:
--   Existing columns kept: 34 (no drops per MAX rule)
--   New columns from Notion: 12
--     - 1 person field (devc_poc)
--     - 11 relation fields (various -> Companies DB, Portfolio DB, Events DB, etc.)
--   New PG-only enrichment columns: 6 (ids_notes, last_interaction, email, phone, relationship_status, source)
--   New indexes: 8
--   Final column count: 52
--
-- CORRECTIONS FROM AUDIT (verified against live Notion 2026-03-20):
--   Companies DB:
--     1. "Corp Dev DB" → actual Notion name is "Corp Dev" (target: 59c31a93)
--     2. "Finance DB" → actual Notion name is "💰 Finance DB" (target: 9b59fd98, NOT same as audit assumed)
--     3. "Network DB" → actual Notion name is "🌐 Network DB"
--     4. "Portfolio DB" → actual Notion name is "Portfolio Interaction Notes"
--     5. "Tasks Tracker" → DOES NOT EXIST in live Notion. Only "Pending Tasks" exists.
--     6. "Description/Notes" → DOES NOT EXIST in live Notion (was inferred from CONTEXT.md)
--     7. "Last Round Timing" → EXISTS in both Notion and Postgres. Audit said "no clear Notion match" — WRONG.
--     8. "Meeting Notes" → MISSED by audit. Exists in live Notion (relation -> 0dc61edf).
--   Network DB:
--     9. "url" and "createdTime" listed as system fields → NOT exposed in live Notion schema (42 live vs 44 audit)
--     10. Email, Phone, IDS Notes, Relationship Status, Last Interaction, Source → confirmed NOT in Notion
--     11. "Batch", "Company Stage", "Sector Classification" → confirmed as rollup type (skip)
--
-- =============================================================================
