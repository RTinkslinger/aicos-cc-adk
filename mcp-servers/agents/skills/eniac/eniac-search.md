# Skill: ENIAC Search Operations

Instructions for ENIAC's cross-surface search — balanced retrieval across all entity types
with intelligence enrichment.

---

## Search Architecture

ENIAC has three tiers of search, each building on the previous:

```
hybrid_search()             → base layer: 8-surface semantic+keyword, proxy embedding,
                              returns record_date for recency signals
balanced_search()           → hybrid + fairness minimums + recency boost (30-day half-life)
enriched_balanced_search()  → balanced + inline context snippets per result
agent_search_context()      → enriched + portfolio connections, thesis relevance,
                              obligations, interaction recency, action hints
```

**Default:** Always use `agent_search_context()` unless you need raw results for
specific processing.

### Recency Boost (active since 2026-03-21)

All balanced/enriched/agent searches apply `recency_boost(record_date, 30, 0.15)`:
- Records updated today: +0.15 to normalized score
- Records updated 30 days ago: +0.075
- Records updated 90 days ago: +0.019
- Records updated 1 year ago: ~0.0

This is additive on top of relevance scoring. It breaks ties in favor of fresher intel
without overriding strong relevance signals. The boost is capped at 0.15 so it can only
nudge rankings when records have comparable relevance.

### Search Quality Monitoring

Run `irgi_search_quality_assessment()` to get a composite quality score across 10
standardized test queries. Current baseline: **9.8/10**. This is included automatically
in `irgi_system_report()`.

---

## agent_search_context() — Primary Search Interface

Your main search tool. Returns results enriched with everything ENIAC needs to reason.

```bash
psql $DATABASE_URL -c "SELECT * FROM agent_search_context('AI infrastructure investment thesis')"
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `p_query` | text | required | Natural language search query |
| `p_embedding` | vector | NULL | Pre-computed embedding (optional, falls back to keyword-only) |
| `p_limit` | integer | 15 | Max results |

### Return Columns

| Column | Type | Description |
|--------|------|-------------|
| `source_table` | text | Which surface: `companies`, `thesis_threads`, `network`, `actions_queue`, `content_digests`, `interactions`, `portfolio`, `whatsapp` |
| `record_id` | integer | ID in the source table |
| `title` | text | Entity name or action text |
| `combined_score` | float | Relevance score (higher = better) |
| `why_it_matters` | text | Context on why this result is relevant to the query |
| `portfolio_connection` | text | Link to portfolio (if any) |
| `thesis_relevance` | text | Which thesis threads connect and how |
| `recent_signals` | text | Recent activity or signals |
| `obligation_context` | text | Open obligations involving this entity |
| `interaction_recency` | text | When Aakash last interacted with this entity |
| `agent_action_hint` | text | Suggested next action for the agent |

### Fairness Guarantees

Results are balanced across 8 surfaces. Even if companies dominate keyword matches,
you'll get minimum representation from:
- 3 companies, 2 thesis threads, 2 network people, 2 actions
- 1 digest, 1 interaction, 1 portfolio entry, 1 WhatsApp conversation

This prevents blind spots where one loud surface drowns out important signals from others.

---

## balanced_search() — Raw Cross-Surface Retrieval

Lower-level search when you need raw scores without enrichment.

```bash
psql $DATABASE_URL -c "
  SELECT * FROM balanced_search(
    'fintech payments India',
    NULL,          -- embedding (NULL = keyword-only)
    20,            -- match_count
    0.3,           -- keyword_weight
    0.7,           -- semantic_weight
    3, 2, 2, 2, 1, 1, 1  -- min per surface
  )"
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query_text` | text | required | Search query |
| `query_embedding` | vector | NULL | Optional embedding vector |
| `match_count` | integer | 20 | Total results to return |
| `keyword_weight` | float | 0.3 | Weight for BM25/keyword matching |
| `semantic_weight` | float | 0.7 | Weight for vector similarity |
| `min_companies` | integer | 3 | Minimum company results |
| `min_thesis` | integer | 2 | Minimum thesis results |
| `min_network` | integer | 2 | Minimum network/people results |
| `min_actions` | integer | 2 | Minimum action results |
| `min_digests` | integer | 1 | Minimum content digest results |
| `min_interactions` | integer | 1 | Minimum interaction results |
| `min_portfolio` | integer | 1 | Minimum portfolio results |
| `min_whatsapp` | integer | 1 | Minimum WhatsApp results |
| `filter_status` | text | NULL | Filter by status (e.g., 'Active') |
| `filter_date_from` | timestamptz | NULL | Results after this date |
| `filter_date_to` | timestamptz | NULL | Results before this date |

### Return Columns

| Column | Type | Description |
|--------|------|-------------|
| `source_table` | text | Surface identifier |
| `record_id` | integer | Entity ID |
| `title` | text | Entity name |
| `snippet` | text | Matched text excerpt |
| `semantic_rank` | integer | Rank by vector similarity |
| `keyword_rank` | integer | Rank by keyword match |
| `semantic_score` | float | Raw semantic similarity score |
| `keyword_score` | float | Raw keyword match score |
| `combined_score` | float | Weighted combination |
| `normalized_score` | float | Normalized to 0.0-1.0 |

---

## enriched_balanced_search() — Balanced + Context

Same as `balanced_search()` but adds a `ctx` column with inline context for each result:
company sector, thesis conviction, person role, action status, etc.

```bash
psql $DATABASE_URL -c "
  SELECT source_table, title, combined_score, ctx
  FROM enriched_balanced_search('enterprise SaaS')
  ORDER BY combined_score DESC"
