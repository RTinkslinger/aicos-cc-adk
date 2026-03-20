# Skill: Strategic Reasoning

Domain knowledge for Megamind's core diverge/converge reasoning and ROI calculation.

---

## Strategic ROI Calculation

The fundamental optimization function:

```
ROI(action) = expected_impact(action) x relevance_to_priorities(action)
              ---------------------------------------------------------
              time_cost(action) x opportunity_cost(action)
```

Produces a **strategic score** from 0.0 to 1.0.

### Component Weights

| Component | Weight | DB Source | How to Compute |
|-----------|--------|-----------|----------------|
| ENIAC raw score | 0.30 | `actions_queue.relevance_score` | Divide by 10.0 to normalize to 0-1 |
| Thesis momentum | 0.20 | `thesis_threads.conviction` + `strategic_assessments` | See momentum table below |
| Information marginal value | 0.20 | `depth_grades` (completed, last 14d) | `1.0 * 0.7^n` where n = completed actions on same thesis/company |
| Portfolio exposure | 0.15 | `portfolio` + `companies` | See portfolio multiplier table below |
| Time decay | 0.15 | `actions_queue.created_at` | See freshness calculation below |

### Thesis Momentum Mapping

| Conviction | Momentum Score |
|------------|---------------|
| Evolving Fast | 1.0 |
| Evolving | 0.7 |
| High | 0.5 |
| Medium | 0.5 |
| Low | 0.3 |
| New | 0.3 |

Query:
```sql
SELECT name, conviction FROM thesis_threads
WHERE status IN ('Active', 'Exploring')
  AND name = ANY($thesis_connections);
```

### Portfolio Exposure Multiplier

| Condition | Multiplier |
|-----------|-----------|
| Portfolio company with upcoming decision (follow-on, BRC within 90 days) | 1.0 |
| Portfolio company, no upcoming decision | 0.6 |
| Not a portfolio company | 0.3 |

Query:
```sql
-- Check if action's company is in portfolio
SELECT p.company_name, p.follow_on_status, p.next_brc_date
FROM portfolio p
JOIN companies c ON LOWER(c.name) = LOWER(p.company_name)
WHERE LOWER(c.name) = LOWER($company_from_action);
```

### Time Decay / Freshness Calculation

```
days_old = (NOW() - action.created_at) in days
time_sensitivity = action metadata or inferred from type

IF action.type = 'Follow-on Eval':
    freshness = max(0.2, 1.0 - (days_old / 30))  -- 30-day window
ELIF action.type = 'Meeting/Outreach':
    freshness = max(0.2, 1.0 - (days_old / 14))  -- 14-day window
ELSE:
    freshness = max(0.2, 1.0 - (days_old / 60))  -- 60-day window (research is less time-sensitive)
```

### Full Calculation Example

Action: "Research Composio competitive landscape"
- ENIAC raw score: 7.2 -> `(7.2 / 10) * 0.30 = 0.216`
- Thesis: "Agentic AI Infrastructure" conviction = "Evolving Fast" -> `1.0 * 0.20 = 0.200`
- Diminishing returns: n=0 (first research) -> `(1.0 * 0.7^0) * 0.20 = 0.200`
- Portfolio: not a portfolio company -> `0.3 * 0.15 = 0.045`
- Freshness: created 2 days ago, research type -> `(1.0 - 2/60) * 0.15 = 0.145`
- **Strategic score: 0.216 + 0.200 + 0.200 + 0.045 + 0.145 = 0.806**

At 0.806, this auto-grades to depth 3 (Ultra) via score-based grading.

---

## The Diverge/Converge Lens

### Diverge Phase (system-wide, not Megamind-specific)

The system naturally diverges:
- Content Agent processes a video -> proposes 3 actions
- Each action, if executed, generates new information -> could spawn more actions
- Datum Agent enriches an entity -> reveals connections -> more potential actions
- Thesis evidence accumulates -> conviction changes -> portfolio implications -> more actions

This divergence is HEALTHY in moderation. It ensures the system doesn't miss signals.

### Converge Phase (Megamind's domain)

Your 5-step convergence process:

1. **Filter:** Not all proposed actions deserve attention. Apply strategic ROI threshold.
   - Score < 0.3: Skip (depth 0). Action dismissed.
   - Score 0.3-0.6: Scan (depth 1). Quick assessment only.
   - Only scores >= 0.6 get meaningful investigation.

2. **Cluster:** Group related actions by thesis thread, company, or person.
   ```sql
   SELECT thesis_connection, COUNT(*) as action_count,
          AVG(relevance_score) as avg_score
   FROM actions_queue
   WHERE status IN ('Proposed', 'Accepted')
   GROUP BY thesis_connection
   ORDER BY action_count DESC;
   ```
   Evaluate the CLUSTER, not individual items. A thesis with 8 open actions needs pruning,
   not more actions.

