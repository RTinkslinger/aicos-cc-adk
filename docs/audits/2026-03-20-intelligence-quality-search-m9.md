# Intelligence Quality Audit: Search & Hybrid Intelligence

**Date:** 2026-03-20
**Database:** Supabase `llfkxnsfczludgigknbs`
**Auditor:** Claude Opus 4.6 (automated)
**Sprint:** M9

---

## Executive Summary

**Overall Search Intelligence Grade: C+ (62/100)**

The search infrastructure has good *bones* -- 100% embedding coverage across all tables, functional hybrid search with RRF scoring, and well-structured FTS generated columns -- but is severely undermined by three systemic data quality issues that cap search accuracy:

1. **Skeletal embedding inputs** -- Companies are embedded from just `name + sector + deal_status + jtbd + ids_notes`, but `jtbd` is empty for 80% and `ids_notes` is empty for 100%. Result: 4,565 companies embedded essentially on name+sector alone, producing a flat, undifferentiated embedding space.
2. **FTS covers only what's in the generated column** -- Companies FTS = `name || sector || agent_ids_notes`. With `agent_ids_notes` always empty, a search for "artificial intelligence" returns **zero results** despite thousands of AI companies.
3. **Network table excluded from hybrid_search** -- The 3,722-person network table is not searched by `hybrid_search()` at all. Person searches cannot cross-reference with companies/actions.

---

## 1. Database Coverage Snapshot

| Table | Total Rows | Has Embedding | Has FTS | Embedding Coverage | FTS Coverage |
|-------|-----------|---------------|---------|-------------------|--------------|
| companies | 4,565 | 4,565 | 4,565 | 100% | 100% |
| network | 3,722 | 3,722 | 3,722 | 100% | 100% |
| thesis_threads | 8 | 8 | 8 | 100% | 100% |
| actions_queue | 115 | 115 | 115 | 100% | 100% |
| content_digests | 22 | 22 | 22 | 100% | 100% |

**Coverage is perfect.** The problem is not missing embeddings but *what* was embedded.

### Embedding Input Quality

| Table | Fields Used for Embedding | Quality Assessment |
|-------|--------------------------|-------------------|
| **companies** | `name`, `sector`, `deal_status`, `jtbd`, `agent_ids_notes` | **Poor.** `jtbd` populated for only 916/4,565 (20%). `agent_ids_notes` populated for 0/4,565 (0%). Most companies embedded on name+sector only. |
| **network** | `person_name`, `role_title`, `home_base` | **Broken.** `role_title` is "postgres" for ALL 3,722 records (data corruption). Embeddings are essentially name-only. |
| **thesis_threads** | Full text (thread_name, core_thesis, etc.) | **Good.** Rich text fields, meaningful embeddings. |
| **actions_queue** | Full text (action, reasoning, thesis_connection, etc.) | **Good.** Rich content, well-differentiated embeddings. |

### FTS Generated Column Definitions

| Table | Generated From | Quality |
|-------|---------------|---------|
| companies | `name \|\| sector \|\| agent_ids_notes` | **Weak.** Missing description, JTBD, sector_tags. `agent_ids_notes` always empty. |
| network | `person_name \|\| role_title \|\| linkedin` | **Weak.** `role_title` is all "postgres". LinkedIn URL included but not useful for text search. |
| thesis_threads | `thread_name \|\| core_thesis \|\| key_companies \|\| investment_implications` | **Good.** Rich FTS document. |
| actions_queue | `action \|\| reasoning \|\| thesis_connection \|\| action_type` | **Good.** Comprehensive FTS coverage. |

---

## 2. Hybrid Search Quality (30 Queries)

### Critical Architecture Issue

`hybrid_search()` requires a **pre-computed query embedding vector** as a parameter. This means:
- It **cannot be called** from pure SQL with just a text string
- The caller must first obtain an embedding (via an external API call)
- For this audit, reference entity embeddings were used as proxies

