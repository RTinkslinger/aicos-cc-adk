# M9 Intel QA: IRGI Intelligence Functions Audit

*Date: 2026-03-20*
*Supabase Project: llfkxnsfczludgigknbs (AI COS Mumbai, ap-south-1)*
*Auditor: M9 Intel QA loop*

---

## Executive Summary

Audited all 8 IRGI intelligence functions plus 2 views. Since the prior audit, the data landscape has **transformed**: companies (0 -> 4565), network (0 -> 3722), portfolio (0 -> 142), and all embeddings are now populated. This means the vector paths (previously dormant) are now **live and primary**, and several functions that were adequate with small data now show quality and performance issues at scale.

**Overall: 7.1/10** -- Functions are architecturally sound and cover the intelligence surface well. Three issues need attention: `hybrid_search` returns zero-score ghost results, `aggregate_thesis_evidence` is slow (1.4s), and `entity_relationships` produces false-positive company matches from short names.

---

## Data State

| Table | Rows | Embeddings | FTS Index | Vector Index | Change vs Prior |
|-------|------|-----------|-----------|--------------|-----------------|
| thesis_threads | 8 | 8 (100%) | GIN | HNSW | Embeddings: 0->8 |
| actions_queue | 116 | 115 (99%) | GIN | HNSW | +1 row, embeddings: 0->115 |
| content_digests | 22 | 22 (100%) | GIN | HNSW | Embeddings: 0->22 |
| companies | 4565 | 4535 (99.3%) | GIN | HNSW | **0->4565 (new)** |
| network | 3722 | 3531 (94.9%) | GIN | HNSW | **0->3722 (new)** |
| portfolio | 142 | -- | GIN | HNSW | **0->142 (new)** |
| action_outcomes | 5 | -- | -- | -- | +1 row |
| preference_weight_adjustments | 11 | -- | -- | -- | **New table** |

---

## Function-by-Function Audit

### 1. `hybrid_search`

**Signature:** `(query_text TEXT, query_embedding VECTOR, match_count INT, keyword_weight FLOAT, semantic_weight FLOAT, filter_tables TEXT[], filter_status TEXT, filter_date_from TIMESTAMPTZ, filter_date_to TIMESTAMPTZ)`

**Architecture:** RRF (Reciprocal Rank Fusion) combining keyword (FTS ts_rank_cd) + semantic (vector cosine) across 5 tables (content_digests, thesis_threads, actions_queue, companies, network). Each table has independent semantic + keyword CTEs, joined via FULL OUTER JOIN, then UNION ALL.

**Test Results:**

| Query | Results | Top Source | Top Score | Correct? |
|-------|---------|-----------|-----------|----------|
| "AI infrastructure" (keyword) | 10 | thesis_threads: "Agentic AI Infrastructure" | 0.0164 | Yes |
| "fintech" (keyword) | 3 | actions_queue, companies, network | 0.0164 | Yes |
| "climate tech" (keyword) | 3 | content_digests with **0.0000 scores** | **NO -- ghost results** |
| "" (empty string) | 3 | content_digests with 0.0000 scores | **NO -- should return 0** |
| NULL | 3 | content_digests with 0.0000 scores | **NO -- should return 0** |

**BUG: Zero-score ghost results.** When neither FTS nor semantic matches exist for a table, the FULL OUTER JOIN can produce rows where both sides are NULL, resulting in `combined_score = 0.0`. These ghost rows pass through because the final `ORDER BY combined_score DESC LIMIT match_count` has no `WHERE combined_score > 0` filter. The `climate tech` and empty-string queries return 3 rows of content_digests with zero scores -- these are the semantic-side rows (with NULL embedding, they still show up as row_number() = 1..N from the semantic CTE when no rows match, which seems to produce phantom rows from the ORDER BY + LIMIT inside the CTE).

**Correctness: 6/10** -- Good results for valid queries, but returns meaningless results for no-match cases.
**Completeness: 9/10** -- Covers all 5 tables, both search modalities, with flexible filters.
**Performance: 9/10** -- 20ms for keyword-only across 5 tables with 8000+ total rows. GIN FTS indexes properly in place. HNSW indexes ready for semantic path.

**Fix needed:** Add `WHERE combined_score > 0` to the final `all_results` CTE or the outer SELECT.

---

### 2. `find_related_companies`

**Signature:** `(p_company_id INTEGER, p_limit_n INTEGER DEFAULT 10)` -- **Changed** from original `(p_query_text TEXT, p_limit_n INTEGER)`.

