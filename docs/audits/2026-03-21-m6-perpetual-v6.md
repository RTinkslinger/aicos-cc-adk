# M6 IRGI Perpetual Loop v6 — 2026-03-21

## Session Summary

IRGI system at 8.8/10. All 36 functions passing. This loop focused on: (1) critical bug fixes, (2) search surface expansion, (3) edge case testing, (4) gap analysis for 8.8 → 9.5.

## Critical Bugs Found & Fixed

### BUG 1: `irgi_interaction_thesis_crossref` — Thesis status filter too restrictive (FIXED)

**Problem:** Function filtered `WHERE t.status = 'Active'` but 7/8 theses have status `Exploring`. Only "Agentic AI Infrastructure" was `Active`. Result: crossref was matching interactions to only 1 thesis instead of all 8.

**Impact:** 87.5% of thesis threads completely invisible to interaction crossref. The system was blind to cybersecurity, healthcare, SaaS death, and other thesis signals in meeting notes.

**Fix:** Changed filter to `WHERE t.status IN ('Active', 'Exploring')`.

**Before:** 1 thesis matched (17 total results, all Agentic AI Infrastructure)
**After:** 7 theses matched (30 results across AI-Native Non-Consumption Markets, Cybersecurity, Agentic AI Infra, Healthcare AI, Agent-Friendly Codebase, SaaS Death, CLAW Stack)

### BUG 2: `hybrid_search` / `balanced_search` — Missing 2 searchable surfaces (FIXED)

**Problem:** Both `interactions` (23 rows) and `portfolio` (142 rows) tables have full FTS + embedding infrastructure but were excluded from hybrid_search. Searches could never return meeting notes or portfolio company data directly.

**Impact:** Agents searching for "meeting notes about cybersecurity" or "portfolio company health" would never find interactions or portfolio entries. These surfaces were invisible to all search-based intelligence functions.

**Fix:** Added `interactions` and `portfolio` CTEs to `hybrid_search`, added `min_interactions` and `min_portfolio` parameters to `balanced_search` (defaults: 1 each), updated `enriched_balanced_search` to enrich new surfaces with context, updated `agent_search_context` to handle interactions/portfolio in `why_it_matters`, `portfolio_connection`, `recent_signals`, `interaction_recency`, and `agent_action_hint` columns.

**Before:** 5 searchable surfaces (companies, network, thesis_threads, actions_queue, content_digests)
**After:** 7 searchable surfaces (+interactions, +portfolio)

**Search result for "cybersecurity meeting notes":**
- interactions: 6 results (avg 0.734)
- portfolio: 1 result (0.767)
- thesis_threads: 2, companies: 3, network: 2, content_digests: 1, actions_queue: 5

## Functions Updated

| Function | Change | Breaking? |
|----------|--------|-----------|
| `irgi_interaction_thesis_crossref` | Status filter `Active` → `Active + Exploring` | No |
| `hybrid_search` | Added interactions + portfolio surfaces | No |
| `balanced_search` | New params: `min_interactions`, `min_portfolio` (with defaults) | Old signature dropped |
| `enriched_balanced_search` | Handles interactions + portfolio context | Old signature dropped |
| `agent_search_context` | Handles interactions + portfolio in all enrichment columns | No |

**Note:** Old `balanced_search` and `enriched_balanced_search` signatures (without min_interactions/min_portfolio) were dropped. All callers use defaults, so no breakage expected.

## Edge Case Testing — balanced_search

| Test | Result | Notes |
|------|--------|-------|
| Standard query ("AI infrastructure") | PASS | 15 results across 5 surfaces, scores 0.6-1.0 |
| Single word ("cybersecurity") | PASS | 20 results, 4 surfaces |
| Person name ("Varun Vummidi") | PASS | Returns network matches by name similarity |
| Nonsense query ("xyzzy12345nonexistent") | WARN | Returns 20 companies (noise). Not a crash but low signal |
| Long natural language query | PASS | 20 results, all 5 surfaces represented |
| SQL injection characters | PASS | Safe, no execution |
| Special characters ("C++ & Rust") | PASS | Returns results, no crash |
| Empty string | PASS | Returns 0 results (correct) |
| Status filter | PASS | Correctly filters by status |
| Date range filter | PASS | Correctly filters by date |

## Benchmark Results — All 36 PASS

| Function | Latency (ms) | Rows |
|----------|-------------|------|
| hybrid_search(kw) | 112 | 10 |
| balanced_search | 158 | 15 |
| agent_search_context | 130 | 15 |
| interaction_thesis_xref | 73 | **30** (was 17) |
| find_related_companies | 21 | 10 |
| find_related_entities | 9 | 10 |
| aggregate_thesis_evidence | 38 | 60 |
| enriched_search | 90 | 20 |
| find_active_deals | 110 | 18 |
| thesis_landscape | 52 | 8 |
| search_across_surfaces | 54 | 10 |
| All others | <30ms | Various |

**Average latency:** 29ms (healthy)

