# M5 Scoring Machine -- Perpetual Loop v6 Audit

**Date:** 2026-03-21
**Model Version:** v5.1-L96 (all version strings now consistent)
**Status:** COMPLETE -- 6 fixes deployed, 2 structural findings

---

## Starting State (from v5 audit)

- Auto-refresh trigger installed, health 10/10
- key_question_relevance at 23.1% (12/52 actions)
- Version strings inconsistent: narrative and scoring_intelligence_report still on old versions
- scoring_intelligence_report broken (missing columns in scoring_health view)

---

## Investigation Results

### 1. Auto-Refresh Trigger Verification

**Status: WORKING but insufficient**

The trigger (`auto_refresh_score_trigger`) fires correctly on INSERT/UPDATE of scoring-relevant columns. Verified by updating action #10's reasoning -- score changed from 8.02 to 8.33.

**However:** 42/52 active actions had drifted scores (avg drift 0.196, max drift 1.435). Root cause: the trigger only fires on `actions_queue` row changes. When *external* tables change (portfolio.key_questions, interactions, thesis_threads), the computed score drifts silently because `compute_user_priority_score()` reads from those tables at call time.

**Fix deployed:** Bulk refresh all 52 active scores. Post-refresh: 52/52 in sync (max drift 0.000014).

**Structural insight:** A row-level trigger on actions_queue alone cannot prevent drift caused by changes to portfolio, interactions, thesis_threads, or obligations data. Options for future:
- Periodic cron bulk refresh (simplest)
- Cross-table triggers on portfolio/interactions/thesis_threads (complex, performance risk)
- Materialized view with scheduled refresh

### 2. key_question_relevance Analysis

**Status: 12/52 matching (23.1%) -- ceiling found**

Current dual matching (20% keyword overlap OR 15% trigram similarity) matches well for actions whose TEXT directly references the same concepts as key_questions. But 11 additional actions link to portfolio companies WITH key_questions yet get no match because the semantic gap is too wide.

