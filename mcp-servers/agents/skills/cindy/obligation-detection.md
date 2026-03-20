# Obligation Detection — Cindy Skill

Cindy scans every processed interaction for obligation signals. This is a MANDATORY
post-processing step that runs AFTER standard signal extraction (action items, thesis
signals, relationship signals) on every surface.

---

## What Is an Obligation

A commitment between Aakash and another person. NOT a task, NOT an action item.
An obligation tracks a promise made — either by Aakash or to Aakash.

Two types:
- **I_OWE_THEM**: Aakash committed to do something for someone
- **THEY_OWE_ME**: Someone committed to do something for Aakash

---

## Detection Patterns by Surface

### Email

**Explicit I_OWE_THEM (Aakash committed):**
| Pattern | Category | Example |
|---------|----------|---------|
| "I'll send you..." / "Let me send..." | send_document | "I'll send you the term sheet by Friday" |
| "I'll get back to you on..." / "Let me circle back..." | reply | "Let me get back to you on the valuation question" |
| "I will follow up..." / "Will circle back..." | follow_up | "Will circle back next week on the IC timeline" |
| "Let me introduce you to..." / "I'll connect you with..." | introduce | "Let me introduce you to our cybersecurity portfolio founder" |
| "I'll review..." / "Let me look at..." | review | "I'll review the deck this weekend" |
| "I'll schedule..." / "Let me set up..." | schedule | "Let me set up a call with our IC" |
| First person future tense + action verb | (varies) | "I will check with the team and revert" |

**Explicit THEY_OWE_ME (someone committed to Aakash):**
| Pattern | Category | Example |
|---------|----------|---------|
| "I'll send you..." (from someone else) | send_document | "I'll send you the updated cap table tomorrow" |
| "Could you send me..." (Aakash requesting) | send_document | "Could you send me the latest financials?" |
| "Will get back to you..." (from someone else) | reply | "Will get back to you on the follow-on terms" |
| "[Name] to send..." / "[Name] will..." | (varies) | "Rahul to send pitch deck next week" |

**Implied I_OWE_THEM:**
- Unanswered email (48h+) where last message was from them
- Meeting happened, no follow-up email within 48h (for important contacts)

**Implied THEY_OWE_ME:**
- Unanswered email (48h+) where last message was from Aakash
- Aakash sent a question ("?") with no response after 48h

### WhatsApp

Same patterns as email, adapted for conversational format:
- "Will share..." / "Let me check and get back..."
- "Sending you..." / "I'll forward..."
- Unread messages from important contacts (portfolio founders) older than 24h
- Messages Aakash sent containing "?" with no reply after 48h

### Granola (Meeting Transcripts)

Richest source of obligations — people make verbal commitments in meetings.

**Speaker identification:**
- `source: "microphone"` = Aakash speaking -> I_OWE_THEM
- `source: "system"` = other participant speaking -> THEY_OWE_ME

**Detection logic:**
```
FOR each utterance in transcript:
    IF utterance contains future_commitment_pattern:
        IF utterance.source == "microphone":
            create_obligation(type='I_OWE_THEM', source_quote=utterance.text)
        ELIF utterance.source == "system":
            create_obligation(type='THEY_OWE_ME', source_quote=utterance.text)

FOR each action_item in meeting.action_items:
    IF action_item assigned to Aakash:
        create_obligation(type='I_OWE_THEM')
    ELSE:
        create_obligation(type='THEY_OWE_ME')
```