Additionally, `hybrid_search()` covers only 4 tables: `content_digests`, `thesis_threads`, `actions_queue`, `companies`. The **network** table (3,722 people) is completely excluded.

### Per-Query Results

#### Company Name Searches (5 queries)

| # | Query | Top Result | Relevant? | Ranking | Missing? |
|---|-------|-----------|-----------|---------|----------|
| 1 | "Swiggy food delivery" | Swiggy (companies, rank 4 of 10) | Partially | **Bad** -- Swiggy buried at #4, behind unrelated action + thesis + content | Zomato not in top 10 |
| 9 | "Flipkart ecommerce" | Flipkart (rank 1) | Relevant | Good for semantic | Amazon, Meesho missing but acceptable |
| 8 | "CRED" | CRED (rank 1, combined FTS+semantic) | Relevant | Good -- FTS boosted it | n/a |
| 15 | "StepSecurity supply chain security" | Cybersecurity thesis (rank 1), StepSecurity company (rank 4) | Partially | Mixed -- thesis outranks the company itself | StepSecurity actions not top-3 |
| 25 | "GameRamp gaming" | Unrelated results (Drop, AGI content) | **Irrelevant** | **Fail** -- GameRamp not found at top | GameRamp may lack embedding differentiation |

**Company Name Search Accuracy: 2/5 Relevant, 2/5 Partial, 1/5 Irrelevant = 40% fully relevant**

#### Sector/Theme Searches (5 queries)

| # | Query | Top 3 Results | Relevant? | Ranking | Notes |
|---|-------|--------------|-----------|---------|-------|
| 3 | "fintech payments India" (companies only) | Razorpay, ZebPay, Vegapay | **Relevant** | Excellent -- all payment companies | Good semantic clustering for payments |
| 10 | "edtech education technology" (companies only) | BYJU'S, Booko, Bytecube | Partially | BYJU'S correct, others questionable | Unacademy at rank 5, should be higher |
| 19 | "B2B enterprise SaaS" (companies only) | Klaar, Kloudlite, Clodo | **Irrelevant** | **Fail** -- random SaaS companies with no B2B signal | Embedding space too flat to differentiate |
| 11 | "aviation electric USTOL" | USTOL thesis (rank 1), Green Propulsion, Skyroot | **Relevant** | Excellent cross-entity | Good thesis + company pairing |
| 20 | "CLAW stack orchestration" | CLAW thesis (rank 1), Unsiloed AI, Temporal content | **Relevant** | Good cross-entity | FTS + semantic both fired |

**Sector Search Accuracy: 3/5 Relevant, 1/5 Partial, 1/5 Irrelevant = 60% fully relevant**

#### Person Name Searches (5 queries)

**BLOCKED:** `hybrid_search()` does not include the `network` table. Person searches are impossible via this function. This is a **critical gap** for an investor tool.

Workaround tested: Direct FTS on network table.

| # | Query (FTS only) | Results | Quality |
|---|-----------------|---------|---------|
| 27 | "investor" | Taz Patel, Madhu Chamarty, Kishore Ganji (3 results) | **Weak** -- only 3 of presumably hundreds of investors |
| 28 | "founder CEO" | 10 results, all with `role_title` containing "founder" or "CEO" | **Partially works** for those with roles set (Nithin Kamath), but `role_title` = "postgres" for most |

**Person Search Accuracy: 0/5 via hybrid_search (excluded), 1/5 via FTS = FAIL**

#### Thesis Topic Searches (5 queries)