```

---

## search_across_surfaces() — Keyword-Only Cross-Surface

Simpler cross-surface search when you just need quick keyword matching without balancing.

```bash
psql $DATABASE_URL -c "
  SELECT * FROM search_across_surfaces(
    'Composio',
    20,
    ARRAY['companies', 'network', 'thesis_threads']  -- filter to specific surfaces
  )"
```

Returns: `surface`, `entity_id`, `entity_name`, `entity_snippet`, `relevance_score`,
`entity_metadata`, `last_activity`.

---

## Specialized Search Functions

### search_thesis_context()
Find thesis threads relevant to a query. Uses name matching, core_thesis text search,
and key_question matching.

```bash
psql $DATABASE_URL -c "SELECT * FROM search_thesis_context('payments infrastructure', 8)"
```

Returns: `thesis_id`, `thread_name`, `core_thesis`, `conviction`, `status`,
`relevance_score`, `match_type`.

### search_content_digests()
Search through analyzed content (articles, podcasts, videos).

```bash
psql $DATABASE_URL -c "
  SELECT * FROM search_content_digests('AI agent frameworks', NULL, 10)"
```

Requires embedding for semantic search; pass NULL for keyword-only.

### search_thesis_threads()
Lower-level thesis search. Requires embedding for vector search.

```bash
psql $DATABASE_URL -c "
  SELECT * FROM search_thesis_threads('agentic infrastructure', NULL, 10)"
```

---

## person_holistic_search() — Person-Centric 360 View

Find people by name, alias, or contextual keywords. Returns a holistic view combining
network profile + WhatsApp conversations + interactions + companies + theses + obligations.

```bash
psql $DATABASE_URL -c "
  SELECT person_name, role_title, match_score, match_method,
    cross_surface_mentions, intelligence_completeness,
    jsonb_array_length(whatsapp_conversations) as wa_convos,
    jsonb_array_length(connected_companies) as companies,
    jsonb_array_length(connected_theses) as theses,
    jsonb_array_length(obligations_pending) as obligations
  FROM person_holistic_search('Mohit', 5)"
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `p_query` | text | required | Person name, partial name, alias, or contextual keyword |
| `p_limit` | integer | 5 | Max people to return |

### Match Methods (ranked by priority)

1. **exact** — substring match on person_name (score 1.0)
2. **alias** — match on aliases array (score 0.9)
3. **trigram** — fuzzy name match via pg_trgm (score varies, threshold 0.2)
4. **fts_context** — full-text search on page_content/role_title (score varies)

### Return Columns

| Column | Type | Description |
|--------|------|-------------|
| `person_id` | integer | Network table ID |
| `person_name` | text | Full name |
| `role_title` | text | Current role |
| `e_e_priority` | text | Engagement priority |
| `match_score` | float | How well the query matched |
| `match_method` | text | Which method matched (exact/alias/trigram/fts_context) |
| `linkedin` | text | LinkedIn URL |
| `home_base` | text | Location(s) |
| `email` | text | Email address |
| `phone` | text | Phone number |
| `last_interaction_at` | timestamptz | Last interaction timestamp |
| `interaction_count_30d` | integer | Interactions in last 30 days |
| `interaction_surfaces` | text[] | Channels used |
| `whatsapp_conversations` | jsonb | Array of up to 5 WhatsApp convos (1:1 prioritized) |
| `recent_interactions` | jsonb | Array of up to 5 recent interactions |
| `connected_companies` | jsonb | Companies via entity_connections |
| `connected_theses` | jsonb | Thesis threads via entity_connections |
| `obligations_pending` | jsonb | Active obligations (not fulfilled/cancelled) |
| `cross_surface_mentions` | integer | How many surfaces reference this person (0-6) |
| `intelligence_completeness` | float | Data completeness score (0.0-1.0) |