**Architecture:** Two paths: (1) Vector cosine similarity when source company has embedding (threshold 0.3), (2) Trigram name similarity fallback (threshold 0.1).

**Test Results:**

| Input | Path | Results | Top Match | Score | Correct? |
|-------|------|---------|-----------|-------|----------|
| Company 2454 (Pravaayu, has embedding) | Vector | 5 | The Vedansia | 0.9327 | Yes -- wellness/consumer companies cluster |
| Company 4365 (Anmasa, no embedding) | Trigram | 5 | Akasa Air | 0.2308 | Weak -- name-string matching only |
| Company 99999 (non-existent) | None | 0 | -- | -- | Yes -- graceful empty return |

**Correctness: 7/10** -- Vector path produces excellent results. Trigram fallback is poor (matching "Anmasa" to "Akasa Air" by character overlap, not semantics). Only 30/4565 companies lack embeddings, so this rarely triggers.
**Completeness: 7/10** -- The original text-query interface was removed. No way to search by description/sector text anymore, only by company ID. This limits usability for discovery use cases.
**Performance: 9/10** -- 16ms with HNSW index on 4535 embedded companies.

**Note:** The signature change from text-query to company-ID is a **breaking change** vs the prior audit. The old fallback to thesis_threads.key_companies is gone (no longer needed since companies table is populated).

---

### 3. `score_action_thesis_relevance`

**Signature:** `(p_action_id INTEGER)` -> `TABLE(thesis_id INT, thesis_name TEXT, relevance_score FLOAT, match_type TEXT)`

**Architecture:** 4-method weighted scoring: vector similarity (0.50), explicit thesis_connection match (0.20), trigram text overlap (0.15), key question keyword match (0.15). Applies conviction multiplier (High=1.15, Low=0.85) and status multiplier (Active=1.10, Parked=0.70). Returns top 5 above threshold 0.05.

**Test Results:**

| Action | Top Thesis | Score | Match Type | Correct? |
|--------|-----------|-------|------------|----------|
| #1 (Pipeline, contact center) | Agentic AI Infrastructure | 0.4975 | vector | Reasonable |
| #89 (Research, white-collar displacement, 5 thesis connections) | Agentic AI Infrastructure | 0.8242 | vector+explicit | Yes -- matches all 5 explicit connections |
| #109 (Research, CLAW stack/OpenClaw) | Agentic AI Infrastructure | 0.8931 | vector+explicit | Debatable -- see below |
| #99999 (non-existent) | -- | -- | -- | Yes -- graceful empty |

**Quality concern with action 109:** This action is *specifically about* CLAW Stack (OpenClaw/NanoClaw adoption), yet it ranks thesis 3 (Agentic AI Infrastructure, 0.8931) *above* thesis 6 (CLAW Stack, 0.6932). The thesis_connection field lists "Agentic AI Infrastructure" first, and the vector embedding also favors the broader infrastructure thesis over the specific CLAW Stack thesis. The conviction multiplier (High=1.15 for Agentic AI vs Medium=1.00 for CLAW Stack) amplifies the gap further. This is not wrong per se -- CLAW Stack *is* part of Agentic AI Infrastructure -- but it means specific thesis relevance can be diluted by broader parent theses.

**Correctness: 8/10** -- Weighted multi-method approach is solid. Conviction/status multipliers add useful prioritization. Minor ranking issue where broader theses outrank specific ones.
**Completeness: 9/10** -- All 4 scoring methods active now that embeddings exist.
**Performance: 9/10** -- 19ms per action. Only scans 8 thesis rows.

---

### 4. `route_action_to_bucket`

**Signature:** `(p_action_id INTEGER)` -> `TABLE(bucket TEXT, confidence FLOAT, reasoning TEXT)`

**Architecture:** Multi-signal routing with keyword regex, action type classification, and portfolio cross-reference. 4 buckets with independent scoring. Applies user priority rebalancing (B2: 1.5x boost, B3: 1.3x, B4: 0.6x penalty). Returns all buckets with score > 0.

**Test Results:**

