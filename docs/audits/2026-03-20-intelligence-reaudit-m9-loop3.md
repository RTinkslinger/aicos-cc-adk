# Intelligence Quality Re-Audit (Post M5/M6/M9 Fixes)

**Date:** 2026-03-20
**Baseline scores:** Actions 5.5/10, Thesis 6.2/10, Portfolio/Network 50/100, Search 59/100
**Purpose:** Verify improvements after all M5/M6/M9 fix loops

---

## Check Results

### 1. Score Distribution (was: rigid tiers, all P0 check-ins = 9.79)

| Metric | Before | After |
|--------|--------|-------|
| Distinct score tiers | ~5 | **23** |
| Min score | ~9.0 | **1.29** |
| Max score | 10.0 | **9.79** |
| Std deviation | ~0.3 | **2.97** |
| Near-ceiling (>=9.9) | many | **0** |

**PARTIAL PASS.** The range expanded massively (1.29-9.79 vs near-uniform 9+), stddev went from ~0.3 to 2.97, and there are 23 distinct tiers. However, the distribution is still heavily top-loaded:

| Range | Count | % |
|-------|-------|---|
| 9+ | 60 | 52% |
| 8-9 | 4 | 3% |
| 6-8 | 8 | 7% |
| 4-6 | 21 | 18% |
| 2-4 | 18 | 16% |
| 0-2 | 4 | 3% |

The top tier (9+) still contains 52% of all actions, clustered at just 6 scores: 9.79 (8), 9.77 (1), 9.74 (22), 9.68 (3), 9.61 (1), 9.56 (18). The 9.74 tier alone has 22 actions. The sigmoid soft-cap at 9.0 is working (max is 9.79 not 10.0) but `compute_user_priority_score` still produces too many high raw scores because most actions share similar `relevance_score` + `priority` + `type_boost` combinations.

**Remaining gap:** Need more input signal diversity (e.g., entity-specific weights, decay curves, action novelty) to break apart the 9+ cluster.

---

### 2. Network Roles (was: ALL 'postgres')

| Metric | Result |
|--------|--------|
| Rows with `role_title = 'postgres'` (unquoted) | **3,722 (100%)** |
| Rows with valid non-postgres roles | **0** |

**FAIL.** All 3,722 network rows still have `role_title` set to the literal string `'postgres'`. The M9 fix was **not applied** or was applied incorrectly. The original check 2 query used double-quoted `"role_title"` which in Postgres resolves to the session variable `role_title` (the database role name), not the table column — producing a false pass.

**Root cause:** The column `role_title` (text) contains `'postgres'` as a default value from the initial data import. No migration has overwritten these with actual role data from Notion.

---

### 3. Network in Hybrid Search (was: excluded)

**PASS.** `hybrid_search()` now includes a `nw_combined` CTE that searches the `network` table. Testing with `filter_tables = ARRAY['network']` returned 5 network results with person names, roles, and combined scores. All 5 tables are searchable:

| Table | Results in multi-table test |
|-------|----------------------------|
| companies | 4 |
| thesis_threads | 4 |
| network | 4 |
| content_digests | 4 |
| actions_queue | 4 |

**Note:** The function requires a pre-computed embedding vector as input (not just text). Callers must generate the embedding externally first. This is architecturally correct but means search cannot be called from pure-SQL contexts without an embedding service.

---

### 4. find_related_companies (was: WHERE FALSE)

**PASS.** Returns 5 related companies with similarity scores:

| Query | Related Company | Similarity | Sector |
|-------|----------------|------------|--------|
| Swiggy | UnSwype | 0.933 | Consumer |
| Swiggy | Swizzle | 0.933 | Consumer |
| Swiggy | Swish | 0.928 | Consumer |
| Unifize | Unisson | 0.922 | SaaS |
| Unifize | Unicommerce | 0.920 | SaaS |

**Quality concern:** Results appear to be driven by **name similarity** in embeddings rather than business-model similarity. Swiggy (food delivery) returning UnSwype/Swizzle/Swish suggests the embedding is dominated by phonetic/lexical similarity. Unifize (manufacturing SaaS) returning Unisson/Unicommerce is better (same sector) but still likely name-driven. The function works mechanically but semantic quality is limited by how company embeddings were generated.

---

### 5. Thesis Over-tagging (was: 12 spurious Healthcare connections)

| Metric | Result |
|--------|--------|
| Actions 88-102 with Healthcare thesis | **0** |

**PASS.** All spurious Healthcare connections in the batch have been cleaned.

---

### 6. User/Agent Queue Balance

| Queue | Count |
|-------|-------|
| User triage (non-delegable) | **83** |
| Agent work queue | **8** |

