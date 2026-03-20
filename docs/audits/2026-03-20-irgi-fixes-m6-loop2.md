# IRGI Scoring Fixes: M6 Loop 2

**Date:** 2026-03-20
**Executor:** Claude Opus 4.6 via Supabase MCP
**Project:** llfkxnsfczludgigknbs (ap-south-1 Mumbai, PG17)
**Scope:** Fix score compression, bucket misrouting, latent connections, bias detection
**SQL saved to:** `sql/irgi-scoring-fixes.sql`

---

## Summary

Five fixes executed against the IRGI intelligence infrastructure, addressing the three critical issues identified in M6 Loop 1 and M5 Loop 1 audits:

1. **Score compression eliminated** -- 39 actions at flat 0.90 now spread across 0.53-0.89
2. **Bucket misrouting fixed** -- Thesis Evolution dropped from 55% to 2.2% of actions
3. **77 latent thesis connections created** -- AI-Native Non-Consumption Markets went from 0 to 26 explicit connections
4. **Confirmation bias detection function deployed** -- flags 3 theses with evidence imbalance
5. **Materialized view refreshed** with new function outputs

---

## Fix 1: Score Compression in `score_action_thesis_relevance`

### Problem
39 of 115 actions scored exactly 0.90 via `explicit_connection` matching. Any action with `thesis_connection` text matching a `thread_name` substring got a flat 0.90. Zero discrimination between high-quality and mediocre thesis-connected actions. The remaining 76 actions scored via vector with a narrow 0.606-0.906 range (stddev 0.056).

### Solution
Rewrote the function to use a **weighted combination of all 4 methods** instead of taking the max:

| Method | Weight | Change |
|--------|--------|--------|
| Vector similarity | 0.50 | Was: co-equal with others. Now: PRIMARY signal |
| Explicit connection | 0.20 | Was: flat 0.90. Now: graduated 1.0/0.7/0.5 |
| Trigram text overlap | 0.15 | Unchanged weight, now additive not max |
| Key question match | 0.15 | Unchanged weight, now additive not max |

Added multipliers:
- **Conviction:** High=1.15, Medium=1.0, New=0.90, Low=0.85
- **Status:** Active=1.10, Exploring=1.0, Parked=0.70

### Before/After Score Distribution

| Metric | BEFORE | AFTER |
|--------|--------|-------|
| **explicit_connection count at 0.90** | 39 (stddev 0.000) | 0 |
| **vector+explicit range** | flat 0.90 | 0.534 - 0.893 (stddev 0.113) |
| **vector-only range** | 0.606 - 0.906 (stddev 0.056) | 0.433 - 0.522 (stddev 0.024) |
| **text_overlap range** | N/A (merged into vector) | 0.405 - 0.432 (stddev 0.008) |
| **Total score spread** | 0.606 - 0.906 (bimodal) | 0.405 - 0.893 (continuous) |

### Sample Action Scores (Action 29: Unifize founder deep dive)

| Thesis | BEFORE | AFTER | Delta |
|--------|--------|-------|-------|
| Agentic AI Infrastructure | 0.90 (explicit) | 0.813 (vector+explicit) | -0.087 |
| SaaS Death / Agentic Replacement | 0.90 (explicit) | 0.803 (vector+explicit) | -0.097 |
| Cybersecurity / Pen Testing | 0.76 (vector) | 0.423 (vector) | -0.337 |
| Agent-Friendly Codebase | 0.75 (vector) | 0.413 (vector) | -0.337 |
| CLAW Stack | 0.76 (vector) | 0.410 (vector) | -0.350 |

**Key improvement:** The two explicitly-connected theses now discriminate (0.813 vs 0.803) instead of being identical at 0.90. Non-connected theses drop sharply to 0.41-0.42 (was 0.75-0.76). This gives the system much better discrimination power.

---

## Fix 2: Bucket Misrouting in `route_action_to_bucket`

### Problem
Bucket 4 (Thesis Evolution) received 55% of all actions (50 of 91 Proposed). Root cause:
- `action_type = 'Research'` (46 actions, 40% of total) auto-triggered thesis keywords
- Portfolio-specific research (flag risks, request data, verify metrics) misrouted to Bucket 4
- No user priority weighting -- all 4 buckets treated equally

### Solution