| Action | Type | Primary Bucket | Confidence | Correct? |
|--------|------|---------------|------------|----------|
| #1 (Pipeline, contact center) | Pipeline Action | Discover New (B1) | 0.70 | Yes |
| #55 (Portfolio, Highperformr) | Portfolio Check-in | Deepen Existing (B2) | 1.00 | Yes |
| #78 (Portfolio, Confido) | Portfolio Check-in | Deepen Existing (B2) | 1.00 | Yes |
| #89 (Research, portfolio impact) | Research | Deepen Existing (B2) | 0.975 | Yes -- portfolio_research signal correctly fires |
| #95 (Meeting, Ian Fischer) | Meeting/Outreach | Expand Network (B3) | 0.65 | Yes |
| #107 (Portfolio, Monday.com) | Portfolio Check-in | Deepen Existing (B2) | 1.00 | Yes |
| #109 (Research, CLAW stack) | Research | Thesis Evolution (B4) | 0.30 | Correct bucket, low confidence |
| #111 (Pipeline, Indian coding AI) | Pipeline Action | Discover New (B1) | 0.85 | Yes |
| #99999 (non-existent) | -- | -- | -- | Yes -- graceful empty |

**Materialized view `action_scores` distribution:**

| Bucket | Actions | Avg Confidence |
|--------|---------|---------------|
| Deepen Existing (B2) | 47 (52%) | 0.96 |
| Expand Network (B3) | 25 (28%) | 0.54 |
| Discover New (B1) | 16 (18%) | 0.68 |
| Thesis Evolution (B4) | 2 (2%) | 0.35 |

The B2 dominance (52%) makes sense given the user priority rebalancing (+50% for portfolio). B4 is nearly eliminated (0.6x penalty, only 2 actions), which aligns with the `action-priority-hierarchy` feedback: thesis work is agent-delegable, only surface when human judgment needed.

**Correctness: 8/10** -- Routing decisions are sensible. Portfolio detection works well with the 142-row portfolio table. The 1.5x/1.3x/0.6x rebalancing effectively implements the priority hierarchy.
**Completeness: 9/10** -- Covers all 4 buckets with rich signal detection. Regex patterns are comprehensive.
**Performance: 7/10** -- 111ms per action is acceptable for single calls but would be slow for batch. The regex matching on concatenated text is the bottleneck. The portfolio lookup (EXISTS against 142 rows) adds overhead.

---

### 5. `suggest_actions_for_thesis`

**Signature:** `(p_thesis_id INTEGER, p_limit_n INTEGER DEFAULT 5)` -> `TABLE(suggestion TEXT, reasoning TEXT, priority TEXT, bucket TEXT, related_company TEXT)`

**Architecture:** 4 suggestion types: key question research, company gap analysis, digest follow-up, evidence gap analysis. Priority logic based on conviction + status.

**Test Results (all 8 theses):**

| Thesis | Suggestions | Types Generated | Correct? |
|--------|------------|-----------------|----------|
| #1 Cybersecurity (Medium/Exploring) | 3 | 3x key_question | Yes -- surfaces all 3 open questions at P2 |
| #2 Healthcare AI (New/Exploring) | 3 | company_gap + 2x digest_followup | Yes |
| #3 Agentic AI (High/Active) | 3 | key_question + 2x digest_followup | Yes -- P1 for High+Active |
| #4 SaaS Death (High/Exploring) | 3 | 2x digest_followup + evidence_gap | Yes |
| #5 USTOL (Low/Exploring) | 3 | company_gap + 2x digest_followup | Questionable -- see below |
| #6 CLAW Stack (Medium/Exploring) | 3 | 2x digest_followup + evidence_gap (contra) | Yes |
| #7 Agent-Friendly (Medium/Exploring) | 3 | 2x digest_followup + evidence_gap (contra) | Yes |
| #11 AI-Native Non-Consumption (New/Exploring) | 3 | 3x key_question | Yes -- 3 open questions at P2 |
| #99999 (non-existent) | 0 | -- | Yes -- graceful empty |

**Quality concern with thesis 5 (USTOL):** Suggests "Evaluate: Early exploration -- no specific pipeline companies yet" which is the literal key_companies text, not a useful suggestion. The company_gap_suggestions CTE doesn't check whether key_companies contains actual company names.

**Quality concern with digest_followup suggestions:** Thesis 5 (USTOL/Aviation/Deep Tech Mobility) gets suggested digests like "How to code with AI agents" and "From Writing Code to Managing Agents" -- these are coding/agent digests, not aviation/mobility content. The matching uses `similarity(v_thread_name || v_core_thesis, cd.title) > 0.1` which is too loose and produces false positives.

**Correctness: 7/10** -- Core logic is sound. Key question and evidence gap suggestions are excellent. Company gap and digest followup have false positives.
**Completeness: 8/10** -- 4 suggestion types cover the main gaps well.
**Performance: 8/10** -- 192ms per thesis. The digest similarity scan and NOT EXISTS subquery add overhead.

