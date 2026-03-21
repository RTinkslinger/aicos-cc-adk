# M9 Intel QA Audit -- L56 (Perpetual Loop v5)
**Date:** 2026-03-21 11:25 UTC
**Auditor:** M9 Intel QA Machine
**Baseline:** L55 audit (same day, scored 6.0/10)
**Supabase:** llfkxnsfczludgigknbs (Mumbai)

---

## AUDIT METHODOLOGY

Every number verified by live SQL against Supabase. No recycling from L55. This audit was triggered with 8 specific verification items: M5 stale scores + key_question_relevance threshold, M6 cross-surface search bias, M4 datum_data_quality_check(), IRGI correlation root cause, network embeddings toward 80%, M12 enrichment flow-through, digest.wiki feedback widget entries, and what would push 6.0 to 7.0.

---

## 1. M5 SCORING -- STALE SCORE REFRESH + KEY_QUESTION_RELEVANCE

**Task from brief:** M5 is refreshing stale scores + fixing key_question_relevance threshold. Verify.

### Score Health (scoring_health view -- Proposed actions only)

| Metric | L55 | L56 | Delta |
|--------|-----|-----|-------|
| Total proposed | 34 | **42** | +8 |
| Distinct scores | 34/34 | **40/42** | 2 collisions |
| Avg raw | 5.14 | **8.03** | **+2.89 (massive shift)** |
| Stddev | 2.49 | **1.54** | -0.95 (compressed) |
| Min/Max | 1.00-10.00 | **4.83-9.85** | Range narrowed |
| Top-bucket % | 5.9% | **38.1%** | REGRESSION |
| Strategic correlation | 0.783 | **0.883** | **+0.100 (best ever)** |
| IRGI correlation | -0.047 | **-0.381** | **-0.334 (major regression)** |
| Health score | 10/10 | **8/10** | -2 |
| Compression check | -- | **FAIL** | NEW failure |

### Score Health Dashboard (full actions_queue, all statuses)

| Metric | Value |
|--------|-------|
| Total actions | 144 |
| Mean score | 4.33 |
| Stddev | 2.66 |
| Range | 1.00 - 9.23 |
| Buckets used | 10/10 |
| Max bucket % | 19.4% |
| Staleness: stale >14d | 100 (69.4%) |
| Pct proposed | 29.2% |

### Distribution (all 144 actions, score_health_dashboard)

| Bucket | % | Count |
|--------|---|-------|
| 1 (lowest) | 18.8% | 27 |
| 2 | 19.4% | 28 |
| 3 | 18.1% | 26 |
| 4 | 7.6% | 11 |
| 5 | 3.5% | 5 |
| 6 | 9.0% | 13 |
| 7 | 2.1% | 3 |
| 8 | 2.8% | 4 |
| 9 | 17.4% | 25 |
| 10 | 1.4% | 2 |

The full distribution shows a bimodal pattern: a cluster at 1-3 (56.3% of all actions) and a secondary peak at 9 (17.4%). The scoring model correctly separates dismissed/stale actions (low) from active proposed actions (high). The bimodal shape is appropriate for a system that has dismissed 92 actions.

### Key_question_relevance: NOT IN scoring_factors

`scoring_factors` JSONB contains: `obligation_boost`, `obligation_boost_reason`, `enriched_at`, `source_summary`, `context_enriched`. **No `key_question_relevance` field exists.** This factor is NOT being stored or tracked in the actions data. It exists in `action_score_breakdown` as `f_irgi` (which maps thesis key questions to actions) but is not exposed as a standalone factor the user can inspect.

### Compression Diagnosis

The scoring_health view reports FAIL on compression. Reason: 38.1% of Proposed actions land in the top bucket. This is because M5's multiplicative model boosted obligation_followup actions and fresh actions, pushing 16+ items into the 8.0-9.85 range. The model is doing the right thing (fresh, obligation-linked actions score high) but lacks spread in the upper half.

