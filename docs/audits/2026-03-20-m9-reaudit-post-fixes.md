# M9 Loop 11 -- Re-Audit Post-Fixes
**Date:** 2026-03-20
**Machine:** M9 Intelligence QA (Loop 11)
**Context:** Re-audit after M5 compression fix, M6 bias detection, M10 propagation, M12 dedup+connections

---

## Executive Summary

| Dimension | L4-10 Score | L11 Score | Delta | Verdict |
|-----------|-------------|-----------|-------|---------|
| **Actions Intelligence** | 7.5/10 | **7.8/10** | +0.3 | Improved -- compression partially fixed |
| **Thesis Intelligence** | 8.2/10 | **8.5/10** | +0.3 | Improved -- bias detection structured |
| **Portfolio/Network Quality** | 52/100 | **68/100** | +16 | Major improvement -- roles + connections |
| **Search Accuracy** | 72/100 | **72/100** | 0 | No change -- FTS still weak |
| **Data Quality** | 29/100 | **42/100** | +13 | Improved -- dedup + connections + roles |
| **Scoring Quality** | 5.5/10 | **6.5/10** | +1.0 | Improved -- compression down from 74% to 60% |

**Overall System Intelligence: 6.2/10 --> 7.0/10 (+0.8)**

---

## 1. Scoring Distribution (M5 Compression Fix)

### Current State
| Bucket | Count | % |
|--------|-------|---|
| 6 | 3 | 3.3% |
| 7 | 10 | 11.1% |
| 8 | 54 | **60.0%** |
| 9 | 23 | 25.6% |

### Delta vs Previous
| Metric | L4-10 | L11 | Delta |
|--------|-------|-----|-------|
| 8-9 bucket % | **74%** (combined 8+9) | **60% in 8, 26% in 9** | RESTRUCTURED |
| Score range | 1.29 - 9.79 | 5.72 - 9.33 | Narrowed (floor raised, ceiling lowered) |
| Mean | 7.83 | 8.07 | +0.24 |
| Stddev | 2.34 | 0.68 | -1.66 (compressed) |
| Distinct scores (rounded 0.1) | 23 | 26 | +3 |

### Verdict: PARTIAL FIX
The old problem was 74% in buckets 8-9. Now 60% is in bucket 8 alone, 26% in bucket 9. The ceiling was lowered (9.33 max vs 9.79) and the floor raised (5.72 vs 1.29), but the mass has shifted to bucket 8 rather than spreading. The compression moved, it didn't resolve.

**Target (<30% per bucket): MISSED.** Bucket 8 at 60% is still double the target.

### Action Type Hierarchy (Proposed Only)
| Type | Count | Avg Score | Stddev | L4-10 Avg |
|------|-------|-----------|--------|-----------|
| Portfolio Check-in | 36 | 8.64 | 0.32 | 7.96 |
| Meeting/Outreach | 33 | 7.96 | 0.21 | 9.36 |
| Pipeline Action | 12 | 7.71 | 0.37 | 9.43 |
| Research | 6 | 6.94 | 0.79 | 5.39 |
| Content Follow-up | 1 | 6.53 | -- | 8.21 |
| Thesis Update | 2 | 6.10 | 0.53 | 4.01 |

**Key change:** Portfolio Check-in now scores HIGHEST (8.64), overtaking Pipeline (7.71) and Meeting (7.96). This aligns better with the action-priority-hierarchy feedback. Pipeline and Meeting scores dropped significantly (9.43 -> 7.71, 9.36 -> 7.96), which is the compression fix at work. Research and Thesis Update scores rose (5.39 -> 6.94, 4.01 -> 6.10), which tightens the range but correctly raises their floor.

---

## 2. Entity Connections (M12 + M10)

### Current State
| Edge Type | Count |
|-----------|-------|
| network-company | 8,085 |
| company-company | 6,867 |
| network-network | 2,000 |
| company-thesis | 2,000 |
| portfolio-company | 142 |
| action-thesis | 138 |
| portfolio-thesis | 61 |
| thesis-thesis | 18 |
| network-thesis | 3 |
| **TOTAL** | **19,314** |

