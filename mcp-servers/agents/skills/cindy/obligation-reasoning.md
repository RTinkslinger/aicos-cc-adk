# Obligation Reasoning — Cindy Skill (LLM-Based)

## Overview

Cindy detects obligations through **LLM reasoning**, not regex patterns. For every
interaction (already cleaned and linked by Datum), Cindy reads the content and reasons
about commitments between Aakash and other participants.

This replaced the regex-based `obligation_extractor.py` and `obligation_detector.py`
which used pattern matching (e.g., "I'll send...", "Will circle back..."). LLM reasoning
catches nuanced obligations that regex misses: implicit commitments, contextual promises,
and obligations embedded in natural conversation flow.

## Two Obligation Types

| Type | Direction | Example |
|------|-----------|---------|
| `I_OWE_THEM` | Aakash committed to do something | "I'll send the deck over" |
| `THEY_OWE_ME` | Someone committed to do something for Aakash | "We'll get back to you with the data room access" |

## 10 Categories

| Category | Description | Examples |
|----------|-------------|---------|
| `send_document` | Send a file, deck, doc, or data | "I'll share the memo", "Will forward the term sheet" |
| `reply` | Respond to a question or email | "Let me get back to you on that", "I'll revert" |
| `schedule` | Set up a meeting or call | "Let's schedule a follow-up", "I'll book time next week" |
| `follow_up` | Check on or follow up on something | "I'll circle back on the IC timeline" |
| `introduce` | Connect two people | "Let me introduce you to Sarah", "I'll loop in our CTO" |
| `review` | Review a document or proposal | "I'll take a look at the deck", "Let me review the terms" |
| `deliver` | Deliver a work product | "We'll prepare the analysis", "I'll draft the memo" |
| `connect` | Facilitate a connection or introduction | "I'll put you in touch with our LP" |
| `provide_info` | Provide information or answer | "I'll check with the team", "Let me find out" |
| `other` | Doesn't fit above categories | "I'll handle it", "Consider it done" |

## LLM Reasoning Process

For each interaction from `interactions WHERE cindy_processed = FALSE`:

### Step 1: Read Interaction Context
```sql
SELECT id, source, summary, raw_data, participants, linked_people, timestamp
FROM interactions WHERE cindy_processed = FALSE ORDER BY timestamp ASC LIMIT 10;
```

### Step 2: Reason About Obligations

For each interaction, think through:

1. **Who said what?** Identify speakers (for email: from_email = speaker; for Granola:
   microphone = Aakash, system = others; for WhatsApp: is_from_me)
2. **What commitments were made?** Look for explicit and implicit promises
3. **Who owes whom?** If Aakash said it, it's I_OWE_THEM. If someone else said it, THEY_OWE_ME.
4. **How confident?** Only create obligations at confidence >= 0.7
5. **When is it due?** Extract explicit dates or infer from context ("next week", "EOD Friday")
6. **What category?** Map to one of the 10 categories above

### Step 3: Dedup Check
Before creating an obligation, check for existing ones:
```sql
SELECT id, description, status FROM obligations
WHERE person_id = $person_id AND status IN ('pending', 'in_progress')
  AND created_at > NOW() - INTERVAL '30 days';
```
If similar obligation exists, skip creating a duplicate.

### Step 4: Create Obligation
```sql
INSERT INTO obligations (
    person_id, obligation_type, category, description,
    due_date, confidence, source_interaction_id, source_quote,
    cindy_priority, status, created_at, updated_at
) VALUES (
    $person_id, $type, $category, $description,
    $due_date, $confidence, $interaction_id, $source_quote,
    $priority, 'pending', NOW(), NOW()
);
```

### Step 5: Auto-Fulfillment Check
When processing a NEW interaction, also check whether it resolves existing obligations:
- Aakash sent email -> may resolve I_OWE reply/send_document obligations
- Person sent document -> may resolve THEY_OWE send_document obligations
- Calendar event created -> may resolve I_OWE schedule obligations

```sql
UPDATE obligations SET
    status = 'fulfilled', fulfilled_at = NOW(),
    fulfilled_method = 'auto_detected',
    fulfilled_evidence = 'Resolved by interaction #' || $interaction_id
WHERE id = $obligation_id AND status IN ('pending', 'in_progress');
```

## Priority Formula (5-Factor)

```
cindy_priority = relationship_tier(0.30) + staleness(0.25) +
                 obligation_type(0.20) + source_reliability(0.15) + recency(0.10)

Where:
  relationship_tier: portfolio founder=1.0, active deal=0.8, network=0.5, unknown=0.2
  staleness: days_overdue/14 (capped at 1.0)
  obligation_type: I_OWE=1.0, THEY_OWE=0.6
  source_reliability: granola=1.0, email=0.8, whatsapp=0.6, calendar=0.5
  recency: 1.0 - (days_old/30) (capped at 0.0)
```

## Do NOT Create Obligations For

- Generic pleasantries ("Let's catch up sometime")
- Vague intentions without specifics ("We should do something together")
- Internal team operations (Z47/DeVC team coordination)
- Obligations already tracked (dedup check first)
- Confidence < 0.7
- Interactions classified as "social" or "operational"

## Strategic Routing

If obligation involves portfolio founder, active deal, or thesis-connected person:
route to Megamind via `cindy_signal` with `signal_type: "obligation_high_priority"`.