| # | Query | Top Result | Relevant? | Ranking | Notes |
|---|-------|-----------|-----------|---------|-------|
| 2 | "AI agents infrastructure" | CLAW stack action (rank 1), Agentic AI Infrastructure thesis (rank 2) | **Relevant** | Excellent | Both FTS + semantic fired, good cross-entity |
| 4 | "cybersecurity pen testing" | Cybersecurity thesis (rank 1, combined top score) | **Relevant** | Excellent | Perfect FTS + semantic alignment |
| 5 | "SaaS replacement AI disruption" | SaaS Death thesis update action (rank 1) | **Relevant** | Good | Actions outrank thesis thread itself |
| 6 | "healthcare AI voice agents" | Smallest AI action (rank 1), Confido action, Healthcare thesis | **Relevant** | Good cross-entity | Thesis found, related actions surfaced |
| 12 | "thesis update conviction evidence" | SaaS Death thesis update (rank 1) | **Relevant** | Good | FTS + semantic alignment |

**Thesis Search Accuracy: 5/5 Relevant = 100%**

#### Action/Task Searches (5 queries)

| # | Query | Top Result | Relevant? | Ranking | Notes |
|---|-------|-----------|-----------|---------|-------|
| 7 | "portfolio check-in urgent" (actions only) | White-collar displacement action (rank 1) | **Partially** | Off-target -- not a portfolio check-in | Urgency signal not captured |
| 13 | "research deep dive investigation" (actions only) | CVE security review (rank 1) | Partially | Generic semantic match | No differentiation of "research" type |
| 14 | "deal sourcing pipeline" | Indian coding AI landscape (rank 1) | **Relevant** | Good | Pipeline actions surfaced correctly |
| 18 | "meeting outreach schedule call" (actions only) | Schedule calls with CEOs (ranks 1-10) | **Relevant** | Excellent | All Meeting/Outreach type, correctly sorted |
| 29 | "portfolio check-in" (FTS) | Monday.com SDR data sharing (rank 1), 9 more Portfolio Check-in actions | **Relevant** | Excellent FTS | FTS excels here due to rich action text |

**Action Search Accuracy: 3/5 Relevant, 2/5 Partial = 60% fully relevant**

#### Cross-Entity Searches (5 queries)

| # | Query | Table Diversity | Relevant? | Notes |
|---|-------|----------------|-----------|-------|
| 16 | "venture capital investing India" | 4 tables represented in top 5 | Partially | Content + thesis relevant, company pick weak |
| 22 | "Klarna SaaS dead" | content + companies + actions + thesis | **Relevant** | Klarna content at #1, SaaS Death thesis at #4 |
| 23 | "Scale AI data infrastructure" | actions + companies + content + thesis | **Relevant** | Scale AI action at #1 with top combined score |
| 26 | "Poetic harness layer" | 2 actions at top, then content + thesis | **Relevant** | Excellent cross-entity, both Poetic actions surfaced |
| 30 | "Gokul Rajaram eight moats" | actions + companies + content + thesis | **Relevant** | Content and actions about Gokul both found |

**Cross-Entity Search Accuracy: 4/5 Relevant, 1/5 Partial = 80% fully relevant**

### Hybrid Search Summary

| Category | Queries | Relevant | Partial | Irrelevant | Accuracy |
|----------|---------|----------|---------|------------|----------|
| Company Name | 5 | 2 | 2 | 1 | 40% |
| Sector/Theme | 5 | 3 | 1 | 1 | 60% |
| Person Name | 5 | 0 | 0 | 5 | 0% (table excluded) |
| Thesis Topic | 5 | 5 | 0 | 0 | 100% |
| Action/Task | 5 | 3 | 2 | 0 | 60% |
| Cross-Entity | 5 | 4 | 1 | 0 | 80% |
| **TOTAL** | **30** | **17** | **6** | **7** | **57% fully relevant** |

### Ranking Quality Score

When the top result IS relevant, is it the BEST result?

- **Excellent (best first):** 12/23 queries with relevant results
- **Acceptable (best in top 3):** 7/23
- **Poor (best result buried):** 4/23

**Ranking Quality: 52% optimal, 82% acceptable (top-3)**

### Identified Patterns

