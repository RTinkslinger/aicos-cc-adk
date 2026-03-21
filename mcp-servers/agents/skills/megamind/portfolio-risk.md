# Skill: Portfolio Risk & Decision Intelligence

SQL functions for portfolio risk assessment, decision queues, convergence simulation,
and strategic network mapping. Call via `psql $DATABASE_URL`.

---

## Portfolio Risk Assessment

### portfolio_risk_assessment()

**Signature:** `portfolio_risk_assessment() RETURNS TABLE(...)`

Full portfolio health scan returning one row per company:

| Column | Type | Description |
|--------|------|-------------|
| `company_id` | int | companies.id |
| `company_name` | text | Company name |
| `health` | text | Red / Yellow / Green |
| `ops_priority` | text | P0-P3 operational priority |
| `cadence` | text | Check-in cadence |
| `thesis_alignment_count` | int | How many thesis threads this company connects to |
| `open_action_count` | int | Active actions mentioning this company |
| `overdue_obligation_count` | int | Overdue obligations involving this company's people |
| `days_since_last_interaction` | int | Recency of last interaction with company contacts |
| `entity_connection_count` | int | Total entity_connections rows for this company |
| `risk_score` | numeric | Composite risk score (higher = more risk) |
| `risk_tier` | text | Critical / High / Medium / Low |
| `risk_factors` | jsonb | Breakdown of what drives the risk score |

```bash
# Full portfolio risk scan
psql $DATABASE_URL -c "SELECT company_name, health, risk_tier, risk_score, open_action_count, overdue_obligation_count FROM portfolio_risk_assessment() ORDER BY risk_score DESC;"

# Just critical/high risk companies
psql $DATABASE_URL -c "SELECT company_name, health, risk_tier, risk_factors FROM portfolio_risk_assessment() WHERE risk_tier IN ('Critical', 'High') ORDER BY risk_score DESC;"

# Companies with zero actions (attention gap)
psql $DATABASE_URL -c "SELECT company_name, health, ops_priority, risk_score FROM portfolio_risk_assessment() WHERE open_action_count = 0 ORDER BY risk_score DESC;"
```

**Use in cascade processing:** After completing research on a portfolio company,
run `portfolio_risk_assessment()` to check if the risk profile changed and whether
new actions are warranted.

---

## Decision Queue

### actions_needing_decision_v2(p_limit)

**Signature:** `actions_needing_decision_v2(p_limit integer DEFAULT 10) RETURNS TABLE(...)`

Returns the top N actions that need Aakash's decision, enriched with full context:

| Column | Type | Description |
|--------|------|-------------|
| `action_id` | int | actions_queue.id |
| `action_text` | text | The action description |
| `action_type` | text | Meeting, Research, Follow-on Eval, etc. |
| `priority` | text | P0-P3 |
| `strategic_score` | numeric | Megamind's ROI score |
| `score_confidence` | numeric | How confident the score is (based on data completeness) |
| `days_open` | int | How long this has been open |
| `decision_impact_score` | numeric | How much impact a decision on this would have |
| `company_context` | jsonb | Company health, ownership, key questions |
| `person_context` | jsonb | Related people, roles, interaction recency |
| `thesis_context` | jsonb | Connected thesis threads, conviction levels |
| `obligation_context` | jsonb | Related obligations (I-owe, they-owe) |
| `interaction_signals` | jsonb | Recent interaction signals relevant to this action |
| `recommendation` | text | Megamind's recommended decision |

```bash
# Top 10 decisions needed
psql $DATABASE_URL -c "SELECT action_id, action_text, strategic_score, decision_impact_score, recommendation FROM actions_needing_decision_v2();"

# Top 5 with full context
psql $DATABASE_URL -c "SELECT action_id, action_text, company_context, thesis_context FROM actions_needing_decision_v2(5);"
```

**Use in strategic assessment:** Run this to populate the "DECISIONS" section of the
daily briefing. The `decision_impact_score` determines ordering.

---

## Convergence Simulation

### simulate_convergence(p_decisions)

**Signature:** `simulate_convergence(p_decisions jsonb DEFAULT '[]'::jsonb) RETURNS jsonb`

Simulates the effect of proposed decisions on the convergence ratio BEFORE executing them.
Use this to preview whether a cascade's planned actions will maintain convergence.

**Input format (p_decisions):**
```json
[
  {"action_id": 55, "decision": "resolve", "reason": "superseded"},
  {"action_id": 56, "decision": "approve_depth_2"},
  {"action_id": null, "decision": "generate", "action": "Schedule intro to CEO", "score": 8.1}
]
```