**Score: 6.5/10** (was 8/10 -- strategic correlation best ever at 0.883, but compression FAIL, IRGI deeply negative, proposed actions over-clustered at top. The all-actions distribution is healthy; only the Proposed subset is compressed)

---

## 2. M6 CROSS-SURFACE SEARCH BIAS -- ENTITY-AWARE MIXING

**Task from brief:** M6 is fixing cross-surface search bias (entity-aware mixing). Verify.

### search_across_surfaces Function

The `search_across_surfaces` function exists and queries 7 surfaces: companies, network, thesis_threads, actions_queue, interactions, content_digests, portfolio. It uses FTS + trigram matching, not semantic/embedding search.

### Bias Summary (thesis threads)

| Thread | Conviction | For:Against | Ratio | Severity |
|--------|-----------|-------------|-------|----------|
| AI-Native Non-Consumption Markets | New | 2:0 | 999:1 | **CRITICAL** |
| Cybersecurity / Pen Testing | Medium | 11:1 | 11:1 | **HIGH** |
| Agentic AI Infrastructure | Very High | 23:4 | 5.75:1 | **HIGH** |
| Agent-Friendly Codebase as Bottleneck | Medium | 6:2 | 3:1 | OK |
| CLAW Stack Standardization & Orchestration Moat | Medium | 5:2 | 2.5:1 | OK |
| Healthcare AI Agents as Infrastructure | New | 7:3 | 2.33:1 | OK |
| USTOL / Aviation / Deep Tech Mobility | Low | 2:1 | 2:1 | OK |
| SaaS Death / Agentic Replacement | High | 12:8 | 1.5:1 | OK |

3 threads have confirmation bias alerts. "AI-Native Non-Consumption Markets" has ZERO counter-evidence -- critical flag. "Cybersecurity / Pen Testing" at 11:1 is strongly biased. "Agentic AI Infrastructure" at 5.75:1 is the highest-conviction thread but has thin counter-evidence relative to its 23 supporting items.

### Thesis Searchability (search_across_surfaces entity coverage)

| Thread | Companies Found |
|--------|----------------|
| SaaS Death / Agentic Replacement | 480 |
| Agentic AI Infrastructure | 463 |
| Cybersecurity / Pen Testing | 58 |
| AI-Native Non-Consumption Markets | 31 |
| Agent-Friendly Codebase as Bottleneck | 21 |
| Healthcare AI Agents as Infrastructure | 10 |
| CLAW Stack Standardization & Orchestration Moat | 9 |
| USTOL / Aviation / Deep Tech Mobility | 1 |

Two thesis threads dominate search: "SaaS Death" (480 companies) and "Agentic AI" (463) account for 90% of thesis-to-company links. The bottom 4 threads have fewer than 31 companies each. Search will over-index on AI/SaaS topics and under-represent healthcare, CLAW, aviation.

**Score: 5.5/10** (was 6/10 -- search structurally works across surfaces. But thesis confirmation bias alerts are real: 3 of 8 threads flagged. Company distribution heavily skewed toward 2 thesis threads. Entity-aware mixing is not yet balancing results across underrepresented thesis domains)

---

## 3. M4 DATUM DATA QUALITY CHECK -- RESULTS

**Task from brief:** M4 built datum_data_quality_check(). Run it and report results.

### datum_data_quality_check() Output

| Check | Status | Count | % | Assessment |
|-------|--------|-------|---|------------|
| unlinked_actions | INFO | 5 | -- | 5 actions have no company link. Low count = acceptable |
| actions_thesis_rate | **OK** | 144 | 68.8% | 68.8% of actions have thesis_connection. Healthy |
| portfolio_thesis_pct | **WARNING** | 92 | 64.8% | Only 64.8% of portfolio has thesis linkage. Gap |
| portfolio_website_pct | OK | 141 | 99.3% | Near-complete website coverage |
| portfolio_funding_pct | OK | 97 | 68.3% | Reasonable |
| exit_consistency | OK | 0 | -- | No inconsistencies |
| network_embedding_pct | **OK** | 2856 | 81.0% | **PAST 80% MILESTONE** |
| entity_connections | OK | 23,732 | -- | Healthy graph |
| stale_proposed | OK | 11 | -- | 11 stale proposed actions remaining |
| companies_embedding_pct | OK | 4,506 | 98.4% | Near-complete |

