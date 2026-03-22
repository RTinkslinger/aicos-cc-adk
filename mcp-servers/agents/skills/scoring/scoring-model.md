# Skill: Scoring Model

How the AI CoS user priority scoring system works. Read this before reasoning about action scores, recommending score changes, or interpreting why an action ranks where it does.

---

## Model Version: v5.5-M5L12

The scoring model is a **multiplicative model** with z-score normalization and 18 multipliers. It produces scores from 1.0 to ~9.5 (sigmoid-capped at 8.0 for top-end granularity).

## Architecture Overview

```
Final Score = sigmoid8(base_score x combined_mult x time_decay)
```

Where:
- `base_score` = weighted combination of 7 normalized factors (1.0 to 10.0 range)
- `combined_mult` = product of 17 multipliers (capped at [0.4, 1.35])
- `time_decay` = 0.97^(days_old - 14) for actions older than 14 days

---

## The 7 Base Factors

These factors are extracted from `actions_queue.scoring_factors` (JSONB) or inferred from action_type/source when scoring_factors is missing.

| Factor | Weight | DB Field | Description |
|--------|--------|----------|-------------|
| **time_sensitivity** | 0.115 | `scoring_factors->>'time_sensitivity'` | How time-critical is this action? |
| **conviction_change** | 0.170 | `scoring_factors->>'conviction_change_potential'` | Could this change Aakash's conviction on a thesis? |
| **stakeholder_impact** | 0.170 | `scoring_factors->>'bucket_impact'` | How much does this affect key stakeholders? |
| **effort_vs_impact** | 0.115 | `scoring_factors->>'effort_vs_impact'` | Ratio of expected impact to effort required |
| **action_novelty** | 0.080 | `scoring_factors->>'action_novelty'` | Is this new information vs. repeat? |
| **irgi_relevance** | 0.150 | `actions_queue.irgi_relevance_score` | Relevance to IRGI framework |
| **strategic_score** | 0.200 | `actions_queue.strategic_score / 10.0` | Megamind's strategic importance rating |

**Weights sum to 1.0.** Strategic score has the highest weight (0.20), followed by conviction_change and stakeholder_impact (0.17 each).

### Z-Score Normalization

Raw factors are normalized against the population distribution stored in `factor_population_stats`:

```sql
normalized = sigmoid(0.5 + 0.5 * (val - pop_mean) / pop_stddev)
```

This ensures factors are comparable regardless of their raw scale. If population stats are unavailable, raw values are used directly.

### Base Score Calculation

```
weighted_factor = sum(weight_i x normalized_factor_i)

-- If content agent provided an original score, blend it in:
weighted_factor = 0.9 * weighted_factor + 0.1 * original_score_normalized

base_score = 1.0 + (weighted_factor * 9.0)  -- maps to 1-10 range
```

---

## The 17 Multipliers

Each multiplier adjusts the base score up or down. They are multiplied together, then capped at [0.4, 1.35].

### 1. Priority Multiplier
| Priority | Multiplier |
|----------|-----------|
| P0 (Now) | 1.15 |
| P1 (Next) | 1.07 |
| P2 (Later) | 1.00 |
| P3 (Someday) | 0.90 |

### 2. Type Multiplier
Action type determines base importance hierarchy:

| Type Pattern | Multiplier | Rationale |
|-------------|-----------|-----------|
| portfolio, check-in, follow-on | 1.15 | Portfolio = highest priority |
| portfolio-linked meetings | 1.15 | Meetings with portfolio companies |
| pipeline, deal | 1.12 | Active deal flow |
| network, meet, connect, outreach | 1.08 | Relationship building |
| thesis, research, evidence | 0.82-0.92 | Agent-delegable (0.92 if strategic_score > 7) |
| content, digest | 0.85 | Agent-delegable |
| (fallback text matching) | varies | Checks action text for portfolio/meet/thesis keywords |

**Key insight:** Thesis/research actions get PENALIZED because they are agent-delegable. Only surface to Aakash when strategic_score is high (>7), which reduces the penalty from -18% to -8%.

### 3. Source Multiplier
| Source | Multiplier |
|--------|-----------|
| Cindy (comms agent) | 1.08 |
| ContentAgent | 1.02 |
| Other | 1.00 |