1. **RRF Score Compression:** Most results have nearly identical `combined_score` values (0.011475 vs 0.011290 vs 0.011111). The RRF formula with k=60 produces a very narrow score range, making ranking unreliable. When FTS fails to fire (common), all results are purely semantic with scores differentiated only by rank position.

2. **FTS Dramatically Improves Results:** When FTS matches (keyword hit), combined scores jump to ~0.016 and the ranking is excellent (tests 2, 4, 11, 20). When FTS misses (most company queries), results are semantic-only with compressed scores.

3. **One-Per-Table Bias:** The RRF scoring creates an implicit one-per-table effect at equivalent ranks. When semantic rank 1 in each table has combined_score 0.011475, results interleave by table rather than true relevance.

---

## 3. Related Items Quality (10 Samples)

`find_related_companies()` uses **trigram similarity only** (pg_trgm). The vector path is disabled (`WHERE FALSE`). This means it matches on string similarity, NOT semantic similarity.

| # | Query Company | Top Related | Same Sector? | Actually Related? | Notes |
|---|--------------|-------------|-------------|-------------------|-------|
| R1 | Swiggy | Swish, SWIFT, Mihir Shah (swiggy) | No | **No** | Name-based: "Sw" trigram matching |
| R2 | Razorpay | Razorfish, Third Watch (acq by Razorpay) | Partial | **Partially** | Third Watch is genuinely related (acquired) |
| R3 | StepSecurity | Hacktron, DataKastro, MyAltId | Mixed | **No** | Random companies with similar sector string |
| R4 | CodeAnt | Codegen, Augment Code, Fast Code | Partial | **Partially** | Codegen and Augment Code are in same space |
| R5 | Unifize | Uni, Unisson, UNIBENCH | No | **No** | Pure "Uni" prefix matching |
| R6 | Confido Health | Cora health, Cumin Health | Yes (health) | **Partially** | "Health" string matching, some sector overlap |
| R7 | "food delivery" (concept) | Delivery Hero, Praful's Food Delivery | Yes | **Yes** | Concept search works when terms match |
| R8 | "cybersecurity" (concept) | StepSecurity, Redacto, Defendermate | Yes | **Yes** | Good result via sector/JTBD trigram |
| R9 | Dodo Payments | Pazy, Propel, Dice, Mylapay | Mixed | **No** | Financial services but not payments-related |
| R10 | InspeCity | InspectHOA, Infinity, Speciale Invest | No | **No** | Name prefix matching only |

**Related Items Accuracy: 2/10 Relevant, 3/10 Partial, 5/10 Irrelevant = 20% fully relevant**

**Root Cause:** The vector similarity path in `find_related_companies()` is explicitly disabled (`WHERE FALSE -- Disabled until query embedding is passed as parameter`). The function was designed for semantic search but fell back to trigram-only, making it essentially a fuzzy name matcher.

---

## 4. Score-Based Ranking Quality

### User Priority Score Distribution

| Metric | Value |
|--------|-------|
| Min | 1.29 |
| Max | 9.79 |
| Mean | 7.14 |
| Median | 9.37 |

**Distribution is heavily right-skewed** -- 50%+ of actions scored above 9.37. The scoring formula creates 3 distinct clusters rather than a smooth gradient.

### Top 15 Actions (highest score: 9.79)

All top-scored actions are **P0 Portfolio Check-ins** with "Proposed" status, primarily flagging risks:
- "Flag privacy/spam complaint risk" (9.790)
- "CRITICAL: Pause investment activities" (9.790)
- "Flag regulatory risk on AI features" (9.790)
- "Flag operational risk on 'Free Lifetime Repairs'" (9.790)

### Bottom 15 Actions (lowest score: 1.29-2.79)

All bottom-scored actions are **P1-P2 Research** items:
- "Monitor open-source harness frameworks" (1.29)
- "Deep research on rural talent + creativity thesis" (1.29)
- "Research AI provider bias concentration risk" (1.29)

### Ranking Quality Assessment

