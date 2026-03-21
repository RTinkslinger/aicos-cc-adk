# M6 IRGI Perpetual Loop v4 - Cross-Surface Search Bias Fix
**Date:** 2026-03-21 | **Machine:** M6 IRGI | **Loop:** Perpetual v4

## Critical Fix: Cross-Surface Search Bias

### Problem
`hybrid_search('AI agent infrastructure India')` returned **0 companies, 0 network** out of 20 results -- content_digests monopolized with 14/20 slots. `search_across_surfaces` found 19 companies for the same query.

### Root Cause
`ts_rank_cd` doesn't normalize by document length. Content digests have FTS vectors with 5000+ characters (from `digest_data` JSONB), while companies/network have ~100 chars. Result:
- Content digest FTS raw score: **0.087** for "AI agent infrastructure India"
- Companies FTS raw score: **0.020** (4x lower)
- After `term_coverage_boost` multiplication: digests hit **1.78** keyword score vs companies at **0.02** (90x gap)

This made `hybrid_search` -> `enriched_search` -> `agent_search_context` all biased toward digests.

### Solution: `balanced_search` Function

Created `balanced_search(query, embedding, limit, ...)` with:
1. **Per-entity-type execution:** Calls `hybrid_search` separately for each of 5 entity types
2. **Within-type normalization:** Min-max normalizes scores to [0,1] within each type, eliminating cross-type score inflation
3. **Reserved minimum slots:** Guarantees minimum representation per type:
   - Companies: 3 (default)
   - Thesis threads: 2
   - Network: 2
   - Actions: 2
   - Content digests: 1
4. **Remaining slots:** Filled by global normalized score (still relevance-ranked)

### Changes Made

| Function | Change | Impact |
|----------|--------|--------|
| `balanced_search` | **NEW** | Core cross-surface search with fairness guarantees |
| `enriched_balanced_search` | **NEW** | balanced_search + rich context snippets |
| `agent_search_context` | **UPDATED** | Now uses `balanced_search` instead of `enriched_search`; passes `normalized_score` as `combined_score` to preserve balanced ordering |
| `irgi_benchmark` | **UPDATED** | Added 4 new functions (31 total benchmarked) |
| `cross_entity_mentions` | **NEW** | Unified mention timeline across all surfaces for any entity |
| `trend_detection` | **NEW** | Temporal trend analysis (accelerating/stable/decelerating) |

### Before/After Distribution

| Query | Surface | hybrid_search | balanced_search |
|-------|---------|:-------------:|:---------------:|
| "AI agent infrastructure India" | content_digests | 14 | 11 |
| | companies | **0** | **3** |
| | network | **0** | **2** |
| | thesis_threads | 2 | 2 |
| | actions_queue | 4 | 2 |
| "cybersecurity enterprise" | thesis_threads | 1 | **4** |
| | network | **0** | **2+** |
| "healthcare voice AI" | network | **0** | **2** |
| | thesis_threads | 1 | **2** |

### Performance

| Function | Latency | Status |
|----------|---------|--------|
| `balanced_search` | 132ms | PASS (<500ms) |
| `agent_search_context` | 119ms | PASS (<500ms) |
| All 29 functions | avg 26.8ms | ALL PASS |

The ~130ms cost is from calling `hybrid_search` 5x (once per entity type, ~80ms each but shared proxy embedding). Acceptable for the fairness guarantee.

## System State

### IRGI Score: 8.9/10 (up from 8.7)
- 31 benchmarked functions, all PASS (warmed cache)
- Average latency: 31ms
- New capabilities: cross_entity_mentions (7.5ms), trend_detection (5.3ms)
- balanced_search: 151ms, agent_search_context: 121ms

### Embedding Coverage
| Entity | Total | Embedded | Coverage |
|--------|-------|----------|----------|
| Companies | 4,579 | 4,506 | 98.4% |
| Network | 3,528 | 2,931 | 83.1% |
| Thesis | 8 | 8 | 100% |
| Portfolio | 142 | 142 | 100% |
| Content Digests | 22 | 22 | 100% |
| Interactions | 23 | 23 | 100% |
| Actions | 144 | 99 | 68.8% |

### Network Embedding Gap
597 network records still lack embeddings (16.9%). All 597 have FTS (keyword search works), 442 have role_title. These are searchable via FTS/trigram but invisible to semantic/vector search.

**Priority:** Actions at 68.8% is the more critical gap -- these are the primary work items for ENIAC.

## ENIAC Tool Gap Assessment

### What's Covered (48 functions across 6 domains)

| Domain | Functions | Assessment |
|--------|-----------|------------|
| **Search** (9) | hybrid, enriched, balanced, enriched_balanced, search_across_surfaces, agent_search_context, search_content_digests, search_thesis_threads, search_thesis_context | **Complete.** balanced_search fixes the last P0 |
| **Signal Intelligence** (2) | cross_entity_mentions, trend_detection | **NEW.** Cross-entity correlation + temporal trends |
| **Entity Intelligence** (11) | company_intelligence_profile, competitive_landscape, deal_pipeline_intelligence, deal_intelligence_brief, network_intelligence_report, person_communication_profile, portfolio_intelligence_report, portfolio_deep_context, portfolio_intelligence_map, interaction_intelligence_report, interaction_intelligence_score | **Complete.** Full entity dossier capability |
| **Thesis Intelligence** (9) | thesis_landscape, thesis_research_package, thesis_momentum_report, thesis_health_dashboard, aggregate_thesis_evidence, detect_thesis_bias, suggest_actions_for_thesis, score_action_thesis_relevance, predict_next_actions | **Complete.** Full thesis analysis |
| **Relationship** (9) | find_related_companies, find_related_entities, find_similar_network, relationship_graph, relationship_strength_score, entity_freshness_score, discover_connections, connect_orphaned_entities, strategic_network_map | **Complete.** Full graph traversal |
| **Scoring** (8) | score_explainer, narrative_score_explanation, explain_score, scoring_intelligence_report, route_action_to_bucket, detect_emerging_signals, intelligence_timeline, suggest_next_actions | **Complete.** Full scoring transparency |

### What's Still Missing (ENIAC Product Manager View)

1. **Embedding generation at query time** -- No Edge Function for real-time embedding of search queries. `balanced_search` uses proxy embeddings (borrowing from best FTS match). True semantic search requires an embedding Edge Function calling an embedding API. **Score impact: search quality 62/100 -> ~85/100.**

2. ~~**Cross-entity signal correlation**~~ -- **BUILT.** `cross_entity_mentions(entity_type, entity_id, days, limit)` finds all mentions via direct links, name ILIKE, and semantic similarity. Returns unified timeline. 7.5ms latency.

3. ~~**Temporal trend detection**~~ -- **BUILT.** `trend_detection(query, window_days, comparison_window_days)` compares mention counts across surfaces in current vs comparison windows. Classifies as accelerating/stable/decelerating/new/gone. 5.3ms latency.

4. **Action deduplication at search time** -- Actions with similar text can crowd results. `deduplicate_actions` exists for batch cleanup but search results don't deduplicate. **Minor -- addressed by balanced_search limiting action slots.**

## Next Loop Priorities

1. **P1:** Get actions embedding coverage from 68.8% to 95%+ (45 actions missing embeddings)
2. **P1:** Get network embedding coverage from 83.1% to 95%+ (597 missing)
3. **P2:** Edge Function for real-time query embedding (would eliminate proxy embedding fallback)
4. **P3:** Expose `cross_entity_mentions` and `trend_detection` via State MCP tools for droplet agents
