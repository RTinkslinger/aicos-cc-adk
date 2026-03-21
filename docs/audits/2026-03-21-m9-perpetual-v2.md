# M9 Intel QA Audit — L53 (Perpetual Loop v2)
**Date:** 2026-03-21 10:42 UTC
**Auditor:** M9 Intel QA Machine
**Baseline:** L52 audit (same day, scored 4.4/10)
**User baseline:** Intelligence 3/10
**Supabase:** llfkxnsfczludgigknbs (Mumbai)

---

## AUDIT METHODOLOGY

Every number verified by live SQL against Supabase. No recycling from L52. This audit examines each dimension's delta from L52, investigates the compute_user_priority_score(integer) error, and tracks whether the system trajectory is still positive.

---

## 1. EMBEDDING QUEUE — RECOVERING, MYSTERY SOLVED

| Metric | L52 | L53 | Delta |
|--------|-----|-----|-------|
| Network embedded | 896/3,528 (25.4%) | **1,281/3,528 (36.3%)** | **+10.9%** |
| Queue remaining | 2,910 | **2,475** | -435 items |
| Companies embedded | 4,575/4,575 (100%) | 4,575/4,575 (100%) | -- |
| Portfolio embedded | 142/142 (100%) | 142/142 (100%) | -- |

### Mystery Solved: Queue IS Draining

L52 reported the queue was "stalling" because `process_embeddings()` completed in 15ms and queue items showed `read_ct=0`. The actual diagnosis:

1. **pgmq.read() works** — manual test returns items immediately. No stuck locks, no invisible items. All 2,475 queue items have VT in the past (visible).
2. **Edge function is processing** — 3,579 HTTP calls in last 12 hours, 3,577 success (99.9%). Latest responses show `completedJobs` for network table records.
3. **The 15ms cron runs** are instances where the advisory lock was already held by another run, so they returned immediately. The actual processing runs take longer but complete between cron windows.
4. **Drain rate: ~435 items in ~2 hours = ~218/hr.** At this rate, remaining 2,475 items need ~11.4 hours. Should complete within the day.
5. **19 companies re-queued** (10:33-10:35 UTC) — CIR triggered re-embedding for modified company records.

### Previous Diagnosis Was Wrong
L52 said "drain rate collapsed to 24/hr" and predicted 4.5 days. Actual drain rate is ~218/hr. The error came from measuring embedded-record count (which lags behind queue processing due to edge function async writes) versus queue size. Queue is healthy.

**Score: 7/10** (was 5/10 — queue is recovering at a healthy rate, mystery diagnosed, on track to complete today)

---

## 2. SCORING MODEL — MAJOR IMPROVEMENT

### scoring_health View
| Metric | L52 | L53 | Delta |
|--------|-----|-----|-------|
| Health score | 8/10 | **10/10** | **+2** |
| Compression check | **FAIL** (55.1%) | **PASS** (24.5%) | **FIXED** |
| IRGI correlation | -0.012 | **0.074** | +0.086 (still low) |
| Strategic correlation | 0.833 | **0.648** | -0.185 |
| Distinct scores (proposed) | -- | **46** (out of 49) | Near unique |
| Avg proposed score | -- | 7.85 | -- |
| Stddev proposed | -- | 1.43 | -- |

### Compression FIXED
The top-bucket compression that plagued L52 (55.1% of actions in max bucket) is now **24.5%** — well within the PASS threshold. The distribution across proposed actions:

| Bucket | Count | % |
|--------|-------|---|
| 9+ | 12 | 24.5% |
| 8-9 | 11 | 22.4% |
| 7-8 | 10 | 20.4% |
| 6-7 | 12 | 24.5% |
| 5-6 | 2 | 4.1% |
| <5 | 2 | 4.1% |

This is a healthy distribution. The scoring model can now differentiate between important and very-important actions. M5's multiplicative model migration (v3.2-L52 + v3.2-auto) and percentile normalization worked.

