# Scoring Verification Report — M5 Loop 3
*Verified: 2026-03-20*
*Supabase Project: llfkxnsfczludgigknbs (AI COS Mumbai, ap-south-1)*
*Source fix report: `docs/audits/2026-03-20-scoring-fix-m5-loop2.md`*
*Source audit: `docs/audits/2026-03-20-scoring-audit-m5-loop1.md`*

---

## Executive Summary

**Overall Verdict: NOT READY for production WebFront integration.**

The 8 fixes from Loop 2 fundamentally improved the system — queue inversion is fixed, bucket routing is rebalanced, and thesis tasks are correctly demoted. However, verification reveals two significant issues that must be resolved before the WebFront can use this data:

1. **Ceiling compression** — 53% of all actions (61/115) are pinned at exactly 10.00, destroying rank discrimination within the top tier (Portfolio Check-ins, Meeting/Outreach, Pipeline Actions all score identically)
2. **Misclassification of portfolio Research actions** — 24 portfolio-specific Research actions (e.g., "Request detailed unit economics", "Flag execution risk", "Commission independent lab testing") are marked `is_agent_delegable = true` despite requiring Aakash's personal judgment and relationships

The scoring *direction* is correct. The scoring *resolution* is not.

---

## Check 1: Score Distribution Quality

### Query Result
| Metric | Value |
|--------|-------|
| Min | 0.05 |
| Max | 10.00 |
| Avg | 7.08 |
| P25 | 4.05 |
| P50 (Median) | 10.00 |
| P75 | 10.00 |
| Stddev | 3.48 |

### Score Histogram
| Range | Count | % |
|-------|-------|---|
| = 10.00 (ceiling) | 61 | **53%** |
| 9.00 - 9.99 | 2 | 2% |
| 7.00 - 8.99 | 4 | 3% |
| 5.00 - 6.99 | 5 | 4% |
| 3.00 - 4.99 | 21 | 18% |
| < 3.00 | 22 | 19% |

### Verdict: PARTIAL PASS

Scores are correctly bounded within 0-10 (no scale bug). The range is wide (0.05 to 10.00) with stddev 3.48, indicating good macro-level discrimination between action *types*. However, the distribution is severely bimodal:
- **61 actions pinned at 10.00** — no discrimination among the most important actions
- **21 actions clustered at ~4.05** — fine-grained time decay creates micro-differences but scores are functionally identical
- The median being 10.00 means more than half the queue is at the ceiling

**Problem:** When the WebFront shows the top 10 user actions, all 10 will score 10.00. The sort order within that tier depends on database insertion order, not priority. A P1 Portfolio Check-in and a P0 Portfolio Check-in are indistinguishable.

---

## Check 2: User vs Agent Queue Sanity

### User Queue (non-delegable) — Text Category Breakdown
| Category | Count | Avg Score |
|----------|-------|-----------|
| Other | 34 | 9.95 |
| Network | 17 | 10.00 |
| Portfolio | 5 | 10.00 |
| Thesis | 1 | 9.61 |

### Agent Queue — Text Category Breakdown
| Category | Count |
|----------|-------|
| Other | 29 |
| Thesis/Research | 5 |

### Queue Size Totals
| Queue | Count |
|-------|-------|
| User triage (total in view) | 91 |
| — Human required (non-delegable) | 57 |
| — Agent delegable (in view) | 34 |
| Agent work queue (separate view) | 34 |

### Verdict: PARTIAL PASS

**Good:** The user queue is portfolio/network-heavy. Thesis tasks are almost absent from the non-delegable queue (only 1 of 57). The agent queue correctly captures 34 research/thesis tasks.

**Problem:** The text-matching categorization undercounts Portfolio (only 5 matched by keyword) because many portfolio actions use action types like "Meeting/Outreach" or "Pipeline Action" rather than containing the word "portfolio" in the action text. The actual action_type breakdown tells the real story (see Check 2b below).

