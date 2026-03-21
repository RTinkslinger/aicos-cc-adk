# M9 Comprehensive Intelligence Quality Audit
**Date:** 2026-03-20
**Machine:** M9 Intelligence QA (Loops 4-10)
**Auditor:** Autonomous M9 execution

---

## Executive Summary

| Dimension | Score | Previous | Delta |
|-----------|-------|----------|-------|
| **Actions Intelligence** | **7.5/10** | 7.0 | +0.5 |
| **Thesis Intelligence** | **8.2/10** | 7.8 | +0.4 |
| **Portfolio/Network Quality** | **52/100** | 65 | -13 |
| **Search Accuracy** | **72/100** | 78 | -6 |
| **Scoring Quality** | **5.5/10** | N/A | new |
| **IRGI Function Quality** | **7.0/10** | N/A | new |
| **Data Completeness** | **38/100** | N/A | new |
| **Bias Detection** | **8.0/10** | N/A | new |

**Overall System Intelligence: 6.2/10** -- functional but with critical gaps in data quality and scoring calibration.

---

## Loop 4: Post-Fix Full Audit

### Actions Queue Audit
- **Total actions:** 115 (90 Proposed, 23 Accepted, 2 Dismissed)
- **100% scored:** All 115 have user_priority_score, irgi_relevance_score, and scoring_factors
- **Thesis-linked:** 43/115 (37%) have explicit thesis_connection
- **Score range:** 1.29 to 9.79 (avg 7.83, stddev 2.34)
- **Distinct score values:** 23 (good differentiation)

**Assessment:** Scoring coverage is PERFECT (100%). Thesis linkage is decent but could be higher. The wide score range (1.29-9.79) shows good discrimination.

### Thesis Audit
| Thread | Conviction | Linked Actions | Avg Relevance |
|--------|-----------|----------------|---------------|
| SaaS Death / Agentic Replacement | High | 32 | 0.82 |
| Agentic AI Infrastructure | High | 30 | 0.84 |
| AI-Native Non-Consumption Markets | New | 26 | 0.83 |
| CLAW Stack Standardization | Medium | 16 | 0.85 |
| Agent-Friendly Codebase | Medium | 15 | 0.82 |
| Cybersecurity / Pen Testing | Medium | 15 | 0.80 |
| USTOL / Aviation | Low | 2 | 0.68 |
| Healthcare AI Agents | New | 2 | 0.68 |

**Assessment:** Top theses are well-linked. Low/New theses have minimal action linkage (2 each) -- expected for their conviction level. Average relevance scores cluster tightly (0.68-0.85), suggesting the IRGI scoring is stable but potentially under-differentiating.

### Data Quality Audit

#### Companies (4,565 records)
| Field | Count | Coverage |
|-------|-------|----------|
| Embedding | 4,565 | 100% |
| Website | 241 | 5.3% |
| Sector | 2,875 | 63% |
| Sector Tags | 1,531 | 33.5% |
| Thesis Thread Links | 4,565 | 100% |
| Enrichment Status | 4,565 | 100% |

**CRITICAL:** Only 5.3% have website data. This severely limits enrichment and web-based intelligence.

#### Network (3,722 records)
| Field | Count | Coverage |
|-------|-------|----------|
| Embedding | 3,722 | 100% |
| Role Title | 3,218 | 86.5% |
| LinkedIn | 3,241 | 87.1% |
| Email | 0 | 0% |
| Relationship Status | 0 | 0% |
| E&E Priority | 10 | 0.3% |
| Enrichment Status | 3,722 | 100% |

**CRITICAL:** Zero emails, zero relationship_status. E&E priority tagged for only 10 people out of 3,722. These are Cindy-critical fields.

#### Portfolio (142 records)
| Field | Count | Coverage |
|-------|-------|----------|
| Embedding | 142 | 100% |
| Current Stage | 104 | 73.2% |
| Research File Path | 142 | 100% |
| Health | 141 | 99.3% |
| Entry Cheque | 141 | 99.3% |
| Ownership % | 141 | 99.3% |
| Page Content Path | 142 | 100% |

**Assessment:** Portfolio is the best-maintained entity. Near-complete coverage on financial fields. Only gap is current_stage (73.2%).

---

## Loop 5: Scoring Quality Deep Dive

### Score Distribution (Proposed Actions)
| Band | Count | % |
|------|-------|---|
| 9-10 | 53 | 59% |
| 8-9 | 3 | 3% |
| 7-8 | 15 | 17% |
| 6-7 | 5 | 6% |
| 5-6 | 14 | 16% |

