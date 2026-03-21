# M5 Scoring Machine - Perpetual Loop v7

**Date:** 2026-03-21
**Model Version:** v5.2 (17 multipliers, semantic KQ, thesis breadth)
**Previous:** v5.1-L96 (16 multipliers, keyword/trigram KQ only)

## Score Distribution (Post v5.2)

| Status | Count | Avg Score | Min | Max | StdDev |
|--------|-------|-----------|-----|-----|--------|
| Accepted | 10 | 8.58 | 6.74 | 9.19 | 0.88 |
| Proposed | 42 | 7.59 | 5.11 | 9.23 | 1.28 |
| Dismissed | 92 | 2.50 | 1.00 | 4.00 | 0.88 |

**Separation gap:** 6.08 (Accepted vs Dismissed avg)

## Changes This Loop

### 1. Cron Job: Score Refresh (every 30 min)

**Problem:** Scores drifted as external tables changed (network, portfolio, depth_grades, time_decay). No automatic refresh existed.

**Solution:** Created `refresh_active_scores()` function + cron job `score-refresh` (*/30 * * * *). Only updates Proposed/Accepted actions with drift > 0.01 points.

Also added `preference-weight-refresh` cron (15 * * * *) to keep preference_weight_adjustments table current from accept/dismiss behavior.

**Cron IDs:** 24 (score-refresh), 25 (preference-weight-refresh)

### 2. Semantic KQ Matching (Embedding-Based)

**Problem:** key_question_relevance was stuck at 23.1% match rate. Root cause: per-line trigram similarity topped out at 0.13 (threshold 0.15) and keyword overlap was 0/N for semantically related but lexically different text.

**Example:** Action "Unifize founder deep dive: agent-native architecture or doubling down on traditional SaaS?" vs key question "AI differentiation sustainability: can MasterControl/Veeva replicate the collaboration-first approach?" -- clearly related but zero keyword overlap and trigram 0.067.

**Solution:**
- Created `portfolio_key_questions` table (386 rows: 222 key_questions + 164 high_impact)
- Each row gets its own 1024-dim embedding via existing pipeline
- Added Strategy C to key_question_relevance(): cosine similarity >= 0.55 for key_questions, >= 0.50 for high_impact
- Created triggers for auto-embedding new questions
- Backfilled 386 embedding jobs (225/386 done, rest processing every 2 min)

**Result:** KQ match rate: **23.1% -> 40.4%** (+17.3pp). Embedding backfill completed (375/386 = 97.2%). Avg KQ multiplier rose from 1.0288 to 1.0577.

### 3. Thesis Breadth Multiplier (New - 17th Multiplier)

**Problem:** Accepted actions have 3.4 avg thesis connections vs 1.1 for dismissed (3x discriminator). The model had no signal for thesis connection count -- only thesis momentum of the best single match.

**Solution:** Created `thesis_breadth_multiplier()`:
- 1 thesis = neutral (1.0)
- 2 theses = +3% (1.03)
- 3 theses = +6% (1.06)
- 4+ theses = +8% (1.08)

Integrated as 17th multiplier in `compute_user_priority_score()`.

**Impact:** Accepted avg: 8.50 -> 8.58 (+0.08), Accepted min: 6.25 -> 6.74 (+0.49). The floor lift is the big win -- multi-thesis actions that were previously borderline now score appropriately.

### 4. Preference Weights Seeded

`preference_weight_adjustments` was empty (update_preference_weights() had a bug with status name matching). Manually seeded via direct SQL. All action_types show negative weights (correctly reflecting high dismiss rate). Heaviest penalties: Pipeline (-0.40), Pipeline Action (-0.40), Thesis Update (-0.40). Lightest: Portfolio Check-in (-0.26).

## Accepted Action Pattern Analysis

| Signal | Accepted (n=10) | Dismissed (n=92) | Discriminative Power |
|--------|-----------------|-------------------|---------------------|
| Portfolio type | 60% | 33% | +27pp |
| **Thesis connections** | **3.4 avg** | **1.1 avg** | **3.1x (strongest)** |
| Portfolio-linked | 50% | 37% | +13pp |
| Meeting type | 20% | 32% | -12pp |
| Research type | 20% | 13% | +7pp |
| Priority strength | 0.69 | 0.74 | -0.05 (counter-intuitive) |

**Key insight:** Thesis connection count is the single strongest discriminator. The model now captures this via thesis_breadth_multiplier. Priority is NOT discriminative (dismissed actions actually had slightly higher P0/P1 rate).

## Score Stability

Pre-cron drift was minimal (max 0.06 points). After v5.2 changes, 14 actions moved with max drift 0.58 (from thesis_breadth). The 30-min cron prevents drift from accumulating.

## Model Architecture (v5.2)

```
Final = sigmoid8(base_score x combined_mult x time_decay)

base_score = 1 + 9 * (weighted_sum_of_7_factors)  [Z-score normalized]
combined_mult = product of 17 multipliers, capped [0.4, 1.35]
time_decay = 0.97^max(0, days_old - 14)

17 Multipliers:
  1. priority_mult (P0=1.15, P1=1.07, P3=0.90)
  2. type_mult (portfolio=1.15, pipeline=1.12, research=0.82-0.92)
  3. source_mult (Cindy=1.08, ContentAgent=1.02)
  4. network_mult (Core=+12%, High=+8%, semantic fallback)
  5. depth_mult (grade 4=1.15, grade 1=0.93)
  6. freshness_mult (exponential decay of recency bonus)
  7. interaction_mult (recent interactions +up to 8%)
  8. preference_mult (learned from accept/dismiss patterns)
  9. acceptance_mult (action_type accept ratio)
  10. obligation_mult (overdue obligations boost)
  11. cindy_mult (communications intelligence)
  12. thesis_momentum_mult (thesis health/momentum)
  13. thesis_breadth_mult (NEW: multi-thesis = +3-8%)
  14. portfolio_health_mult (ownership, health, follow-on)
  15. financial_urgency_mult (financial signals)
  16. key_question_mult (keyword + trigram + embedding cosine)
  17. verb_pattern_mult (action verb dismiss patterns)
```

## Infrastructure Added

| Component | Type | Purpose |
|-----------|------|---------|
| `portfolio_key_questions` | Table | Per-question embeddings for semantic matching |
| `embedding_input_portfolio_key_questions()` | Function | Input text generator for embedding pipeline |
| `embed_pkq_on_insert` | Trigger | Auto-embed new questions |
| `embed_pkq_on_update` | Trigger | Re-embed on question text change |
| `thesis_breadth_multiplier()` | Function | Count pipe-separated thesis connections |
| `refresh_active_scores()` | Function | Batch score refresh for active actions |
| `score-refresh` | Cron (*/30) | Periodic score refresh |
| `preference-weight-refresh` | Cron (*/60) | Preference learning from behavior |

## Next Loop Priorities

1. **Embedding backfill complete** (375/386 = 97.2%). KQ match rate confirmed at 40.4%. 11 remaining items will embed on next cron cycle.
2. **explain_score() updated** to v5.2 with thesis_breadth_mult in 17-multiplier breakdown.
3. **Explore accepted-action embedding clustering** -- do the 10 accepted actions cluster in embedding space? If so, train a "similarity to accepted centroid" signal.
4. **Research actions scoring low despite acceptance** -- IDs 113 (4.00) and 14 (3.65) were accepted but score low because research type penalty dominates. Consider: should research actions connected to 4+ theses bypass the type penalty?
5. **Score trend dashboard** -- track avg scores per status over time to detect model degradation.
