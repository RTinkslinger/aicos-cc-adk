# Actions Intelligence Quality Fix Report (M9 Audit Response)

**Date:** 2026-03-20
**Audit Reference:** `docs/audits/2026-03-20-intelligence-quality-actions-m9.md`
**Database:** Supabase `llfkxnsfczludgigknbs`
**SQL Archive:** `sql/actions-intelligence-fixes.sql`

---

## Summary

Applied 5 fixes to address systemic intelligence quality issues identified by the M9 audit (scored 5.5/10). These fixes target action_type misclassification, duplicate cleanup, scoring_factors population, score recomputation, and materialized view refresh.

---

## Fixes Applied

### Fix 1: Reclassified 27 Mistyped Research Actions

**Problem:** 27 actions typed as "Research" contained user-action verbs (Schedule, Request, Flag, Commission, Investigate, Verify, Resolve, Portfolio check-in). The Research type_boost of -1.5 suppressed P0 urgent diligence items to score ~4.3, ranking them far below routine P1 portfolio check-ins at ~9.6.

**Action taken:**
- 3 actions reclassified Research -> Meeting/Outreach (ids: 34, 56, 66)
- 24 actions reclassified Research -> Portfolio Check-in (ids: 4, 12, 13, 16, 18, 24, 25, 27, 31, 35, 36, 37, 38, 46, 47, 60, 62, 64, 67, 71, 72, 81, 99, 100)

**Exclusion:** id:110 "Research which SaaS categories survive..." was deliberately excluded. It matched `%resolve%` but the word "resolve" in context means "understand a contradiction," not "resolve an issue with a portfolio company."

**Impact:** Research dropped from 46 to 19 actions. Portfolio Check-in grew from 19 to 43. Meeting/Outreach grew from 32 to 35. P0 user-action items previously scored ~4.3 now score 6.8-7.3.

### Fix 2: Dismissed 1 Confirmed Duplicate

**Problem:** Audit flagged 3 HIGH-severity duplicate pairs: (2, 68), (67, 71), (36, 62).

**Investigation findings:**
- **(2, 68): TRUE DUPLICATE** -- Both about Orange Slice trademark risk. id:2 is P0 with more detailed text; id:68 is P1 weaker version.
- **(67, 71): NOT DUPLICATE** -- Different companies. id:67 references Tracxn $1.89M / $1M April 2025 pre-seed. id:71 references Tracxn $7.28M / PitchBook $2.44M / 2025 Pre-Series A. Different funding amounts, different entities.
- **(36, 62): NOT DUPLICATE** -- Different companies. id:36 references agritech with ₹36.46L paid-up / $1.96M raise / dealer inventory. id:62 references manufacturing with ~$5M raised / ₹4.2Cr revenue / Hafele partner. Different industries and amounts.

**Action taken:** Dismissed id:68 with reason "Duplicate of action id:2." Kept ids 67, 71, 36, 62 as distinct actions for different companies.

### Fix 3: Populated scoring_factors for All 115 Actions

**Problem:** The multi-factor scoring model (`bucket_impact`, `time_sensitivity`, `action_novelty`, `effort_vs_impact`, `conviction_change_potential`) existed in the schema but was not implemented. 39 actions had empty `{}`. 76 had only `legacy_thesis_note` strings. 4 (ids 101-104) had a different integer-scale format.

**Action taken:**
- 39 actions: Created full multi-factor JSONB object
- 72 actions: Added multi-factor fields alongside existing `legacy_thesis_note`
- 4 actions (101-104): Added `conviction_change_potential` to normalize field naming

**Result:** 115/115 actions now have `bucket_impact`, `time_sensitivity`, `action_novelty`, `effort_vs_impact`, and `conviction_change_potential` in their scoring_factors.

### Fix 4: Recomputed All Scores

Ran `compute_user_priority_score()` across all 115 actions to reflect new action_type classifications.

### Fix 5: Refreshed Materialized View

Ran `REFRESH MATERIALIZED VIEW CONCURRENTLY action_scores` to propagate changes.

---

## Validation Results

