-- =============================================================================
-- M6 IRGI Loop 8: FTS Column Enrichment for Search Quality
-- =============================================================================
-- Executed: 2026-03-20 on Supabase llfkxnsfczludgigknbs (Mumbai)
-- Problem: FTS GENERATED columns only indexed 2-3 fields per table.
--   Companies: name + sector + agent_ids_notes → near-zero FTS recall
--   Network: person_name + role_title + linkedin → misses IDS notes, relationships
--   Content Digests: title + channel + content_type → misses ALL digest_data JSONB
--   Portfolio: portfolio_co + health + today → misses key investment fields
-- Fix: Drop and recreate with comprehensive field coverage.
-- =============================================================================

-- Immutable wrapper for array_to_string (STABLE → IMMUTABLE)
-- Required because GENERATED columns only accept IMMUTABLE expressions
CREATE OR REPLACE FUNCTION immutable_array_to_string(arr text[], sep text DEFAULT ' ')
RETURNS text
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
AS $$
  SELECT array_to_string(arr, sep);
$$;

-- =============================================================================
-- COMPANIES: 3 fields → 14 fields
-- =============================================================================
DROP INDEX IF EXISTS idx_companies_fts;
ALTER TABLE companies DROP COLUMN IF EXISTS fts;

ALTER TABLE companies ADD COLUMN fts tsvector GENERATED ALWAYS AS (
  to_tsvector('english'::regconfig,
    COALESCE(name, '') || ' ' ||
    COALESCE(sector, '') || ' ' ||
    COALESCE(deal_status, '') || ' ' ||
    COALESCE(pipeline_status, '') || ' ' ||
    COALESCE(type, '') || ' ' ||
    COALESCE(priority, '') || ' ' ||
    COALESCE(immutable_array_to_string(sector_tags), '') || ' ' ||
    COALESCE(immutable_array_to_string(jtbd), '') || ' ' ||
    COALESCE(immutable_array_to_string(sells_to), '') || ' ' ||
    COALESCE(agent_ids_notes, '') || ' ' ||
    COALESCE(smart_money, '') || ' ' ||
    COALESCE(hil_review, '') || ' ' ||
    COALESCE(founding_timeline, '') || ' ' ||
    COALESCE(venture_funding, '')
  )
) STORED;

CREATE INDEX idx_companies_fts ON companies USING GIN (fts);

-- =============================================================================
-- NETWORK: 3 fields → 11 fields
-- =============================================================================
DROP INDEX IF EXISTS idx_network_fts;
ALTER TABLE network DROP COLUMN IF EXISTS fts;

ALTER TABLE network ADD COLUMN fts tsvector GENERATED ALWAYS AS (
  to_tsvector('english'::regconfig,
    COALESCE(person_name, '') || ' ' ||
    COALESCE(role_title, '') || ' ' ||
    COALESCE(ids_notes, '') || ' ' ||
    COALESCE(relationship_status, '') || ' ' ||
    COALESCE(immutable_array_to_string(home_base), '') || ' ' ||
    COALESCE(immutable_array_to_string(devc_relationship), '') || ' ' ||
    COALESCE(immutable_array_to_string(collective_flag), '') || ' ' ||
    COALESCE(investing_activity, '') || ' ' ||
    COALESCE(sourcing_flow_hots, '') || ' ' ||
    COALESCE(e_e_priority, '') || ' ' ||
    COALESCE(devc_poc, '')
  )
) STORED;

CREATE INDEX idx_network_fts ON network USING GIN (fts);

-- =============================================================================
-- CONTENT DIGESTS: 3 fields → 9 fields (includes JSONB extraction)
-- =============================================================================
DROP INDEX IF EXISTS idx_content_digests_fts;
ALTER TABLE content_digests DROP COLUMN IF EXISTS fts;

ALTER TABLE content_digests ADD COLUMN fts tsvector GENERATED ALWAYS AS (
  to_tsvector('english'::regconfig,
    COALESCE(title, '') || ' ' ||
    COALESCE(channel, '') || ' ' ||
    COALESCE(content_type, '') || ' ' ||
    COALESCE(digest_data->>'essence_notes', '') || ' ' ||
    COALESCE(digest_data->>'relevance', '') || ' ' ||
    COALESCE(digest_data->>'thesis_connections', '') || ' ' ||
    COALESCE(digest_data->>'contra_signals', '') || ' ' ||
    COALESCE(digest_data->>'portfolio_connections', '') || ' ' ||
    COALESCE(digest_data->>'net_newness', '')
  )
) STORED;

CREATE INDEX idx_content_digests_fts ON content_digests USING GIN (fts);

-- =============================================================================
-- PORTFOLIO: 3 fields → 11 fields
-- =============================================================================
DROP INDEX IF EXISTS idx_portfolio_fts;
ALTER TABLE portfolio DROP COLUMN IF EXISTS fts;

ALTER TABLE portfolio ADD COLUMN fts tsvector GENERATED ALWAYS AS (
  to_tsvector('english'::regconfig,
    COALESCE(portfolio_co, '') || ' ' ||
    COALESCE(health, '') || ' ' ||
    COALESCE(today, '') || ' ' ||
    COALESCE(current_stage, '') || ' ' ||
    COALESCE(outcome_category, '') || ' ' ||
    COALESCE(follow_on_decision, '') || ' ' ||
    COALESCE(spikey, '') || ' ' ||
    COALESCE(external_signal, '') || ' ' ||
    COALESCE(key_questions, '') || ' ' ||
    COALESCE(high_impact, '') || ' ' ||
    COALESCE(scale_of_business, '')
  )
) STORED;

CREATE INDEX idx_portfolio_fts ON portfolio USING GIN (fts);