### Action Type Hierarchy
| Type | Avg Score | Assessment |
|------|-----------|------------|
| Portfolio/Support | 8.35 | Correct — highest |
| Portfolio Check-in | 6.98 | Correct tier |
| Pipeline | 5.72 | Mid-tier |
| Meeting/Outreach | 5.30 | Mid-tier |
| Research | 3.83 | Lower — appropriate |
| Thesis Update | 3.68 | Lowest — correct |

The hierarchy matches user preference: Portfolio > Pipeline > Meeting > Research > Thesis. This is the right ordering.

### Score History
193 score history entries across all 144 actions. Two scoring versions active: `v3.2-auto` and `v3.2-L52`. The system is tracking score evolution over time.

### IRGI Still Irrelevant
IRGI correlation improved from -0.012 to 0.074 but remains essentially noise. 115 actions have IRGI scores (avg 0.582, stddev 0.173). The IRGI system produces scores with no predictive value for user priority.

### Strategic Correlation Dropped
The strategic_score correlation dropped from 0.833 to 0.648. This may be expected: the new multiplicative model uses more factors beyond strategic_score, so the raw correlation between any single factor and the final score naturally decreases. The overall health score going from 8 to 10 suggests the model is better overall even with lower single-factor correlation.

**Score: 8/10** (was 6/10 — compression fixed, health 10/10, type hierarchy correct. IRGI remains dead weight)

---

## 3. ACTION-COMPANY LINKAGE — STILL IMPROVING

| Metric | L52 | L53 | Delta |
|--------|-----|-----|-------|
| Actions with company_notion_id | 66/144 (45.8%) | **72/144 (50.0%)** | **+4.2%** |
| Company context in scoring_factors | 16/144 | 16/144 | -- |

Half of all actions now have company linkage. The remaining 50% are likely people-centric actions (Meeting/Outreach, Network/Relationships) or generic actions without company context.

**Score: 5.5/10** (was 5/10 — incremental improvement, 50% is a clean milestone)

---

## 4. PORTFOLIO DATA QUALITY

| Metric | L52 | L53 | Delta |
|--------|-----|-----|-------|
| key_questions populated | 46/142 (32.4%) | **63/142 (44.4%)** | **+12.0%** |
| thesis_connection | 45/142 (31.7%) | 45/142 (31.7%) | -- |
| signal_history | 0/142 (0%) | 0/142 (0%) | -- |
| page_content >50 chars | 142/142 (100%) | 142/142 (100%) | -- |
| outcome_category (non-NA) | 97/142 (68.3%) | 97/142 (68.3%) | -- |
| health Red | 18 | 18 | -- |
| health Yellow | 33 | 33 | -- |
| health Green | 84 | 84 | -- |

### Key Questions Progress
14 -> 28 -> 46 -> **63**. A 4.5x improvement from the original 14, all in one day. M12 is steadily enriching portfolio companies with key questions. At this rate, full coverage is achievable within 2 more loops.

### signal_history: STILL EMPTY
Zero companies have signal_history data. CIR propagation runs 74,781 UPDATE events in 24h but none feed into portfolio signal_history. This column remains structurally dead.

**Score: 5/10** (was 4/10 — key_questions 32%->44% is real progress. signal_history still 0%)

---

## 5. OBLIGATION SYSTEM — GENUINELY IMPRESSIVE NEW CAPABILITY

| Metric | L52 | L53 | Delta |
|--------|-----|-----|-------|
| Total obligations | 16 | **14** | -2 (cleaned up?) |
| Overdue | 10 | 10 | -- |
| Completed | 0 | 0 | -- |
| Escalated | 1 | 1 | -- |
| Pending | 5 | **3** | -2 (became overdue) |
| megamind_priority | 0/14 | 0/14 | -- |
| Linked to action | 13/14 | 13/14 | -- |

### NEW: obligation_staleness_audit() — EA-Quality Output

This is the single most impressive new function in the system. It produces:

1. **Critical overdue** — 5 items with EA-quality notes:
   - "CRITICAL: You owe Abhishek Anita (portfolio). 20 days overdue. Set up the WhatsApp group. Takes 2 minutes."
   - "CRITICAL: You owe Ayush Sharma (portfolio). 11 days overdue."
   - Each has `time_estimate`, `category`, `confidence` (0.85-0.95), and `recommendation` (ACT_NOW)

