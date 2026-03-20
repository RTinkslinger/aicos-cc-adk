-- Cindy Communications Agent — Database Migrations
-- Created: 2026-03-20
-- Purpose: Tables for interaction tracking, context gaps, and people-interaction linking
--
-- Run order: This migration is self-contained. No dependencies on other Cindy code.
-- Depends on: network table (existing), companies table (existing)

BEGIN;

-- ============================================================================
-- 1. INTERACTIONS TABLE
-- Canonical record for every observed interaction across all four surfaces.
-- ============================================================================

CREATE TABLE IF NOT EXISTS interactions (
    id SERIAL PRIMARY KEY,

    -- Source identification
    source TEXT NOT NULL,
        -- 'email' | 'whatsapp' | 'granola' | 'calendar'
    source_id TEXT NOT NULL,
        -- Unique ID from the source system (email message_id, whatsapp chat_id+timestamp,
        -- granola meeting_id, calendar event_id)
    thread_id TEXT,
        -- Groups related interactions (email thread, whatsapp conversation, calendar recurrence)

    -- Participants
    participants TEXT[] NOT NULL,
        -- Raw participant identifiers as received (email addresses, phone numbers, names)
    linked_people INTEGER[],
        -- FK references to network.id (resolved by Cindy's people resolution)
    linked_companies INTEGER[],
        -- FK references to companies.id (when company is identified in interaction)

    -- Content
    summary TEXT,
        -- Agent-generated summary of the interaction (NOT raw content for WhatsApp)
    raw_data JSONB,
        -- Full structured data from the source (email body, granola transcript, calendar details)
        -- For WhatsApp: metadata only, NOT raw message text

    -- Timing
    timestamp TIMESTAMPTZ NOT NULL,
        -- When the interaction occurred (email sent_at, meeting start_time, message timestamp)
    duration_minutes INTEGER,
        -- For meetings: duration. For email threads: NULL. For WhatsApp: NULL.

    -- Extracted intelligence
    action_items TEXT[],
        -- Extracted action items (also written to actions_queue)
    thesis_signals JSONB,
        -- Array of {thesis_thread, signal, strength, direction}
    relationship_signals JSONB,
        -- {warmth, engagement, key_topics, follow_up_needed}
    deal_signals JSONB,
        -- {company, stage, terms_mentioned, next_steps}

    -- Context assembly (for calendar events)
    context_assembly JSONB,
        -- Pre-meeting brief: attendee context, open actions, thesis connections
    context_gap_id INTEGER,
        -- FK to context_gaps.id if this interaction fills a gap

    -- Metadata
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Dedup constraint
    UNIQUE(source, source_id)
);

-- Index: recent interactions by source
CREATE INDEX IF NOT EXISTS idx_interactions_source_time
    ON interactions(source, timestamp DESC);

-- Index: interactions by person (for people activity view)
CREATE INDEX IF NOT EXISTS idx_interactions_people
    ON interactions USING gin(linked_people);

-- Index: interactions by time (for gap detection)
CREATE INDEX IF NOT EXISTS idx_interactions_timestamp
    ON interactions(timestamp DESC);

-- Index: interactions by thread (for thread grouping)
CREATE INDEX IF NOT EXISTS idx_interactions_thread
    ON interactions(thread_id) WHERE thread_id IS NOT NULL;

-- Index: full-text search on summary
CREATE INDEX IF NOT EXISTS idx_interactions_summary_fts
    ON interactions USING gin(to_tsvector('english', summary));

-- Index: interactions by company (for company activity view)
CREATE INDEX IF NOT EXISTS idx_interactions_companies
    ON interactions USING gin(linked_companies);


-- ============================================================================
-- 2. CONTEXT_GAPS TABLE
-- Meetings where Cindy lacks observational coverage.
-- ============================================================================

CREATE TABLE IF NOT EXISTS context_gaps (
    id SERIAL PRIMARY KEY,

    -- Calendar event reference
    calendar_event_id TEXT NOT NULL,
        -- Source ID from the calendar surface
    calendar_interaction_id INTEGER,
        -- FK to interactions.id for the calendar record

    -- Meeting details (denormalized for quick access on WebFront)
    meeting_title TEXT NOT NULL,
    meeting_date TIMESTAMPTZ NOT NULL,
    attendees TEXT[] NOT NULL,
        -- Participant names/emails

    -- Gap analysis
    missing_sources TEXT[] NOT NULL,
        -- Which surfaces have no data: ['granola', 'email', 'whatsapp']
    available_sources TEXT[],
        -- Which surfaces DO have data
    context_richness REAL,
        -- 0.0 to 1.0 weighted context score

    -- Resolution
    status TEXT NOT NULL DEFAULT 'pending',
        -- 'pending' | 'partial' | 'filled' | 'skipped' | 'auto_skip' | 'post_meeting_gap'
    user_input JSONB,
        -- Structured notes from Aakash when filling manually:
        -- { notes: "...", key_takeaways: [...], action_items: [...], people_mentioned: [...] }
    filled_by TEXT,
        -- 'automatic' (retroactive source arrival) | 'webfront' | 'cai' | NULL
    filled_sources TEXT[],
        -- Which source(s) resolved the gap

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    filled_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Dedup
    UNIQUE(calendar_event_id)
);

-- Index: pending gaps for WebFront display
CREATE INDEX IF NOT EXISTS idx_context_gaps_pending
    ON context_gaps(status, meeting_date DESC)
    WHERE status IN ('pending', 'partial', 'post_meeting_gap');

-- Index: gaps by date (for gap detection queries)
CREATE INDEX IF NOT EXISTS idx_context_gaps_date
    ON context_gaps(meeting_date DESC);


-- ============================================================================
-- 3. PEOPLE_INTERACTIONS TABLE
-- Per-person interaction index linking people to their interactions across all surfaces.
-- ============================================================================

CREATE TABLE IF NOT EXISTS people_interactions (
    id SERIAL PRIMARY KEY,

    -- Links
    person_id INTEGER NOT NULL,
        -- FK to network.id
    interaction_id INTEGER NOT NULL,
        -- FK to interactions.id

    -- Context
    role TEXT NOT NULL DEFAULT 'participant',
        -- 'organizer' | 'sender' | 'recipient' | 'cc' | 'participant' | 'mentioned'
    surface TEXT NOT NULL,
        -- 'email' | 'whatsapp' | 'granola' | 'calendar'
    identifier_used TEXT,
        -- Which identifier matched: 'email:rahul@composio.dev' | 'phone:+91XXXXXXXXXX' | 'name:Rahul Sharma'
    link_confidence REAL NOT NULL DEFAULT 1.0,
        -- 0.0-1.0: how confident is the person match

    -- Timestamps
    linked_at TIMESTAMPTZ DEFAULT NOW(),

    -- Dedup: one link per person per interaction
    UNIQUE(person_id, interaction_id)
);

-- Index: all interactions for a person (People Activity view)
CREATE INDEX IF NOT EXISTS idx_pi_person
    ON people_interactions(person_id, linked_at DESC);

-- Index: all people in an interaction
CREATE INDEX IF NOT EXISTS idx_pi_interaction
    ON people_interactions(interaction_id);

-- Index: interactions by surface per person
CREATE INDEX IF NOT EXISTS idx_pi_person_surface
    ON people_interactions(person_id, surface);


-- ============================================================================
-- 4. ALTER TABLE: network (interaction tracking columns for Cindy)
-- ============================================================================

-- Last interaction tracking (computed by Cindy)
ALTER TABLE network ADD COLUMN IF NOT EXISTS last_interaction_at TIMESTAMPTZ;
    -- When was the most recent interaction with this person (any surface)

ALTER TABLE network ADD COLUMN IF NOT EXISTS last_interaction_surface TEXT;
    -- Which surface: 'email' | 'whatsapp' | 'granola' | 'calendar'

ALTER TABLE network ADD COLUMN IF NOT EXISTS interaction_count_30d INTEGER DEFAULT 0;
    -- Rolling count of interactions in the last 30 days

ALTER TABLE network ADD COLUMN IF NOT EXISTS interaction_surfaces TEXT[];
    -- Which surfaces this person has appeared on: ['email', 'whatsapp', 'granola']


-- ============================================================================
-- 5. AUTO EMBEDDINGS — interactions table
-- Semantic search over interaction summaries.
-- ============================================================================

ALTER TABLE interactions ADD COLUMN IF NOT EXISTS embedding vector(1024);
ALTER TABLE interactions ADD COLUMN IF NOT EXISTS embedding_input TEXT;
    -- Format: "{summary} | {participants} | {source}"

-- Vector similarity search index
CREATE INDEX IF NOT EXISTS idx_interactions_embedding
    ON interactions USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);


