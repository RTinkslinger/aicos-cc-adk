# People Linking — Cindy Skill

## Overview

Cross-surface identity resolution is Cindy's core intelligence. The same person appears
differently across four surfaces: email (email address), WhatsApp (phone number), Granola
(attendee name), Calendar (email + name). Cindy links these into a unified interaction
history per person in the Network DB.

## Identity Signals by Surface

| Surface | Available Identifiers | Reliability | Resolution Path |
|---------|----------------------|-------------|----------------|
| Email | Email address, display name | High (email unique) | Tier 1 (email match) |
| WhatsApp | Phone number, push name | High (phone unique) | Tier 2 (phone match) |
| Granola | Full name (from invite) | Medium (name variations) | Tier 4-5 (name match) |
| Calendar | Email address, display name | High (email unique) | Tier 1 (email match) |

## 6-Tier Resolution Algorithm

Execute tiers in order. Stop at first match.

### Tier 1: Email Match (strongest)

**Works for:** Email, Calendar surfaces

```bash
psql $DATABASE_URL -t -A -c "SELECT id, person_name FROM network WHERE email = 'rahul@composio.dev';"
```

- Confidence: **1.0** (email is globally unique)
- Action: Auto-link, no review needed
- Cross-link: If person has no phone and signal provides one, update network.phone

### Tier 2: Phone Match

**Works for:** WhatsApp surface

```bash
# Normalize phone: strip spaces, ensure + prefix with country code
psql $DATABASE_URL -t -A -c "SELECT id, person_name FROM network WHERE phone = '+919999999999';"
```

- Confidence: **1.0** (phone is globally unique)
- Action: Auto-link, no review needed
- Cross-link: If person has no email and signal provides one, update network.email

### Tier 3: LinkedIn URL Match

**Works for:** Any surface where LinkedIn was previously enriched

```bash
psql $DATABASE_URL -t -A -c "SELECT id, person_name FROM network WHERE linkedin = 'https://linkedin.com/in/rahul-sharma';"
```

- Confidence: **1.0** (LinkedIn URL is unique)
- Action: Auto-link, no review needed
- Rarely used directly by Cindy (LinkedIn URLs come from Datum enrichment)

### Tier 4: Exact Name + Company Match

**Works for:** Granola (name from transcript), any surface with name + company context

```bash
psql $DATABASE_URL -t -A -c "
  SELECT id, person_name, current_role FROM network
  WHERE LOWER(person_name) = LOWER('Rahul Sharma')
    AND LOWER(current_role) ILIKE '%composio%';"
```

- Confidence: **0.95** (name + company is highly reliable)
- Action: Auto-link, note in log
- Company context comes from: meeting title, email domain, message content

### Tier 5: Name-Only Match (lower confidence)

**Works for:** Granola (when no company context available)

```bash
psql $DATABASE_URL -t -A -c "
  SELECT id, person_name, current_role, email, phone FROM network
  WHERE LOWER(person_name) = LOWER('Rahul Sharma');"
```

**Single match:**
- Confidence: **0.80**
- Action: Auto-link, but flag for confirmation via datum request
- Log: "Name-only match for Rahul Sharma → ID 42 (single result, confidence 0.80)"

**Multiple matches:**
- Confidence: **0.50-0.79** (ambiguous)
- Action: Do NOT auto-link. Create datum request with all candidates.
- ```sql
  INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
  VALUES ('datum_person',
    'Ambiguous person match: Rahul Sharma — 3 candidates in Network DB',
    '{"name": "Rahul Sharma", "source": "cindy_granola",
      "candidates": [42, 67, 103],
      "context": "Attendee in Composio Series A Discussion meeting",
      "interaction_id": 456}'::jsonb,
    FALSE, NOW());
  ```

### Tier 6: No Match — Delegate to Datum Agent

**When:** All tiers failed to match

```bash
psql $DATABASE_URL <<'SQL'
INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
VALUES ('datum_person',
  'New person from email: Sarah Lee <sarah@composio.dev>',
  '{"name": "Sarah Lee", "email": "sarah@composio.dev",
    "phone": null, "company": "Composio",
    "source": "cindy_email",
    "context": "CC on email thread: Re: Series A follow-up",
    "interaction_id": 123}'::jsonb,
  FALSE, NOW());
SQL
```

- Datum Agent handles: dedup check (more thorough), web enrichment, record creation
- Cindy does NOT create network records directly for new people
- On next processing cycle, the person should be resolvable via Tier 1-5

## Cross-Surface Linking (Identity Stitching)

After matching a person on one surface, check if the match provides new identifiers
for other surfaces. This progressively builds a complete cross-surface identity map.

### When to Cross-Link

