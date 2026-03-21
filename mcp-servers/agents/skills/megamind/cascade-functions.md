# Skill: Cascade SQL Functions & Obligation Cascades

SQL functions for creating cascade events, analyzing cascade impact, processing
obligation cascades, and generating obligation follow-up actions. Call via `psql $DATABASE_URL`.

---

## Cascade Event Creation

### create_cascade_event(p_trigger_type, p_trigger_id, p_description, p_impact_scope)

**Signature:** `create_cascade_event(p_trigger_type text, p_trigger_id integer DEFAULT NULL, p_description text DEFAULT '', p_impact_scope jsonb DEFAULT '{}') RETURNS integer`

Creates a new cascade event record. Returns the new cascade event ID.

**Trigger types:** `'depth_completed'`, `'conviction_change'`, `'new_thesis'`, `'contra_signal'`, `'portfolio_event'`, `'obligation_change'`

```bash
# Create cascade from completed depth-graded work
psql $DATABASE_URL -t -A -c "
  SELECT create_cascade_event(
    'depth_completed',
    12,
    'Ultra research on Composio completed',
    '{\"affected_theses\": [\"Agentic AI Infrastructure\"], \"affected_companies\": [\"Composio\"]}'::jsonb
  );"

# Create cascade from conviction change
psql $DATABASE_URL -t -A -c "
  SELECT create_cascade_event(
    'conviction_change',
    NULL,
    'Agentic AI Infrastructure conviction moved to Evolving Fast',
    '{\"affected_theses\": [\"Agentic AI Infrastructure\"]}'::jsonb
  );"

# Create cascade from obligation change
psql $DATABASE_URL -t -A -c "
  SELECT create_cascade_event(
    'obligation_change',
    42,
    'Overdue obligation to LP escalated',
    '{\"affected_people\": [\"John Smith\"], \"affected_companies\": [\"Z47\"]}'::jsonb
  );"
```

**Use this instead of raw INSERT** — it handles:
- Cascade chain limit enforcement (checks if trigger already spawned a cascade)
- Timestamp management
- Impact scope validation

---

## Cascade Impact Analysis

### cascade_impact_analysis(p_event_id)

**Signature:** `cascade_impact_analysis(p_event_id integer DEFAULT NULL) RETURNS jsonb`

Analyzes the downstream impact of a cascade event (or the most recent if NULL).

**Returns JSONB with:**
- `cascade_event` — the trigger event details
- `blast_radius` — thesis threads, companies, people in scope
- `actions_in_scope` — all open actions within blast radius
- `score_deltas` — how scores would change given new information
- `resolution_candidates` — actions that could be resolved
- `generation_candidates` — potential new actions identified
- `convergence_projection` — whether generating/resolving would maintain convergence
- `chain_status` — whether this cascade has already triggered follow-ups

```bash
# Analyze most recent cascade
psql $DATABASE_URL -t -A -c "SELECT cascade_impact_analysis();"

# Analyze specific cascade event
psql $DATABASE_URL -t -A -c "SELECT cascade_impact_analysis(5);"
```

**Workflow:**
1. `create_cascade_event()` — record the trigger
2. `cascade_impact_analysis(event_id)` — understand the blast radius
3. Review the impact analysis, decide what to rescore/resolve/generate
4. Execute the changes (UPDATE scores, SET status='Done', INSERT new actions)
5. Update the cascade_events record with final counts

```bash
# After analysis, update cascade with actual results
psql $DATABASE_URL -c "
  UPDATE cascade_events SET
    actions_rescored = 3,
    actions_resolved = 2,
    actions_generated = 1,
    net_action_delta = -1,
    convergence_pass = TRUE,
    cascade_report = '{
      \"rescored\": [...],
      \"resolved\": [...],
      \"generated\": [...],
      \"summary\": \"...\"
    }'::jsonb,
    updated_at = NOW()
  WHERE id = $event_id;"
```

---

## Obligation Cascades

### process_obligation_cascade()

**Signature:** `process_obligation_cascade() RETURNS TABLE(obligation_id, obligation_desc, linked_action_id, score_boost, depth_change, cascade_event_id)`

Processes all unprocessed obligation changes and their cascade effects on the action
space. When obligations change (new, overdue, fulfilled), related actions may need
re-scoring.

| Column | Type | Description |
|--------|------|-------------|
| `obligation_id` | int | The obligation that changed |
| `obligation_desc` | text | Obligation description |
| `linked_action_id` | int | Action affected by this obligation change |
| `score_boost` | numeric | How much the action's score was adjusted |
| `depth_change` | text | Whether depth grade changed (e.g., 'Scan->Investigate') |
| `cascade_event_id` | int | The cascade event created for this batch |

```bash
psql $DATABASE_URL -c "SELECT obligation_id, obligation_desc, linked_action_id, score_boost, depth_change FROM process_obligation_cascade();"
```

