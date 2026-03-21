# M9 Intel QA Audit -- L57 (Perpetual Loop v6)
**Date:** 2026-03-21 21:30 UTC
**Auditor:** M9 Intel QA Machine
**Baseline:** L56 audit (v5, same day, scored 6.0/10)
**Supabase:** llfkxnsfczludgigknbs (Mumbai)

---

## AUDIT METHODOLOGY

Every number verified by live SQL against Supabase. No recycling from v5. Full system sweep across all 8 dimensions: Actions, Scoring, Thesis, Content, Data (Network/Companies/Portfolio), Entity Connections, Obligations, and Infrastructure (cron/embeddings/CIR).

---

## SYSTEM SCORE: 6.9/10

Previous: 6.0/10 (v5). **Delta: +0.9**

| Dimension | Score | Prev | Delta | Key Finding |
|-----------|-------|------|-------|-------------|
| Scoring Model | 7.5 | 6.5 | +1.0 | Compression PASS, health 10/10, model v5.1-L96 |
| Data Completeness | 8.0 | 7.5 | +0.5 | Embeddings 99.5-100% across all entities |
| Thesis Quality | 7.5 | 7.8 | -0.3 | 3 bias warnings, 1 critical (zero counter-evidence) |
| Content Pipeline | 3.0 | 3.0 | 0 | STALE: 128h since last digest. Pipeline offline |
| Actions Queue | 6.5 | 6.0 | +0.5 | 30 new actions in 24h, but 51% misclassification |
| Obligations | 6.0 | N/A | NEW | 16 tracked, 6 overdue, Ayush bug confirmed |
| Entity Connections | 5.5 | 5.0 | +0.5 | 23,716 connections but 100% single-evidence |
| Infrastructure | 8.0 | 7.0 | +1.0 | 25 crons, 20 healthy, 3 degraded, 2 failing |

---

## 1. SCORING MODEL — 7.5/10

### scoring_health view (Proposed actions only)

| Metric | v5 | v6 | Delta |
|--------|-----|-----|-------|
| Total proposed | 42 | **32** | -10 (cleanup) |
| Avg score | 8.03 | **5.85** | -2.18 (decompressed) |
| Stddev | 1.54 | **1.86** | +0.32 (spread improved) |
| Range | 4.83-9.85 | **3.04-8.70** | Wider, healthier |
| Compression check | FAIL | **PASS** | Fixed |
| Diversity check | -- | **WARN** | New warning |
| Health score | 8/10 | **10/10** | +2 |
| Model version | -- | **v5.1-L96** | Tracked |

### Score separation by status (all scored actions)

| Status | Count | Avg relevance | Avg user_priority | Avg strategic |
|--------|-------|---------------|-------------------|---------------|
| expired | 11 | 9.33 | 6.33 | 0.87 |
| Accepted | 8 | 8.10 | 6.79 | 0.82 |
| Proposed | 25 | 7.70 | 5.55 | 0.84 |
| Dismissed | 90 | 6.70 | 3.99 | 0.41 |

**Separation quality:** Accepted (8.10) vs Dismissed (6.70) = 1.40 gap on relevance_score. User_priority gap is better: 6.79 vs 3.99 = 2.80 spread. Strategic score does best: 0.82 vs 0.41. The user_priority_score is the most discriminating signal.

### Misclassification rate

- Min accepted score: 7.25
- Dismissed actions scoring >= 7.25: **46 out of 90** (51.1%)
- This is a significant problem. Half of dismissed actions have relevance_scores equal to or higher than the lowest accepted action.
- Root cause: `relevance_score` alone is not sufficient for triage prediction. `user_priority_score` provides better separation.

### Score distribution (all 145 actions)

| Bucket | Count | % |
|--------|-------|---|
| 1 (1.0-1.9) | 19 | 13.1% |
| 2 (2.0-2.9) | 13 | 9.0% |
| 3 (3.0-3.9) | 24 | 16.6% |
| 4 (4.0-4.9) | 30 | 20.7% |
| 5 (5.0-5.9) | 14 | 9.7% |
| 6 (6.0-6.9) | 14 | 9.7% |
| 7 (7.0-7.9) | 15 | 10.3% |
| 8 (8.0-8.9) | 11 | 7.6% |
| 9 (9.0-10.0) | 5 | 3.4% |

