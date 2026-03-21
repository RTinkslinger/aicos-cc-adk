-- Migration: Cindy+Datum Refactor — interaction_staging table
-- Applied: 2026-03-20 by Cindy+Datum Refactor (L61-66)
--
-- New architecture:
--   Fetchers (Python plumbing) -> interaction_staging (raw data)
--   Datum Agent (Claude SDK) -> interactions (clean, linked data)
--   Cindy Agent (Claude SDK) -> obligations, actions, signals (LLM reasoning)
--
-- Tables created:
--   interaction_staging — raw data from fetchers, processed by Datum then Cindy
--
-- Columns added:
--   interactions.cindy_processed — Cindy's LLM reasoning completion flag
--   interactions.datum_staged_id — FK back to staging row
--
-- Deleted:
--   11 sample rows from interactions (regex-processed garbage)
--   people_interactions rows linked to those interactions

-- 1. Create interaction_staging
CREATE TABLE IF NOT EXISTS interaction_staging (
  id SERIAL PRIMARY KEY,
  source TEXT NOT NULL,                    -- 'whatsapp', 'email', 'granola', 'calendar'
  source_id TEXT NOT NULL,                 -- unique ID from source system
  raw_data JSONB NOT NULL,                 -- full raw data from fetcher
  datum_processed BOOLEAN DEFAULT FALSE,   -- Datum has resolved people + linked
  cindy_processed BOOLEAN DEFAULT FALSE,   -- Cindy has reasoned about obligations/signals
  error_message TEXT,                      -- if processing failed
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(source, source_id)
);

CREATE INDEX IF NOT EXISTS idx_staging_datum_pending ON interaction_staging (created_at) WHERE datum_processed = FALSE;
CREATE INDEX IF NOT EXISTS idx_staging_cindy_pending ON interaction_staging (created_at) WHERE datum_processed = TRUE AND cindy_processed = FALSE;
CREATE INDEX IF NOT EXISTS idx_staging_source ON interaction_staging (source);

-- 2. Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_staging_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS staging_updated_at ON interaction_staging;
CREATE TRIGGER staging_updated_at
BEFORE UPDATE ON interaction_staging
FOR EACH ROW
EXECUTE FUNCTION update_staging_updated_at();

-- 3. Add columns to interactions
ALTER TABLE interactions ADD COLUMN IF NOT EXISTS cindy_processed BOOLEAN DEFAULT FALSE;
ALTER TABLE interactions ADD COLUMN IF NOT EXISTS datum_staged_id INTEGER REFERENCES interaction_staging(id);
CREATE INDEX IF NOT EXISTS idx_interactions_cindy_pending ON interactions (created_at) WHERE cindy_processed = FALSE;

-- 4. Clean regex-processed garbage
DELETE FROM people_interactions WHERE interaction_id IN (SELECT id FROM interactions);
DELETE FROM interactions;
