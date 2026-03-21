# M6 IRGI Perpetual Loop v3 — 2026-03-21

## IRGI Score: 8.7/10 (up from 8.6 in v2)

All 27 benchmark functions PASS. Avg latency 22.9ms. Two intermittent cold-cache failures on `find_related_companies` (258ms) and `competitive_landscape` (278ms) resolved on second run (2.4ms and 3.9ms respectively). HNSW indexes confirmed on both `companies.embedding` and `network.embedding`.

---

## 1. Embedding Status — QUEUE ACTIVELY DRAINING

### Companies: 98.6% embedded (4,513 / 4,579)
- **66 missing**: 59 `research_enriched`, 4 `raw`, 3 `M12-L50-enriched`
- 62 of 66 have rich page_content (>50 chars), all 66 have sector
- All 66 in the embedding queue — **estimated drain: 0.8 hours**

### Network: 70.8% embedded (2,499 / 3,528) — UP from 66.1% at session start
- **1,029 remaining** (was 1,197 at start of this loop — 168 processed during analysis)
- Breakdown: 704 `enriched_l40`, 456 `enriched_l41`, 37 `M12-L52-enriched`
- 1,076 of 1,197 have rich page_content, 1,041 have role_title
- All in queue — **estimated drain: 0.8 hours at 1,520 items/hour**

### Queue Infrastructure: HEALTHY
- Cron: `process_embeddings` every 2 min (15 items/batch, 5 concurrent)
- Cron: `cleanup_embedding_jobs` every 2 min (odd minutes)
- Success rate 24h: 94.9% (6,798 success, 366 fail — intermittent connection failures)
- Queue depth dropping steadily

### Verdict: SELF-HEALING. No action needed. Check back in ~1 hour for 100% coverage.

---

## 2. CRITICAL BUG: hybrid_search Returns Zero Companies for Multi-Entity Queries

### The Problem
Searching "AI agent infrastructure India" via `hybrid_search` / `enriched_search` / `agent_search_context` returns **zero companies** in the top 20. All 20 results are content_digests (12), actions_queue (4), and thesis_threads (2).

### Root Cause Analysis (3-layer diagnosis)

**Layer 1 — Keyword Score Asymmetry:**
Content digests score 1.78 on FTS for this query (dense text mentioning all 4 terms). Companies score 0.019 at best (terms scattered across page_content). The OR-based `text_to_or_tsquery` with `term_coverage_boost` amplifies this gap.

**Layer 2 — Proxy Embedding Bias:**
When no external embedding is provided, `hybrid_search` selects a "proxy embedding" from the best FTS-matching record. For this query, it picks a content_digest. The semantic search then finds records similar to *that digest's embedding*, systematically biasing toward more digests.

**Layer 3 — Global Sort With No Entity Quotas:**
The final `UNION ALL + ORDER BY combined_score DESC LIMIT 20` has no minimum per-entity-type representation. High-scoring entity types crowd out lower-scoring ones entirely.

### Proof
- `hybrid_search('...', NULL, 50)`: 6 companies appear (avg score 0.81)
- `hybrid_search('...', NULL, 20, filter_tables => ARRAY['companies'])`: 15 companies appear
- `search_across_surfaces('...')`: 19 companies appear (FTS + trigram, no semantic)

### Impact
When ENIAC asks "find companies in AI agent infrastructure in India," the primary search function returns NOTHING useful. ENIAC would have to know to call `search_across_surfaces` instead, which lacks semantic scoring and the rich enrichment layer of `agent_search_context`.

### Fix Required: ENTITY-AWARE RESULT MIXING
The `hybrid_search` or `agent_search_context` function needs a minimum entity quota. Proposed approach:
```
Per-table top-N selection (top 3-5 per entity type)
UNION
Global top-N selection (remaining slots by score)
```
This ensures every entity type that has ANY match gets representation, while still allowing high-scoring results to dominate the remaining slots.

### Alternatively: NEW FUNCTION `balanced_search`
Create a new function that combines `search_across_surfaces` (entity diversity) with `enriched_search` (rich context). Return top 3 per entity type + fill remaining with global best.

---

## 3. agent_search_context — Enrichment Quality VERIFIED

### What Works Well
- Portfolio company lookup (Smallest AI): Full portfolio data, thesis links, competitive landscape, network connections, agent directive
- `deal_intelligence_brief`: Outstanding — returns portfolio data, key questions, competitive context, network connections, thesis connections, agent action recommendation
- Entity connections: 23,732 connections across 17 types. Rich graph.
- Person search (Surabhi Bhandari): Finds person, shows portfolio connection (Soulside [Green]), interaction recency

### Issues Found
1. **Person search ranking**: "Surabhi Bhandari" search returns "Forbes" as #1 (score 0.80) and the actual person as #2 (0.76). The proxy embedding selection picks a company with name similarity, biasing semantic results.
2. **No-embedding companies invisible**: Boba Bhai (portfolio, `research_enriched`, no embedding) doesn't appear when searched by name. Same root cause — missing embedding means missing from semantic arm.

### entity_connections Coverage
| Source → Target | Count |
|---|---|
| network → company | 9,100 |
| company → company | 8,465 |
| network → network | 2,036 |
| network → thesis | 1,479 |
| thesis → company | 1,077 |
| company → thesis | 498 |
| portfolio → network | 338 |
| portfolio → thesis | 287 |
| portfolio → company | 142 |
| action → thesis | 138 |
| action → company | 114 |
| interaction → network | 20 |
| interaction → company | 20 |

