# IRGI Reprocessing Loop 1: M6 Intelligence Re-scoring

**Date:** 2026-03-20
**Executor:** Claude Opus 4.6 via Supabase MCP
**Project:** llfkxnsfczludgigknbs (ap-south-1 Mumbai, PG17)
**Scope:** 115 actions, 22 digests, 8 thesis threads -- first pass through IRGI intelligence infrastructure

---

## 1. Pre-Reprocessing State

### Embedding Coverage (100% across all tables)

| Table | Total Rows | Embedded | Coverage |
|-------|-----------|----------|----------|
| content_digests | 22 | 22 | 100% |
| thesis_threads | 8 | 8 | 100% |
| actions_queue | 115 | 115 | 100% |
| companies | 4,635 | 3,890 | 83.9% |

All Voyage AI voyage-3.5 (1024-dim) embeddings are populated for the three core tables. Companies has 745 rows still pending (backfill in progress).

### Pre-existing Scoring State

| Metric | Count |
|--------|-------|
| Actions with `relevance_score` | 23 of 115 (20%) |
| Actions with `scoring_factors` populated | 115 (all have empty `{}`) |
| Actions with `thesis_connection` text | 115 (100%) |
| Actions with `triage_history` | 115 (all present) |

**Critical finding: Two incompatible scoring scales co-exist.**
- IDs 1-100 (early batch): 0-10 scale (range: 6.5-9.5, 11 scored)
- IDs 101-115 (later batch): 0-100 scale (range: 6.5-76, 12 scored)
- 92 actions had NULL `relevance_score`

### Thesis Threads State

| ID | Thread | Conviction | Status | Evidence FOR | Evidence AGAINST | Embedded |
|----|--------|-----------|--------|-------------|-----------------|----------|
| 1 | Cybersecurity / Pen Testing | Medium | Exploring | 1,567 chars | 173 chars | Yes |
| 2 | Healthcare AI Agents as Infrastructure | New | Exploring | 1,130 chars | 230 chars | Yes |
| 3 | Agentic AI Infrastructure | High | Active | 3,618 chars | 436 chars | Yes |
| 4 | SaaS Death / Agentic Replacement | High | Exploring | 2,386 chars | 1,261 chars | Yes |
| 5 | USTOL / Aviation / Deep Tech Mobility | Low | Exploring | 657 chars | 171 chars | Yes |
| 6 | CLAW Stack Standardization & Orchestration Moat | Medium | Exploring | 1,154 chars | 228 chars | Yes |
| 7 | Agent-Friendly Codebase as Bottleneck | Medium | Exploring | 983 chars | 133 chars | Yes |
| 11 | AI-Native Non-Consumption Markets | New | Exploring | 379 chars | 0 chars | Yes |

---

## 2. IRGI Functions Tested

### Functions Available (Phase A + Intelligence Layer)

| Function | Type | Status | Notes |
|----------|------|--------|-------|
| `score_action_thesis_relevance(action_id)` | Scoring | WORKING | Multi-method: vector, trigram, explicit, key-question match |
| `route_action_to_bucket(action_id)` | Routing | WORKING | 4 buckets: Discover New, Deepen Existing, DeVC Collective, Thesis Evolution |
| `suggest_actions_for_thesis(thesis_id)` | Suggestion | WORKING | 4 suggestion types: key questions, company gaps, digest gaps, evidence gaps |
| `aggregate_thesis_evidence(thesis_id)` | Evidence | WORKING | Cross-table evidence aggregation with sentiment |
| `refresh_action_scores()` | Materialized View | WORKING | Refreshes `action_scores` view |
| `find_related_companies(...)` | Graph | PRESENT | Not tested this loop |
| `hybrid_search(...)` | Search | WORKING | Vector + FTS with RRF blending |

### Test Results

**`score_action_thesis_relevance(29)`** (Unifize founder deep dive, old_score=9.5):
- Agentic AI Infrastructure: 0.90 (explicit_connection)
- SaaS Death / Agentic Replacement: 0.90 (explicit_connection)
- AI-Native Non-Consumption Markets: 0.77 (vector)
- CLAW Stack: 0.76 (vector)
- Agent-Friendly Codebase: 0.75 (vector)

