# Postgres Schema Skill

Complete database schema reference for all 8 tables. Used by Content Agent, Sync Agent, and any agent that reads or writes Postgres.

---

## Connection

All agents connect via the `DATABASE_URL` environment variable:

```bash
psql $DATABASE_URL -c "SELECT 1;"
```

Standard psql command pattern:
```bash
psql $DATABASE_URL -c "SQL STATEMENT HERE;"
```

For multi-line queries:
```bash
psql $DATABASE_URL <<'SQL'
SELECT ...
FROM ...
WHERE ...;
SQL
```

---

## Write Convention (MANDATORY)

All new rows and updates to synced tables MUST set `notion_synced = FALSE`:

```bash
# INSERT
psql $DATABASE_URL -c "INSERT INTO thesis_threads (..., notion_synced) VALUES (..., FALSE);"

# UPDATE
psql $DATABASE_URL -c "UPDATE actions_queue SET reasoning = '...', notion_synced = FALSE WHERE id = 123;"
```

The Sync Agent picks up rows where `notion_synced = FALSE`, pushes them to Notion, then sets `notion_synced = TRUE`.

**The database IS the queue.** There is no separate sync_queue table.

---

## Table 1: thesis_threads

Stores investment thesis hypotheses. AI-managed conviction engine.

```sql
CREATE TABLE thesis_threads (
    id SERIAL PRIMARY KEY,
    thread_name TEXT NOT NULL UNIQUE,
    conviction TEXT NOT NULL DEFAULT 'New',
        -- Values: New, Evolving, Evolving Fast, Low, Medium, High
    status TEXT NOT NULL DEFAULT 'Exploring',
        -- Values: Active, Exploring, Parked, Archived
        -- Human-owned: Notion always wins on sync
    core_thesis TEXT,
        -- The durable value insight
    key_questions TEXT,
        -- Summary: "3 open, 1 answered"
        -- Actual questions live as page content blocks in Notion
    evidence_for TEXT DEFAULT '',
        -- Append-only. IDS notation with timestamps.
        -- Format: [YYYY-MM-DD] ++ Signal text. Source: agent/slug
    evidence_against TEXT DEFAULT '',
        -- Append-only. Same format as evidence_for.
    key_companies TEXT,
    key_people TEXT,
    connected_buckets TEXT[],
        -- Array: {'New Cap Tables', 'Thesis Evolution', ...}
    investment_implications TEXT,
    discovery_source TEXT,
        -- ContentAgent, Claude.ai, Meeting, Research, X/LinkedIn, Other
    date_discovered DATE,
    notion_page_id TEXT UNIQUE,
        -- Links to Notion page. NULL = not yet synced to Notion.
    notion_synced BOOLEAN DEFAULT FALSE,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Written by:** Content Agent, CAI (via State MCP)
**Read by:** Content Agent, Sync Agent, CAI (via State MCP)

### Common queries

```bash
# All active/exploring threads
psql $DATABASE_URL -c "SELECT id, thread_name, conviction, status FROM thesis_threads WHERE status IN ('Active', 'Exploring') ORDER BY status, thread_name;"

# Unsynced threads (need Notion push)
psql $DATABASE_URL -c "SELECT id, thread_name FROM thesis_threads WHERE notion_synced = FALSE;"

# Thread by name
psql $DATABASE_URL -c "SELECT * FROM thesis_threads WHERE thread_name = 'Agentic AI Infrastructure';"