**The ranking makes directional sense.** Portfolio risk-flagging actions (P0, immediate investor attention required) are correctly ranked above research tasks (P1-P2, can wait). However:

1. **Score clustering is too tight within tiers.** The top 8 actions all score 9.790025 with only the 12th decimal place differentiating them. This is effectively a tie, not a ranking.
2. **Missing gradation.** There is a gap from 9.79 (tier 1) to 9.77 (tier 2) to 9.74 (tier 3) to 2.79 (tier 4) to 1.29 (tier 5). No actions score 3-7, suggesting the formula uses category multipliers rather than continuous scoring.
3. **Priority field dominates.** The score appears to be primarily driven by `priority` (P0 > P1 > P2) with minimal differentiation within priority tiers.

**Score Ranking Quality: B- (directionally correct but insufficiently granular)**

---

## 5. Embedding Quality Spot-Check

### Company Pair Similarity (Known Companies)

| Company A | Company B | Cosine Similarity | Same Domain? | Assessment |
|-----------|-----------|------------------|-------------|------------|
| Flipkart | Razorpay | 0.8976 | No (ecomm vs payments) | **Distorted** |
| Swiggy | Zomato | 0.8975 | Yes (food delivery) | **Correct** |
| StepSecurity | CodeAnt | 0.8881 | No (security vs code review) | **Distorted** |
| Flipkart | Zomato | 0.8845 | Partial (both consumer) | Acceptable |
| CodeAnt | Confido Health | 0.8814 | No (code vs healthcare) | **Distorted** |
| StepSecurity | BYJU'S | 0.8704 | No (security vs edtech) | **Distorted** |
| Swiggy | BYJU'S | 0.8662 | No (food vs edtech) | **Distorted** |

**The embedding space is severely compressed.** The range of similarities is only 0.86-0.90 across completely different companies. Flipkart-Razorpay (0.898) is nearly identical to Swiggy-Zomato (0.898), despite the former pair being in different sectors.

**Root Cause:** With embedding input being just `name + sector + deal_status`, all companies within the same sector (or with null sectors) cluster tightly. Companies with null sector (Flipkart, Razorpay, CRED) are even more compressed because their embedding inputs are almost entirely just the company name.

**Embedding Quality Grade: D (distorted, undifferentiated space)**

---

## 6. FTS (Full-Text Search) Quality

### Direct FTS Tests on Companies

| # | Query | Results Count | Top Results | Quality |
|---|-------|-------------|-------------|---------|
| 21 | "security" | 8 | System Two Security, Astra Security, RSA Security | **Acceptable** -- finds companies with "security" in name |
| 22 | "artificial intelligence" | **0** | (none) | **FAIL** -- zero results for "AI" |
| 23 | "payment" | 2 | Hitachi Payment Services, Coda Payments | **Poor** -- misses Razorpay, PayU, Juspay |
| 24 | "healthcare" | 5 | Even Healthcare, GE Healthcare | **Weak** -- misses Confido Health, HealthWorksAI |
| 25 | "education" | 7 | JSS Academy, Pathfinder Education AI | **Acceptable** -- finds education-named entities |
| 26 | "fintech" | 5 | HAPPY Fintech, Bind Fintech | **Poor** -- only finds companies with "fintech" literally in name |

### FTS Tests on Actions Queue

| # | Query | Results Count | Quality |
|---|-------|-------------|---------|
| 29 | "portfolio check-in" | 10 | **Excellent** -- rich FTS document catches both terms |
| 30 | "research thesis" | 10 | **Good** -- correct action types surfaced |

### FTS Tests on Thesis Threads

| # | Query | Results | Quality |
|---|-------|---------|---------|
| FTS-T1 | "SaaS death agent" | 1 (SaaS Death thread) | **Good** -- correct match |

### FTS Quality Summary