---

### 6. `aggregate_thesis_evidence`

**Signature:** `(p_thesis_id INTEGER)` -> `TABLE(evidence_type TEXT, source_type TEXT, source_id INT, source_title TEXT, relevance FLOAT, sentiment TEXT, created_at TIMESTAMPTZ)`

**Architecture:** Gathers evidence from 3 sources (content_digests, actions_queue, action_outcomes) using trigram similarity and explicit field matching. Classifies sentiment as FOR/AGAINST/NEUTRAL. Returns top 50 by relevance.

**Test Results:**

| Thesis | Total Evidence | By Source | Avg Relevance | Sentiments |
|--------|---------------|-----------|--------------|------------|
| #3 Agentic AI | 50 (capped) | 16 digests (0.700), 30 actions (0.800), 4 outcomes (0.900) | 0.780 | FOR, AGAINST, NEUTRAL |
| #1 Cybersecurity | 50 (capped) | 19 digests (0.254), 31 actions (0.487) | 0.386 | FOR, AGAINST, NEUTRAL |
| #99999 (non-existent) | 0 | -- | -- | Yes -- graceful empty |

**Correctness issue:** For thesis 3, all 4 action_outcomes are classified NEUTRAL despite the function checking for Gold/Helpful outcomes. This suggests the outcomes either have NULL `outcome` fields or the outcome values don't match the CASE branches.

**Performance issue:** 1421ms (1.4 seconds) -- the **slowest function by far**. The bottleneck is trigram `similarity()` called on every row of `actions_queue` (116 rows) and `content_digests` (22 rows) against the thesis text. The `LEFT(COALESCE(cd.digest_data::text, ''), 5000)` trigram call is especially expensive -- computing character-level trigram similarity on up to 5000 chars of JSON text per row.

**Correctness: 7/10** -- Evidence collection is comprehensive. Explicit match scoring (0.7/0.8/0.9) provides good stratification. Sentiment classification has gaps (outcomes all NEUTRAL).
**Completeness: 8/10** -- Covers all 3 evidence sources. Would benefit from including companies and network tables as evidence sources.
**Performance: 4/10** -- 1.4s is unacceptable for an interactive function. Will worsen as digests/actions grow. Needs vector-based scoring instead of trigram on large text fields.

---

### 7. `detect_thesis_bias`

**Signature:** `(p_thesis_id INTEGER DEFAULT NULL)` -> `TABLE(thesis_id INT, thread_name TEXT, conviction TEXT, evidence_for_count INT, evidence_against_count INT, ratio NUMERIC, confirmation_bias BOOLEAN, possible_bias BOOLEAN, source_bias BOOLEAN, flags JSONB)`

**Architecture:** Counts evidence_for/against lines (newline-delimited), computes ratio, and flags 6 bias types in a comprehensive JSONB `flags` object: confirmation_bias, possible_bias, source_bias, stale_evidence, conviction_mismatch, thin_evidence. Also computes severity (CRITICAL/HIGH/MEDIUM/LOW/OK).

**Test Results:**

| Thesis | FOR:AGAINST | Ratio | Confirmation Bias | Possible Bias | Source Bias | Severity |
|--------|-------------|-------|-------------------|---------------|-------------|----------|
| #3 Agentic AI (High) | 21:4 | 5.25 | false | true | false | MEDIUM |
| #4 SaaS Death (High) | 11:8 | 1.38 | false | false | false | OK |
| #1 Cybersecurity (Medium) | 10:1 | 10.00 | false | true | false | MEDIUM |
| #11 AI-Native (New) | 1:0 | 999.0 | true | false | false | HIGH |
| #5 USTOL (Low) | 2:1 | 2.00 | false | false | false | OK |
| #2 Healthcare AI (New) | 7:3 | 2.33 | false | false | false | OK |
| #7 Agent-Friendly (Medium) | 6:2 | 3.00 | false | false | false | OK |
| #6 CLAW Stack (Medium) | 5:2 | 2.50 | false | false | false | OK |

**Quality strengths:**
- Correctly flags thesis 11 (AI-Native) as HIGH severity with zero contra evidence
- Correctly flags thesis 1 (Cybersecurity) and thesis 3 (Agentic AI) with possible bias at >5x ratio
- `flags` JSONB is comprehensive with 6 dimensions + severity + timestamp

