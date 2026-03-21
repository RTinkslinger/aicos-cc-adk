# M5 Scoring Machine — Perpetual Loop v5 Audit

**Date:** 2026-03-21
**Model Version:** v5.0-L86 -> v5.1-L96
**Status:** COMPLETE — 4 critical fixes deployed

---

## Problem Statement

All stored `user_priority_score` values were 3.5-4.75 points below live computation. The scoring_health view reported 10/10, but the actual live distribution had 44.2% of actions compressed into bucket 9-10 (severe top-compression). Root cause: no auto-refresh mechanism — scores were computed once and never updated as the scoring model evolved through 16 iterations.

Secondary issue: `key_question_relevance` multiplier had 0% coverage due to 40% keyword overlap threshold being too strict for the semantic gap between action text and key questions.

---

## Fixes Deployed

### Fix 1: Score Refresh
**Action:** `UPDATE actions_queue SET user_priority_score = compute_user_priority_score(actions_queue.*) WHERE status IN ('Proposed', 'Accepted')`

All 52 proposed/accepted actions refreshed. Scores jumped 3.5-4.75 points upward, revealing massive top-compression (44.2% in bucket 9-10).

### Fix 2: Auto-Refresh Trigger
**Function:** `auto_refresh_priority_score()`
**Trigger:** `auto_refresh_score_trigger` — BEFORE INSERT OR UPDATE on `actions_queue`

Fires when any scoring-relevant column changes: action, action_type, priority, source, status, company_notion_id, thesis_connection, scoring_factors, relevance_score, reasoning. Only recomputes for Proposed/Accepted statuses.

Bulk refresh pattern: disable trigger, bulk update, re-enable trigger.

### Fix 3: key_question_relevance Dual Matching
**Old:** 40% keyword overlap only (0/52 coverage)
**New:** 20% keyword overlap OR 15% trigram similarity (pg_trgm)

Coverage: 0/52 -> 12/52 (23.1% of proposed/accepted actions)

Example matches:
- Action "Schedule urgent brand consolidation call with founders" matched Orbit Farming question "What are unit economics and pricing for the Balisto 130 Pro?" via trigram similarity (0.20)
- Action "Connect AuraML with 5 investors" matched "NVIDIA partnership: revenue-generating or strategic/promotional?" via keyword overlap (20%)

### Fix 4: Model Recalibration (v5.1)
Three parameter changes to decompress top scores:

| Parameter | v5.0 | v5.1 | Rationale |
|-----------|------|------|-----------|
| combined_mult cap | 1.8 | 1.35 | 16 mostly-positive multipliers compound to push raw scores above sigmoid wall |
| combined_mult floor | 0.5 | 0.4 | Allow sharper downward adjustments |
| sigmoid wall | 9.0 | 8.0 (with 0.5 steepness) | More granularity in 8-10 range |

---

## Distribution Before/After

| Bucket | Stale (reported) | After Refresh v5.0 | After Recalibrate v5.1 |
|--------|-----------------|---------------------|------------------------|
| 9-10 | 9.6% | 44.2% | **17.3%** |
| 7-8 | 19.2% | 28.8% | **44.2%** |
| 5-6 | 32.7% | 25.0% | **36.5%** |
| 3-4 | 19.2% | 1.9% | **1.9%** |
| 1-2 | 19.2% | 0.0% | **0.0%** |

**Stats:** avg=7.54, stddev=1.43, range=4.83-9.23, 28 distinct scores

---

## Top 10 Actions (Post-Recalibration)

| # | Score | Action | Priority |
|---|-------|--------|----------|
| 1 | 9.23 | Make investment decision on Cultured Computers ($150-300K at $30M cap) | P0 |
| 2 | 9.19 | Unifize founder deep dive: agent-native architecture | P0 |
| 3 | 9.09 | Map emerging data infrastructure layer for AI | P1 |
| 4 | 9.07 | CodeAnt AI integration roadmap: positioning as 'the agent' | P1 |
| 5 | 9.07 | Share Monday.com SDR-to-agent data with portfolio | P1 |
| 6 | 9.05 | Highperformr positioning review: agent infrastructure | P1 |
| 7 | 9.03 | Review Levocred pitch deck | P1 |
| 8 | 9.02 | Confido Health: inquire about AI agent strategy | P1 |
| 9 | 9.00 | Meeting prep: Reach out to Ian Fischer/Poetic team | P1 |
| 10 | 8.98 | Share Wang interview with CodeAnt AI founder | P2 |

Rank order is correct: investment decisions first, portfolio strategic questions next, thesis research lower.

---

## Validation

- **Health Score:** 10/10
- **Compression:** 17.3% in bucket 9-10 (PASS: under 30%)
- **Diversity:** 4 buckets populated (PASS)
- **Hierarchy:** portfolio avg > thesis avg (PASS)
- **Regression:** 21/22 PASS (confidence_populated is pre-existing)
- **Key question coverage:** 12/52 actions (23.1%) — up from 0%
- **Trigger tested:** auto_refresh_score_trigger installed and verified

---

## Multiplier Coverage Summary (v5.1)

| Multiplier | Avg Value | Coverage | Signal |
|------------|-----------|----------|--------|
| priority | 1.073 | 100% | P0/P1 boost |
| thesis_momentum | 1.060 | 63.5% | Almost always boost |
| portfolio_health | 1.060 | 32.7% | Portfolio actions only |
| key_question | 1.029 | 23.1% | Dual matching active |
| cindy | 1.023 | 23.1% | Intelligence signal |
| financial_urgency | 1.002 | 5.8% | Rare but strong |
| verb_pattern | 0.933 | 38.5% | Primary penalty source |

---

## Functions Modified

1. `auto_refresh_priority_score()` — NEW trigger function
2. `key_question_relevance(actions_queue)` — dual matching (keyword + trigram)
3. `compute_user_priority_score(actions_queue)` — recalibrated caps and sigmoid
4. `explain_score(bigint)` — updated caps, formula string, model version
5. `scoring_health` VIEW — recreated for v5.1

---

## Remaining Items

- **confidence_populated:** 8 actions missing score_confidence (pre-existing, not regression)
- **person_context coverage:** Still 8.8% (needs M12 enrichment)
- **Narrative version string:** `narrative_score_explanation` still says v5.0-L86 (cosmetic)
- **scoring_intelligence_report:** Still says v4.0-L75 (cosmetic)