```
IF matched person AND signal provides an email:
    Check: does person have email in Network DB?
    IF NULL: UPDATE network SET email = signal.email WHERE id = person.id

IF matched person AND signal provides a phone:
    Check: does person have phone in Network DB?
    IF NULL: UPDATE network SET phone = signal.phone WHERE id = person.id
```

### Cross-Link SQL Pattern

```bash
# Fill missing email (e.g., Calendar provides email for a person matched via phone in WhatsApp)
psql $DATABASE_URL -c "
  UPDATE network SET email = 'rahul@composio.dev', updated_at = NOW()
  WHERE id = 42 AND email IS NULL;"

# Fill missing phone (e.g., WhatsApp provides phone for a person matched via email in Calendar)
psql $DATABASE_URL -c "
  UPDATE network SET phone = '+919999999999', updated_at = NOW()
  WHERE id = 42 AND phone IS NULL;"
```

**Rule:** Only fill NULL fields. Never overwrite existing non-NULL values. If there's a
conflict (existing value differs from new signal), create a datum request to resolve.

### Linking Record

Every person-interaction link is recorded in `people_interactions`:

```bash
psql $DATABASE_URL <<'SQL'
INSERT INTO people_interactions (person_id, interaction_id, role, surface,
                                  identifier_used, link_confidence)
VALUES (42, 123, 'sender', 'email', 'email:rahul@composio.dev', 1.0)
ON CONFLICT (person_id, interaction_id) DO NOTHING;
SQL
```

### Role Assignment

| Surface | Sender/Organizer | Others |
|---------|-----------------|--------|
| Email | `from` → 'sender' | `to` → 'recipient', `cc` → 'cc' |
| WhatsApp | `is_from_me: true` → 'sender' | Other JIDs → 'participant' |
| Granola | N/A (all are participants) | 'participant' |
| Calendar | `organizer` → 'organizer' | Attendees → 'participant' |

## Resolution Flow by Surface

### Email Resolution
```
1. Parse all email addresses from from/to/cc
2. For each address:
   a. Tier 1: email match → auto-link
   b. Tier 6: no match → datum_person with email + from_name
3. Cross-link: if phone was NULL, no update (email doesn't provide phone)
```

### WhatsApp Resolution
```
1. Parse JIDs → phone numbers
2. For each phone:
   a. Tier 2: phone match → auto-link
   b. If no match, get push name from extraction data
   c. Tier 4-5: name match (using push name)
   d. Tier 6: no match → datum_person with phone + push name
3. Cross-link: if email was NULL and person now matched, no new email (WhatsApp doesn't provide email)
```

### Granola Resolution
```
1. Parse attendee names from Granola metadata
2. Look up the Calendar event for this meeting time window
3. If Calendar event found: use attendee emails for Tier 1 matching (most reliable)
4. If no Calendar match: use names only
   a. Tier 4: name + company (from meeting title/context)
   b. Tier 5: name only
   c. Tier 6: no match → datum_person with name + meeting context
5. Cross-link: Calendar provides email, Granola provides meeting context
```

### Calendar Resolution
```
1. Parse attendee emails and names
2. For each attendee:
   a. Tier 1: email match → auto-link
   b. Tier 4-5: name match (if email not in Network DB)
   c. Tier 6: no match → datum_person with email + name
3. Cross-link: if phone was NULL, no update (Calendar doesn't provide phone)
```

## Learning Loop

As Aakash confirms or corrects identity links via WebFront datum requests:
- Confirmed matches → aliases added to Network DB, improving future matching
- Corrections → identity signals recalibrated
- Over time, the system builds a complete cross-surface identity map

## Common Edge Cases

| Scenario | Handling |
|----------|---------|
| Same person, different email domains (personal vs work) | Tier 4-5 catches via name. Cross-link adds second email context. |
| Name transliterations (Rahul vs Raahul) | Tier 5 uses LOWER exact match. For fuzzy matching, delegate to Datum Agent (embedding similarity). |
| Person changed companies (new role) | Tier 1-2 (email/phone) still matches. Tier 4 may fail if company changed. If Tier 1-2 matches, note role change for Datum to update. |
| Group chat with unknown participants | Resolve what you can. Create batch datum_entity for unknowns. |
| Aakash himself in the participant list | Filter out. Common emails: ak@z47.com, aakash@devc.fund. Phone: known. Skip resolution for Aakash. |
| Generic email (info@company.com) | Do not resolve to a person. Log as company contact. May create company interaction link instead. |

## Confidence Thresholds (Summary)

| Confidence | Action | Review Required |
|------------|--------|----------------|
| 1.00 | Auto-link | No |
| 0.95 | Auto-link + log | No |
| 0.80 | Auto-link + flag | Datum request for confirmation |
| 0.50-0.79 | Do NOT link | Datum request with candidates |
| < 0.50 | Create new | Datum Agent handles creation |
