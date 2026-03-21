# Skill: Depth Automation & Staleness Management

SQL functions for automated depth grade refresh, stale action dismissal, and
cascade deduplication. These are your maintenance tools — call via `psql $DATABASE_URL`.

---

## Auto-Refresh Depth Grades

### auto_refresh_depth_grades()

**Signature:** `auto_refresh_depth_grades() RETURNS TABLE(action_id, action_text, old_depth, new_depth, reason)`

Scans all pending depth grades and recalculates whether the assigned depth is still
correct given current context changes. Triggers include:

- Thesis conviction changed since grade was assigned
- Diminishing returns n increased (more completed work on same thesis)
- Portfolio status changed (company health moved)
- Daily budget state changed
- Action staleness crossed threshold

Returns only grades where depth CHANGED, with the reason.

```bash
# Check which grades need updating
psql $DATABASE_URL -c "SELECT action_id, action_text, old_depth, new_depth, reason FROM auto_refresh_depth_grades();"
```

**When to run:**
- At the start of every depth grading session (before grading new actions)
- After any cascade completes (new information may invalidate existing grades)
- During daily strategic assessment

**Important:** This function READS and RETURNS changes but does NOT write them.
You must review the output and apply changes manually:

```bash
# After reviewing auto_refresh output, apply a depth change:
psql $DATABASE_URL -c "
  UPDATE depth_grades SET
    auto_depth = $new_depth,
    reasoning = reasoning || ' | Auto-refreshed: ' || '$reason',
    updated_at = NOW()
  WHERE action_id = $action_id
    AND execution_status = 'pending';"
```

### regrade_on_strategic_change()

**Signature:** `regrade_on_strategic_change() RETURNS trigger`

This is a TRIGGER function, not called directly. It fires automatically when:
- `thesis_threads.conviction` changes
- `strategic_config` values change

The trigger recalculates depth grades for affected pending actions. You do NOT
call this — it runs automatically. But you should be aware it exists because
depth grades may change between your prompts.

---

## Stale Action Dismissal

### auto_dismiss_stale_actions()

**Signature:** `auto_dismiss_stale_actions() RETURNS TABLE(action_id, action_text, reason, old_score)`

Identifies and dismisses actions that meet staleness criteria:

| Staleness Condition | Action Taken |
|-------------------|-------------|
| Open > 30 days with score < 5.0 | Auto-dismiss |
| Open > 14 days with no depth grade | Auto-dismiss |
| Open > 30 days with depth grade but no execution | Auto-dismiss |
| Agent-assigned, open > 21 days, no progress | Auto-dismiss |

Returns the actions that were dismissed with reasons.

```bash
# Run stale action cleanup
psql $DATABASE_URL -c "SELECT action_id, action_text, reason, old_score FROM auto_dismiss_stale_actions();"
```

**When to run:**
- During every daily strategic assessment
- When convergence ratio drops below 1.0 (helps recover convergence)

**Important:** This function DOES write changes — it sets `status = 'Dismissed'`
on matching actions. Run it when you are confident the staleness rules are appropriate.

---

## Cascade Deduplication

### cascade_dedup_guard(p_action_text, p_threshold)

**Signature:** `cascade_dedup_guard(p_action_text text, p_threshold real DEFAULT 0.6) RETURNS TABLE(is_duplicate, matching_action_id, matching_action_text, similarity_score)`

Before generating a new action in a cascade, check whether a similar action already
exists. Uses text similarity matching.

| Column | Type | Description |
|--------|------|-------------|
| `is_duplicate` | boolean | TRUE if a sufficiently similar action exists |
| `matching_action_id` | int | The existing action that matches |
| `matching_action_text` | text | Text of the matching action |
| `similarity_score` | real | How similar (0.0-1.0, higher = more similar) |

```bash
# Check before generating a cascade action
psql $DATABASE_URL -t -A -c "
  SELECT is_duplicate, matching_action_id, similarity_score
  FROM cascade_dedup_guard('Research Composio competitive landscape', 0.6);"
```

**Use in cascade Step 4 (Generate New Actions):**
1. Before inserting any new action from a cascade, call `cascade_dedup_guard()`
2. If `is_duplicate = TRUE`, skip the generation — the action already exists
3. If `is_duplicate = FALSE`, proceed with INSERT

```bash
# Full cascade generation workflow with dedup
psql $DATABASE_URL -t -A -c "
  SELECT is_duplicate, matching_action_id
  FROM cascade_dedup_guard('Schedule intro to Composio CEO');"
# If is_duplicate = FALSE, proceed:
psql $DATABASE_URL -c "
  INSERT INTO actions_queue (action, action_type, priority, status, assigned_to,
    relevance_score, reasoning, thesis_connection, source)
  VALUES ('Schedule intro to Composio CEO', 'Meeting', 'P1', 'Proposed', 'Aakash',
    8.1, 'Ultra research revealed Series B timing', 'Agentic AI Infrastructure',
    'megamind_cascade');"
```

**Threshold tuning:**
- Default 0.6 catches most duplicates while allowing related-but-different actions
- Use 0.4 for stricter dedup (fewer duplicates slip through)
- Use 0.8 for looser dedup (only near-exact matches blocked)

---

## Workflow: Full Maintenance Cycle

Run this sequence during daily strategic assessment:

```bash
# 1. Refresh existing depth grades
psql $DATABASE_URL -c "SELECT * FROM auto_refresh_depth_grades();"

# 2. Dismiss stale actions (helps convergence)
psql $DATABASE_URL -c "SELECT * FROM auto_dismiss_stale_actions();"

# 3. Recalibrate all strategic scores
psql $DATABASE_URL -t -A -c "SELECT apply_strategic_recalibration();"

# 4. Check convergence health
psql $DATABASE_URL -c "SELECT * FROM megamind_convergence;"

# 5. Generate full assessment
psql $DATABASE_URL -c "SELECT generate_strategic_assessment();"
```

---

## When to Use Each Function

| Situation | Function |
|-----------|----------|
| Start of depth grading session | `auto_refresh_depth_grades()` |
| Daily maintenance | `auto_dismiss_stale_actions()` |
| Before generating cascade action | `cascade_dedup_guard(action_text)` |
| Convergence recovery mode | `auto_dismiss_stale_actions()` (aggressive cleanup) |
| After thesis conviction change | Check `auto_refresh_depth_grades()` for affected grades |
| Investigating duplicate actions | `cascade_dedup_guard(text, 0.4)` with lower threshold |