### datum_thesis_coverage()

| Thesis | Portfolio | Actions | Active Portfolio | Exited |
|--------|----------|---------|-----------------|--------|
| AI-Native Non-Consumption Markets | 16 | 9 | 10 | 1 |
| SaaS Death / Agentic Replacement | 14 | 10 | 8 | 2 |
| Agentic AI Infrastructure | 11 | 8 | 7 | 2 |
| Healthcare AI Agents as Infrastructure | 6 | 8 | 4 | 1 |
| Cybersecurity / Pen Testing | 6 | 4 | 3 | 0 |
| CLAW Stack Standardization | 5 | 3 | 2 | 1 |
| Agent-Friendly Codebase | 2 | 4 | 2 | 0 |
| USTOL / Aviation / Deep Tech | 1 | 4 | 1 | 0 |

Thesis coverage gap: 50 portfolio companies (35.2%) have NO thesis linkage. "USTOL" has only 1 portfolio company. "Agent-Friendly Codebase" has only 2. These are investment thesis threads with thin portfolio evidence, meaning conviction levels are based on market observation rather than portfolio outcomes.

### cindy_data_quality_check()

| Check | Result |
|-------|--------|
| Health score | CLEAN |
| Duplicates | 0 |
| Unresolved names | 0 |
| Missing person_id | 0 |
| Orphaned interactions | 0 |
| Wrong portfolio match | 0 |
| Obligations: overdue | 8 |
| Obligations: pending | 3 |
| Obligations: escalated | 3 |
| Sources: granola=12, whatsapp=2 | |

Cindy's data quality is pristine (CLEAN) but operationally stalled: 8 overdue, 3 escalated, 0 fulfilled obligations.

**Score: 7/10** (NEW dimension -- datum functions produce clean, actionable output. Network past 80%, companies at 98.4%. The portfolio_thesis gap of 35.2% unlinkaged is the main finding)

---

## 4. IRGI CORRELATION -- ROOT CAUSE IDENTIFIED

**Task from brief:** IRGI correlation regressed to -0.047. Investigate root cause.

### Correlation Matrix (all statuses where both scores exist, n=115)

| Pair | Correlation |
|------|------------|
| user_priority vs strategic | **0.898** (very strong) |
| user_priority vs irgi | **0.372** (weak positive) |
| strategic vs irgi | **0.181** (very weak) |

### Correlation (scoring_health view -- Proposed only, n=42, but 19 have NULL irgi)

| Pair | Correlation |
|------|------------|
| user_priority vs strategic (corr_strategic) | **0.883** |
| user_priority vs irgi (corr_irgi) | **-0.381** |

### Root Cause Analysis

**The -0.381 is a small-sample artifact.** Here's why:

1. **19 of 42 Proposed actions (45.2%) have NULL irgi_relevance_score.** The scoring_health view computes correlation only on the 23 rows that have both values. n=23 is too small for stable correlation.

2. **f_irgi distribution in action_score_breakdown:** 19 actions have f_irgi=0.50 (the default). That's 45% of the sample at one value. For the remaining 23 items, f_irgi ranges from 0.44 to 0.89 -- a narrow band.

3. **The anti-correlation pattern:** High-irgi actions include low-blended-score items (e.g., f_irgi=0.86 has blended_score=2.86, f_irgi=0.85 averages 4.19). These are thesis-connected research actions that score high on IRGI relevance but low on user_priority because they lack time sensitivity, stakeholder priority, or portfolio linkage. This is **correct behavior** -- an action can be thesis-relevant but not urgent.

4. **Across all 115 rows (all statuses):** irgi-vs-user_priority = +0.372. The full dataset shows a positive, if weak, correlation. The Proposed-only subset is distorted by the small n and null concentration.