-- ============================================================================
-- 6. RLS POLICY + PUBLIC VIEW (for WebFront via PostgREST)
-- ============================================================================

-- Public view hides raw_data column from PostgREST responses
CREATE OR REPLACE VIEW interactions_public AS
    SELECT id, source, source_id, thread_id, participants, linked_people,
           linked_companies, summary, timestamp, duration_minutes,
           action_items, thesis_signals, relationship_signals, deal_signals,
           context_assembly, context_gap_id, processed_at, created_at
    FROM interactions;


-- ============================================================================
-- 7. HELPER FUNCTIONS
-- ============================================================================

-- Function: update network.last_interaction_at after inserting a people_interaction
CREATE OR REPLACE FUNCTION update_network_last_interaction()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE network SET
        last_interaction_at = GREATEST(last_interaction_at, NEW.linked_at),
        last_interaction_surface = CASE
            WHEN last_interaction_at IS NULL OR NEW.linked_at > last_interaction_at
            THEN NEW.surface
            ELSE last_interaction_surface
        END,
        interaction_surfaces = ARRAY(
            SELECT DISTINCT unnest FROM unnest(
                COALESCE(interaction_surfaces, ARRAY[]::TEXT[]) || ARRAY[NEW.surface]
            )
        ),
        updated_at = NOW()
    WHERE id = NEW.person_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: auto-update network interaction stats on people_interactions INSERT
