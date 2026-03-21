# Skill: Scoring SQL Tools

Complete reference for all scoring-related SQL functions. Every agent that reads, writes, or reasons about scores should load this skill.

**Connection:** All queries run via `psql $DATABASE_URL` (on droplet) or via the Supabase MCP tool.

---

## 1. Core Scoring Functions

### `compute_user_priority_score(action_row actions_queue) -> numeric`

The main scoring function. Takes a full `actions_queue` row and returns a score (1.0 to ~9.5).

**You almost never call this directly.** It runs automatically via triggers and `refresh_action_scores()`. Use it only for what-if analysis:

```sql
-- What would this action score if we changed its priority?
SELECT compute_user_priority_score(a.*) as hypothetical_score
FROM actions_queue a WHERE id = 42;
```

### `refresh_action_scores() -> void`

Recomputes scores for ALL proposed actions. Updates `user_priority_score` and `score_confidence` in place.

```sql
SELECT refresh_action_scores();
```

**When to call:** After bulk data changes (new interactions, updated portfolio data, thesis changes). Not needed for single-action updates (triggers handle those).

### `refresh_active_scores() -> TABLE(refreshed int, max_drift numeric)`

Recomputes scores only for actions that have drifted from their stored score. More efficient than full refresh.

```sql
SELECT * FROM refresh_active_scores();
-- Returns: refreshed=12, max_drift=0.45
```

### `normalize_all_scores() -> TABLE(updated_count int, min_score numeric, max_score numeric, avg_score numeric, max_bucket_pct numeric)`

Recalibrates the `factor_population_stats` table (mean/stddev for z-score normalization), then recomputes all scores.

```sql
SELECT * FROM normalize_all_scores();
```

**When to call:** After adding many new actions, or when score diversity drops below 20 distinct values. This is a heavier operation.

### `snapshot_scores() -> integer`

Captures current scores into `score_history` table. Returns count of snapshots taken.

```sql
SELECT snapshot_scores();
-- Returns: 41 (number of proposed actions snapshotted)
```

**Runs on cron every 30 minutes.** You can call manually before/after a scoring change to capture the delta.

---

## 2. Score Explanation Functions

### `explain_score(action_id bigint) -> jsonb`

The technical explainer. Returns full breakdown of how a score was computed.

```sql
SELECT explain_score(42);
```

**Returns:**
```json
{
  "action_id": 42,
  "action_preview": "Schedule call with CEO of...",
  "action_type": "Portfolio Check-in",
  "final_score": 8.72,
  "explanation": "Portfolio Check-in scoring 8.7/10 (top 5% globally). Driven by: high strategic importance (Megamind 8.5/10). Boosts: P1 priority +7%; Portfolio Check-in type boost +15%; involves John Smith (Core) +14%.",
  "global_percentile": 95.1,
  "type_percentile": 100.0,
  "base_model": { "base_score": 7.234, "weighted_factor": 0.6927 },
  "factors_raw": { "time_sensitivity": 0.700, "conviction_change": 0.500, ... },
  "factors_normalized": { "time_sensitivity": 0.723, "conviction_change": 0.481, ... },
  "multipliers": {
    "priority": 1.070, "type": 1.150, "source": 1.000,
    "network": 1.140, "network_person": "John Smith",
    "depth": 1.100, "depth_grade": 3,
    "freshness": 1.045, "interaction": 1.030,
    "obligation": 1.000, "preference": 1.020,
    "acceptance": 1.040, "cindy_intelligence": 1.000,
    "thesis_momentum": 1.050, "portfolio_health": 1.080,
    "financial_urgency": 1.000, "key_question_relevance": 1.030,
    "verb_pattern": 1.000,
    "combined": 1.350, "combined_capped": 1.350
  },
  "portfolio_context": { "company": "Acme Corp", "ownership_pct": 4.5, ... },
  "decay": { "days_old": 2.3, "decay_factor": 1.0000 },
  "formula": "final = sigmoid8(base_score x combined_mult(17, cap=1.35) x time_decay)",
  "model_version": "v5.2-L96"
}
```