Three-part fix:

**A. Portfolio research detection** -- new regex patterns catch:
- Company-specific actions: "flag risk", "request data", "request breakdown", "request case study"
- Portfolio company names: Unifize, CodeAnt, Highperformr, Kisan, Sierra, etc.
- Portfolio operations: "scaling call", "working capital", "customer cohort", "execution risk"

**B. Thesis signal narrowing** -- Research action_type no longer auto-triggers Bucket 4:
- Only `Thesis Update` and `Content Follow-up` action types trigger thesis signal
- Research only gets Bucket 4 if it explicitly mentions "thesis", "conviction", "evidence gather"
- Portfolio research is excluded from thesis signal even if it mentions thesis keywords

**C. User priority rebalancing:**
- Bucket 2 (Portfolio): x1.5 boost
- Bucket 3 (Network): x1.3 boost
- Bucket 4 (Thesis): x0.6 penalty
- Research fallback: unmatched Research actions default to Bucket 1 (Discover New)

### Before/After Bucket Distribution (91 Proposed Actions)

| Bucket | BEFORE Count | BEFORE % | AFTER Count | AFTER % | Shift |
|--------|-------------|----------|-------------|---------|-------|
| Deepen Existing (B2) | 13 | 14.3% | **43** | **47.3%** | +30 |
| Expand Network (B3) | 10 | 11.0% | **24** | **26.4%** | +14 |
| Discover New (B1) | 18 | 19.8% | 22 | 24.2% | +4 |
| Thesis Evolution (B4) | **50** | **54.9%** | 2 | 2.2% | **-48** |

### Confidence Improvement

| Bucket | BEFORE Avg Conf | AFTER Avg Conf | Delta |
|--------|----------------|----------------|-------|
| Deepen Existing (B2) | 0.365 | **0.837** | +0.472 |
| Expand Network (B3) | 0.350 | **0.542** | +0.192 |
| Discover New (B1) | 0.650 | **0.580** | -0.070 |
| Thesis Evolution (B4) | 0.545 | 0.345 | -0.200 |

Portfolio bucket confidence jumped from 0.37 to 0.84 -- the router is now much more certain about portfolio actions.

### Specific Routing Fixes Verified

| Action | BEFORE | AFTER |
|--------|--------|-------|
| #29 Unifize founder deep dive | Thesis Evolution + Deepen Existing | **Deepen Existing (0.825)** |
| #53 Kisan Agri Show pipeline | Discover New (0.55) | **Discover New (0.55) + Network (0.39)** |
| #35 Flag product quality issue | NULL (no match) | **Deepen Existing** (portfolio research) |
| #36 Request working capital health check | NULL (no match) | **Deepen Existing** (portfolio research) |

---

## Fix 3: Latent Thesis Connections

### Problem
AI-Native Non-Consumption Markets thesis had 17 actions with high vector similarity (0.60-0.91) but zero explicit `thesis_connection` tags. Other theses also had untagged high-similarity connections.

### Solution
Ran vector similarity scan across all actions x all theses. Tagged connections where cosine similarity > 0.75 and the thesis name was not already present in `thesis_connection`.

Executed in 3 batches:
1. All theses, initial pass: **40 connections tagged**
2. AI-Native Non-Consumption Markets targeted: **24 more connections**
3. Agent-Friendly Codebase (9) + CLAW Stack (4) remaining strong connections: **13 more**

**Total: 77 latent connections created**

### Thesis Connection Counts (Before/After)

| Thesis | BEFORE | AFTER | New Connections |
|--------|--------|-------|-----------------|
| SaaS Death / Agentic Replacement | ~18 | 32 | +14 |
| Agentic AI Infrastructure | ~18 | 30 | +12 |
| **AI-Native Non-Consumption Markets** | **0** | **26** | **+26** |
| CLAW Stack | ~3 | 16 | +13 |
| Agent-Friendly Codebase | ~5 | 15 | +10 |
| Cybersecurity / Pen Testing | ~3 | 15 | +12 |
| Healthcare AI Agents | ~1 | 8 | +7 |
| USTOL / Aviation | ~1 | 2 | +1 |

### Top Latent Connections Discovered