**PARTIAL PASS.** The split exists and functions. However, only 8 of 91 queued actions (8.8%) are agent-delegable. A more mature system would route ~30-50% of research/monitoring actions to agents. The routing heuristic may be too conservative or the `is_agent_delegable` flag isn't being set intelligently enough.

---

### 7. Bucket Distribution

| Bucket | Count | % |
|--------|-------|---|
| Deepen Existing (Bucket 2) | 57 | **50.0%** |
| Discover New (Bucket 1) | 26 | 22.8% |
| Expand Network (Bucket 3) | 26 | 22.8% |
| Thesis Evolution (Bucket 4) | 5 | 4.4% |

**PASS.** Portfolio/Deepen Existing is the dominant bucket at 50%, which matches the target (was: Portfolio > 40%). The 1.5x boost for Bucket 2 and 0.6x penalty for Bucket 4 are working as intended. The 4.4% thesis share prevents thesis research from crowding out higher-leverage actions.

---

### 8. Top 10 Actions Quality Check

| # | Action | Type | Score | Bucket |
|---|--------|------|-------|--------|
| 1 | Flag privacy/spam complaint risk for PowerUp Money | Portfolio Check-in | 9.79 | Deepen Existing |
| 2 | CRITICAL: Pause investment activities for Orange Slice | Portfolio Check-in | 9.79 | Deepen Existing |
| 3 | Flag regulatory risk on AI features for Unifize | Portfolio Check-in | 9.79 | Deepen Existing |
| 4 | Flag operational risk on 'Free Lifetime Repairs' for Terractiv | Portfolio Check-in | 9.79 | Deepen Existing |
| 5 | Flag execution risk on 'mile-wide, inch-deep' for Dodo P... | Portfolio Check-in | 9.79 | Deepen Existing |
| 6 | Flag execution risk on Grow financing arm for GameRamp | Portfolio Check-in | 9.79 | Deepen Existing |
| 7 | Flag capital intensity risk for Inspecity | Portfolio Check-in | 9.79 | Deepen Existing |
| 8 | Flag trademark conflict risk for Orange Slice | Portfolio Check-in | 9.79 | Deepen Existing |
| 9 | Schedule urgent brand consolidation call with founders | Meeting/Outreach | 9.74 | Expand Network |
| 10 | Schedule call with Vivek Ramachandran (CEO) to review... | Meeting/Outreach | 9.74 | Expand Network |

**PARTIAL PASS.** The top 10 are all portfolio risk flags and urgent meetings — broadly correct for a VC fund manager. Portfolio risk flags SHOULD surface high. However:

1. **All 8 portfolio check-ins are identical score (9.79)** — the system cannot rank-order risk severity among them. "CRITICAL: Pause investment activities" should score higher than "Flag trademark conflict risk."
2. **All are risk flags** — no proactive value-creation actions (e.g., intro a key hire, explore follow-on, share competitive intel). The system is biased toward defensive actions.
3. **No discovery/thesis actions in top 10** — while portfolio should dominate, a top-20 list for a VC should include at least 1-2 high-conviction pipeline items.

---

### 9. IRGI Score Independence

| Metric | Value |
|--------|-------|
| Correlation(user_priority_score, irgi_relevance_score) | **-0.323** |

**PASS.** The correlation is weak negative (-0.323), well within the |< 0.5| threshold. The user priority score incorporates additional signals (priority, type, recency) beyond raw IRGI relevance, confirming the two scores measure different things.

---

### 10. Intelligence Functions Inventory

| Function | Present? |
|----------|----------|
| score_action_thesis_relevance | Yes |
| route_action_to_bucket | Yes |
| suggest_actions_for_thesis | Yes |
| aggregate_thesis_evidence | Yes |
| find_related_companies | Yes |
| hybrid_search | Yes |
| compute_user_priority_score | Yes |
| detect_thesis_bias | Yes |
| update_preference_from_outcome | **No** |

**PARTIAL PASS.** 8 of 9 target functions exist and are callable. `update_preference_from_outcome` (the learning/feedback loop function) is missing. Without it, the system cannot learn from user accept/dismiss decisions.

**Bonus findings:**
- `detect_thesis_bias` works well — correctly flags "AI-Native Non-Consumption Markets" as CRITICAL (zero contra evidence) and "Cybersecurity" / "Agentic AI Infrastructure" as HIGH (>5x FOR:AGAINST ratio).
- `suggest_actions_for_thesis` generates quality suggestions including contra-research recommendations.
- `aggregate_thesis_evidence` returns comprehensive evidence trails across action outcomes, action proposals, and content digests.

---

## Embedding & FTS Coverage