**Key fields to examine:**
- `multipliers.combined_capped` — if this equals 1.35, the action is hitting the boost ceiling
- `multipliers.*` — any value significantly different from 1.0 is an active driver
- `global_percentile` — where this action ranks vs. all others
- `portfolio_context` — full portfolio company data if matched

### `narrative_score_explanation(action_id bigint) -> jsonb`

Human-readable narrative explanation. Better for presenting to the user or for agent reasoning.

```sql
SELECT narrative_score_explanation(42);
```

**Returns:**
```json
{
  "action_id": 42,
  "score": 8.7,
  "narrative": "This portfolio check-in scores 8.7/10 -- in the top 5% of all actions. Acme Corp is your highest-ownership position at 4.50% ($150K invested). You want to double down (Strong Pro-Rata follow-on). Health status is Yellow -- some concerns worth monitoring. Involves John Smith (Core priority in your network). Connected to your \"AI Infrastructure\" thesis (conviction: High) -- thesis has strong momentum right now, boosting priority. 2 obligation(s) connected to this action. Why this ranks high: P0 priority (+15%). Megamind rates this strategically important (8.5/10).",
  "technical_explanation": { ... full explain_score output ... },
  "model_version": "v5.2-L96"
}
```

**Use this for:** Agent-to-user communication, WebFront display, digest summaries. The narrative ties together portfolio context, network relationships, thesis connections, and obligations into a coherent story.

### `score_explainer(action_id integer) -> jsonb`

Lightweight explainer that returns just the action preview, score, and a short explanation string.

```sql
SELECT score_explainer(42);
```

### `agent_scoring_context(action_id bigint) -> jsonb`

The FULL context package for agent reasoning. Returns everything in `explain_score()` PLUS:
- All portfolio company details (ownership, entry cheque, valuations, outcomes, health, follow-on decisions, key questions, financials)
- Network person context (role, priority, RYG, sourcing flow)
- Thesis thread details (conviction, evidence previews, key companies)
- Related interactions (last 30 days, with deal/thesis signal flags)
- Obligations (with overdue status, blended priority)
- Depth grade (auto depth, approved depth, reasoning, marginal value)
- Score history (last 10 snapshots)
- Score trend (RISING/FALLING/STABLE/VOLATILE)
- Agent instructions for reasoning about the score

```sql
SELECT agent_scoring_context(42);
```

**This is the go-to function for any agent that needs to reason about whether a score is appropriate.**

---

## 3. Monitoring and Health Functions

### `scoring_regression_test() -> TABLE(test_name text, passed boolean, detail text)`

Runs 22 regression tests on the scoring system. Returns pass/fail for each.

```sql
SELECT test_name, passed, detail FROM scoring_regression_test();
```

**Tests include:**
1. `score_range_1_10` — all scores within bounds
2. `score_diversity` — >20 distinct score values
3. `priority_hierarchy_p0_gt_p2` — P0 avg > P2 avg
4. `no_dominant_bucket` — no action_type > 40% of queue
5. `pipeline_gt_thesis` — pipeline actions score higher than thesis
6. `top5_dedup_clean` — no near-duplicate actions in top 5
7. `preference_weights_safe` — all preference rows have sufficient samples
8. `all_proposed_scored` — no NULL scores on proposed actions
9. `interaction_coverage_30pct` — at least 30% of actions have interaction boost
10. `confidence_populated` — confidence scores assigned
11-17. Individual multiplier functionality tests
18. `agent_scoring_context_functional` — context function returns valid JSONB
19. `context_enrichment_coverage` — scoring_factors enrichment ran
20. `agent_feedback_store_exists` — feedback table accessible
21. `verb_pattern_multiplier_functional` — verb patterns active
22. `score_compression_under_35pct` — top bucket not overloaded

### `scoring_health` (VIEW)

Quick health dashboard. Returns a single row:

```sql
SELECT * FROM scoring_health;
```

**Columns:** `total`, `total_proposed`, `avg_score`, `std_score`, `min_raw`, `max_raw`, `distinct_scores`, `compression_check`, `pct_9_10`, `diversity_check`, `hierarchy_check`, `pipeline_check`, `portfolio_avg`, `network_avg`, `pipeline_avg`, `thesis_avg`, `health_score` (0-10), `model_version`.

