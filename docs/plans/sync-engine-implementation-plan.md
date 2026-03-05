# Sync Engine Implementation Plan

> Step-by-step build plan for the 4-layer sync architecture defined in `docs/architecture/DATA-SOVEREIGNTY.md`.
> Each phase is independently deployable and adds incremental value.

---

## Phase 1: Write-Ahead Log + Thesis Cache

**Goal:** Prevent data loss on Notion write failures. Eliminate live Notion dependency for thesis thread reads.

### 1a. Postgres Schema — Sync Foundation

**File:** `mcp-servers/ai-cos-mcp/migrations/001_sync_foundation.sql`

```sql
-- Write-ahead queue for failed Notion writes
CREATE TABLE sync_queue (
    id SERIAL PRIMARY KEY,
    target_db TEXT NOT NULL,          -- 'content_digest', 'actions_queue', 'thesis_tracker'
    operation TEXT NOT NULL,          -- 'create_page', 'update_page', 'append_block'
    payload JSONB NOT NULL,           -- full Notion API payload (properties, parent, etc.)
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'synced', 'failed'
    attempts INT DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    synced_at TIMESTAMPTZ,
    notion_page_id TEXT               -- populated after successful sync
);

CREATE INDEX idx_sync_queue_status ON sync_queue(status) WHERE status = 'pending';

-- Local thesis threads cache
CREATE TABLE thesis_threads_cache (
    id SERIAL PRIMARY KEY,
    notion_page_id TEXT UNIQUE NOT NULL,
    thread_name TEXT NOT NULL,
    status TEXT,                       -- Active, Exploring, Parked
    conviction TEXT,                   -- High, Medium, Low, TBD
    core_thesis TEXT,
    key_question TEXT,
    key_companies TEXT,
    connected_buckets TEXT,
    evidence_for TEXT,
    evidence_against TEXT,
    investment_implications TEXT,
    last_synced_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 1b. Write-Ahead Wrapper for Notion Writes

**File:** `mcp-servers/ai-cos-mcp/lib/sync.py` (new)

Wrap existing `notion_client.py` functions with write-ahead logic:

```
def sync_create_digest_entry(**kwargs) -> dict:
    1. Insert into sync_queue (target_db='content_digest', payload=kwargs, status='pending')
    2. Try notion_client.create_digest_entry(**kwargs)
    3. If success → update sync_queue row to status='synced', set notion_page_id
    4. If fail → leave as 'pending', log error
    5. Return local record either way (caller gets data regardless of Notion state)

def sync_create_action_entry(**kwargs) -> dict:
    Same pattern as above for actions_queue

def sync_update_thesis_tracker(**kwargs) -> dict:
    Same pattern for thesis evidence appends
```

### 1c. Thesis Tracker Read Cache

**File:** `mcp-servers/ai-cos-mcp/lib/sync.py` (continued)

```
def refresh_thesis_cache() -> list[dict]:
    1. Call notion_client.fetch_thesis_threads()
    2. Upsert each thread into thesis_threads_cache (by notion_page_id)
    3. Return the refreshed list

def get_thesis_threads() -> list[dict]:
    1. Try refresh_thesis_cache()
    2. If Notion fails → SELECT * FROM thesis_threads_cache (last known state)
    3. If cache is empty too → return [] (CONTEXT.md fallback handled by caller)
```

### 1d. Retry Worker

**File:** `mcp-servers/ai-cos-mcp/lib/sync.py` (continued)

```
def retry_pending_syncs(max_retries: int = 3) -> dict:
    1. SELECT * FROM sync_queue WHERE status = 'pending' AND attempts < max_retries
    2. For each: replay the Notion API call from payload
    3. On success → status='synced', set notion_page_id, synced_at=now()
    4. On fail → attempts += 1, last_error = str(e)
    5. If attempts >= max_retries → status='failed'
    6. Return summary: {retried: N, succeeded: N, failed: N}