Mean 4.47, stddev 2.03. 9 of 10 buckets used. Max bucket 20.7% (bucket 4). Not perfectly uniform but no catastrophic compression. Healthy for a system with 101 dismissed actions.

### Scoring factors completeness (last 24h actions)

Of 30 new actions created in last 24h:
- 7/30 (23%) have full scoring factors (bucket_impact, time_sensitivity, conviction_change_potential, effort_vs_impact, action_novelty)
- 21/30 (70%) have enrichment flag
- 0/30 have IRGI scores
- 30/30 have strategic_score, user_priority_score, and score_confidence

**IRGI scores are NOT being populated for new actions.** This is a regression or gap — IRGI was present on 115 older actions but zero new ones. The IRGI function exists (avg 0.582, range 0.398-0.893) but is not being called during action creation.

---

## 2. THESIS QUALITY — 7.5/10

### Thread health

| Thread | Conviction | Status | Days stale | Counter-evidence | Bias flags |
|--------|-----------|--------|------------|-----------------|------------|
| Healthcare AI Agents | New | Exploring | 0.6 | Yes | Yes |
| Cybersecurity / Pen Testing | Medium | Exploring | 0.6 | Yes | Yes |
| AI-Native Non-Consumption | New | Exploring | 0.6 | **No** | Yes |
| SaaS Death / Agentic Replacement | High | Exploring | 0.6 | Yes | Yes |
| Agentic AI Infrastructure | Very High | Active | 0.6 | Yes | Yes |
| Agent-Friendly Codebase | Medium | Exploring | 5.4 | Yes | Yes |
| CLAW Stack Standardization | Medium | Exploring | 5.4 | Yes | Yes |
| USTOL / Aviation | Low | Exploring | 15.7 | Yes | Yes |

8 threads total, 100% have embeddings, 100% have key questions, 100% have conviction set.
7/8 have counter-evidence. 1 has zero counter-evidence (AI-Native Non-Consumption).

### Bias analysis

| Thread | Severity | Issue |
|--------|----------|-------|
| AI-Native Non-Consumption Markets | **CRITICAL** | Zero counter-evidence, for:against = infinity |
| Agentic AI Infrastructure | HIGH | 5.75:1 for:against ratio (23:4) |
| Cybersecurity / Pen Testing | HIGH | 11:1 for:against ratio (11:1) |
| SaaS Death / Agentic Replacement | OK | 1.5:1 (12:8) — well balanced |
| Healthcare AI Agents | OK | 2.33:1 (7:3) |

**Action needed:** AI-Native Non-Consumption needs counter-evidence research. Cybersecurity needs counter-evidence collection (11:1 is extreme for Medium conviction).

### Staleness

- Average days since update: 3.7
- USTOL/Aviation thread at 15.7 days — approaching stale but Low conviction so acceptable
- 5 threads updated within last day (healthy)

---

## 3. CONTENT PIPELINE — 3.0/10

| Metric | Value | Assessment |
|--------|-------|------------|
| Total digests | 22 | Low overall volume |
| Last digest | 128.2 hours ago | **CRITICAL: 5+ days stale** |
| Last 24h | 0 | No new content |
| Last 3 days | 0 | No new content |
| Embedding coverage | 100% (22/22) | Perfect |
| Unique channels | 15 | Good diversity |
| Status | All "published" | No stuck items |

**Root cause:** Content pipeline on droplet has been offline since March 16. This is a known issue from the checkpoint ("Content pipeline restart — stale 5+ days — but not a blocker per user"). The pipeline infrastructure exists but is not running.

**Impact:** No new content means no new thesis evidence, no new action generation from content, and no digest.wiki updates. The scoring model and thesis tracker are running on stale inputs.

---

## 4. DATA COMPLETENESS — 8.0/10

### Network DB (3,513 contacts)

| Field | Count | Coverage |
|-------|-------|----------|
| Embedding | 3,508 | 99.9% |
| Name | 3,513 | 100% |
| Role | 3,364 | 95.8% |
| LinkedIn | 3,090 | 87.9% |
| Email | 1,079 | 30.7% |
| Last interaction | 35 | 1.0% |
| Active 30d | 0 | 0% |