### 4. Network Multiplier
Matches person names in the action text against the `network` table. Uses actual DB priority values (P0/P1/P2 with emoji, not Core/High/Medium/Low):

| Person Priority | Base Boost |
|----------------|-----------|
| P0 (contains "P0") | +12% |
| P1 (contains "P1") | +8% |
| P2 (contains "P2") | +4% |
| Any other value | +2% |
| NULL (name matched, no priority) | +3% (fallback) |

Additional +2% if person's RYG status is Green. Falls back to embedding similarity (>0.65 threshold) if no text match found. Embedding fallback also uses P0/P1/P2 matching.

### 5. Depth Multiplier
Uses `depth_grades.auto_depth` or `approved_depth` (if set, takes precedence). 0-4 scale from Megamind:

| Depth Grade | Multiplier |
|-------------|-----------|
| 4 (deepest) | 1.15 |
| 3 | 1.05-1.10 (1.10 if strategic_score > 7) |
| 2 | 1.02 |
| 1 (shallow) | 1.00 (neutral — v5.4 fix, was 0.93) |
| 0 (skip) | 0.90 |

### 6. Freshness Multiplier
For Proposed actions: `1.0 + 0.05 * e^(-0.1 * days_old)`. New actions get a small boost that decays exponentially.

### 7. Interaction Multiplier
Uses `interaction_recency_boost()` to check for recent interactions linked to this action. Boost capped at +8%.

### 8. Preference Multiplier
Learned from user accept/dismiss behavior via `preference_weight_adjustments` table. Adjusts based on action_type and priority patterns. Capped at +/-10%.

### 9. Acceptance Multiplier
Historical accept vs. dismiss rate for this action_type. Needs at least 3 decided actions to activate. Adjusts up to +/-8%.