```

### 1e. Integration

**Modify:** `runners/content_agent.py`
- Replace direct `create_digest_entry()`, `create_action_entry()`, `update_thesis_tracker()` calls with `sync_create_digest_entry()`, etc.
- Replace `fetch_thesis_threads()` call in `_format_thesis_threads_from_notion()` with `get_thesis_threads()`

**Modify:** `runners/pipeline.py`
- Call `retry_pending_syncs()` at pipeline start (before extraction)
- Log retry results

### 1f. Verification

- Kill Notion token temporarily → run pipeline → verify:
  - Digest still publishes to digest.wiki (unaffected)
  - sync_queue has 'pending' rows for the Notion writes
  - Thesis threads served from cache
- Restore token → next pipeline run retries pending writes → sync_queue rows become 'synced'

---

## Phase 2: Companies / Network / Portfolio Local Mirror

**Goal:** Rich portfolio data available locally for content analysis. No live Notion dependency for company matching. Change detection foundation.

### 2a. Postgres Schema — Core Data Tables

**File:** `mcp-servers/ai-cos-mcp/migrations/002_core_data_tables.sql`

```sql
-- Companies DB mirror + enrichment
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    notion_page_id TEXT UNIQUE NOT NULL,

    -- Notion-owned fields (synced from Notion, never edited locally)
    company_name TEXT NOT NULL,
    deal_status TEXT,
    stage TEXT,
    sector TEXT,
    thesis TEXT,
    spiky_score REAL,
    eo_score REAL,
    fmf_score REAL,
    thesis_score REAL,
    price_score REAL,
    team_notes TEXT,
    jtbd TEXT,
    founders_notion_ids TEXT[],      -- relation page IDs into Network DB

    -- Droplet-enriched fields (agent-managed, never overwritten by Notion sync)
    agent_ids_notes TEXT,            -- agent-generated IDS trail
    content_connections JSONB,       -- [{digest_slug, relevance, date}]
    thesis_thread_links TEXT[],      -- which thesis threads this company connects to
    signal_history JSONB,            -- [{date, signal_type, detail}]
    computed_conviction REAL,        -- agent-computed from evidence
    enrichment_metadata JSONB,       -- freeform agent data

    -- Sync metadata
    notion_last_modified TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ DEFAULT NOW(),
    last_change_detected_at TIMESTAMPTZ
);

-- Network DB mirror + enrichment
CREATE TABLE network (
    id SERIAL PRIMARY KEY,
    notion_page_id TEXT UNIQUE NOT NULL,

    -- Notion-owned fields
    person_name TEXT NOT NULL,
    archetype TEXT,
    company TEXT,
    role TEXT,
    linkedin TEXT,
    email TEXT,
    phone TEXT,
    city TEXT,
    ids_notes TEXT,
    relationship_status TEXT,
    last_interaction TIMESTAMPTZ,
    source TEXT,
    collective_status TEXT,

    -- Droplet-enriched fields
    agent_interaction_summary TEXT,
    meeting_context JSONB,
    content_connections JSONB,
    signal_history JSONB,
    enrichment_metadata JSONB,

    -- Sync metadata
    notion_last_modified TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ DEFAULT NOW(),
    last_change_detected_at TIMESTAMPTZ
);

-- Portfolio DB mirror + enrichment
CREATE TABLE portfolio (
    id SERIAL PRIMARY KEY,
    notion_page_id TEXT UNIQUE NOT NULL,
    company_notion_page_id TEXT,      -- hidden 'Company Name' relation → companies.notion_page_id

    -- Notion-owned fields
    ef_score REAL,
    eo_score REAL,
    follow_on_status TEXT,
    financial_data JSONB,             -- rollup from Finance DB

    -- Droplet-enriched fields
    agent_health_signals JSONB,       -- [{date, signal, severity}]
    content_cross_refs JSONB,         -- digest connections
    thesis_conviction_trail JSONB,    -- [{date, conviction, evidence}]
    enrichment_metadata JSONB,

    -- Sync metadata
    notion_last_modified TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ DEFAULT NOW(),
    last_change_detected_at TIMESTAMPTZ,

    FOREIGN KEY (company_notion_page_id) REFERENCES companies(notion_page_id)
);

CREATE INDEX idx_companies_name ON companies(company_name);
CREATE INDEX idx_network_name ON network(person_name);
CREATE INDEX idx_portfolio_company ON portfolio(company_notion_page_id);
```

### 2b. Notion Pull Functions

**File:** `mcp-servers/ai-cos-mcp/lib/notion_client.py` (extend)

```
def fetch_all_companies(page_size=100) -> list[dict]:
    Paginate through Companies DB (data_source_id)
    Extract Notion-owned fields from each page's properties
    Return list of dicts with notion_page_id + field values