**When obligations become overdue:**
- Actions related to that person/company get score boost (+0.15 to strategic_score)
- If boosted score crosses depth threshold, depth grade auto-upgrades
- Creates cascade_event with `trigger_type = 'obligation_change'`

**When obligations get fulfilled:**
- Related follow-up actions may become redundant (candidates for resolution)
- Score may decrease if obligation was the primary driver

### auto_generate_obligation_followup_actions()

**Signature:** `auto_generate_obligation_followup_actions() RETURNS void` (implied from name)

Scans overdue obligations and generates follow-up actions in `actions_queue`
with `source = 'obligation_followup'`. Respects per-person action caps.

```bash
psql $DATABASE_URL -c "SELECT auto_generate_obligation_followup_actions();"
```

---

## Obligation Support Functions

These are used internally by cascade processing but can be called directly
for debugging or analysis:

### obligation_health_summary()

**Signature:** `obligation_health_summary() RETURNS ...`

Overall health of the obligation tracking system.

```bash
psql $DATABASE_URL -c "SELECT * FROM obligation_health_summary();"
```

### obligation_staleness_audit()

**Signature:** `obligation_staleness_audit() RETURNS ...`

Identifies obligations that are stale (no updates, no linked actions).

```bash
psql $DATABASE_URL -c "SELECT * FROM obligation_staleness_audit();"
```

### obligation_fulfillment_rate()

**Signature:** `obligation_fulfillment_rate() RETURNS ...`

Calculates fulfillment rates for I-owe vs they-owe obligations.

```bash
psql $DATABASE_URL -c "SELECT * FROM obligation_fulfillment_rate();"
```

### detect_obligation_fulfillment_candidates()

**Signature:** `detect_obligation_fulfillment_candidates() RETURNS ...`

Finds obligations that may have been fulfilled based on recent interactions
but haven't been marked as fulfilled yet.

```bash
psql $DATABASE_URL -c "SELECT * FROM detect_obligation_fulfillment_candidates();"
```

### detect_obligation_fulfillment_from_interactions()

**Signature:** `detect_obligation_fulfillment_from_interactions() RETURNS ...`

More targeted version — specifically checks recent interactions for fulfillment signals.

```bash
psql $DATABASE_URL -c "SELECT * FROM detect_obligation_fulfillment_from_interactions();"
```

---

## process_cascade_event() [TRIGGER]

**Signature:** `process_cascade_event() RETURNS trigger`

This is a TRIGGER function — NOT called directly. It fires automatically when a new
row is inserted into `cascade_events`. It handles:
- Updating affected action scores
- Creating notifications
- Checking cascade chain limits

You do NOT call this. But when you INSERT into `cascade_events` (or use
`create_cascade_event()`), this trigger fires automatically.

---

## Full Cascade Processing Workflow

```bash
# 1. Create the cascade event
EVENT_ID=$(psql $DATABASE_URL -t -A -c "
  SELECT create_cascade_event('depth_completed', 12, 'Ultra on Composio done',
    '{\"affected_theses\": [\"Agentic AI Infrastructure\"]}'::jsonb);")

# 2. Analyze impact
psql $DATABASE_URL -t -A -c "SELECT cascade_impact_analysis($EVENT_ID);"

# 3. Check for obligation cascades too
psql $DATABASE_URL -c "SELECT * FROM process_obligation_cascade();"

# 4. Dedup any new actions before generating
psql $DATABASE_URL -t -A -c "
  SELECT is_duplicate FROM cascade_dedup_guard('Schedule intro to Composio CEO');"

# 5. Simulate convergence before committing
psql $DATABASE_URL -t -A -c "
  SELECT simulate_convergence('[
    {\"action_id\": 48, \"decision\": \"resolve\"},
    {\"action_id\": null, \"decision\": \"generate\", \"action\": \"Schedule intro\", \"score\": 8.1}
  ]'::jsonb);"

# 6. If convergence_pass = true, execute changes
# ... UPDATE scores, INSERT new actions, UPDATE cascade_events record ...

# 7. Write notification
psql $DATABASE_URL -c "
  INSERT INTO notifications (source, type, content, metadata)
  VALUES ('Megamind', 'cascade_report', 'Cascade summary...', '{}'::jsonb);"
```

---

## When to Use Each Function

| Situation | Function |
|-----------|----------|
| New cascade trigger detected | `create_cascade_event()` |
| Understanding blast radius | `cascade_impact_analysis(event_id)` |
| Obligations changed | `process_obligation_cascade()` |
| Before generating cascade actions | `cascade_dedup_guard(action_text)` |
| Daily obligation maintenance | `auto_generate_obligation_followup_actions()` |
| Obligation system health check | `obligation_health_summary()` |
| Finding auto-fulfillable obligations | `detect_obligation_fulfillment_candidates()` |
