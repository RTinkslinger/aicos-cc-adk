# Datum Processing Skill

How to process incoming datum messages. Load this skill when you receive entity signals from the Orchestrator.

---

## Input Parsing

### Text Input (most common)

Extract structured fields from natural language:

```
Input: "Add Rahul Sharma, CTO at Composio"
Parsed:
  type: person
  name: Rahul Sharma
  role: CTO
  company: Composio
```

```
Input: "Track Composio - AI agent tooling startup, composio.dev"
Parsed:
  type: company
  name: Composio
  sector: AI Infrastructure
  domain: composio.dev
```

**Extraction patterns:**
- "X at Y" / "X from Y" / "X, Y" → person name + company
- "CTO" / "CEO" / "Founder" / "VP" / "Head of" → role
- "linkedin.com/in/..." → linkedin_url
- Domain-like strings (x.com, x.io, x.dev) → company domain
- City names / "based in X" → city

### URL Input

| URL Pattern | Action |
|-------------|--------|
| `linkedin.com/in/...` | Person entity. Scrape for name, role, company, city. |
| `linkedin.com/company/...` | Company entity. Scrape for name, sector, description. |
| `*.com`, `*.io`, etc. (non-LinkedIn) | Company entity. Domain = URL host. Scrape for company info. |
| `twitter.com/...`, `x.com/...` | Extract username. web_search for identity. |

### Batch Input

Content pipeline sends batches in this format:
```
Entities:
1. [company] Composio — AI agent tooling, mentioned in interview
2. [person] Karan Vaidya — CEO at Composio, speaker in interview
3. [person] Sarah Lee — CTO at Composio, co-speaker
```

Process sequentially. The second entity in a batch may match the first (just-created) record.

---

## datum_requests Table Schema

```sql
CREATE TABLE datum_requests (
    id SERIAL PRIMARY KEY,
    entity_type TEXT NOT NULL,       -- 'person' or 'company'
    entity_id INTEGER NOT NULL,      -- FK to network.id or companies.id
    field_name TEXT NOT NULL,         -- Column name: 'email', 'sector', etc.
    source_context TEXT,             -- Where entity came from
    current_value TEXT,              -- Existing value (for correction requests)
    suggested_value TEXT,            -- Agent's best guess
    suggestion_confidence REAL,      -- 0.0-1.0
    suggestion_source TEXT,          -- 'LinkedIn scrape', 'web search', etc.
    merge_candidate_ids INTEGER[],   -- For merge confirmation requests
    merge_type TEXT,                 -- 'confirm_merge' | 'pick_match' | 'fill_field'
    status TEXT DEFAULT 'pending',   -- pending | answered | skipped | expired
    answer TEXT,                     -- User's answer
    answered_by TEXT,                -- 'webfront' | 'cai' | 'auto'
    answered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Creating Datum Requests

**For missing fields:**
```sql
INSERT INTO datum_requests (entity_type, entity_id, field_name, source_context,
                            suggested_value, suggestion_confidence, suggestion_source,
                            merge_type, status, created_at, updated_at)
VALUES ('person', $id, 'email', 'Parsed from CAI: "Add Rahul from Composio"',
        'rahul@composio.dev', 0.72, 'domain inference', 'fill_field', 'pending', NOW(), NOW());
```

**For merge confirmation:**
```sql
INSERT INTO datum_requests (entity_type, entity_id, field_name, source_context,
                            merge_candidate_ids, merge_type, status, created_at, updated_at)
VALUES ('person', $new_id, 'merge_decision',
        'New entity "Rahul S." may be same as "Rahul Sharma" (ID=42). Similarity: 0.87',
        ARRAY[42], 'confirm_merge', 'pending', NOW(), NOW());
```

**For multiple merge candidates:**
```sql
INSERT INTO datum_requests (entity_type, entity_id, field_name, source_context,
                            merge_candidate_ids, merge_type, status, created_at, updated_at)
VALUES ('person', $new_id, 'merge_decision',
        'New entity "Rahul" matches 3 existing records. Pick the correct one or keep separate.',
        ARRAY[42, 57, 63], 'pick_match', 'pending', NOW(), NOW());
```

### Dedup before creating requests

Always check first:
```sql
SELECT id FROM datum_requests
WHERE entity_type = $type AND entity_id = $id
  AND field_name = $field AND status = 'pending';
```
If a pending request exists, do NOT create a duplicate.

---

## Network Table — Key Columns for Datum Agent

**IMPORTANT:** The network table uses non-standard column names. Always use the exact names below.

| Column | Type | Datum Agent Usage |
|--------|------|-------------------|
| `person_name` | TEXT | P0 — required for record creation (NOT "name") |
| `current_role` | TEXT | P0 — "Role at Company" format (NOT "role") |
| `linkedin` | TEXT | P1 — strongest dedup key (NOT "linkedin_url") |
| `e_e_priority` | TEXT | P1 — engagement priority classification |
| `email` | TEXT | P2 — contact |
| `home_base` | TEXT[] | P2 — location array (NOT "city") |
| `phone` | TEXT | P3 — contact |
| `ids_notes` | TEXT | P3 — IDS methodology notes |
| `source` | TEXT | P3 — how this person entered the network |
| `aliases` | TEXT[] | Dedup — alternative names |
| `enrichment_status` | TEXT | Status tracking: raw/partial/enriched/verified |
| `enrichment_source` | TEXT | Who enriched: datum_agent/manual/sync |
| `last_enriched_at` | TIMESTAMPTZ | When last enriched |
| `datum_source` | TEXT | Signal origin: cai_message/content_pipeline/meeting/manual |
| `datum_created_at` | TIMESTAMPTZ | When Datum Agent first created/touched |
| `embedding` | vector(1024) | Auto-populated by trigger pipeline |
| `current_company_ids` | TEXT[] | Notion page IDs of current companies |
| `past_company_ids` | TEXT[] | Notion page IDs of past companies |

---

## Companies Table — Key Columns for Datum Agent

| Column | Type | Datum Agent Usage |
|--------|------|-------------------|
| `name` | TEXT | P0 — required for record creation |
| `domain` | TEXT (UNIQUE) | P0 — strongest dedup key |
| `sector` | TEXT | P1 — classification |
| `stage` | TEXT | P1 — funding stage |
| `description` | TEXT | P1 — one-liner description |
| `aliases` | TEXT[] | Dedup — alternative names |
| `enrichment_status` | TEXT | Status tracking |
| `enrichment_source` | TEXT | Who enriched |
| `last_enriched_at` | TIMESTAMPTZ | When last enriched |
| `datum_source` | TEXT | Signal origin |
| `datum_created_at` | TIMESTAMPTZ | When first created/touched |
| `embedding` | vector(1024) | Auto-populated by trigger pipeline |

---

## Processing Checklist

For every entity signal, follow this exact order:

1. [ ] Parse input — extract all available fields
2. [ ] Determine entity type (person or company)
3. [ ] Run dedup algorithm (load `skills/datum/dedup-algorithm.md`)
4. [ ] If match found: merge (COALESCE pattern)
5. [ ] If no match: INSERT new record
6. [ ] Attempt web enrichment for NULL P0/P1 fields (max 3 calls)
7. [ ] Compute enrichment_status
8. [ ] Create datum requests for remaining NULL fields
9. [ ] Write notification
10. [ ] Write summary to `state/datum_last_log.txt`
11. [ ] End with structured ACK