def fetch_all_network(page_size=100) -> list[dict]:
    Same for Network DB

def fetch_all_portfolio(page_size=100) -> list[dict]:
    Same for Portfolio DB
    Extract hidden 'Company Name' relation → get linked page ID
```

### 2c. Sync Functions

**File:** `mcp-servers/ai-cos-mcp/lib/sync.py` (extend)

```
def sync_companies_from_notion() -> dict:
    1. fetch_all_companies() from Notion
    2. For each company:
       a. UPSERT into companies table (ON CONFLICT notion_page_id)
       b. Only update Notion-owned columns (never touch enriched columns)
       c. Compare old vs new values for change detection
       d. If any Notion-owned field changed → record in change_log
    3. Return {synced: N, changed: N, new: N}

def sync_network_from_notion() -> dict:
    Same pattern

def sync_portfolio_from_notion() -> dict:
    Same pattern, including Company Name relation resolution
```

### 2d. Content Agent Integration

**Modify:** `runners/content_agent.py`

Replace `portfolio-research/` filename scanning with Postgres query:
```
def _get_portfolio_companies() -> str:
    1. SELECT company_name, deal_status, sector, thesis FROM companies
       WHERE deal_status IN ('Active Pipeline', 'IC Ready', 'Portfolio', ...)
    2. Format as markdown for prompt injection
    3. Fallback: portfolio-research/ filenames if Postgres is empty
```

This gives Claude real company data — not just title-cased filenames, but names, sectors, thesis connections, and deal status. Dramatically better portfolio connections in digests.

### 2e. Initial Sync Script

**File:** `mcp-servers/ai-cos-mcp/scripts/initial_sync.py`

One-time script to populate the local tables from Notion:
```
1. Run migrations (001 + 002)
2. sync_companies_from_notion()
3. sync_network_from_notion()
4. sync_portfolio_from_notion()
5. refresh_thesis_cache()
6. Print summary
```

### 2f. Periodic Sync Schedule

Add to pipeline or separate cron:
- Companies/Network/Portfolio: sync every 6 hours (data changes slowly)
- Thesis Tracker: sync every pipeline run (5 min — already implemented)
- Content Digest Action Status: sync every hour (triage happens manually, not time-critical)

---

## Phase 3: Bidirectional Actions Queue Sync

**Goal:** Actions can be triaged from any surface (Notion, digest.wiki, WhatsApp, agent) without conflicts.

### 3a. Postgres Schema — Actions Table

**File:** `mcp-servers/ai-cos-mcp/migrations/003_actions_table.sql`

```sql
CREATE TABLE actions (
    id SERIAL PRIMARY KEY,
    notion_page_id TEXT UNIQUE,       -- NULL until synced to Notion

    -- Core fields
    action_text TEXT NOT NULL,
    priority TEXT NOT NULL,            -- P0, P1, P2, P3
    action_type TEXT,
    assigned_to TEXT DEFAULT 'Aakash',
    status TEXT NOT NULL DEFAULT 'Proposed',  -- Proposed, Accepted, In Progress, Done, Dismissed
    source TEXT,                       -- ContentAgent, Agent, Manual, Meeting
    created_by TEXT,                   -- Claude Code, Claude.ai, Manual

    -- Relations (stored as Notion page IDs for sync)
    company_notion_page_id TEXT,
    thesis_notion_page_id TEXT,
    source_digest_notion_page_id TEXT,

    -- Metadata
    relevance_score REAL,
    reasoning TEXT,
    thesis_connection_text TEXT,       -- legacy free-text
    outcome TEXT,
    due_date DATE,

    -- Scoring (from action scoring model)
    score REAL,
    classification TEXT,              -- 'surface', 'low_confidence', 'context_enrichment'
    scoring_factors JSONB,

    -- Sync metadata
    last_modified_at TIMESTAMPTZ DEFAULT NOW(),
    last_modified_by TEXT,            -- 'droplet', 'notion', 'digest_wiki', 'whatsapp'
    last_synced_at TIMESTAMPTZ,
    sync_status TEXT DEFAULT 'pending' -- 'pending', 'synced', 'conflict'
);