# Threads with recent evidence updates
psql $DATABASE_URL -c "SELECT thread_name, updated_at FROM thesis_threads WHERE updated_at > NOW() - INTERVAL '7 days' ORDER BY updated_at DESC;"
```

---

## Table 2: actions_queue

Central action sink for all proposed actions from all sources.

```sql
CREATE TABLE actions_queue (
    id SERIAL PRIMARY KEY,
    action TEXT NOT NULL,
        -- Concise action description
    action_type TEXT,
        -- Research, Meeting/Outreach, Thesis Update, Content Follow-up,
        -- Portfolio Check-in, Follow-on Eval, Pipeline Action
    priority TEXT,
        -- P0 - Act Now, P1 - This Week, P2 - This Month, P3 - Backlog
        -- Previously: P1 - Next, P2 - Later (v1 format)
    status TEXT DEFAULT 'Proposed',
        -- Proposed, Accepted, In Progress, Done, Dismissed
        -- Human-owned for Accepted/Dismissed transitions
    source TEXT,
        -- Content Processing, SyncAgent, Agent, Manual, Meeting, Thesis Research
    created_by TEXT DEFAULT 'AI CoS',
    assigned_to TEXT DEFAULT 'Aakash',
        -- Aakash, Agent, Sneha, Team
    reasoning TEXT,
        -- Why this action matters
    relevance_score INTEGER,
        -- 0-100 from scoring model
    thesis_connection TEXT,
        -- Pipe-delimited thesis thread names
    source_content TEXT,
        -- Context from the source that spawned this action
    outcome TEXT,
        -- Unknown, Helpful, Gold
        -- Human-owned: Notion always wins on sync
    notion_page_id TEXT UNIQUE,
    notion_synced BOOLEAN DEFAULT FALSE,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Written by:** Content Agent, Sync Agent (auto-generated actions)
**Read by:** Sync Agent, Content Agent, CAI (via State MCP)

### Common queries

```bash
# Proposed actions by priority
psql $DATABASE_URL -c "SELECT id, action, priority, relevance_score FROM actions_queue WHERE status = 'Proposed' ORDER BY CASE priority WHEN 'P0 - Act Now' THEN 1 WHEN 'P1 - This Week' THEN 2 WHEN 'P2 - This Month' THEN 3 WHEN 'P3 - Backlog' THEN 4 END;"

# Unsynced actions
psql $DATABASE_URL -c "SELECT id, action FROM actions_queue WHERE notion_synced = FALSE;"

# Actions connected to a thesis
psql $DATABASE_URL -c "SELECT id, action, priority FROM actions_queue WHERE thesis_connection LIKE '%Agentic AI%';"

# Recent Gold-rated actions (for calibration)
psql $DATABASE_URL -c "SELECT action, action_type, relevance_score FROM actions_queue WHERE outcome = 'Gold' ORDER BY updated_at DESC LIMIT 10;"
```

---

## Table 3: content_digests

Stores analyzed content with full digest metadata.

```sql
CREATE TABLE content_digests (
    id SERIAL PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    channel TEXT,
    url TEXT,
    content_type TEXT,
        -- Podcast, Interview, Talk, Tutorial, Panel, Article
    duration TEXT,
    upload_date DATE,
    relevance_score TEXT,
        -- High, Medium, Low
    net_newness TEXT,
        -- Mostly New, Additive, Reinforcing, Contra, Mixed
    connected_buckets TEXT[],
    digest_data JSONB,
        -- Full DigestData JSON blob (complete analysis)
    digest_url TEXT,
        -- https://digest.wiki/d/{slug}
    processing_date TIMESTAMP DEFAULT NOW(),
    notion_page_id TEXT UNIQUE,
    notion_synced BOOLEAN DEFAULT FALSE,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Written by:** Content Agent
**Read by:** Sync Agent, Content Agent

### Common queries

```bash
# Recent digests
psql $DATABASE_URL -c "SELECT slug, title, relevance_score, processing_date FROM content_digests ORDER BY processing_date DESC LIMIT 10;"

# Unsynced digests
psql $DATABASE_URL -c "SELECT slug, title FROM content_digests WHERE notion_synced = FALSE;"

# High-relevance digests
psql $DATABASE_URL -c "SELECT slug, title, net_newness FROM content_digests WHERE relevance_score = 'High' ORDER BY processing_date DESC;"
```

---

## Table 4: action_outcomes

Records action outcomes with scoring metadata. Used for model calibration and preference tracking.

```sql
CREATE TABLE action_outcomes (
    id SERIAL PRIMARY KEY,
    action_text TEXT,
    action_type TEXT,
    outcome TEXT,
    score REAL,
    scoring_factors JSONB,
    source_digest_slug TEXT,
    company TEXT,
    thesis_thread TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    notion_synced BOOLEAN DEFAULT FALSE
);
```

**Written by:** Content Agent (when proposing actions)
**Read by:** Content Agent (for calibration)

### Common queries

```bash
# Actions with outcomes and scores
psql $DATABASE_URL -c "SELECT action_type, outcome, score, company, thesis_thread FROM action_outcomes WHERE outcome IN ('Helpful', 'Gold') ORDER BY created_at DESC LIMIT 20;"

# Average scores by outcome
psql $DATABASE_URL -c "SELECT outcome, AVG(score), COUNT(*) FROM action_outcomes GROUP BY outcome;"

# Actions by thesis thread
psql $DATABASE_URL -c "SELECT action_text, outcome, score, scoring_factors FROM action_outcomes WHERE thesis_thread = 'Agentic AI Infrastructure' ORDER BY created_at DESC;"

# Unsynced action outcomes
psql $DATABASE_URL -c "SELECT id, action_text FROM action_outcomes WHERE notion_synced = FALSE;"
```

---

## Table 5: change_events

Audit trail for Notion-Postgres sync changes. Tracks what changed, when, and whether it's been processed for action generation.

```sql
CREATE TABLE change_events (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
        -- 'thesis_threads' or 'actions_queue'
    record_id INTEGER NOT NULL,
        -- Postgres row ID in the source table
    notion_page_id TEXT,
    field_name TEXT NOT NULL,
        -- Which field changed (e.g., 'status', 'conviction', 'outcome')
    old_value TEXT,
    new_value TEXT,
    detected_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
        -- FALSE = not yet processed for action generation
);
```

**Written by:** Sync Agent (during change detection)
**Read by:** Sync Agent (for action generation)

### Common queries

```bash
# Unprocessed changes
psql $DATABASE_URL -c "SELECT * FROM change_events WHERE NOT processed ORDER BY detected_at ASC LIMIT 50;"

# Recent changes
psql $DATABASE_URL -c "SELECT table_name, field_name, old_value, new_value, detected_at FROM change_events ORDER BY detected_at DESC LIMIT 10;"

# Mark as processed
psql $DATABASE_URL -c "UPDATE change_events SET processed = TRUE WHERE id IN (1, 2, 3);"
```

---

## Table 6: sync_metadata

Tracks per-table sync state. One row per table (UNIQUE on table_name).

```sql
CREATE TABLE sync_metadata (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) UNIQUE,
    last_sync_at TIMESTAMPTZ,
    sync_status VARCHAR(50) DEFAULT 'never',
        -- 'never', 'syncing', 'completed', 'failed'
    rows_synced INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

**Written by:** Sync Agent
**Read by:** Any agent (diagnostics)

### Common queries

```bash
# All table sync statuses
psql $DATABASE_URL -c "SELECT table_name, sync_status, last_sync_at, rows_synced, updated_at FROM sync_metadata ORDER BY table_name;"

# Tables that have never synced
psql $DATABASE_URL -c "SELECT table_name FROM sync_metadata WHERE sync_status = 'never';"

# Update sync status for a table
psql $DATABASE_URL -c "INSERT INTO sync_metadata (table_name, last_sync_at, sync_status, rows_synced, updated_at) VALUES ('thesis_threads', NOW(), 'completed', {n}, NOW()) ON CONFLICT (table_name) DO UPDATE SET last_sync_at = NOW(), sync_status = 'completed', rows_synced = {n}, updated_at = NOW();"

# Failed syncs
psql $DATABASE_URL -c "SELECT table_name, last_sync_at, updated_at FROM sync_metadata WHERE sync_status = 'failed';"
```

---

## Table 7: cai_inbox

Inbox for messages from Claude.ai (CAI) to agents. CAI writes via State MCP `post_message` tool. Content Agent reads and processes.

```sql
CREATE TABLE cai_inbox (
    id SERIAL PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
        -- track_source, research_request, thesis_update,
        -- watch_list_add, watch_list_remove, general
    content TEXT NOT NULL,
        -- The message text
    metadata JSONB DEFAULT '{}',
        -- Structured metadata (varies by type)
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

**Written by:** CAI (via State MCP `post_message` tool)
**Read by:** Content Agent

### Common queries

```bash
# Unprocessed messages (oldest first)
psql $DATABASE_URL -c "SELECT id, type, content, metadata, created_at FROM cai_inbox WHERE NOT processed ORDER BY created_at ASC;"

# Mark as processed
psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE, processed_at = NOW() WHERE id = {id};"

# Recent messages by type
psql $DATABASE_URL -c "SELECT type, COUNT(*), MAX(created_at) as latest FROM cai_inbox GROUP BY type ORDER BY latest DESC;"
```

---

## Table 8: notifications

Outbound notifications from agents to CAI. Agents write, CAI reads via State MCP `get_state` tool.

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
        -- ContentAgent, SyncAgent
    type VARCHAR(100) NOT NULL,
        -- thesis_milestone, sync_event, content_processed,
        -- inbox_processed, error, research_complete
    content TEXT NOT NULL,
        -- Notification message content
    metadata JSONB DEFAULT '{}',
        -- Structured metadata (varies by type)
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

**Written by:** Content Agent, Sync Agent
**Read by:** CAI (via State MCP `get_state` tool)

### Common queries

```bash
# Unread notifications
psql $DATABASE_URL -c "SELECT id, source, type, content, created_at FROM notifications WHERE NOT read ORDER BY created_at DESC;"

# Mark as read
psql $DATABASE_URL -c "UPDATE notifications SET read = TRUE WHERE id = {id};"

# Write a notification
psql $DATABASE_URL -c "INSERT INTO notifications (source, type, content, metadata) VALUES ('ContentAgent', 'content_processed', 'Analyzed 3 new videos. Found 2 thesis-relevant items. 1 action proposed (P1).', '{}');"

# Recent notifications by type
psql $DATABASE_URL -c "SELECT type, COUNT(*), MAX(created_at) as latest FROM notifications GROUP BY type ORDER BY latest DESC;"
```

---

## Schema Migration Reference

For creating tables 4, 6, 7, 8 and adding `notion_synced` columns to existing tables:

```sql
-- Table 4: action_outcomes
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    notion_synced BOOLEAN DEFAULT FALSE
);