| Check | Result | Status |
|-------|--------|--------|
| Remaining mistyped Research | 0 | PASS |
| Duplicate id:68 dismissed | Dismissed with reason | PASS |
| scoring_factors populated | 115/115 have bucket_impact | PASS |
| conviction_change_potential | 115/115 | PASS |
| Scores recomputed | All 115 updated | PASS |
| Materialized view refreshed | Success | PASS |

### Score Distribution (Before vs After, excluding Dismissed)

| action_type | Before Count | Before Avg | After Count | After Avg |
|-------------|-------------|------------|-------------|-----------|
| Research | 46 | 4.08 | 19 | 4.73 |
| Meeting/Outreach | 32 | 9.58 | 35 | 9.34 |
| Portfolio Check-in | 19 | 9.71 | 42 | 7.90 |
| Pipeline Action | 13 | 9.32 | 12 | 9.30 |
| Thesis Update | 4 | 3.38 | 4 | 3.38 |
| Content Follow-up | 1 | 7.68 | 1 | 7.68 |

**Key improvements:**
- Portfolio Check-in avg dropped from 9.71 to 7.90 because newly reclassified items have lower relevance_score (they were originally scored as Research). This creates better score differentiation within the type.
- Meeting/Outreach avg slightly dropped (9.58 -> 9.34) due to 3 newly reclassified items with lower base scores.
- Research count dropped from 46 to 19, all genuine research items. Average rose from 4.08 to 4.73.
- Previously-suppressed P0 user-action items (ids 4, 13, 16, 24, etc.) jumped from ~4.3 to ~7.3.

### Previously-Mistyped P0 Actions (Score Improvement)

| ID | Action | Old Type | New Type | Old Score (~) | New Score |
|----|--------|----------|----------|---------------|-----------|
| 4 | Flag platform dependency risk (Highperformr) | Research | Portfolio Check-in | ~4.3 | 7.29 |
| 13 | Flag execution risk of dual-market expansion | Research | Portfolio Check-in | ~4.3 | 7.29 |
| 34 | Schedule urgent team scaling call | Research | Meeting/Outreach | ~4.3 | 6.79 |
| 56 | Commission independent lab testing | Research | Meeting/Outreach | ~4.3 | 6.79 |
| 66 | Schedule product security review (CVE) | Research | Meeting/Outreach | ~4.3 | 6.79 |

---

## Remaining Issues (Not Addressed)

These were identified by the M9 audit but are outside the scope of this fix batch:

1. **Scoring function ignores IRGI** -- `compute_user_priority_score` still uses base_score + priority_boost + type_boost + recency. The `irgi_relevance_score` and populated `scoring_factors` are not yet consumed by the function. Requires function rewrite.

2. **Thesis over-tagging** -- 12 actions (ids 88-102) still have spurious "Healthcare AI Agents as Infrastructure" connections. This requires changes to the content agent's thesis-tagging logic.

3. **Cybersecurity over-tagging** -- 6 non-security actions still have "Cybersecurity / Pen Testing" thesis connections.

4. **Agent-delegable misses** -- ids 87, 91, 105 are research assigned to "Aakash" but could be agent-delegated. Requires view logic update.

5. **Embedding quality** -- Vector similarity for related items scored 30% accurate. Requires embedding model improvement or domain-aware fine-tuning.

---

## Estimated Impact on Intelligence Quality Score

| Dimension | M9 Score | Post-Fix Estimate | Change |
|-----------|----------|-------------------|--------|
| action_type classification | D (61%) | B+ (84%) | +23pp |
| scoring_factors population | F (1%) | A (100%) | +99pp |
| Duplicate detection | D | C+ (1 of 1 true dup fixed) | Improved |
| Scoring differentiation | F (0%) | D+ (marginal, still ignores IRGI) | Slight |
| Priority assignment | B- (80%) | B- (80%) | No change |
| Action text quality | A- (90%) | A- (90%) | No change |
| Thesis connection | F (20%) | F (20%) | Not addressed |
| Related companies | F (30%) | F (30%) | Not addressed |
| Agent classification | B+ (88%) | B+ (88%) | Not addressed |

**Estimated new overall score: ~6.5-7.0/10** (up from 5.5)

The two biggest remaining drags are thesis over-tagging and scoring function ignoring IRGI. Fixing either would push the score solidly above 7.