**Target state:** health_score = 10, all checks PASS.

### `scoring_intelligence_report() -> jsonb`

Comprehensive intelligence report combining top-20 actions (with narratives), health stats, factor distributions, multiplier impact analysis, type breakdown, confidence stats, velocity, agent feedback, and recommendations.

```sql
SELECT scoring_intelligence_report();
```

**Returns a large JSONB with sections:**
- `top_20_actions` — top actions with full narrative explanations
- `health` — scoring_health data
- `factor_distribution` — average values for each factor
- `multiplier_impact` — per-multiplier stats (avg, max, boosted count, percentage)
- `type_breakdown` — per-action-type stats
- `confidence_stats` — confidence distribution
- `velocity` — scoring velocity metrics
- `agent_feedback` — summary of agent feedback
- `recommendations` — auto-generated recommendations for improvement

### `scoring_velocity() -> jsonb`

Tracks how fast scores are changing across the system.

```sql
SELECT scoring_velocity();
```

### `scoring_validation() -> jsonb`

Validates current scoring state and returns any issues found.

```sql
SELECT scoring_validation();
```

### `scoring_system_context() -> jsonb`

Returns overall system context for scoring — model version, multiplier count, factor weights, and current configuration.

```sql
SELECT scoring_system_context();
```

---

## 4. Score Trend and History

### `score_trend(action_id integer) -> jsonb`

Analyzes score history and returns the trend:

```sql
SELECT score_trend(42);
```

**Returns:**
```json
{
  "trend": "RISING",
  "current_score": 8.72,
  "previous_score": 8.15,
  "change": 0.57,
  "change_pct": 7.0,
  "snapshots_analyzed": 8,
  "period_days": 3.5
}
```

### `score_summary_api(limit integer DEFAULT 20) -> jsonb`

API-ready summary of top-N proposed actions with scores and explanations.

```sql
SELECT score_summary_api(10);
```

---

## 5. Score Override and Experiment Functions

### `apply_agent_score_overrides() -> jsonb`

Processes pending agent feedback (score_override and score_adjustment types) and applies them to action scores. Updates `adjustment_applied = true` on processed feedback.

```sql
SELECT apply_agent_score_overrides();
```

**When to call:** When `scoring_regression_test()` shows pending feedback, or periodically.

### `run_scoring_experiment(name text, model_name text, description text, config jsonb) -> jsonb`

Runs an A/B scoring experiment with modified parameters. Does NOT change production scores — returns hypothetical results for comparison.

```sql
SELECT run_scoring_experiment(
  'test_higher_strategic_weight',
  'v5.2-experiment',
  'What if strategic weight was 0.25 instead of 0.20?',
  '{"strategic_weight": 0.25}'::jsonb
);
```

---

## 6. Preference Learning Functions

### `update_preference_from_outcome(action_id integer, outcome text) -> void`

Records a user decision on an action and updates preference weights. Call this when the user accepts, dismisses, or rates an action.

```sql
-- User accepted the action (found it helpful)
SELECT update_preference_from_outcome(42, 'helpful');

-- User loved it
SELECT update_preference_from_outcome(42, 'gold');

-- User skipped/dismissed
SELECT update_preference_from_outcome(42, 'skip');
```

**Outcome values and weight deltas:**
| Outcome | Delta | Meaning |
|---------|-------|---------|
| `gold` | +0.3 | Highly valuable action |
| `helpful` | +0.1 | Useful action |
| `skip` | -0.2 | Not useful, dismissed |

Updates `preference_weight_adjustments` for 4 dimensions: `action_type`, `priority`, `source`, `thesis` (if present). Uses running average weighted by sample_count.

### `update_preference_from_rating(action_id integer, rating integer) -> void`

Alternative: record a 1-5 star rating instead of outcome category.

### `preference_insights() -> jsonb`

Returns current state of preference learning — which action types, priorities, sources are being boosted or penalized by user behavior.

```sql
SELECT preference_insights();
```

---

## 7. Individual Multiplier Functions

These are helper functions called by `compute_user_priority_score()`. Agents can call them directly to understand a specific signal:

| Function | Input | Returns | What It Measures |
|----------|-------|---------|-----------------|
| `cindy_intelligence_multiplier(action_row)` | actions_queue row | numeric | Cindy comms signals |
| `thesis_momentum_multiplier(action_row)` | actions_queue row | numeric | Thesis evolution speed |
| `thesis_breadth_multiplier(action_row)` | actions_queue row | numeric | Cross-thesis connections |
| `portfolio_health_multiplier(action_row)` | actions_queue row | numeric | Portfolio company health/importance |
| `financial_urgency_multiplier(action_row)` | actions_queue row | numeric | Cash runway urgency |
| `key_question_relevance(action_row)` | actions_queue row | numeric | Semantic match to portfolio KQs |
| `obligation_urgency_multiplier(action_row)` | actions_queue row | numeric | Overdue obligation pressure |
| `interaction_recency_boost(action_row)` | actions_queue row | numeric | Recent interaction signal |
| `action_verb_pattern_multiplier(action_row)` | actions_queue row | numeric | Verb pattern accept/dismiss history |
| `is_portfolio_linked(text, text)` | action_text, source | boolean | Checks if action involves portfolio co |
| `normalize_factor(val, mean, stddev)` | raw, pop_mean, pop_std | numeric | Z-score normalization |

**Example: Check all multipliers for a specific action:**

```sql
SELECT
  a.id,
  LEFT(a.action, 80) as action_preview,
  ROUND(a.user_priority_score, 2) as score,
  ROUND(cindy_intelligence_multiplier(a), 3) as cindy,
  ROUND(thesis_momentum_multiplier(a), 3) as thesis_mom,
  ROUND(thesis_breadth_multiplier(a), 3) as thesis_breadth,
  ROUND(portfolio_health_multiplier(a), 3) as portfolio,
  ROUND(financial_urgency_multiplier(a), 3) as financial,
  ROUND(key_question_relevance(a), 3) as kq,
  ROUND(obligation_urgency_multiplier(a), 3) as obligation,
  ROUND(interaction_recency_boost(a), 3) as interaction,
  ROUND(action_verb_pattern_multiplier(a), 3) as verb_pattern
FROM actions_queue a
WHERE a.status = 'Proposed'
ORDER BY a.user_priority_score DESC
LIMIT 10;
```

---

## 8. Related Scoring Functions

### `compute_portfolio_strategic_score(portfolio_id) -> numeric`

Computes strategic importance of a portfolio company (not an action). Used by Megamind for portfolio prioritization.

### `entity_freshness_score(entity_type, entity_id) -> numeric`

How recently an entity (person, company, thesis) has been updated/interacted with.

### `interaction_intelligence_score(interaction_id) -> numeric`

Scores the intelligence value of an interaction record.

### `relationship_strength_score(person_id) -> numeric`

Computes relationship strength based on interaction frequency, obligation fulfillment, and engagement quality.

### `recalibrate_strategic_scores() -> void`

Recomputes strategic scores for all portfolio companies. Called by M5 machine periodically.

### `rescore_related_actions(entity_type, entity_id) -> void`

After updating an entity (portfolio, network, thesis), rescores all actions linked to that entity.

### `score_action_thesis_relevance(action_id) -> numeric`

Computes how relevant an action is to its linked thesis thread.

---

## Common Agent Workflows

### "Is this score right?"
```sql
-- 1. Get full context
SELECT agent_scoring_context(ACTION_ID);
-- 2. Check narrative explanation
SELECT narrative_score_explanation(ACTION_ID);
-- 3. If score seems wrong, submit feedback
SELECT record_agent_feedback(ACTION_ID, 'megamind', 'score_adjustment', 'Score too low because...', 8.5);
```

### "What are the top actions right now?"
```sql
SELECT score_summary_api(20);
-- or for full intelligence:
SELECT scoring_intelligence_report();
```

### "Is the scoring system healthy?"
```sql
SELECT * FROM scoring_health;
SELECT test_name, passed, detail FROM scoring_regression_test() WHERE NOT passed;
```

### "What changed since last snapshot?"
```sql
SELECT * FROM refresh_active_scores();
```