3. **Rank:** Within each cluster, apply diminishing returns.
   ```sql
   SELECT COUNT(*) FROM depth_grades
   WHERE thesis_connections && ARRAY[$thesis_name]
     AND execution_status = 'completed'
     AND created_at > NOW() - INTERVAL '14 days';
   ```
   The 3rd research action on the same thesis has marginal_value = base * 0.343.

4. **Cap:** Enforce hard ceiling on actions per thesis thread.
   - Max 5 human + 3 agent actions open per thesis
   - Query:
     ```sql
     SELECT assigned_to, COUNT(*) FROM actions_queue
     WHERE thesis_connection = $thesis_name
       AND status IN ('Proposed', 'Accepted', 'In Progress')
     GROUP BY assigned_to;
     ```
   - Beyond cap: set status = 'Queued'

5. **Resolve:** Track action completion. Every completed action should net-reduce open count.
   - In cascades: `actions_resolved >= actions_generated`
   - In assessments: check 7-day convergence ratio

### When to Stop Exploring

Stop expanding investigation when ANY of these apply:
- Diminishing returns n >= 3 (marginal value < 0.343x)
- Per-thesis action cap reached
- Daily depth budget > $8 (approaching $10 limit)
- Convergence ratio < 0.8 (system is diverging)
- No new key questions remain on the thesis thread

---

## Megamind-Specific Database Tables

### depth_grades

```sql
-- Key columns for strategic reasoning:
-- action_id: FK to actions_queue.id
-- auto_depth: 0=Skip, 1=Scan, 2=Investigate, 3=Ultra
-- approved_depth: NULL until approved, then final depth
-- strategic_score: 0.0-1.0 (your ROI calculation)
-- reasoning: TEXT — why this depth was assigned
-- thesis_connections: TEXT[] — connected thesis thread names
-- diminishing_returns_n: INT — how many similar completed in window
-- marginal_value: REAL — strategic_score * 0.7^n
-- execution_status: pending | approved | executing | completed | skipped
-- execution_agent: 'content' | 'datum'
-- execution_prompt: depth-calibrated prompt text
-- execution_cost_usd: actual cost after completion
```

### cascade_events

```sql
-- Key columns:
-- trigger_type: 'depth_completed' | 'conviction_change' | 'new_thesis' | 'contra_signal' | 'portfolio_event'
-- trigger_source_id: FK to triggering record
-- affected_thesis_threads: TEXT[] — blast radius
-- affected_companies: TEXT[] — blast radius
-- affected_actions_count: INT — how many open actions in blast radius
-- actions_rescored: INT — meaningful score changes (delta > 0.1)
-- actions_resolved: INT — closed as redundant/superseded
-- actions_generated: INT — new actions created
-- net_action_delta: INT — generated - resolved (should be <= 0)
-- convergence_pass: BOOLEAN — TRUE if net_action_delta <= 0
-- cascade_report: JSONB — full structured report
```

### strategic_assessments

```sql
-- Key columns:
-- assessment_type: 'daily' | 'post_cascade' | 'on_demand'
-- total_open_actions, total_open_human_actions, total_open_agent_actions
-- bucket_distribution: JSONB — per-bucket coverage analysis
-- thesis_momentum: JSONB — per-thesis conviction and velocity
-- stale_actions: INT — actions open > 14 days
-- concentration_warnings: TEXT[] — over-concentrated thesis threads
-- underserved_buckets: TEXT[] — buckets with no 7-day resolutions
-- recommendations: JSONB — actionable recommendations
-- convergence_trend: 'converging' | 'stable' | 'diverging'
-- convergence_ratio: REAL — resolved/generated over 7 days
```

### strategic_config

```sql
-- Key-value store for Megamind configuration:
-- trust_level: "manual" | "semi-auto" | "auto"
-- trust_stats: {"total_graded": N, "auto_accepted": N, "overridden": N}
-- daily_depth_budget_usd: 10.0
-- diminishing_returns_decay: 0.7
-- diminishing_returns_window_days: 14
-- action_cap_human_per_thesis: 5
-- action_cap_agent_per_thesis: 3
-- staleness_warning_days: 14
-- staleness_resolution_days: 30
-- cascade_chain_limit: 1
-- convergence_critical_threshold: 0.8
-- convergence_critical_consecutive_days: 3
```

---

## Priority Bucket Reference

| # | Bucket | Always-On Weight | When Highest |
|---|--------|-----------------|-------------|
| 1 | New Cap Tables | Highest always | Always |
| 2 | Deepen Existing Cap Tables | High always | Portfolio decision periods |
| 3 | New Founders/Companies (DeVC) | High always | Active pipeline periods |
| 4 | Thesis Evolution | Variable | When capacity exists (buckets 1-3 adequately covered) |

Actions serving Bucket 1 or 2 get structural priority in strategic ROI.
Bucket 4 actions are subject to strongest diminishing returns decay.