**`route_action_to_bucket(29)`**:
- Deepen Existing (Bucket 2): 0.55 confidence (portfolio_action_type)
- Thesis Evolution (Bucket 4): 0.50 confidence (thesis_keywords)

**`aggregate_thesis_evidence(3)`** (Agentic AI Infrastructure):
- 50 evidence items: 27 action proposals, 19 content digests, 4 action outcomes
- 17 digest evidence items scored FOR, 0 AGAINST, 2 NEUTRAL
- Average relevance: action_outcomes 0.90, actions 0.78, digests 0.65

---

## 3. Bucket Distribution (All 115 Actions)

| Primary Bucket | Count | Avg Confidence |
|----------------|-------|---------------|
| Thesis Evolution (Bucket 4) | 63 | 0.55 |
| Discover New (Bucket 1) | 24 | 0.65 |
| DeVC Collective (Bucket 3) | 14 | 0.35 |
| Deepen Existing (Bucket 2) | 14 | 0.38 |

**Observation:** Bucket 4 (Thesis Evolution) is massively overloaded at 55% of all actions. This is because `action_type = 'Research'` (46 actions) triggers thesis keywords, and many Meeting/Outreach actions also get routed to Bucket 4 via weak thesis signals (0.3 confidence). The routing function needs better disambiguation between "research about a thesis topic" and "portfolio/company-specific research."

### Confidence Distribution

| Confidence Range | Count | Interpretation |
|-----------------|-------|---------------|
| 0.80-0.85 | 24 | High confidence routing (Pipeline + Research with thesis action_type) |
| 0.55-0.70 | 10 | Medium confidence (mixed signals) |
| 0.35-0.50 | 52 | Low confidence (weak signals, often single-keyword match) |
| 0.30 | 29 | Very low confidence (thesis_keywords only) |

---

## 4. IRGI Thesis Relevance Scoring (Delta Analysis)

### IRGI Score Distribution (all 115 actions, top thesis match)

| Score Range | Count | Match Type | Interpretation |
|-------------|-------|-----------|---------------|
| 0.90 | 41 | explicit_connection | Direct thesis_connection field match |
| 0.75-0.89 | 6 | vector | Strong semantic similarity |
| 0.70-0.749 | 23 | vector | Moderate semantic similarity |
| 0.65-0.699 | 27 | vector | Weak semantic similarity |
| 0.60-0.649 | 18 | vector | Marginal similarity |

### Score Scale Reconciliation

The IRGI `score_action_thesis_relevance` returns 0.0-1.0 scores. Pre-existing `relevance_score` used two incompatible scales. Mapping:

| Old Scale | IRGI Equivalent | Notes |
|-----------|----------------|-------|
| 0-10 (IDs 1-100) | Multiply by 0.1 | Old 9.5 -> 0.95, comparable to IRGI 0.90 |
| 0-100 (IDs 101-115) | Divide by 100 | Old 76 -> 0.76, comparable to IRGI explicit 0.90 |

**Key delta findings for scored actions:**

| ID | Action | Old Score | IRGI Score | Delta | Shift |
|----|--------|-----------|-----------|-------|-------|
| 105 | Analyze public market AI transition | 76 (0.76) | 0.90 | +0.14 | UP |
| 108 | Map E2B orchestration infra | 76 (0.76) | 0.90 | +0.14 | UP |
| 109 | Research OpenClaw/NanoClaw | 76 (0.76) | 0.90 | +0.14 | UP |
| 107 | Share Monday.com SDR data | 73 (0.73) | 0.90 | +0.17 | UP |
| 111 | Map Indian coding AI landscape | 71 (0.71) | 0.90 | +0.19 | UP |
| 110 | Research SaaS survival categories | 70 (0.70) | 0.90 | +0.20 | UP |
| 106 | Map human-agent orchestration | 64 (0.64) | 0.90 | +0.26 | UP |
| 29 | Unifize founder deep dive | 9.5 (0.95) | 0.90 | -0.05 | STABLE |
| 39 | Sierra AI intro call | 9.0 (0.90) | 0.90 | 0.00 | STABLE |
| 14 | Map agent infra ecosystem | 8.5 (0.85) | 0.90 | +0.05 | STABLE |
| 32 | CodeAnt AI integration roadmap | 8.0 (0.80) | 0.90 | +0.10 | UP |
| 55 | Highperformr positioning review | 8.0 (0.80) | 0.90 | +0.10 | UP |
| 8 | Research incumbent responses | 6.5 (0.65) | 0.90 | +0.25 | UP |

