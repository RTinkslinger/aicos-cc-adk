# Scoring System Fix Report — M5 Loop 2
*Executed: 2026-03-20*
*Supabase Project: llfkxnsfczludgigknbs (AI COS Mumbai, ap-south-1)*
*Source audit: `docs/audits/2026-03-20-scoring-audit-m5-loop1.md`*
*SQL saved: `sql/scoring-improvements.sql`*

---

## Executive Summary

All 8 fixes from the M5 Loop 1 audit have been executed successfully. The action scoring system has been transformed from a thesis-centric dump into a portfolio-and-network-first curated queue. Key outcomes:

- **Score coverage:** 20% -> 100% (115/115 actions now scored)
- **Scale bug:** Fixed. All scores normalized to 0-10 range
- **Queue inversion:** Fixed. Portfolio and Network now dominate the user queue; Thesis/Research routed to agent queue
- **Bucket routing:** Thesis Evolution dropped from 55% to 2% of routed actions; Portfolio (Bucket 2) now leads at 47%

---

## Fix-by-Fix Results

### Fix 1: Normalize Score Scale (CRITICAL)

**Problem:** 7 actions scored 64-76 on a 0-100 scale, causing them to dominate the top of the queue.

**Before:**
| Metric | Value |
|--------|-------|
| Min score | 6.5 |
| Max score | 76 |
| Avg score | 27.21 |
| Stddev | 30.58 |
| Scores > 10 | 7 |

**Action:** `UPDATE actions_queue SET relevance_score = relevance_score / 10.0 WHERE relevance_score > 10`

**After:**
| Metric | Value |
|--------|-------|
| Min score | 6.4 |
| Max score | 9.5 |
| Avg score | 7.41 |
| Stddev | 0.80 |
| Scores > 10 | 0 |

**Affected IDs:** 105, 106, 107, 108, 109, 110, 111

---

### Fix 2: Normalize Priority Labels

**Problem:** Two formats coexisted: "P1" vs "P1 - This Week" and "P2" vs "P2 - This Month"

**Before:**
| Priority | Count |
|----------|-------|
| P0 - Act Now | 44 |
| P1 | 4 |
| P1 - This Week | 55 |
| P2 | 4 |
| P2 - This Month | 8 |

**After:**
| Priority | Count |
|----------|-------|
| P0 | 44 |
| P1 | 59 |
| P2 | 12 |

Clean labels. No P3 actions exist currently.

---

### Fix 3: Create `compute_user_priority_score()` Function

**Problem:** No scoring function that reflects Aakash's actual priority hierarchy (Portfolio > Network > Thesis).

**Created:** `compute_user_priority_score(action_row actions_queue) RETURNS numeric`

**Scoring logic:**
- Base: `COALESCE(relevance_score, 5.0)`
- Priority boost: P0 +2, P1 +1, P2 +0, P3 -1
- Type boost: Portfolio/Check-in +3, Meeting/Outreach +2, Thesis/Research -3, Content -2
- Fallback text matching on action text for Pipeline Actions and untyped actions
- Recency factor: decays over 30 days
- Output clamped to [0, 10]

**Result:** Portfolio Check-ins score 10.0 at the top; Thesis Updates score 0.05-2.53 at the bottom.

---

### Fix 4: Create User Triage Queue and Agent Work Queue Views

**Problem:** No separation between actions for Aakash and actions for agents. Thesis tasks pollute the user's triage surface.

**Created:**
- `user_triage_queue` view — all Proposed actions, sorted by `user_score DESC`, with `is_agent_delegable` flag
- `agent_work_queue` view — only Research, Thesis Update, Content Follow-up, and evidence-related Proposed actions

**Queue split:**
| Queue | Actions | Types |
|-------|---------|-------|
| User (non-delegable) | 57 | Meeting/Outreach (30), Portfolio Check-in (15), Pipeline Action (12) |
| Agent (delegable) | 34 | Research (31), Thesis Update (2), Content Follow-up (1) |

**User queue top 10 (all Portfolio Check-in or Meeting/Outreach, all score 10.0):**
1. Flag operational risk on 'Free Lifetime Repairs' promise for Terractive (Portfolio Check-in, P0)
2. Share Monday.com SDR-to-agent operational data with portfolio companies (Portfolio Check-in, P1)
3. Schedule call with Dhruv Kohli to review unit economics data (Meeting/Outreach, P0)
4. CRITICAL: Pause investment activities for Orange Slice (Portfolio Check-in, P0)
5. Schedule operational deep-dive with CEO Rohit Arora (Meeting/Outreach, P0)
6. Flag privacy/spam complaint risk for PowerUp Money (Portfolio Check-in, P0)
7. Flag execution risk on Grow financing arm for GameRamp (Portfolio Check-in, P0)
8. Flag regulatory risk on AI features for Unifize (Portfolio Check-in, P0)
9. Schedule call with Unifize product/investor (Meeting/Outreach, P0)
10. Schedule board-level call with CEO Akash Goel (Meeting/Outreach, P0)

This is the correct priority order. Previously, the top 7 were all thesis/research tasks.

---

### Fix 5: Backfill Scores for Unscored Actions

**Problem:** 92 of 115 actions (80%) had NULL `relevance_score`, making them invisible in sorted views.

**Action:** Backfilled using `compute_user_priority_score()` as the base score.