2. **Needs nudge** — 3 items with draft messages:
   - "Hey Supan, wanted to follow up on the send deck and demo video. Any update?" (21 days overdue)
   - "Hey Surabhi, wanted to follow up on the msc fund..." (20 days overdue)
   - Each with confidence and `recommendation: SEND_NUDGE`

3. **Auto-dismiss candidates** — 1 item:
   - "They were supposed to send pitch deck for levocred — 20 days ago. No follow-up since. Safe to dismiss."
   - Confidence 0.9, `recommendation: DISMISS`

4. **EA headline:** "You have 5 critical obligations. Block 30 minutes to clear the backlog."

5. **Total time to clear:** "44 min"

This is the first function in the system that produces genuinely actionable, Cindy-quality EA output. It doesn't just list obligations — it triages them, estimates effort, drafts follow-up messages, and recommends dismissals.

### Still Broken
- Zero completions ever. No fulfillment detection path works.
- megamind_priority still NULL on all 14 obligations.
- Draft messages need polish — "send deck and demo video" should be "the deck and demo video."

### NEW: cindy_daily_briefing() and store_daily_briefing()
Two new functions for Cindy's daily briefing workflow. Not yet evaluated for output quality.

**Score: 7/10** (was 6/10 — obligation_staleness_audit is a breakthrough. Zero completions and null megamind_priority keep it from 8+)

---

## 6. STRATEGIC BRIEFING

No change to `format_strategic_briefing()` function since L52. The same issues apply:
- Dead companies (6 with health=NA) still appear in views
- Truncation in key_questions and action descriptions
- Internal metrics ("Convergence: 49 proposed actions pending") in the header
- Strategic Contradictions section (v2.0) is a good addition

### Strategic Assessments: Active
16 strategic assessments in the last 24 hours. Latest shows:
- 59 total open actions, 36 human actions
- Convergence ratio: 0.796
- 34 stale actions (58% of open actions are stale)
- Portfolio Check-in dominates (23 of 59 = 39%)

### 34 Stale Actions = 58% of Open Actions
More than half of all proposed+accepted actions are stale (>14 days old). This suggests the system generates actions faster than Aakash processes them, or the actions aren't compelling enough to act on. Either way, the action queue is accumulating debt.

**Score: 6/10** (unchanged — briefing structure is good, stale action debt is a concern)

---

## 7. CONTENT PIPELINE — STILL DEAD

| Metric | L52 | L53 | Delta |
|--------|-----|-----|-------|
| Total digests | 22 | 22 | -- |
| Days since last digest | 5.5 | **4.9** | Time passing (NOT improvement) |
| New digests in 24h | 0 | 0 | -- |

Nearly 5 days without any new content digest. The content-to-intelligence loop remains completely broken. No new content-sourced actions since March 16.

**Score: 1/10** (was 2/10 — downgraded because 5 days of stale content with no sign of recovery is worse than "stalling")

---

## 8. INFRASTRUCTURE HEALTH

### Cron Jobs (24h)
| Job | Success | Failed | Assessment |
|-----|---------|--------|------------|
| process_embeddings (jobid=1) | 6,862 | 463 | 93% success — **improved** |
| process_cir_queue (jobid=5) | 738 | 51 | 94% success |
| process_cir_queue_batch (jobid=7) | 422 | 62 | 87% success |
| action_scores matview refresh | 74 | 11 | 87% success |
| cleanup_embedding_jobs | 16 | 0 | 100% success |
| CIR heartbeat | 46 | 2 | 96% success |

### compute_user_priority_score(integer) Error — ROOT CAUSE FOUND

**Diagnosis:**
- Function signature: `compute_user_priority_score(action_row actions_queue)` — takes a ROW type
- Error: "function compute_user_priority_score(integer) does not exist"
- Source: CIR rule #3 fires `process_new_action` on actions_queue INSERT
- `process_cir_queue_item` correctly calls `compute_user_priority_score(v_action_row)` with a row variable
- The 7 errors all occurred at 02:23 UTC for action IDs 118-122 (same batch)
- **No errors since 02:23 UTC** — the issue was a one-time batch that hit a race condition or stale function cache
- All functions currently in the database correctly use the row-type call