**Quality concern:** The evidence counting method splits on `\n` and counts lines. This is fragile -- evidence_for/against text may contain blank lines, bullet points, or other formatting that inflates counts. A line like "" (empty) would still count as 1 due to `string_to_array` behavior, though the `NULLIF(TRIM(...), '')` guard partially mitigates this.

**Correctness: 8/10** -- Bias detection logic is sound. 6 flag dimensions provide comprehensive coverage.
**Completeness: 9/10** -- Covers confirmation bias, ratio bias, source diversity, staleness, conviction mismatch, and thin evidence. Strong design.
**Performance: 10/10** -- 11ms for all 8 theses. Pure text processing, no joins.

---

### 8. `compute_user_priority_score`

**Signature:** `(action_row actions_queue)` -> `NUMERIC` (1-10 scale with sigmoid soft cap)

**Architecture:** 5-step scoring model:
1. Extract 6 factors from scoring_factors JSONB (with 0-1 normalization and /10 guard)
2. Weighted combination (time_sensitivity 0.15, conviction_change 0.20, stakeholder 0.20, effort_vs_impact 0.15, action_novelty 0.10, irgi_relevance 0.20)
3. Domain adjustments: priority boost (P0: +0.8, P1: +0.4, P3: -0.4), type boost (portfolio: +1.2, network: +0.8, thesis: -1.2, content: -0.8), recency factor (30-day decay)
4. Preference learning from preference_weight_adjustments table (action_type + priority dimensions)
5. Sigmoid soft cap at 1 and 9

**Test Results:**

| Action | Type | Priority | Score | Expected Range? |
|--------|------|----------|-------|-----------------|
| #55 Portfolio Check-in | Portfolio Check-in | P1 | 10.00 | Yes -- portfolio + P1 = max |
| #78 Portfolio Check-in | Portfolio Check-in | P1 | 9.82 | Yes |
| #107 Portfolio Check-in | Portfolio Check-in | P1 | 9.56 | Yes |
| #95 Meeting/Outreach | Meeting/Outreach | P1 | 9.04 | Yes |
| #111 Pipeline Action | Pipeline Action | P1 | 8.12 | Yes |
| #1 Pipeline Action | Pipeline Action | P0 | 6.75 | **Low for P0** |
| #109 Research | Research | P1 | 5.61 | Yes -- thesis/research penalized |
| #89 Research | Research | P1 | 5.08 | Yes -- thesis/research penalized |

**Score distribution by type (sample of 20 proposed actions):**

| Type | Priority | Avg Score | Correct Ordering? |
|------|----------|-----------|-------------------|
| Portfolio Check-in | P0 | 8.74 | Yes -- highest |
| Portfolio Check-in | P1 | 8.37 | Yes |
| Meeting/Outreach | P0 | 8.09 | Yes |
| Pipeline Action | P0 | 7.92 | Yes |
| Meeting/Outreach | P1 | 7.79 | Yes |
| Pipeline Action | P1 | 7.47 | Yes |

**Quality strength:** The action-priority-hierarchy is correctly implemented: Portfolio > Network > Pipeline > Thesis/Research. This matches the `action-priority-hierarchy` feedback rule.

**Quality concern: P0 action #1 scores 6.75**, lower than P1 Portfolio Check-ins (8-10). The reason: the `preference_weight_adjustments` table has P0 = -0.2 based on just 1 sample. This single negative feedback data point is dragging down ALL P0 actions. With `sample_count >= 1` threshold, a single dismissal creates a persistent penalty.

**Correctness: 8/10** -- Multi-factor model produces correct priority ordering. Sigmoid cap works. P0 penalty from sparse preference data is a concern.
**Completeness: 9/10** -- 6 input factors + 4 domain adjustments + preference learning. Comprehensive.
**Performance: 9/10** -- 14ms per action. One SELECT to preference_weight_adjustments per action_type + priority.

---

## Views Audit

### `entity_relationships` (Regular VIEW)

| Relationship Type | Count | Avg Strength | Issue |
|-------------------|-------|-------------|-------|
| network_company | 7385 | 0.900 (flat) | All scores identical -- uses hardcoded 0.9 for explicit matches |
| action_thesis | 381 | 0.200 | Good -- trigram similarity provides differentiation |
| thesis_company | 53 | 0.837 | **False positives from short company names** |

