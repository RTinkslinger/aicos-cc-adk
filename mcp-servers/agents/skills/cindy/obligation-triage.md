# Obligation Triage — Cindy Agent Skill

## Purpose

This skill teaches Cindy how to use the SQL obligation management functions to triage,
audit, action, and draft nudge messages for obligations. These functions run in Postgres
and are called via `psql $DATABASE_URL`.

---

## Available SQL Functions

### 1. `cindy_obligation_full_context(p_obligation_id integer) -> jsonb`

**What it does:** Returns the complete context for a single obligation — the obligation
record, the person's network profile, the source interaction, recent interactions with
that person, related open obligations, and the thesis/company connections.

**When to use:** Before reasoning about whether to escalate, fulfill, or dismiss an
obligation. This is the "full picture" function — call it before any obligation decision.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_obligation_full_context(42);" | jq .
```

**Return structure:**
```json
{
  "obligation": { "id", "type", "category", "description", "due_date", "status", "confidence", "cindy_priority", "source_quote" },
  "person": { "id", "person_name", "role_title", "email", "phone", "archetype" },
  "source_interaction": { "id", "source", "summary", "timestamp" },
  "recent_interactions": [ { "source", "summary", "timestamp" } ],
  "related_obligations": [ { "id", "description", "status", "type" } ],
  "company_connections": [ { "company_name", "thesis_thread" } ]
}
```

---

### 2. `generate_obligation_suggestions(p_obligation_id integer) -> jsonb`

**What it does:** Generates actionable suggestions for resolving an obligation. Returns
the obligation context plus recommended actions based on the obligation type, category,
staleness, and the person's relationship tier.

**When to use:** When Cindy needs to propose a resolution path for a stale or urgent
obligation. Feed the output into LLM reasoning for final decision.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT generate_obligation_suggestions(42);" | jq .
```

**Return structure:**
```json
{
  "obligation": { ... },
  "suggestions": [
    { "action_type": "nudge|escalate|auto_resolve|dismiss",
      "reasoning": "why this suggestion",
      "draft_message": "optional draft text" }
  ],
  "person_context": { ... },
  "urgency_factors": { "days_overdue", "relationship_tier", "deal_active" }
}
```

---

### 3. `obligation_staleness_audit() -> jsonb`

**What it does:** Scans ALL pending/in_progress obligations and identifies stale ones.
Groups by staleness severity (overdue, approaching_due, aging). Returns counts, lists,
and recommended batch actions.

**When to use:** During Cindy's daily briefing cycle or when the Orchestrator triggers
an obligation health check. Run this at the start of every Cindy processing cycle to
surface obligations needing attention.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT obligation_staleness_audit();" | jq .
```

**Return structure:**
```json
{
  "total_active": 15,
  "overdue": [ { "id", "description", "person_name", "days_overdue", "type" } ],
  "approaching_due": [ { "id", "description", "person_name", "days_until_due" } ],
  "aging_no_due_date": [ { "id", "description", "person_name", "days_since_created" } ],
  "recommended_actions": [ { "obligation_id", "action": "nudge|escalate|dismiss" } ]
}
```

---

### 4. `obligation_batch_action(p_actions jsonb) -> jsonb`

**What it does:** Executes batch status changes on multiple obligations at once. Accepts
an array of `{obligation_id, action, reason}` objects and applies them atomically.

**When to use:** After reviewing the staleness audit and deciding on batch actions.
Also used after auto-fulfillment detection (mark multiple obligations as fulfilled).

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "
  SELECT obligation_batch_action('[
    {\"obligation_id\": 42, \"action\": \"fulfilled\", \"reason\": \"Email sent per interaction #789\"},
    {\"obligation_id\": 43, \"action\": \"dismissed\", \"reason\": \"Superseded by new agreement\"},
    {\"obligation_id\": 44, \"action\": \"escalate\", \"reason\": \"3 days overdue, portfolio founder\"}
  ]'::jsonb);
" | jq .
```

