# Datum Staging Processing Skill

How to process `interaction_staging` rows into clean `interactions` + `people_interactions`
records. Load this skill when the Orchestrator sends `datum_staging_process` or when
`interaction_staging` has unprocessed rows.

---

## Overview

Fetchers (email, WhatsApp, Granola, calendar) drop raw interaction data into
`interaction_staging`. Datum processes each row: resolves participants to network IDs,
extracts structured data, writes clean records to `interactions` and `people_interactions`,
then marks the staging row processed.

**Pipeline:** Fetcher -> `interaction_staging` -> Datum processes -> `interactions` + `people_interactions` -> Cindy reads

**Datum owns:** participant resolution, entity linking, record creation.
**Cindy owns:** intelligence extraction from the clean interactions (obligations, signals, context gaps).

---

## Schema Reference

### interaction_staging (input)

| Column | Type | Purpose |
|--------|------|---------|
| `id` | int | PK |
| `source` | text | 'email', 'whatsapp', 'granola', 'calendar' |
| `source_id` | text | Dedup key from source system |
| `raw_data` | jsonb | Full raw data from fetcher |
| `datum_processed` | boolean | FALSE until Datum processes |
| `cindy_processed` | boolean | FALSE until Cindy processes |
| `error_message` | text | Error if processing failed |
| `resolved_participants` | jsonb | Datum writes resolved participant map here |
| `resolution_status` | text | 'pending', 'partial', 'complete', 'failed' |
| `participant_count` | int | Total participants found |
| `resolved_count` | int | Participants matched to network IDs |
| `extracted_data` | jsonb | Structured data extracted by Datum |
| `linked_companies` | int[] | Company IDs linked |
| `linked_people` | int[] | Network IDs linked |
| `datum_processed_at` | timestamptz | When Datum finished |
| `interaction_id` | int | FK to interactions table (after creation) |

### interactions (output)

| Column | Type | Purpose |
|--------|------|---------|
| `id` | int | PK |
| `source` | text | Inherited from staging |
| `source_id` | text | Inherited from staging |
| `thread_id` | text | Conversation thread grouping |
| `participants` | text[] | Display names array |
| `linked_people` | int[] | Network IDs |
| `linked_companies` | int[] | Company IDs |
| `summary` | text | Brief summary |
| `raw_data` | jsonb | Inherited from staging |
| `timestamp` | timestamptz | When interaction occurred |
| `duration_minutes` | int | For meetings |
| `action_items` | text[] | Extracted action items |
| `thesis_signals` | jsonb | Thesis-relevant signals |
| `relationship_signals` | jsonb | Relationship quality signals |
| `deal_signals` | jsonb | Deal pipeline signals |
| `context_assembly` | jsonb | Assembled context for Cindy |
| `datum_staged_id` | int | FK back to staging row |
| `cindy_processed` | boolean | FALSE until Cindy processes |

### people_interactions (linking)

| Column | Type | Purpose |
|--------|------|---------|
| `id` | int | PK |
| `person_id` | int | FK to network.id |
| `interaction_id` | int | FK to interactions.id |
| `role` | text | 'sender', 'recipient', 'cc', 'participant', 'organizer' |
| `surface` | text | 'email', 'whatsapp', 'granola', 'calendar' |
| `identifier_used` | text | 'email:x@y.com', 'phone:+91...', 'name:Rahul Sharma' |
| `link_confidence` | real | 0.0-1.0 |
| `linked_at` | timestamptz | When link was created |

---

## Processing Flow

For each unprocessed staging row:

### Step 1: Read Unprocessed Rows

```sql
SELECT id, source, source_id, raw_data, participant_count
FROM interaction_staging
WHERE datum_processed = FALSE
  AND error_message IS NULL
ORDER BY created_at ASC
LIMIT 10;
```

Process sequentially. Limit to 10 per batch to avoid overload.

### Step 2: Extract Participants from raw_data

Participants vary by source:

**Email:**
```json
{
  "from": {"email": "rahul@composio.dev", "name": "Rahul Sharma"},
  "to": [{"email": "ak@z47.com", "name": "Aakash Kumar"}],
  "cc": [{"email": "sarah@composio.dev", "name": "Sarah Lee"}],
  "subject": "Re: Series A follow-up",
  "body": "...",
  "date": "2026-03-21T10:00:00Z"
}
```

**WhatsApp:**
```json
{
  "chat_id": "...",
  "messages": [...],
  "participants": [
    {"jid": "919999999999@s.whatsapp.net", "push_name": "Rahul"},
    {"jid": "918888888888@s.whatsapp.net", "push_name": "Aakash"}
  ]
}
```

**Granola:**
```json
{
  "meeting_id": "...",
  "title": "Composio Series A Discussion",
  "attendees": ["Rahul Sharma", "Aakash Kumar", "Sarah Lee"],
  "transcript": "...",
  "date": "2026-03-21T10:00:00Z",
  "duration_minutes": 45
}
```

**Calendar:**
```json
{
  "event_id": "...",
  "title": "Meeting with Composio",
  "organizer": {"email": "ak@z47.com", "name": "Aakash Kumar"},
  "attendees": [
    {"email": "rahul@composio.dev", "name": "Rahul Sharma", "status": "accepted"}
  ],
  "start": "2026-03-21T10:00:00Z",
  "end": "2026-03-21T10:45:00Z"
}
```

### Step 3: Resolve Each Participant

