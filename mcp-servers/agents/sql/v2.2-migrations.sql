-- v2.2 Schema Migrations
-- Run against the AI CoS Postgres database on aicos-droplet
-- Idempotent: safe to run multiple times

-- ============================================================================
-- 1. Add notion_synced column to existing tables
-- ============================================================================
-- Agents write rows with notion_synced=FALSE; SyncAgent sets TRUE after pushing to Notion.
-- Existing rows are already in Notion, so they default to TRUE.

ALTER TABLE thesis_threads ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT TRUE;
ALTER TABLE actions_queue ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT TRUE;
ALTER TABLE action_outcomes ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT TRUE;

-- ============================================================================
-- 2. sync_metadata table — tracks per-table sync state for SyncAgent
-- ============================================================================

CREATE TABLE IF NOT EXISTS sync_metadata (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) UNIQUE NOT NULL,
    last_sync_at TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'unknown',
    rows_synced INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO sync_metadata (table_name, sync_status) VALUES
    ('thesis_threads', 'unknown'),
    ('actions_queue', 'unknown'),
    ('action_outcomes', 'unknown')
ON CONFLICT (table_name) DO NOTHING;

-- ============================================================================
-- 3. cai_inbox table — cross-surface messages for Claude.ai sync
-- ============================================================================

CREATE TABLE IF NOT EXISTS cai_inbox (
    id SERIAL PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cai_inbox_unprocessed
    ON cai_inbox (processed, created_at)
    WHERE processed = FALSE;

-- ============================================================================
-- 4. notifications table — surfacing alerts to user (WhatsApp, digest, etc.)
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_unread
    ON notifications (read, created_at)
    WHERE read = FALSE;
