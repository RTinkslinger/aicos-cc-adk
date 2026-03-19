# Data Architecture
*Last Updated: 2026-03-18*

All data stores, schemas, field ownership, and sync patterns for the AI CoS system.

---

## Data Layer Overview

Data lives in two systems with field-level ownership (see ENTITY-SCHEMAS.md for the full 3-actor sovereignty model):

- **Notion** — Human interface. 8 databases. Aakash interacts here. Source of truth for human-managed fields (company names, deal status, person contacts, action status changes).
- **Postgres** — Machine brain. 10 tables. Agents reason here. Source of truth for enriched fields, preference history, pipeline state, inbox relay, and change events.

**Planned migration:** Postgres moves from droplet to **Supabase** (managed Postgres with real-time, PostgREST, MCP). WebFront server components query Supabase directly via `@supabase/ssr`. Agents on the droplet connect via standard `DATABASE_URL` (psql). Supabase Realtime enables live pipeline status on WebFront. Single source of truth, no replication layer needed. See `WEBFRONT.md` for migration steps.

**Core principle:** Postgres data is always equal or richer than Notion's. It has everything Notion has (synced periodically) plus agent-generated analysis, computed fields, and historical enrichments.

---

## Notion Databases (8)

### 1. Content Digest DB
**Data Source ID:** `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`
**SoT:** Droplet (creates analysis, pushes to Notion)
**Key Fields:** Video Title, Channel, Video URL, Duration, Content Type, Relevance Score, Net Newness, Connected Buckets, Summary, Key Insights, Essence Notes, Watch These Sections, Contra Signals, Rabbit Holes, Thesis Connections, Portfolio Relevance, Proposed Actions, Digest URL, Discovery Source, Action Status, Processing Date
**Write pattern:** Content Agent writes to Postgres (content_digests table with status column), then pushes to Notion after analysis completes.

### 2. Actions Queue
**Data Source ID:** `1df4858c-6629-4283-b31d-50c5e7ef885d`
**SoT:** Both (bidirectional)
**Key Fields:** Action (title), Company (relation to Portfolio DB), Thesis (relation to Thesis Tracker), Source Digest (relation to Content Digest), Action Type (select: Research, Meeting/Outreach, Thesis Update, Content Follow-up, Portfolio Check-in, Follow-on Eval, Pipeline Action), Priority (P0-P3), Status (Proposed → Accepted → In Progress → Done / Dismissed), Source, Assigned To, Created By, Relevance Score, Reasoning, Thesis Connection (text), Source Content, Outcome (Unknown/Helpful/Gold)
**Field Ownership:** Status = droplet-owned (MCP tools manage). Outcome = Notion-owned (human feedback).
**Write pattern:** Content Agent proposes actions → Postgres → Notion. Aakash changes Outcome in Notion.

### 3. Thesis Tracker
**Data Source ID:** `3c8d1a34-e723-4fb1-be28-727777c22ec6`
**SoT:** Droplet → Notion (AI-managed, all fields except Status)
**Key Fields:** Thread Name (title), Status (select: Active/Exploring/Parked/Archived — HUMAN ONLY), Conviction (select: New/Evolving/Evolving Fast/Low/Medium/High), Core Thesis, Key Questions (summary + page content blocks as [OPEN]/[ANSWERED]), Evidence For, Evidence Against, Key Companies, Key People, Connected Buckets, Discovery Source, Investment Implications, Date Discovered, Last Updated
**All surfaces write through State MCP tools** — droplet is single write authority for all fields except Status.
**Write pattern:** All writes go through MCP tools (write-ahead to Postgres, push to Notion). Status is human-owned in Notion.

### 4. Companies DB
**Data Source ID:** `1edda9cc-df8b-41e1-9c08-22971495aa43`
**SoT:** Droplet (enriched) + Notion (human fields)
**Key Fields (49 total):** Company Name, Deal Status (3D matrix: pipeline stage x conviction x active/inactive), Stage, Sector, Thesis, Spiky Score (7 criteria x 1.0), EO/FMF/Thesis/Price scores (4 x /10), Founders (relation to Network DB), Team Notes, JTBD, Website, Description
**Notion-owned:** Company Name, Deal Status, Stage, Sector, scores, Founders
**Droplet-enriched:** Agent IDS notes, content pipeline connections, thesis thread links, signal history, computed conviction scores
**Sync:** Deferred (agents access via Notion MCP when needed).

### 5. Network DB
**Data Source ID:** `6462102f-112b-40e9-8984-7cb1e8fe5e8b`
**SoT:** Droplet (enriched) + Notion (human fields)
**Key Fields (40+ total, 13 archetypes):** Person Name, Archetype (Founder, DF, CXO, Operator, Angel, Collective Member, LP, Academic, Journalist, Government, Advisor, EXT Target, Other), Company, Role, LinkedIn URL, Email, Phone, City, IDS Notes, Relationship Status, Last Interaction, Source, Collective Status, Fund Context
**Sync:** Deferred.