For each participant, run the 6-tier resolution from `people-linking.md`:

1. **Filter out Aakash** -- skip resolution for known Aakash emails/phones
2. **Tier 1-3:** Unique identifier match (email, phone, LinkedIn)
3. **Tier 4-5:** Name match (with or without company context)
4. **Tier 6:** No match -> delegate to Datum entity creation

Build the resolved_participants map:

```json
[
  {"identifier": "email:rahul@composio.dev", "network_id": 42, "confidence": 1.0, "name": "Rahul Sharma"},
  {"identifier": "email:sarah@composio.dev", "network_id": null, "confidence": 0.0, "name": "Sarah Lee", "action": "create"}
]
```

### Step 4: Create New Entities for Unresolved Participants

For participants with `action: "create"`:

```sql
-- Only create if we have enough data (name + email or name + phone)
INSERT INTO network (person_name, email, role_title, enrichment_status, enrichment_source, datum_source, datum_created_at)
VALUES ('Sarah Lee', 'sarah@composio.dev', 'at Composio', 'raw', 'datum_agent', 'interaction_staging', NOW())
RETURNING id;
```

Then re-resolve to get the new network ID.

### Step 5: Update Staging Row with Resolution Results

```sql
UPDATE interaction_staging SET
  resolved_participants = $resolved_json,
  resolution_status = CASE
    WHEN all_resolved THEN 'complete'
    WHEN some_resolved THEN 'partial'
    ELSE 'failed'
  END,
  participant_count = $total_count,
  resolved_count = $resolved_count,
  linked_people = ARRAY[$network_ids],
  updated_at = NOW()
WHERE id = $staging_id;
```

### Step 6: Create Interaction Record

```sql
INSERT INTO interactions (
  source, source_id, thread_id, participants,
  linked_people, linked_companies, summary,
  raw_data, timestamp, duration_minutes,
  datum_staged_id, cindy_processed, created_at, updated_at
) VALUES (
  $source, $source_id, $thread_id,
  ARRAY[$participant_names],
  ARRAY[$network_ids],
  ARRAY[$company_ids],
  $summary,
  $raw_data, $timestamp, $duration,
  $staging_id, FALSE, NOW(), NOW()
) RETURNING id;
```

### Step 7: Create People-Interaction Links

```sql
INSERT INTO people_interactions (person_id, interaction_id, role, surface, identifier_used, link_confidence, linked_at)
VALUES ($person_id, $interaction_id, $role, $source, $identifier, $confidence, NOW())
ON CONFLICT (person_id, interaction_id) DO NOTHING;
```

### Step 8: Mark Staging Row Processed

```sql
UPDATE interaction_staging SET
  datum_processed = TRUE,
  datum_processed_at = NOW(),
  interaction_id = $new_interaction_id,
  updated_at = NOW()
WHERE id = $staging_id;
```

---

## Error Handling

If processing fails for a staging row:

```sql
UPDATE interaction_staging SET
  error_message = 'Error description: ' || $error,
  resolution_status = 'failed',
  updated_at = NOW()
WHERE id = $staging_id;
```

Do NOT mark `datum_processed = TRUE` on failure. The row will be retried on next cycle.

After 3 failures (check `error_message IS NOT NULL`), write a notification for manual review.

---

## Company Linking

While resolving participants, also identify company context:

1. **Email domain** -> check `companies.domain`
2. **Meeting title** -> extract company names, check `companies.name`
3. **Role context** -> from `role_title` of resolved participants

```sql
-- Find company by email domain
SELECT id FROM companies
WHERE domain = 'composio.dev'
  AND pipeline_status != 'Merged/Duplicate';

-- Or by name from meeting context
SELECT id FROM companies
WHERE LOWER(name) = LOWER('Composio')
  AND pipeline_status != 'Merged/Duplicate';
```

Add found company IDs to `linked_companies` on both the staging row and the interaction.

---

## Aakash Identity Filter

Always filter out Aakash from participant resolution:

```
Known Aakash identifiers:
- Emails: ak@z47.com, aakash@devc.fund, hi@aacash.me
- Phone: (check network WHERE person_name ILIKE 'Aakash Kumar')
- Name patterns: "Aakash Kumar", "Aakash"
```

Do NOT create datum_requests or network records for Aakash.
Do NOT include Aakash in `linked_people` arrays.
DO include Aakash in the `participants` display array.

---

## Dedup Guard

Before creating an interaction record, check for duplicates:

```sql
SELECT id FROM interactions
WHERE source = $source AND source_id = $source_id;
```

If exists, update the existing record instead of creating a duplicate.

---

## Batch Processing Summary

After processing a batch of staging rows:

```
ACK: Staging processing complete.
- Rows processed: 8
- Resolution: 6 complete, 2 partial
- People resolved: 15 (12 existing, 3 new)
- Companies linked: 5
- Interactions created: 8
- People-interaction links: 23
- Datum requests created: 2 (ambiguous matches)
```

---

## Anti-Patterns

1. **Never skip the dedup check** before creating interactions
2. **Never create network records without enough data** (at minimum: name + one identifier)
3. **Never mark datum_processed on error** -- let the retry mechanism handle it
4. **Never overwrite existing non-NULL fields** during participant cross-linking
5. **Never process more than 10 staging rows per batch** -- keeps context manageable
6. **Never resolve Aakash** -- filter out known identifiers
7. **Never create interactions without at least one resolved participant** (besides Aakash)