**Embedding recovery complete** — was 23.3% earlier today, now 99.9%. Autonomous cron processor worked.

**Gaps:** `last_interaction` is nearly empty (35/3513 = 1%). `interaction_count_30d` is zero across the board. This means Cindy has no interaction timeline to work with. M12 Data Enrichment needs to backfill interaction data.

### Companies DB (4,567 companies)

| Field | Count | Coverage |
|-------|-------|----------|
| Embedding | 4,545 | 99.5% |
| Sector | 4,567 | 100% |
| Deal status | 4,564 | 99.9% |
| Pipeline status | 4,561 | 99.9% |
| Page content | 4,567 | 100% |
| Website | 762 | 16.7% |
| Agent IDS notes | 16 | 0.4% |
| Research file | 21 | 0.5% |

**Structural completeness excellent** (sector, deal status, pipeline status). **Intelligence completeness poor** — only 16 companies (0.4%) have agent-generated IDS notes. Only 21 have research files. This means the AI CoS has almost no original intelligence on 99.5% of companies.

### Portfolio DB (142 companies)

| Field | Count | Coverage |
|-------|-------|----------|
| Embedding | 142 | 100% |
| High impact | 142 | 100% |
| Key questions | 142 | 100% |
| Health | 141 | 99.3% |
| Research file | 142 | 100% |
| Page content | 142 | 100% |
| Thesis connection | 92 | 64.8% |

**Portfolio is the best-enriched entity.** 100% on all critical fields. Thesis connection at 64.8% — 50 portfolio companies have no thesis linkage. This is expected (not every portfolio company maps to an active thesis thread).

### Staleness monitor

| Entity | Total | Avg staleness (days) | Stale 30d | Stale 90d |
|--------|-------|---------------------|-----------|-----------|
| action | 115 | 1.3 | 0 | 0 |
| interaction | 45 | 0.7 | 0 | 0 |
| network | 3,528 | 0.5 | 0 | 0 |
| company | 4,571 | 0.5 | 0 | 0 |
| thesis | 8 | 0.4 | 0 | 0 |
| portfolio | 142 | 0.0 | 0 | 0 |

**Zero stale entities across all types.** CIR system is keeping everything fresh. This is the best staleness reading ever recorded.

---

## 5. ENTITY CONNECTIONS — 5.5/10

23,716 total connections across 18 types and 6 source types.

### Connection type breakdown

| Type | Count | Avg strength | Single-evidence % |
|------|-------|-------------|-------------------|
| vector_similar | 10,655 | 0.778 | 100% |
| sector_peer | 3,093 | 0.354 | 100% |
| current_employee | 3,067 | 0.912 | 100% |
| past_employee | 2,950 | 0.671 | 100% |
| thesis_relevance | 1,500 | 0.569 | 100% |
| inferred_via_company | 1,471 | 0.598 | 100% |
| led_by | 261 | 0.950 | 100% |
| similar_embedding | 231 | 0.897 | 100% |
| portfolio_investment | 142 | 0.864 | 100% |
| action_references | 122 | 0.846 | 100% |
| interaction_linked | 19 | 0.918 | 42.1% |

**Critical issue: 100% single-evidence across almost all connection types.** Only `interaction_linked` (19 connections) has multi-evidence support (57.9% have >1 evidence point). This means the connection graph is broad but shallow. No connection has been corroborated by multiple independent signals, making confidence levels unreliable.

**vector_similar dominates** at 45% of all connections (10,655). These are cosine similarity matches — the weakest connection type. The graph is noise-dominated by embedding distance rather than actual relationship evidence.

**Positive:** Structural connections (current_employee, past_employee, led_by) have appropriate high strength values. The schema supports multi-evidence but it's not being exercised.

---

## 6. OBLIGATIONS — 6.0/10

16 total obligations tracked. First audit of this dimension.

### Status breakdown

| Status | Count | Past due |
|--------|-------|----------|
| overdue | 6 | 6 |
| pending | 5 | 0 |
| fulfilled | 2 | 2 |
| escalated | 3 | 2 |

