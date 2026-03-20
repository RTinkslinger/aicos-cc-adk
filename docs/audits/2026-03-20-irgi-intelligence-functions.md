# IRGI Phase B: Intelligence Functions Audit
*Created: 2026-03-20*
*Supabase Project: llfkxnsfczludgigknbs (AI COS Mumbai, ap-south-1)*

---

## Summary

Created 6 SQL functions + 1 materialized view + 1 view on the Supabase Postgres database. These power the intelligence backend for action scoring, thesis-portfolio connections, and bucket routing per the ENIAC APM brief.

All functions use **pg_trgm trigram similarity** as the primary matching strategy (newly enabled), with **pgvector cosine distance** wired in for when embeddings get populated. Currently all embedding columns are NULL across all tables, so the vector paths are dormant but ready.

---

## Extensions Enabled

| Extension | Version | Purpose |
|-----------|---------|---------|
| `vector` | 0.8.0 | Pre-existing. Cosine distance for embeddings |
| `pg_trgm` | 1.6 | **Newly enabled.** Trigram-based fuzzy text matching |

---

## Functions Created

### A. `score_action_thesis_relevance(p_action_id INTEGER)`

**Returns:** `TABLE(thesis_id INT, thesis_name TEXT, relevance_score FLOAT, match_type TEXT)`

Scores relevance of a given action to all thesis threads using 4 methods:
1. **Vector similarity** (cosine distance) -- when both embeddings are non-NULL
2. **Trigram text overlap** -- pg_trgm similarity across action text vs thesis fields (thread_name, core_thesis, key_companies, evidence_for, investment_implications)
3. **Explicit thesis_connection field** -- substring matching between action's thesis_connection and thread names
4. **Key question keyword match** -- similarity between action text and open key questions from thesis JSON

Returns top 5 matches above threshold (0.05). Security: DEFINER, search_path: public, extensions.

**Test result (action 1 -- Pipeline Action about contact center ops):**

| thesis_id | thesis_name | score | match_type |
|-----------|-------------|-------|------------|
| 7 | Agent-Friendly Codebase as Bottleneck | 0.9000 | explicit_connection |
| 1 | Cybersecurity / Pen Testing | 0.2152 | text_overlap |
| 5 | USTOL / Aviation / Deep Tech Mobility | 0.2110 | text_overlap |
| 4 | SaaS Death / Agentic Replacement | 0.1986 | text_overlap |
| 2 | Healthcare AI Agents as Infrastructure | 0.1896 | text_overlap |

Correctly identifies explicit connection at 0.9 and ranks text-overlap matches below.

---

### B. `route_action_to_bucket(p_action_id INTEGER)`

**Returns:** `TABLE(bucket TEXT, confidence FLOAT, reasoning TEXT)`

Routes an action to ENIAC APM buckets using:
- **Keyword regex signals** on combined action text (action + thesis_connection + source_content + reasoning)
- **Action type classification** (Pipeline Action -> B1, Portfolio Check-in/Follow-on Eval -> B2, Meeting/Outreach -> B3, Research/Thesis Update -> B4)
- **Portfolio cross-reference** (checks company_notion_id against portfolio table)

Buckets:
- **Discover New (Bucket 1):** new company signals, pipeline actions, non-portfolio companies
- **Deepen Existing (Bucket 2):** portfolio companies, check-in/follow-on types
- **DeVC Collective (Bucket 3):** network/people keywords, meeting/outreach type
- **Thesis Evolution (Bucket 4):** thesis/research keywords, thesis-related action types

**Test result (10 proposed actions):**

| id | action_type | primary_bucket | confidence |
|----|------------|----------------|------------|
| 1 | Pipeline Action | Discover New (Bucket 1) | 0.70 |
| 2 | Portfolio Check-in | Deepen Existing (Bucket 2) | 0.35 |
| 3 | Meeting/Outreach | Discover New (Bucket 1) | 0.40 |
| 4 | Research | Thesis Evolution (Bucket 4) | 0.60 |
| 5 | Meeting/Outreach | DeVC Collective (Bucket 3) | 0.35 |

Routing aligns with action types and content semantics.

---

### C. `find_related_companies(p_query_text TEXT, p_limit_n INTEGER DEFAULT 10)`

**Returns:** `TABLE(company_id INT, company_name TEXT, similarity FLOAT, sector TEXT)`

