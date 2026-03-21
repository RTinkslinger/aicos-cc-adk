# M9 Scoring Quality Audit

**Date:** 2026-03-20
**Scope:** `actions_queue` table — score distribution, correlations, anomalies
**Dataset:** 115 total rows (90 Proposed, 23 Accepted, 2 Dismissed)

---

## Overall Scoring Quality: 4/10

The scoring model produces differentiated output but suffers from **severe top-compression**, **action-type banding**, and a **broken IRGI correlation** that collectively reduce its utility as a triage signal.

---

## 1. Score Distribution

### Summary Statistics (Proposed only, n=90)

| Metric | Value |
|--------|-------|
| Mean | 8.15 |
| Median | 8.30 |
| Std Dev | 0.86 |
| P25 | 7.78 |
| P75 | 8.86 |
| P90 | 9.09 |
| Min | 5.12 |
| Max | 9.43 |

### Distribution by Bucket

| Score Range | Count | % of Total |
|-------------|-------|------------|
| 9.0 - 9.5 | 23 | 25.6% |
| 8.0 - 8.9 | 48 | 53.3% |
| 7.0 - 7.9 | 10 | 11.1% |
| 5.0 - 6.9 | 9 | 10.0% |
| Below 5.0 | 0 | 0.0% |
| Above 9.5 | 0 | 0.0% |

### Compression Analysis

| Zone | Count | % |
|------|-------|---|
| Ceiling (>= 9.5) | 0 | 0% |
| Floor (<= 1.5) | 0 | 0% |
| Middle (4-7) | 9 | 10% |
| **Upper band (7-9.5)** | **81** | **90%** |

**Diagnosis: Severe top-compression.** 90% of all Proposed actions score between 7.0 and 9.5. The effective scoring range is only 2.5 points wide (7.0-9.5), not the theoretical 1-10 scale. The bottom half of the scale (1-5) is essentially unused. This means the model cannot meaningfully distinguish priority — a score of 8.3 vs 8.1 is noise, not signal.

---

## 2. Action Type Breakdown

| Action Type | Count | Avg Score | Min | Max | Range |
|-------------|-------|-----------|-----|-----|-------|
| Portfolio Check-in | 36 | 8.85 | 8.25 | 9.43 | 1.18 |
| Meeting/Outreach | 33 | 8.09 | 7.64 | 8.46 | 0.82 |
| Pipeline Action | 12 | 7.50 | 6.99 | 8.11 | 1.12 |
| Research | 6 | 6.65 | 5.34 | 8.04 | 2.70 |
| Content Follow-up | 1 | 6.38 | 6.38 | 6.38 | 0.00 |
| Thesis Update | 2 | 5.50 | 5.12 | 5.88 | 0.76 |

### Type Tier Distribution (Proposed)

| Action Type | Score >= 8.5 | 7.5 - 8.5 | Below 7.5 |
|-------------|-------------|-----------|-----------|
| Portfolio Check-in | **26** | 10 | 0 |
| Meeting/Outreach | 0 | **33** | 0 |
| Pipeline Action | 0 | 6 | 6 |
| Research | 0 | 1 | 5 |
| Thesis Update | 0 | 0 | 2 |
| Content Follow-up | 0 | 0 | 1 |

**Diagnosis: Perfect action-type banding.** The scoring model has collapsed into a de facto action-type ranking, not a priority ranking:

- **Portfolio Check-in owns the entire top tier.** 100% of scores >= 8.5 are Portfolio Check-ins. Zero exceptions.
- **Meeting/Outreach occupies a narrow, non-overlapping band** (7.64-8.46), sitting perfectly below Portfolio.
- **Research and Thesis are permanently deprioritized** — they can never out-score even the weakest Portfolio Check-in.

This means the model is not evaluating individual action merit. It is applying a fixed type multiplier. A trivial portfolio flag ("Flag trademark conflict risk if Orange Slice exist...") scores 9.0, while a potentially high-impact thesis update scores 5.1. The scoring function has effectively become `action_type_rank * constant + small_noise`.

---

## 3. IRGI Independence Check

| Metric | Value |
|--------|-------|
| Correlation (user_priority vs IRGI) | **-0.489** |
| IRGI Mean | 0.58 |
| IRGI Std Dev | 0.17 |
| IRGI Range | 0.40 - 0.89 |

**Diagnosis: Moderate negative correlation is anomalous.** IRGI relevance and user priority should be either independent (near 0) or positively correlated (higher IRGI = higher priority). A -0.489 correlation means **the more IRGI-relevant an action is, the lower its priority score**. This is backwards.

Likely cause: Portfolio Check-ins (high priority score, high count) are operationally urgent but low on IRGI relevance (flagging risks, requesting data). Meanwhile, Research and Thesis actions (low priority score) are high IRGI relevance by nature. The scoring model privileges operational urgency over strategic relevance, which inverts the IRGI signal.

---

## 4. Portfolio Dominance Check (Top 15)

