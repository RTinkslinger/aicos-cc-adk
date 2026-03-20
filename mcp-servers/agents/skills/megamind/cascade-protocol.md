# Skill: Cascade Re-ranking Protocol

Domain knowledge for Megamind's cascade processing — re-evaluating actions after new
information arrives.

---

## What Triggers a Cascade

A cascade fires when new information changes the strategic landscape. Five trigger types:

| Trigger Type | DB Value | Source | Example |
|-------------|----------|--------|---------|
| Depth-graded work completes | `depth_completed` | `depth_grades.execution_status = 'completed'` | Ultra research on Composio returns results |
| Thesis conviction changes | `conviction_change` | `thesis_threads.conviction` updated | "Agentic AI" moves from Evolving to Evolving Fast |
| New thesis thread created | `new_thesis` | Content Agent creates new thread | "Vertical AI Agents" identified as new pattern |
| High-value contra signal | `contra_signal` | Content Agent flags contra in digest | Evidence that agentic AI is overhyped |
| Portfolio event detected | `portfolio_event` | Content/Datum finds funding, competitor move | Portfolio company's competitor raises $100M |

The Orchestrator detects these and sends Megamind a cascade trigger prompt.

---

## Cascade Algorithm (Step by Step)

### Step 1: Identify Blast Radius

From the trigger event, determine which entities are affected:

```sql
-- Get thesis connections from the trigger
-- (provided in the Orchestrator's cascade prompt)
-- Example: affected_thesis = 'Agentic AI Infrastructure'

-- Get all open actions in the blast radius
SELECT id, action_text, relevance_score, strategic_score,
       thesis_connection, assigned_to, status, created_at
FROM actions_queue
WHERE status IN ('Proposed', 'Accepted', 'In Progress')
  AND (
    thesis_connection = $affected_thesis
    OR action_text ILIKE '%' || $affected_company || '%'
  )
ORDER BY relevance_score DESC;
```

Record the blast radius size in `cascade_events.affected_actions_count`.

### Step 2: Re-Score Each Affected Action

For every open action in the blast radius:

1. **Recalculate strategic ROI** incorporating new information from the trigger:
   - If trigger answered questions: information marginal value DROPS for actions
     investigating the same questions
   - If trigger revealed new connections: strategic score may RISE
   - If trigger invalidated a hypothesis: score drops sharply
   - Update diminishing returns n (increment if trigger was a completed research action)

2. **Compute delta:**
   ```
   delta = new_strategic_score - old_strategic_score
   ```

3. **Log if meaningful (abs(delta) > 0.1):**
   ```json
   {
     "action_id": 55,
     "old_score": 0.72,
     "new_score": 0.41,
     "delta": -0.31,
     "reasoning": "Ultra research on Composio already covered competitive landscape. This action is now redundant."
   }
   ```

### Step 3: Identify Actions to Resolve

An action should be resolved (closed without execution) if:

| Condition | Resolution Reason |
|-----------|------------------|
| The trigger's results directly answered this action's question | "Answered by [trigger description]" |
| The action is now redundant with another higher-priority action | "Superseded by action id=[X]" |
| New information invalidated the action's premise | "Premise invalidated: [explanation]" |
| The action's strategic score dropped below 0.1 after re-scoring | "Score dropped below threshold after cascade" |

Resolve action:
```sql
UPDATE actions_queue SET
  status = 'Done',
  updated_at = NOW()
WHERE id = $action_id;
```

### Step 4: Generate New Actions (if warranted)

Only generate new actions if the trigger results reveal genuinely NEW opportunities that
were not previously in the action space.

Rules:
- Each new action MUST have explicit ROI justification
- Each new action MUST be scored using the full 5-component model
- New actions count toward the per-thesis cap
- New actions count toward the convergence constraint

Write new actions:
```sql
INSERT INTO actions_queue (
  action_text, action_type, priority, status, assigned_to,
  relevance_score, reasoning, thesis_connection, source, created_at, updated_at
) VALUES (
  $action_text, $action_type, $priority, 'Proposed', $assigned_to,
  $relevance_score, $reasoning, $thesis_connection,
  'megamind_cascade', NOW(), NOW()
) RETURNING id;
```

### Step 5: Enforce Convergence

**HARD CONSTRAINT:** `actions_generated <= actions_resolved`

```
IF new_actions_count > resolved_count:
    # Must drop some new actions to maintain convergence
    # Sort new actions by strategic score ascending
    # Drop lowest-scoring new actions until constraint holds
    # If ALL new actions have higher ROI than resolved actions,
    # log convergence exception with reasoning
```

Convergence exception is allowed but must be RARE:
```sql
-- Set convergence_pass = FALSE and provide reason
INSERT INTO cascade_events (..., convergence_pass, convergence_exception_reason)
VALUES (..., FALSE, 'All 3 new actions score > 0.8 while only 2 resolved. Net positive justified by high-ROI opportunity window.');
```

### Step 6: Check Cascade Chain Limit

Before processing, verify this isn't a chain cascade:
```sql
SELECT COUNT(*) FROM cascade_events
WHERE trigger_source_id = $original_trigger_source_id
  AND trigger_type = $trigger_type;
```