### Usage Patterns

**Quick person lookup before research:**
```bash
psql $DATABASE_URL -c "SELECT * FROM person_holistic_search('Rahul Sharma', 1)"
```

**Find people connected to a topic:**
```bash
psql $DATABASE_URL -c "SELECT person_name, role_title, connected_theses
  FROM person_holistic_search('fintech', 5)"
```

**Identify intel gaps (low completeness):**
```bash
psql $DATABASE_URL -c "SELECT person_name, intelligence_completeness
  FROM person_holistic_search('Mohit', 5)
  WHERE intelligence_completeness < 0.5"
```

---

## company_holistic_search() — Company-Centric 360 View

Find companies by name, sector, or deal status. Returns a holistic view combining
company profile + portfolio data + connected people + theses + interactions + WhatsApp + actions.

```bash
psql $DATABASE_URL -c "
  SELECT company_name, sector, deal_status, match_score, match_method,
    portfolio_info IS NOT NULL AND portfolio_info != 'null'::jsonb AS is_portfolio,
    connected_people != '[]'::jsonb AS has_people,
    connected_theses != '[]'::jsonb AS has_theses,
    recent_interactions != '[]'::jsonb AS has_interactions,
    whatsapp_mentions != '[]'::jsonb AS has_whatsapp,
    cross_surface_mentions, intelligence_completeness
  FROM company_holistic_search('AuraML', 5)"
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `p_query` | text | required | Company name, sector keyword, or deal status |
| `p_limit` | integer | 5 | Max companies to return |

### Match Methods (ranked by priority)

1. **exact** — substring match on company name (score 1.0)
2. **trigram** — fuzzy name match via pg_trgm (score varies, threshold 0.2)
3. **fts_context** — full-text search on page_content (score varies)
4. **sector_match** — sector or deal_status substring match (score 0.7)

### Return Columns

| Column | Type | Description |
|--------|------|-------------|
| `company_id` | integer | Companies table ID |
| `company_name` | text | Company name |
| `sector` | text | Company sector |
| `deal_status` | text | Deal pipeline status |
| `company_type` | text | Company type |
| `match_score` | float | How well the query matched |
| `match_method` | text | Which method matched (exact/trigram/fts_context/sector_match) |
| `portfolio_info` | jsonb | Portfolio data if portfolio company (health, ownership, scale) or null |
| `connected_people` | jsonb | People via entity_connections (employees, founders, deal contacts) |
| `connected_theses` | jsonb | Thesis threads via entity_connections |
| `recent_interactions` | jsonb | Up to 5 recent interactions mentioning this company |
| `whatsapp_mentions` | jsonb | WhatsApp groups/chats mentioning this company |
| `related_actions` | jsonb | Actions related to this company |
| `cross_surface_mentions` | integer | How many surfaces reference this company (0-7) |
| `intelligence_completeness` | float | Data completeness score (0.0-1.0) |

### Usage Patterns

**Quick company lookup for research:**
```bash
psql $DATABASE_URL -c "SELECT * FROM company_holistic_search('E2B', 1)"
```

**Find companies in a sector:**
```bash
psql $DATABASE_URL -c "SELECT company_name, sector, deal_status, connected_theses
  FROM company_holistic_search('cybersecurity', 5)"
```

**Identify intel gaps (low completeness):**
```bash
psql $DATABASE_URL -c "SELECT company_name, intelligence_completeness
  FROM company_holistic_search('Composio', 5)
  WHERE intelligence_completeness < 0.5"
```

---

## Search Best Practices

1. **Start broad, then narrow.** Use `agent_search_context()` first. If a surface
   is underrepresented, do a targeted search on that surface.

2. **Cross-reference results.** When a company appears in search results, check if
   it's connected to any thesis threads. When a thesis appears, check connected companies.

3. **Use date filters for freshness.** When investigating recent signals, filter to
   last 14-30 days to avoid stale noise.

4. **Combine with research brief.** After searching, load a research brief for the
   most interesting results to get full context before acting.

5. **Surface-specific deep dives.** If balanced search shows a weak signal from
   `interactions`, do a targeted `search_across_surfaces()` on just interactions
   to see if there's more.
