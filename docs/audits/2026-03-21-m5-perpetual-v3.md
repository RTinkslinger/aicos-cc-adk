# M5 Scoring Machine -- Perpetual Loop v3 Audit

**Date:** 2026-03-21
**Model Version:** v5.0-L86 (16 multipliers)
**Trigger:** Critical portfolio context routing bug fix

---

## Critical Fix: Portfolio Context Routing

### Problem
`company_notion_id` in `actions_queue` points to `companies.notion_page_id` (100% match rate).
All Strategy 2 fallbacks in 6 functions were doing direct lookups against `portfolio.notion_page_id` (0% match rate).
The tables use **different IDs** -- companies and portfolio are separate entities bridged by `companies.portfolio_notion_ids` (text[] array).

### Correct Route
```
action.company_notion_id -> companies.notion_page_id -> companies.portfolio_notion_ids[] -> portfolio.notion_page_id
```

### Functions Fixed (6 total)

| Function | Fix Applied |
|----------|-------------|
| `portfolio_health_multiplier()` | Strategy 2 now JOINs through companies bridge |
| `financial_urgency_multiplier()` | Strategy 2 now JOINs through companies bridge |
| `key_question_relevance()` | Strategy 2 now JOINs through companies bridge |
| `explain_score()` | Strategy 2 + portfolio_context JSONB block fixed |
| `agent_scoring_context()` | Strategy 2 + portfolio_context JSONB block fixed |
| `narrative_score_explanation()` | Strategy 2 + portfolio_context JSONB block fixed |

### Additional Fix: Stale Integer Overloads
Three functions (`explain_score`, `agent_scoring_context`, `narrative_score_explanation`) had duplicate integer-type variants that weren't being updated. The `explain_score(integer)` overload was being resolved by PostgreSQL for literal calls like `explain_score(58)`, bypassing the fixed `bigint` version. Dropped all 3 integer variants, keeping only the fixed `bigint` versions.

---

## Action #46 Fix

**Problem:** Action "Request detailed unit economics from Akasa Air and Motorq customers" was mapped to CodeAnt (`8a90536a-463f-490f-bee5-d29b2a315db0`). Akasa Air and Motorq are not CodeAnt -- wrong mapping.
**Fix:** Set `company_notion_id = NULL` for action #46.

---

## Impact Measurement

### Portfolio Context Coverage

| Metric | Before Fix | After Fix |
|--------|-----------|-----------|
| Strategy 2 (direct portfolio lookup) | 0/49 (0%) | N/A (removed) |
| Strategy 2 (companies bridge) | N/A | 14/34 via bridge |
| Strategy 1 (text match) | 11/49 (22.4%) | 11/34 (32.4%) |
| **Total portfolio context** | **11/49 (22.4%)** | **14/34 (41.2%)** |
| Newly connected (bridge-only) | 0 | 3 actions |

### Newly Connected Actions (bridge found what text match missed)

| Action ID | Action | Company (companies table) | Portfolio Company |
|-----------|--------|---------------------------|-------------------|
| #45 | "Schedule board-level call with CEO Akash Goel..." | Atica | Atica (1.52%, $211K, spikey) |
| #58 | "Schedule urgent capital structure call with CEO Vinay Jaisingh..." | Legend of Toys | Legend of Toys (4.67%, $100K, P0 ops) |
| #111 | "Map Indian coding AI infrastructure landscape..." | CodeAnt | CodeAnt (portfolio) |

### Scoring Health (post-fix)

| Metric | Value |
|--------|-------|
| Health Score | 10/10 |
| Regression Tests | 22/22 PASS |
| Total Proposed | 34 |
| Avg Score | 5.19 |
| Stddev | 2.50 |
| Range | 1.00 - 10.00 |
| Distinct Scores | 34 (100% unique) |
| Compression (bucket 9-10) | 5.9% |
| Portfolio Coverage | 41.2% (14/34) |
| Cindy Coverage | 35.3% (12/34) |
| Thesis Momentum Coverage | 50.0% (17/34) |
| Interaction Coverage | 70.6% |
| Verb Pattern Coverage | 58.8% (20/34) |

### Score Distribution (post-fix)

- Portfolio avg: 6.01 (up from ~5.5, correctly elevated)
- Pipeline avg: 6.41
- Network avg: 4.53
- Thesis avg: 3.39
- Hierarchy: portfolio >= pipeline >= thesis (CORRECT)

---

## Model State

- **Version:** v5.0-L86
- **Multipliers:** 16 (priority, type, source, network, depth, freshness, interaction, preference, acceptance, obligation, cindy_intelligence, thesis_momentum, portfolio_health, financial_urgency, key_question_relevance, verb_pattern)
- **Combined mult cap:** [0.5, 1.8]
- **Regression:** 22/22 passing
- **Health:** 10/10
- **Preference learning:** Still guarded (95/100 decisions, 10.5% accept rate -- both thresholds unmet)

---

## What Changed in Score Rankings

The bridge fix primarily affects the **explanation and context quality** rather than raw scores, because:
1. `portfolio_health_multiplier` already found most portfolio companies via Strategy 1 (text match)
2. The 3 newly connected actions get ~3-19% portfolio health boost
3. The main win is that `agent_scoring_context()`, `explain_score()`, and `narrative_score_explanation()` now return **full portfolio context** (ownership, cheque, health, fumes, key_questions, follow-on decisions) for 14 actions instead of just 11

This means agents (Megamind, ENIAC) reasoning about these actions now have the complete picture: "Legend of Toys is YOUR HIGHEST TIER at 4.67% ownership, $100K invested, P0 ops priority" -- instead of having no portfolio context at all.
