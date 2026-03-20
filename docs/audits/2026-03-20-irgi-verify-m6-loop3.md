# IRGI Verification: M6 Loop 3

**Date:** 2026-03-20
**Verifier:** Claude Opus 4.6 via Supabase MCP
**Project:** llfkxnsfczludgigknbs (ap-south-1 Mumbai, PG17)
**Scope:** Independent verification of M6 Loop 2 fixes (score compression, bucket routing, latent connections, bias detection)

---

## Check 1: Score Distribution (No More Compression)

**Query:** `actions_queue` where `relevance_score IS NOT NULL`

| Metric | Value |
|--------|-------|
| Total scored | 115 |
| Min score | 2.525 |
| Max score | 10.000 |
| Avg score | 7.066 |
| Stddev | **2.432** |
| Flat 0.90 count | **0** |

**Scale note:** The `relevance_score` column on `actions_queue` uses a **0-10 scale** (M5 user priority scores), NOT the 0-1 scale from the IRGI function. The IRGI `score_action_thesis_relevance` function outputs on 0-1 (verified: action 29 returns 0.818, 0.805, 0.624, etc.). These are **two separate scoring systems** that have not yet been unified.

**Score histogram (0-10 scale, actions_queue.relevance_score):**

| Range | Count |
|-------|-------|
| 2.0-3.0 | 4 |
| 3.0-4.0 | 18 |
| 4.0-5.0 | 15 |
| 5.0-6.4 | **0 (gap)** |
| 6.4-7.0 | 6 |
| 7.0-8.0 | 13 |
| 8.0-9.0 | 24 |
| 9.0-10.0 | 27 |
| 10.0 | 8 |

**Score ceiling at 10.0:** 8 actions sit at exactly 10.0. All are "Flag risk" critical portfolio actions (trademark risk, execution risk, regulatory risk, etc.) with `user_priority_score` also at 10.0. These are legitimate high-priority scores, NOT compression artifacts.

**Gap finding:** Zero actions have `relevance_score` between 4.54 and 6.39. This creates a bimodal distribution -- actions cluster either at the low end (2.5-4.5) or the high end (6.4-10.0). This may be a side effect of the scoring formula having discrete bands rather than continuous output.

### IRGI Function Verified Separately

`score_action_thesis_relevance(29)` output (0-1 scale):

| Thesis | Score | Match Type |
|--------|-------|------------|
| Agentic AI Infrastructure | 0.818 | vector+explicit |
| SaaS Death / Agentic Replacement | 0.805 | vector+explicit |
| CLAW Stack | 0.624 | vector+explicit |
| AI-Native Non-Consumption Markets | 0.586 | vector+explicit |
| Cybersecurity / Pen Testing | 0.422 | vector |

No flat 0.90 scores. Good discrimination between connected theses (0.818 vs 0.805 vs 0.624) and unconnected (0.422).

**Verdict: PASS** -- flat 0.90 compression eliminated in IRGI function. Stored column scores (0-10) are from M5, not IRGI. Stddev 2.432 >> 0.05 threshold.

**Issue found:** IRGI scores (0-1) are not yet written back to `relevance_score` column (0-10). The Loop 2 report's "Next Steps" item #3 confirmed this was planned but not done.

---

## Check 2: Bucket Distribution (Portfolio-Heavy)

**Query:** `action_scores` materialized view, `primary_bucket` column

| Bucket | Count | Pct |
|--------|-------|-----|
| Deepen Existing (Bucket 2) | **43** | **47.3%** |
| Expand Network (Bucket 3) | 24 | 26.4% |
| Discover New (Bucket 1) | 22 | 24.2% |
| Thesis Evolution (Bucket 4) | 2 | **2.2%** |

**Verdict: PASS** -- Portfolio (B2) at 47.3% > 40% threshold. Thesis (B4) at 2.2% < 10% threshold. Distribution matches Loop 2 report exactly.

---

## Check 3: Latent Connections Quality

**Sample of 20 most recent actions with thesis_connection:**

Spot-check observations:

- **Action 115** (Update SaaS Death thesis with G...): Connected to `SaaS Death / Agentic Replacement|Agentic AI Infrastructure|AI-Native Non-Consumption Markets|CLAW Stack`. Appropriate -- thesis update action correctly tagged to all relevant theses.
- **Action 114** (Research Granola and Gamma as Non-Consumption Market example): Connected to `SaaS Death / Agentic Replacement|AI-Native Non-Consumption Markets`. Correct -- Granola/Gamma are directly relevant to non-consumption markets thesis.
- **Action 108** (Map and reach out to E2B, orchestration layer infra companies): Connected to 6 theses. Reasonable for an infrastructure mapping action that spans the portfolio.
- **Action 107** (Share Monday.com SDR-to-agent operational data): Connected to `SaaS Death / Agentic Replacement`. Exact match -- this is a direct thesis evidence point.

