# M6 IRGI Agent Tools Audit — L61-70
*2026-03-21 | 10 loops | 4 new functions + performance audit*

## Summary

L61-70 transformed IRGI from a set of intelligence functions into a proper **agent toolbox**. The fundamental shift: stop trying to make SQL functions produce "intelligence" — make them produce rich **context** that agents can reason with.

Four new agent-ready functions were built, each designed as a TOOL that a specific agent calls:

| Function | Agent Consumer | Purpose | Latency |
|----------|---------------|---------|---------|
| `agent_search_context()` | ENIAC | Enriched search: returns WHY each result matters, portfolio connection, thesis relevance, obligation context, agent action hints | 60ms |
| `thesis_research_package()` | ENIAC | Complete thesis research bundle: 23 data fields from 12 sources. Everything needed to produce a thesis research report. | 240ms |
| `portfolio_deep_context()` | Any agent (meeting prep) | Full company dossier: portfolio data, key people with obligations, interaction history, actions pipeline, thesis connections, similar companies, agent meeting prep directives | 10ms |
| `discover_connections()` | Any agent ("you should know") | Non-obvious connections: shared people, thesis overlap, interaction bridges, sector clusters, hidden semantic links | 22ms |

## IRGI System State

| Metric | Value |
|--------|-------|
| IRGI Score | **8.4/10** |
| Total Functions | 14 IRGI core (was 10, +4 agent tools) |
| All Passing | Yes |
| Average Latency | 15.4ms (benchmark suite) |
| Functions <200ms | 13/14 |
| Functions <500ms | 14/14 |

## Complete Agent Tools Inventory

### Tier 1: Agent-Ready Tools (L61-70, NEW)

**1. `agent_search_context(query, embedding?, limit?)`**
- **When an agent should use it:** Any time an agent needs to research a topic, person, company, or thesis. This is the PRIMARY search entry point.
- **Returns per result:** source_table, record_id, title, combined_score, why_it_matters, portfolio_connection, thesis_relevance, recent_signals, obligation_context, interaction_recency, agent_action_hint
- **Agent action hints:** URGENT (red health, fumes date), ACTION (stale relationships, open obligations), RESEARCH (bias alerts), TRIAGE (high-priority actions), ANALYZE (content), CONTEXT (background)
- **Performance:** 60ms

**2. `thesis_research_package(thesis_id)`**
- **When an agent should use it:** ENIAC agent starting thesis research, or any agent needing full thesis context.
- **Returns (JSONB):** 23 keys — thesis core data, evidence (for/against with cross-references), connected companies (with portfolio status), connected people (with obligations), key questions (open/answered), recent interaction signals, comparable theses (by embedding similarity), bias analysis (6 flags), momentum indicators, actions pipeline, related content, obligations, agent_research_directives
- **Agent research directives:** research_gaps (HIGH/MODERATE/LOW), evidence_health (CRITICAL/HIGH/MEDIUM/OK), freshness (STALE/AGING/FRESH), suggested_next_steps
- **Performance:** 240ms

**3. `portfolio_deep_context(company_id)`**
- **When an agent should use it:** Meeting prep for any company (portfolio or pipeline). Getting full intelligence package before a founder call, board prep, or deal review.
- **Returns (JSONB):** company core data, intelligence_score, portfolio_data (if portfolio: health, ownership, cash, fumes, key questions, high-impact, research file), key_people (with obligations, relationship status, interaction summary), interactions_history, obligations (I-owe/they-owe with urgency), actions_pipeline, thesis_connections, similar_companies, agent_meeting_prep
- **Agent meeting prep directives:** i_owe_count, they_owe_count, overdue_obligations, open_actions_count, stale_relationships, context_richness (RICH/MODERATE/THIN/MINIMAL), preparation_priorities (URGENT/ACTION/STANDARD/PIPELINE)
- **Performance:** 10ms

**4. `discover_connections(entity_type, entity_id, limit?)`**
- **When an agent should use it:** Finding "you should know" connections. Looking for non-obvious relationships before meetings. Cross-pollinating intelligence across entities.
- **Entity types:** 'company', 'network', 'thesis', 'portfolio'
- **Returns (JSONB):** shared_people_connections (companies/people linked through shared contacts), thesis_overlap (theses with shared company coverage), interaction_bridges (people appearing in multiple interactions), sector_clusters (same-sector companies with high vector similarity), hidden_semantic_connections (cross-type semantic links), insight_summary (total discoveries, breakdown, agent directive)
- **Agent directives:** RICH NETWORK / THESIS CLUSTER / HIDDEN LINKS / STANDARD
- **Performance:** 22ms

### Tier 2: Core Intelligence Functions (L6-20)

**5. `hybrid_search(query, embedding?, limit?, kw_weight?, sem_weight?, filter_tables?, filter_status?, filter_date_from?, filter_date_to?)`**
- **Purpose:** Cross-table FTS+vector search across 5 tables (content_digests, thesis_threads, actions_queue, companies, network)
- **When to use:** Raw search when agent_search_context is too heavy or when specific filters needed
- **Returns:** source_table, record_id, title, snippet, semantic/keyword ranks and scores, combined_score
- **Performance:** 45ms

**6. `enriched_search(...)` — same params as hybrid_search**
- **Purpose:** hybrid_search + context_snippet per entity type (portfolio status, thesis conviction, action reasoning)
- **When to use:** Search with one layer of context, lighter than agent_search_context
- **Performance:** 30ms