### Check 2b: Action Type Distribution with Scores
| Action Type | Count | Avg Score | Min | Max |
|-------------|-------|-----------|-----|-----|
| Portfolio Check-in | 19 | 10.00 | 10.00 | 10.00 |
| Meeting/Outreach | 32 | 9.99 | 9.61 | 10.00 |
| Pipeline Action | 13 | 9.88 | 8.97 | 10.00 |
| Content Follow-up | 1 | 7.62 | 7.62 | 7.62 |
| Research | 46 | 3.48 | 0.05 | 7.46 |
| Thesis Update | 4 | 2.23 | 0.05 | 4.47 |

**This is the correct hierarchy.** Portfolio > Meeting > Pipeline > Content > Research > Thesis. The scoring function perfectly captures Aakash's priorities at the type level. The problem is within-type discrimination (all 19 Portfolio Check-ins score exactly 10.00).

---

## Check 3: Top 10 User Actions

| Rank | ID | Action | Type | Priority | Score |
|------|-----|--------|------|----------|-------|
| 1 | 48 | Flag operational risk on 'Free Lifetime Repairs' promise for Terractive | Portfolio Check-in | P0 | 10.00 |
| 2 | 107 | Share Monday.com SDR-to-agent operational data with Z47/DeVC portfolio companies | Portfolio Check-in | P1 | 10.00 |
| 3 | 74 | Schedule call with Dhruv Kohli (CEO) to review unit economics data | Meeting/Outreach | P0 | 10.00 |
| 4 | 75 | CRITICAL: Pause investment activities for Orange Slice | Portfolio Check-in | P0 | 10.00 |
| 5 | 61 | Schedule operational deep-dive with CEO Rohit Arora | Meeting/Outreach | P0 | 10.00 |
| 6 | 84 | Flag privacy/spam complaint risk for PowerUp Money | Portfolio Check-in | P0 | 10.00 |
| 7 | 11 | Flag execution risk on Grow financing arm for GameRamp | Portfolio Check-in | P0 | 10.00 |
| 8 | 50 | Flag regulatory risk on AI features for Unifize | Portfolio Check-in | P0 | 10.00 |
| 9 | 52 | Schedule call with Unifize product/investor to clarify funding opacity | Meeting/Outreach | P0 | 10.00 |
| 10 | 45 | Schedule board-level call with CEO Akash Goel | Meeting/Outreach | P0 | 10.00 |

### Verdict: PASS

Every single action in the top 10 is either a Portfolio Check-in or Meeting/Outreach. These are all genuine high-priority actions that require Aakash's personal judgment. This is a massive improvement over the pre-fix state where the top 7 were all thesis/research tasks.

**Note:** All 10 score 10.00, so the *relative* ordering within this tier is arbitrary (database order). ID 75 ("CRITICAL: Pause investment activities for Orange Slice") should arguably be #1, not #4.

---

## Check 4: Bottom 10 User Actions

| Rank | ID | Action | Type | Priority | Score |
|------|-----|--------|------|----------|-------|
| 1 | 111 | Map Indian coding AI infrastructure landscape for DeVC pipeline | Pipeline Action | P1 | 8.97 |
| 2 | 108 | Map and reach out to E2B, orchestration layer infra companies | Pipeline Action | P1 | 9.47 |
| 3 | 104 | Share Wang interview with CodeAnt AI founder | Meeting/Outreach | P2 | 9.61 |
| 4-10 | Various | Portfolio Check-ins and Meeting/Outreach | Mixed | P0-P1 | 10.00 |

### Verdict: PASS (with caveat)

The bottom of the non-delegable user queue still contains high-quality actions (Pipeline Actions and Meeting/Outreach). No thesis or research tasks leaked into the bottom of the user queue. The lowest-scored non-delegable actions (8.97-9.61) are Pipeline Actions with slight time decay — which is reasonable.

**Caveat:** The "bottom 10" query returned items scoring 8.97-10.00 because the sort was ASC and the view's ORDER BY was overridden. The actual bottom-scored items in the full view are the agent-delegable Research items (scoring 2.05-7.46), which are filtered out by `WHERE NOT is_agent_delegable`.

---

