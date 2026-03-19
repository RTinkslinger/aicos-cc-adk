-- AI CoS Postgres — Baseline Schema
-- Exported from live droplet: 2026-03-18
-- PostgreSQL 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)
-- Owner: aicos
--
-- This is the complete schema as it exists on the droplet.
-- Use this as the authoritative reference for Supabase migration.

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;

SET default_tablespace = '';
SET default_table_access_method = heap;

-- ============================================================================
-- TABLES
-- ============================================================================

-- 1. thesis_threads
CREATE TABLE IF NOT EXISTS thesis_threads (
    id SERIAL PRIMARY KEY,
    notion_page_id TEXT UNIQUE,
    thread_name TEXT NOT NULL,
    core_thesis TEXT NOT NULL DEFAULT '',
    conviction TEXT NOT NULL DEFAULT 'New',
    status TEXT NOT NULL DEFAULT 'Exploring',
    discovery_source TEXT NOT NULL DEFAULT 'Claude',
    connected_buckets TEXT[] DEFAULT '{}',
    evidence_for TEXT DEFAULT '',
    evidence_against TEXT DEFAULT '',
    key_question_summary TEXT DEFAULT '',
    key_questions_json JSONB DEFAULT '{"open": [], "answered": []}',
    key_companies TEXT DEFAULT '',
    investment_implications TEXT DEFAULT '',
    date_discovered DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_synced_at TIMESTAMPTZ,
    notion_synced BOOLEAN DEFAULT TRUE
);

-- 2. actions_queue
CREATE TABLE IF NOT EXISTS actions_queue (
    id SERIAL PRIMARY KEY,
    notion_page_id TEXT UNIQUE,
    action TEXT NOT NULL,
    action_type TEXT DEFAULT '',
    status TEXT DEFAULT 'Proposed',
    priority TEXT DEFAULT '',
    source TEXT DEFAULT '',
    assigned_to TEXT DEFAULT '',
    created_by TEXT DEFAULT '',
    reasoning TEXT DEFAULT '',
    source_content TEXT DEFAULT '',
    thesis_connection TEXT DEFAULT '',
    relevance_score REAL,
    outcome TEXT DEFAULT '',
    company_notion_id TEXT,
    source_digest_notion_id TEXT,
    scoring_factors JSONB DEFAULT '{}',
    triage_history JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_synced_at TIMESTAMPTZ,
    notion_last_edited TIMESTAMPTZ,
    last_local_edit TIMESTAMPTZ,
    last_notion_edit TIMESTAMPTZ,
    notion_synced BOOLEAN DEFAULT TRUE
);

-- 3. action_outcomes
CREATE TABLE IF NOT EXISTS action_outcomes (
    id SERIAL PRIMARY KEY,
    action_text TEXT,
    action_type TEXT,
    outcome TEXT,
    score REAL,
    scoring_factors JSONB,
    source_digest_slug TEXT,
    company TEXT,
    thesis_thread TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    notion_synced BOOLEAN DEFAULT TRUE
);

-- 4. content_digests
CREATE TABLE IF NOT EXISTS content_digests (
    id SERIAL PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    channel TEXT,
    url TEXT UNIQUE,
    content_type TEXT,
    duration TEXT,
    upload_date DATE,
    relevance_score TEXT,
    net_newness TEXT,
    connected_buckets TEXT[],
    digest_data JSONB,
    digest_url TEXT,
    processing_date TIMESTAMP DEFAULT now(),
    created_at TIMESTAMP DEFAULT now(),
    status VARCHAR(20) DEFAULT 'queued'
);

-- 5. companies
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    notion_page_id TEXT UNIQUE,
    name TEXT NOT NULL,
    deal_status TEXT DEFAULT '',
    deal_status_at_discovery TEXT DEFAULT '',
    pipeline_status TEXT DEFAULT '',
    type TEXT DEFAULT '',
    sector TEXT DEFAULT '',
    sector_tags TEXT[] DEFAULT '{}',
    priority TEXT DEFAULT '',
    founding_timeline TEXT DEFAULT '',
    venture_funding TEXT DEFAULT '',
    last_round_amount REAL,
    last_round_timing TEXT DEFAULT '',
    smart_money TEXT DEFAULT '',
    hil_review TEXT DEFAULT '',
    jtbd TEXT[] DEFAULT '{}',
    sells_to TEXT[] DEFAULT '{}',
    batch TEXT[] DEFAULT '{}',
    website TEXT DEFAULT '',
    deck_link TEXT DEFAULT '',
    vault_link TEXT DEFAULT '',
    agent_ids_notes TEXT DEFAULT '',
    content_connections JSONB DEFAULT '[]',
    thesis_thread_links JSONB DEFAULT '[]',
    signal_history JSONB DEFAULT '[]',
    computed_conviction_score REAL,
    enrichment_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_synced_at TIMESTAMPTZ,
    notion_last_edited TIMESTAMPTZ
);