| Rank | Score | Type | Action (truncated) |
|------|-------|------|--------------------|
| 1 | 9.43 | Portfolio Check-in | Request detailed unit economics from Akasa Air... |
| 2 | 9.39 | Portfolio Check-in | Share Monday.com SDR-to-agent operational data... |
| 3 | 9.32 | Portfolio Check-in | Request detailed customer case study from Dallas... |
| 4 | 9.22 | Portfolio Check-in | Flag platform dependency risk. Highperformr... |
| 5 | 9.16 | Portfolio Check-in | Flag regulatory risk on AI features for Unifize |
| 6 | 9.16 | Portfolio Check-in | Flag operational capacity risk. With 36-46... |
| 7 | 9.15 | Portfolio Check-in | Flag closed-source components (Windows/macOS... |
| 8 | 9.11 | Portfolio Check-in | Flag execution risk on 'mile-wide, inch-deep'... |
| 9 | 9.10 | Portfolio Check-in | Flag pricing volatility risk on CodeAnt tiers |
| 10 | 9.09 | Portfolio Check-in | Request detailed breakdown of customer cohort... |
| 11 | 9.04 | Portfolio Check-in | Investigate the 46% MoM drop in D2C web traffic... |
| 12 | 9.04 | Portfolio Check-in | Request detailed case study from life sciences... |
| 13 | 9.03 | Portfolio Check-in | Request working capital health check. With... |
| 14 | 9.03 | Portfolio Check-in | Flag privacy/spam complaint risk for PowerUp... |
| 15 | 9.03 | Portfolio Check-in | Flag execution risk on Grow financing arm... |

**Diagnosis: 15/15 top actions are Portfolio Check-ins.** Complete monoculture. No Meeting/Outreach, Research, Pipeline, or Thesis action can break into the top 15 regardless of its actual importance. This confirms the banding problem from Section 2 — the model never lets non-portfolio actions compete for attention.

---

## 5. Status Comparison Anomaly

| Status | Count | Avg Score | Std Dev |
|--------|-------|-----------|---------|
| Dismissed | 2 | 8.42 | 0.11 |
| Proposed | 90 | 8.15 | 0.86 |
| Accepted | 23 | 6.91 | 1.82 |

**Diagnosis: Accepted items score LOWER than Proposed.** This is the most alarming finding. The user has been accepting actions that the model scored lower (avg 6.91) and leaving higher-scored actions (avg 8.15) in Proposed. Two possible explanations:

1. **The user is rationally ignoring the score** because the scoring does not match their actual priorities.
2. **The accepted items were early/different-era actions** scored under different criteria.

Either way, the scoring model is not predicting user acceptance behavior. A scoring model that the user systematically overrides is worse than no model — it creates cognitive overhead without value.

The 2 Dismissed items scored 8.42 avg — the user also dismissed high-scoring items, reinforcing that the score is not driving decisions.

---

## Summary of Anomalies

| # | Anomaly | Severity | Impact |
|---|---------|----------|--------|
| 1 | 90% of scores compressed into 7.0-9.5 band | **Critical** | Cannot distinguish priority within the majority of actions |
| 2 | Perfect action-type banding (no cross-type competition) | **Critical** | Model is a type ranker, not a priority scorer |
| 3 | Negative IRGI correlation (-0.489) | **High** | Strategic relevance inversely weighted |
| 4 | 15/15 top scores are Portfolio Check-ins | **High** | Non-portfolio actions permanently buried |
| 5 | Accepted items score lower than Proposed | **Critical** | Model does not predict user behavior |
| 6 | Zero scores below 5.0 or above 9.5 | **Medium** | Scale underutilized (effective range: 4.3 points) |

---

## Recommendations

### Immediate (fix scoring utility)

1. **Normalize within action type.** Score each action against its peers of the same type, then apply a cross-type weight. This breaks the banding where all Portfolio Check-ins auto-win.

2. **Widen the effective range.** Force-calibrate: the weakest proposed action should score near 2-3, not 5.1. Use percentile-based scoring or a sigmoid stretch centered at the median.

3. **Fix IRGI integration.** Either make IRGI a positive contributor to user_priority_score (multiply, don't ignore) or separate IRGI as a distinct ranking axis the user can filter by.

### Medium-term (validate against user behavior)

4. **Train on acceptance signal.** The 23 Accepted + 2 Dismissed actions are ground truth. Use them to recalibrate scoring weights. If the user consistently accepts lower-scored items, the model's feature weights are wrong.

5. **Log user triage decisions** (accept, dismiss, defer) with timestamps to build a feedback loop. Currently the model generates scores but has no mechanism to learn from outcomes.

### Structural

6. **Add sub-scores visibility.** Expose the component scores (time_sensitivity, conviction_change_potential, stakeholder_priority, etc.) so the user can see WHY something scored high, not just THAT it did. This also enables debugging when scores feel wrong.

7. **Introduce score decay.** Stale Proposed actions (90 sitting untriaged) should decay over time. A 2-week-old "Flag X risk" is less urgent than a fresh one. Currently all 90 are treated equally.