DROP TRIGGER IF EXISTS trg_update_network_interaction ON people_interactions;
CREATE TRIGGER trg_update_network_interaction
    AFTER INSERT ON people_interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_network_last_interaction();


-- Function: auto-update interactions.updated_at on UPDATE
CREATE OR REPLACE FUNCTION update_interactions_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_interactions_updated ON interactions;
CREATE TRIGGER trg_interactions_updated
    BEFORE UPDATE ON interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_interactions_timestamp();


-- Function: auto-update context_gaps.updated_at on UPDATE
CREATE OR REPLACE FUNCTION update_context_gaps_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_context_gaps_updated ON context_gaps;
CREATE TRIGGER trg_context_gaps_updated
    BEFORE UPDATE ON context_gaps
    FOR EACH ROW
    EXECUTE FUNCTION update_context_gaps_timestamp();


-- Function: auto-populate embedding_input on interactions INSERT/UPDATE
CREATE OR REPLACE FUNCTION populate_interactions_embedding_input()
RETURNS TRIGGER AS $$
BEGIN
    NEW.embedding_input = COALESCE(NEW.summary, '') || ' | ' ||
                          COALESCE(array_to_string(NEW.participants, ', '), '') || ' | ' ||
                          COALESCE(NEW.source, '');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_interactions_embedding_input ON interactions;
CREATE TRIGGER trg_interactions_embedding_input
    BEFORE INSERT OR UPDATE OF summary, participants, source ON interactions
    FOR EACH ROW
    EXECUTE FUNCTION populate_interactions_embedding_input();


COMMIT;

-- ============================================================================
-- Post-migration notes:
-- 1. Configure Supabase Auto Embeddings for the interactions table:
--    - Source column: embedding_input
--    - Destination column: embedding
--    - Model: voyage-3-large (1024 dimensions)
--    - Trigger on: INSERT and UPDATE of embedding_input
-- 2. The IVFFlat index (idx_interactions_embedding) may need rebuilding
--    after initial data load with: REINDEX INDEX idx_interactions_embedding;
-- ============================================================================