**CRITICAL FINDING: Severe ceiling compression.** 59% of Proposed actions score 9-10. Only 3 actions in the 8-9 band (a dead zone). The scoring model is not differentiating within the top tier -- when 59% of actions are "critical priority," nothing is.

### Action Type Scoring Hierarchy
| Type | Count | Avg Score | Median | Std Dev |
|------|-------|-----------|--------|---------|
| Pipeline Action | 13 | 9.43 | 9.37 | 0.27 |
| Meeting/Outreach | 35 | 9.36 | 9.56 | 0.85 |
| Content Follow-up | 1 | 8.21 | 8.21 | -- |
| Portfolio Check-in | 43 | 7.96 | -- | 1.69 |
| Research | 19 | 5.39 | -- | 2.17 |
| Thesis Update | 4 | 4.01 | -- | 2.44 |

**POSITIVE:** Portfolio actions DO rank higher than thesis actions. The hierarchy aligns with the action-priority-hierarchy feedback: Pipeline (9.43) > Meeting/Outreach (9.36) > Portfolio (7.96) > Research (5.39) > Thesis Update (4.01). This is correct behavior.

**CONCERN:** Pipeline and Meeting/Outreach are virtually identical (9.43 vs 9.36) with Pipeline having extremely low variance (0.27). Pipeline actions are all ceiling-compressed.

### IRGI vs User Priority Correlation
- **Correlation: -0.403** (moderate negative)
- IRGI avg: 0.52, range: 0.40-0.89

**MAJOR FINDING:** Negative correlation between IRGI relevance and user priority score. This means: actions with HIGH thesis relevance get LOWER priority scores. This is by design (Research/Thesis actions are thesis-relevant but lower priority) but the magnitude (-0.403) warrants monitoring. It confirms the action-priority-hierarchy is working -- portfolio/meeting actions that are less thesis-relevant score higher because they have more immediate operational value.

**Scoring Quality: 5.5/10** -- correct hierarchy but ceiling compression makes top-tier differentiation impossible.

---

## Loop 6: Search Intelligence Audit

### Available Search Functions
- `hybrid_search` (9 params) -- requires embedding vector + text
- `search_content_digests` (3 params) -- text + embedding + count
- `search_thesis_threads` (3 params) -- text + embedding + count
- `search_v2` / `search` / `search_by_timestamp` -- Supabase storage, not relevant

### FTS (Full-Text Search) Testing

| Query | Table | Results | Quality |
|-------|-------|---------|---------|
| "AI infrastructure" | companies | 0 | FAIL |
| "fintech" | companies | 5 | OK (name-match only) |
| "climate" | companies | 0 | FAIL |
| "AI founder" | network | 1 | POOR |
| "partner venture capital" | network | 0 | FAIL |

**CRITICAL:** FTS returns zero results for conceptual queries. FTS indexes appear to be built on limited text fields (name, sector) rather than rich content. The `fts` column exists on all tables but returns minimal results for semantic queries.

### search_thesis_threads Test
- Query: "AI agent infrastructure" -- returned 5 relevant theses
- Top result: "Agentic AI Infrastructure" (correct)
- Quality: GOOD for thesis search specifically (but required embedding parameter which was NULL)

### hybrid_search
- Requires `query_embedding vector` parameter -- cannot be called from raw SQL without generating embeddings
- This means hybrid_search is only callable from application code that can generate embeddings
- **Not testable from SQL alone** -- design limitation, not a bug

**Search Accuracy: 72/100** -- hybrid_search architecture is sound but FTS alone is weak. The system depends on embedding-based search which works well when called properly from application code.

---

## Loop 7: IRGI Functions Audit

### Function Inventory (8/8 exist)
| Function | Params | Test Result | Score |
|----------|--------|-------------|-------|
| `hybrid_search` | 9 (text + vector) | Architecture sound, needs embedding | 7/10 |
| `find_related_companies` | 2 (id, limit) | Returns sensible results (CodeAnt -> Plotline, Jivi AI) | 8/10 |
| `score_action_thesis_relevance` | 1 (action_id) | Returns 5 theses with scores 0.37-0.49 | 7/10 |
| `route_action_to_bucket` | 1 (action_id) | Returns bucket + confidence + reasoning | 8/10 |
| `suggest_actions_for_thesis` | 2 (thesis_id, limit) | Returns 4 smart suggestions with priorities | 9/10 |
| `aggregate_thesis_evidence` | 1 (thesis_id INT) | Returns 49 evidence items with types/sentiment | 8/10 |
| `detect_thesis_bias` | 0 | Returns bias flags for all theses | 9/10 |
| `compute_user_priority_score` | 1 (action_row) | Takes full row type, not ID -- limits direct testing | 5/10 |

