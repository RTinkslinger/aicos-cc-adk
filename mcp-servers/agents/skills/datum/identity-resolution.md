# Datum Identity Resolution Skill

When to create vs. not create entity records, confidence gating, cross-entity
resolution, and the full decision framework for identity management.
Load this skill when processing new entity signals, resolving ambiguous matches,
or when handling datum_requests.

---

## Core Principle: Confidence Gating

Datum is the **gatekeeper** of data quality. Every entity decision goes through
confidence gating. The threshold determines whether Datum acts autonomously or
escalates to the user.

```
Confidence >= 0.90  →  ACT AUTONOMOUSLY (create, merge, link)
Confidence 0.70-0.89 →  ASK VIA DATUM_REQUEST (create request, do not act)
Confidence < 0.70   →  DO NOT CREATE (log for context, no record)
```

**Exception:** If the entity signal comes directly from Aakash (e.g., "Add Rahul
from Composio"), confidence floor is 0.90 regardless of data completeness.
User-initiated entities always get created.

---

## Decision Matrix: Create vs. Not Create

### When to CREATE a new record

| Condition | Confidence | Action |
|-----------|-----------|--------|
| User explicitly says "add/track/create" | 1.0 | CREATE immediately |
| Name + company + at least one identifier (email/phone/LinkedIn) | 0.95 | CREATE |
| Name + company, no identifier | 0.90 | CREATE, add datum_requests for identifiers |
| Full name + role, no company | 0.85 | ASK (datum_request: "Create record for X?") |
| Full name only, from trusted source (content pipeline, meeting) | 0.80 | ASK |

### When to NOT CREATE

| Condition | Confidence | Action |
|-----------|-----------|--------|
| First name only, no context | 0.30 | LOG only. Do not create. |
| Name contains org suffix (Inc, Labs, Ltd) | 0.20 | It's a company, not a person. Route to company creation. |
| Multiple names in one field ("John and Jane") | 0.40 | SPLIT first. Create each individually. |
| Empty or nonsensical input | 0.00 | REJECT. Write notification. |
| Exact duplicate detected (Tier 1-2 match) | N/A | MERGE, do not create. |

### Edge cases

| Scenario | Decision |
|----------|----------|
| "Rahul" with no other context | Do NOT create. First-name-only records are garbage. |
| "Rahul Sharma, CTO at Composio" from content analysis | CREATE at 0.90. Name + role + company is sufficient. |
| "rahul@composio.dev" with no name | CREATE, extract name from email prefix. Set person_name = "Rahul". Add datum_request for full name. |
| LinkedIn URL only | CREATE skeleton. Scrape LinkedIn for fields (name, role, company, city). |
| Image/screenshot with text | Parse visible text. If name + context extractable, CREATE. If not, REJECT. |

---

## Resolution Hierarchy

When resolving whether an incoming entity matches an existing record, Datum
uses a strict hierarchy. Each tier is tried in order. Stop at first match.

### Person Resolution (6 Tiers)

```
TIER 1: Email match          → confidence 1.0, auto-link
TIER 2: Phone match           → confidence 1.0, auto-link
TIER 3: LinkedIn URL match    → confidence 1.0, auto-link
TIER 4: Exact name + company  → confidence 0.95, auto-link
TIER 5: Name-only match
  - Single result             → confidence 0.80, auto-link + flag
  - Multiple results          → confidence 0.50-0.79, ASK via datum_request
TIER 6: No match              → CREATE new record (if confidence gating passes)
```

### Company Resolution (4 Tiers)

```
TIER 1: Domain match          → confidence 1.0, auto-merge
TIER 2: Exact name match
  - Single result             → confidence 0.95, auto-merge
  - Multiple results          → ASK via datum_request
TIER 3: Embedding similarity
  - > 0.92                    → auto-merge
  - 0.85-0.92                 → ASK via datum_request
TIER 4: Alias check           → confidence 0.90, auto-merge
No match                      → CREATE new record
```

---

## SQL Functions for Identity Resolution

### datum_resolve_pseudo_ids()

Fixes broken `pg:` references in actions_queue. These occur when actions reference
companies by Postgres ID instead of Notion page ID.

```bash
psql $DATABASE_URL -c "SELECT * FROM datum_resolve_pseudo_ids();"
```

**Returns:** `(action_id INTEGER, old_company_id TEXT, new_company_id TEXT, company_name TEXT, resolution_method TEXT)`

**Resolution methods:**
- `pg_id_lookup` — Company found, had a notion_page_id, reference fixed
- `generated_uuid` — Company found but had no notion_page_id, UUID generated, reference fixed

Run this whenever `datum_data_quality_check()` reports `pseudo_id_count > 0`.

### datum_company_name_deduplicator()

See `enrichment.md` for full details. Returns duplicate company candidates for
resolution.

---

## Cross-Surface Identity Stitching

After matching a person on one surface, Datum fills gaps in their record from
the new surface's data.

### Stitching Rules

| If matched via | And signal provides | Fill if NULL |
|----------------|-------------------|-------------|
| Email (Tier 1) | Phone | network.phone |
| Phone (Tier 2) | Email | network.email |
| LinkedIn (Tier 3) | Email, phone | network.email, network.phone |
| Name+Company (Tier 4) | Email, phone, LinkedIn | All NULL fields |

### SQL Pattern

```sql
-- Fill missing email for a phone-matched person
UPDATE network SET email = $new_email, updated_at = NOW()
WHERE id = $person_id AND email IS NULL;

-- Fill missing phone for an email-matched person
UPDATE network SET phone = $new_phone, updated_at = NOW()
WHERE id = $person_id AND phone IS NULL;

-- Fill missing LinkedIn
UPDATE network SET linkedin = $new_linkedin, updated_at = NOW()
WHERE id = $person_id AND (linkedin IS NULL OR linkedin = '');
```

**NEVER overwrite non-NULL values.** If the new value conflicts with the existing
value, create a datum_request to let the user decide.

---

## Datum Request Lifecycle

Datum requests are the escalation mechanism. When Datum cannot make a confident
decision, it creates a request for user review.

### Creating Requests

```sql
-- Check for existing pending request first (ALWAYS)
SELECT id FROM datum_requests
WHERE entity_type = $type AND entity_id = $id
  AND field_name = $field AND status = 'pending';

-- If none exists, create
INSERT INTO datum_requests (
  entity_type, entity_id, field_name, source_context,
  suggested_value, suggestion_confidence, suggestion_source,
  merge_type, status, created_at, updated_at
) VALUES (
  'person', $id, 'email', 'Inferred from company domain',
  'rahul@composio.dev', 0.72, 'domain_inference',
  'fill_field', 'pending', NOW(), NOW()
);
```

### Request Types

| merge_type | When Used |
|------------|-----------|
| `fill_field` | A field is NULL and Datum has a suggestion |
| `confirm_merge` | Fuzzy match found, need user to confirm same entity |
| `pick_match` | Multiple fuzzy matches, user picks the right one |

### Processing Answered Requests

When the user answers a datum_request (via WebFront or CAI):

```sql
-- Check for answered requests
SELECT id, entity_type, entity_id, field_name, answer, answered_by
FROM datum_requests
WHERE status = 'answered'
ORDER BY answered_at ASC;
```

For each answered request:

1. **fill_field answers:**
   - If answer matches suggestion: `UPDATE network SET $field = $answer WHERE id = $entity_id`
   - If answer is different: use the user's answer (user always wins)
   - If answer is "skip": mark request as `skipped`

2. **confirm_merge answers:**
   - If "yes": execute the merge (COALESCE pattern)
   - If "no": keep as separate records, add alias to prevent re-flagging

3. **pick_match answers:**
   - User picks an ID: merge into that record
   - User says "none": create new record

After processing:
```sql
UPDATE datum_requests SET status = 'processed', updated_at = NOW()
WHERE id = $request_id;
```

---

## Confidence Calibration

These confidence values are calibrated from real-world data quality observations:

| Signal | Confidence | Rationale |
|--------|-----------|-----------|
| Email exact match | 1.0 | Email is globally unique |
| Phone exact match | 1.0 | Phone is globally unique |
| LinkedIn URL exact match | 1.0 | LinkedIn URL is globally unique |
| Name + company exact match | 0.95 | Very high but not perfect (common names at large companies) |
| Name-only single match | 0.80 | Likely correct but risks exist (common names) |
| Name-only multiple matches | 0.50-0.79 | Ambiguous — must ask user |
| Domain inference (name@company.domain) | 0.70-0.75 | Common pattern but not guaranteed |
| Web search enrichment | 0.60-0.80 | Depends on result quality |
| Embedding similarity > 0.90 | 0.90 | Auto-merge safe |
| Embedding similarity 0.80-0.90 | 0.80 | Ask user |

---

## Collaboration with Cindy

Datum and Cindy have a clean separation of concerns:

| Responsibility | Owner |
|---------------|-------|
| People resolution (name → ID) | **Datum** |
| Entity creation (new records) | **Datum** |
| Entity enrichment (fill fields) | **Datum** |
| Deduplication | **Datum** |
| Entity graph (entity_connections) | **Datum** |
| Interaction staging → clean interactions | **Datum** |
| Obligation detection | **Cindy** |
| Signal extraction (LLM reasoning) | **Cindy** |
| Action creation from communications | **Cindy** |
| Context gap detection | **Cindy** |

**Data flow:** Fetchers → `interaction_staging` → Datum processes (resolves people,
links entities) → writes to `interactions` → Cindy reads `interactions WHERE
cindy_processed = FALSE` → Cindy reasons via LLM.

Datum never does LLM reasoning about communication content. Cindy never creates
or modifies entity records directly.

---

## Anti-Patterns (Identity-Specific)

1. **Never create first-name-only records** without identifiers. These become
   unresolvable garbage.
2. **Never auto-merge below 0.90 confidence.** Always create a datum_request.
3. **Never overwrite non-NULL fields.** Use COALESCE. If values conflict, ask.
4. **Never guess LinkedIn URLs.** Guessed URLs fail silently and corrupt data.
5. **Never process the same datum_request twice.** Check status before acting.
6. **Never create duplicate datum_requests.** Check before creating.
7. **Never skip the dedup check.** Run the full hierarchy before any INSERT.
8. **Never trust embedding similarity alone.** Embeddings are Tier 3 — only
   used when Tier 1-2 fail. And auto-merge threshold is 0.90, not 0.80.