CREATE INDEX idx_actions_status ON actions(status);
CREATE INDEX idx_actions_sync ON actions(sync_status) WHERE sync_status = 'pending';
```

### 3b. Bidirectional Sync Logic

**File:** `mcp-servers/ai-cos-mcp/lib/sync.py` (extend)

```
def sync_actions_bidirectional() -> dict:
    1. PUSH: SELECT * FROM actions WHERE sync_status = 'pending' AND last_modified_by = 'droplet'
       - For each: create/update in Notion → set notion_page_id, sync_status='synced'
    2. PULL: Query Actions Queue in Notion (modified since last sync)
       - For each Notion page:
         a. Find matching local row by notion_page_id
         b. If local row doesn't exist → INSERT (Notion-originated action)
         c. If local row exists:
            - Compare last_modified_at (local) vs Notion's Last Updated
            - If Notion is newer → update local row, set last_modified_by='notion'
            - If local is newer → skip (will be pushed on next cycle)
            - If same timestamp → no-op
    3. Return {pushed: N, pulled: N, conflicts: N}
```

### 3c. Triage API for Non-Notion Surfaces

**File:** `mcp-servers/ai-cos-mcp/server.py` (extend MCP tool)

```
@mcp.tool()
def cos_triage_action(action_id: int, decision: str, notes: str = "") -> dict:
    """Triage a proposed action: accept, dismiss, or defer."""
    1. UPDATE actions SET status=decision, last_modified_by='droplet', last_modified_at=now()
    2. Set sync_status='pending' (will push to Notion on next sync)
    3. Log to action_outcomes for preference learning
```

This tool enables future surfaces (digest.wiki action cards, WhatsApp buttons) to triage actions without going through Notion.

---

## Phase 4: Change Detection → Action Generation

**Goal:** Notion edits become signals. When Aakash changes a company's deal status or adds a person, the AI CoS detects it and can reason about it.

### 4a. Change Log Table

**File:** `mcp-servers/ai-cos-mcp/migrations/004_change_log.sql`

```sql
CREATE TABLE change_log (
    id SERIAL PRIMARY KEY,
    source_table TEXT NOT NULL,        -- 'companies', 'network', 'portfolio'
    source_notion_page_id TEXT NOT NULL,
    entity_name TEXT,                  -- human-readable: company name, person name
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,   -- has an action been generated from this?
    generated_action_id INT            -- FK to actions table if action was created
);

CREATE INDEX idx_change_log_unprocessed ON change_log(processed) WHERE processed = FALSE;
```

### 4b. Diff Engine

**Modify:** `mcp-servers/ai-cos-mcp/lib/sync.py`

Enhance `sync_companies_from_notion()` (and network/portfolio equivalents):

```
For each company being synced:
    1. SELECT current row from companies table
    2. For each Notion-owned field:
       if old_value != new_value:
           INSERT INTO change_log (source_table, source_notion_page_id, entity_name,
                                   field_name, old_value, new_value)
    3. Then proceed with UPSERT as before
```

### 4c. Change → Action Generator

**File:** `mcp-servers/ai-cos-mcp/lib/change_actions.py` (new)

```
def process_changes() -> list[dict]:
    1. SELECT * FROM change_log WHERE processed = FALSE
    2. For each change, apply rules:
       - deal_status changed → generate P1 action: "Review {company} — deal status moved to {new}"
       - relationship_status changed → generate P2 action: "Follow up with {person} — status now {new}"
       - conviction changed on thesis → generate P1 action: "Thesis '{thread}' conviction changed to {new}"
       - new company added → generate P2 action: "Initial IDS on new company: {name}"
       - new person added → generate P2 action: "Research {person} — new network entry"
    3. INSERT generated actions into actions table (source='ChangeDetection')
    4. UPDATE change_log SET processed=TRUE, generated_action_id=...
    5. Return list of generated actions
```

### 4d. Integration with Pipeline

**Modify:** `runners/pipeline.py`

Add after sync steps:
```
# Process any detected changes into actions
from lib.change_actions import process_changes
new_actions = process_changes()
if new_actions:
    print(f"  Generated {len(new_actions)} actions from Notion changes")