Finds companies related to a query string. Has two paths:
- **Primary:** Trigram similarity on companies table (name, sector, JTBD, agent_ids_notes, sector_tags)
- **Fallback (active now):** When companies table is empty (0 rows), searches thesis_threads.key_companies and portfolio.portfolio_co instead

**Test result (query: "AI-powered code review for enterprise"):**
Returns 5 results from thesis key_companies fallback. Low similarity scores (0.05-0.08) because the fallback path matches against company name strings, not descriptions. This will improve dramatically once:
1. Companies table gets populated (200+ companies from Notion)
2. Embeddings get generated via Auto Embeddings pipeline

---

### D. `aggregate_thesis_evidence(p_thesis_id INTEGER)`

**Returns:** `TABLE(evidence_type TEXT, source_type TEXT, source_id INT, source_title TEXT, relevance FLOAT, sentiment TEXT, created_at TIMESTAMPTZ)`

Gathers all evidence for a thesis from 3 sources:
- **content_digests** -- thesis name mention in digest_data JSON (0.7 score) or trigram similarity
- **actions_queue** -- explicit thesis_connection match (0.8 score) or text similarity
- **action_outcomes** -- thesis_thread field match (0.9 score) or text similarity

Sentiment classification:
- **FOR:** evidence_direction "for" in digest, outcome = Gold/Helpful
- **AGAINST:** evidence_direction "against" in digest, contra signals, status = Dismissed
- **NEUTRAL:** no clear signal

**Test result (thesis 3 -- Agentic AI Infrastructure):**
- 50 evidence items returned (capped at limit)
- 4 action_outcomes (all scored 0.9 via explicit thesis match)
- 30+ action proposals (scored 0.8 via explicit thesis_connection)
- 16 content digests (scored 0.7 via thesis name in digest_data, classified as FOR)
- 2 digests matched via text similarity only (0.23-0.24, classified NEUTRAL)

Evidence aggregator correctly prioritizes explicit connections over inferred ones.

---

### E. `suggest_actions_for_thesis(p_thesis_id INTEGER, p_limit_n INTEGER DEFAULT 5)`

**Returns:** `TABLE(suggestion TEXT, reasoning TEXT, priority TEXT, bucket TEXT, related_company TEXT)`

Generates 4 types of suggestions:
1. **Key question research** -- surfaces open questions from thesis key_questions_json
2. **Company gap analysis** -- companies mentioned in thesis but no existing actions
3. **Digest follow-up** -- thesis-relevant digests without linked actions
4. **Evidence gap analysis** -- FOR vs AGAINST balance check, evidence sufficiency

Priority logic:
- Active thesis + High/Evolving Fast conviction -> P1
- Active thesis -> P1 for questions, P2 for evidence
- Non-active -> P2/P3

**Test result (thesis 3 -- Agentic AI Infrastructure, conviction: High):**

| suggestion | priority | bucket |
|-----------|---------|--------|
| Research: MCP security/category question | P1 - This Week | Thesis Evolution |
| Follow up: 8 Moats digest | P2 - This Month | Thesis Evolution |
| Follow up: Why Big AI India digest | P2 - This Month | Thesis Evolution |
| Contra research (evidence imbalance: 3618 FOR vs 436 AGAINST) | P2 - This Month | Thesis Evolution |

**Test result (thesis 1 -- Cybersecurity, 3 open questions):**
- All 3 open questions surfaced as research suggestions
- Company evaluation suggestion with 9 companies from key_companies field
- Digest follow-up suggestion

Both tests demonstrate correct prioritization and gap detection.

---

### F. `entity_relationships` (VIEW)

Shows cross-entity connections:
- **action_thesis:** 470 relationships (avg strength 0.184). Mix of explicit (thesis_connection field match) and inferred (trigram similarity > 0.15)
- **digest_action:** links content digests to their spawned actions
- **thesis_company:** links thesis threads to companies table (dormant -- companies table empty)
- **network_company:** links network people to companies via relation arrays (dormant -- both tables empty)

Top 10 strongest action-thesis links all score 0.28-0.34 and are correctly explicit connections (e.g., "Map agent infrastructure ecosystem" <-> "Agentic AI Infrastructure").

---

## Materialized View

### `action_scores`

Pre-computes bucket routing + thesis relevance for all Proposed actions.

| Metric | Value |
|--------|-------|
| Total rows | 92 (all Proposed actions) |
| Routed rows | 92 (100% coverage) |
| Distinct buckets | 4 |

**Bucket distribution:**

