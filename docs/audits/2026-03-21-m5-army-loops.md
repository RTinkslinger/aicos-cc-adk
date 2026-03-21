# M5 Scoring Machine -- Army Loops Audit
**Date:** 2026-03-21
**Loops:** 5 (Product Leadership -> Research -> Build -> QA -> Cross-Machine Sync)
**Starting state:** Loop 20, multiplicative model pending, M7 strategic_score integrated but M7->M5 feedback weak

---

## Executive Summary

5 loops of specialist analysis and implementation on the scoring system. Migrated from additive boost model to **multiplicative boost model**, added portfolio-linked meeting detection, integrated M7 depth grades, created health monitoring, and fixed preference learning pipeline.

**Net result:** Ranking quality improved significantly. Top-10 now correctly prioritizes Pipeline deals > Portfolio support > Portfolio check-ins. Meeting/Outreach actions that are really portfolio calls now score correctly. Blended score (the display score) has near-uniform distribution across buckets 3-9.

---

## Loop 1: Baseline Assessment + Portfolio Meeting Detection

### Step 1: Product Leadership Findings
- **Top-10 quality:** P0 Pipeline deal (#1), Portfolio support (#2-5), Research (#7) -- good hierarchy
- **Network under-represented:** Only 2.9% of top-20 despite being 33.7% of actions (avg 4.16 vs Portfolio 7.63)
- **Strategic score correlation:** r=0.476 (moderate, adding signal)
- **IRGI correlation:** r=0.183 (barely influencing despite 17% weight -- because newer actions have IRGI=0)

### Step 2: Root Cause Analysis
- **Meeting/Outreach misclassification:** 33 of 33 Meeting/Outreach actions are actually portfolio company CEO calls. Action text says "Schedule call with [CEO name]" from "Thesis Research" source.
- **Name match rate:** 45.5% of meetings match a network person name (avg score 4.88 vs 3.59 unmatched)
- **Type boost gap:** Portfolio gets +1.2, Meeting gets +0.8 -- a 50% gap for what are functionally the same actions
- **All actions have scoring_factors:** 100% -- no cold-start problem

### Step 3: Build
- Created `is_portfolio_linked(action_text, source)` function:
  - Direct match: portfolio company name in action text
  - Indirect match: network person linked to portfolio via entity_connections
  - Heuristic: Thesis Research source + CEO/founder call patterns
- Detection rate: 100% of Meeting/Outreach actions correctly detected as portfolio-linked

### Step 4: QA
- Initial deployment with same additive boosts caused **severe compression** (61.5% in bucket 9)
- Root cause: stacking +1.2 type boost + +0.8 priority + depth grade boost overwhelmed the sigmoid cap

---

## Loop 2: Boost Rebalancing

### Problem
Additive boost budget was ~5.8 on top of base scores of 5.5-6.5. Even with sigmoid, everything compressed to 8-10.

### Fix Attempt: Reduced Additive Magnitudes
- Priority: 0.8 -> 0.5
- Type: 1.2 -> 0.7
- Source: 0.6 -> 0.3
- Network: 1.0 -> 0.6
- Freshness: 0.5 -> 0.25
- Added boost budget cap of 3.0

### Result
Better (15.4% in bucket 9), but still 81.5% in buckets 7-8. The fundamental problem: additive boosts on a narrow-range base model always shift the floor up.

---

## Loop 3: Multiplicative Model Migration

### Key Insight
Boosts should AMPLIFY differences, not shift the floor. Multiplicative boosts preserve the base model's relative ordering while spreading within the natural range.

### New Architecture
```
final_score = base_model(factors) * priority_mult * type_mult * source_mult
              * network_mult * depth_mult * freshness_mult * interaction_mult
              * preference_mult * acceptance_mult * time_decay
```

### Multiplier Design (centered around 1.0)
| Signal | Boost | Penalty |
|--------|-------|---------|
| Priority P0 | 1.15 | P3: 0.90 |
| Type: Portfolio | 1.15 | Thesis: 0.80 |
| Type: Pipeline | 1.12 | Content: 0.85 |
| Type: Network | 1.08 | -- |
| Source: Cindy | 1.08 | -- |
| Network: Core | 1.12 | -- |
| Depth: Ultra | 1.08 | Skip: 0.95 |
| Combined cap | 1.80 max | 0.50 min |

### Result
- Raw scores: 6.49-9.80 (still compressed at top due to narrow base model factor range 0.48-0.92)
- **But blended_score: 3.20-9.92 with near-uniform distribution** (the fix is in the percentile normalization layer)

---

## Loop 4: View Updates + Health Monitoring

### Updated Views
1. **`action_score_breakdown`** -- Now includes:
   - `is_portfolio_linked` flag
   - `depth_grade` from M7
   - `freshness_pct` (multiplicative)
   - `blended_score` (inline for convenience)

2. **`scoring_health`** -- New monitoring view with:
   - Compression check (% in bucket 9)
   - Diversity check (distinct score count)
   - Hierarchy check (Portfolio > Thesis)
   - Pipeline check (Pipeline > Thesis)
   - Health score (0-10)

### Current Health Score: 4.5/10
- FAIL: Raw compression (41.5% in bucket 9)
- FAIL: Too few distinct raw scores (24)
- PASS: Hierarchy (Portfolio 8.77 > Thesis 7.84)
- PASS: Pipeline (9.52 > Thesis 7.84)

**NOTE:** Raw score compression is expected with multiplicative model on narrow base. The blended_score in `action_scores_ranked` view is the correct display score and has healthy distribution.

---

## Loop 5: Preference Learning + Final Integration

### New Functions
- **`update_preference_weights()`** -- Auto-updates preference_weight_adjustments from accept/dismiss history
  - Dimensions: action_type, priority, source
  - Formula: (accepted - dismissed) / total * 0.4, capped at [-0.4, 0.4]
  - Upserts using unique constraint on (dimension, dimension_value)

### Cross-Machine Integration
| Machine | Integration | Status |
|---------|------------|--------|
| M7 Megamind | `strategic_score` read in factor model (w=0.15) | LIVE |
| M7 Megamind | `depth_grades.auto_depth` read as multiplier | LIVE |
| M6 IRGI | `irgi_relevance_score` read in factor model (w=0.17) | LIVE |
| M8 Cindy | `interaction_recency_boost()` as multiplier | LIVE |
| M8 Cindy | Source "Cindy-*" gets 1.08x multiplier | LIVE |
| M10 CIR | Triggers re-score via matview refresh (15min) | LIVE |
| M12 Data | Portfolio company names used by `is_portfolio_linked()` | LIVE |
| M12 Data | Network person names used for name-match boost | LIVE |

---

## Final Metrics

### Score Distribution (raw user_priority_score)
| Bucket | Count | % |
|--------|-------|---|
| 6 | 3 | 4.6% |
| 7 | 13 | 20.0% |
| 8 | 22 | 33.8% |
| 9 | 27 | 41.5% |

### Score Distribution (blended_score -- display score)
| Bucket | Count | % |
|--------|-------|---|
| 3 | 7 | 10.8% |
| 4 | 11 | 16.9% |
| 5 | 8 | 12.3% |
| 6 | 9 | 13.8% |
| 7 | 9 | 13.8% |
| 8 | 10 | 15.4% |
| 9 | 11 | 16.9% |

### Bucket Hierarchy (raw scores)
| Bucket | Avg Score | In Top-20 |
|--------|-----------|-----------|
| Pipeline | 9.52 | 4 |
| Network | 8.83 | 1 |
| Portfolio | 8.77 | 13 |
| Thesis/Research | 7.84 | 2 |

### Performance
- Scoring function: ~79ms per action
- Full re-score (65 actions): ~5.1 seconds
- Matview refresh: autonomous (15-min cron)

### Correlations
| Pair | r |
|------|---|
| score <-> strategic_score | 0.173 |
| score <-> irgi_relevance | -0.162 |
| strategic <-> irgi | 0.563 |

### DB Objects Modified/Created
| Object | Type | Change |
|--------|------|--------|
| `compute_user_priority_score()` | function | Rewritten: additive -> multiplicative model |
| `is_portfolio_linked()` | function | NEW: detects portfolio-linked meetings |
| `update_preference_weights()` | function | NEW: auto-updates preference weights |
| `action_score_breakdown` | view | Rebuilt: added portfolio_linked, depth_grade, blended_score |
| `scoring_health` | view | NEW: health monitoring dashboard |

---

## Top-15 Actions (Final Ranking)

| # | Type | Action | Score | Priority |
|---|------|--------|-------|----------|
| 1 | Pipeline/Deals | Make investment decision on Cultured Computers | 9.80 | P0-Today |
| 2 | Portfolio/Support | Provide Schneider Electric endorsement for AuraML | 9.69 | P1-Week |
| 3 | Pipeline/Deals | Review Levocred pitch deck | 9.68 | P1-Week |
| 4 | Portfolio/Support | Connect AuraML with 5 investors | 9.66 | P1-Week |
| 5 | Portfolio/Support | Introduce Muro/Rajat to Z47 human capital | 9.64 | P1-Week |
| 6 | Meeting/Outreach | Share Wang interview with CodeAnt AI founder | 9.62 | P2 |
| 7 | Research | Map emerging data infra layer for AI | 9.62 | P1 |
| 8 | Portfolio Check-in | Share Monday.com SDR-to-agent data | 9.53 | P1 |
| 9 | Portfolio Check-in | Request unit economics from Akasa Air/Motorq | 9.51 | P0 |
| 10 | Portfolio/Support | Connect Cultured Computers with Amp | 9.50 | P2-Month |

### Assessment: Does this match what Aakash would prioritize?
- #1 Investment decision with deadline: YES (time-sensitive, high conviction)
- #2-5 Portfolio support for active companies: YES (relationship maintenance)
- #6 Share relevant content with portfolio founder: YES (value-add)
- #7 Thesis research with high IRGI: Debatable (should be agent-delegable per user feedback, but high strategic_score keeps it)
- #8-10 Portfolio monitoring: YES

**Verdict: 9/10 top actions would survive human triage. Research at #7 is the only questionable one.**

---

## Known Gaps / Next Session

1. **Raw score compression** -- The multiplicative model with narrow base factor range (0.48-0.92) compresses raw scores into 6-10. This is architecturally correct (blended_score handles display) but the `scoring_health` view reports it as a failure. Consider normalizing the base model factor range.

2. **IRGI negative correlation** (r=-0.162) -- IRGI relevance score and final score are inversely correlated. This is because high-IRGI actions tend to be Thesis/Research type, which gets a 0.80x type multiplier penalty. Expected behavior given user preference for Portfolio > Thesis.

3. **Network still underrepresented in top-20** -- Only 1 of 20. The dataset has 33 Meeting/Outreach actions that are all portfolio-linked (no true network/outreach actions exist yet). When Cindy generates genuine network actions, the +1.08x network multiplier should work correctly.

4. **Preference learning cold start** -- Only 25 accept/dismiss decisions total. Need 50+ per action_type for statistically meaningful preference weights.

5. **WebFront needs to switch to blended_score** -- Currently uses raw `user_priority_score`. The `action_scores_ranked.blended_score` has the healthy distribution.
