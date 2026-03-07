# Data Architecture
*Last Updated: 2026-03-07*

All data stores, schemas, field ownership, and sync patterns for the AI CoS system.

---

## Data Layer Overview

Data lives in two systems with field-level ownership defined in `docs/architecture/DATA-SOVEREIGNTY.md`:

- **Notion** — Human interface. 8 databases. Aakash interacts here. Source of truth for human-managed fields (company names, deal status, person contacts, action status changes).
- **Postgres (droplet)** — Machine brain. 7 tables. Agents reason here. Source of truth for enriched fields, preference history, sync state, and change events.

**Core principle:** The droplet's data is always equal or richer than Notion's. It has everything Notion has (synced periodically) plus agent-generated analysis, computed fields, and historical enrichments.

---

## Notion Databases (8)

### 1. Content Digest DB
**Data Source ID:** `df2d73d6-e020-46e8-9a8a-7b9da48b6ee2`
**SoT:** Droplet (creates analysis, pushes to Notion)
**Key Fields:** Video Title, Channel, Video URL, Duration, Content Type, Relevance Score, Net Newness, Connected Buckets, Summary, Key Insights, Essence Notes, Watch These Sections, Contra Signals, Rabbit Holes, Thesis Connections, Portfolio Relevance, Proposed Actions, Digest URL, Discovery Source, Action Status, Processing Date
**Sync:** Push (droplet → Notion after pipeline creates entry). Pull Action Status changes periodically.

### 2. Actions Queue
**Data Source ID:** `1df4858c-6629-4283-b31d-50c5e7ef885d`
**SoT:** Both (bidirectional)
**Key Fields:** Action (title), Company (relation to Portfolio DB), Thesis (relation to Thesis Tracker), Source Digest (relation to Content Digest), Action Type (select: Research, Meeting/Outreach, Thesis Update, Content Follow-up, Portfolio Check-in, Follow-on Eval, Pipeline Action), Priority (P0-P3), Status (Proposed → Accepted → In Progress → Done / Dismissed), Source, Assigned To, Created By, Relevance Score, Reasoning, Thesis Connection (text), Source Content, Outcome (Unknown/Helpful/Gold)
**Field Ownership:** Status = droplet-owned (MCP tools manage). Outcome = Notion-owned (human feedback, synced FROM Notion).
**Sync:** Push proposals (droplet → Notion). Pull Outcome changes (Notion → droplet). Bidirectional on triage events.

### 3. Thesis Tracker
**Data Source ID:** `3c8d1a34-e723-4fb1-be28-727777c22ec6`
**SoT:** Droplet → Notion (AI-managed, all fields except Status)
**Key Fields:** Thread Name (title), Status (select: Active/Exploring/Parked/Archived — HUMAN ONLY), Conviction (select: New/Evolving/Evolving Fast/Low/Medium/High), Core Thesis, Key Questions (summary + page content blocks as [OPEN]/[ANSWERED]), Evidence For, Evidence Against, Key Companies, Key People, Connected Buckets, Discovery Source, Investment Implications, Date Discovered, Last Updated
**All surfaces write through ai-cos-mcp** — droplet is single write authority for all fields except Status.
**Sync:** All writes go through MCP tools (write-ahead to Postgres, push to Notion). Status synced FROM Notion periodically (human-owned).

### 4. Companies DB
**Data Source ID:** `1edda9cc-df8b-41e1-9c08-22971495aa43`
**SoT:** Droplet (enriched) + Notion (human fields)
**Key Fields (49 total):** Company Name, Deal Status (3D matrix: pipeline stage x conviction x active/inactive), Stage, Sector, Thesis, Spiky Score (7 criteria x 1.0), EO/FMF/Thesis/Price scores (4 x /10), Founders (relation to Network DB), Team Notes, JTBD, Website, Description
**Notion-owned:** Company Name, Deal Status, Stage, Sector, scores, Founders
**Droplet-enriched:** Agent IDS notes, content pipeline connections, thesis thread links, signal history, computed conviction scores
**Sync:** Companies/Network/Portfolio sync deferred to Phase 5 (undeferred when agents need local access).