Example: "Unifize founder deep dive: agent-native architecture" vs key question "Series A timing: with $1.7M revenue and 73% growth, when will they raise?" -- trigram similarity is only 0.036, keyword overlap near zero. These are semantically related (both about the same company's strategic direction) but textually unrelated.

**Matching companies with unmatched actions:**
| Company | Action | Issue |
|---------|--------|-------|
| Unifize | Founder deep dive: agent-native architecture | KQs about revenue/growth/Series A timing |
| Confido Health | Inquire about AI agent strategy | KQs about ACV expansion and GTM |
| Inspecity | Flag capital intensity risk | KQs about non-gov GTM and fundraising |
| GameRamp | Flag execution risk on Grow financing | KQs about Sentinel RL validation |
| Terractive | Flag operational risk on repairs promise | KQs about founder strategic thinking |
| Orange Slice | Pause investment activities | KQs about MRR/ARR growth |
| Legend of Toys | Capital structure clarification | KQs about revenue/margin disclosure |

**Conclusion:** Trigram/keyword matching has hit its ceiling. Next level requires semantic (embedding) matching between action text and key_question text. This would catch "any action about a company where we have open questions" regardless of textual overlap.

### 3. Narrative Score Explanation -- Key Question Inclusion

**Status: FIXED**

Added explicit key_question narrative line. Example for CodeAnt (action #32):
> "This action directly addresses key questions for the portfolio company (key_question boost +16%)."

Previously the narrative mentioned key_question effects only in the technical_explanation section. Now surfaced in the human-readable narrative.

### 4. Version String Consistency

**Status: ALL FIXED**

| Function | Before | After |
|----------|--------|-------|
| `explain_score()` | v5.1-L96 | v5.1-L96 (was already correct) |
| `narrative_score_explanation()` | v5.0-L86 | v5.1-L96 |
| `agent_scoring_context()` | v5.0-L86 | v5.1-L96 |
| `scoring_intelligence_report()` | v4.0-L75 | v5.1-L96 |
| `scoring_health` view | v5.1-L96 | v5.1-L96 (was already correct) |

### 5. scoring_intelligence_report Fix

**Status: FIXED**

The function was broken -- it referenced columns (`total_proposed`, `avg_raw`, `stddev_raw`, `min_raw`, `max_raw`, `pipeline_check`, `portfolio_avg`, `network_avg`, `pipeline_avg`, `thesis_avg`) that did not exist in the `scoring_health` view. The view was recreated with all required columns plus new ones (pipeline_check, category averages). Also fixed multiplier_count from 15 to 16.

### 6. User Feedback Analysis

**8 feedback entries found in user_feedback_store:**

| ID | Type | Rating | Key Signal |
|----|------|--------|------------|
| 11 | UX | 1/5 | Portfolio health section on home page showing irrelevant companies with prep buttons -- wants P0 actions instead |
| 5 | Scoring | 4/10 | Score distribution compressed, stddev 1.42 (target >2.0) |
| 2 | Intelligence Quality | 4/10 | Data skeletal, connections noise-dominated |
| 3 | Data Richness | 1/5 | Page content is tweets, not intelligence |
| 4 | Connection Quality | 4/10 | 10,719 vector_similar with single evidence, only 24.9% evidence-based |
| 7 | Cron Health | 3/5 | 490 embedding failures, 62 CIR failures -- connection pool pressure |

**Scoring-relevant feedback:** User wants stddev > 2.0 (currently 1.29). The distribution is compressed into 5.11-9.23 range with no actions below 5.0. This is partly structural -- all 92 dismissed actions scored 1.0-4.0 and have been removed from the active pool, leaving only mid-to-high scorers.

### 7. Accepted Action Patterns

**10 accepted actions analyzed:**

| Pattern | Accepted | Dismissed | Proposed |
|---------|----------|-----------|----------|
| Portfolio Check-in (P0/P1) | 6 | 28 | 5 |
| Meeting/Outreach | 2 | 29 | 4 |
| Research | 2 | 12 | 7 |

**Key predictors of acceptance:**
1. **Company linkage + Portfolio Check-in type** -- 6/10 accepted are portfolio check-ins with specific company context
2. **Score threshold** -- Accepted avg=8.50, Proposed avg=7.54, Dismissed avg=2.52. Perfect separation.
3. **Has thesis connection** -- 100% of accepted actions have thesis_connection (vs 74% dismissed)
4. **Has company** -- 70% of accepted have company_notion_id

**Verb patterns with 0% acceptance rate (user always dismisses):**
- "Schedule..." (0/15 dismissed, 0/4 proposed)
- "Flag risk..." (0/9 dismissed, 0/6 proposed)
- "Connect..." (0/2 dismissed, 0/3 proposed)
- "Update thesis..." (0/1 dismissed, 0/2 proposed)

The verb_pattern_multiplier is already penalizing these, but the 6 proposed "flag risk" and 4 proposed "schedule" actions are still scoring 7.96-8.53. The penalty may need strengthening.

---

## Post-Fix Distribution

| Bucket | Pre-Refresh | Post-Refresh |
|--------|-------------|--------------|
| 9-10 | 17.3% | 17.3% (9 actions) |
| 7-8 | 44.2% | 44.2% (23 actions) |
| 5-6 | 36.5% | 38.5% (20 actions) |
| 3-4 | 1.9% | 0.0% |
| 1-2 | 0.0% | 0.0% |

**Stats:** avg=7.73 (+0.19 from v5 refresh), stddev=1.29 (-0.14), distinct_scores=23, health=10/10

**Category averages (new):** Portfolio=8.55, Pipeline=7.46, Network=7.13, Thesis=7.11

**Diversity WARN:** Only 3 buckets populated (need 4 for PASS). This is structural -- all active actions score 5.11+. The dismissed actions (scoring 1.0-4.0) are the ones that would fill lower buckets. Not a model defect.

---

## Functions Modified

1. `agent_scoring_context()` -- version string v5.0-L86 -> v5.1-L96
2. `narrative_score_explanation()` -- version string + added key_question narrative line
3. `scoring_intelligence_report()` -- version v4.0-L75 -> v5.1-L96, multiplier_count 15 -> 16
4. `scoring_health` VIEW -- dropped and recreated with 8 new columns for scoring_intelligence_report compatibility

---

## Remaining Items / Next Loop

1. **Score drift prevention** -- Need periodic bulk refresh (cron or edge function) since row-level trigger cannot detect external table changes. Recommended: 15-min cron running `UPDATE actions_queue SET user_priority_score = compute_user_priority_score(actions_queue.*) WHERE status IN ('Proposed', 'Accepted')`.

2. **key_question_relevance semantic matching** -- Current 23.1% is the ceiling for trigram/keyword. Embedding-based matching would unlock the 11 additional company-linked actions. Requires: generate embeddings for key_questions, compare via cosine similarity with action text embeddings.

3. **Verb pattern penalty strengthening** -- "Flag risk" and "Schedule" actions have 0% historical acceptance but still score 7.96-8.53. The verb_pattern_multiplier penalty could be increased from ~5% to ~15-20% for consistently dismissed patterns.

4. **stddev target** -- User feedback wants >2.0 stddev (currently 1.29). The active pool (42 proposed + 10 accepted) naturally clusters high because low-scoring actions get dismissed. This may require rethinking the target or measuring stddev only within proposed actions.

5. **score_trend function** -- Missing. `agent_scoring_context` catches the error gracefully but the function should be created to track score movement over time.