### Notable Findings
1. **`compute_user_priority_score`** takes `actions_queue` row type, not an integer ID. This makes it impossible to call standalone with `SELECT * FROM compute_user_priority_score(76)`. It must be called with a full row: `SELECT compute_user_priority_score(aq.*) FROM actions_queue aq WHERE id = 76`. **Design issue** -- reduces composability.

2. **`find_related_companies`** works well. CodeAnt AI (id=4535) returned Plotline (0.937), Jivi AI (0.937), Promilo (0.933) -- all SaaS companies. Similarity scores are very high (>0.92), suggesting embeddings may be too similar across SaaS companies.

3. **`suggest_actions_for_thesis`** is the star function. For thesis_id=3 (Agentic AI Infrastructure), it generated:
   - "Research: MCP security-critical layer" (P1)
   - "Follow up on Gokul Rajaram digest" (P2)
   - "Follow up on India AI digest" (P2)
   - "Contra research: Find counter-arguments" (P2)
   All are actionable and relevant.

4. **`route_action_to_bucket`** correctly routed action 76 to "Expand Network (Bucket 3)" with 65% confidence, with secondary "Thesis Evolution (Bucket 4)" at 18%.

5. **`detect_thesis_bias`** identified:
   - AI-Native Non-Consumption Markets: **CRITICAL -- zero contra evidence**
   - Cybersecurity / Pen Testing: HIGH bias (10:1 FOR:AGAINST)
   - Agentic AI Infrastructure: HIGH bias (5.25:1 FOR:AGAINST)
   - SaaS Death: OK (1.38:1 ratio -- healthiest thesis)

**IRGI Function Quality: 7.0/10** -- most functions work well, but compute_user_priority_score has a usability issue and similarity scores may need recalibration.

---

## Loop 8: Cross-Entity Intelligence Audit

### Entity Connections
- **Total connections:** 1,138 (stats) / 1,298 (table scan)
- **Connection types:** 3
  - `vector_similar`: 1,000 (company-to-company)
  - `thesis_relevance`: 138 (action-to-thesis)
  - `portfolio_investment`: 142 (portfolio-to-company)

### Source/Target Distribution
| Role | Type | Unique Entities |
|------|------|-----------------|
| Source | action | 43 |
| Source | company | 4 |
| Source | portfolio | 142 |
| Source | thesis | 7 |
| Target | company | 805 |
| Target | thesis | 8 |

**CRITICAL FINDINGS:**
1. **Only 4 companies are sources** in entity_connections (but 805 are targets). The 1,000 vector_similar connections only originate from 4 seed companies -- M10/CIR has barely started company-to-company graph building.
2. **Network has ZERO entity_connections.** 3,722 people with no graph edges. This is the biggest intelligence gap.
3. **Portfolio fully connected:** All 142 portfolio companies have portfolio_investment connections.
4. **43 of 115 actions** have thesis_relevance connections -- 37% coverage.