```

---

## Phase 5: SyncAgent Runner

**Goal:** Single orchestrator that runs all sync operations on schedule, with monitoring and alerting.

### 5a. SyncAgent Runner

**File:** `mcp-servers/ai-cos-mcp/runners/sync_agent.py` (new)

```
def run_sync():
    1. retry_pending_syncs()                    — replay failed Notion writes
    2. refresh_thesis_cache()                   — pull thesis threads
    3. sync_actions_bidirectional()              — push/pull actions
    4. If time for periodic sync (check last_synced timestamps):
       a. sync_companies_from_notion()          — every 6h
       b. sync_network_from_notion()            — every 6h
       c. sync_portfolio_from_notion()          — every 6h
       d. sync_content_digest_status()          — every 1h (pull Action Status changes)
    5. process_changes()                         — generate actions from detected diffs
    6. Log summary to sync_log table
    7. If any failures → alert (future: WhatsApp notification)
```

### 5b. Deployment

- Separate systemd unit: `ai-cos-sync.service` (or run as part of pipeline cron)
- Runs every 5 min (same as pipeline) but lightweight — most syncs are no-ops unless the periodic timer fires
- Alternatively: pipeline calls `run_sync()` at start of each run (simpler, one fewer service)

### 5c. Monitoring Table

**File:** `mcp-servers/ai-cos-mcp/migrations/005_sync_monitoring.sql`

```sql
CREATE TABLE sync_log (
    id SERIAL PRIMARY KEY,
    run_at TIMESTAMPTZ DEFAULT NOW(),
    duration_seconds REAL,
    thesis_synced INT DEFAULT 0,
    companies_synced INT DEFAULT 0,
    network_synced INT DEFAULT 0,
    portfolio_synced INT DEFAULT 0,
    actions_pushed INT DEFAULT 0,
    actions_pulled INT DEFAULT 0,
    changes_detected INT DEFAULT 0,
    actions_generated INT DEFAULT 0,
    retries_succeeded INT DEFAULT 0,
    retries_failed INT DEFAULT 0,
    errors JSONB                       -- [{table, error, timestamp}]
);
```

### 5d. Health Check Extension

**Modify:** `server.py` — extend `health_check()` MCP tool:

```
Add to health_check response:
- sync_queue_pending: count of pending writes
- last_sync_run: timestamp
- thesis_cache_age: seconds since last refresh
- companies_cache_age: seconds since last sync
- any sync errors in last 24h
```

---

## File Map

| File | Phase | Action |
|------|-------|--------|
| `migrations/001_sync_foundation.sql` | 1 | New — sync_queue + thesis_threads_cache tables |
| `migrations/002_core_data_tables.sql` | 2 | New — companies, network, portfolio tables |
| `migrations/003_actions_table.sql` | 3 | New — actions table with bidirectional sync |
| `migrations/004_change_log.sql` | 4 | New — change_log table |
| `migrations/005_sync_monitoring.sql` | 5 | New — sync_log table |
| `lib/sync.py` | 1-3 | New — all sync logic |
| `lib/change_actions.py` | 4 | New — change detection → action generation |
| `lib/notion_client.py` | 2 | Extend — add fetch_all_companies/network/portfolio |
| `runners/content_agent.py` | 1-2 | Modify — use sync wrappers, Postgres company data |
| `runners/pipeline.py` | 1, 4 | Modify — retry at start, change processing |
| `runners/sync_agent.py` | 5 | New — orchestrator |
| `scripts/initial_sync.py` | 2 | New — one-time population script |
| `server.py` | 3, 5 | Extend — triage tool, health check |

---

## Dependencies

- **Postgres** — already running on droplet (has `action_outcomes` table)
- **notion-client v3** — already installed
- **psycopg2** — already installed
- No new infrastructure needed. All phases use existing droplet Postgres + Notion API.

## Risk Notes

- **Notion API rate limits:** 3 requests/second. Batch fetches for Companies (49 entries) and Network (100+ entries) need pagination with backoff. Phase 2 sync should take <30s even with rate limiting.
- **Schema drift:** If Notion DB schema changes (new fields, renamed properties), the sync functions break. Mitigation: sync functions should log unknown properties, not crash. Schema changes are rare and human-initiated.
- **Bidirectional conflicts (Phase 3):** Last-writer-wins is simple but can lose edits if two surfaces triage the same action within the same sync cycle. Acceptable at current scale (low triage volume). Can upgrade to field-level CRDTs later if needed.
- **Initial data volume:** Companies ~50 entries, Network ~200 entries, Portfolio ~20 entries. Well within single-query Notion API limits. No scalability concerns.