### 5. Network DB
**Data Source ID:** `6462102f-112b-40e9-8984-7cb1e8fe5e8b`
**SoT:** Droplet (enriched) + Notion (human fields)
**Key Fields (40+ total, 13 archetypes):** Person Name, Archetype (Founder, DF, CXO, Operator, Angel, Collective Member, LP, Academic, Journalist, Government, Advisor, EXT Target, Other), Company, Role, LinkedIn URL, Email, Phone, City, IDS Notes, Relationship Status, Last Interaction, Source, Collective Status, Fund Context
**Sync:** Deferred (Phase 5).

### 6. Portfolio DB
**Data Source ID:** `4dba9b7f-e623-41a5-9cb7-2af5976280ee`
**SoT:** Droplet (enriched) + Notion (human fields)
**Key Fields (94 total):** Fund, Vintage, Money In, Ownership, Valuation, EF/EO scores, Follow-on tracking, Follow-on scoring criteria, Company Name (HIDDEN relation to Companies DB), Founders
**Key relation:** Portfolio → Companies DB via hidden `Company Name` property links portfolio financial data to the company IDS trail.
**Sync:** Deferred (Phase 5).

### 7. Build Roadmap
**Data Source ID:** `6e1ffb7e-01f1-4295-a7ea-67d5c9216d8f`
**View URL:** `view://4eb66bc1-322b-4522-bb14-253018066fef`
**Key Fields:** Item (title), Status (7-state: Insight → Backlog → Planned → In Progress → Testing → Shipped → Won't Do), Priority (P0-P3), Epic, T-Shirt Size, Parallel Safety, Source, Sprint#, Branch, Technical Notes, Task Breakdown

### 8. Tasks Tracker
**Data Source ID:** `1b829bcc-b6fc-80fc-9da8-000b4927455b`
**Key Fields:** Task name, relations to Companies DB and Network DB, Task types (Network chat, Customer Call, BRC), Status, Assignee

---

## Postgres Tables (7)

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

### 4. companies

Postgres mirror of Companies DB (schema exists, sync deferred).

### 5. network

Postgres mirror of Network DB (schema exists, sync deferred).

### 6. sync_queue

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

### 7. change_events

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

---

## Sync Architecture

### Write-Ahead Pattern

All droplet-originated writes follow: **Postgres first → Notion push → sync_queue on failure**.

```
MCP Tool Call
    │
    ├─→ Write to Postgres (always succeeds or raises)
    │
    └─→ Push to Notion
         ├── Success → mark synced
         └── Failure → enqueue to sync_queue
                        (exponential backoff: 2^attempts minutes)
                        (max 5 attempts before considered failed)
```

### Sync Flows by Database

| Database | Direction | What Syncs | Frequency |
|----------|-----------|------------|-----------|
| **Thesis Tracker** | Droplet → Notion | All AI-written fields (conviction, evidence, key questions) | On every write via MCP tools |
| **Thesis Tracker** | Notion → Droplet | Status field only (human-owned) | Every 10 min (SyncAgent) |
| **Actions Queue** | Droplet → Notion | New proposed actions | On creation via pipeline |
| **Actions Queue** | Notion → Droplet | Outcome field only (human feedback) | Every 10 min (SyncAgent) |
| **Content Digest** | Droplet → Notion | Full analysis record | On pipeline completion |
| **sync_queue** | Droplet → Notion | Failed writes retried | Every 10 min (SyncAgent) |
| **Companies/Network/Portfolio** | Not synced | Deferred to Phase 5 | N/A |

### Change Detection → Action Generation

```
SyncAgent detects field change
    │
    ├─→ Log to change_events table
    │
    └─→ Generate proposed action (if rules match):
         - Thesis conviction → High → "Review portfolio for opportunities"
         - Thesis Active → Parked → "Deprioritize connected actions"
         - Thesis Parked → Active → "Resurface actions for thesis"
         - Action outcome → Gold → "Analyze what made this valuable"
```

---

## Detailed Reference

- **Field ownership rules:** `docs/architecture/DATA-SOVEREIGNTY.md`
- **Notion operations guide:** `docs/notion/README.md`
- **Thesis DB implementation:** `mcp-servers/ai-cos-mcp/lib/thesis_db.py`
- **Actions DB implementation:** `mcp-servers/ai-cos-mcp/lib/actions_db.py`
- **Change detection implementation:** `mcp-servers/ai-cos-mcp/lib/change_detection.py`
- **Database schemas (Notion):** `docs/notion/schemas/`
- **CONTEXT.md** — Notion DB IDs, schema snapshots, domain knowledge