## Check 5: Bucket Distribution (action_scores matview)

| Bucket | Actions | % | Avg Confidence |
|--------|---------|---|----------------|
| Deepen Existing (Bucket 2 — Portfolio) | 43 | **47.3%** | 0.84 |
| Expand Network (Bucket 3) | 24 | **26.4%** | 0.54 |
| Discover New (Bucket 1) | 22 | 24.2% | 0.58 |
| Thesis Evolution (Bucket 4) | 2 | **2.2%** | 0.35 |

### Verdict: PASS

The bucket routing is now correctly aligned with Aakash's priority hierarchy:
- **Portfolio (Bucket 2) dominates at 47%** — was 14% pre-fix. Highest confidence (0.84).
- **Network (Bucket 3) at 26%** — was 11% pre-fix.
- **Thesis (Bucket 4) collapsed to 2%** — was 55% pre-fix.

The multiplier rebalancing (B2 x1.5, B3 x1.3, B4 x0.6) worked as designed. This is the most successful fix in the batch.

---

## Check 6: Agent-Delegable Classification Spot-Check

### Agent-Delegable = TRUE (top 15)
| ID | Action | Type | Assessment |
|----|--------|------|------------|
| 112 | Listen to 20VC Gokul Rajaram 12:15-20:16 segment | Content Follow-up | CORRECT — agent can listen/summarize |
| 105 | Analyze public market AI transition opportunities | Research | CORRECT — market research, agent can do |
| 109 | Research OpenClaw/NanoClaw adoption patterns | Research | CORRECT — pure research |
| 101 | Map the emerging data infrastructure layer for AI | Research | CORRECT — landscape mapping |
| 110 | Research which SaaS categories survive the agentic transition | Research | CORRECT — pure thesis research |
| 115 | Update SaaS Death thesis thread with Gokul's 8 moats framework | Thesis Update | CORRECT — thesis maintenance |
| 103 | Research defense-AI data infrastructure companies | Research | CORRECT — pure research |
| 102 | Update SaaS Death thesis to incorporate Wang's enterprise data moat | Thesis Update | CORRECT — thesis maintenance |
| 106 | Map human-agent orchestration platform landscape | Research | CORRECT — landscape mapping |
| **66** | **Schedule product security review following CVE-2025-32955** | **Research** | **WRONG — requires Aakash's relationship + judgment** |
| **64** | **Request detailed breakdown of customer cohort retention** | **Research** | **WRONG — portfolio diligence, needs Aakash** |
| **60** | **Investigate the 46% MoM drop in D2C web traffic** | **Research** | **WRONG — portfolio risk assessment** |
| **56** | **Commission independent lab testing for Terrasoft** | **Research** | **WRONG — portfolio decision, needs Aakash** |
| **46** | **Request detailed unit economics from Akasa Air** | **Research** | **WRONG — portfolio diligence** |
| **37** | **Request detailed customer case study from Dallas Renal** | **Research** | **WRONG — portfolio diligence** |

### Agent-Delegable = FALSE (top 15)
| ID | Action | Type | Assessment |
|----|--------|------|------------|
| 45 | Schedule board-level call with CEO Akash Goel | Meeting/Outreach | CORRECT |
| 107 | Share Monday.com SDR-to-agent data with portfolio companies | Portfolio Check-in | CORRECT |
| 74 | Schedule call with Dhruv Kohli to review unit economics | Meeting/Outreach | CORRECT |
| 48 | Flag operational risk on 'Free Lifetime Repairs' | Portfolio Check-in | CORRECT |
| 61 | Schedule operational deep-dive with CEO Rohit Arora | Meeting/Outreach | CORRECT |
| 84 | Flag privacy/spam complaint risk for PowerUp Money | Portfolio Check-in | CORRECT |
| 11 | Flag execution risk on Grow financing arm for GameRamp | Portfolio Check-in | CORRECT |
| 50 | Flag regulatory risk on AI features for Unifize | Portfolio Check-in | CORRECT |
| 52 | Schedule call with Unifize product/investor | Meeting/Outreach | CORRECT |
| 75 | CRITICAL: Pause investment activities for Orange Slice | Portfolio Check-in | CORRECT |
| 33 | Intro to Tier-1 Indian auto component OEMs | Pipeline Action | CORRECT |
| 3 | Intro to ISRO and Indian government defense procurement | Meeting/Outreach | CORRECT |
| 63 | Intro to GitHub Enterprise+ and Atlassian sales teams | Pipeline Action | CORRECT |
| 79 | Flag pricing volatility risk on CodeAnt tiers | Portfolio Check-in | CORRECT |
| 9 | Schedule call with Rishabh Goel to review UPI data | Meeting/Outreach | CORRECT |