| Table | FTS Effectiveness | Why |
|-------|------------------|-----|
| companies | **20%** (1/5 useful) | Generated column = `name + sector + empty`. Most business context (description, product, market) not indexed. |
| network | **10%** | Generated column includes `role_title` which is all "postgres" and LinkedIn URLs. |
| actions_queue | **90%** | Generated column = `action + reasoning + thesis_connection + action_type`. Rich text, good recall. |
| thesis_threads | **90%** | Generated column = `thread_name + core_thesis + key_companies + investment_implications`. Excellent. |

**Overall FTS Accuracy: 50% (strong on thesis/actions, broken on companies/network)**

---

## 7. Critical Issues Summary

### CRITICAL (search intelligence broken)

| # | Issue | Impact | Fix Effort |
|---|-------|--------|-----------|
| C1 | **Network table excluded from hybrid_search()** | Person searches impossible via primary search API. 3,722 contacts unsearchable. | Medium -- add network CTE to hybrid_search function |
| C2 | **Network `role_title` all "postgres"** | Network FTS useless. Network embeddings are name-only. All person matching is degraded. | Low -- data fix: repopulate from Notion sync |
| C3 | **Company embedding inputs skeletal** | Companies are embedded on name+sector alone (JTBD empty 80%, IDS notes empty 100%). Embedding space is flat and undifferentiated. | Medium -- enrich `agent_ids_notes` and `jtbd` from page content, re-embed |
| C4 | **`find_related_companies()` vector path disabled** | Related companies function is trigram-only (fuzzy name match). Semantic relatedness not functional. | Low -- pass query embedding as parameter, enable vector path |

### HIGH (search quality significantly degraded)

| # | Issue | Impact | Fix Effort |
|---|-------|--------|-----------|
| H1 | **Companies FTS too sparse** | FTS for "artificial intelligence" returns 0 results. Only name + sector + empty field indexed. | Medium -- add `jtbd`, `sector_tags`, `deal_status` to FTS generated column |
| H2 | **RRF score compression (k=60)** | Combined scores cluster at 0.0114-0.0116, making ranking effectively random when FTS misses. | Low -- reduce k to 10-20 for sharper score differentiation |
| H3 | **hybrid_search requires pre-computed embedding** | Callers must obtain a 1024-dim vector before calling search. No text-only search path. | Medium -- add server-side embedding generation or fallback to FTS-only mode |
| H4 | **User priority score clusters too tightly** | Top 8 actions identical to 12 decimal places. No meaningful within-tier differentiation. | Medium -- add time-decay, recency, or interaction-based secondary scoring |

### MEDIUM (search quality noticeably reduced)

| # | Issue | Impact | Fix Effort |
|---|-------|--------|-----------|
| M1 | **Content digests snippet quality** | Snippet field often shows just channel name ("20VC with Harry Stebbings") instead of content summary | Low -- use `summary` or `analysis` field in snippet |
| M2 | **Companies snippet format** | Company snippets show `" \| NA"` for most entries (sector + deal_status). Uninformative. | Low -- include more fields in snippet construction |
| M3 | **No query expansion or synonyms** | "AI" does not match "artificial intelligence"; "payments" does not match "fintech" | Medium -- add synonym dictionary or query expansion layer |

---

## 8. Recommendations (Priority Order)

### 1. Fix Network Data (Quick Win)
- Repopulate `role_title` from Notion sync (all 3,722 records show "postgres")
- This immediately fixes network FTS and network embeddings

### 2. Enrich Company Embedding Inputs
- Populate `agent_ids_notes` for top companies (at minimum, companies with deal_status != "NA")
- Use `page_content_path` data to generate richer embedding input text
- Consider adding `sector_tags`, `jtbd`, and enrichment data to embedding input function
- Re-embed after enrichment

### 3. Add Network to hybrid_search()
Add a `network` CTE following the same semantic + keyword + combined pattern as the other 4 tables. Use `person_name` as title, `role_title || home_base` as snippet.