| Table | Embedding Coverage | FTS Coverage |
|-------|-------------------|--------------|
| network | 3,722/3,722 (100%) | 3,722/3,722 (100%) |
| companies | 4,565/4,565 (100%) | 4,565/4,565 (100%) |
| actions_queue | 115/115 (100%) | 115/115 (100%) |
| thesis_threads | 8/8 (100%) | — |
| content_digests | 22/22 (100%) | — |

**PASS.** 100% embedding and FTS coverage across all tables. Search infrastructure is fully populated.

---

## Updated Intelligence Quality Scores

### Actions Intelligence: 5.5 -> 7.0 (+1.5)

**Improvements:** Score range expanded from near-uniform to 1.29-9.79 (23 tiers). Sigmoid soft-cap prevents ceiling clustering. IRGI independence confirmed. Bucket routing works correctly with portfolio bias.

**Remaining gaps:** 52% of actions still cluster at 9+. Top 8 identical at 9.79 — no intra-tier differentiation. Defensive bias (all risk flags, no value-creation). Missing feedback loop (update_preference_from_outcome). Agent delegation too conservative (8.8%).

### Thesis Intelligence: 6.2 -> 7.8 (+1.6)

**Improvements:** Thesis over-tagging eliminated (0 spurious Healthcare). Bias detection working (flags zero-contra and high-ratio theses). suggest_actions_for_thesis generates contra-research recommendations. aggregate_thesis_evidence provides comprehensive trails. score_action_thesis_relevance functional.

**Remaining gaps:** All content_digest evidence has sentiment = 'FOR' — the content pipeline may not be generating enough contra signals. Evidence relevance scores are flat (0.7 for content, 0.8 for actions) with no differentiation.

### Portfolio/Network Intelligence: 50 -> 65 (+15)

**Improvements:** Bucket distribution correct (50% portfolio). find_related_companies works (no longer WHERE FALSE). Sector-appropriate results (Consumer for Consumer, SaaS for SaaS). Network included in hybrid search. 100% embedding coverage.

**Remaining critical gap:** Network roles still ALL 'postgres' — 3,722/3,722 rows have the database default instead of actual role data. This means network search returns hits by name/embedding only; role-based filtering is broken. find_related_companies results are dominated by name similarity rather than business-model similarity.

### Search Intelligence: 59 -> 78 (+19)

**Improvements:** Network table now included in hybrid_search (was excluded). 100% embedding + FTS coverage across all 5 tables. RRF (Reciprocal Rank Fusion) combining semantic + keyword search. Multi-table queries return balanced results across all tables. Filter parameters (status, date range, table scope) all functional.

**Remaining gaps:** Requires pre-computed embedding vector as input — no text-only search path. Network search quality degraded by 'postgres' role values in snippets. find_related_companies similarity is lexical not semantic.

---

## Summary Scorecard

| Dimension | Before | After | Delta | Grade |
|-----------|--------|-------|-------|-------|
| Actions | 5.5/10 | **7.0/10** | +1.5 | B- |
| Thesis | 6.2/10 | **7.8/10** | +1.6 | B+ |
| Portfolio/Network | 50/100 | **65/100** | +15 | C+ |
| Search | 59/100 | **78/100** | +19 | B+ |

### Check Pass/Fail Summary

| # | Check | Result |
|---|-------|--------|
| 1 | Score Distribution | PARTIAL PASS (range good, top-heavy) |
| 2 | Network Roles | **FAIL** (still all 'postgres') |
| 3 | Network in Search | PASS |
| 4 | find_related_companies | PASS (quality concern) |
| 5 | Thesis Over-tagging | PASS |
| 6 | Queue Balance | PARTIAL PASS (8.8% agent) |
| 7 | Bucket Distribution | PASS |
| 8 | Top 10 Quality | PARTIAL PASS (no differentiation) |
| 9 | IRGI Independence | PASS |
| 10 | Functions Inventory | PARTIAL PASS (8/9, missing feedback loop) |

---

## Priority Fixes for Next Loop

1. **P0 — Network roles data fix:** Backfill `role_title` from Notion Network DB. This is the single biggest gap — affects search quality, network intelligence, and portfolio/network scoring.
2. **P1 — Score differentiation:** Add entity-specific signals to `compute_user_priority_score` (deal stage, last-interaction recency, company health indicators) to break apart the 9+ cluster.
3. **P1 — Feedback loop:** Implement `update_preference_from_outcome` to learn from user accept/dismiss patterns.
4. **P2 — Company embedding quality:** Regenerate company embeddings using description/sector/stage text rather than name-dominant vectors, so `find_related_companies` returns business-model peers.
5. **P2 — Agent delegation tuning:** Adjust `is_agent_delegable` heuristics to route ~30% of research/monitoring actions to agents.