**entity_connections is NOT empty** (was empty at M12 start). 23,732 connections exist with good diversity.

---

## 4. Portfolio Intelligence — 137/142 STALE

The `irgi_system_report` shows:
- **137 STALE** portfolio companies (no recent interaction data)
- **3 FRESH**, **2 RECENT**, **0 AGING**
- Average intelligence score: 5.3/10
- Health: 84 Green, 33 Yellow, 18 Red, 7 NA

This is a data freshness problem, not an IRGI function problem. Portfolio companies need interaction data from Granola/Calendar/WhatsApp to become FRESH. This is M8 Cindy's domain.

---

## 5. What Agent Tools Are MISSING for ENIAC?

Thinking as ENIAC's product manager — what would a research analyst agent need that doesn't exist?

### Functions That Exist and Work (27 benchmarked):
- Search: `hybrid_search`, `enriched_search`, `agent_search_context`, `search_across_surfaces`, `search_content_digests`, `search_thesis_context`
- Company intel: `deal_intelligence_brief`, `deal_pipeline_intelligence`, `company_intelligence_profile`, `competitive_landscape`, `find_related_companies`, `find_active_deals`
- Network: `find_similar_network`, `network_intelligence_report`, `relationship_graph`, `relationship_strength_score`, `strategic_network_map`
- Thesis: `thesis_landscape`, `thesis_research_package`, `aggregate_thesis_evidence`, `detect_thesis_bias`, `suggest_actions_for_thesis`, `thesis_momentum_report`, `thesis_health_dashboard`
- Scoring: `agent_scoring_context`, `score_explainer`, `scoring_intelligence_report`
- Actions: `predict_next_actions`, `suggest_next_actions`, `route_action_to_bucket`, `detect_emerging_signals`
- Portfolio: `portfolio_intelligence_map`, `portfolio_risk_assessment`, `portfolio_deep_context`

### MISSING — What ENIAC Needs:

**P0 — Critical:**
1. **`balanced_search(query, limit)`** — The search fix described above. Entity-aware ranking that guarantees company/network/thesis representation alongside digests.

**P1 — High Value:**
2. **`thesis_company_map(thesis_id)`** — Given a thesis, return ALL connected companies with their deal status, pipeline stage, and conviction scores. Currently requires multiple queries (entity_connections → companies → portfolio JOIN).
3. **`person_360(person_id)`** — One-call complete person dossier: role, companies (current + past), thesis connections, obligations, interactions, portfolio links, communication profile. Currently requires 5+ function calls.
4. **`market_landscape(sector_or_keywords)`** — Given a thesis area, return the competitive map: all companies in that space, their stages, funding, portfolio overlaps. Currently `competitive_landscape` only works from a single company, not from a thesis/sector query.

**P2 — Nice to Have:**
5. **`content_to_entity_links(digest_id)`** — Given a content digest, return which companies/people/theses it mentions. Currently digest analysis is in the digest JSON but not queryable as structured relations.
6. **`stale_thesis_evidence(thesis_id)`** — Return evidence items that are older than 30 days and need refresh. Currently requires manual date comparison.

---

## 6. Thesis Searchability

| Thesis | Connected Entities |
|---|---|
| SaaS Death / Agentic Replacement | 480 |
| Agentic AI Infrastructure | 463 |
| Cybersecurity / Pen Testing | 58 |
| AI-Native Non-Consumption Markets | 31 |
| Agent-Friendly Codebase as Bottleneck | 21 |
| Healthcare AI Agents as Infrastructure | 10 |
| CLAW Stack Standardization | 9 |
| USTOL / Deep Tech Mobility | 1 |

Top 2 theses are well-connected. Bottom 4 are thin — USTOL has only 1 entity connection. These need enrichment (M12's domain).

---

## 7. Data Quality Snapshot

| Metric | Companies | Network | Portfolio |
|---|---|---|---|
| Total records | 4,579 | 3,528 | 142 |
| Embeddings | 98.4% | 70.8% | 100% |
| Page content fill | 99.9% | 100% | 100% |
| Avg content length | 169 chars | 204 chars | 864 chars |
| Rich (300+ chars) | 731 (16%) | 253 (7%) | 105 (74%) |
| Has LinkedIn/website | 759 | 3,089 | — |
| Has email | — | 1,079 (31%) | — |

Company content is mostly thin (39% < 100 chars). Network is better but 94% are < 300 chars. Portfolio is well-documented. M12 enrichment is improving quality but the thin records still dominate.

---

## Summary & Next Loop Priorities

### Working Well
- IRGI score 8.7 — all functions PASS
- Embedding queue self-healing (1,520/hr processing rate)
- `deal_intelligence_brief` is outstanding
- `agent_search_context` enrichment layer is production-grade
- entity_connections at 23,732 with 17 types
- Network coverage climbing steadily (66% → 71% during this analysis)

### Critical Fix Needed
- **Search ranking: zero companies in multi-entity queries** — needs entity-aware result mixing (P0)

### ENIAC Tool Gaps
- `balanced_search` (P0), `thesis_company_map` (P1), `person_360` (P1), `market_landscape` (P1)

### Upstream Dependencies
- Portfolio staleness (137/142 STALE) — needs M8 Cindy interaction data
- Thin thesis connections (USTOL=1, CLAW=9) — needs M12 enrichment
- Company content depth (39% thin) — needs M12 enrichment

### Embedding Projection
At current rate, by end of day:
- Companies: 100% (66 remaining, <1 hour)
- Network: ~85-90% (1,029 remaining, ~0.7 hours to complete what's queued)
