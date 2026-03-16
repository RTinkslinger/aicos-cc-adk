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

Preference store. Records scoring factor snapshots for every proposed action. Used for model calibration.

```sql
CREATE TABLE action_outcomes (
    id SERIAL PRIMARY KEY,
    action_id INTEGER REFERENCES actions_queue(id),
    action_type TEXT,
    outcome TEXT,
        -- Unknown, Helpful, Gold
    bucket_impact REAL,
    conviction_change REAL,
    time_sensitivity REAL,
    action_novelty REAL,
    effort_vs_impact REAL,
    total_score REAL,
    notion_synced BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Written by:** Content Agent (when proposing actions)
**Read by:** Content Agent (for calibration)

### Common queries

```bash
# Gold-rated actions with scoring factors
psql $DATABASE_URL -c "SELECT action_type, outcome, bucket_impact, conviction_change, time_sensitivity, action_novelty, effort_vs_impact, total_score FROM action_outcomes WHERE outcome IN ('Helpful', 'Gold') ORDER BY created_at DESC LIMIT 20;"

# Average scores by outcome
psql $DATABASE_URL -c "SELECT outcome, AVG(total_score), COUNT(*) FROM action_outcomes GROUP BY outcome;"

# Scoring factor distribution for Gold actions
psql $DATABASE_URL -c "SELECT AVG(bucket_impact) as avg_bucket, AVG(conviction_change) as avg_conviction, AVG(time_sensitivity) as avg_time, AVG(action_novelty) as avg_novelty, AVG(effort_vs_impact) as avg_effort FROM action_outcomes WHERE outcome = 'Gold';"
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

## Table 6: sync_metadata (NEW)

Tracks sync cycle metadata. One row per sync cycle.

```sql
CREATE TABLE sync_metadata (
    id SERIAL PRIMARY KEY,
    sync_type TEXT NOT NULL,
        -- 'full', 'incremental', 'thesis_only', 'actions_only'
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    rows_pushed INTEGER DEFAULT 0,
        -- Rows pushed Postgres -> Notion
    rows_pulled INTEGER DEFAULT 0,
        -- Rows pulled Notion -> Postgres
    changes_detected INTEGER DEFAULT 0,
    actions_generated INTEGER DEFAULT 0,
    errors TEXT[],
        -- Array of error messages (if any)
    status TEXT DEFAULT 'running'
        -- running, completed, failed
);
```

**Written by:** Sync Agent
**Read by:** Any agent (diagnostics)

### Common queries

```bash
# Last sync status
psql $DATABASE_URL -c "SELECT * FROM sync_metadata ORDER BY started_at DESC LIMIT 1;"

# Failed syncs
psql $DATABASE_URL -c "SELECT * FROM sync_metadata WHERE status = 'failed' ORDER BY started_at DESC LIMIT 5;"

# Sync history (last 24 hours)
psql $DATABASE_URL -c "SELECT sync_type, started_at, completed_at, rows_pushed, rows_pulled, changes_detected, status FROM sync_metadata WHERE started_at > NOW() - INTERVAL '24 hours' ORDER BY started_at DESC;"

# Record sync completion
psql $DATABASE_URL -c "UPDATE sync_metadata SET completed_at = NOW(), rows_pushed = {n}, rows_pulled = {m}, changes_detected = {c}, actions_generated = {a}, status = 'completed' WHERE id = {sync_id};"
```

---

## Table 7: cai_inbox (NEW)

Inbox for messages from Claude.ai (CAI) to agents. CAI writes via State MCP `post_message` tool. Content Agent reads and processes.

```sql
CREATE TABLE cai_inbox (
    id SERIAL PRIMARY KEY,
    message_type TEXT NOT NULL,
        -- track_source, research_request, thesis_update,
        -- watch_list_add, watch_list_remove, general
    content TEXT NOT NULL,
        -- The message text
    metadata JSONB DEFAULT '{}',
        -- Structured metadata (varies by type)
    priority TEXT DEFAULT 'normal',
        -- urgent, normal, low
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    error TEXT,
        -- Error message if processing failed
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Written by:** CAI (via State MCP `post_message` tool)
**Read by:** Content Agent

### Common queries

```bash
# Unprocessed messages (priority-ordered)
psql $DATABASE_URL -c "SELECT id, message_type, content, priority, created_at FROM cai_inbox WHERE NOT processed ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'normal' THEN 2 WHEN 'low' THEN 3 END, created_at ASC;"

# Mark as processed
psql $DATABASE_URL -c "UPDATE cai_inbox SET processed = TRUE, processed_at = NOW() WHERE id = {id};"

# Failed messages (retry_count >= 3)
psql $DATABASE_URL -c "SELECT * FROM cai_inbox WHERE NOT processed AND retry_count >= 3;"

# Increment retry count
psql $DATABASE_URL -c "UPDATE cai_inbox SET retry_count = retry_count + 1 WHERE id = {id};"
```

---

## Table 8: notifications (NEW)

Outbound notifications from agents to CAI. Agents write, CAI reads via State MCP `get_state` tool.

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    notification_type TEXT NOT NULL,
        -- thesis_milestone, sync_event, content_processed,
        -- inbox_processed, error, research_complete
    title TEXT NOT NULL,
        -- Short summary for display
    body TEXT,
        -- Detailed notification content
    source_agent TEXT NOT NULL,
        -- ContentAgent, SyncAgent
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Written by:** Content Agent, Sync Agent
**Read by:** CAI (via State MCP `get_state` tool)

### Common queries

```bash
# Unread notifications
psql $DATABASE_URL -c "SELECT id, notification_type, title, source_agent, created_at FROM notifications WHERE NOT read ORDER BY created_at DESC;"

# Mark as read
psql $DATABASE_URL -c "UPDATE notifications SET read = TRUE, read_at = NOW() WHERE id = {id};"

# Write a notification
psql $DATABASE_URL -c "INSERT INTO notifications (notification_type, title, body, source_agent) VALUES ('content_processed', 'Analyzed 3 new videos', 'Found 2 thesis-relevant items. 1 action proposed (P1).', 'ContentAgent');"

# Recent notifications by type
psql $DATABASE_URL -c "SELECT notification_type, COUNT(*), MAX(created_at) as latest FROM notifications GROUP BY notification_type ORDER BY latest DESC;"
```

---

## Schema Migration Reference

For creating the NEW tables (6, 7, 8) and adding `notion_synced` columns to existing tables:

```sql
-- Table 6: sync_metadata
CREATE TABLE IF NOT EXISTS sync_metadata (
    id SERIAL PRIMARY KEY,
    sync_type TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    rows_pushed INTEGER DEFAULT 0,
    rows_pulled INTEGER DEFAULT 0,
    changes_detected INTEGER DEFAULT 0,
    actions_generated INTEGER DEFAULT 0,
    errors TEXT[],
    status TEXT DEFAULT 'running'
);

-- Table 7: cai_inbox
CREATE TABLE IF NOT EXISTS cai_inbox (
    id SERIAL PRIMARY KEY,
    message_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    priority TEXT DEFAULT 'normal',
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table 8: notifications
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    source_agent TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add notion_synced to existing tables (if not already present)
ALTER TABLE thesis_threads ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT FALSE;
ALTER TABLE thesis_threads ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP;
ALTER TABLE actions_queue ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT FALSE;
ALTER TABLE actions_queue ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP;
ALTER TABLE content_digests ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT FALSE;
ALTER TABLE content_digests ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP;
ALTER TABLE action_outcomes ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT FALSE;
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