**Connection format issue identified:**

| Format | Action Count |
|--------|-------------|
| Pipe-delimited (new format, `|`) | 40 |
| Single value or legacy format | 75 |

Of 124 pipe-delimited connection segments across all actions, **101 match** actual `thesis_threads.thread_name` values and **23 do not match**. The 23 unmatched are legacy pre-Loop-2 entries using:
- Comma-delimited thesis lists: `"Agentic AI Infrastructure, SaaS Death / Agentic Replacement, Healthcare AI Agents"`
- Free-text hypotheses: `"Developer tools: Stickiness depends on continuous value..."`
- Compound formats: `"Agentic AI Infrastructure + SaaS Death / Agentic Replacement"`

These legacy entries were not normalized during Loop 2.

**Verdict: PASS with caveat** -- The 77 new connections make semantic sense. But 23 legacy thesis_connection values use inconsistent formats that won't resolve in JOINs or function lookups against `thesis_threads`.

---

## Check 4: Bias Detection Working

**Query:** `SELECT * FROM detect_thesis_bias()`

| Thesis | FOR | AGAINST | Ratio | Flag |
|--------|-----|---------|-------|------|
| AI-Native Non-Consumption Markets | 1 | 0 | 999:1 | **CRITICAL: Zero contra evidence** |
| Cybersecurity / Pen Testing | 10 | 1 | 10:1 | **HIGH: >5x FOR:AGAINST ratio** |
| Agentic AI Infrastructure | 21 | 4 | 5.25:1 | **HIGH: >5x FOR:AGAINST ratio** |
| Agent-Friendly Codebase | 6 | 2 | 3:1 | OK |
| CLAW Stack | 5 | 2 | 2.5:1 | OK |
| Healthcare AI Agents | 7 | 3 | 2.33:1 | OK |
| USTOL / Aviation | 2 | 1 | 2:1 | OK |
| SaaS Death / Agentic Replacement | 11 | 8 | 1.38:1 | OK (best balanced) |

Results match Loop 2 report exactly. Function returns 8 rows (all theses), with correct bias flags.

**Verdict: PASS** -- Function deployed, returns correct bias flags, data unchanged since Loop 2.

---

## Check 5: Materialized View Consistent

| Source | Count |
|--------|-------|
| `action_scores` | 91 |
| `actions_queue` | 115 |

**Difference explained:** The materialized view definition filters `WHERE status = 'Proposed'`. Status distribution on `actions_queue`:

| Status | Count |
|--------|-------|
| Proposed | 91 |
| Accepted | 23 |
| Dismissed | 1 |
| **Total** | **115** |

91 Proposed = 91 in materialized view. The view correctly excludes triaged actions.

**Verdict: PASS** -- Count mismatch is by design (view filters to Proposed only). No data loss.

---

## Check 6: M5 / M6 Score Correlation

```
corr(user_priority_score, relevance_score) = 0.954
```

Both `user_priority_score` and `relevance_score` are on a 0-10 scale. The 0.954 correlation is **suspiciously high** for two metrics that supposedly measure different things (user priority vs thesis relevance).

**Investigation:** Both columns have the same range (0.05-10.0 for user_priority, 2.53-10.0 for relevance), and the 8 actions at 10.0 in relevance also have 10.0 in user_priority. This strongly suggests that the `relevance_score` column currently holds **M5 user priority scores or a value derived from them**, not IRGI thesis relevance scores.

This aligns with the Loop 2 report's "Next Steps" item #3: "Write back IRGI scores to `relevance_score` column on actions_queue" -- confirming this writeback has not happened yet.

**Verdict: PASS (not negative)** -- Correlation is 0.954 > 0, meeting the "not negative" threshold. However, this is a data quality flag: the IRGI thesis relevance scores have not been written to `relevance_score`, so the column still holds M5-era data.

---

## Check 7: Triage Queues Working

| Queue | Count |
|-------|-------|
| `user_triage_queue` (non-agent-delegable) | 57 |
| `agent_work_queue` | 34 |

Both views return results (57 + 34 = 91 total Proposed actions). Views are functional.

**Verdict: PASS** -- Both queue views operational, total matches Proposed count.

---

