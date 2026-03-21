# Calendar & Gap Detection — Cindy Skill

## Overview

Calendar is Cindy's **anchor surface**. It defines what meetings ARE happening. Cindy
checks whether the other surfaces (Granola, Email, WhatsApp) have provided context for
each meeting. When no surface has data, Cindy creates a context gap.

## Calendar Event Structure

Events arrive via two paths:

### Path A: Calendar API Incremental Sync

```json
{
  "type": "cindy_calendar",
  "content": "Calendar event batch: 5 new/updated events",
  "metadata": {
    "events": [
      {
        "event_id": "gcal_abc123",
        "ical_uid": "uid@google.com",
        "title": "Composio Series A Discussion",
        "start_time": "2026-03-21T10:00:00Z",
        "end_time": "2026-03-21T10:45:00Z",
        "attendees": [
          {"email": "rahul@composio.dev", "name": "Rahul Sharma", "response": "accepted"},
          {"email": "sarah@composio.dev", "name": "Sarah Lee", "response": "tentative"}
        ],
        "location": "Google Meet",
        "description": "Discussion about Series A terms...",
        "organizer": "sneha@z47.com",
        "conference_uri": "https://meet.google.com/abc-def-ghi",
        "sequence": 0,
        "status": "confirmed"
      }
    ],
    "sync_token": "CPjA..."
  }
}
```

### Path B: .ics from Email

Parsed from email attachments via `icalendar` library. Same fields extracted.

## Calendar Processing Steps

### 1. Parse and Store

```bash
psql $DATABASE_URL <<'SQL'
INSERT INTO interactions (source, source_id, thread_id, participants, linked_people,
                          summary, raw_data, timestamp, duration_minutes)
VALUES ('calendar', 'gcal_abc123', NULL,
        ARRAY['rahul@composio.dev', 'sarah@composio.dev', 'sneha@z47.com'],
        ARRAY[42, 1],
        'Composio Series A Discussion — 45 min with Rahul Sharma, Sarah Lee',
        '{"title": "Composio Series A Discussion", "location": "Google Meet",
          "attendees": [...], "organizer": "sneha@z47.com"}'::jsonb,
        '2026-03-21T10:00:00Z', 45)
ON CONFLICT (source, source_id) DO UPDATE SET
    participants = EXCLUDED.participants,
    linked_people = EXCLUDED.linked_people,
    raw_data = EXCLUDED.raw_data;
SQL
```

### 2. Attendee Resolution

For each attendee, resolve via email (Calendar provides email addresses):

```bash
psql $DATABASE_URL -t -A -c "SELECT id, person_name FROM network WHERE email = 'rahul@composio.dev';"
```

Calendar is the best surface for email-based resolution since every attendee has an email.

### 3. Event Change Detection

| Sequence | Meaning | Action |
|----------|---------|--------|
| 0 | New event | Full processing: resolve attendees, gap detection or context assembly |
| > 0 | Updated event | Re-resolve attendees (new people may have been added), update interaction |
| status = 'cancelled' | Cancelled event | Update interaction, skip gap detection, resolve existing gap |

## Context Gap Detection Algorithm

### When to Run

Gap detection runs for **past events** (last 24 hours, at least 30 minutes after meeting end).

```sql
-- Get all calendar events from the past 24 hours that have ended
SELECT i.id, i.source_id, i.summary, i.timestamp, i.participants, i.linked_people,
       (i.raw_data->>'end_time')::timestamptz as end_time
FROM interactions i
WHERE i.source = 'calendar'
  AND i.timestamp > NOW() - INTERVAL '24 hours'
  AND i.timestamp < NOW() - INTERVAL '30 minutes'
```

### Surface Coverage Check

For each calendar event, check all three observation surfaces:

#### Granola Check (time window match)

```sql
SELECT id FROM interactions
WHERE source = 'granola'
  AND timestamp BETWEEN $event_start - INTERVAL '15 minutes'
                     AND $event_end + INTERVAL '15 minutes';
```

Score: 0.35 if found, 0.0 if not.

#### Email Check (attendee overlap, last 48h)

```sql
SELECT id FROM interactions
WHERE source = 'email'
  AND timestamp > $event_start - INTERVAL '48 hours'
  AND linked_people && $attendee_ids;
```

Score: 0.25 if found, 0.0 if not.

#### WhatsApp Check (attendee overlap, last 48h)

```sql
SELECT id FROM interactions
WHERE source = 'whatsapp'
  AND timestamp > $event_start - INTERVAL '48 hours'
  AND linked_people && $attendee_ids;
```

Score: 0.15 if found, 0.0 if not.

#### Network DB Check (known people)

```sql
SELECT COUNT(*) FROM unnest($attendee_ids) aid
WHERE aid IN (SELECT id FROM network WHERE enrichment_status IN ('partial', 'enriched', 'verified'));
```

Score: 0.25 * (matched_enriched / total_attendees)

### Context Richness Scoring

```
context_richness = granola_score + email_score + network_score + whatsapp_score

Weights:
  Granola transcript:  0.35
  Email threads:       0.25
  Network DB history:  0.25
  WhatsApp:            0.15
```

### Gap Classification and Action

| Richness | Event Timing | Gap Status | Action |
|----------|-------------|-----------|--------|
| < 0.3 | Past, within 24h | `pending` (urgent) | Create gap + notification |
| < 0.3 | Future, within 24h | `pending` (urgent) | Create gap + urgent notification |
| < 0.3 | Future, 24-48h | `pending` (planned) | Create gap, queue context request |
| 0.3 - 0.6 | Any | `partial` | Create gap with available sources noted |
| > 0.6 | Any | No gap | Meeting well-covered |

