# M5 Scoring Machine -- Perpetual Loop v4 Audit

**Date:** 2026-03-21
**Model Version:** v5.0-L86 (16 multipliers)
**Trigger:** Post-portfolio-fix validation: narrative quality, distribution health, agent context, M7/M9 alignment, missing dimensions

---

## CRITICAL FINDING: Stored Scores Are Massively Stale

### The Bug

`user_priority_score` is a stored column on `actions_queue`. There is **no trigger** to auto-update it when `compute_user_priority_score()` changes. The live function returns values 3.78 to 4.75 points higher than stored values for every single proposed action.

### Evidence

| Action | Stored Score | Live Computed | Delta |
|--------|-------------|---------------|-------|
| #135 Evaluate Plaza round | 2.47 | 7.22 | **+4.75** |
| #138 Schedule Supermemory | 1.21 | 5.70 | **+4.49** |
| #58 Schedule Legend of Toys call | 3.93 | 8.18 | **+4.25** |
| #41 Flag Dodo Payments | 3.30 | 7.53 | **+4.23** |
| #102 Update SaaS Death thesis | 3.09 | 7.30 | **+4.21** |
| #136 Ping Aakrit for LP chat | 4.35 | 8.45 | **+4.10** |
| #11 Flag GameRamp | 3.51 | 7.59 | **+4.08** |
| #10 Flag Inspecity | 4.14 | 8.22 | **+4.08** |
| #45 Schedule Atica board call | 3.72 | 7.79 | **+4.07** |
| #106 Map orchestration landscape | 1.00 | 4.88 | **+3.88** |

**All 34 proposed actions are affected.** Average delta: ~3.5 points.

### Root Cause

The scores were written at an earlier model version (likely pre-multiplicative, pre-verb-pattern, pre-portfolio-bridge). The model has evolved through L26-L86 (60+ iterations of function changes), but nobody called `UPDATE actions_queue SET user_priority_score = compute_user_priority_score(actions_queue.*)` to materialize the new scores.

### Downstream Impact

Everything that reads `user_priority_score` is reporting stale data:
- `scoring_health` view: reports 10/10 health, 5.9% compression -- **wrong**
- `scoring_regression_test()`: 22/22 PASS -- **based on stale data**
- `score_history` / `snapshot_scores()`: tracking stale values
- `scoring_velocity()`: trends are meaningless (comparing stale to stale)
- `scoring_intelligence_report()`: ranking and top-20 based on stale scores
- WebFront / any consumer reading `user_priority_score` directly

The `explain_score()` function creates a **split brain**: it recomputes multipliers/factors live but reads `final_score` from the stale `user_priority_score` column, so explanations say "scoring 3.3/10" while the actual multiplier math produces 7.5.

### Live Distribution (What Scores Actually Are)

| Bucket | Count | Pct | Avg Score |
|--------|-------|-----|-----------|
| 9-10 | 13 | **31.0%** | 9.56 |
| 7-8 | 17 | **40.5%** | 8.03 |
| 5-6 | 11 | 26.2% | 6.04 |
| 3-4 | 1 | 2.4% | 4.83 |
| 1-2 | 0 | 0% | -- |

**71.5% of actions score 7+. 31% in bucket 9-10.** This is severe top-compression. The model reported healthy (5.9% in 9-10) only because it was reading stale scores.

### Required Fix