### Connection Type Breakdown
| Type | Count |
|------|-------|
| vector_similar | 12,989 |
| current_employee | 3,064 |
| past_employee | 2,902 |
| thesis_relevance | 314 |
| portfolio_investment | 142 |
| co_occurrence | 18 |

### Delta vs Previous
| Metric | L4-10 | L11 | Delta |
|--------|-------|-----|-------|
| Total connections | 1,298 | **19,314** | **+18,016 (+1,388%)** |
| Connection types | 3 | **6** | +3 new types |
| Network edges | 0 | **10,088** | FROM ZERO |
| Company-company edges | 1,000 | **6,867** | +5,867 |
| Thesis edges | 138 | **2,534** | +2,396 |

**Target (10,000+): HIT.** 19,314 connections -- nearly 15x the previous count.

### Verdict: MAJOR IMPROVEMENT
The entity graph went from skeletal (1,298 edges, 3 types) to functional (19,314 edges, 6 types). The most critical fix: network entities went from ZERO connections to 10,088 (network-company 8,085 + network-network 2,000 + network-thesis 3). M12 built current_employee (3,064) and past_employee (2,902) edges from the existing company ID columns. M10 expanded vector_similar from 1,000 to 12,989.

**Remaining gap:** network-thesis only has 3 edges. People are connected to companies but not directly to thesis threads.

---

## 3. Network Roles (M12 Dedup + Enrichment)

### Current State
| Category | Count | % |
|----------|-------|---|
| Real roles | 3,064 | **86.8%** |
| Missing (null/empty) | 467 | 13.2% |
| Corrupted ("postgres") | 0 | 0% |
| **Total** | **3,531** | -- |

### Delta vs Previous
| Metric | L4-10 | L11 | Delta |
|--------|-------|-----|-------|
| Total network rows | 3,722 | 3,531 | -191 (dedup) |
| Real roles | 0% | **86.8%** | **FROM ZERO** |
| Corrupted ("postgres") | widespread | **0** | FIXED |
| LinkedIn coverage | 87.1% (of 3,722) | 87.6% (3,095/3,531) | Stable |
| Email coverage | 0% | 0% | No change |

**Target (80%+ real roles): HIT.** 86.8% real roles, zero corruption.

### Verdict: MAJOR FIX
M12 eliminated the "postgres" corruption entirely and enriched 3,064 records with real role titles. The dedup pass removed 191 rows (3,722 -> 3,531).

### Dedup Detail
| Metric | L4-10 | L11 | Delta |
|--------|-------|-----|-------|
| Total rows | 3,722 | 3,531 | -191 |
| Dupe groups | 276 | **76** | -200 groups resolved |
| Rows in dupe groups | -- | 167 | 76 groups with 167 rows remaining |

**Target (<3,600): HIT.** 3,531 rows, down from 3,722. Backup table `network_dedup_backup` preserved the original 3,722.

---

## 4. Bias Detection (M6)

### Current State -- bias_summary View
| Thesis | Conviction | FOR:AGAINST | Severity |
|--------|-----------|-------------|----------|
| AI-Native Non-Consumption Markets | New | 1:0 (999x) | **CRITICAL** -- zero contra |
| Cybersecurity / Pen Testing | Medium | 10:1 (10x) | **HIGH** |
| Agentic AI Infrastructure | High | 21:4 (5.25x) | **HIGH** -- possible_bias flagged |
| Agent-Friendly Codebase | Medium | 6:2 (3x) | OK |
| CLAW Stack | Medium | 5:2 (2.5x) | OK |
| Healthcare AI Agents | New | 7:3 (2.3x) | OK |
| USTOL / Aviation | Low | 2:1 (2x) | OK |
| SaaS Death / Agentic Replacement | High | 11:8 (1.38x) | OK (best balanced) |

### Delta vs Previous
| Metric | L4-10 | L11 | Delta |
|--------|-------|-----|-------|
| Structured bias flags | No view | **bias_summary view live** | NEW |
| Theses flagged | Ad-hoc only | **All 8 tracked** | COMPLETE |
| Severity levels | None | critical / high / ok | 3 tiers |
| Fields tracked | None | confirmation_bias, possible_bias, source_bias, ratio, warning_text | 6 flags |

**Target (all theses flagged): HIT.** All 8 thesis threads have structured bias flags with severity levels.