### Auto-Skip Rules

Skip gap detection entirely for:

```sql
-- Internal meetings: all attendees are @z47.com or @devc.fund
-- Check: if ALL attendee emails end in @z47.com or @devc.fund
SELECT EVERY(email LIKE '%@z47.com' OR email LIKE '%@devc.fund')
FROM unnest($attendee_emails) email;
```

```sql
-- Short meetings: duration < 15 minutes
SELECT EXTRACT(EPOCH FROM ($event_end - $event_start)) / 60 < 15;
```

### Gap Creation

```sql
INSERT INTO context_gaps (calendar_event_id, calendar_interaction_id, meeting_title,
                           meeting_date, attendees, missing_sources, available_sources,
                           context_richness, status)
VALUES ('gcal_abc123', 456, 'Composio Series A Discussion',
        '2026-03-20T10:00:00Z', ARRAY['Rahul Sharma', 'Sarah Lee'],
        ARRAY['granola', 'email', 'whatsapp'], ARRAY[]::TEXT[],
        0.15, 'pending')
ON CONFLICT (calendar_event_id) DO UPDATE SET
    missing_sources = EXCLUDED.missing_sources,
    available_sources = EXCLUDED.available_sources,
    context_richness = EXCLUDED.context_richness,
    status = CASE
        WHEN EXCLUDED.context_richness >= 0.6 THEN 'filled'
        WHEN EXCLUDED.context_richness >= 0.3 THEN 'partial'
        ELSE context_gaps.status  -- keep existing status if still low
    END;
```

### Retroactive Gap Fill

When a new interaction arrives (Granola transcript, email, WhatsApp), re-check existing
pending gaps:

```sql
-- Find pending gaps where this new interaction might provide coverage
SELECT cg.id, cg.calendar_event_id, cg.meeting_date, cg.attendees
FROM context_gaps cg
WHERE cg.status IN ('pending', 'partial')
  AND cg.meeting_date BETWEEN $new_interaction_start - INTERVAL '1 hour'
                          AND $new_interaction_start + INTERVAL '1 hour';
```

If the new interaction matches (by time + attendee overlap), update the gap.

### Post-Meeting Gap Detection

For past meetings with no Granola transcript after 30 minutes:

```sql
UPDATE context_gaps SET status = 'post_meeting_gap'
WHERE status = 'pending'
  AND meeting_date < NOW() - INTERVAL '30 minutes'
  AND NOT EXISTS (
    SELECT 1 FROM interactions
    WHERE source = 'granola'
      AND timestamp BETWEEN context_gaps.meeting_date - INTERVAL '15 minutes'
                        AND context_gaps.meeting_date + INTERVAL '2 hours'
  );
```

Write notification: "Meeting ended but no transcript. How did it go?"

## Pre-Meeting Context Assembly

For **upcoming events** (next 48 hours), assemble context instead of detecting gaps.

### Assembly Steps

```
For each attendee:
  1. Resolve person → Network DB (email match from calendar)
  2. Get recent interactions:
     SELECT i.source, i.summary, i.timestamp
     FROM interactions i JOIN people_interactions pi ON pi.interaction_id = i.id
     WHERE pi.person_id = $person_id AND i.timestamp > NOW() - INTERVAL '30 days'
     ORDER BY i.timestamp DESC LIMIT 5
  3. Get open actions:
     SELECT action, status FROM actions_queue
     WHERE (action ILIKE '%person_name%' OR action ILIKE '%company%')
       AND status IN ('Proposed', 'Accepted')
  4. Get thesis connections:
     SELECT name, conviction FROM thesis_threads
     WHERE status IN ('Active', 'Exploring')
```

### Context Assembly JSON

```json
{
  "meeting_title": "Composio Series A Discussion",
  "meeting_time": "2026-03-21T10:00:00Z",
  "attendees": [
    {
      "name": "Rahul Sharma",
      "role": "CTO at Composio",
      "archetype": "Founder",
      "last_interaction": {"date": "2026-03-18", "surface": "email", "summary": "Term sheet review"},
      "interaction_count_30d": 14,
      "open_actions": ["Follow up on term sheet review"],
      "thesis_connections": ["Agentic AI Infrastructure"],
      "recent_summaries": ["Discussed competitive landscape", "Term sheet review email"]
    }
  ],
  "company_context": {
    "name": "Composio",
    "stage": "Series A",
    "thesis": "Agentic AI Infrastructure",
    "conviction": "Evolving Fast"
  }
}
```

Store in `interactions.context_assembly` for the calendar event record.
Write notification: "Pre-meeting brief ready for Composio Series A Discussion"

## Gap Resolution Paths

### 1. Automatic Fill (retroactive source arrival)

```sql
UPDATE context_gaps SET
    status = 'filled',
    filled_by = 'automatic',
    filled_sources = ARRAY['granola'],
    filled_at = NOW()
WHERE calendar_event_id = 'gcal_abc123'
  AND status IN ('pending', 'partial');
```

### 2. User Input via WebFront

Orchestrator receives `cindy_gap_filled` inbox message. Cindy processes the user's
structured notes through the signal extraction pipeline.

### 3. User Skip

Gap marked as `skipped` directly by WebFront Server Action. No Cindy processing needed.