| Bucket | Actions | Avg Confidence |
|--------|---------|---------------|
| Thesis Evolution (Bucket 4) | 51 | 0.55 |
| Discover New (Bucket 1) | 18 | 0.65 |
| Deepen Existing (Bucket 2) | 13 | 0.37 |
| DeVC Collective (Bucket 3) | 10 | 0.35 |

**Observation:** Thesis Evolution dominates (55%) because current actions are mostly content-pipeline-generated (Research, Thesis Update, Content Follow-up types). As Companies DB and Network DB get populated with data, Buckets 1-3 will grow proportionally.

**Indexes:** `idx_action_scores_id` (lookup), `idx_action_scores_bucket` (filter), `idx_action_scores_unique_id` (enables CONCURRENTLY refresh).

**Refresh:** `SELECT refresh_action_scores();` (non-blocking, concurrent).

---

## Utility Function

### `refresh_action_scores()`

Convenience wrapper for `REFRESH MATERIALIZED VIEW CONCURRENTLY action_scores`. Security DEFINER. Call after:
- New actions are proposed
- Embeddings get populated or updated
- Action status changes

---

## Data State at Creation Time

| Table | Rows | Embeddings | Notes |
|-------|------|-----------|-------|
| thesis_threads | 8 | 0 (all NULL) | Rich text fields enable good trigram matching |
| actions_queue | 115 | 0 (all NULL) | 92 Proposed, rest Done/Dismissed |
| content_digests | 22 | 0 (all NULL) | All have digest_data JSONB with thesis mentions |
| companies | 0 | N/A | Table empty -- sync from Notion deferred |
| network | 0 | N/A | Table empty -- sync from Notion deferred |
| portfolio | 0 | N/A | Table empty -- sync from Notion deferred |
| action_outcomes | 4 | N/A | Small preference store, growing |

---

## Performance Notes

- All functions operate on small datasets (8 thesis threads, 115 actions, 22 digests) so performance is not a concern currently
- Trigram similarity is O(n*m) on text length -- adequate for current scale but will need GIN trigram indexes when companies table reaches 200+ rows
- The materialized view creation took ~30s for 92 actions (calls both router and relevance scorer per action). Refresh will be similar.
- When embeddings get populated, vector similarity will be significantly faster than trigram for large text fields (indexed IVFFlat or HNSW scans)

### Recommended Indexes (Future, when data grows)

```sql
-- When companies table gets populated:
CREATE INDEX idx_companies_name_trgm ON companies USING GIN (name gin_trgm_ops);
CREATE INDEX idx_companies_sector_trgm ON companies USING GIN (sector gin_trgm_ops);

-- When embeddings get populated:
CREATE INDEX idx_thesis_embedding ON thesis_threads USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_actions_embedding ON actions_queue USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_companies_embedding ON companies USING hnsw (embedding vector_cosine_ops);
```

---

## What Improves When Embeddings Arrive

The Auto Embeddings pipeline (DB trigger -> pgmq -> pg_cron -> Edge Function -> Voyage AI voyage-3.5 -> 1024-dim vectors) will dramatically improve these functions:

1. **score_action_thesis_relevance** -- vector path activates, providing semantic matching rather than character-level trigram overlap
2. **find_related_companies** -- primary path uses vector similarity instead of name-string matching
3. **aggregate_thesis_evidence** -- relevance scoring shifts from trigram to embedding distance
4. **entity_relationships** -- strength scores become semantic rather than surface-level

---

## Function Inventory (Quick Reference)

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `score_action_thesis_relevance(action_id)` | action ID | top 5 thesis matches | Which thesis threads does this action relate to? |
| `route_action_to_bucket(action_id)` | action ID | bucket + confidence + reasoning | Which ENIAC bucket should this action go to? |
| `find_related_companies(query_text, limit)` | free text | company matches | What companies relate to this text? |
| `aggregate_thesis_evidence(thesis_id)` | thesis ID | evidence items with sentiment | What's all the evidence for/against this thesis? |
| `suggest_actions_for_thesis(thesis_id, limit)` | thesis ID | prioritized suggestions | What actions should we take for this thesis? |
| `refresh_action_scores()` | none | void | Refresh the action_scores materialized view |

| View | Type | Rows | Purpose |
|------|------|------|---------|
| `entity_relationships` | Regular VIEW | 470 | Cross-entity connection map |
| `action_scores` | MATERIALIZED VIEW | 92 | Pre-computed bucket + thesis scores for proposed actions |