-- 6. network
CREATE TABLE IF NOT EXISTS network (
    id SERIAL PRIMARY KEY,
    notion_page_id TEXT UNIQUE,
    person_name TEXT NOT NULL,
    current_role TEXT,
    home_base TEXT[] DEFAULT '{}',
    linkedin TEXT,
    ryg TEXT,
    e_e_priority TEXT,
    sourcing_flow_hots TEXT,
    investing_activity TEXT,
    devc_relationship TEXT[] DEFAULT '{}',
    collective_flag TEXT[] DEFAULT '{}',
    engagement_playbook TEXT[] DEFAULT '{}',
    leverage TEXT[] DEFAULT '{}',
    customer_for TEXT[] DEFAULT '{}',
    investorship TEXT[] DEFAULT '{}',
    prev_foundership TEXT[] DEFAULT '{}',
    folio_franchise TEXT[] DEFAULT '{}',
    operating_franchise TEXT[] DEFAULT '{}',
    big_events_invite TEXT[] DEFAULT '{}',
    in_folio_of TEXT[] DEFAULT '{}',
    local_network_tags TEXT[] DEFAULT '{}',
    saas_buyer_type TEXT[] DEFAULT '{}',
    current_company_ids TEXT[] DEFAULT '{}',
    past_company_ids TEXT[] DEFAULT '{}',
    agent_interaction_summaries JSONB DEFAULT '[]',
    meeting_context JSONB DEFAULT '[]',
    content_connections JSONB DEFAULT '[]',
    signal_history JSONB DEFAULT '[]',
    enrichment_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_synced_at TIMESTAMPTZ,
    notion_last_edited TIMESTAMPTZ
);

-- 7. cai_inbox
CREATE TABLE IF NOT EXISTS cai_inbox (
    id SERIAL PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. notifications
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. sync_metadata
CREATE TABLE IF NOT EXISTS sync_metadata (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) UNIQUE NOT NULL,
    last_sync_at TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'unknown',
    rows_synced INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. sync_queue
CREATE TABLE IF NOT EXISTS sync_queue (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    operation TEXT NOT NULL,
    payload JSONB NOT NULL,
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    next_retry_at TIMESTAMPTZ DEFAULT now()
);

-- 11. change_events
CREATE TABLE IF NOT EXISTS change_events (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    notion_page_id TEXT,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    detected_at TIMESTAMPTZ DEFAULT now(),
    processed BOOLEAN DEFAULT FALSE,
    action_generated_id INTEGER
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- thesis_threads
CREATE INDEX IF NOT EXISTS idx_thesis_threads_name ON thesis_threads (thread_name);
CREATE INDEX IF NOT EXISTS idx_thesis_threads_status ON thesis_threads (status);
CREATE INDEX IF NOT EXISTS idx_thesis_threads_conviction ON thesis_threads (conviction);

-- actions_queue
CREATE INDEX IF NOT EXISTS idx_actions_status ON actions_queue (status);
CREATE INDEX IF NOT EXISTS idx_actions_priority ON actions_queue (priority);
CREATE INDEX IF NOT EXISTS idx_actions_type ON actions_queue (action_type);

-- action_outcomes
CREATE INDEX IF NOT EXISTS idx_action_outcomes_type ON action_outcomes (action_type);
CREATE INDEX IF NOT EXISTS idx_action_outcomes_outcome ON action_outcomes (outcome);

-- content_digests (partial index on active statuses)
CREATE INDEX IF NOT EXISTS idx_content_digests_status ON content_digests (status)
    WHERE status IN ('queued', 'processing');

-- companies
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies (name);
CREATE INDEX IF NOT EXISTS idx_companies_deal_status ON companies (deal_status);
CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies (sector);

-- network
CREATE INDEX IF NOT EXISTS idx_network_name ON network (person_name);
CREATE INDEX IF NOT EXISTS idx_network_ryg ON network (ryg);

-- cai_inbox (partial index on unprocessed)
CREATE INDEX IF NOT EXISTS idx_cai_inbox_unprocessed ON cai_inbox (processed, created_at)
    WHERE processed = FALSE;

-- notifications (partial index on unread)
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications (read, created_at)
    WHERE read = FALSE;

-- change_events
CREATE INDEX IF NOT EXISTS idx_change_events_table ON change_events (table_name);
CREATE INDEX IF NOT EXISTS idx_change_events_unprocessed ON change_events (detected_at)
    WHERE NOT processed;

-- sync_queue (partial index on retryable)
CREATE INDEX IF NOT EXISTS idx_sync_queue_next_retry ON sync_queue (next_retry_at)
    WHERE attempts < 5;
