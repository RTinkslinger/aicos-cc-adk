-- =============================================================================
-- Datum Agent: Database Migrations
-- =============================================================================
-- Generated: 2026-03-20
-- Purpose: Create datum_requests table + ALTER network/companies for enrichment
--          tracking, dedup support, and embedding infrastructure.
--
-- Strategy: Idempotent (IF NOT EXISTS / ADD COLUMN IF NOT EXISTS).
-- Dependencies:
--   - pgvector extension (already enabled from IRGI Phase A)
--   - util schema + queue_embeddings trigger (already from IRGI Phase A)
--   - companies.embedding already exists (from IRGI Phase A)
--   - network.embedding does NOT exist (excluded from IRGI)
--
-- Execution: Run via Supabase MCP execute_sql in sequential batches.
-- =============================================================================


-- =============================================================================
-- PART 1: datum_requests TABLE
-- =============================================================================
-- Human-in-the-loop queue for data quality. When the Datum Agent cannot fill
-- a field or is unsure about a merge, it creates a datum request.
-- Users answer on WebFront (digest.wiki/datum). Answered requests trigger
-- field updates via Server Actions.

CREATE TABLE IF NOT EXISTS datum_requests (
    id SERIAL PRIMARY KEY,

    -- What entity this request is about
    entity_type TEXT NOT NULL,
        -- 'person' or 'company'
    entity_id INTEGER NOT NULL,
        -- FK to network.id or companies.id

    -- What field needs filling
    field_name TEXT NOT NULL,
        -- Column name on the target table (e.g., 'email', 'sector')

    -- Context for the user
    source_context TEXT,
        -- Where this entity came from: "CAI message: Add Rahul from Composio"
    current_value TEXT,
        -- Current value of the field (NULL if empty, shows existing value for correction requests)
    suggested_value TEXT,
        -- Agent's best guess if it has one but is not confident enough to write
    suggestion_confidence REAL,
        -- 0.0-1.0. If > 0.9, agent would have written it directly.
    suggestion_source TEXT,
        -- Where the suggestion came from: "LinkedIn scrape", "web search", "name inference"

    -- Dedup-specific fields (for merge confirmation requests)
    merge_candidate_ids INTEGER[],
        -- If this is a "confirm merge" request, the candidate record IDs
    merge_type TEXT,
        -- 'confirm_merge' | 'pick_match' | 'fill_field'

    -- Lifecycle
    status TEXT NOT NULL DEFAULT 'pending',
        -- pending | answered | skipped | expired
    answer TEXT,
        -- The user's answer (written by WebFront Server Action)
    answered_by TEXT,
        -- 'webfront' | 'cai' | 'auto'
    answered_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for WebFront queries (pending requests, sorted by recency)
CREATE INDEX IF NOT EXISTS idx_datum_requests_status
  ON datum_requests(status) WHERE status = 'pending';

-- Index for per-entity lookups (dedup check before creating new requests)
CREATE INDEX IF NOT EXISTS idx_datum_requests_entity
  ON datum_requests(entity_type, entity_id);

-- Index for field-level dedup (prevent duplicate pending requests for same entity+field)
CREATE INDEX IF NOT EXISTS idx_datum_requests_entity_field
  ON datum_requests(entity_type, entity_id, field_name) WHERE status = 'pending';

COMMENT ON TABLE datum_requests IS 'Human-in-the-loop queue for Datum Agent. Created when agent cannot fill a field or needs merge confirmation.';


-- =============================================================================
-- PART 2: ALTER TABLE network — Enrichment + Dedup columns
-- =============================================================================
-- The network table (3728 rows) already has: person_name, role_title,
-- home_base TEXT[], linkedin, embedding vector(1024), fts tsvector.
-- Adding enrichment tracking, aliases, and source tracking for Datum Agent.
--
-- EXECUTED: 2026-03-20 via Supabase MCP (verified: all columns present)
-- NOTE: The design spec assumed generic column names (name, role, city, linkedin_url).
--       Actual columns are: person_name, role_title, home_base, linkedin.
--       The linkedin_url column was created then dropped (linkedin already had 3247 values).
--       A UNIQUE index on linkedin was not possible due to existing duplicates.

-- Page content (Notion page body, loaded from network-pages/ files)
ALTER TABLE network ADD COLUMN IF NOT EXISTS page_content TEXT;

-- Enrichment tracking
ALTER TABLE network ADD COLUMN IF NOT EXISTS enrichment_status TEXT DEFAULT 'raw';
ALTER TABLE network ADD COLUMN IF NOT EXISTS enrichment_source TEXT;
ALTER TABLE network ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMPTZ;

-- Aliases for alternative names, nicknames, transliterations
ALTER TABLE network ADD COLUMN IF NOT EXISTS aliases TEXT[];

-- Source tracking
ALTER TABLE network ADD COLUMN IF NOT EXISTS datum_source TEXT;
ALTER TABLE network ADD COLUMN IF NOT EXISTS datum_created_at TIMESTAMPTZ;


-- =============================================================================
-- PART 3: ALTER TABLE companies — Enrichment + Dedup columns
-- =============================================================================
-- Companies already has embedding from IRGI Phase A. Adding enrichment
-- tracking, domain dedup key, and aliases.

-- Enrichment tracking
ALTER TABLE companies ADD COLUMN IF NOT EXISTS enrichment_status TEXT DEFAULT 'raw';
COMMENT ON COLUMN companies.enrichment_status IS 'Datum Agent enrichment status: raw | partial | enriched | verified.';

ALTER TABLE companies ADD COLUMN IF NOT EXISTS enrichment_source TEXT;
COMMENT ON COLUMN companies.enrichment_source IS 'Who last enriched this record.';

ALTER TABLE companies ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMPTZ;
COMMENT ON COLUMN companies.last_enriched_at IS 'When this record was last enriched.';

-- Dedup support: Domain as strongest durable key for companies
-- Using unique partial index to allow multiple NULLs
ALTER TABLE companies ADD COLUMN IF NOT EXISTS domain TEXT;
COMMENT ON COLUMN companies.domain IS 'Primary website domain (e.g., composio.dev). Strongest durable key for company dedup.';

CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_domain_unique
  ON companies(domain) WHERE domain IS NOT NULL;

-- Aliases for company name variations
ALTER TABLE companies ADD COLUMN IF NOT EXISTS aliases TEXT[];
COMMENT ON COLUMN companies.aliases IS 'Alternative company names and prior names (e.g., Z47 fka Matrix Partners India).';

-- Source tracking
ALTER TABLE companies ADD COLUMN IF NOT EXISTS datum_source TEXT;
COMMENT ON COLUMN companies.datum_source IS 'Where the Datum Agent first received this entity signal.';

ALTER TABLE companies ADD COLUMN IF NOT EXISTS datum_created_at TIMESTAMPTZ;
COMMENT ON COLUMN companies.datum_created_at IS 'When the Datum Agent first created/touched this record.';


-- =============================================================================
-- PART 4: Network Embedding Infrastructure
-- =============================================================================
-- Network already had embedding vector(1024) and fts tsvector from a prior
-- migration, plus an old trigger (embed_network_insert using queue_network_embedding).
-- This part replaces with the IRGI-pattern triggers for consistency.
--
-- EXECUTED: 2026-03-20 via Supabase MCP (verified: 3 triggers present)

-- 4a. HNSW index for vector similarity search on network
CREATE INDEX IF NOT EXISTS idx_network_embedding
  ON network
  USING hnsw (embedding vector_cosine_ops);

-- 4b. Content input function for network embedding
-- Uses ACTUAL column names: person_name, role_title, home_base (TEXT[])
-- Updated 2026-03-20: Added page_content, linkedin, ids_notes for richer embeddings
CREATE OR REPLACE FUNCTION embedding_input_network(rec network)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
  RETURN
    coalesce(rec.person_name, '') || ' | ' ||
    coalesce(rec.role_title, '') || ' | ' ||
    coalesce(array_to_string(rec.home_base, ', '), '') || ' | ' ||
    coalesce(rec.linkedin, '') || ' | ' ||
    coalesce(rec.ids_notes, '') ||
    CASE WHEN rec.page_content IS NOT NULL THEN E'\n' || left(rec.page_content, 2000) ELSE '' END;
END;
$$;

-- 4c. Replace old trigger, create IRGI-pattern triggers
-- Old trigger: embed_network_insert -> queue_network_embedding()
-- New triggers: embed_network_on_insert/update -> util.queue_embeddings()
DROP TRIGGER IF EXISTS embed_network_insert ON network;

CREATE OR REPLACE TRIGGER embed_network_on_insert
  AFTER INSERT ON network
  FOR EACH ROW
  EXECUTE FUNCTION util.queue_embeddings('embedding_input_network', 'embedding');

CREATE OR REPLACE TRIGGER embed_network_on_update
  AFTER UPDATE OF "person_name", "role_title", "home_base", "page_content" ON network
  FOR EACH ROW
  EXECUTE FUNCTION util.queue_embeddings('embedding_input_network', 'embedding');

CREATE OR REPLACE TRIGGER clear_network_embedding_on_update
  BEFORE UPDATE OF "person_name", "role_title", "home_base", "page_content" ON network
  FOR EACH ROW
  EXECUTE FUNCTION util.clear_column('embedding');

-- NOTE: FTS column (fts tsvector) and GIN index (idx_network_fts) already exist
-- from a prior migration. No action needed.


-- =============================================================================
-- VERIFICATION QUERIES (all verified 2026-03-20 via Supabase MCP)
-- =============================================================================
-- datum_requests: 0 rows, all columns present
-- network: page_content, enrichment_status, enrichment_source, last_enriched_at,
--          linkedin (pre-existing), aliases, datum_source, datum_created_at,
--          embedding (pre-existing) — all present
--          page_content loaded from network-pages/ files: 48 rows with meaningful content
-- companies: enrichment_status, enrichment_source, last_enriched_at, domain (pre-existing),
--            aliases, datum_source, datum_created_at — all present
-- network triggers: embed_network_on_insert, embed_network_on_update (watches page_content),
--                   clear_network_embedding_on_update (watches page_content) — all present
-- network HNSW index: idx_network_embedding — present
-- embedding_input_network: includes page_content (LEFT 2000 chars), linkedin, ids_notes