**Mutual obligations:** "Let's schedule a follow-up" -> create TWO records:
- I_OWE (Aakash takes scheduling responsibility, he has the EA)
- THEY_OWE (the other party's share of the mutual commitment)

### Calendar

Calendar triggers obligation inference rather than direct detection:
- External meeting happened but no follow-up in email/WhatsApp within 48h -> implied I_OWE
- Only for: portfolio founders, deal-flow contacts, thesis-relevant people
- Skip: internal meetings, casual coffees, large group events

---

## Obligation Record Schema

```sql
INSERT INTO obligations (
    person_id, person_name, person_role,
    obligation_type, description, category,
    source, source_interaction_id, source_quote, detection_method,
    detected_at, due_date, due_date_source,
    cindy_priority, cindy_priority_factors,
    context
) VALUES (
    $person_id, $person_name, $person_role,
    $type, $description, $category,
    $surface, $interaction_id, $quote, $detection_method,
    NOW(), $due_date, $due_date_source,
    $computed_priority, $priority_factors_json,
    $context_json
);
```

### Categories
`send_document` | `reply` | `schedule` | `follow_up` | `introduce` | `review` | `deliver` | `connect` | `provide_info` | `other`

### Detection Methods
- `explicit` — clear verbal/written commitment ("I'll send you the deck")
- `implied` — inferred from behavior (unanswered email, meeting etiquette)
- `manual` — Aakash created it manually

---

## Cindy Priority Formula (0.0 - 1.0)

```
cindy_priority =
    relationship_tier_weight * 0.30 +
    staleness_weight         * 0.25 +
    obligation_type_weight   * 0.20 +
    source_reliability_weight * 0.15 +
    recency_weight           * 0.10
```

### Factor 1: Relationship Tier (30%)
| Tier | Weight |
|------|--------|
| Portfolio founder | 1.0 |
| Active deal contact | 0.9 |
| GP/Partner (other fund) | 0.85 |
| Thesis-connected person | 0.75 |
| DeVC Collective member | 0.7 |
| Network contact (known) | 0.5 |
| Cold/new contact | 0.3 |

### Factor 2: Staleness (25%)
| Days outstanding | Weight |
|-----------------|--------|
| 0-2 | 0.2 |
| 3-5 | 0.5 |
| 5-7 | 0.7 |
| 7-10 | 0.85 |
| 10-14 | 0.95 |
| 14+ | 1.0 |

### Factor 3: Obligation Type (20%)
- I_OWE_THEM base: 0.8 (multiplied by category weight below)
  - send_document: 0.9, reply: 0.85, introduce: 0.8, schedule: 0.75, review: 0.7, follow_up: 0.65
- THEY_OWE_ME: 0.5

### Factor 4: Source Reliability (15%)
| Method | Weight |
|--------|--------|
| explicit | 1.0 |
| manual | 0.9 |
| implied | 0.5 |

### Factor 5: Recency (10%)
| Age | Weight |
|-----|--------|
| Today | 1.0 |
| 1-3 days | 0.8 |
| 3-7 days | 0.6 |
| 7+ days | 0.4 |

Store the computed factors in `cindy_priority_factors` JSONB:
```json
{
  "relationship_tier": "portfolio_founder",
  "relationship_tier_weight": 0.30,
  "staleness_weight": 0.25,
  "obligation_type_weight": 0.144,
  "source_reliability_weight": 0.15,
  "recency_weight": 0.08,
  "computed_at": "2026-03-20T10:00:00Z"
}
```

---

## Deduplication

Before creating any obligation, check for existing obligations with the same person:

```sql
SELECT id, description, status, detected_at
FROM obligations
WHERE person_id = $person_id
  AND status IN ('pending', 'overdue', 'snoozed', 'escalated')
  AND (
    source_interaction_id = $interaction_id
    OR description ILIKE '%' || $key_phrase || '%'
  )
LIMIT 5;
```

Rules:
- Same interaction ID -> skip (already detected)
- Similar description from different interaction -> UPDATE existing with new evidence
- Different description from same person -> create new record

---

## Auto-Fulfillment Detection

When processing a NEW interaction, check whether it resolves any existing obligations
with the same person:

```sql
SELECT id, obligation_type, category, description
FROM obligations
WHERE person_id = $person_id
  AND status IN ('pending', 'overdue')
LIMIT 10;
```

### Resolution Signals

| Existing Obligation | New Interaction Signal | Result |
|--------------------|-----------------------|--------|
| I_OWE send_document | Aakash sent email with attachment to this person | fulfilled |
| I_OWE reply | Aakash sent email/message to this person's thread | fulfilled |
| I_OWE schedule | Calendar event created with this person | fulfilled |
| I_OWE introduce | Email with both parties included | fulfilled |
| THEY_OWE send_document | Person sent email with attachment to Aakash | fulfilled |
| THEY_OWE reply | Person replied to Aakash's message | fulfilled |
| THEY_OWE deliver | Relevant document/info received from person | fulfilled |

### Fulfillment Update

```sql
UPDATE obligations SET
    status = 'fulfilled',
    fulfilled_at = NOW(),
    fulfilled_method = 'auto_detected',
    fulfilled_evidence = 'Resolved by interaction #' || $new_interaction_id || ' — ' || $evidence_summary,
    status_changed_at = NOW(),
    updated_at = NOW()
WHERE id = $obligation_id;
```

---

## Megamind Routing

Route to Megamind (via `cindy_signal` in `cai_inbox`) when:
- Person is portfolio founder
- Person is connected to active deal (deal_status = active pipeline)
- Person is connected to Active thesis
- Obligation is overdue (> staleness threshold)
- Cindy priority > 0.7
- I_OWE_THEM + person relationship_tier >= GP/Partner

Do NOT route when:
- Person is new contact with no relationship history
- THEY_OWE_ME with staleness < 7 days
- Social WhatsApp conversation

```sql
INSERT INTO cai_inbox (type, content, metadata, processed, created_at)
VALUES ('cindy_signal', 'Obligation priority assessment request',
        '{"signal_type": "obligation_priority",
          "obligation_id": $obligation_id,
          "person_id": $person_id,
          "obligation_type": "$type",
          "cindy_priority": $priority,
          "description": "$description"}'::jsonb,
        FALSE, NOW());
```

---

## Confidence Threshold

Only create obligations with confidence >= 0.7.

Do NOT create obligations for:
- Generic pleasantries ("Let's catch up sometime")
- Vague intentions without specifics ("We should do something together")
- Internal team operations (Z47/DeVC team coordination)
- Obligations already tracked (check dedup first)

---

## ACK Addition

After obligation detection, add to every ACK:
```
- [count] obligations detected ([I-owe count] I-owe, [they-owe count] they-owe)
- [count] obligations auto-fulfilled
```

Example:
```
ACK: Processed 1 email interaction.
- Email: 1 interaction processed (thread: Re: Series A follow-up)
- 3 people linked (2 matched, 1 new sent to Datum)
- 1 action item extracted
- 1 thesis signal identified
- Context gaps: 0 created, 0 filled
- 2 obligations detected (1 I-owe, 1 they-owe)
- 0 obligations auto-fulfilled
```

---

## Staleness Thresholds

| Obligation Type | Warning (days) | Overdue (days) | Escalation (days) |
|----------------|---------------|----------------|-------------------|
| I_OWE_THEM (explicit) | 3 | 5 | 10 |
| I_OWE_THEM (implied) | 5 | 7 | 14 |
| THEY_OWE_ME (explicit) | 5 | 10 | 21 |
| THEY_OWE_ME (implied) | 7 | 14 | 30 |

I_OWE obligations are more urgent (Aakash's reputation at stake).
THEY_OWE obligations can wait longer (nudging too early is pushy).
Explicit commitments are more urgent than implied ones.