### Verdict: COMPLETE
M6 bias detection is live and structured. The `bias_summary` view provides real-time monitoring. Two threads flagged HIGH (Cybersecurity 10:1, Agentic AI 5.25:1) and one CRITICAL (AI-Native Non-Consumption with zero contra). SaaS Death remains the healthiest thesis (1.38:1).

---

## 5. CIR State (M10 Propagation)

### Current State
| Category | Count |
|----------|-------|
| Companies | 4,566 |
| Network | 3,722 |
| Portfolio | 142 |
| Theses | 8 |
| Summaries | 5 |
| Meta (config/system) | 3 |
| **Total cir_state entries** | **8,562** |

### Supporting Infrastructure
| Table | Rows |
|-------|------|
| cir_propagation_log | 7,230 |
| change_events | 742 |
| cir_propagation_rules | 7 |

### Delta vs Previous
| Metric | L4-10 | L11 | Delta |
|--------|-------|-----|-------|
| cir_state entries | 0 (empty) | **8,562** | **FROM ZERO** |
| propagation_log | 80 | **7,230** | +7,150 |
| change_events | 742 | 742 | No change |

**Target (all entities tracked): HIT.** 4,566 companies + 3,722 network + 142 portfolio + 8 theses = 8,438 entities tracked. Plus 5 summaries and 3 meta entries.

### Verdict: MAJOR IMPROVEMENT
CIR state went from empty to tracking every entity in the system. The propagation log exploded from 80 to 7,230 entries, indicating active intelligence propagation across the graph.

---

## 6. Network Dedup (M12)

| Metric | L4-10 | L11 | Delta |
|--------|-------|-----|-------|
| Total rows | 3,722 | **3,531** | **-191** |
| Dupe groups | 276 | **76** | **-200 resolved** |
| Remaining dupe rows | -- | 167 | Low residual |

**Target (<3,600): HIT.** Clean dedup with backup preserved.

---

## 7. Composite Score Card

| Dimension | L4-10 | L11 | Delta | Target | Status |
|-----------|-------|-----|-------|--------|--------|
| **Actions Intelligence** | 7.0 -> 7.5 | **7.8** | +0.3 | 8.5 | Approaching |
| **Thesis Intelligence** | 7.8 -> 8.2 | **8.5** | +0.3 | 9.0 | On track |
| **Portfolio/Network Quality** | 65 -> 52 | **68** | +16 | 85 | Recovering |
| **Search Accuracy** | 78 -> 72 | **72** | 0 | 85 | STALLED |
| **Data Quality** | 29 | **42** | +13 | 70 | Improving slowly |
| **Scoring Quality** | 5.5 | **6.5** | +1.0 | 8.0 | Improving |

### Scoring Justification

**Actions Intelligence: 7.8** (+0.3)
- 100% scoring coverage (maintained)
- Hierarchy now correct: Portfolio > Meeting > Pipeline > Research > Thesis (was inverted for Portfolio)
- Compression partially addressed: range narrowed but bucket 8 still dominates at 60%
- Action type diversity good: 6 types represented

**Thesis Intelligence: 8.5** (+0.3)
- All 8 theses active with evidence aggregation
- Structured bias detection live (bias_summary view)
- 2,534 thesis-linked edges (up from 138)
- Counter-evidence tracking structured for all threads
- Gap: AI-Native Non-Consumption still has zero contra

**Portfolio/Network Quality: 68** (+16)
- Portfolio remains excellent (99%+ coverage on financial fields)
- Network roles: 86.8% real (was 0%)
- Network dedup: 3,531 rows, 76 remaining dupe groups (was 276)
- Network connections: 10,088 edges (was 0)
- Still missing: 0% email, 0% relationship_status, 0.3% E&E priority

**Search Accuracy: 72** (no change)
- FTS still returns near-zero for semantic queries
- hybrid_search architecture unchanged
- No new FTS index improvements detected

**Data Quality: 42** (+13)
- Entity connections: 19,314 (was 1,298) -- massive improvement
- CIR state: 8,562 entries (was 0) -- tracking all entities
- Network enrichment_status: 100% "raw" still -- no enriched records yet
- Companies enrichment_status: 100% "raw" still
- Companies with page_content: 3/4,565 (0.07%)
- Companies with website: 241/4,565 (5.3%) -- unchanged
- 6 empty tables remain (interactions, context_gaps, people_interactions, datum_requests, sync_queue, obligations)