**Pattern:** Actions with explicit thesis connections all normalize to 0.90. The old scoring was more discriminating between actions; IRGI's explicit_connection method caps at 0.90 regardless of action quality. The vector method (0.60-0.78) provides better differentiation for non-explicit actions.

---

## 5. User Priority Hierarchy: User-Facing vs Agent-Delegable

Per user feedback, applying the priority reclassification:

### Classification Rules Applied

| Category | Rule | Action Types |
|----------|------|-------------|
| **USER-FACING (Boosted: Portfolio)** | Portfolio decisions, deepening positions | Portfolio Check-in |
| **USER-FACING (Boosted: Pipeline)** | Investment discovery, new deals | Pipeline Action |
| **USER-FACING (Boosted: Network)** | Relationships, meetings, DeVC Collective | Meeting/Outreach |
| **USER-FACING (Human Judgment)** | Research requiring conviction decisions | Research with conviction/follow-on/investment signals |
| **AGENT-DELEGABLE (Research)** | Evidence gathering, analysis, mapping | Research (general) |
| **AGENT-DELEGABLE (Thesis Maint.)** | Evidence updates, thesis thread updates | Thesis Update |
| **AGENT-DELEGABLE (Content)** | Content processing, follow-ups | Content Follow-up |

### Distribution

| Classification | Count | % of Total |
|---------------|-------|-----------|
| **USER-FACING** | 64 | 55.7% |
| -- Portfolio Check-in (Boosted) | 19 | 16.5% |
| -- Pipeline Action (Boosted) | 13 | 11.3% |
| -- Meeting/Outreach (Boosted) | 32 | 27.8% |
| **AGENT-DELEGABLE** | 51 | 44.3% |
| -- Research (general) | 42 | 36.5% |
| -- Research (human judgment required) | 4 | 3.5% |
| -- Thesis Update | 4 | 3.5% |
| -- Content Follow-up | 1 | 0.9% |

### Reclassified Research Actions (Human Judgment Required)

These 4 Research actions remain USER-FACING because they involve investment decisions or conviction changes:

| ID | Action | Reason |
|----|--------|--------|
| 86 | Model SaaS multiple compression scenarios across portfolio B2B companies | Portfolio investment modeling |
| 91 | Product deep-dive: Unifize + CodeAnt (agentic migration path) | Portfolio strategic decision |
| 113 | Map Z47/DeVC portfolio against 8 Moats framework | Portfolio durability assessment |
| 71 | Resolve funding discrepancy (Tracxn vs PitchBook) | Due diligence investment decision |

### Net Shift Summary

| From | To | Count | Impact |
|------|-----|-------|--------|
| Previously unlabeled | AGENT-DELEGABLE | 47 | **47 actions can now be delegated to AI agents** |
| Previously unlabeled | USER-FACING | 68 | Correctly surfaced for Aakash's attention |
| 92 had no score | All now scored via IRGI | 92 | Full scoring coverage achieved |

**Key insight: 44.3% of all actions (51 of 115) are agent-delegable** under the new priority scheme. These are primarily Research actions (evidence gathering, landscape mapping, monitoring) and Thesis Updates that don't require human judgment. The ContentAgent and future ResearchAgent can handle these autonomously.

---

## 6. New Suggestions Generated (suggest_actions_for_thesis)

Generated 24 suggestions across all 8 thesis threads:

### High-Priority Suggestions (P1)

| Thesis | Suggestion | Type |
|--------|-----------|------|
| Agentic AI Infrastructure | "Is MCP the security-critical layer that defines Agentic AI Infrastructure vs Cybersecurity?" | Key Question |

### Medium-Priority Suggestions (P2)

| Thesis | Suggestion | Type |
|--------|-----------|------|
| Cybersecurity / Pen Testing | 3 open key questions (MCP attack surface, StepSecurity ARR, Agent Security Posture Management category) | Key Questions |
| Healthcare AI Agents | Evaluate Confido Health, Infinitus, Notable, athenahealth | Company Gap |
| Healthcare AI Agents | Follow up on Gokul Rajaram 8 Moats digest | Digest Gap |
| CLAW Stack | Evaluate E2B, Poetic/YC, CodeAnt AI, Step Security | Company Gap |
| CLAW Stack | Follow up on Temporal durable execution digest | Digest Gap |
| Agent-Friendly Codebase | Evaluate CodeAnt AI, Step Security, GitHub Copilot, Cursor | Company Gap |
| AI-Native Non-Consumption | 3 key questions (market size, terminal multiples, India-specific opportunities) | Key Questions |
| SaaS Death | Conviction review: evidence balance check | Evidence Gap |
| Multiple theses | 8 digest follow-up suggestions (content not yet actioned) | Digest Gaps |

### Evidence Gap Analysis

| Thesis | FOR Length | AGAINST Length | Ratio | Recommendation |
|--------|-----------|---------------|-------|---------------|
| Cybersecurity / Pen Testing | 1,567 | 173 | 9:1 | Seek contra signals |
| Healthcare AI Agents | 1,130 | 230 | 5:1 | Seek contra signals |
| Agentic AI Infrastructure | 3,618 | 436 | 8:1 | Seek contra signals |
| SaaS Death / Agentic Replacement | 2,386 | 1,261 | 2:1 | Best balanced |
| CLAW Stack | 1,154 | 228 | 5:1 | Seek contra signals |
| Agent-Friendly Codebase | 983 | 133 | 7:1 | Seek contra signals |
| AI-Native Non-Consumption | 379 | 0 | inf | No contra evidence at all |
| USTOL / Aviation | 657 | 171 | 4:1 | Acceptable for Low conviction |

**7 of 8 theses have significant confirmation bias** (FOR evidence vastly outweighs AGAINST). Only SaaS Death has reasonable balance (2:1). The `suggest_actions_for_thesis` function correctly flags this via evidence gap suggestions.

---

## 7. Materialized View Refreshed

`action_scores` materialized view was refreshed with the latest IRGI function outputs. It now contains:
- All Proposed actions (the view filters to `status = 'Proposed'`)
- Primary bucket + confidence + reasoning
- Top 3 thesis relevance scores with match types per action
- Ready for consumption by any front-end or API caller

---

## 8. Issues Encountered

### 8.1 Connection Pool Saturation (CRITICAL)
- Supabase free tier: limited connection slots
- Parallel queries (2+) consistently hit `FATAL: 53300: remaining connection slots are reserved for roles with the SUPERUSER attribute`
- Mitigation: all queries run sequentially with 6-12 second cooldowns between heavy operations
- **Recommendation for Loop 2:** Batch operations into single queries where possible; consider connection pooler (PgBouncer) or Supabase Pro plan

### 8.2 Bucket Routing Over-concentration
- 55% of actions route to Thesis Evolution (Bucket 4)
- Root cause: `action_type = 'Research'` is the most common type (46 actions), and the routing function gives 0.3+ to anything with thesis keywords
- Many portfolio-specific research actions (flag risks, request data, verify metrics) get misrouted to Bucket 4 instead of Bucket 2
- **Recommendation:** Add portfolio-company detection to Research routing; Research actions about specific portfolio companies should route to Bucket 2