**Valid actions:** `fulfilled`, `dismissed`, `escalate`, `in_progress`, `snoozed`

**Return structure:**
```json
{
  "processed": 3,
  "results": [
    { "obligation_id": 42, "status": "success", "new_status": "fulfilled" },
    { "obligation_id": 43, "status": "success", "new_status": "dismissed" },
    { "obligation_id": 44, "status": "success", "new_status": "escalated" }
  ],
  "errors": []
}
```

---

### 5. `obligation_health_summary() -> jsonb`

**What it does:** Returns a high-level health summary of the obligations system — total
counts by status, fulfillment rates, average resolution time, top overdue items.

**When to use:** For the daily briefing or system health checks.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT obligation_health_summary();" | jq .
```

---

### 6. `obligation_fulfillment_rate() -> jsonb`

**What it does:** Calculates fulfillment rates (overall and by category/type) over
configurable time windows. Shows how well Aakash is fulfilling obligations.

**When to use:** Trend analysis for the EA briefing. Surface patterns like "send_document
obligations have 40% fulfillment rate — Aakash needs a reminder system for decks."

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT obligation_fulfillment_rate();" | jq .
```

---

### 7. `obligation_urgency_multiplier(action_row actions_queue) -> numeric`

**What it does:** Given an action from the actions_queue, computes an urgency multiplier
based on related obligations. Actions linked to overdue obligations get higher scores.

**When to use:** Called by the scoring system, not directly by Cindy. But Cindy should
understand that obligation-linked actions get priority boosts.

---

### 8. `obligation_deliverable_phrase(p_desc text, p_person_name text) -> text`

**What it does:** Generates a concise, human-readable deliverable phrase from an
obligation description and person name. Used for notification text and briefing bullets.

**When to use:** When composing notification messages or briefing summaries.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT obligation_deliverable_phrase('Send updated term sheet to Rahul', 'Rahul Sharma');"
```

---

### 9. `cindy_obligation_key_question_link() -> jsonb`

**What it does:** Finds obligations that are linked to active thesis key questions.
When Aakash owes someone something that would answer a thesis key question, that
obligation has strategic value beyond the relationship.

**When to use:** During thesis signal routing. If a "send deck" obligation is related
to a thesis key question, escalate it.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_obligation_key_question_link();" | jq .
```

---

### 10. `cindy_obligation_kq_fts_match(p_obligation_id integer) -> jsonb`

**What it does:** Full-text search matching between a specific obligation's description
and all active key questions across thesis threads. Returns match scores.

**When to use:** Deep analysis of a single obligation's thesis relevance.

**Usage:**
```bash
psql $DATABASE_URL -t -A -c "SELECT cindy_obligation_kq_fts_match(42);" | jq .
```

---

## Triage Workflow

When Cindy receives a trigger to triage obligations:

```
1. Run obligation_staleness_audit() — get the full picture
2. For each overdue obligation:
   a. Run cindy_obligation_full_context(id) — understand the context
   b. Run generate_obligation_suggestions(id) — get suggested actions
   c. Reason (LLM): Is this still valid? Should it be nudged, escalated, or dismissed?
   d. Check cindy_obligation_kq_fts_match(id) — any thesis relevance?
3. Collect decisions into a batch
4. Run obligation_batch_action(decisions) — execute all at once
5. For nudge/escalate actions:
   a. Run cindy_draft_nudge_message(id) — get draft message
   b. Write notification with the draft for Aakash to send
6. Run obligation_health_summary() — log the current state
7. Include obligation counts in ACK
```

---

## Anti-Patterns

- Never auto-send nudge messages. Draft them and put in notifications for Aakash.
- Never dismiss obligations without checking for thesis key question links first.
- Never batch-action more than 20 obligations at once — process in chunks.
- Never create duplicate obligations. Always dedup check before INSERT.
- Never skip the staleness audit at the start of a processing cycle.
