# Signal Extraction — Cindy Skill (LLM-Based)

## Overview

Cindy extracts strategic signals from interactions through **LLM reasoning**, not regex
patterns. For every interaction (already cleaned and linked by Datum), Cindy reads the
content and identifies actionable intelligence for the AI CoS system.

This replaced regex-based `extract_action_items()`, `extract_deal_signals()`, and
`extract_thesis_signals()` functions that used simple pattern matching. LLM reasoning
catches nuanced signals that regex misses: contextual deal intelligence, subtle thesis
confirmations/disconfirmations, and relationship dynamics.

## Signal Types

### 1. Action Items

Explicit commitments, follow-ups, scheduled next steps, requests.

**LLM reasoning prompt:** "What specific actions were committed to in this interaction?
Who is responsible? What is the timeline?"

**Write to:** `actions_queue` with appropriate source attribution:

```sql
INSERT INTO actions_queue (action, action_type, priority, status, assigned_to, source,
                           reasoning, thesis_connection, created_at, updated_at)
VALUES ($action_text, $action_type, $priority, 'Proposed', $assigned_to,
        'Cindy-' || $surface, $reasoning, $thesis_connection, NOW(), NOW());
```

**Source attribution rules:**
- Email interactions -> `source = 'Cindy-Email'`
- Granola transcripts -> `source = 'Cindy-Meeting'`
- WhatsApp conversations -> `source = 'Cindy-WhatsApp'`
- Calendar events -> `source = 'Cindy-Calendar'`

### 2. Thesis Signals

Evidence that moves conviction on an investment thesis (up or down).

**LLM reasoning prompt:** "Does this interaction contain evidence that confirms or
challenges any of Aakash's active thesis threads? What is the signal strength?"

**Active thesis threads (query before reasoning):**
```sql
SELECT name, core_thesis, status, conviction FROM thesis_threads
WHERE status IN ('Active', 'Exploring');
```

**Signal structure:**
```json
{
    "thesis_thread": "Agentic AI Infrastructure",
    "signal": "Composio seeing 10x growth in API calls",
    "strength": "strong",
    "direction": "confirming"
}
```

**Write to:** `cindy_signal` in `cai_inbox` for Megamind routing (only strong signals):

```sql
INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
VALUES ('cindy_signal', $summary,
        json_build_object(
            'signal_type', 'thesis_conviction',
            'strength', $strength,
            'thesis_connections', $thesis_names,
            'interaction_id', $interaction_id
        )::jsonb, FALSE, NOW());
```

### 3. Deal Signals

Deal-related intelligence: term sheets, valuations, fundraising, financials, diligence.

**LLM reasoning prompt:** "Does this interaction contain deal-related intelligence?
What stage is the deal? What specific deal data points were mentioned?"

**Signal types:** term_sheet, valuation, fundraise, financials, diligence, competitive,
pipeline_movement

**Write to:** `cindy_signal` in `cai_inbox` with `signal_type: "deal_signal"`

### 4. Relationship Signals

Interaction frequency, warmth, engagement level, rapport indicators.

**LLM reasoning prompt:** "What is the relationship temperature? Is there cooling
(high-value person + long gap)? Is there strengthening (increased interaction frequency)?
Any notable rapport changes?"

**Signal structure:**
```json
{
    "warmth": "high",
    "engagement": "active",
    "follow_up_needed": true,
    "relationship_change": "strengthening"
}
```

**Write to:** `relationship_signals` JSONB column on the interaction record

### 5. Context Assembly (Calendar Events)

For upcoming calendar events, assemble pre-meeting context.

**Query per-attendee context:**
```sql
-- Recent interactions with attendee
SELECT source, summary, timestamp FROM interactions
JOIN people_interactions ON ... WHERE person_id = $attendee_id
ORDER BY timestamp DESC LIMIT 5;

-- Open actions related to attendee
SELECT action, status FROM actions_queue
WHERE action ILIKE '%' || $attendee_name || '%' AND status IN ('Proposed', 'Accepted');

-- Thesis connections
SELECT name, conviction FROM thesis_threads
WHERE status IN ('Active', 'Exploring');
```

**Write to:** `context_assembly` JSONB column on the calendar interaction record

## Strategic Signal Routing Criteria

Only route high-value signals to Megamind. Not every interaction generates a strategic signal.

| Signal Type | Threshold | Route |
|-------------|-----------|-------|
| Deal signal | Any mention of terms, valuation, funding | `cindy_signal` to Megamind |
| Thesis conviction change | Strong signal (confirming or challenging) | `cindy_signal` to Megamind |
| Portfolio risk | Any portfolio company concern | `cindy_signal` to Megamind |
| Relationship cooling | High-value person + no interaction 21+ days | `cindy_signal` to Megamind |
| Meeting cluster | 3+ meetings with same company in 7 days | `cindy_signal` to Megamind |
| Action item | Any explicit commitment | `actions_queue` directly |

## Interaction Enrichment

After reasoning, update the interaction record with extracted intelligence:

```sql
UPDATE interactions SET
    action_items = $extracted_actions,
    thesis_signals = $thesis_signals::jsonb,
    deal_signals = $deal_signals::jsonb,
    relationship_signals = $relationship_signals::jsonb,
    cindy_processed = TRUE,
    updated_at = NOW()
WHERE id = $interaction_id;
```

## Surface-Specific Reasoning Guidance

### Email
- `extracted_text` is the reply content only (no quoted history) — focus signal extraction here
- Thread context from `thread_id` — consider conversation arc, not just latest message
- Attachment metadata may contain high-signal indicators (deck, term sheet, data room)

### Granola (Meeting Transcripts)
- Full transcript available in `raw_data` — richest signal source
- Speaker attribution: `source: "microphone"` = Aakash, `source: "system"` = others
- Use Granola's `ai_summary` and `action_items` as starting points, but also reason independently
- Apply IDS methodology lens: thesis signals, conviction changes, key questions addressed

### WhatsApp
- Only metadata available (message counts, timestamps, media types) — NO raw text
- Signal extraction is LIMITED to what Datum staged in metadata
- Focus on: interaction frequency, response patterns, group dynamics
- NEVER attempt to access raw message text

### Calendar
- Focus on: attendee resolution, pre-meeting context assembly, gap detection
- Past events (24h): check for coverage gaps across other surfaces
- Future events (48h): assemble pre-meeting briefs