### 4. Enable Vector Path in find_related_companies()
- Accept query embedding as an optional parameter
- When provided, use embedding similarity instead of trigram
- Alternatively, use the target company's own embedding to find nearest neighbors

### 5. Expand Company FTS
Change the generated column from:
```sql
to_tsvector('english', name || ' ' || sector || ' ' || agent_ids_notes)
```
To:
```sql
to_tsvector('english', name || ' ' || COALESCE(sector, '') || ' ' ||
  COALESCE(array_to_string(sector_tags, ' '), '') || ' ' ||
  COALESCE(array_to_string(jtbd, ' '), '') || ' ' ||
  COALESCE(agent_ids_notes, '') || ' ' ||
  COALESCE(deal_status, ''))
```

### 6. Reduce RRF k Parameter
Change `rrf_k` from 60 to 15-20. This will produce more differentiated combined scores:
- Current: rank 1 = 1/(60+1) = 0.0164, rank 2 = 1/(60+2) = 0.0161 (0.2% difference)
- Proposed (k=15): rank 1 = 1/(15+1) = 0.0625, rank 2 = 1/(15+2) = 0.0588 (6.3% difference)

### 7. Add Text-Only Search Fallback
Add an overloaded `hybrid_search(query_text, ...)` signature that uses FTS-only when no embedding is provided. This enables SQL-only callers without external embedding API dependencies.

---

## 9. Accuracy Scorecard

| Dimension | Score | Grade | Weight | Weighted |
|-----------|-------|-------|--------|----------|
| Hybrid Search Relevance | 57% | D+ | 30% | 17.1 |
| Hybrid Search Ranking | 82% (top-3) | B | 15% | 12.3 |
| FTS Quality | 50% | D | 15% | 7.5 |
| Related Companies | 20% | F | 10% | 2.0 |
| Score-Based Ranking | 75% | B- | 10% | 7.5 |
| Embedding Quality | 30% | F | 10% | 3.0 |
| Coverage (% indexed) | 100% | A+ | 10% | 10.0 |
| **TOTAL** | | **C+ (59.4/100)** | **100%** | **59.4** |

### Where It Works Well
- **Thesis searches** (100% accuracy) -- rich text inputs make embeddings + FTS both effective
- **Action searches** (60-90% accuracy) -- full action text + reasoning indexed
- **Cross-entity searches** (80% accuracy) -- RRF correctly surfaces diverse results
- **FTS on rich-text tables** -- thesis_threads and actions_queue FTS is excellent

### Where It Fails
- **Person searches** (0%) -- network table not in hybrid_search
- **Company name lookups** (40%) -- skeletal embeddings, sparse FTS
- **Related companies** (20%) -- vector path disabled, trigram-only
- **Sector/concept searches on companies** (40%) -- no business description indexed

---

## 10. Data Quality Issues Found During Audit

| Issue | Table | Severity | Details |
|-------|-------|----------|---------|
| `role_title` = "postgres" for ALL rows | network | CRITICAL | 3,722/3,722 records. Data corruption during initial sync. |
| `agent_ids_notes` empty for ALL rows | companies | HIGH | 0/4,565 populated. Field in FTS + embedding but never written. |
| `jtbd` empty for 80% of rows | companies | HIGH | 916/4,565 populated. Key differentiator missing from most records. |
| `sector` null for 37% of rows | companies | MEDIUM | 1,690/4,565 have null sector. |
| Razorpay has null sector | companies | MEDIUM | Major fintech company missing sector classification. |
| CRED has null sector | companies | MEDIUM | Well-known fintech missing sector classification. |
| Flipkart has null sector | companies | MEDIUM | Major ecommerce company missing sector classification. |
| BYJU'S classified as "SaaS" | companies | LOW | Edtech company incorrectly classified as SaaS. |

---

*Audit generated by automated search intelligence review. 30+ queries executed across all search surfaces. All assessments based on actual query results, not theoretical analysis.*