## Embedding Status — 100% Coverage

All 7 entity types at 100% embedding coverage:
- companies: 4,579/4,579
- network: 3,535/3,535 (was 3,528 at start of session, 7 processed during)
- portfolio: 142/142
- thesis_threads: 8/8
- actions_queue: 144/144
- content_digests: 22/22
- interactions: 23/23

Embedding pipeline: Cron running every 2 min, 1,460 items/hour capacity. Queue drained.

## ENIAC Research Queue — 9 Items

| Priority | Type | Entity | Urgency | Issue |
|----------|------|--------|---------|-------|
| 1 | thesis_key_question | Agentic AI Infrastructure | LOW | 1 open KQ (MCP security) |
| 2 | thesis_contra_research | AI-Native Non-Consumption Markets | HIGH | 999:1 evidence ratio — 0 contra |
| 3 | thesis_contra_research | Agentic AI Infrastructure | MEDIUM | 5.75:1 ratio |
| 4 | thesis_contra_research | Cybersecurity / Pen Testing | MEDIUM | 11:1 ratio |
| 5 | deal_intelligence_gap | E2B | HIGH | 0 chars intel, Tracking |
| 6 | deal_intelligence_gap | Sierra AI | HIGH | 0 chars intel, Active |
| 7 | deal_intelligence_gap | Poetic | HIGH | 0 chars intel, Active |
| 8 | deal_intelligence_gap | ChefKart | HIGH | 77 chars intel |
| 9 | deal_intelligence_gap | WeldT | HIGH | 79 chars intel |

**Note on evidence ratios:** The `eniac_research_queue` uses character length of `evidence_for`/`evidence_against` text fields as a proxy ratio. The `detect_thesis_bias` function uses actual structured evidence counts. The 999:1 for AI-Native Non-Consumption Markets reflects truly empty `evidence_against` field (0 characters), while aggregate_thesis_evidence shows 10 AGAINST signals from dismissed actions. Gap: the text fields don't reflect the automated evidence aggregation.

## 8.8 → 9.5 Gap Analysis

### What IRGI Does Well (8.8 level)
- 36 functions, all passing, sub-200ms latencies
- 7-surface hybrid search with balanced allocation
- Thesis bias detection with structured flags
- Cross-entity intelligence (relationships, mentions, timelines)
- ENIAC research toolkit (brief, queue, save findings)
- Interaction-thesis crossref (now fixed to 7/8 theses)
- Embedding health monitoring + auto-recovery

### What's Needed for 9.5

| Gap | Impact | Effort | Description |
|-----|--------|--------|-------------|
| **Text-based person search** | HIGH | S | `find_similar_network` takes person_id only. No way to search by text query like "who works on cybersecurity in Bay Area". Need `search_network(text)` function. |
| **Evidence ratio sync** | MEDIUM | S | `evidence_for`/`evidence_against` text fields on thesis_threads don't reflect automated evidence from `aggregate_thesis_evidence`. Need a sync function or change the ratio source. |
| **Nonsense query handling** | LOW | S | Queries with no semantic match still return results (20 companies). Could add a confidence indicator or minimum score threshold. |
| **Cross-surface entity resolution** | HIGH | M | When searching, results from different surfaces about the same entity aren't grouped. E.g., a company appearing in companies, portfolio, interactions, and actions as separate results. |
| **Interaction volume** | MEDIUM | External | Only 23 interactions limits the scoring formula (component 4 capped by interactions/50). More Granola meetings → higher score automatically. |
| **Portfolio key question search** | MEDIUM | S | 386 portfolio_key_questions with embeddings but not searchable via hybrid_search. Could add as 8th surface. |
| **Temporal decay in search** | MEDIUM | M | balanced_search doesn't boost recent results. A meeting from yesterday should rank higher than one from 3 months ago for the same similarity score. |

### Score Ceiling

The IRGI score formula is data-limited at component 4 (interactions + obligations + connections). With current data volumes:
- 23 interactions → 0.32/0.7 possible
- 14 obligations → 0.08/0.6 possible
- 23,741 connections → 0.55/0.7 possible

**Max achievable with current data: ~9.0**. To hit 9.5, the system needs either more data volume or formula recalibration to reward capability breadth rather than just data volume.

## Data Counts

| Entity | Count |
|--------|-------|
| Companies | 4,579 |
| Network | 3,535 |
| Portfolio | 142 |
| Thesis Threads | 8 |
| Actions Queue | 144 |
| Content Digests | 22 |
| Interactions | 23 |
| Entity Connections | 23,741 |
| Obligations | 14 |

## Next Loop Priorities

1. **Text-based network search function** — highest impact gap, small effort
2. **Evidence ratio source fix** — make thesis bias detection use aggregate_thesis_evidence counts instead of character lengths
3. **Temporal decay in balanced_search** — recent results should rank higher
4. **Portfolio key questions as 8th search surface** — 386 questions with embeddings, ready to wire
5. **Score formula recalibration** — reward function breadth + search surface count, not just data volume