**7. `find_related_companies(company_id, limit?)`**
- **Purpose:** Vector similarity between companies
- **Returns:** company_id, company_name, similarity, sector
- **Performance:** 2ms

**8. `find_related_entities(company_id, limit?)`**
- **Purpose:** Companies + network people related to a company (via connections, refs, vectors)
- **Returns:** entity_type, entity_id, entity_name, similarity, context
- **Performance:** 8ms

**9. `score_action_thesis_relevance(action_id)`**
- **Purpose:** How relevant is an action to each thesis? 4-method weighted scoring (vector 0.50, explicit 0.20, trigram 0.15, key_question 0.15)
- **Returns:** thesis_id, thesis_name, relevance_score, match_type
- **Performance:** 12ms

**10. `route_action_to_bucket(action_id)`**
- **Purpose:** Classify action into 4 buckets: Discover New, Deepen Existing, Expand Network, Thesis Evolution
- **Returns:** bucket, confidence, reasoning (with signal breakdown)
- **Performance:** 6ms

**11. `suggest_actions_for_thesis(thesis_id, limit?)`**
- **Purpose:** Generate action suggestions from key questions, company gaps, digest gaps, network candidates, evidence gaps
- **Returns:** suggestion, reasoning, priority, bucket, related_company
- **Performance:** 18ms

**12. `aggregate_thesis_evidence(thesis_id)`**
- **Purpose:** All evidence for/against a thesis from 7 sources (portfolio, content digests, actions, outcomes, interactions, network connections, vector matches)
- **Returns:** evidence_type, source_type, source_id, source_title, relevance, sentiment, created_at
- **Performance:** 49ms

**13. `detect_thesis_bias(thesis_id?)`**
- **Purpose:** 6-flag bias detection (confirmation, possible, source, stale, conviction_mismatch, thin_evidence) with severity grading
- **Returns:** thesis_id, thread_name, conviction, evidence counts, ratio, bias flags, flags JSONB with severity
- **Performance:** 2ms

**14. `company_intelligence_profile(company_id)`**
- **Purpose:** Row-per-metric company profile (portfolio data, thesis connections, key people, pending actions, interactions, sector peers, intelligence score)
- **Returns:** metric, value, detail
- **Performance:** 6ms

### Tier 3: System Health & Reports

| Function | Purpose | Consumer |
|----------|---------|----------|
| `irgi_system_report()` | Full JSONB system report (score, benchmarks, embedding health, thesis health, portfolio summary, data counts, signals, deals) | Health checks, monitoring |
| `irgi_benchmark()` | Performance benchmark of all core functions with PASS/FAIL | CI, monitoring |
| `thesis_health_dashboard()` | All theses with momentum, freshness, health grade | WebFront /strategy page |
| `portfolio_intelligence_map()` | All portfolio companies with intelligence scores, freshness, attention flags | WebFront, agents |
| `bias_summary` (view) | All theses with bias severity flags | ENIAC, WebFront |

## Performance Summary

```
Function                        Latency   Status
────────────────────────────────────────────────
find_related_companies            2ms     FAST
detect_thesis_bias                2ms     FAST
company_intelligence_profile      6ms     FAST
route_action_to_bucket            6ms     FAST
find_related_entities             8ms     FAST
portfolio_deep_context           10ms     FAST
score_action_thesis_relevance    12ms     FAST
suggest_actions_for_thesis       18ms     FAST
discover_connections             22ms     FAST
enriched_search                  30ms     FAST
hybrid_search                    45ms     FAST
aggregate_thesis_evidence        49ms     FAST
agent_search_context             60ms     FAST
thesis_research_package         240ms     OK
────────────────────────────────────────────────
Average: 35ms | Max: 240ms | All under 500ms
```

## Data Volumes (as of 2026-03-21)

| Table | Rows |
|-------|------|
| entity_connections | 26,573 |
| companies | 4,575 |
| network | 3,528 |
| actions_queue | 144 |
| portfolio | 142 |
| interaction_action_links | 31 |
| interactions | 23 |
| content_digests | 22 |
| obligations | 14 |
| thesis_threads | 8 |

## Known Gaps & Next Steps

1. **Embedding generation gap**: Search functions fall back to trigram/FTS when no embedding provided (query-by-example works but is indirect). Edge Function for real-time embedding generation would unlock full agent_search_context potential.
2. **thesis_research_package at 240ms**: Acceptable for research contexts but would benefit from materialized views for connected_companies (355 rows for thesis 1) if called frequently.
3. **Interaction data is thin**: Only 23 interactions — as Cindy processes more email/calendar/WhatsApp data, all functions that use interaction signals will become dramatically richer.
4. **Obligation data is thin**: Only 14 obligations — same Cindy dependency. portfolio_deep_context and agent_search_context both surface obligation context that's currently sparse.
5. **discover_connections shared_people**: Currently requires >= 2 shared contacts to surface. With more entity_connections, threshold could be relaxed to find more subtle bridges.

## Architecture Decision

These 4 functions follow the **"tools produce context, agents produce intelligence"** pattern:
- SQL functions return structured data with metadata (connection strengths, bias flags, freshness indicators)
- Agent directives suggest what to DO with the data, but the agent decides
- No function tries to "be smart" — they provide rich, multi-dimensional context packets

This is the correct separation: PostgreSQL is fast at graph traversal, vector search, and aggregation. Agents are good at reasoning about what the data means and what to do next.