### 6. Portfolio DB
**Data Source ID:** `4dba9b7f-e623-41a5-9cb7-2af5976280ee`
**SoT:** Droplet (enriched) + Notion (human fields)
**Key Fields (94 total):** Fund, Vintage, Money In, Ownership, Valuation, EF/EO scores, Follow-on tracking, Follow-on scoring criteria, Company Name (HIDDEN relation to Companies DB), Founders
**Key relation:** Portfolio → Companies DB via hidden `Company Name` property links portfolio financial data to the company IDS trail.
**Sync:** Deferred.

### 7. Build Roadmap
**Data Source ID:** `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f`
**View URL:** `view://4eb66bc1-322b-4522-bb14-253018066fef`
**Key Fields:** Item (title), Status (7-state: Insight → Backlog → Planned → In Progress → Testing → Shipped → Won't Do), Priority (P0-P3), Epic, T-Shirt Size, Parallel Safety, Source, Sprint#, Branch, Technical Notes, Task Breakdown

### 8. Tasks Tracker
**Data Source ID:** `1b829bcc-b6fc-80fc-9da8-000b4927455b`
**Key Fields:** Task name, relations to Companies DB and Network DB, Task types (Network chat, Customer Call, BRC), Status, Assignee

---

## Postgres Tables (10)

### 1. thesis_threads

Mirrors Thesis Tracker from Notion with enrichment columns.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| thread_name | TEXT | |
| core_thesis | TEXT | |
| conviction | TEXT | New/Evolving/Evolving Fast/Low/Medium/High |
| status | TEXT | Active/Exploring/Parked/Archived (synced from Notion) |
| discovery_source | TEXT | Claude/Content Pipeline/Meeting/Research |
| connected_buckets | TEXT[] | Array of bucket names |
| key_questions_json | JSONB | `{"open": [...], "answered": [...]}` |
| key_question_summary | TEXT | e.g. "3 open, 1 answered" |
| evidence_for | TEXT | IDS notation (+ signals), append-only |
| evidence_against | TEXT | IDS notation (? signals), append-only |
| investment_implications | TEXT | |
| key_companies | TEXT | |
| notion_page_id | TEXT | Links to Notion page |
| notion_synced | BOOLEAN | Flag for sync agent pickup |
| date_discovered | DATE | |
| last_synced_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

### 2. actions_queue

Mirrors Actions Queue from Notion with sync metadata.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| action | TEXT | Action description (title) |
| action_type | TEXT | |
| status | TEXT | Proposed/Accepted/In Progress/Done/Dismissed |
| priority | TEXT | P0-P3 |
| source | TEXT | |
| assigned_to | TEXT | |
| created_by | TEXT | |
| reasoning | TEXT | |
| source_content | TEXT | |
| thesis_connection | TEXT | |
| relevance_score | REAL | 0-100 |
| outcome | TEXT | Unknown/Helpful/Gold (synced from Notion) |
| company_notion_id | TEXT | |
| source_digest_notion_id | TEXT | |
| notion_page_id | TEXT | Links to Notion page |
| notion_synced | BOOLEAN | Flag for sync agent pickup |
| scoring_factors | JSONB | Scoring model snapshot |
| last_local_edit | TIMESTAMPTZ | Last edit from droplet |
| last_notion_edit | TIMESTAMPTZ | Last edit from Notion |
| last_synced_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

### 3. action_outcomes (Preference Store)

THE learning mechanism. Every accept/reject with scoring factor snapshots.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| action_id | TEXT NOT NULL | |
| action_type | TEXT NOT NULL | |
| company_id | TEXT | |
| person_id | TEXT | |
| proposed_at | TIMESTAMPTZ NOT NULL | |
| decided_at | TIMESTAMPTZ | |
| decision | TEXT | accepted/dismissed/deferred/expired |
| proposed_score | REAL | |
| scoring_factors | JSONB | Factor snapshots at proposal time |
| context_snapshot | JSONB | |
| feedback_note | TEXT | |
| source_signal | TEXT | |

### 4. content_digests

Pipeline state for content processing. Postgres-as-queue pattern with status column.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| url | TEXT UNIQUE | Source URL (dedup key) |
| title | TEXT | |
| channel | TEXT | |
| status | TEXT | pending/processing/published/failed |
| digest_data | JSONB | Full analysis output |
| upload_date | DATE | Original content publish date |
| processing_date | TIMESTAMPTZ | When pipeline processed it |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Index:** `idx_content_digests_status` on status column.

### 5. companies

Postgres mirror of Companies DB (schema exists, sync deferred).

### 6. network

Postgres mirror of Network DB (schema exists, sync deferred).

### 7. sync_queue

Failed Notion writes queued for retry with exponential backoff.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| table_name | TEXT | Which table the write targets |
| record_id | INT | PK of the failed record |
| operation | TEXT | "create" or "update" |
| payload | JSONB | Full payload to retry |
| attempts | INT | Retry count |
| last_error | TEXT | Most recent error message |
| next_retry_at | TIMESTAMPTZ | Backoff: 2^attempts minutes |
| created_at | TIMESTAMPTZ | |

### 8. change_events

Field-level change log from sync detection.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| table_name | TEXT | thesis_threads or actions_queue |
| record_id | INT | PK of the changed record |
| notion_page_id | TEXT | |
| field_name | TEXT | Which field changed |
| old_value | TEXT | Previous value |
| new_value | TEXT | New value |
| processed | BOOLEAN | Whether action generation has processed this |
| detected_at | TIMESTAMPTZ | |

### 9. cai_inbox

Async inbox relay: CAI posts messages via State MCP `post_message` → Content Agent reads via psql.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| content | TEXT | Message from CAI |
| processed | BOOLEAN | FALSE until agent picks up |
| created_at | TIMESTAMPTZ | |

### 10. notifications

Agent → CAI notifications. Agents write, CAI reads via State MCP `get_state(notifications)`.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| content | TEXT | Notification message |
| type | TEXT | Category/type tag |
| read | BOOLEAN | FALSE until CAI reads |
| created_at | TIMESTAMPTZ | |

*Note: sync_metadata table also exists (tracks freshness per table/field). Discover schema via `psql \d sync_metadata`.*

---

## Sync Architecture

### Write-Ahead Pattern

All droplet-originated writes follow: **Postgres first → Notion push → sync_queue on failure**.

```
MCP Tool Call (State MCP) or Content Agent (direct psql)
    │
    ├─→ Write to Postgres (always succeeds or raises)
    │
    └─→ Push to Notion
         ├── Success → mark synced
         └── Failure → enqueue to sync_queue
                        (exponential backoff: 2^attempts minutes)
                        (max 5 attempts before considered failed)
```

### Content Pipeline: Postgres-as-Queue

Content Agent uses the `status` column on `content_digests` as a processing queue:

```
Discover new content (YouTube/RSS)
    → INSERT with status='pending'
    → Agent picks up pending rows
    → UPDATE status='processing'
    → Claude analysis → DigestData JSON
    → Write digest_data, UPDATE status='published'
    → Push to Notion + publish to digest.wiki
    → On error: UPDATE status='failed'
```

### Write Patterns by Database

| Database | Write Source | Pattern |
|----------|-------------|---------|
| **Thesis Tracker** | State MCP tools | Write-ahead (Postgres → Notion). Status is human-owned in Notion. |
| **Actions Queue** | Content Agent | Postgres → Notion. Outcome is human-owned in Notion. |
| **Content Digest** | Content Agent | Postgres-as-queue (status column). Push to Notion after analysis. |
| **CAI Inbox** | CAI via State MCP | `post_message` → cai_inbox table → Content Agent reads via psql. |
| **Notifications** | Content Agent | Agent writes → CAI reads via State MCP `get_state`. |
| **Companies/Network/Portfolio** | Not synced | Deferred — agents access via Notion MCP when needed. |

### Change Detection → Action Generation (Designed, not currently active)

Infrastructure exists for detecting field-level changes and generating actions:

```
Sync detects field change
    │
    ├─→ Log to change_events table
    │
    └─→ Generate proposed action (if rules match):
         - Thesis conviction → High → "Review portfolio for opportunities"
         - Thesis Active → Parked → "Deprioritize connected actions"
         - Thesis Parked → Active → "Resurface actions for thesis"
         - Action outcome → Gold → "Analyze what made this valuable"
```

*This was built for SyncAgent which is currently disabled. Infrastructure ready for re-activation.*

---

## Field Ownership Summary

| Field | Owner | Written By | Synced Via |
|-------|-------|-----------|------------|
| Thesis: all fields except Status | Droplet | State MCP tools | Write-ahead → Notion |
| Thesis: Status | Human | Notion (manual) | Read by agents when needed |
| Actions: Status | Droplet | Content Agent | Push to Notion |
| Actions: Outcome | Human | Notion (manual) | Read by agents when needed |
| Content Digest: all fields | Droplet | Content Agent | Push to Notion after analysis |
| Companies/Network/Portfolio: all fields | Human | Notion (manual) | Not synced (agents query Notion directly) |

---

## Detailed Reference

- **Field ownership rules:** `docs/source-of-truth/ENTITY-SCHEMAS.md` (3-actor sovereignty model)
- **Notion operations guide:** `docs/notion/README.md`
- **State MCP DB layer:** `mcp-servers/agents/state/db/` (thesis.py, inbox.py, notifications.py)
- **Database schemas (Notion):** See CONTEXT.md for full field lists
- **Postgres schemas (live):** `psql \d <tablename>` on droplet