### 10. Obligation Multiplier
From `obligation_urgency_multiplier()` (v2, M5L12). Activates for ANY action with `obligation_action_links`, regardless of source. Factors in blended_priority (from M8 Cindy's differentiated priorities 0.43-0.80), overdue days, obligation_type (I_OWE_THEM +4%), and fulfilled status (0.75x stale penalty). Orphan penalty (0.92x) only applies to `obligation_followup`-sourced actions with no links. Cap: [0.75, 1.25]. Coverage: 46% of proposed actions.

### 11. Cindy Intelligence Multiplier
From `cindy_intelligence_multiplier()`. Boosts actions where Cindy (comms agent) has detected signals in emails/interactions.

### 12. Thesis Momentum Multiplier
From `thesis_momentum_multiplier()`. Boosts actions on theses that are actively evolving (recent evidence additions). Penalizes stale theses.

### 13. Thesis Breadth Multiplier (v5.2)
From `thesis_breadth_multiplier()`. Boosts actions that connect to multiple theses. This was the strongest discriminator for accepted vs. dismissed actions in regression analysis.

### 14. Portfolio Health Multiplier
From `portfolio_health_multiplier()`. Accounts for:
- Ownership tier (higher ownership = more important)
- Company health status (Red/Yellow boosts attention)
- Follow-on decision (SPR = boost, Token/Zero = penalize)
- Spikey/differentiated flag

### 15. Financial Urgency Multiplier
From `financial_urgency_multiplier()`. Triggers when portfolio company is running low on cash (fumes_date approaching).

### 16. Key Question Relevance
From `key_question_relevance()`. Uses **semantic embedding matching** between action text and portfolio company key questions (stored in `portfolio_key_questions` with embeddings). Boosts actions that directly address unanswered key questions.

### 17. Verb Pattern Multiplier
From `action_verb_pattern_multiplier()`. Learns from user behavior — actions phrased as "flag risk," "explore opportunity," etc. have different accept/dismiss rates. This multiplier adjusts scores based on the action's verb pattern matching historical outcomes.

---

## Time Decay

Actions older than 14 days begin decaying:
```
decay_factor = 0.97 ^ max(0, days_old - 14)
```

At 30 days old: 0.97^16 = 0.61 (39% reduction).
At 60 days old: 0.97^46 = 0.25 (75% reduction).

---

## Sigmoid Wall at 8.0

Prevents score compression at the top:
```
if raw > 8.0:  final = 8.0 + (raw - 8.0) / (1.0 + (raw - 8.0) * 0.5)
if raw < 1.0:  final = 1.0 - (1.0 - raw) / (1.0 + (1.0 - raw))
```

This creates granularity in the 8-10 range. A raw score of 10.0 maps to ~9.0. A raw score of 12.0 maps to ~9.3.

---

## Score Confidence

Computed by `compute_score_confidence()`. Measures how well-supported the score is:
- High confidence (>0.7): scoring_factors present, network/portfolio context matched, interactions linked
- Medium confidence (0.4-0.7): some factors present, partial context
- Low confidence (<0.4): missing scoring_factors, no context enrichment

---

## How to Read `agent_scoring_context(action_id)`

This is the primary function agents should call to understand an action's score. It returns a comprehensive JSONB object with:

| Key | What It Contains |
|-----|-----------------|
| `action_id`, `action_text`, `action_type` | Basic action info |
| `scores.final_score` | The computed score |
| `scores.confidence` | How confident the model is |
| `scores.explanation` | Natural language explanation |
| `scoring_factors` | The raw 7 input factors |
| `multipliers` | All 17 multiplier values (see which are boosting/penalizing) |
| `factors_normalized` | Z-score normalized factors |
| `portfolio_context` | Full portfolio company context (ownership, health, follow-on, key questions, financials) |
| `network_context` | Person info (priority, RYG, role) |
| `thesis_connections` | Linked thesis threads with conviction, evidence previews |
| `related_interactions` | Last 30 days of linked interactions |
| `obligations` | Connected obligations (overdue = relationship risk) |
| `depth_grade` | Megamind's depth assessment |
| `score_history` | Last 10 score snapshots (for trend) |
| `score_trend` | RISING, FALLING, STABLE, or VOLATILE |
| `agent_instructions` | Guidance on what to consider |

### Reading Multipliers

When analyzing a score, look at the multipliers object. A multiplier of 1.0 means neutral. Greater than 1.0 = boost. Less than 1.0 = penalty.

**Key patterns to check:**
1. **type < 0.90** = thesis/research penalty (consider: is strategic_score high enough to justify surfacing?)
2. **network > 1.05** = strong person match (Core/High priority contact)
3. **portfolio_health > 1.05** = portfolio company needs attention (Red health, high ownership)
4. **verb_pattern < 0.90** = user historically dismisses this action pattern
5. **obligation > 1.0** = overdue obligations create urgency
6. **thesis_momentum > 1.03** = thesis is actively evolving, good time to act
7. **thesis_momentum < 0.97** = stale thesis, may need fresh evidence first

---

## Score Thresholds (Action Surface Rules)

| Score Range | Interpretation | Surface To User? |
|-------------|---------------|-----------------|
| >= 7.0 | High priority action | Yes, surface prominently |
| 4.0 - 6.9 | Medium priority | Yes, as low-confidence suggestion |
| < 4.0 | Low priority | Context enrichment only, don't surface |

---

## Priority Hierarchy (MANDATORY)

The scoring model enforces this ranking:
```
Portfolio + Network actions > Pipeline/Deal actions > Thesis/Research actions > Content actions
```

Portfolio actions score highest because:
1. Type multiplier: 1.15 (vs. 0.82 for thesis)
2. Portfolio health multiplier: adds more for high-ownership, Red health
3. Financial urgency multiplier: fumes alerts
4. Key question relevance: semantic match to portfolio questions

Thesis/research actions score lower because they are **agent-delegable** — ENIAC should handle most research work autonomously, only surfacing to Aakash when human judgment is required.

---

## Score History and Trends

Scores are snapshotted by `snapshot_scores()` (runs on cron every 30 min). The `score_trend()` function analyzes the last 10 snapshots and returns:

| Trend | Meaning |
|-------|---------|
| RISING | Score increasing over recent snapshots |
| FALLING | Score decreasing (decay, preference shifts) |
| STABLE | Score steady (+/- 0.3) |
| VOLATILE | Score fluctuating (data changing frequently) |
| NEW | Fewer than 3 snapshots available |