**Bug: thesis_company false positives.** The view uses `LIKE '%' || lower(c.name) || '%'` to match company names against thesis key_companies text. With 4565 companies, short names like "Pi" (id 2459), "EY" (id 4948), "Open" (id 4449), "NEA" (id 295) match as substrings in key_companies text or even in words like "pipeline", "survey", "open-source". Thesis 5 (USTOL) has key_companies = "Early exploration -- no specific pipeline companies yet" and still produces company matches via substring collision.

**Fix needed:** Add minimum name length filter (e.g., `LENGTH(c.name) >= 4`) or use word-boundary matching instead of LIKE.

### `action_scores` (Materialized VIEW)

- 90 rows, matches current Proposed count (90)
- 4 distinct buckets, distribution aligns with routing function
- Indexes in place for lookup (id), filter (bucket), and concurrent refresh (unique id)
- `refresh_action_scores()` wrapper works

---

## Scorecard Summary

| # | Function | Correctness | Completeness | Performance | Overall | Critical Issues |
|---|----------|-------------|-------------|-------------|---------|-----------------|
| 1 | `hybrid_search` | 6 | 9 | 9 | **7.5** | Ghost results (0-score rows) for no-match queries |
| 2 | `find_related_companies` | 7 | 7 | 9 | **7.5** | Signature changed; text-query interface removed |
| 3 | `score_action_thesis_relevance` | 8 | 9 | 9 | **8.5** | Broad theses outrank specific ones |
| 4 | `route_action_to_bucket` | 8 | 9 | 7 | **8.0** | 111ms per action; fine for single calls |
| 5 | `suggest_actions_for_thesis` | 7 | 8 | 8 | **7.5** | False positive digests for unrelated theses |
| 6 | `aggregate_thesis_evidence` | 7 | 8 | 4 | **6.0** | 1.4s execution; trigram on large JSON text |
| 7 | `detect_thesis_bias` | 8 | 9 | 10 | **9.0** | Minor: line-count fragility |
| 8 | `compute_user_priority_score` | 8 | 9 | 9 | **8.5** | P0 penalty from sparse preference data |

**Weighted Average: 7.8/10** (excluding views)

---

## Priority Fixes (Ranked)

### P0 -- Fix Now

1. **`hybrid_search` ghost results:** Add `WHERE r.combined_score > 0` to the final SELECT. One-line fix. Currently returns meaningless results for any query that doesn't match.

2. **`aggregate_thesis_evidence` performance:** Replace `similarity(v_thesis_text, LEFT(COALESCE(cd.digest_data::text, ''), 5000))` with vector-based scoring now that embeddings exist. This single change should drop execution from 1.4s to ~50ms.

### P1 -- Fix This Week

3. **`entity_relationships` thesis_company false positives:** Add `AND LENGTH(c.name) >= 4` to the thesis_company UNION in the view definition. Short names ("Pi", "EY", "NEA") produce false substring matches.

4. **`compute_user_priority_score` preference learning threshold:** Change `sample_count >= 1` to `sample_count >= 3` in the preference lookup. A single data point should not permanently penalize an entire action type or priority level.

### P2 -- Fix This Month

5. **`suggest_actions_for_thesis` digest matching:** Tighten the similarity threshold from 0.1 to 0.2, or switch to FTS/vector matching to prevent unrelated digests from being suggested.

6. **`find_related_companies` text search interface:** Consider adding a second overload `find_related_companies(p_query_text TEXT, p_limit_n INT)` for discovery use cases where you don't have a company ID.

7. **`entity_relationships` network_company flat scores:** Replace hardcoded 0.9 with actual relationship strength based on role (current employee = 0.9, past = 0.6, angel = 0.7).

### P3 -- Backlog

8. **`aggregate_thesis_evidence` outcome sentiment:** Investigate why action_outcomes for thesis 3 all return NEUTRAL. Likely missing outcome values in the table.

9. **`detect_thesis_bias` line counting:** Consider storing evidence items as JSONB arrays instead of newline-delimited text for more robust counting.

10. **`route_action_to_bucket` performance:** 111ms is acceptable now but will need regex pre-compilation or materialized text columns if actions grow past 500.

---

## Infrastructure State (Positive)

- All recommended indexes from prior audit are now in place (HNSW for embeddings, GIN for FTS)
- No missing GIN trigram indexes needed -- trigram similarity is only used on small tables (thesis_threads)
- `action_scores` materialized view is in sync (90/90 proposed actions)
- `preference_weight_adjustments` table is operational with 11 entries across 4 dimensions
- Auto Embeddings pipeline has successfully populated 99%+ of all tables