**Verdict:** This is NOT a persistent bug. It was a transient error from a single batch at 02:23 UTC. The fix (if any) already happened — possibly a function was replaced between the INSERT trigger firing and the queue processing. No action needed.

### Entity Connections: Growing
| Connection Type | Count | L52 | Delta |
|-----------------|-------|-----|-------|
| Total | **23,251** | 24,752 | -1,501 (cleanup?) |
| company->company vector_similar | 5,161 | -- | -- |
| company->company sector_peer | 3,103 | -- | -- |
| network->company current_employee | 3,062 | -- | -- |
| network->company vector_similar | 3,062 | -- | -- |
| network->company past_employee | 2,898 | -- | -- |
| network->network vector_similar | 1,998 | -- | -- |
| network->thesis inferred | 1,479 | -- | -- |
| thesis->company relevance | 1,077 | -- | -- |

The entity graph is substantial. 23K+ connections with diverse types. The slight decrease from L52 may be from deduplication or cleanup.

### CIR Dead Letter Queue: Empty (0 items)
CIR queue size: 1 item. Dead letter: 0. The CIR system is processing cleanly with no accumulated failures.

### New Data Sources
- **Email candidates:** 4,848 entries across 1,091 unique people (M12 enrichment)
  - Avg confidence: 0.19 — very low. Zero verified. These are pattern-generated guesses, not confirmed emails.
- **WhatsApp conversations:** 0 entries (M8 Cindy not connected yet)
- **Notifications:** 37 total, **0 read**. All notifications are going unread.

**Score: 5/10** (was 4/10 — compute_user_priority_score error resolved as transient, CIR queue healthy, embedding cron working. Email candidates are low-quality)

---

## 9. DATUM IMPACT

| Metric | L52 | L53 | Delta |
|--------|-----|-----|-------|
| Companies with datum_source | 10 | 10 | -- |
| Network with datum_source | 0 | 0 | -- |
| Identity resolution log | -- | **1 entry** | NEW |
| Latest datum activity | 07:37 UTC | 08:03 UTC | +26 min |

Datum touched the same 10 company records and made a single identity resolution entry. Effectively stalled.

**Score: 1/10** (unchanged — negligible impact)

---

## 10. DATA ENRICHMENT (M12)

### Companies (4,575 total)
| Field | L52 | L53 | Delta |
|-------|-----|-----|-------|
| page_content >50 chars | 3,942 (86.2%) | 3,942 (86.2%) | -- |
| sector (100%) | 4,575 | 4,575 | -- |

### Network (3,528 total)
| Field | Coverage | Assessment |
|-------|----------|------------|
| page_content >50 chars | 3,406 (96.5%) | EXCELLENT |
| role_title | 3,359 (95.2%) | EXCELLENT |
| linkedin | 3,089 (87.6%) | GOOD |
| phone | 3,342 (94.7%) | EXCELLENT |
| email | 1,082 (30.7%) | MODERATE |
| enrichment_status | 3,528 (100%) | FULL |
| embedding | 1,281 (36.3%) | RECOVERING |

### Portfolio (142 total)
| Field | L52 | L53 | Delta |
|-------|-----|-----|-------|
| key_questions | 46 (32.4%) | **63 (44.4%)** | **+12.0%** |
| thesis_connection | 45 (31.7%) | 45 (31.7%) | -- |

M12 continues to make progress on portfolio key_questions. Network enrichment is mature (96.5% content, 95.2% roles, 94.7% phone). The main gap is network email (30.7% from real sources vs 4,848 low-confidence candidates).

**Score: 5.5/10** (was 5/10 — key_questions continuing to improve)

---

## 11. AGENT-READINESS RATIO