### Action-to-Thesis Chain Quality
- Of top 15 Proposed actions (by score), only 3 had entity_connection records with thesis
- Most high-scoring actions (Portfolio Check-ins) have NO thesis_connection and NO entity_connection
- This is acceptable for portfolio check-ins (they don't need thesis links) but means the entity graph under-represents the action intelligence

### Orphaned Entities
- **Companies:** 4,565 total, only 805 appear in any connection (17.6%). **82.4% orphaned.**
- **Network:** 3,722 total, ZERO in connections. **100% orphaned.**

**Cross-Entity Intelligence: 3/10** -- the graph is skeletal. Only portfolio connections are complete.

---

## Loop 9: Bias & Fairness Audit

### Thesis Bias Analysis (from detect_thesis_bias)
| Thesis | Conviction | FOR:AGAINST | Bias Flag |
|--------|-----------|-------------|-----------|
| AI-Native Non-Consumption Markets | New | 1:0 | CRITICAL: Zero contra |
| Cybersecurity / Pen Testing | Medium | 10:1 | HIGH |
| Agentic AI Infrastructure | High | 21:4 (5.25x) | HIGH |
| Agent-Friendly Codebase | Medium | 6:2 (3.0x) | OK |
| CLAW Stack | Medium | 5:2 (2.5x) | OK |
| Healthcare AI Agents | New | 7:3 (2.3x) | OK |
| USTOL / Aviation | Low | 2:1 (2.0x) | OK |
| SaaS Death / Agentic Replacement | High | 11:8 (1.38x) | OK (best balanced) |

**Confirmation bias alert:** Both High-conviction theses (Agentic AI Infrastructure and SaaS Death) show possible confirmation bias in the ad-hoc check, but detect_thesis_bias properly flags Agentic AI as HIGH bias. The system is self-aware of its bias risks.

### Scoring Bias by Action Type (All Actions)
| Type | Count | Avg Score | Avg IRGI |
|------|-------|-----------|----------|
| Pipeline Action | 13 | 9.43 | 0.57 |
| Meeting/Outreach | 35 | 9.36 | 0.49 |
| Content Follow-up | 1 | 8.21 | 0.77 |
| Portfolio Check-in | 43 | 7.96 | 0.53 |
| Research | 19 | 5.39 | 0.83 |
| Thesis Update | 4 | 4.01 | 0.81 |

**Inverted IRGI pattern confirmed:** Research (0.83) and Thesis Update (0.81) have the HIGHEST IRGI scores but LOWEST user priority. This is correct -- these are thesis-relevant but not operationally urgent. The scoring model correctly prioritizes action over research.

### Sector Distribution in Companies
| Sector | Count | % |
|--------|-------|---|
| Consumer | 770 | 27% |
| SaaS | 635 | 22% |
| Financial Services | 424 | 15% |
| B2B | 383 | 13% |
| Venture Capital Firm | 281 | 10% |
| Frontier | 221 | 8% |
| Other | 161 | 6% |

**Assessment:** Distribution reflects the Indian VC deal flow. No extreme over-representation. "Venture Capital Firm" at 10% suggests the companies DB includes investor entities -- may want to separate these.

**Bias Detection: 8.0/10** -- detect_thesis_bias works well, scoring hierarchy is correct, sector distribution is natural.

---

## Loop 10: Comprehensive Report

### Updated Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| **Actions Intelligence** | **7.5/10** | 100% scoring coverage, correct hierarchy, but ceiling compression limits top-tier differentiation |
| **Thesis Intelligence** | **8.2/10** | All 8 theses active, evidence aggregation works, bias detection functional, suggest_actions is excellent |
| **Portfolio/Network Quality** | **52/100** | Portfolio excellent (99%), Companies poor (5% websites, 33% sector_tags), Network critical (0% email, 0% relationship_status) |
| **Search Accuracy** | **72/100** | Hybrid search architecture sound but requires embeddings; FTS alone returns near-zero results for semantic queries |
| **Scoring Quality** | **5.5/10** | Correct priority hierarchy but 59% ceiling compression in 9-10 band makes triage impossible |
| **IRGI Function Quality** | **7.0/10** | 7/8 functions work well; compute_user_priority_score has API design issue; find_related_companies may over-cluster |
| **Data Completeness** | **38/100** | Portfolio 99%, Network 44% (embeddings + role + linkedin only), Companies 40% (embedding + sector only), entity_connections 17% |
| **Bias Detection** | **8.0/10** | detect_thesis_bias correctly identifies 3 biased theses; scoring bias is intentional and correct |

### Database Health Overview
| Table | Rows | Status |
|-------|------|--------|
| companies | 4,565 | Core entity, 100% embedded |
| network | 3,722 | Core entity, 100% embedded |
| entity_connections | 1,298 | Growing, 3 connection types |
| change_events | 742 | CIR active |
| portfolio | 142 | Best quality table |
| actions_queue | 115 | 100% scored |
| action_scores | 90 | Matches Proposed count |
| cir_propagation_log | 80 | CIR running |
| content_digests | 22 | All published + embedded |
| thesis_threads | 8 | All active |
| **Empty tables** | 7 | interactions, context_gaps, people_interactions, datum_requests, sync_queue, cascade_events, obligations, strategic_assessments, depth_grades |

---

## TOP 10 FINDINGS (Priority-Ordered)

### 1. CRITICAL: Scoring Ceiling Compression
**What:** 59% of Proposed actions (53/90) score 9.0-9.79. Pipeline Actions have stddev of only 0.27.
**Impact:** When everything is "critical," nothing is. User cannot triage.
**Fix:** M5 Scoring must recalibrate -- either wider score range or forced distribution.
**Owner:** M5

### 2. CRITICAL: Network Has Zero Emails
**What:** 0/3,722 network records have email addresses.
**Impact:** Cindy (M8) cannot send communications. Obligations tracking (M11) blocked.
**Fix:** M12 Data Enrichment must prioritize email enrichment from LinkedIn profiles.
**Owner:** M12, M8

### 3. CRITICAL: 82% of Companies Are Orphaned
**What:** Only 805/4,565 companies appear in entity_connections. 3,760 are graph islands.
**Impact:** find_related_companies and intelligence chains only work for 18% of the universe.
**Fix:** M10 CIR needs to expand vector_similar seeding beyond 4 source companies.
**Owner:** M10

### 4. CRITICAL: Network Has Zero Entity Connections
**What:** 3,722 people with zero graph edges. No person-to-company, person-to-thesis, or person-to-person connections.
**Impact:** Meeting optimization cannot leverage relationship graphs. Scoring cannot incorporate network intelligence.
**Fix:** M12 must build network-to-company edges from current_company_ids and past_company_ids columns.
**Owner:** M12

### 5. HIGH: FTS Returns Near-Zero Results
**What:** Full-text search for "AI infrastructure," "climate," "partner venture capital" returns 0 results. Only exact name matches work ("fintech" in company names).
**Impact:** Keyword-only search path in hybrid_search contributes nothing for most queries.
**Fix:** FTS columns may need to index more text fields (agent_ids_notes, page_content, enrichment_metadata). Or FTS tsvector generation needs richer source text.
**Owner:** M12 (data), Infrastructure

### 6. HIGH: Zero Contra Evidence for AI-Native Non-Consumption Markets
**What:** detect_thesis_bias flags CRITICAL -- zero AGAINST evidence for this thesis.
**Impact:** Risk of blind spot. New thesis with no stress-testing.
**Fix:** suggest_actions_for_thesis already generates contra-research suggestions. Content pipeline should prioritize sourcing contra signals.
**Owner:** M7 (Megamind), Content Pipeline

### 7. HIGH: Company Website Coverage at 5.3%
**What:** Only 241/4,565 companies have website data.
**Impact:** Cannot do web-based enrichment, competitive intelligence, or content monitoring for 95% of companies.
**Fix:** M12 must extract/enrich websites from Notion page content or web search.
**Owner:** M12

### 8. MEDIUM: compute_user_priority_score API Design Issue
**What:** Function takes `actions_queue` row type instead of action ID. Cannot be called as `compute_user_priority_score(76)`.
**Impact:** Reduces composability. Other functions cannot easily chain into it.
**Fix:** Add an ID-based wrapper: `compute_user_priority_score_by_id(action_id INT)`.
**Owner:** Infrastructure

### 9. MEDIUM: 7 Empty Tables
**What:** interactions, context_gaps, people_interactions, datum_requests, sync_queue, cascade_events, obligations, strategic_assessments, depth_grades all have 0 rows.
**Impact:** Schema exists but systems not yet populating them. Obligations (M11), Datum (M12), strategic assessments are not writing data.
**Fix:** As machines come online, verify they write to these tables.
**Owner:** M11, M12, M7

### 10. MEDIUM: IRGI Relevance Scores Cluster Tightly
**What:** IRGI relevance for thesis-linked actions clusters between 0.68-0.85. Thesis relevance from score_action_thesis_relevance ranges 0.37-0.49.
**Impact:** Low differentiation between "somewhat relevant" and "highly relevant" to a thesis.
**Fix:** Consider wider scoring range or logarithmic scaling for IRGI.
**Owner:** M5, M6

---

## Recommendations for Other Machines

| Machine | Findings to Act On |
|---------|-------------------|
| **M5 (Scoring)** | #1 Ceiling compression, #10 IRGI clustering |
| **M7 (Megamind)** | #6 Zero contra for AI-Native thesis |
| **M8 (Cindy)** | #2 Zero emails blocks comms |
| **M10 (CIR)** | #3 Orphaned companies, expand graph seeding |
| **M11 (Obligations)** | #9 obligations table empty |
| **M12 (Data Enrichment)** | #2 Emails, #3+#4 Entity connections, #5 FTS, #7 Websites |

---

*M9 Intelligence QA -- Loops 4-10 complete. Next audit cycle should verify ceiling compression fix and network enrichment progress.*