### Ayush Sharma bug (user feedback #18)

User reported seeing "Ayush thrice" with "two of those tasks pretty much the same." Verified:

1. **Escalated (due Mar 10):** "Set up WhatsApp group or email introduction for Schneider Electric connection"
2. **Overdue (due Mar 13):** "Provide investor endorsement to Siddharth at Schneider Electric Ventures for AuraML"
3. **Overdue (due Mar 20):** "Connect AuraML with 5 potential investors in robotics/AI space"

Items 1 and 2 are indeed near-duplicates — both relate to making a Schneider Electric introduction for AuraML. Item 3 is broader (5 investors, not just Schneider). The user is correct: items 1 and 2 should be merged. This is a Cindy deduplication gap.

### Other obligation issues

- **Abhishek Anita / Intract** (priority 0.30, escalated, due Mar 1): User feedback #19 says "Intract in my portfolio isn't a priority company." The obligation system correctly has low priority (0.30) but the WebFront is surfacing it as "urgent" — a display layer bug, not a data bug.
- 6 obligations overdue with no evidence of follow-up actions being generated. The obligation-to-action pipeline exists (obligation_action_links table) but is sparse.

---

## 7. ACTIONS QUEUE — 6.5/10

### Overview

| Metric | Value |
|--------|-------|
| Total actions | 145 |
| Proposed (awaiting triage) | 25 |
| Accepted | 8 |
| Dismissed | 101 (90 scored) |
| Expired | 11 |
| Last 24h new | 30 |
| Last 7d new | 45 |
| Hours since last | 0.4 |

**Action generation is active** — 30 new actions in 24 hours. The system is producing.

### Proposed actions quality (25 pending triage)

| Type | Count | Avg score | Avg user_priority |
|------|-------|-----------|-------------------|
| Pipeline/Deals | 2 | 9.61 | 8.20 |
| Portfolio/Support | 4 | 8.84 | 6.95 |
| Portfolio | 1 | 8.81 | 4.37 |
| Meeting | 4 | 7.60 | 4.35 |
| Pipeline | 3 | 7.48 | 3.51 |
| Research | 4 | 7.40 | 5.14 |
| Pipeline Action | 2 | 7.35 | 6.87 |
| Meeting/Outreach | 1 | 6.75 | 8.23 |
| Thesis Update | 1 | 6.60 | 3.98 |
| Portfolio Check-in | 1 | 7.30 | 7.85 |
| Network/Relationships | 1 | 5.28 | 3.56 |
| follow_up | 1 | 6.00 | 3.44 |

Top action: "Make investment decision on Cultured Computers ($150-300K at $30M cap)" — score 10.00, user_priority 8.70. This is appropriately ranked.

### Action type taxonomy issue

12 distinct action types for 25 proposed actions. Types are inconsistent: "Pipeline" vs "Pipeline/Deals" vs "Pipeline Action", "Meeting" vs "Meeting/Outreach", "Portfolio" vs "Portfolio/Support" vs "Portfolio Check-in". This taxonomy fragmentation will hurt scoring and analytics. Should be normalized to 5-6 canonical types.

---

## 8. INFRASTRUCTURE — 8.0/10

### Cron jobs (25 active)

| Health | Count | Jobs |
|--------|-------|------|
| HEALTHY | 10 | cir-connection-decay, cir-log-retention, cir-preemptive-refresh, cir-cron-health-check, daily_depth_grade_refresh, cir-self-heal-weekly, cleanup-embedding-jobs, pool_cleanup, daily-strategic-briefing, strategic_recalibration |
| GOOD | 4 | process-embeddings (93.9%), cir-queue-processor (94.5%), cir-heartbeat (98.9%), cir-action-entity-map-refresh (98.2%) |
| DEGRADED | 3 | cir-matview-refresh (89.6%), cir-staleness-check (87.5%), cir-proactive-staleness-refresh (75%) |
| FAILING | 2 | normalize-scores (66.7%), daily_strategic_assessment (0%) |

**All failures are "connection failed" errors** — transient pool exhaustion, not logic bugs. The pool_cleanup cron (100% success rate) is mitigating this.

### CIR health dashboard