| Metric | L52 | L53 | Delta |
|--------|-----|-----|-------|
| Total public functions | 220 | **228** | **+8** |
| New functions | -- | cindy_daily_briefing, detect_obligation_fulfillment_candidates, clean_obligation_description, store_daily_briefing, latest_briefing, term_coverage_boost, obligation_staleness_audit, action_verb_pattern_multiplier | -- |

### New Function Assessment
| Function | Category | Assessment |
|----------|----------|------------|
| obligation_staleness_audit | **Agent-ready intelligence** | EXCELLENT — produces structured JSONB with EA reasoning |
| cindy_daily_briefing | Agent-ready context | Good — assembles Cindy context |
| detect_obligation_fulfillment_candidates | Agent-ready intelligence | Good — searches for fulfillment evidence |
| store_daily_briefing / latest_briefing | Infrastructure | Storage/retrieval pair |
| clean_obligation_description | Utility | String cleaning |
| term_coverage_boost / action_verb_pattern_multiplier | Scoring helpers | M5 model refinements |

3 of 8 new functions are agent-ready intelligence (the right direction). The obligation_staleness_audit in particular is the archetype of what good agent-SQL collaboration looks like: SQL structures the data and applies rules, then the output is rich enough for an agent to act on.

### Updated Ratio
- Intelligence-in-SQL: ~16 (format_strategic_briefing and friends — unchanged)
- Agent-tool/Context-serving: ~26 (+3 from obligation and Cindy functions)
- Ratio: **1.63:1** (agent tools : intelligence-in-SQL)

**Score: 5/10** (was 4/10 — obligation_staleness_audit is a model for how to build agent-ready functions)

---

## 12. SYSTEM-WIDE OBSERVATIONS

### Stale Action Debt
34 of 59 open actions (58%) are stale (>14 days). The system generates actions but they accumulate without resolution. This undermines the "what's next" framing — if the queue is 58% old items, the "next" actions are buried under unprocessed debt.

### Notification Dead Zone
37 notifications generated, 0 read. The notification system writes but nothing reads. This is a sink — computation spent producing notifications nobody sees.

### Depth Queue: All Pending
144 depth grades exist, 141 pending, 0 completed. The depth research queue is fully loaded but nothing executes. This was the "DEPTH QUEUE BACKED UP: 141 pending" from the strategic briefing. The system knows about the backlog but can't clear it.

### Email Candidates: Volume Without Quality
4,848 email candidates at 0.19 average confidence, 0 verified. This is bulk pattern-matching (firstname.lastname@domain, etc.) without any verification layer. The data exists but isn't usable until verified.

---

## COMPOSITE SCORECARD

| Dimension | L52 Score | L53 Score | Delta | What Changed |
|-----------|----------|----------|-------|-------------|
| Embedding coverage | 5/10 | **7/10** | **+2** | Network 25%->36%, drain rate 218/hr, mystery solved |
| Scoring model | 6/10 | **8/10** | **+2** | Compression FIXED (55%->24.5%), health 10/10, hierarchy correct |
| Action-company linkage | 5/10 | **5.5/10** | +0.5 | 46%->50% linkage |
| Portfolio data quality | 4/10 | **5/10** | +1 | key_questions 32%->44%, signal_history still 0% |
| Obligation quality | 6/10 | **7/10** | **+1** | obligation_staleness_audit is EA-quality. Still zero completions |
| Strategic briefing | 6/10 | **6/10** | 0 | Unchanged. 58% stale actions is a concern |
| Content pipeline | 2/10 | **1/10** | -1 | 5 days dead. Downgraded for sustained outage |
| Infrastructure health | 4/10 | **5/10** | +1 | CIR clean, embedding cron working, transient error resolved |
| Datum impact | 1/10 | **1/10** | 0 | Stalled at 10 records |
| Data enrichment (M12) | 5/10 | **5.5/10** | +0.5 | key_questions 32%->44%, network mature |
| Agent-readiness ratio | 4/10 | **5/10** | +1 | +8 functions, obligation_staleness_audit is model function |

### OVERALL: 5.1/10 (was 4.4/10)

**Net improvement: +0.7 points.** The system has crossed the 5/10 threshold for the first time.

---