1. Run score refresh: `UPDATE actions_queue SET user_priority_score = compute_user_priority_score(actions_queue.*) WHERE status = 'Proposed'`
2. Add a trigger or scheduled job to keep scores current
3. After refresh, re-evaluate whether the model itself needs recalibration (likely yes -- the live distribution shows the verb_pattern and acceptance multipliers aren't penalizing enough to spread the distribution)

---

## Narrative Score Explanation Quality (Top 5)

Despite the stale score issue, narratives are working well structurally. Tested via `narrative_score_explanation()` on top 5 actions.

### #118 -- Cultured Computers Investment Decision (10.0/10)
- Narrative correctly identifies: P0 priority, "Agentic AI Infrastructure" thesis (Very High conviction), Cindy +7%, depth grade 4
- Includes Megamind agent feedback: "strong P0... 4-5 day deadline... novel pre/post reasoning architecture"
- **Missing:** No portfolio context (correct -- this is pipeline, not portfolio)
- **Quality: GOOD** -- actionable, includes agent reasoning

### #121 -- Levocred Pitch Deck Review (9.58/10)
- Correctly flags 1 overdue obligation (relationship risk), Cindy +12%
- Thesis link: "AI-Native Enterprise"
- **Missing:** No company-specific context (Levocred not in portfolio yet)
- **Quality: GOOD**

### #120 -- AuraML Investor Connects (8.95/10)
- **EXCELLENT portfolio context:** "AuraML is a significant position at 2.22% ownership ($100K invested)"
- Includes Cindy +16%, verb_pattern -22% penalty (historically dismissed connect actions)
- Agent feedback from ENIAC: "should be slightly lower -- Green health, no fumes risk"
- Key questions present in agent_scoring_context: NVIDIA partnership, revenue model, CTO departure
- **Quality: EXCELLENT** -- full portfolio context, agent reasoning, behavioral learning

### #119 -- AuraML Schneider Endorsement (8.74/10)
- Full portfolio context, 1 overdue obligation, Cindy +16%
- Portfolio health +13% (significant ownership)
- **Quality: EXCELLENT**

### #107 -- Monday.com SDR Data Sharing (8.33/10)
- Thesis momentum: "SaaS Death / Agentic Replacement" (High conviction, strong momentum)
- Interaction coverage +7.8%
- **Missing:** No portfolio_context (action references portfolio generically, not specific company)
- **Quality: GOOD**

### Narrative Verdict
Portfolio context is rich and useful when present. AuraML actions (#119, #120) demonstrate the ideal: ownership, cheque, key questions, health status, agent feedback, behavioral learning all flowing into a readable narrative. The portfolio bridge fix is working -- these narratives would have been empty before v3.

---

## Agent Scoring Context Quality (Top 3 Portfolio-Linked)

Tested `agent_scoring_context()` on the 3 highest-scoring portfolio-linked actions.

### #120 -- AuraML Investor Connects
**Portfolio context returned:**
- Ownership: 2.22% (HIGH tier), $100K entry cheque
- Stage: early revenue, Health: Green, Ops priority: P1
- Key questions: 5 specific questions (NVIDIA partnership revenue, pricing model, enterprise pipeline, CTO departure, hardware lock-in)
- Thesis connections: 5 threads (CLAW Stack, Agent-Friendly Codebase, AI-Native Non-Consumption, Agentic AI Infra, SaaS Death)
- Outcome: Cat C SaaS, Best case $150M, Good case $60M
- Agent instructions: clear 5-point reasoning framework

**Verdict: EXCELLENT.** An agent receiving this context has everything needed to reason about whether "connect AuraML with 5 investors" is the right priority. The key questions alone would let Megamind reason: "Is fundraising support the highest-value action when we still don't know if NVIDIA partnership generates revenue?"

### #119 -- AuraML Schneider Endorsement
Same rich portfolio context + obligation multiplier 1.25 (overdue obligation detected).

### #104 -- CodeAnt Wang Interview Share
- Ownership: 1.73% (MEDIUM tier), $200K entry + $300K reserve deployed
- Key questions: 5 questions (ARR, enterprise/SMB mix, churn vs CodeRabbit, India/US split, Series A)
- Deep dive: Yes (breakout potential noted)
- Thesis: "Agent-Friendly Codebase as Bottleneck"
- Thesis momentum multiplier: 1.10 (active thesis with momentum)

**Verdict: EXCELLENT.** Full picture for agent reasoning.

### Coverage Gap
- 13/34 proposed actions are portfolio-linked (38.2%)
- Of those, `agent_scoring_context` returns full portfolio context for all 13
- 21/34 non-portfolio actions get no portfolio_context (correct behavior)

---

## M9 Distribution Health (Post-Stale-Score Discovery)

M9 reported 70.8% of actions in buckets 1-3 after recalibration. That was based on stale scores.

### Stale Distribution (What M9 Saw)

| Bucket | Count | Pct |
|--------|-------|-----|
| 9-10 | 2 | 5.9% |
| 7-8 | 6 | 17.6% |
| 5-6 | 9 | 26.5% |
| 3-4 | 9 | 26.5% |
| 1-2 | 8 | 23.5% |

This looked healthy. Evenly distributed, no compression.

### Live Distribution (Reality)

| Bucket | Count | Pct |
|--------|-------|-----|
| 9-10 | 13 | **31.0%** |
| 7-8 | 17 | **40.5%** |
| 5-6 | 11 | 26.2% |
| 3-4 | 1 | 2.4% |
| 1-2 | 0 | 0% |

**The distribution is severely top-heavy.** The model's 16 multipliers, when properly applied, boost almost everything above 7. The verb_pattern penalty (max -25%) and acceptance_mult (max -8%) are insufficient to counterbalance the cumulative effect of 14 other boosting multipliers.

### Why This Happens
Every multiplier defaults to 1.0 and can only go UP (except verb_pattern, acceptance, and thesis type). So the product of 16 multipliers almost always exceeds 1.0. Combined with P0/P1 priority boosts (+7-15%), type boosts (+8-15%), depth boosts (+5-15%), and source boosts (+2-8%), even a mediocre base score gets pushed to 7+.

### M9 Alignment
M9's finding of "70.8% in buckets 1-3" was an artifact of stale scores. The live model actually has 0% in bucket 1-2 and only 2.4% in bucket 3-4. M9's recalibration assessment needs to be revised.

---

## M7 Convergence Alignment

M7 convergence at 0.764. Is scoring aligned with convergence goals?

### Strategic Correlation
- `corr_strategic`: 0.791 (from scoring_health view -- but this is stale)
- Live correlation would need recomputation after score refresh

### Priority Hierarchy (Live)
The P0 anomaly analysis reveals a **structural problem** with live scores:

| Priority | Stored Avg | Live Avg (estimated) |
|----------|-----------|---------------------|
| P0 | 5.13 | ~8.0 |
| P1 | ~5.5 | ~7.8 |
| P2 | 3.79 | ~6.5 |

The gap between P0 and P1 has collapsed in the live model. P0 actions that were correctly below median (Flag actions with 0% accept history) now score 7.5+ because the portfolio_health, depth, and priority multipliers overwhelm the verb_pattern penalty.

### M7 Alignment Assessment
The scoring model is **not well-aligned** with M7 convergence goals because:
1. Score compression prevents differentiation between "important" and "critical"
2. P0 actions that users historically dismiss still score 7+
3. The model can't express "this is important but user won't act on it"

---

## Key Question Relevance: 142/142 Populated but 0/34 Matching

### Discovery
M12 data enrichment has populated `key_questions` for 142/142 portfolio companies (100% coverage). This is up from 14/142 (9.8%) reported in the L56-65 audit.

### The Matching Problem
Despite full population, `key_question_relevance()` returns 1.0 (no boost) for every single action. The function requires **40% keyword overlap** between action text and individual key question lines (words >4 chars).

Example test case -- AuraML:
- Action: "Connect AuraML with 5 investors in robotics/AI space for fundraising"
- Key question: "NVIDIA partnership: revenue-generating or strategic/promotional only?"
- Overlap: "AuraML" doesn't appear in key_questions. Key words like "NVIDIA", "partnership", "revenue" don't appear in action text.
- Result: 0% overlap, no match

The threshold (40% keyword overlap) is too strict for the style of actions vs key questions. Actions are action-oriented ("connect", "schedule", "flag"), while key questions are analytical ("what is ARR growth rate?"). They operate at different semantic levels.

### Potential Fixes
1. Lower threshold from 40% to 20% keyword overlap
2. Switch to semantic/embedding similarity instead of keyword overlap
3. Match at company level: if action is about company X and company X has key_questions, give a baseline boost

---

## Missing Scoring Dimensions

### What Agents Still Lack

1. **Temporal context** -- No "last time user engaged with this company" signal. We have `interaction_recency_boost` but it only goes back 30 days. For portfolio companies with quarterly check-in cadence, a 60-90 day window would capture the "overdue for check-in" signal.

2. **Cross-action dependencies** -- No way to express "do this BEFORE that." Investment decisions should pull related research/evaluation actions up. Currently each action scores independently.

3. **User engagement velocity** -- Accept/dismiss rate over the last 7 days vs 30 days. A user who dismissed 5 actions today is in a different mode than one who accepted 3.

4. **Company lifecycle stage weighting** -- Pre-revenue portfolio companies with fumes risk should score differently than post-revenue growth companies. Currently all portfolio companies get similar base treatment.

5. **Obligation chain depth** -- Single obligation count, but no sense of whether it's a 1-step response or a multi-step project. "Send endorsement email" vs "Lead board restructuring" should score differently.

### Factor Coverage Gaps (Current)

| Factor | Coverage | Notes |
|--------|----------|-------|
| Company context | 22/34 (64.7%) | company_notion_id populated |
| Person context | 3/34 (8.8%) | Very low -- scoring_factors person_name |
| Thesis context | 17/34 (50.0%) | Thesis connection enriched |
| Confidence | 34/34 (100%) | All have confidence scores |
| Key question relevance | 0/34 (0%) | Populated but matching broken |
| Avg confidence | 0.84 | Range: 0.653-0.960 |

Low-confidence actions (< 0.75): 14/34 (41.2%). These are mostly old "Flag risk" and "Schedule call" actions from Mar 6 that lack thesis context, have no interactions, and get limited multiplier coverage.

---

## Scoring Velocity Analysis

### System-Wide Trend
- **17 rising, 1 stable, 31 falling** across all tracked actions (including non-Proposed)
- Average change: -1.33 (but this is stale-to-stale comparison)
- The "falling" trend is actually the verb_pattern and acceptance penalties catching up in stored scores from the last refresh

### Top Risers (Stale Scores)
- #20 Flag Boba Bhai: +2.57 (health scrutiny correctly elevated)
- #52 Schedule Unifize call: +1.70

### Top Fallers
- #41 Flag Dodo: -5.77 (verb pattern penalty applied)
- #11 Flag GameRamp: -5.49
- #138 Schedule Supermemory: -4.66

These velocity numbers are artifacts of the last partial score refresh. After a full refresh, all actions would jump 3-5 points and velocity would reset.

---

## Recommendations (Priority Order)

### P0 -- Score Refresh Required
Run `UPDATE actions_queue SET user_priority_score = ROUND(compute_user_priority_score(actions_queue.*)::numeric, 2) WHERE status = 'Proposed'` to materialize current model. After refresh, re-run scoring_health and regression tests against live data.

### P0 -- Auto-Refresh Mechanism
Add one of:
- A Postgres trigger on relevant columns (scoring_factors, priority, etc.)
- A cron-triggered `refresh_action_scores()` that also updates `user_priority_score`
- A view-based approach where consumers read `compute_user_priority_score()` instead of stored column

### P1 -- Recalibrate After Refresh
Once live scores are materialized, the distribution will show 71.5% scoring 7+. The model needs recalibration:
- Increase verb_pattern penalty floor (currently 0.75, maybe 0.60)
- Add more downward multipliers (time_since_last_engagement, user_action_fatigue)
- Or adjust the base model weights to produce lower base scores

### P1 -- Fix Key Question Relevance
Lower threshold from 40% to 20%, or switch to company-level boost (any action about a company with key_questions gets +3-5%).

### P2 -- Person Context Coverage
8.8% coverage is too low. Enrich scoring_factors with person resolution from network DB during action creation.

### P2 -- Extended Interaction Window
Increase interaction_recency_boost window from 30 to 90 days for portfolio companies with quarterly check-in cadence.

---

## Model State Summary

| Metric | Stale (Reported) | Live (Actual) |
|--------|-----------------|---------------|
| Health Score | 10/10 | ~5/10 (estimated after refresh) |
| Regression Tests | 22/22 PASS | Unknown (stale-dependent tests will fail) |
| Compression (9-10) | 5.9% | **31.0%** |
| Score Range | 1.00-10.00 | 4.83-9.85 (estimated) |
| Avg Score | 5.14 | ~7.8 |
| Distinct Scores | 34 | TBD after refresh |
| Portfolio Context | 41.2% | 41.2% (this is live and correct) |
| Key Question Coverage | 0% matching | 0% matching (142/142 populated) |
| Agent Scoring Context | Working | Working (excellent quality) |
| Narrative Explanations | Working | Working (excellent quality) |

**Model version:** v5.0-L86 | 16 multipliers | **Scores need refresh before any assessment is valid**