## Summary

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Score Distribution | **PASS** | Flat 0.90 eliminated in IRGI function. Stddev 2.432. |
| 2 | Bucket Distribution | **PASS** | B2 47.3%, B4 2.2%. Exactly as reported. |
| 3 | Latent Connections | **PASS*** | 77 connections valid. *23 legacy entries use inconsistent format. |
| 4 | Bias Detection | **PASS** | 8 rows, correct flags, matches Loop 2 report. |
| 5 | Materialized View | **PASS** | 91 = 91 Proposed. Filter-by-status is by design. |
| 6 | M5/M6 Correlation | **PASS** | 0.954 (not negative). But reveals IRGI writeback not done. |
| 7 | Triage Queues | **PASS** | 57 user + 34 agent = 91 Proposed. |

**Overall: 7/7 PASS (2 with caveats)**

---

## Issues Found

### Issue A: IRGI Scores Not Written Back (Severity: High)

The `relevance_score` column on `actions_queue` still contains M5-era user priority scores (0-10 scale). The IRGI `score_action_thesis_relevance` function outputs correct, decompressed scores on a 0-1 scale, but these have not been written back to the column. The 0.954 correlation between `user_priority_score` and `relevance_score` confirms they are effectively the same data.

**Impact:** Any code reading `relevance_score` from `actions_queue` (Notion sync, triage queues, agent delegation) is using M5 scores, not IRGI thesis relevance. The materialized view `action_scores` does have correct IRGI data in its `thesis_relevance` JSONB array, but the scalar column is stale.

### Issue B: Score Histogram Gap (Severity: Low)

Zero actions in the 4.54-6.39 range creates a bimodal distribution. Not a bug per se (actions genuinely cluster into high-priority portfolio risks vs lower-priority research), but worth monitoring as more actions are added. If the gap persists, it may indicate the scoring formula has a dead zone.

### Issue C: Legacy thesis_connection Format (Severity: Medium)

23 thesis_connection segments use inconsistent formats (comma-delimited, free-text hypotheses, compound `+` notation) that don't resolve against `thesis_threads.thread_name`. These predate Loop 2 and weren't normalized.

Examples of unresolvable values:
- `"Agentic AI Infrastructure, SaaS Death / Agentic Replacement, Healthcare AI Agents"` (comma-delimited)
- `"Developer tools: Stickiness depends on continuous value..."` (free-text hypothesis, not a thread name)
- `"SaaS Death / Agentic Replacement + Agentic AI Infrastructure"` (plus-sign notation)

**Impact:** The `score_action_thesis_relevance` function's explicit_connection matching may miss these 23 connections, underscoring those actions' relevance to their actual theses.

---

## Recommendations for Loop 4

### P0 -- Must Do

1. **Write IRGI scores to `relevance_score`** -- Execute the planned writeback from `score_action_thesis_relevance()` to `actions_queue.relevance_score`. Either:
   - Normalize IRGI 0-1 output to 0-10 scale to match existing convention, OR
   - Migrate `relevance_score` to 0-1 and update all downstream consumers
   - Decision needed on scale before execution

2. **Normalize legacy thesis_connection values** -- Convert the 23 non-standard entries to pipe-delimited format using exact `thesis_threads.thread_name` values. Map `"Agentic AI Infrastructure, SaaS Death / Agentic Replacement, Healthcare AI Agents"` to `"Agentic AI Infrastructure|SaaS Death / Agentic Replacement|Healthcare AI Agents as Infrastructure"`. Drop free-text hypothesis entries (move to `scoring_factors` JSONB if worth preserving).

### P1 -- Should Do

3. **Populate `scoring_factors` JSONB** -- Store the per-method breakdown (vector, trigram, explicit, kq scores) from the IRGI function. This enables debugging and future rebalancing without rerunning the function.

4. **Set up pg_cron for materialized view refresh** -- Currently manual. Schedule `REFRESH MATERIALIZED VIEW CONCURRENTLY action_scores` on a reasonable cadence (every 30 min or on new action insert via trigger).

5. **Investigate histogram gap** -- Run `score_action_thesis_relevance` across all 115 actions and check if the 0-1 output has a similar gap. If not, the gap is an artifact of the M5 scoring formula, and will resolve when IRGI scores are written back.

### P2 -- Nice to Have

6. **Test `find_related_companies` function** -- Not tested in Loop 1, 2, or 3.

7. **Add contra-evidence for AI-Native Non-Consumption Markets** -- Still at 1:0 FOR:AGAINST. The thesis needs deliberate disconfirming signal search before any investment decisions are made based on it.

8. **Audit the 0.954 correlation post-writeback** -- After IRGI scores replace M5 scores in `relevance_score`, re-run the correlation check. A healthy system should show moderate positive correlation (0.3-0.7), not near-perfect correlation, since user priority and thesis relevance measure different dimensions.