| Metric | Value |
|--------|-------|
| Queue pending | 0 |
| Total processed | 39,046 |
| Dead letters | 0 |
| Tracked entities | 8,421 |
| Total connections | 23,716 |
| Errors 24h | 7 |
| Batches last hour | 9 |
| Avg connection strength | 0.706 |
| Active rules | 10 |
| Active cron jobs | 24 |
| Orphaned companies | 217 |
| Orphaned network | 3 |

Queue is clear (0 pending). 7 errors in 24h is acceptable. 217 orphaned companies — entities not connected to anything — should be investigated by M12.

### Embedding status

All entity types at 99.5-100% embedding coverage. The embedding processor cron (every 2 min) is healthy at 93.9% success rate.

---

## USER FEEDBACK AUDIT

20 feedback entries in `user_feedback_store`. 7 system-generated, 13 user-submitted.

### Unprocessed user feedback

| ID | Page | Type | Feedback | Processed by |
|----|------|------|----------|-------------|
| 16 | system | comment | Embedding milestone (100%) | [] |
| 10 | /test | General | Constraint fix test | [] |
| 2 | system | rate_quality | Intelligence quality 3-4/10 | [] |
| 3 | system | flag_wrong | Page content is tweet not intelligence | [] |
| 4 | system | flag_wrong | Connections noise-dominated | [] |
| 5 | system | rate_quality | Score compression (stddev 1.42) | [] |
| 6 | system | comment | Embedding recovery progress | [] |
| 7 | system | flag_wrong | Embedding processor failures | [] |

8 entries with empty `processed_by` arrays. System-generated entries (#2-7) were baseline measurements — arguably don't need processing. But #16 (embedding milestone) should be acknowledged.

### Processed feedback with active issues

| ID | Issue | Status |
|----|-------|--------|
| #20 | Quivly is portfolio, poor reasoning | Processed by M10 |
| #19 | Intract urgency wrong | Processed by M1, M8 |
| #18 | Ayush duplicate obligations | Processed by M1, M8 — **not fixed** |
| #17 | Rajat card click does nothing | Processed by M1, M8 |
| #15 | Deep research button broken | Processed by M4, M1, M12 |
| #14 | Founder name click broken | Processed by M4, M1, M12 |
| #13 | Founder name opens network page | Processed by M4, M1, M12 |
| #12 | Ownership number wrong | Processed by M4, M1, M12 |
| #11 | Portfolio health prep buttons useless | Processed by M1, M7, M5 |

Multiple bugs marked as "processed" but the underlying data issues persist. Feedback #18 (Ayush duplicates) is still present in the obligations table. Processing means routed to machines, not necessarily fixed.

---

## CRITICAL ISSUES (must address)

1. **Content pipeline offline** (128+ hours) — no new intelligence flowing into the system
2. **IRGI scores not populating on new actions** — 0/30 last-24h actions have IRGI scores
3. **Ayush obligation deduplication** — 3 entries, 2 near-duplicates, user reported as bug
4. **51% scoring misclassification** — 46/90 dismissed actions score >= min accepted threshold
5. **Entity connections 100% single-evidence** — graph breadth without depth makes it unreliable
6. **Action type taxonomy fragmented** — 12+ types where 5-6 canonical types would suffice
7. **AI-Native Non-Consumption thesis: zero counter-evidence** — critical bias flag

## WHAT WOULD PUSH 6.9 TO 8.0?

1. **Restart content pipeline** (+0.5) — currently the biggest drag on system quality
2. **Fix IRGI score population for new actions** (+0.2) — scoring completeness regression
3. **Merge Ayush obligations + dedup logic** (+0.1) — user-reported bug, trust issue
4. **Add counter-evidence to AI-Native Non-Consumption thesis** (+0.1) — intellectual rigor
5. **Connection evidence accumulation** (+0.2) — multi-evidence connections would transform graph quality
6. **Action type normalization** (+0.1) — 12 types to 5-6 canonical types
7. **Backfill interaction data on network** (+0.3) — 1% last_interaction coverage kills Cindy's utility

**Total theoretical uplift: +1.5 to 8.4/10**

---

*Audit complete. Next audit: continue perpetual loop, verify content pipeline restart, IRGI score regression, and obligation dedup fix.*
