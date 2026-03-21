# Skill: ENIAC Search Operations

Instructions for ENIAC's cross-surface search — balanced retrieval across all entity types
with intelligence enrichment.

---

## Search Architecture

ENIAC has three tiers of search, each building on the previous:

```
balanced_search()           → raw cross-surface retrieval with fairness guarantees
enriched_balanced_search()  → balanced + inline context snippets per result
agent_search_context()      → enriched + portfolio connections, thesis relevance,
                              obligations, interaction recency, action hints
```

**Default:** Always use `agent_search_context()` unless you need raw results for
specific processing.

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
| `source_table` | text | Which surface: `companies`, `thesis_threads`, `network`, `actions_queue`, `content_digests`, `interactions`, `portfolio` |
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

Results are balanced across surfaces. Even if companies dominate keyword matches,
you'll get minimum representation from:
- 3 companies, 2 thesis threads, 2 network people, 2 actions
- 1 digest, 1 interaction, 1 portfolio entry

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