### Verdict: FAIL — Misclassification Found

**Root cause identified in the view definition:**

```sql
CASE
    WHEN action_type ~~* '%research%' THEN true
    WHEN action ~~* '%research%' THEN true
    ELSE false
END AS is_agent_delegable
```

The `is_agent_delegable` flag is determined purely by `action_type` and text keyword matching. **Any action with `action_type = 'Research'` is automatically marked as agent-delegable**, regardless of whether it's:
- Thesis-level research (agent can do) -- e.g., "Map AI infrastructure landscape"
- Portfolio diligence research (Aakash must do) -- e.g., "Request unit economics from portfolio CEO"

**24 misclassified actions identified:**
- 9 Research actions assigned to Aakash but marked delegable (IDs: 105, 56, 46, 37, 31, 27, 38, 25, 18)
- 15+ Research actions with empty assigned_to that are clearly portfolio-specific diligence (IDs: 66, 64, 60, 36, 35, 34, 24, 16, 13, 4, 81, 72, 71, 67, 62)

These portfolio diligence actions — requesting unit economics, flagging risks, scheduling security reviews — require Aakash's relationships and judgment. They are NOT the same as "map the AI landscape" tasks.

---

## Check 7: Priority Inflation

| Priority | Count | % |
|----------|-------|---|
| P0 | 44 | 38.3% |
| P1 | 59 | 51.3% |
| P2 | 12 | 10.4% |

### Verdict: PARTIAL PASS

Priority labels are clean (P0/P1/P2 only — no mixed formats). However, **89.6% of actions are P0 or P1** (was 86% pre-fix). The normalization from "P1 - This Week" to "P1" absorbed the 4 former "P1" items into the P1 pool, slightly worsening the inflation.

The priority distribution still lacks meaningful signal. When 90% of items are "urgent" or "high," priority is not a useful discriminator.

---

## Check 8: compute_user_priority_score Consistency

### Query Result
```
[] (empty — zero rows with diff > 0.01)
```

### Verdict: PASS

The stored `user_priority_score` column matches the live `compute_user_priority_score()` function output for all 115 actions. Zero drift. The function is deterministic and the persisted values are consistent.

**Note:** The view `user_triage_queue` computes `user_score` live via `compute_user_priority_score(aq.*)` on every query, so it always reflects the current function logic. The `user_priority_score` column on `actions_queue` is a snapshot that could drift if the function is updated without re-running the backfill.

---

## Misclassification Summary

| Issue | Count | Severity | IDs (sample) |
|-------|-------|----------|--------------|
| Portfolio diligence Research marked agent-delegable | ~24 | HIGH | 56, 46, 37, 66, 64, 60, 36, 35, 34 |
| No misclassified non-delegable items | 0 | — | All 57 non-delegable are correct |
| No thesis items in non-delegable queue | 0 (only 1 borderline) | — | — |

The misclassification is one-directional: too many items marked as delegable. The non-delegable classification is tight.

---

## Remaining Issues for Loop 4

### P0 — Must Fix Before WebFront

| # | Issue | Impact | Fix |
|---|-------|--------|-----|
| **L4-1** | **Ceiling compression: 61 actions at 10.00** | Top 10 actions indistinguishable; no within-tier ranking possible | Expand scoring scale: add priority weight (P0 +2, P1 +1, P2 +0 within the function), reduce type boost magnitude, or use a finer scale (0-100 internally, display 0-10) |
| **L4-2** | **Portfolio Research misclassification** | 24 portfolio diligence actions wrongly offered to agents | Add portfolio detection to `is_agent_delegable`: if `action_type = 'Research'` AND (`company_notion_id IS NOT NULL` OR action text matches portfolio company names or `assigned_to = 'Aakash'`), mark as NOT delegable |