If count > 0 (this trigger already spawned a cascade), do NOT process another cascade.
Instead, queue the analysis for the next strategic assessment:
```
Log: "Cascade chain limit reached for trigger [X]. Queued for next strategic assessment."
```

### Step 7: Write Cascade Event

```sql
INSERT INTO cascade_events (
  trigger_type, trigger_source_id, trigger_description,
  affected_thesis_threads, affected_companies, affected_actions_count,
  actions_rescored, actions_resolved, actions_generated, net_action_delta,
  convergence_pass, convergence_exception_reason, cascade_report
) VALUES (
  $trigger_type, $trigger_source_id, $trigger_description,
  $affected_thesis_threads, $affected_companies, $affected_actions_count,
  $actions_rescored, $actions_resolved, $actions_generated,
  $actions_generated - $actions_resolved,
  ($actions_generated - $actions_resolved) <= 0,
  $exception_reason_or_null,
  $cascade_report_jsonb
) RETURNING id;
```

### Step 8: Write Notification

```sql
INSERT INTO notifications (source, type, content, metadata, created_at)
VALUES (
  'Megamind', 'cascade_report',
  $human_readable_summary,
  $metadata_jsonb,
  NOW()
);
```

---

## Cascade Report JSONB Schema

The `cascade_report` column stores the full structured report for WebFront display:

```json
{
  "rescored": [
    {
      "action_id": 55,
      "action_text": "Research Composio competitive landscape",
      "old_score": 7.2,
      "new_score": 4.1,
      "delta": -3.1,
      "reasoning": "Already covered by ultra research results"
    }
  ],
  "resolved": [
    {
      "action_id": 48,
      "action_text": "Add Composio to companies DB",
      "reason": "Done by Datum Agent as part of research pre-req"
    }
  ],
  "generated": [
    {
      "action_text": "Schedule intro to Composio CEO via [mutual connection]",
      "score": 8.1,
      "priority": "P1",
      "assigned_to": "Aakash",
      "reasoning": "Ultra research revealed Series B timing aligns with Z47 check size",
      "thesis_connection": "Agentic AI Infrastructure"
    }
  ],
  "summary": "Cascade from ultra research on Composio. 3 actions rescored, 2 resolved as redundant, 1 new high-priority action generated. Net: -1 actions. System is converging."
}
```

---

## Convergence Rules Reference

### Per-Cascade Constraint

```
cascade.actions_resolved >= cascade.actions_generated
```

Enforced in Step 5. Exceptions must be logged with reasoning.

### 7-Day Rolling Window (checked in strategic assessment)

```sql
SELECT
  COALESCE(SUM(actions_resolved), 0) as total_resolved,
  COALESCE(SUM(actions_generated), 0) as total_generated
FROM cascade_events
WHERE created_at > NOW() - INTERVAL '7 days';
```

```
convergence_ratio = total_resolved / NULLIF(total_generated, 0)
-- If total_generated = 0, ratio is infinite (perfect convergence)
-- Target: ratio >= 1.0
-- Warning: ratio 0.8-1.0
-- Critical: ratio < 0.8
```

### Convergence Failure Protocol

If ratio < 0.8 for 3 consecutive strategic assessments:
1. Cap all new depth grades at depth 1 (Scan)
2. Set cascade generation limit to 0 (no new actions from cascades)
3. Push CRITICAL notification to Aakash
4. Generate convergence recovery plan in next strategic assessment
5. Recovery: ratio >= 1.0 for 2 consecutive days removes caps

---

## Cascade Trigger Detection Queries

These are run by the Orchestrator (in HEARTBEAT.md), not by Megamind directly. Included here
for reference.

### Completed depth-graded work (most common trigger)

```sql
SELECT dg.id, dg.action_id, aq.action_text, aq.thesis_connection
FROM depth_grades dg
JOIN actions_queue aq ON dg.action_id = aq.id
WHERE dg.execution_status = 'completed'
  AND dg.id NOT IN (
    SELECT trigger_source_id FROM cascade_events
    WHERE trigger_type = 'depth_completed'
  )
LIMIT 1;
```

### Conviction change (detected by comparing thesis state)

```sql
-- Orchestrator monitors thesis_threads for conviction changes
-- When detected, sends cascade trigger to Megamind
SELECT name, conviction, updated_at
FROM thesis_threads
WHERE status = 'Active'
  AND updated_at > NOW() - INTERVAL '1 hour';
```

### Portfolio events (detected via content pipeline)

The Content Agent flags portfolio events in notifications. The Orchestrator routes these
to Megamind as cascade triggers.

---

## Escalation Rules

During cascade processing, some generated actions require human judgment:

| Action Type | Assigned To | Why Escalate |
|------------|-------------|-------------|
| Meeting/Outreach | Aakash | Requires human relationship judgment |
| Follow-on Eval | Aakash | Investment decision, not delegatable |
| Portfolio Check-in | Aakash | Relationship management |
| Thesis conviction override | Aakash | Conviction is human-only |

For agent-assignable actions (Research, Content Follow-up, Pipeline Action, Entity Enrichment),
Megamind can route through depth grading without human involvement (subject to trust level).