**Returns JSONB with:**
- `current_state` — open actions, convergence ratio before decisions
- `projected_state` — what happens if all decisions execute
- `net_delta` — change in action count
- `convergence_pass` — whether invariant would hold
- `warnings` — any convergence violations or budget concerns

```bash
# Simulate resolving 2 actions and generating 1
psql $DATABASE_URL -t -A -c "
  SELECT simulate_convergence('[
    {\"action_id\": 55, \"decision\": \"resolve\"},
    {\"action_id\": 48, \"decision\": \"resolve\"},
    {\"action_id\": null, \"decision\": \"generate\", \"action\": \"New action\", \"score\": 7.5}
  ]'::jsonb);"

# Check current convergence without changes
psql $DATABASE_URL -t -A -c "SELECT simulate_convergence();"
```

**Use in cascade processing:** Before committing cascade results, simulate to verify
convergence will hold. If `convergence_pass = false`, drop lowest-ROI new actions.

---

## Strategic Scoring

### compute_portfolio_strategic_score(p_id)

**Signature:** `compute_portfolio_strategic_score(p_id integer) RETURNS numeric`

Computes the full 5-component strategic score for a single action.
Use when you need to recalculate after context changes.

```bash
psql $DATABASE_URL -t -A -c "SELECT compute_portfolio_strategic_score(55);"
```

### recalibrate_strategic_scores()

**Signature:** `recalibrate_strategic_scores() RETURNS TABLE(action_id, old_score, new_score, score_components)`

Batch recalculates strategic scores for ALL open actions. Returns only actions
where the score changed. Use in strategic assessments.

```bash
psql $DATABASE_URL -c "SELECT action_id, old_score, new_score, score_components FROM recalibrate_strategic_scores() WHERE abs(new_score - old_score) > 0.1;"
```

### apply_strategic_recalibration()

**Signature:** `apply_strategic_recalibration() RETURNS jsonb`

Runs `recalibrate_strategic_scores()` AND writes the new scores to `actions_queue`.
Returns summary of changes made. Use when you want to both compute and persist.

```bash
psql $DATABASE_URL -t -A -c "SELECT apply_strategic_recalibration();"
```

---

## Strategic Network Map

### strategic_network_map(p_limit)

**Signature:** `strategic_network_map(p_limit integer DEFAULT 20) RETURNS TABLE(...)`

Ranks people in the network by strategic importance:

| Column | Type | Description |
|--------|------|-------------|
| `person_id` | int | network.id |
| `person_name` | text | Full name |
| `role_title` | text | Current role |
| `strategic_importance` | numeric | Composite importance score |
| `portfolio_connections` | int | How many portfolio companies they connect to |
| `active_deal_involvement` | int | Current deal involvement count |
| `obligation_count` | int | Total obligations (I-owe + they-owe) |
| `obligation_overdue_count` | int | Overdue obligations |
| `interaction_recency_days` | int | Days since last interaction |
| `interaction_count_30d` | int | Interaction count in last 30 days |
| `entity_connection_strength` | numeric | Strength of entity connections |
| `action_mentions` | int | How many open actions mention this person |
| `importance_factors` | jsonb | Breakdown of importance score components |

```bash
# Top 20 strategically important people
psql $DATABASE_URL -c "SELECT person_name, role_title, strategic_importance, obligation_overdue_count, interaction_recency_days FROM strategic_network_map();"

# People with overdue obligations
psql $DATABASE_URL -c "SELECT person_name, obligation_overdue_count, interaction_recency_days FROM strategic_network_map() WHERE obligation_overdue_count > 0 ORDER BY obligation_overdue_count DESC;"
```

---

## When to Use Each Function

| Situation | Function |
|-----------|----------|
| Daily strategic assessment | `portfolio_risk_assessment()` + `actions_needing_decision_v2()` |
| Before committing cascade results | `simulate_convergence(decisions_jsonb)` |
| After completing depth-graded work | `compute_portfolio_strategic_score(action_id)` to re-score |
| Periodic score refresh | `apply_strategic_recalibration()` |
| Cascade blast radius people check | `strategic_network_map()` filtered by company connection |
| Identifying attention gaps | `portfolio_risk_assessment() WHERE open_action_count = 0` |
| Presenting action to Aakash | `actions_needing_decision_v2()` for full context |
| Quick convergence health | `simulate_convergence()` with no args |