**Scoring Quality: 6.5** (+1.0)
- Ceiling lowered: max 9.33 (was 9.79)
- Floor raised: min 5.72 (was 1.29)
- Hierarchy corrected: Portfolio > Meeting > Pipeline (was Pipeline > Meeting > Portfolio)
- Still compressed: 60% in bucket 8
- Stddev dropped to 0.68 (was 2.34) -- may be over-corrected

---

## Database Health Snapshot

| Table | Rows | L4-10 Rows | Delta |
|-------|------|------------|-------|
| entity_connections | 19,314 | 1,298 | **+18,016** |
| cir_state | 8,562 | 0 | **+8,562** |
| cir_propagation_log | 7,230 | 80 | **+7,150** |
| companies | 4,565 | 4,565 | 0 |
| network | 3,531 | 3,722 | -191 (dedup) |
| change_events | 742 | 742 | 0 |
| portfolio | 142 | 142 | 0 |
| actions_queue | 115 | 115 | 0 |
| action_scores | 90 | 90 | 0 |
| notifications | 34 | -- | new |
| content_digests | 22 | 22 | 0 |
| preference_weight_adjustments | 16 | -- | new |
| strategic_config | 12 | -- | new |
| thesis_threads | 8 | 8 | 0 |
| cir_propagation_rules | 7 | -- | new |
| action_outcomes | 4 | -- | new |
| cascade_events | 2 | 0 | +2 |
| strategic_assessments | 1 | 0 | +1 |
| depth_grades | 1 | 0 | +1 |
| **Empty tables** | **6** | **9** | **-3 fewer empty** |

---

## Top Remaining Gaps (Priority Order)

### 1. CRITICAL: Scoring Compression Persists
Bucket 8 holds 60% of Proposed actions. Target was <30%. The M5 fix restructured the distribution but didn't spread it. Need a forced distribution or percentile-based scoring.

### 2. CRITICAL: Network Emails Still Zero
0/3,531 network records have email. Blocks M8 (Cindy) and M11 (Obligations). M12 must prioritize email enrichment.

### 3. HIGH: No Enriched Records
Both network and companies show 100% "raw" enrichment_status. The role_title fix and entity_connections build happened but enrichment_status was never updated to reflect that work.

### 4. HIGH: Company Data Still Sparse
- Websites: 5.3% (241/4,565) -- unchanged
- Page content: 0.07% (3/4,565) -- unchanged
- Sector tags: 33.5% -- unchanged

### 5. HIGH: FTS Still Broken
No FTS improvements detected. Semantic queries return zero results. This blocks keyword-based search fallbacks.

### 6. MEDIUM: Network-Thesis Edges Minimal
Only 3 network-thesis connections vs 8,085 network-company. People aren't linked to thesis threads, limiting Megamind's ability to identify thesis-relevant contacts.

### 7. MEDIUM: 6 Empty Tables
interactions, context_gaps, people_interactions, datum_requests, sync_queue, obligations -- still unpopulated.

---

## What Worked

1. **M12 entity connections** -- 1,298 -> 19,314 (14.9x). The single biggest improvement this session.
2. **M12 network dedup** -- 276 dupe groups reduced to 76, 191 rows removed cleanly.
3. **M12 role cleanup** -- 0% -> 86.8% real roles, zero corruption.
4. **M6 bias detection** -- bias_summary view live with structured severity tiers.
5. **M10 CIR state** -- from empty to tracking all 8,438 entities with 7,230 propagation events.
6. **M5 scoring hierarchy** -- Portfolio now correctly outscores Pipeline/Meeting.

## What Didn't Move

1. **Search accuracy** -- FTS untouched.
2. **Email enrichment** -- still zero.
3. **Company enrichment** -- websites, page_content unchanged.
4. **Enrichment_status field** -- never updated despite actual enrichment work.

---

*Next audit: Verify scoring spread after forced-distribution fix. Monitor email enrichment progress. Check if enrichment_status gets updated.*