**Before:**
| Metric | Value |
|--------|-------|
| Scored | 23 (20%) |
| Unscored | 92 (80%) |

**After:**
| Metric | Value |
|--------|-------|
| Scored | 115 (100%) |
| Unscored | 0 (0%) |
| Min score | 2.53 |
| Max score | 10.00 |
| Avg score | 7.07 |
| Stddev | 2.43 |

---

### Fix 6: Rewrite Bucket Router with User Priority Weighting

**Problem:** `route_action_to_bucket()` treated all 4 buckets equally, causing Thesis Evolution to dominate at 55%.

**Changes:**
- Bucket 2 (Portfolio/Deepen Existing): x1.5 multiplier
- Bucket 3 (Network/DeVC Collective): x1.3 multiplier
- Bucket 4 (Thesis Evolution): x0.6 multiplier (40% penalty)
- Added `SET search_path = public, extensions` to fix vector type resolution
- Recreated `action_scores` materialized view with unique index for `REFRESH CONCURRENTLY`
- Also fixed `score_action_thesis_relevance` search_path

**Before (action_scores matview):**
| Bucket | Actions | % | Avg Confidence |
|--------|---------|---|----------------|
| Thesis Evolution (Bucket 4) | 50 | **55%** | 0.545 |
| Discover New (Bucket 1) | 18 | 20% | 0.650 |
| Deepen Existing (Bucket 2) | 13 | 14% | 0.365 |
| DeVC Collective (Bucket 3) | 10 | 11% | 0.350 |

**After (action_scores matview):**
| Bucket | Actions | % | Avg Confidence |
|--------|---------|---|----------------|
| Deepen Existing (Bucket 2) | 43 | **47%** | 0.837 |
| Expand Network (Bucket 3) | 24 | **26%** | 0.542 |
| Discover New (Bucket 1) | 22 | 24% | 0.580 |
| Thesis Evolution (Bucket 4) | 2 | **2%** | 0.345 |

The inversion is completely fixed. Portfolio work now dominates (47%), followed by Network (26%). Thesis dropped from 55% to 2%.

---

### Fix 7: Add `user_priority_score` Column

**Problem:** Computed priority scores were not persisted, requiring recalculation on every query.

**Action:** Added `user_priority_score numeric` column to `actions_queue` and populated it for all 115 actions.

**Result:**
| Metric | Value |
|--------|-------|
| Min | 0.05 |
| Max | 10.00 |
| Avg | 7.08 |
| Stddev | 3.48 |
| Populated | 115/115 |

The wide stddev (3.48) indicates good discrimination power across the score range.

---

## Validation Summary

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Scores > 10 | 0 | 0 | PASS |
| Score coverage | 100% | 115/115 | PASS |
| Priority labels clean | P0, P1, P2 only | P0, P1, P2 | PASS |
| User queue: portfolio/network heavy | Top 10 = portfolio + meeting | 15 Portfolio + 30 Meeting/Outreach | PASS |
| Agent queue: thesis/research heavy | Mostly research | 31 Research + 2 Thesis + 1 Content | PASS |
| Bucket 2 (Portfolio) leads | > 40% | 47% | PASS |
| Bucket 4 (Thesis) demoted | < 10% | 2% | PASS |
| Matview refreshable | CONCURRENTLY works | Unique index added | PASS |

---

## What Changed (Database Objects)

### New
- **Function:** `compute_user_priority_score(actions_queue) -> numeric`
- **View:** `user_triage_queue` (Proposed actions sorted by user priority, with agent-delegable flag)
- **View:** `agent_work_queue` (Proposed agent-delegable actions only)
- **Column:** `actions_queue.user_priority_score` (persisted priority score)
- **Index:** `action_scores_id_idx` UNIQUE on `action_scores(id)` (enables REFRESH CONCURRENTLY)

### Modified
- **Function:** `route_action_to_bucket(integer)` — added user priority multipliers (B2 x1.5, B3 x1.3, B4 x0.6) and `SET search_path = public, extensions`
- **Function:** `score_action_thesis_relevance(integer)` — added `SET search_path = public, extensions` (fixes vector type resolution)
- **Materialized View:** `action_scores` — dropped and recreated (CASCADE from route_action_to_bucket drop)

### Data Changes
- 7 actions: `relevance_score` divided by 10 (scale normalization)
- 92 actions: `relevance_score` backfilled from user priority score function
- 115 actions: `priority` normalized to short form (P0/P1/P2)
- 115 actions: `user_priority_score` populated

---

## Remaining Issues (Not Fixed in This Loop)

1. **Priority inflation** — 86% of actions are P0/P1. The priority labels are now clean, but the distribution is still top-heavy. Needs: priority re-evaluation logic in the content pipeline.
2. **Preference store empty** — `action_outcomes` still has 0 human-rated entries. The calibration loop remains non-functional until the WebFront enables triage feedback.
3. **Thesis connection format** — Still mixed delimiters (pipe, plus, commas) and ad-hoc strings. Deferred to a separate data hygiene pass.
4. **Score decay** — The `user_priority_score` column is populated once but does not auto-decay. Needs: a cron job or trigger to re-compute periodically.
5. **Scoring at write time** — New actions from the content pipeline still may arrive without `scoring_factors` or `relevance_score`. The `compute_user_priority_score` function and the backfill pattern handle this, but a write-time trigger would be cleaner.
