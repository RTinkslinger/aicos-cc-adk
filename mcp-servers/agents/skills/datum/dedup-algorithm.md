# Dedup Algorithm Skill

The 4-tier dedup algorithm for entity resolution. Load this skill before processing any entity.

---

## Overview

The dedup algorithm resolves whether an incoming entity candidate matches an existing record.
It produces one of three outcomes:
- **CREATE** — No match found, create a new record
- **MERGE** — Match found, merge new data into existing record
- **ASK_USER** — Ambiguous match, create a datum_request for human decision

---

## For Persons (entity_type = 'person')

### Tier 1: LinkedIn Match (Strongest — Confidence 1.0)

LinkedIn URL is a globally unique identifier. If available, check it first.

**NOTE:** The network table uses `linkedin` (not `linkedin_url`), `person_name` (not `name`),
`current_role` (not `role`). Always use the exact column names.

```sql
SELECT id, person_name, current_role, linkedin
FROM network
WHERE linkedin = $candidate_linkedin;
```

- **If match:** MERGE. Confidence = 1.0. Done.
- **If no match:** Continue to Tier 2.
- **If candidate has no LinkedIn:** Skip to Tier 2.

**Note:** There are duplicate LinkedIn URLs in the existing data. If multiple matches,
use the most recently updated record (`ORDER BY updated_at DESC LIMIT 1`).

### Tier 2: Exact Name Match (Confidence 0.95)

Exact text match on person_name (case-insensitive). The network table does not have a
separate "company" column — company context is embedded in `current_role`.

```sql
SELECT id, person_name, current_role, linkedin
FROM network
WHERE LOWER(person_name) = LOWER($candidate_name);
```

- **If single match:** MERGE. Confidence = 0.95. Done.
- **If multiple matches:** ASK_USER with all candidate IDs. Common for names like "Rahul Sharma".
- **If no match:** Continue to Tier 3.

### Tier 3: Embedding Similarity (Confidence varies)

Semantic similarity via vector embeddings. Only works if:
- The candidate record already has an embedding (requires INSERT first, then ~10-30s for auto-embed)
- Existing records have embeddings

**For new records that need immediate dedup:** Insert the record first, then check Tier 4
(name-only) as a fallback. Embedding dedup is primarily for catching duplicates that slip
through Tier 1-2, detected on subsequent encounters.

**For records that already have embeddings** (e.g., re-enrichment, batch second pass):

```sql
SELECT id, person_name, current_role,
       1 - (embedding <=> $candidate_embedding) as similarity
FROM network
WHERE embedding IS NOT NULL
  AND id != $candidate_id
  AND 1 - (embedding <=> $candidate_embedding) > 0.80
ORDER BY similarity DESC
LIMIT 5;
```

| Result | Action |
|--------|--------|
| No matches above 0.80 | CREATE new record |
| Single match, similarity > 0.90 | MERGE. Auto-merge with confidence note. |
| Single match, similarity 0.80-0.90 | ASK_USER. Create datum_request for merge confirmation. |
| Multiple matches above 0.80 | ASK_USER. Create datum_request listing all candidates. |

### Tier 4: Name-Only Match (Fallback — Confidence 0.50-0.70)

Last resort when neither LinkedIn, nor embedding is available. Same query as Tier 2 but
reached when Tier 3 also failed (no embeddings available).

```sql
SELECT id, person_name, current_role, linkedin
FROM network
WHERE LOWER(person_name) = LOWER($candidate_name);
```

| Result | Action |
|--------|--------|
| No match | CREATE new record |
| Single match | ASK_USER. Confidence = 0.70. Likely the same person but needs confirmation. |
| Multiple matches | ASK_USER. Confidence = 0.50. List all candidates for user to pick. |

**Never auto-merge on name-only match.** Always create a datum_request.

---

## For Companies (entity_type = 'company')

### Tier 1: Domain Match (Strongest — Confidence 1.0)

Domain is a globally unique identifier for companies.

```sql
SELECT id, name, domain, sector, stage
FROM companies
WHERE domain = $candidate_domain;
```

- **If match:** MERGE. Confidence = 1.0. Done.
- **If no match:** Continue to Tier 2.
- **If candidate has no domain:** Skip to Tier 2.

### Tier 2: Exact Name Match (Confidence 0.95)

```sql
SELECT id, name, domain, sector, stage
FROM companies
WHERE LOWER(name) = LOWER($candidate_name);
```