### P1 — Should Fix Soon

| # | Issue | Impact | Fix |
|---|-------|--------|-----|
| L4-3 | Priority inflation (90% P0/P1) | Priority is not a useful filter in the WebFront | Re-evaluate priority assignment in the content pipeline; redistribute to target: P0 ~15%, P1 ~35%, P2 ~35%, P3 ~15% |
| L4-4 | Score decay not active | Stale actions retain full scores indefinitely | Set up a cron job or pg_cron to run score recomputation periodically |
| L4-5 | user_priority_score column drift risk | Column could diverge from function if function is updated | Add a trigger on INSERT/UPDATE to auto-compute, or replace with a generated column |

### P2 — Nice to Have

| # | Issue | Impact | Fix |
|---|-------|--------|-----|
| L4-6 | Preference store still empty (0 rated outcomes) | Calibration loop non-functional | Depends on WebFront triage UI — no fix possible until users can rate |
| L4-7 | Thesis connection format still mixed | Inconsistent delimiters | Data hygiene pass (was Fix 7 in Loop 1 but deferred) |

---

## Detailed Scoring Analysis

### Why 61 Actions Hit the Ceiling

The `compute_user_priority_score` function applies:
- **Base:** `COALESCE(relevance_score, 5.0)` — most backfilled scores land at 6.5-9.5
- **Priority boost:** P0 +2, P1 +1
- **Type boost:** Portfolio/Check-in +3, Meeting/Outreach +2
- **Clamp:** `GREATEST(0, LEAST(10, ...))`

For a typical P0 Portfolio Check-in: `base(~7.0) + priority(+2) + type(+3) = 12.0 -> clamped to 10.0`
For a typical P1 Meeting/Outreach: `base(~7.0) + priority(+1) + type(+2) = 10.0 -> exactly 10.0`

The boosts are too large relative to the 0-10 scale. Any portfolio or meeting action with P0/P1 priority mathematically hits the ceiling. The function provides excellent *between-type* discrimination but zero *within-type* discrimination.

### Recommended Fix for Ceiling Compression

Option A (preferred): **Reduce boost magnitudes and add more granular factors**
```
Priority: P0 +1.0, P1 +0.5, P2 +0, P3 -0.5
Type: Portfolio +1.5, Meeting +1.0, Pipeline +0.5
Recency: stronger decay (halve score over 14 days, not 30)
```
This would spread Portfolio P0 actions across 7.0-10.0 instead of all landing at 10.0.

Option B: **Internal 0-100 scale, display 0-10**
Keep current boosts but on a wider scale, then divide by 10 for display. Preserves more granularity.

---

## Overall Verdict

| Dimension | Status | Detail |
|-----------|--------|--------|
| Score range (0-10) | PASS | No out-of-range values |
| Score coverage (100%) | PASS | 115/115 scored |
| Queue separation | PASS | User and agent queues exist and function |
| Queue content alignment | PASS | Top 10 all portfolio/network |
| Bucket routing | PASS | Portfolio 47%, Thesis 2% |
| Priority labels | PASS | Clean P0/P1/P2 |
| Score consistency | PASS | Stored = computed for all rows |
| Score discrimination (within-tier) | **FAIL** | 53% at ceiling, no ranking within top tier |
| Agent-delegable classification | **FAIL** | 24 portfolio Research actions misclassified |
| Priority distribution | **PARTIAL** | 90% P0/P1 still inflated |

**Production readiness: NO — 2 blockers (L4-1, L4-2) must be resolved first.**

The fixes moved the system from "fundamentally broken" to "directionally correct." The WebFront can be *built* against this schema (the views, column names, and sort order are stable), but the data quality needs one more pass before it should be *shown to users*.