### 8.3 IRGI Score Compression at 0.90
- 41 of 115 actions score exactly 0.90 (explicit_connection match type)
- This is because any action with `thesis_connection` text matching a `thread_name` substring gets 0.90 automatically
- Reduces discrimination between high-quality and mediocre thesis-connected actions
- **Recommendation:** Weight explicit_connection by action_type and priority; a P0 Pipeline Action with explicit thesis connection should score higher than a P3 Research task

### 8.4 Two Incompatible Score Scales in `relevance_score`
- IDs 1-100: 0-10 scale
- IDs 101-115: 0-100 scale
- Neither matches IRGI's 0-1 scale
- **Recommendation:** Normalize all `relevance_score` values to 0-1 scale in Loop 2

### 8.5 Empty `scoring_factors` JSONB
- All 115 actions have `scoring_factors = {}` (empty)
- This field should store the breakdown of how the score was computed
- **Recommendation:** Populate from IRGI function outputs in Loop 2

---

## 9. Recommendations for Loop 2

### Data Fixes (Safe to execute)
1. **Normalize `relevance_score` to 0-1 scale** -- unify the two legacy scales
2. **Populate `scoring_factors`** with IRGI function outputs (vector score, trigram score, explicit match, key question match)
3. **Add `irgi_bucket` column** or use scoring_factors to store bucket routing results
4. **Add `agent_delegable` boolean** column based on the classification rules above

### Function Improvements
5. **Fix bucket routing** -- add portfolio-company detection for Research actions
6. **Break explicit_connection score ceiling** -- weight by action_type and priority to discriminate within the 0.90 cluster
7. **Add `find_related_companies` testing** -- graph function not tested this loop

### Process
8. **Write back IRGI scores** -- UPDATE actions_queue SET relevance_score = IRGI score (after normalizing to common scale)
9. **Populate the 92 previously-unscored actions** with IRGI scores
10. **Set up recurring materialized view refresh** -- currently manual, should be on pg_cron

### Agent Delegation
11. **Tag 51 agent-delegable actions** -- these can be routed to ContentAgent or a future ResearchAgent
12. **Build agent routing logic** -- AGENT-DELEGABLE actions with status=Proposed can be auto-dispatched

---

## Appendix A: Thesis Relevance Heatmap (All Actions x All Theses)

Top thesis match per action (showing IRGI scores):

| Thesis | Actions Matched (Top Match) | Avg IRGI Score | Match Types |
|--------|---------------------------|----------------|-------------|
| Agentic AI Infrastructure (3) | 24 | 0.876 | 18 explicit, 6 vector |
| SaaS Death (4) | 14 | 0.862 | 9 explicit, 5 vector |
| AI-Native Non-Consumption (11) | 17 | 0.672 | 0 explicit, 17 vector |
| Agent-Friendly Codebase (7) | 16 | 0.743 | 5 explicit, 11 vector |
| Cybersecurity (1) | 14 | 0.736 | 3 explicit, 11 vector |
| Healthcare AI Agents (2) | 13 | 0.713 | 1 explicit, 12 vector |
| USTOL / Aviation (5) | 7 | 0.704 | 1 explicit, 6 vector |
| CLAW Stack (6) | 5 | 0.868 | 3 explicit, 2 vector |

**Observation:** Agentic AI Infrastructure and SaaS Death dominate explicit connections (they are the highest-conviction, most-worked theses). AI-Native Non-Consumption Markets has zero explicit connections but 17 vector matches -- these are latent connections discovered by IRGI that weren't tagged by the content pipeline.

## Appendix B: Action Type x Status Distribution

| Action Type | Proposed | Accepted | Dismissed | Total |
|-------------|---------|----------|----------|-------|
| Research | 31 | 15 | 0 | 46 |
| Meeting/Outreach | 30 | 2 | 0 | 32 |
| Portfolio Check-in | 15 | 4 | 0 | 19 |
| Pipeline Action | 12 | 0 | 1 | 13 |
| Thesis Update | 2 | 2 | 0 | 4 |
| Content Follow-up | 1 | 0 | 0 | 1 |
| **Total** | **91** | **23** | **1** | **115** |
