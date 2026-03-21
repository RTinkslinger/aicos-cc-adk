# M6 IRGI Perpetual Loop Audit — L71-72
*2026-03-21 | Search Quality Revolution: Term-Coverage Ranking + Entity-Preferred Proxy*

## Summary

L71-72 fixed the critical search ranking problem where Confido Health (a portfolio company that IS a "healthcare AI voice agent" company) ranked outside the top 60 for the query "healthcare AI voice agents." Root cause was three-fold: (1) OR-query dilution flooding 1143 matches, (2) proxy embedding selected from a generic content digest instead of the specific company, (3) no term-coverage weighting.

Three fixes deployed:
1. **term_coverage_boost()** — new helper function. Counts what fraction of query terms match a document. Full coverage (4/4 terms) = 2x keyword boost. Half coverage = 1.5x.
2. **AND-first proxy with entity preference** — proxy selection tries AND query first (more specific), falls back to OR. Within each strategy, prefers companies/thesis embeddings over content_digest embeddings (entity-specific vs generic).
3. **Document-length normalization** — ts_rank_cd flag 32 divides by document length, preventing 50K-word podcast transcripts from drowning 900-char company descriptions.

## Before vs After

| Query | Before | After |
|-------|--------|-------|
| "healthcare AI voice agents" — Confido Health | Not in top 60 | **Rank 2** (score 0.967, sem=1.0) |
| "healthcare AI voice agents" — Healthcare thesis | Rank ~14 | **Rank 3** (score 0.941) |
| "healthcare AI voice agents" — Confido action | Not ranked | **Rank 6** (score 0.872) |
| "cybersecurity penetration testing" — thesis | Rank 2 | Rank 2 (no regression) |
| "fintech payments India" | Working | Working (no regression) |

## New Functions

### `term_coverage_boost(p_fts tsvector, p_query_text TEXT) -> FLOAT`
- Returns 0.0-1.0 based on fraction of query terms matching the document
- Splits query into individual words (>= 2 chars), tests each against the tsvector
- IMMUTABLE for caching

## hybrid_search Changes (v4)

### Proxy Selection
```
BEFORE: Best FTS match across all tables (OR query) -> often a generic content digest
AFTER:
  1a. AND-match proxy, entity preference: companies > thesis > actions > network > content_digests
  1b. OR-match proxy fallback (same entity preference)
  2.  Trigram fallback (unchanged)
```

### Keyword Scoring
```
BEFORE: ts_rank_cd(fts, ts_query)  -- raw, unnormalized, no coverage
AFTER:  ts_rank_cd(fts, ts_query, 32) * (1.0 + term_coverage_boost(fts, query_text))
        -- normalized by doc length, boosted by term coverage
```

### Proxy Self-Inclusion
```
BEFORE: Only thesis_threads and actions_queue had proxy self-inclusion (score=1.0)
AFTER:  ALL 5 tables have proxy self-inclusion with semantic_score=1.0
```

### CTE Limits
```
BEFORE: match_count * 2 for all keyword CTEs
AFTER:  match_count * 3 (kw_limit) for keyword CTEs -- more coverage for OR queries
```

## IRGI System State

| Metric | Value | Change |
|--------|-------|--------|
| IRGI Score | **8.5/10** | +0.1 |
| Total Functions | 15 (14 core + term_coverage_boost) | +1 |
| All Passing | Yes (27/27) | Stable |
| hybrid_search latency | 160ms | +92ms (term_coverage_boost overhead) |
| enriched_search latency | 117ms | +67ms (wraps hybrid_search) |
| All other functions | Unchanged | Stable |
| All under 500ms | Yes | Stable |

## Embedding Health

| Table | Coverage | Change |
|-------|----------|--------|
| companies | 99.5% (4553/4575) | ~stable (22 new unembedded) |
| network | 40.6% (1431/3528) | +13.1% (from 27.5%) |
| thesis_threads | 100% | Stable |
| interactions | 100% | Stable |
| portfolio | 100% | Stable |
| actions_queue | 100% | Stable |
| content_digests | 100% | Stable |

## Data Volumes

| Table | Rows |
|-------|------|
| companies | 4,575 |
| network | 3,528 |
| actions_queue | 144 |
| portfolio | 142 |
| interactions | 23 |
| content_digests | 22 |
| obligations | 14 |
| thesis_threads | 8 |

## Performance Benchmark (all PASS)

```
Function                        Latency   Status
hybrid_search(kw)               160ms     PASS (was 68ms, +coverage boost overhead)
enriched_search                 117ms     PASS (was 50ms)
find_active_deals               111ms     PASS
search_across_surfaces           54ms     PASS
thesis_landscape                 52ms     PASS
aggregate_thesis_evidence        39ms     PASS
find_related_companies            6ms     PASS
competitive_landscape            33ms     PASS
network_intel_report             29ms     PASS
portfolio_intel_map              23ms     PASS
find_similar_network             21ms     PASS
predict_next_actions             17ms     PASS
suggest_actions_thesis           15ms     PASS
intelligence_timeline            11ms     PASS
embedding_health                 11ms     PASS
score_action_thesis_rel          11ms     PASS
find_related_entities             8ms     PASS
deal_pipeline_intel               8ms     PASS
thesis_momentum_report            8ms     PASS
route_action_to_bucket            5ms     PASS
relationship_strength             4ms     PASS
detect_emerging_signals           4ms     PASS
interaction_intel_report          3ms     PASS
suggest_next_actions(co)          3ms     PASS
relationship_graph                2ms     PASS
detect_thesis_bias                2ms     PASS
score_explainer                   0ms     PASS
```

## Known Gaps & Next Loops

1. **hybrid_search latency** (160ms): term_coverage_boost is called per-row for all 1143 OR-matched companies. Could optimize with a materialized coverage column or pre-filter to top FTS matches before applying boost.
2. **Network embeddings at 40.6%**: Recovering steadily. Person search quality will keep improving.
3. **Content digest keyword dominance**: Even with normalization, long transcripts still have high keyword scores. RRF (Reciprocal Rank Fusion) would be the proper fix but requires larger refactor.
4. **Portfolio intelligence map**: Working well with M12's enriched data. Companies with richer profiles now show in competitive_landscape searches.
5. **agent_search_context action hints**: Confido Health gets "CONTEXT" hint instead of "PORTFOLIO COMPANY" because the company->portfolio join uses LOWER name match. Could add direct portfolio_co lookup for better coverage.

## Architecture Notes

The "entity preference" proxy selection is a key design decision: when a query has AND matches in a company and also in a content digest, the company embedding is more domain-specific and produces better semantic neighborhoods. A podcast discussing "AI agents in healthcare" broadly gives a generic embedding. A company description for "Confido Health builds AI voice agents for healthcare" gives a precise domain embedding that pulls in similar companies (RapidClaims, Nidana AI, MedMitra).

This mirrors how human search works: if you're looking for "healthcare AI voice agents," you want to explore the space around an actual healthcare AI company, not around a podcast episode that mentioned those words.