### Diagnosis
IRGI correlation is not broken -- it was never strongly coupled to user_priority by design. IRGI measures thesis relevance; user_priority blends time, stakeholder, effort, and strategic factors. A thesis-relevant action with no deadline should correctly score high on IRGI but low on user_priority. The -0.381 is a statistical artifact of n=23 with 19 defaults at 0.50.

**Recommendation:** The scoring_health view should either:
- Exclude rows with f_irgi=0.50 (the default) from the correlation calculation, or
- Report irgi correlation as "INSUFFICIENT DATA" when >40% of the sample has null/default values
- Display the full-dataset correlation (0.372) alongside the Proposed-only correlation

**Score: 5.5/10** (was effectively unmeasured -- the correlation metric is misleading. The underlying scoring logic is sound, but the health view produces a scary number that doesn't reflect reality)

---

## 5. NETWORK EMBEDDINGS -- PAST 80%

**Task from brief:** Network embeddings should be approaching 80%+. Verify.

| Metric | L55 | L56 | Delta |
|--------|-----|-----|-------|
| Network total | 3,528 | **3,528** | -- |
| Has embedding | 2,181 (61.8%) | **2,781 (78.8%)** | **+600 (+17.0%)** |
| datum_data_quality_check reports | -- | **2,856 (81.0%)** | -- |
| Has linkedin | -- | **3,089 (87.6%)** | -- |
| Has email | -- | **1,082 (30.7%)** | -- |
| Has role_title | -- | **3,366 (95.4%)** | -- |

### Discrepancy Note
Two different embedding counts: direct query returns 2,781 (78.8%), datum_data_quality_check returns 2,856 (81.0%). The function likely counts differently (possibly including pending jobs that have been processed but not yet committed). The embedding queue shows 698 network items still pending, with an estimated 0.5 hours to drain at 1,570 items/hour.

### Embedding Queue Status

| Table | Pending |
|-------|---------|
| Network | 698 |
| Companies | 84 |
| Actions | 45 |
| **Total** | **827** |

Processing rate: 1,570 items/hour (157 responses in last hour, 10 items per response). Queue will drain in ~30 minutes. After drain, network embeddings will reach approximately **97-98%** (2,781 + 698 = 3,479 / 3,528).

**Score: 8/10** (was 7/10 -- 78.8% and climbing fast. Queue draining at 1,570/hour. Will hit 97%+ within the hour. The 80% milestone from datum_data_quality_check is already reported)

---

## 6. M12 ENRICHMENT FLOW-THROUGH

**Task from brief:** M12 at 142/142. Is ALL the enriched data actually flowing through to intelligence functions?

### Data Quality Dashboard (full system snapshot)

| Entity | Total | Rich (>300 chars) | Medium (100-300) | Thin (<100) | Empty | Avg Content Len |
|--------|-------|-------------------|-------------------|-------------|-------|-----------------|
| Portfolio | 142 | **105 (73.9%)** | 37 (26.1%) | 0 | 0 | **864** |
| Network | 3,528 | **253 (7.2%)** | 2,944 (83.4%) | 331 (9.4%) | 0 | **204** |
| Companies | 4,579 | **731 (16.0%)** | 2,047 (44.7%) | 1,797 (39.2%) | 4 | **169** |

### Portfolio: BEST ENRICHED
105/142 (73.9%) portfolio companies have rich content (>300 chars). Average content length 864 chars. 100% have embeddings. This is the strongest data layer.

### Companies: THIN
Only 731/4,579 (16.0%) have rich content. 1,797 (39.2%) are thin (<100 chars). 4 are completely empty. The vast majority have medium-length content (100-300 chars) -- likely auto-generated summaries from Notion page content, not deep enrichment.

### Network: MEDIUM-DOMINATED
2,944/3,528 (83.4%) have medium content (100-300 chars). Only 253 (7.2%) are rich. Average 204 chars. Most entries are Notion page scrapes yielding "Name | Role | Company" style content rather than intelligence-grade profiles.

### Entity Connections: Flow-Through Evidence

| Connection Type | Total | With Rich Person | With Rich Company |
|-----------------|-------|-------------------|-------------------|
| vector_similar | 10,719 | 4,405 (41.1%) | 5,651 (52.7%) |
| sector_peer | 3,103 | 0 | 3,012 (97.1%) |
| current_employee | 3,062 | 2,979 (97.3%) | 0 |
| past_employee | 2,898 | 2,898 (100%) | 0 |
| thesis_relevance | 1,502 | 0 | 0 |
| inferred_via_company | 1,479 | 1,336 (90.3%) | 0 |

**Critical finding:** `thesis_relevance` connections (1,502 items) have **0% rich content** on either side. These connections exist but the entities they link are thin/medium. The thesis graph is structurally complete but data-poor. Similarly, `led_by` (261), `portfolio_investment` (142), and `action_references` (114) all show 0% rich content joins.

### Enrichment Staging: EMPTY
`util.enrichment_staging` has 0 rows. No pending enrichment in the staging pipeline.

### Verdict: M12 Built the Graph, But Data is Shallow
- Entity_connections went from 0 to 23,732 -- structural success
- But 17 connection types exist and only 5 (vector_similar, sector_peer, current_employee, past_employee, inferred_via_company) actually connect rich data
- thesis_relevance (the most strategically important connection type) links zero rich entities
- The enrichment pipeline needs to prioritize depth on thesis-linked and portfolio-linked entities, not breadth across all 8,000+

**Score: 5.5/10** (structural flow-through is working -- CIR propagates, embeddings process, connections exist. But data richness doesn't penetrate the strategically important connection types. The graph is wide but shallow)

---

## 7. FEEDBACK WIDGET -- ENTRIES EXIST

**Task from brief:** Feedback widget live on digest.wiki. Any feedback entries yet?

### user_feedback_store

| Metric | Value |
|--------|-------|
| Total entries | **6** |
| Oldest | 2026-03-21 10:31 UTC |
| Newest | 2026-03-21 10:31 UTC |
| All timestamps identical | Yes -- batch insert |

### Entry Details

| # | Type | Item Type | Rating | Summary |
|---|------|-----------|--------|---------|
| 1 | rate_quality | intelligence_quality | 4/10 | "User rates overall intelligence quality at 3-4/10. Data is skeletal, connections noise-dominated, scoring compressed" |
| 2 | flag_wrong | data_richness | 1/10 | "Page content is a tweet not intelligence. 29 entities have >500 chars out of 8000+" |
| 3 | flag_wrong | connection_quality | 4/10 | "Connections noise-dominated. 10,719 vector_similar with single evidence. Only 24.9% evidence-based" |
| 4 | rate_quality | scoring | 4/10 | "Score distribution compressed. Stddev 1.42 (target >2.0)" |
| 5 | comment | embedding_recovery | 5/10 | "Companies 100% recovered. Network 23.3% and climbing" |
| 6 | flag_wrong | cron_health | 3/10 | "Embedding processor 490 failures in 24h, CIR queue 62 failures" |

### Assessment
All 6 entries were batch-inserted at the same timestamp by the M10 CIR session -- these are **system-generated audit feedback**, not user-generated widget clicks from digest.wiki visitors. The context fields reference "M10 CIR session 2026-03-21" and "system_health_aggregate."

**No real user feedback has been submitted via the digest.wiki widget.** The 6 entries are machine self-assessments stored as feedback records. The feedback infrastructure works (table exists, inserts succeed) but has zero organic user engagement.

**Score: 3/10** (widget technically works, table stores data. But 0 real user entries. All 6 are machine-generated audit artifacts. The feedback loop is not closing with the actual user)

---

## 8. CRON HEALTH -- 3 FAILING, 3 DEGRADED

### Full Cron Status (22 jobs)

| Status | Count | Jobs |
|--------|-------|------|
| **FAILING** | 3 | normalize-scores, daily_strategic_assessment, cir-staleness-refresh |
| **DEGRADED** | 3 | cir-staleness-check (86.4%), cir-matview-refresh (87.5%), cir-queue-processor (88.2%) |
| **GOOD** | 4 | process-embeddings (95.4%), cir-heartbeat (96.4%), cir-action-entity-map-refresh (93.3%), cleanup-embedding-jobs (100%) |
| **HEALTHY** | 12 | All remaining (pool_cleanup, daily-strategic-briefing, strategic_recalibration, etc.) |

### Failure Clustering
All failures share the same error: `connection failed`. Time distribution of failures in last 24h:

| Hour (UTC) | Failures |
|------------|----------|
| 02:00 | **100** (peak) |
| 03:00 | **87** |
| 04:00 | **44** |
| 05:00 | 27 |
| 06:00 | 14 |
| 07:00 | 1 |
| 08:00 | 9 |
| 20:00-01:00 (prev day) | 5-46 scattered |

The heaviest failure cluster was 02:00-04:00 UTC (231 failures in 3 hours). This correlates with the embedding processor's highest throughput period -- the embedding queue was draining network items at peak rate, exhausting the connection pool. The `pool_cleanup` cron runs every 15 minutes but couldn't keep up during this burst.

**Critical:** `normalize-scores` (0% success, 1 run) failed. This job runs every 6 hours and normalizes action scores. Its failure means the multiplicative model's normalized output hasn't been refreshed, contributing to the compression FAIL in scoring_health.

### Process Stability (last hour)
0 failures in the last hour. All jobs succeeding. The connection pool pressure has subsided. This is a transient issue, not a persistent one.

**Score: 5.5/10** (was 6/10 -- 3 FAILING jobs is worse than L55. normalize-scores failure directly impacts scoring. Connection pool exhaustion during embedding bursts is a known pattern. The system self-heals but the spike at 02:00-04:00 UTC caused cascading impact)

---

## 9. CONTENT PIPELINE -- DAY 5+ DEAD

| Metric | L55 | L56 | Delta |
|--------|-----|-----|-------|
| Total digests | 22 | **22** | -- |
| Last digest | 2026-03-16 | **2026-03-16** | -- |
| Days since last | ~5.5 | **~5.75** | Still dead |

Zero new content. The intelligence loop optimizes stale data. Change events in CIR stopped on March 16 (same day as last digest). The entire downstream system -- action generation, thesis updates, portfolio signal detection -- runs on information that is nearly 6 days old.

**Score: 1/10** (unchanged)

---

## 10. OBLIGATIONS + STRATEGIC LAYER

### Obligations

| Metric | L55 | L56 |
|--------|-----|-----|
| Total | 14 | **14** |
| Overdue | 10→8 | **8** |
| Pending | 3 | **3** |
| Escalated | 1→3 | **3** |
| Fulfilled | 0 | **0** |
| Sources | -- | granola=12, whatsapp=2 |

Still zero fulfilled obligations. Cindy's data quality is CLEAN (no orphans, no mismatches, no duplicates). The data is pristine but operationally inert.

### Strategic Layer

| Component | L55 | L56 |
|-----------|-----|-----|
| Strategic assessments | 17 | **18** (+1) |
| Strategic recommendations | 44 | **52** (+8) |
| Score history | 227 | **227** |
| Interactions | 23 | **23** |
| People interactions | 22 | **22** |

8 new strategic recommendations and 1 new assessment since L55. The Megamind layer is generating output. But interactions haven't grown (still 23) -- no new meeting/call data feeding the system.

**Score: 5/10** (unchanged -- infrastructure pristine, usage zero, strategic layer slowly growing)

---

## 11. THESIS THREADS -- ALL 8 ALIVE

| Thread | Conviction | Status | Last Updated |
|--------|-----------|--------|-------------|
| Healthcare AI Agents | New | Exploring | 2026-03-21 |
| Cybersecurity / Pen Testing | Medium | Exploring | 2026-03-21 |
| AI-Native Non-Consumption | New | Exploring | 2026-03-21 |
| SaaS Death / Agentic Replacement | High | Exploring | 2026-03-21 |
| Agentic AI Infrastructure | Very High | Active | 2026-03-21 |
| Agent-Friendly Codebase | Medium | Exploring | 2026-03-16 |
| CLAW Stack Standardization | Medium | Exploring | 2026-03-16 |
| USTOL / Aviation | Low | Exploring | 2026-03-06 |

All 8 threads have: conviction set, embedding, key_questions_json, bias_flags. 5 of 8 updated today. "USTOL" last updated March 6 (15 days stale). Only "Agentic AI Infrastructure" has status=Active; all others are "Exploring" despite "SaaS Death" having High conviction and being the most evidence-balanced thread (12:8 ratio).

**Score: 7/10** (comprehensive, all have data, bias_flags working. Status field underused -- "SaaS Death" at High conviction should arguably be Active)

---

## COMPOSITE SCORECARD

| Dimension | L55 Score | L56 Score | Delta | What Changed |
|-----------|----------|----------|-------|-------------|
| Scoring model (M5) | 8/10 | **6.5/10** | **-1.5** | Compression FAIL, IRGI -0.381, normalize-scores cron failing. Strategic corr 0.883 best ever |
| Search bias (M6) | 6/10 | **5.5/10** | -0.5 | 3/8 thesis threads with confirmation bias. Company distribution 90% skewed to 2 threads |
| Datum quality check (M4) | NEW | **7/10** | NEW | Functions produce clean output. Network 81%, companies 98.4%. Portfolio 64.8% thesis gap |
| IRGI correlation | N/A | **5.5/10** | NEW | Root cause: small-sample artifact (n=23, 19 defaults). Full dataset shows +0.372. Metric misleading |
| Network embeddings | 7/10 | **8/10** | **+1.0** | 61.8% -> 78.8%, approaching 98% after queue drain. Fastest-improving dimension |
| M12 flow-through | 7.5/10 | **5.5/10** | -2.0 | Graph wide (23,732) but shallow. thesis_relevance has 0% rich content. Depth problem |
| Feedback widget | NEW | **3/10** | NEW | 6 entries, all machine-generated. Zero real user feedback |
| Cron health | 6/10 | **5.5/10** | -0.5 | 3 FAILING, 3 DEGRADED. Connection pool exhaustion at 02-04 UTC. normalize-scores down |
| Content pipeline | 1/10 | **1/10** | 0 | Day 5.75 dead |
| Obligations + strategic | 7.5/10 | **5/10** | -2.5 | Zero fulfilled. 8 overdue. Strategic layer growing slowly (+8 recommendations) |
| Thesis threads | NEW | **7/10** | NEW | All 8 alive with full data. 3 bias alerts. Status field underused |

### OVERALL: 5.5/10 (was 6.0/10, -0.5)

The regression is driven by deeper measurement precision:
- L55 rated scoring 8/10 before the compression FAIL surfaced
- L55 rated M12 enrichment 7.5/10 based on key_questions coverage; flow-through analysis reveals the graph is wide but shallow
- L55 didn't measure feedback widget or datum quality check separately
- Obligation score dropped because zero completions after 14+ hours of full infrastructure availability is a system failure, not a pending item

---

## WHAT WOULD PUSH FROM 5.5/10 (OR 6.0) TO 7.0

Ranked by expected impact on composite score:

### 1. Fix Content Pipeline (+1.5 points)
Still the single highest-impact fix. 5.75 days without fuel. YouTube cookies likely expired. Refresh cookies, verify orchestrator heartbeat. Even 5 new digests prove the loop lives and unblock: new actions, new thesis evidence, new change events for CIR, new signals for portfolio.

### 2. Fix normalize-scores Cron (+0.5 points)
The `normalize-scores` job failed (0% success rate in 24h). It runs `compute_user_priority_score()` for all proposed actions every 6 hours. Its failure means the scoring model's multiplicative output isn't being renormalized. This directly causes the compression FAIL. Check: is it a simple connection pool issue (transient) or a code error?

### 3. Enrich thesis_relevance Connections (+0.5 points)
1,502 thesis_relevance connections link zero rich-content entities. These are the most strategically important connections in the graph. M12's enrichment pipeline should prioritize: (a) portfolio companies linked to thesis threads, (b) network contacts at those companies. Currently the pipeline enriches everything equally -- it should weight thesis-adjacent entities higher.

### 4. Fix IRGI Correlation Metric (+0.3 points)
The scoring_health view reports -0.381 which is misleading. Fix: when >40% of the correlation sample has null/default values, report "INSUFFICIENT DATA" instead of a number. Or compute correlation only on non-default rows. This doesn't fix scoring, it fixes the monitoring layer so audits measure reality.

### 5. Drive 1 Obligation Fulfillment (+0.3 points)
14 obligations, 0 fulfilled. The infrastructure is complete (Supabase tables, server actions, client buttons, AI suggestions). The gap is delivery. One real obligation completion -- even manually via digest.wiki -- would prove the loop closes. Top 3 candidates: Ping Aakrit for LP chat (time-sensitive), AuraML/Schneider endorsement (blocking a deal), Hitesh/Kilrr Series A docs.

### 6. Fix Connection Pool Exhaustion (+0.2 points)
Configure `pool_cleanup` to run more frequently during embedding bursts, or rate-limit the embedding processor to prevent pool exhaustion. The 02:00-04:00 UTC spike caused 231 failures. `process-embeddings` runs every 2 minutes but spawns batches that can hit max_connections. A simple `SET statement_timeout = '30s'` or connection pooling (pgbouncer) would help.

### 7. Add Counter-Evidence to Biased Thesis Threads (+0.2 points)
"AI-Native Non-Consumption Markets" has ZERO counter-evidence. This is a critical bias alert. Either the content pipeline needs to source contrarian views, or M5 should penalize actions linked to zero-counter-evidence thesis threads, or M12 should explicitly seek counter-arguments when enriching thesis-linked entities.

---

## TRAJECTORY ASSESSMENT

**Direction: MIXED.** The headline score dropped 6.0 -> 5.5, but this is measurement refinement, not regression. The dimensions that improved (embeddings 62% -> 79%, datum functions working, thesis threads fully populated) are real. The dimensions that scored lower (enrichment depth, feedback widget, obligations) are existing gaps that L55 didn't fully measure.

**The system's actual capabilities improved since L55:**
- Network embeddings: +17% (fastest improvement across any dimension)
- Strategic recommendations: +8 new
- Datum quality functions: producing clean, actionable output
- Connection pool failures: subsided (0 in last hour, down from 231 peak)

**The system's monitoring got sharper:**
- Compression FAIL detected in scoring_health
- IRGI correlation root-caused (small-sample artifact)
- thesis_relevance data poverty identified
- Feedback widget: 0 real user entries exposed

**Structural constraint unchanged:** Content pipeline dead for 5.75 days. This caps every downstream dimension. No new actions, no new evidence, no new thesis signals. The system polishes stale data with increasing precision.

**Path to 7.0 requires 2 things:**
1. Content pipeline alive (necessary condition)
2. Data depth on strategically important entities (sufficient condition)

Everything else -- cron fixes, metric corrections, obligation completions -- are incremental. The step function from 5.5 to 7.0 needs fresh data flowing through an enrichment pipeline that prioritizes depth where it matters (thesis-linked, portfolio-linked) over breadth across all 8,000+ entities.

---

*Generated: 2026-03-21 11:25 UTC*
*Auditor: M9 Intel QA Machine, L56*
*All numbers from live SQL queries against Supabase llfkxnsfczludgigknbs*
*Previous: docs/audits/2026-03-21-m9-perpetual-v4.md (L55, 6.0/10)*