- **If single match:** MERGE. Confidence = 0.95. Done.
- **If multiple matches:** ASK_USER.
- **If no match:** Continue to Tier 3.

### Tier 3: Embedding Similarity (Threshold 0.85 — higher than persons)

Company names are less ambiguous than person names, so the threshold is higher.

```sql
SELECT id, name, domain, sector,
       1 - (embedding <=> $candidate_embedding) as similarity
FROM companies
WHERE embedding IS NOT NULL
  AND id != $candidate_id
  AND 1 - (embedding <=> $candidate_embedding) > 0.85
ORDER BY similarity DESC
LIMIT 5;
```

| Result | Action |
|--------|--------|
| No matches above 0.85 | CREATE new record |
| Single match, similarity > 0.92 | MERGE. Auto-merge. |
| Single match, similarity 0.85-0.92 | ASK_USER. |
| Multiple matches above 0.85 | ASK_USER. |

### Tier 4: Alias Check (Fallback)

Check the aliases array for known alternative names.

```sql
SELECT id, name, domain, aliases
FROM companies
WHERE $candidate_name = ANY(aliases)
   OR LOWER(name) = LOWER($candidate_name);
```

If a match is found in aliases, it is a known variation — MERGE with confidence 0.90.

---

## Merge Protocol

When merging new data into an existing record:

### COALESCE Pattern (never overwrite non-NULL with NULL)

```sql
-- For persons (NOTE: use actual column names from network table)
UPDATE network SET
  current_role = COALESCE($new_role, current_role),
  linkedin = COALESCE($new_linkedin, linkedin),
  email = COALESCE($new_email, email),
  home_base = COALESCE($new_home_base, home_base),
  enrichment_status = $computed_status,
  enrichment_source = 'datum_agent',
  last_enriched_at = NOW(),
  updated_at = NOW()
WHERE id = $existing_id;
```

### Conflict Handling

When a field already has a value AND the new value differs:

```
Existing: company = 'Composio'
New: company = 'Composio Inc.'
```

**If the values are trivially different** (trailing Inc./Ltd., case difference, leading "The"):
→ Keep existing value. Optionally add new value to aliases.

**If the values are meaningfully different** (different company entirely):
→ Create a datum_request:
```sql
INSERT INTO datum_requests (entity_type, entity_id, field_name,
    current_value, suggested_value, merge_type, source_context, status, created_at, updated_at)
VALUES ('person', $id, 'company',
    'Composio', 'Google', 'fill_field',
    'New signal says Google, existing says Composio. Possible job change?',
    'pending', NOW(), NOW());
```

### Array Field Merging

For aliases and other array fields, append unique values:

```sql
UPDATE network SET
  aliases = array_cat(
    COALESCE(aliases, '{}'),
    ARRAY[$new_alias]::TEXT[]
  )
WHERE id = $existing_id
  AND NOT ($new_alias = ANY(COALESCE(aliases, '{}')));
```

---

## Decision Flowchart

```
Entity arrives
  │
  ├─ Has LinkedIn URL? ──yes──> Query Tier 1 ──match──> MERGE (1.0)
  │                                            no match
  │                                               │
  ├─ Has name + company? ──yes──> Query Tier 2 ──match──> MERGE (0.95)
  │                                              no match
  │                                               │
  ├─ Has embedding? ──yes──> Query Tier 3 ──>0.90──> MERGE (auto)
  │                                          0.80-0.90──> ASK_USER
  │                                          multiple──> ASK_USER
  │                                          none──> fall through
  │                                               │
  ├─ Has name only? ──yes──> Query Tier 4 ──match──> ASK_USER (0.50-0.70)
  │                                         no match
  │                                               │
  └─────────────────────────────────────────> CREATE new record
```

---

## Special Cases

### Job Changes (Same Person, Different Company)

LinkedIn URL match (Tier 1) proves it is the same person. Auto-merge and update company/role.
The old company name can be added to aliases or a note.

### Company Rebrands (Same Company, Different Name)

Domain match (Tier 1) proves it is the same company. Auto-merge and update name.
The old name should be added to the aliases array.

### Transliterated / Misspelled Names

Embedding similarity (Tier 3) handles these naturally. "Rahul" and "Raahul" will have high
cosine similarity. The 0.80 threshold is deliberately set to catch these variations.

### Batch Processing

When processing a batch of entities:
1. Process sequentially (not parallel)
2. After creating entity N, entity N+1 may match it
3. The sequential approach ensures correct dedup within the batch