-- Table 6: sync_metadata
CREATE TABLE IF NOT EXISTS sync_metadata (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) UNIQUE,
    last_sync_at TIMESTAMPTZ,
    sync_status VARCHAR(50) DEFAULT 'never',
    rows_synced INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Table 7: cai_inbox
CREATE TABLE IF NOT EXISTS cai_inbox (
    id SERIAL PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Table 8: notifications
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Add notion_synced to existing tables (if not already present)
ALTER TABLE thesis_threads ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT FALSE;
ALTER TABLE thesis_threads ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP;
ALTER TABLE actions_queue ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT FALSE;
ALTER TABLE actions_queue ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP;
ALTER TABLE content_digests ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT FALSE;
ALTER TABLE content_digests ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP;
```

---

## Conventions Summary

| Convention | Rule |
|-----------|------|
| Connection | `psql $DATABASE_URL -c "..."` |
| New rows | Always `notion_synced = FALSE` |
| After Notion sync | Set `notion_synced = TRUE, last_synced_at = NOW()` |
| Evidence fields | Append-only, never overwrite |
| Timestamps | Use `NOW()` for Postgres-side timestamps |
| Arrays | Use `TEXT[]` with `'{value1, value2}'` syntax |
| JSONB | Use for flexible/variable-shape data (metadata, digest_data) |
| Soft deletes | No physical deletes. Use status fields (Archived, Dismissed). |