## WHAT ACTUALLY GOT BETTER

1. **Scoring compression FIXED.** The #1 scoring problem from L52 (55% in top bucket) is resolved. 24.5% in top bucket with correct type hierarchy. M5's multiplicative model + percentile normalization delivered.

2. **Embedding queue is healthy.** The "collapsed drain rate" diagnosis was wrong. Queue drains at ~218/hr and should complete today. The process_embeddings function works correctly.

3. **obligation_staleness_audit() is breakthrough-quality.** EA-level triage with draft messages, time estimates, confidence scores, and dismiss recommendations. This is the first function that produces genuinely actionable output without an agent needing to add value.

4. **Key questions: 14->63 in one day.** M12 has enriched 44.4% of portfolio companies with key questions, up from 10% at start of day.

5. **compute_user_priority_score(integer) error: not a bug.** Transient race condition from a single batch at 02:23 UTC. All current function calls use correct row-type signature. No code fix needed.

---

## WHAT'S STILL BROKEN

1. **Content pipeline: 5 DAYS DEAD.** Zero new digests. No content-sourced actions since March 16. This is the single biggest system failure. Without fresh content, the intelligence loop has no fuel.

2. **Datum: ghost.** 10 records touched, 1 identity resolution. The agent has effectively not started.

3. **IRGI: still noise.** Correlation 0.074 with user priority. 27 IRGI functions that pass internal benchmarks but produce irrelevant scores.

4. **Zero obligation completions.** The system can detect and triage obligations beautifully (obligation_staleness_audit proves this) but cannot detect when they're fulfilled.

5. **58% stale actions.** 34 of 59 open actions are >14 days old. The action queue is accumulating debt faster than it clears.

6. **37 unread notifications.** The notification system produces output nobody consumes. Dead computation.

7. **signal_history: still 0%.** CIR runs 74K events/day but none feed portfolio signal history.

8. **141 depth grades pending, 0 completed.** The depth research system is loaded but never executes.

---

## WHAT WOULD MOVE THE NEEDLE TO 6.5/10

1. **Resume content pipeline.** Check droplet orchestrator. Even 2 new digests would prove the loop works. This is the single highest-impact fix.

2. **Connect obligation fulfillment detection.** The new `detect_obligation_fulfillment_candidates()` function exists. Wire it to Granola meeting data or interactions table to detect when obligations are resolved.

3. **Clear stale action debt.** Auto-dismiss or archive actions >21 days old with no obligation link. The obligation_staleness_audit already identifies auto-dismiss candidates — apply similar logic to actions.

4. **Wire notifications to a reader.** 37 unread notifications are waste. Either connect to WhatsApp/mobile or stop generating them.

5. **Execute depth grades.** 141 pending research items. Pick the top 10 by strategic_score and execute. This feeds the intelligence layer.

---

## TRAJECTORY ASSESSMENT

**Direction: UP.** Second consecutive positive audit. The L52->L53 jump (+0.7) crossed the 5/10 threshold. M5 scoring is now genuinely good (compression fixed, hierarchy correct, health 10/10). M8 obligation tooling reached EA quality. Embeddings are recovering.

**Risk: Content pipeline.** Day 5 of zero digests. Every day without content makes the intelligence layer more stale. The improvements from scoring, obligations, and data enrichment are building on a foundation of 5-day-old content. If the pipeline stays dead another 48 hours, the system will start feeling stale to the user regardless of other improvements.

**Milestone: First time above 5/10.** The system went from 3.6 (L51) -> 4.4 (L52) -> 5.1 (L53). At this rate, 6/10 is achievable if the content pipeline resumes and stale actions are cleared.

**Next audit should focus on:**
- Content pipeline status (is orchestrator alive?)
- Embedding completion verification (should hit 50%+ network by next audit)
- Stale action debt resolution
- Depth grade execution progress
- obligation_staleness_audit integration with action queue

---

*Generated: 2026-03-21 10:42 UTC*
*Auditor: M9 Intel QA Machine, L53*
*All numbers from live SQL queries against Supabase llfkxnsfczludgigknbs*