| Action ID | Action | Thesis | Similarity |
|-----------|--------|--------|-----------|
| 114 | Research Granola and Gamma as Non-Consumption Market example | AI-Native Non-Consumption Markets | 0.9058 |
| 90 | Research CLAW stack standardization | CLAW Stack | 0.9011 |
| 78 | Confido Health: inquire about AI agent strategy | Healthcare AI Agents | 0.8549 |
| 32 | CodeAnt AI integration roadmap | Agent-Friendly Codebase | 0.8450 |
| 87 | Assess Z47/DeVC agent deployment readiness | Agent-Friendly Codebase | 0.8303 |
| 99 | Portfolio check-in: CodeAnt AI (Poetic threat) | Agent-Friendly Codebase | 0.8263 |
| 14 | Map agent infrastructure ecosystem | CLAW Stack | 0.8217 |
| 91 | Product deep-dive: Unifize + CodeAnt | Agent-Friendly Codebase | 0.8210 |
| 92 | Interview enterprise engineers on agent deployment | Agent-Friendly Codebase | 0.8120 |
| 88 | Monitor open-source harness frameworks | CLAW Stack | 0.8086 |

---

## Fix 4: Confirmation Bias Detection

### Function Created
`detect_thesis_bias()` -- flags thesis threads with imbalanced FOR:AGAINST evidence ratios.

### Current Bias State

| Thesis | FOR | AGAINST | Ratio | Flag |
|--------|-----|---------|-------|------|
| AI-Native Non-Consumption Markets | 1 | 0 | 999:1 | **CRITICAL: Zero contra evidence** |
| Cybersecurity / Pen Testing | 10 | 1 | 10:1 | **HIGH: >5x FOR:AGAINST ratio** |
| Agentic AI Infrastructure | 21 | 4 | 5.25:1 | **HIGH: >5x FOR:AGAINST ratio** |
| Agent-Friendly Codebase | 6 | 2 | 3:1 | OK |
| CLAW Stack | 5 | 2 | 2.5:1 | OK |
| Healthcare AI Agents | 7 | 3 | 2.3:1 | OK |
| USTOL / Aviation | 2 | 1 | 2:1 | OK |
| SaaS Death / Agentic Replacement | 11 | 8 | 1.38:1 | OK (best balanced) |

### Recommendations
- **AI-Native Non-Consumption Markets:** Needs immediate contra-signal search. No evidence against the thesis exists.
- **Cybersecurity / Pen Testing:** Needs deliberate contra evidence (10:1 ratio).
- **Agentic AI Infrastructure:** At High conviction with 5:1 ratio -- should actively seek disconfirming evidence before follow-on decisions.

---

## Fix 5: Materialized View Refresh

`action_scores` materialized view refreshed with all new function outputs. Now contains:
- Corrected bucket routing (47% B2, 26% B3, 24% B1, 2% B4)
- Corrected thesis relevance scores (continuous 0.40-0.89 spread, no flat 0.90 ceiling)
- Updated thesis_relevance arrays with new match types (vector+explicit, vector, text_overlap)

---

## Validation Summary

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| No flat 0.90 scores | 0 at exactly 0.90 | 0 | PASS |
| Bucket 4 < 10% of actions | < 9 actions | 2 (2.2%) | PASS |
| Bucket 2 is largest | > 30% | 47.3% | PASS |
| No NULL buckets | 0 | 0 | PASS |
| AI-Native connections > 0 | > 10 | 26 | PASS |
| Bias detection returns results | 8 rows | 8 rows | PASS |
| Mat view refreshed | Fresh data | Confirmed | PASS |

---

## Connection Pool Notes

No connection pool issues encountered in this loop. All queries ran sequentially via Supabase MCP. The function rewrites (CREATE OR REPLACE) executed cleanly without conflicts.

---

## Next Steps for Loop 3

1. **Normalize `relevance_score` column** to 0-1 scale (currently 0-10 / 0-100 mixed in the column itself)
2. **Populate `scoring_factors` JSONB** with IRGI function outputs (vector, trigram, explicit, kq scores)
3. **Write back IRGI scores** to `relevance_score` column on actions_queue
4. **Address AI-Native Non-Consumption contra evidence gap** flagged by bias detection
5. **Test `find_related_companies`** function (not tested in Loop 1 or 2)
6. **Set up pg_cron for `REFRESH MATERIALIZED VIEW action_scores`** (currently manual)
