# M5 Scoring Machine: Perpetual Loop v2 Audit
**Date:** 2026-03-21
**Starting State:** v5.0-L76, 16 multipliers, 22/22 regression, health 10/10, compression 24.5%
**Scope:** Verify M4 company_notion_id fix, agent_scoring_context portfolio data, narrative explanations, accepted action patterns, score stability

---

## Executive Summary

The scoring model (v5.0-L76) is structurally healthy: 22/22 regression tests pass, health 10/10, compression 24.5%. But a **critical data routing gap** undermines the richest scoring signals. All 34 `company_notion_id` values in proposed actions point to the **companies** table, not the **portfolio** table -- and every function that uses `company_notion_id` as a fallback to look up portfolio data (`agent_scoring_context`, `portfolio_health_multiplier`, `narrative_score_explanation`, `explain_score`) tries `portfolio.notion_page_id = company_notion_id`, which matches **zero rows**. 18 of those 34 actions also fail text-matching (the company name isn't in the action text), meaning they get **no portfolio context at all** -- no ownership, no health, no follow-on, no fumes date. The other 16 are saved by text-match Strategy 1, but only by accident.

Additionally, analysis of the 10 accepted actions reveals a clear preference pattern that the verb multiplier partially captures but misses the strongest signal: **Aakash accepts actions framed as company-first strategic questions** (e.g., "Unifize founder deep dive: agent-native architecture?", "CodeAnt AI integration roadmap: positioning as 'the agent'?"). These are classified as UNCLASSIFIED by the verb pattern system because they don't start with a verb -- they start with the company name.

---

## Finding 1: company_notion_id Routing Gap (CRITICAL)

### The Problem

| Metric | Value |
|--------|-------|
| Proposed actions with company_notion_id | 34 / 49 (69.4%) |
| company_notion_id matches companies table | **34 / 34 (100%)** |
| company_notion_id matches portfolio table | **0 / 34 (0%)** |
| Actions with text-match fallback to portfolio | 16 / 34 |
| Actions with NO portfolio context at all | **18 / 34 (36.7% of all proposed)** |

M4 Datum correctly mapped `company_notion_id` to the **companies** table (where the IDs live). But all scoring functions assume `company_notion_id` is a **portfolio** `notion_page_id`. The companies table has a `portfolio_notion_ids` array that links to portfolio -- but no scoring function follows this join path.

### Impact on Scoring Functions

| Function | Strategy 1 (text match) | Strategy 2 (company_notion_id) | Impact |
|----------|------------------------|-------------------------------|--------|
| `portfolio_health_multiplier()` | Works for 16 actions | Broken (0 matches) | 12 portfolio companies get **no health multiplier** via ID fallback |
| `agent_scoring_context()` | Works for 16 actions | Broken (0 matches) | Agent context returns `null` portfolio for 18 actions |
| `narrative_score_explanation()` | Works for 16 actions | Broken (0 matches) | Narrative misses portfolio context for 18 actions |
| `explain_score()` | Works for 16 actions | Broken (0 matches) | Technical explanation incomplete for 18 actions |
| `is_portfolio_linked()` | Text match only | Not used | Partially unaffected |

### Actions Losing Portfolio Context (sample)

| ID | Action | Company (via companies table) | Portfolio Match | Score |
|----|--------|------------------------------|-----------------|-------|
| 121 | Review Levocred pitch deck | Levocred | No portfolio_notion_ids | 9.81 |
| 46 | Request unit economics from Akasa Air/Motorq | CodeAnt (wrong mapping!) | Has portfolio link | 9.30 |
| 58 | Schedule urgent capital call with CEO Vinay Jaisingh | Legend of Toys | Has portfolio link | 8.67 |
| 45 | Schedule board-level call with CEO Akash Goel | Atica | Has portfolio link | 7.99 |
| 138 | Schedule meeting with Supermemory founder | Supermemory | No portfolio_notion_ids | 6.11 |

**Note:** Action #46 ("Request unit economics from Akasa Air and Motorq") has `company_notion_id` pointing to CodeAnt -- this is a **wrong mapping** from M4's fix. The action mentions Akasa Air and Motorq, not CodeAnt.

### Fix Required

All functions with Strategy 2 (`portfolio.notion_page_id = company_notion_id`) need an intermediate join:
```
company_notion_id -> companies.notion_page_id -> companies.portfolio_notion_ids -> portfolio.notion_page_id
```

This is a single-hop join: `companies.portfolio_notion_ids` is an array, and `portfolio.notion_page_id = ANY(companies.portfolio_notion_ids)`.

Of the 34 actions with company_notion_id, 28 companies have `portfolio_notion_ids` populated. The remaining 6 are pipeline companies (Levocred, Muro AI, PlatinumRX, Badnaam Chai, Supermemory, Plaza) that correctly have no portfolio entry.

---

## Finding 2: Accepted Action Pattern Analysis

### The 10 Accepted Actions

| Action | First Word | Verb Pattern | Type |
|--------|-----------|-------------|------|
| Unifize founder deep dive: agent-native architecture? | Unifize | UNCLASSIFIED | Portfolio Check-in |
| CodeAnt AI integration roadmap: positioning... | CodeAnt | UNCLASSIFIED | Portfolio Check-in |
| Highperformr positioning review: agent infra... | Highperformr | UNCLASSIFIED | Portfolio Check-in |
| Confido Health: inquire about AI agent strategy | Confido | UNCLASSIFIED | Portfolio Check-in |
| Meeting prep: Reach out to Ian Fischer... | Meeting | UNCLASSIFIED | Meeting/Outreach |
| Portfolio check-in: CodeAnt AI. Question:... | Portfolio | UNCLASSIFIED | Portfolio Check-in |
| Portfolio check-in: Smallest AI. Question:... | Portfolio | UNCLASSIFIED | Portfolio Check-in |
| Interview 5-10 enterprise engineers... | Interview | UNCLASSIFIED | Meeting/Outreach |
| Map Z47 and DeVC portfolio companies... | Map | MAP_RESEARCH | Research |
| Map agent infrastructure ecosystem... | Map | MAP_RESEARCH | Research |

### Pattern Discovery

**8 of 10 accepted actions (80%) are verb-pattern UNCLASSIFIED.** The UNCLASSIFIED bucket has a 21.1% accept rate (8 accepted out of 38 total decisions), making it the **highest-accepting category** -- but the verb multiplier applies no adjustment to it because it can't classify it.

The accepted actions share three characteristics:
1. **Company-first framing** (5/10): Action starts with the company name, not a verb ("Unifize founder deep dive", "CodeAnt AI integration roadmap")
2. **Strategic question embedded** (7/10): Contains a question or strategic inquiry ("agent-native architecture or doubling down?", "positioning as 'the agent' not 'another SaaS tool'?")
3. **Portfolio Check-in type** (7/10): The dominant accepted type

The verb pattern multiplier correctly penalizes FLAG (0%), CONNECT (0%), SCHEDULE (0%), REQUEST (0%) patterns. But it cannot reward the company-first-question pattern because those actions don't match any verb category.

### Accept Rates by Type

| Type | Proposed | Accepted | Dismissed | Accept Rate |
|------|----------|----------|-----------|-------------|
| Portfolio Check-in | 17 | 6 | 20 | **23.1%** |
| Research | 5 | 2 | 12 | 14.3% |
| Meeting/Outreach | 10 | 2 | 23 | 8.0% |
| Pipeline/Deals | 2 | 0 | 4 | 0% |
| Pipeline Action | 2 | 0 | 12 | 0% |
| Portfolio/Support | 4 | 0 | 1 | 0% |
| All others | 7 | 0 | 13 | 0% |

### Global Accept Rate

- **Total decisions:** 95 (10 accepted, 85 dismissed)
- **Accept rate:** 10.5%
- **Preference learning guards:** Need 100 decisions AND 20% accept rate. Currently at 95/100 decisions and 10.5%/20% accept rate. Both guards are protecting correctly -- the model should NOT learn from this skewed data yet.

---

## Finding 3: Score Stability Assessment

### Score Trends

| Trend | Count | Avg Change % | Avg Volatility |
|-------|-------|-------------|---------------|
| RISING | 42 | +1.12% | Low |
| STABLE | 5 | ~0% | Minimal |
| FALLING | 2 | -0.14% | Minimal |

Scores are **stabilizing** -- the large movements (rising) are from the v5.0-L76 verb pattern changes propagating through score history. The top 5 fallers have minimal movement (-0.15% to 0%). This is healthy: the verb pattern multiplier caused a one-time score adjustment that is now settling.

### Score Distribution (Current)

| Bucket | Count | % | Avg Score |
|--------|-------|---|-----------|
| 9 | 12 | 24.5% | 9.58 |
| 8 | 11 | 22.4% | 8.65 |
| 7 | 10 | 20.4% | 7.54 |
| 6 | 12 | 24.5% | 6.57 |
| 5 | 2 | 4.1% | 5.38 |
| 4 | 2 | 4.1% | 4.79 |

Distribution is healthy. No single bucket exceeds 25%. Spread across 4.73-9.85.

### Score History

- 193 snapshots across 144 distinct actions
- Last snapshot: ~1 hour ago
- First snapshot: ~2.5 hours ago
- Rolling window active and healthy

---

## Finding 4: narrative_score_explanation Quality

Tested on top-5 actions. Narratives are **rich and meaningful** where portfolio context exists via text match:

**Action 119 (AuraML - Schneider endorsement, score 9.8):**
> "AuraML is a significant position at 2.22% ownership ($100K invested). Linked to thesis: 'AI-Native Enterprise'. You have 1 overdue obligation(s) tied to this -- relationship risk. Recent interactions add strong intelligence signal (+16% Cindy boost)."

**Action 120 (AuraML - Connect with investors, score 9.8):**
> Includes concern: "You have historically dismissed actions phrased this way (22% penalty from user behavior learning)"

**Action 118 (Cultured Computers investment decision, score 9.8):**
> "Connected to your 'Agentic AI Infrastructure' thesis (conviction: Very High). Thesis has strong momentum right now, boosting priority."

Narratives are contextually accurate, include portfolio data where available, surface concerns, and reference thesis connections. The v5.0-L76 version tag is consistently applied.

**Gap:** For the 18 actions where portfolio context is missing (company_notion_id routing issue), narratives lack the ownership/health/fumes context that would make them richer.

---

## Finding 5: Regression Suite Status

22/22 tests pass. Key results:

| Test | Status | Detail |
|------|--------|--------|
| score_range_1_10 | PASS | 4.73 - 9.85 |
| score_diversity | PASS | 46 distinct scores |
| priority_hierarchy | PASS | P0=7.99, P2=7.19 |
| compression | PASS | 24.5% in bucket 9-10 |
| pipeline_gt_thesis | PASS | 8.51 vs 6.93 |
| interaction_coverage | PASS | 53.1% |
| verb_pattern_functional | PASS | 33 actions with signal |
| agent_scoring_context | PASS | 25 keys returned |
| context_enrichment | PASS | 49/49 enriched |

**Missing regression test:** No test validates that `agent_scoring_context` returns non-null portfolio context for actions with `company_notion_id`. The test only checks that 25 keys are returned, not that portfolio data is populated. This is how the routing bug went undetected.

---

## Multiplier Coverage Update

| # | Multiplier | Active | Coverage | Change from L76 |
|---|-----------|--------|----------|-----------------|
| 1 | Priority | 36 | 73.5% | -- |
| 2 | Type | 45 | 91.8% | -- |
| 3 | Source | 8 | 16.3% | -- |
| 4 | Network | ~15 | ~30% | -- |
| 5 | Depth | ~40 | ~82% | -- |
| 6 | Freshness | 49 | 100% | -- |
| 7 | Interaction | 26 | 53.1% | -- |
| 8 | Preference | 0 | 0% | Guarded (10.5% accept < 20% threshold) |
| 9 | Acceptance | ~30 | ~61% | -- |
| 10 | Obligation | 8 | 16.3% | -- |
| 11 | Cindy Intelligence | 13 | 26.5% | -- |
| 12 | Thesis Momentum | 17 | 34.7% | -- |
| 13 | Portfolio Health | 16 | 32.7% | **Should be ~28 with fix** |
| 14 | Financial Urgency | 2 | 4.1% | -- |
| 15 | Key Question | 0 | 0% | Needs M12 enrichment |
| 16 | Verb Pattern | 33 | 67.3% | -- |

---

## Recommended Actions (Priority Order)

### P0: Fix company_notion_id -> portfolio routing
All 4 functions (`agent_scoring_context`, `portfolio_health_multiplier`, `narrative_score_explanation`, `explain_score`) need Strategy 2 updated from:
```sql
-- BROKEN: company_notion_id is a companies.notion_page_id, not portfolio.notion_page_id
SELECT p.* INTO v_portfolio FROM portfolio p WHERE p.notion_page_id = a.company_notion_id;
```
to:
```sql
-- FIXED: route through companies table to portfolio
SELECT p.* INTO v_portfolio
FROM companies c
JOIN portfolio p ON p.notion_page_id = ANY(c.portfolio_notion_ids)
WHERE c.notion_page_id = a.company_notion_id
LIMIT 1;
```
**Impact:** 12 additional actions gain portfolio context (the 6 pipeline companies correctly have no portfolio). Portfolio health multiplier coverage rises from 32.7% to ~57%.

### P1: Add regression test for portfolio context population
```sql
-- Test: portfolio_context_coverage
-- Actions with company_notion_id that maps through companies -> portfolio
-- should return non-null portfolio context from agent_scoring_context()
```

### P2: Investigate wrong company_notion_id mappings
Action #46 ("Request unit economics from Akasa Air and Motorq") maps to CodeAnt. Action #76 and #111 also map to CodeAnt despite being about different companies. M4 Datum may have mapping bugs beyond the ID format fix.

### P3: Consider company-first verb pattern
The UNCLASSIFIED bucket (21.1% accept rate) contains the highest-accepting pattern: company-name-first strategic questions. A future verb pattern evolution could add a STRATEGIC_INQUIRY category for actions matching `^[A-Z][a-z]+ .*(:|question|deep dive|roadmap|positioning|review)`.

### P4: Preference learning approaching activation
95/100 decisions (5 more needed). Accept rate at 10.5% (needs 20%). The accept rate guard is correctly preventing premature learning. As Aakash accepts more company-first portfolio check-ins, the rate should naturally rise.

---

## Cross-Machine Impact

| Machine | Finding | Required Action |
|---------|---------|----------------|
| M4 Datum | Wrong company_notion_id on some actions | Audit company_notion_id assignment logic |
| M7 Megamind | agent_scoring_context missing portfolio data for 18 actions | Blocked on P0 fix |
| M8 Cindy | Cindy multiplier working (13 actions) | No change needed |
| M9 Intel QA | Missing regression test for portfolio context | Add test after P0 fix |
| M12 Data | key_questions still 0% coverage | M12 remains blocking dependency |

---

## Model State

**v5.0-L76** | 16 multipliers | 22/22 regression | Health 10/10 | Compression 24.5%

Score snapshots refreshed. 193 -> 242 history records (49 new proposed action snapshots captured).
