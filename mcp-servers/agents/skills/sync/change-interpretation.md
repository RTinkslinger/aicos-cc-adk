# Change Interpretation Skill

Instructions for interpreting change events detected during Notion-Postgres sync and generating appropriate actions.

---

## Change Detection Overview

The Sync Agent compares Notion state against Postgres state on every sync cycle (every 10 minutes). When differences are found, they are logged to the `change_events` table and optionally trigger action generation.

---

## Change Event Types

### Thesis Status Change

**What it means:** Aakash manually changed a thesis thread's status in Notion.

| Old -> New | Interpretation | Action |
|-----------|---------------|--------|
| Active/Exploring -> Parked | Aakash is de-prioritizing this thesis. | Generate action: "Review and deprioritize pending actions connected to '{thread_name}'" (P2). |
| Active/Exploring -> Archived | Thesis is dead or fully resolved. | Generate action: "Review and deprioritize pending actions connected to '{thread_name}'" (P2). |
| Parked/Archived -> Active | Aakash is reactivating this thesis. | Generate action: "Resurface and review actions for reactivated thesis '{thread_name}'" (P1). |
| Parked/Archived -> Exploring | Thesis is being reconsidered. | Generate action: "Resurface and review actions for reactivated thesis '{thread_name}'" (P1). |
| Exploring -> Active | Thesis promoted to active tracking. | No action needed -- thesis is now receiving full scoring weight. |

### Thesis Conviction Change

**What it means:** Conviction level was updated (by ContentAgent, CAI, or manually).

| New Value | Interpretation | Action |
|-----------|---------------|--------|
| High | Strong convergent evidence. Investable thesis. | Generate action: "Review portfolio and pipeline for '{thread_name}' investment opportunities -- conviction just reached High" (P1, Research). |
| Low (from Medium/High) | Conviction weakening. Evidence may be turning. | Notify Aakash. No auto-generated action. |
| Evolving Fast (from New/Evolving) | Rapid signal flow. | Notify Aakash of acceleration. No auto-generated action. |

### Action Outcome Change

**What it means:** Aakash rated an action's outcome in Notion.

| New Value | Interpretation | Action |
|-----------|---------------|--------|
| Gold | Exceptionally valuable action. | Generate action: "Analyze what made action #{id} Gold-rated -- find similar high-value patterns" (P2, Research). |
| Helpful | Positive but not exceptional. | Log for preference calibration. No action. |
| Unknown -> Helpful/Gold | First feedback received. | Update preference store (action_outcomes table). |

---

## Action Generation Rules

When change events trigger action generation, create actions in the `actions_queue` table:

```bash
psql $DATABASE_URL -c "INSERT INTO actions_queue (action, action_type, priority, source, created_by, assigned_to, reasoning, notion_synced) VALUES (
  '{action_text}',
  '{action_type}',
  '{priority}',
  'SyncAgent',
  'AI CoS',
  'Aakash',
  '{reasoning}',
  FALSE
);"
```

### Action templates by trigger

**Thesis conviction -> High:**
- Action: "Review portfolio and pipeline for '{thread_name}' investment opportunities -- conviction just reached High"
- Type: Research
- Priority: P1 - Next
- Reasoning: "Thesis '{thread_name}' conviction moved from {old} to High. High-conviction thesis should trigger active deal sourcing."

**Thesis status Active -> Parked/Archived:**
- Action: "Review and deprioritize pending actions connected to '{thread_name}' (now {new_status})"
- Type: Thesis Update
- Priority: P2 - Later
- Reasoning: "Thesis '{thread_name}' moved from {old} to {new}. Connected actions may no longer be relevant."

**Thesis status Parked/Archived -> Active/Exploring:**
- Action: "Resurface and review actions for reactivated thesis '{thread_name}'"
- Type: Thesis Update
- Priority: P1 - Next
- Reasoning: "Thesis '{thread_name}' reactivated from {old} to {new}. Check for new signals and pending actions."

**Action outcome -> Gold:**
- Action: "Analyze what made action #{id} Gold-rated -- find similar high-value patterns"
- Type: Research
- Priority: P2 - Later
- Reasoning: "Action outcome rated Gold. Understanding what makes actions valuable improves future scoring."

---

## Processing Protocol

### Step 1: Fetch unprocessed changes

```bash
psql $DATABASE_URL -c "SELECT id, table_name, record_id, notion_page_id, field_name, old_value, new_value, detected_at FROM change_events WHERE NOT processed ORDER BY detected_at ASC LIMIT 50;"
```

### Step 2: Interpret each change

For each change event:
1. Match against the rules above (table_name + field_name + new_value).
2. If a rule matches, generate the corresponding action.
3. If no rule matches, log but take no action (some changes are informational only).

### Step 3: Generate actions

Create actions in the `actions_queue` table per the templates above.

### Step 4: Mark changes as processed

```bash
psql $DATABASE_URL -c "UPDATE change_events SET processed = TRUE WHERE id IN ({comma_separated_ids});"
```

---

## Notification Triggers

Some changes should also generate notifications (written to `notifications` table for CAI to read):

| Change | Notification? | Why |
|--------|--------------|-----|
| Thesis conviction -> High | Yes | Aakash should be aware of this milestone |
| Thesis conviction downgrade (Medium/High -> Low) | Yes | Aakash should know conviction is weakening |
| Thesis reactivated (Parked/Archived -> Active) | Yes | Confirms Aakash's action was registered |
| Action rated Gold | Yes | Positive feedback loop |
| Sync failure (3+ consecutive) | Yes | Infrastructure issue needs attention |

```bash
psql $DATABASE_URL -c "INSERT INTO notifications (notification_type, title, body, source_agent, created_at) VALUES (
  'thesis_milestone',
  'Thesis conviction reached High: {thread_name}',
  'Thesis \"{thread_name}\" conviction moved from {old} to High based on accumulated evidence. Generated action: review portfolio for investment opportunities.',
  'SyncAgent',
  NOW()
);"
```

---

## Change Event Schema

For reference, the `change_events` table:

```sql
CREATE TABLE change_events (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,       -- 'thesis_threads' or 'actions_queue'
    record_id INTEGER NOT NULL,      -- Postgres row ID
    notion_page_id TEXT,             -- Notion page ID
    field_name TEXT NOT NULL,        -- Which field changed
    old_value TEXT,                  -- Previous value
    new_value TEXT,                  -- New value
    detected_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);
```

---

## Diagnostic Queries

```bash
# Recent unprocessed changes
psql $DATABASE_URL -c "SELECT * FROM change_events WHERE NOT processed ORDER BY detected_at DESC LIMIT 10;"

# Change history for a specific thesis
psql $DATABASE_URL -c "SELECT field_name, old_value, new_value, detected_at FROM change_events WHERE table_name = 'thesis_threads' AND record_id = {id} ORDER BY detected_at DESC;"

# Summary of changes by type
psql $DATABASE_URL -c "SELECT table_name, field_name, COUNT(*) as count FROM change_events GROUP BY table_name, field_name ORDER BY count DESC;"

# Gold-rated action outcomes (for pattern analysis)
psql $DATABASE_URL -c "SELECT ce.*, aq.action FROM change_events ce JOIN actions_queue aq ON ce.record_id = aq.id WHERE ce.table_name = 'actions_queue' AND ce.field_name = 'outcome' AND ce.new_value = 'Gold';"
```
