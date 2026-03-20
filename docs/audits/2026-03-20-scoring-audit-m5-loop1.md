# Scoring & Bucket Routing Audit — M5 Loop 1
*Created: 2026-03-20*
*Supabase Project: llfkxnsfczludgigknbs (AI COS Mumbai, ap-south-1)*

---

## Executive Summary

The action scoring and bucket routing system has **critical structural problems** that undermine its core purpose of curating high-leverage actions for Aakash. The system currently operates as a dump, not a filter. Key findings:

1. **80% of actions have NO score at all** (92 of 115 have NULL relevance_score)
2. **The 23 scored actions use TWO incompatible scales** (0-10 and 0-100) — a generation-time bug
3. **44% of all actions are thesis/research tasks** that should be agent-delegated, not user-surfaced
4. **The preference store has zero human feedback** (4 entries, all "proposed" — no Gold/Helpful/Dismissed outcomes)
5. **Bucket routing is inverted relative to user priorities**: Thesis Evolution dominates (55% of routed actions) while Portfolio (14%) and Network (11%) are underrepresented
6. **No assignment-aware scoring**: the system does not distinguish "Aakash must do this" from "an agent can do this"

The scoring system needs a fundamental reorientation: from thesis-centric to portfolio-and-network-centric, with thesis work treated as agent-executable background processing.

---

## 1. Current State Analysis

### 1.1 Score Coverage

| Metric | Value |
|--------|-------|
| Total actions | 115 |
| With `relevance_score` | 23 (20%) |
| Without `relevance_score` | 92 (80%) |
| With populated `scoring_factors` JSONB | 4 (3.5%) |
| With empty `scoring_factors` `{}` | 111 (96.5%) |

**Diagnosis:** The vast majority of actions were generated before the scoring skill was wired into the content pipeline. Only 4 actions (IDs 101-104) have real scoring_factors data. 7 actions (IDs 105-112) have high scores (64-76) from a different scoring generation. The remaining 12 scored actions (6.5-9.5) appear to be from an earlier batch with correct 0-10 scale.

### 1.2 Bimodal Score Distribution (THE SCALE BUG)

The 23 scored actions split into two incompatible clusters:

| Cluster | Score Range | Count | Scale | Source |
|---------|------------|-------|-------|--------|
| Low cluster | 6.5 — 9.5 | 16 | 0-10 (correct) | Early content pipeline + manual |
| High cluster | 64 — 76 | 7 | 0-100 (WRONG) | Recent content pipeline batch |

**Root cause:** The content agent generated scores on a 0-100 scale for a batch of actions (IDs 105-112), while the scoring skill and all documentation specify 0-10. The `relevance_score` column is `REAL` with no CHECK constraint, so both scales were accepted silently.

**Statistical artifacts from the bug:**
- Reported avg: 27.21 (meaningless — mixing scales)
- Reported stddev: 30.58 (artificially inflated)
- Reported median: 8.00 (pulled toward the 0-10 cluster)
- P25: 7.08, P75: 67.00 (straddles both clusters)

### 1.3 Priority Distribution

| Priority | Count | Avg Score |
|----------|-------|-----------|
| P1 - This Week | 55 | 40.70 |
| P0 - Act Now | 44 | 42.75 |
| P2 - This Month | 8 | 25.83 |
| P2 | 4 | 6.59 |
| P1 | 4 | 7.39 |

**Problems:**
- **86% of actions are P0 or P1** — priority inflation destroys the signal. If everything is urgent, nothing is.
- **Inconsistent priority labels**: "P1" vs "P1 - This Week" and "P2" vs "P2 - This Month" — two generations used different formats
- **P0/P1 avg scores (40-42) reflect the scale bug**, not genuine high urgency

### 1.4 Status Distribution

| Status | Count | Avg Score |
|--------|-------|-----------|
| Proposed | 91 (79%) | 42.12 |
| Accepted | 23 (20%) | 7.71 |
| Dismissed | 1 (1%) | 9.00 |

**Problem:** 91 unreviewed actions in the queue. Only 1 dismissal ever. The triage surface is being overwhelmed, not curated.

### 1.5 Action Type Distribution

| Action Type | Count | % | Avg Score |
|-------------|-------|---|-----------|
| Research | 46 | 40.0% | 30.57 |
| Meeting/Outreach | 32 | 27.8% | 6.75 |
| Portfolio Check-in | 19 | 16.5% | 21.20 |
| Pipeline Action | 13 | 11.3% | 52.00 |
| Thesis Update | 4 | 3.5% | 6.55 |
| Content Follow-up | 1 | 0.9% | 7.75 |

**Research actions dominate** at 40% of all actions, and receive inflated scores from the 0-100 batch.

### 1.6 Thesis Connection Distribution

| Thesis Connection | Count |
|-------------------|-------|
| SaaS Death / Agentic Replacement | 9 |
| Agentic AI Infrastructure + SaaS Death + Healthcare | 6 |
| SaaS Death + Agentic AI + Cybersecurity | 4 |
| SaaS Death + Agentic AI + Healthcare | 3 |
| Various pipe-delimited combinations | 2 each |
| Ad-hoc thesis strings (portfolio-generated) | 1 each |

**Problems:**
- **Inconsistent delimiters**: pipe `|`, plus `+`, and comma-separated — three formats in one column
- **Ad-hoc thesis strings** that don't match any thesis_threads row: "India agritech - sales execution and pipeline velocity", "QSR growth: Execution transparency matters..."
- These ad-hoc strings are paragraph-length sentences, not thread references — they leak content analysis into what should be a structured reference field

### 1.7 Materialized View: action_scores

The `action_scores` materialized view pre-computes bucket routing for all 91 Proposed actions.

| Bucket | Actions | % | Avg Confidence |
|--------|---------|---|---------------|
| Thesis Evolution (Bucket 4) | 50 | **55%** | 0.545 |
| Discover New (Bucket 1) | 18 | 20% | 0.650 |
| Deepen Existing (Bucket 2) | 13 | **14%** | 0.365 |
| DeVC Collective (Bucket 3) | 10 | **11%** | 0.350 |

### 1.8 Embedding State

All 115 actions, 8 thesis threads, and 22 content digests are fully embedded (Voyage AI voyage-3.5, 1024 dims). The `action_scores` materialized view confirms vector-based thesis matching is active — `match_type: "vector"` appears in thesis_relevance arrays.

### 1.9 Preference Store (action_outcomes)

| Outcome | Count |
|---------|-------|
| proposed | 4 |
| Gold | 0 |
| Helpful | 0 |
| Dismissed | 0 |

**The preference store has ZERO human feedback.** All 4 entries are "proposed" (logged at creation time by the content agent). The calibration loop described in the scoring skill and ENIAC APM brief is completely non-functional because no human has rated any action outcome.

---

## 2. User Priority Alignment (CRITICAL)

### The Mismatch

Aakash's actual priority hierarchy:
- **P0:** Portfolio work (deepen existing positions, follow-on decisions)
- **P1:** Network expansion (relationship building, DeVC Collective funnel)
- **LOW:** Thesis work (should be auto-delegated to agents, not surfaced)

What the system currently surfaces:

| User Priority Bucket | Actions | % of Queue | Ideal % |
|---------------------|---------|------------|---------|
| PORTFOLIO (user P0) | 19 | 16.5% | ~40-50% |
| NETWORK (user P1) | 32 | 27.8% | ~30-40% |
| PIPELINE (Bucket 1) | 13 | 11.3% | ~10-15% |
| THESIS/RESEARCH (should delegate) | 51 | **44.3%** | ~5-10% |

**The system is inverted.** Thesis/Research work — which should be mostly invisible to Aakash — is the largest category at 44.3%. Portfolio work — his stated P0 — is only 16.5%.

### Assignment vs. Surfacing Gap

Of the 51 thesis/research actions:
- 12 assigned to Aakash (should NOT be surfaced unless they require human judgment)
- 22 assigned to Agent (correctly delegated but still appearing in the user's triage queue)
- 17 unassigned (neither human nor agent — no routing at all)

**Even the correctly agent-assigned thesis tasks appear in the same queue as portfolio P0s.** There is no separation between "actions for Aakash to triage" and "actions for agents to execute."

### What the Triage Queue Looks Like Today

When sorted by `relevance_score DESC NULLS LAST` (the user's view), the top 20 Proposed actions are:

| Rank | Score | Type | Action (truncated) | Assigned |
|------|-------|------|--------------------|----------|
| 1 | 76 | Research | Analyze public market AI transition opportunities... | Aakash |
| 2 | 76 | Pipeline Action | Map and reach out to E2B, orchestration layer... | Aakash |
| 3 | 76 | Research | Research OpenClaw/NanoClaw adoption patterns... | Agent |
| 4 | 73 | Portfolio Check-in | Share Monday.com SDR-to-agent data with portfolio... | Aakash |
| 5 | 71 | Pipeline Action | Map Indian coding AI infrastructure landscape... | Agent |
| 6 | 70 | Research | Research which SaaS categories survive agentic... | Agent |
| 7 | 64 | Research | Map human-agent orchestration platform landscape... | Agent |
| 8 | 7.75 | Content Follow-up | Listen to 20VC Gokul Rajaram 12:15-20:16... | Aakash |
| 9 | 7.4 | Research | Map emerging data infrastructure layer for AI... | Agent |
| 10 | 6.75 | Meeting/Outreach | Share Wang interview with CodeAnt AI founder... | Aakash |
| 11 | 6.6 | Thesis Update | Update SaaS Death thesis with Gokul's 8 moats... | Agent |
| 12 | 6.5 | Research | Research defense-AI data infrastructure companies... | Agent |
| 13 | 6.5 | Thesis Update | Update SaaS Death thesis with Wang's data moat... | Agent |
| 14-20 | NULL | Mixed | Portfolio Check-ins, Research, Meeting/Outreach... | Mixed |

**Problems visible in the triage queue:**
1. Top 3 are all thesis research (scored on wrong scale) — not a single portfolio action
2. Agent-assigned tasks (ranks 3, 5, 6, 7, 9, 11, 12, 13) appear in the user queue
3. The ONLY portfolio action in the top 7 is rank 4 (Share Monday.com data)
4. 92 actions with NULL scores are listed below the scored ones — user would never see them
5. P0 portfolio actions (IDs 46, 64, 36, 45) with NULL scores are buried at the bottom

### The Dump Problem

If Aakash opens the triage view right now, he sees:
- 7 thesis/research tasks at the top (scored 64-76 on wrong scale)
- 1 portfolio check-in (rank 4)
- 6 more thesis/research tasks (scored 6.5-7.75)
- Then 79 unscored actions in no meaningful order

**This is a dump, not a curated queue.** The user would need to scroll past ~13 thesis tasks to find portfolio and network work.

---

## 3. Function-by-Function Assessment

### 3A. `score_action_thesis_relevance(action_id)`

**Purpose:** Score relevance of an action to all 8 thesis threads using 4 methods.

**Implementation quality:** Good. Clean 4-method approach (vector similarity, trigram text overlap, explicit connection matching, key question keyword match). Returns top 5 matches above 0.05 threshold.

**Strengths:**
- Vector path is now active (all rows embedded) — provides genuine semantic matching
- Explicit connection matching at 0.9 correctly dominates other methods
- Graceful fallback chain when one method returns nothing

**Weaknesses:**
- W1: **No thesis status weighting.** Active vs Parked theses get equal scoring treatment. The ENIAC APM brief and CONTEXT.md both specify that Active theses should receive a scoring multiplier, but this function treats all 8 threads identically.
- W2: **Vector similarity scores are compressed.** From the materialized view data, vector match scores cluster in the 0.60-0.76 range. With 8 thesis threads, every action matches most of them in that narrow band. Low discrimination power.
- W3: **No conviction weighting.** A thesis at "High" conviction has different implications than one at "New" — answering a key question on a High-conviction thesis is more valuable (closer to investment decision) than on a New thesis.
- W4: **Returns 5 matches by default** — nearly every thesis for an 8-thesis universe. The function rarely filters anything out.

**Verdict:** Structurally sound but provides near-zero discrimination because every action matches most theses at similar scores.

### 3B. `route_action_to_bucket(action_id)`

**Purpose:** Route an action to one of 4 ENIAC priority buckets using keyword signals + action type + portfolio cross-reference.

**Implementation quality:** Functional but fundamentally misaligned with user priorities.

**Strengths:**
- Portfolio cross-reference check (v_has_portfolio_company) is a strong structural signal
- Returns all matching buckets with confidence scores, not just the top one
- Keyword regex patterns are reasonable for initial classification

**Weaknesses:**
- W1: **Thesis Evolution has the widest trigger surface.** ANY action with: thesis in the text (almost all have thesis_connection), OR action_type Research/Thesis Update/Content Follow-up (51% of all actions), OR thesis_connection not empty — gets Bucket 4 signals. The trigger is too broad.
  - Bucket 4 score accumulation: `v_has_thesis_signal (0.3) + action_type match (0.3) + keyword match (0.2) + content follow-up (0.15) = up to 0.95`
  - Bucket 2 score accumulation: `portfolio_company (0.5) + action_type match (0.35) + keyword match (0.2) = up to 1.05` — but v_has_portfolio_company requires company_notion_id to match portfolio table, and most actions lack this cross-reference
- W2: **Portfolio detection requires company_notion_id join** — but only 19 of 115 actions are typed as Portfolio Check-in. Many portfolio-relevant actions (like "Share Monday.com data with portfolio companies") are typed as Research or Meeting/Outreach and have no company_notion_id, so they miss the Bucket 2 signal entirely.
- W3: **Bucket confidence scores are low across the board.** Avg confidence: B1=0.65, B2=0.37, B3=0.35, B4=0.55. The router rarely reaches high confidence because most actions trigger multiple buckets at low levels.
- W4: **No user priority weighting.** Buckets 2 and 3 should be boosted for Aakash-assigned actions. Bucket 4 should be demoted for user-facing surfaces.
- W5: **Misrouting of portfolio actions.** Example: action 53 ("Validate Kisan Agri Show pipeline — request dealer list") is routed to Bucket 1 (Discover New) at 0.55 confidence. This is clearly portfolio IDS work (Bucket 2). The keyword "pipeline" triggered new_company signals instead of portfolio signals.

**Verdict:** Fundamentally misaligned. The function treats all 4 buckets equally when user priorities demand a strong skew toward Buckets 2 and 3.

### 3C. `suggest_actions_for_thesis(thesis_id, limit)`

**Purpose:** Generate action suggestions for a given thesis thread.

**Implementation quality:** Clever gap analysis but produces user-wrong suggestions.

**Strengths:**
- 4-type suggestion generation (key questions, company gaps, digest follow-ups, evidence balance)
- Evidence imbalance detection (FOR vs AGAINST ratio) is valuable
- Priority mapping considers thesis status and conviction

**Weaknesses:**
- W1: **All suggestions route to Thesis Evolution (Bucket 4).** The function hardcodes `'Thesis Evolution (Bucket 4)'` for almost every suggestion type. Company gap analysis routes to Bucket 1, but key question research, digest follow-ups, and evidence analysis all go to Bucket 4.
- W2: **All suggestions are thesis-maintenance tasks.** "Research open key question", "Follow up on digest", "Seek contra signals" — these are exactly the kind of agent-executable tasks that should NOT appear in the user's triage queue.
- W3: **No filter for "requires human judgment."** The function cannot distinguish between "research this topic" (agent can do) and "make a conviction decision" (only Aakash can do).

**Verdict:** Useful as an agent work-queue generator but should never feed the user-facing triage surface.

### 3D. `aggregate_thesis_evidence(thesis_id)`

**Purpose:** Gather all evidence for a thesis from content_digests, actions_queue, and action_outcomes.

**Implementation quality:** Good for what it does.

**Strengths:**
- 3-source evidence aggregation with clear priority ordering (explicit > trigram)
- Sentiment classification (FOR/AGAINST/NEUTRAL) from evidence direction
- Source type tracking enables provenance

**Weaknesses:**
- W1: **Evidence volume is overwhelming.** Test showed 50 items for a single thesis. No summarization or compression — raw evidence list.
- W2: **No recency weighting.** Old evidence and new evidence are treated equally. In a conviction engine, recent signals should carry more weight.
- W3: **Sentiment heuristic is crude.** "outcome = Dismissed" = AGAINST is wrong — a dismissed action means "not worth doing", not "evidence against the thesis."

**Verdict:** Solid data-gathering function. Needs recency decay and better sentiment logic.

### 3E. `find_related_companies(query_text, limit)`

**Purpose:** Find companies matching a text query.

**Implementation quality:** Now functional with 4,635 companies in the table.

**Strengths:**
- Trigram similarity across multiple company fields
- Fallback path for empty companies table (no longer needed)

**Weaknesses:**
- W1: **No portfolio vs. non-portfolio distinction.** Does not indicate whether a matched company is in the portfolio (Bucket 2 signal) or new (Bucket 1 signal).
- W2: **No embedding path despite companies being embedded.** The function uses only trigram matching, not vector similarity, even though companies now have embeddings.

**Verdict:** Needs portfolio flag and vector path added.

### 3F. `hybrid_search(query_text, query_embedding, ...)`

**Purpose:** Cross-table search combining vector similarity and FTS via Reciprocal Rank Fusion.

**Implementation quality:** Excellent. Well-designed RRF blending, clean per-table CTEs, proper filtering.

**Strengths:**
- RRF is the correct algorithm for blending heterogeneous score scales
- Configurable keyword/semantic weights (default 0.3/0.7)
- Optional date, status, and table filters
- Searches all 4 tables simultaneously

**Weaknesses:**
- W1: **No user-priority weighting in search results.** Portfolio and network results are not boosted relative to thesis results.
- W2: **No "assigned_to" awareness.** Search results from actions_queue don't indicate whether the action is for Aakash or an agent.

**Verdict:** Strong search infrastructure. Priority weighting can be added at the application layer.

---

## 4. Python Scoring Layer Assessment

### `scripts/action_scorer.py` and `lib/scoring.py`

Both implement the same 5-factor weighted sum:

```
Score = 0.25*bucket_impact + 0.25*conviction_change + 0.20*time_sensitivity + 0.15*action_novelty + 0.15*effort_vs_impact
```

**Problems:**
- P1: **Not wired into the live pipeline.** The content agent's scoring skill (`skills/content/scoring.md`) instructs the LLM to compute scores, but only 4 of 115 actions have populated `scoring_factors`. The Python scorer is a standalone script never integrated into production.
- P2: **No non-linear scoring.** The formula is purely linear. The ENIAC APM brief explicitly calls out: "a single 10 on conviction_change might matter more than balanced 6s." No threshold effects, no multiplicative interactions.
- P3: **bucket_impact scores thesis work at 6/10.** The scoring guide gives Bucket 4 (Thesis Evolution) a 6 while Buckets 1-3 get 8-10. This is directionally correct but insufficient — the gap should be much larger for user-facing surfaces.
- P4: **No "agent vs human" dimension.** The 5 factors have no concept of "can an agent execute this?" The same score applies whether the action requires Aakash's personal judgment or could be fully automated.
- P5: **Preference store calibration is documented but non-functional.** The scoring skill describes querying `action_outcomes` for Gold/Helpful patterns — but the table has zero rated outcomes.

---

## 5. Weaknesses & Failure Modes

### Critical (System Doesn't Serve User)

| # | Weakness | Impact | Severity |
|---|----------|--------|----------|
| C1 | **80% of actions are unscored** | Cannot rank, sort, or filter meaningfully | CRITICAL |
| C2 | **Bimodal scale bug** (0-10 and 0-100 mixed) | Incorrect sort order; 0-100 items always surface first | CRITICAL |
| C3 | **Thesis/Research work dominates queue** (44% of actions) | User sees agent-executable tasks, not portfolio P0s | CRITICAL |
| C4 | **No separation between user and agent queues** | Agent tasks pollute user's triage surface | CRITICAL |
| C5 | **Priority inflation** (86% P0/P1) | Priority is meaningless — everything looks urgent | CRITICAL |

### Structural (Design Gap)

| # | Weakness | Impact | Severity |
|---|----------|--------|----------|
| S1 | Bucket routing skews to Thesis Evolution (55%) | Misrepresents action composition | HIGH |
| S2 | No "requires human judgment" classifier | Cannot filter agent-executable from user-actionable | HIGH |
| S3 | Scoring model has no assignment-awareness | Same score for human-required and agent-doable actions | HIGH |
| S4 | Preference store empty (0 outcomes rated) | Calibration loop is dead | HIGH |
| S5 | Inconsistent thesis_connection formats | Cannot reliably join actions to thesis threads | MEDIUM |
| S6 | No score decay / staleness | 3-week-old P0 actions still show as urgent | MEDIUM |
| S7 | No dedup across actions | Semantically similar research tasks accumulate | MEDIUM |

### Latent (Will Bite Later)

| # | Weakness | Impact | Severity |
|---|----------|--------|----------|
| L1 | Vector similarity scores compress to 0.60-0.76 | Poor discrimination as action count grows | LOW now |
| L2 | No portfolio cross-reference in most actions | Bucket 2 routing depends on company_notion_id most actions lack | MEDIUM |
| L3 | suggest_actions_for_thesis only generates Bucket 4 | If used to populate queue, thesis tasks multiply further | MEDIUM |

---

## 6. Proposed Improvements

### FIX 1: Normalize Score Scale (IMMEDIATE)

Fix the bimodal scale bug. All scores should be on 0-10.

```sql
-- Audit: find actions on wrong scale
SELECT id, relevance_score FROM actions_queue
WHERE relevance_score > 10;

-- Fix: normalize 0-100 scores to 0-10
UPDATE actions_queue
SET relevance_score = relevance_score / 10.0
WHERE relevance_score > 10;

-- Guard: add CHECK constraint
ALTER TABLE actions_queue
ADD CONSTRAINT chk_relevance_score_range
CHECK (relevance_score IS NULL OR (relevance_score >= 0 AND relevance_score <= 10));
```

### FIX 2: Backfill Scores for All 92 Unscored Actions (IMMEDIATE)

Create a SQL function that computes a basic score from available metadata when the content agent didn't provide one.

```sql
CREATE OR REPLACE FUNCTION backfill_action_scores()
RETURNS TABLE(action_id INT, computed_score FLOAT)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  WITH scored AS (
    SELECT
      a.id,
      -- bucket_impact from action_type proxy
      (CASE
        WHEN a.action_type = 'Pipeline Action' THEN 8.0
        WHEN a.action_type IN ('Portfolio Check-in', 'Follow-on Eval') THEN 8.0
        WHEN a.action_type = 'Meeting/Outreach' THEN 7.0
        WHEN a.action_type = 'Content Follow-up' THEN 5.0
        WHEN a.action_type = 'Thesis Update' THEN 4.0
        WHEN a.action_type = 'Research' THEN 5.0
        ELSE 3.0
      END * 0.25 +
      -- conviction_change: proxy from thesis connection strength
      CASE WHEN a.thesis_connection IS NOT NULL AND a.thesis_connection != '' THEN 5.0 ELSE 2.0 END * 0.25 +
      -- time_sensitivity: decay from age
      GREATEST(0, 8.0 - EXTRACT(EPOCH FROM (NOW() - a.created_at)) / 86400 * 0.3) * 0.20 +
      -- action_novelty: static proxy (we don't have dedup data)
      5.0 * 0.15 +
      -- effort_vs_impact: proxy from assigned_to
      CASE
        WHEN a.assigned_to = 'Agent' THEN 7.0  -- agent can do cheaply
        WHEN a.action_type IN ('Meeting/Outreach', 'Portfolio Check-in') THEN 6.0
        ELSE 5.0
      END * 0.15
      ) AS computed
    FROM actions_queue a
    WHERE a.relevance_score IS NULL
  )
  SELECT s.id, ROUND(s.computed::numeric, 2)::FLOAT
  FROM scored s;
END;
$$;
```

### FIX 3: Add User Priority Score (KEY CHANGE)

Create a `user_priority_score` function that reranks actions according to Aakash's actual priorities. This is the most important change.

```sql
CREATE OR REPLACE FUNCTION compute_user_priority_score(p_action_id INTEGER)
RETURNS TABLE(
  user_score FLOAT,
  user_bucket TEXT,
  surfacing TEXT,     -- 'user_triage' | 'agent_queue' | 'background'
  reasoning TEXT
)
LANGUAGE plpgsql STABLE AS $$
DECLARE
  v_action_type TEXT;
  v_assigned_to TEXT;
  v_priority TEXT;
  v_company_notion_id TEXT;
  v_relevance_score FLOAT;
  v_is_portfolio BOOLEAN := FALSE;
  v_base_score FLOAT;
  v_portfolio_boost FLOAT := 0;
  v_network_boost FLOAT := 0;
  v_thesis_penalty FLOAT := 0;
  v_human_judgment_required BOOLEAN := FALSE;
  v_final_score FLOAT;
  v_bucket TEXT;
  v_surface TEXT;
  v_reason TEXT := '';
BEGIN
  SELECT a.action_type, a.assigned_to, a.priority,
         a.company_notion_id, a.relevance_score
  INTO v_action_type, v_assigned_to, v_priority,
       v_company_notion_id, v_relevance_score
  FROM actions_queue a WHERE a.id = p_action_id;

  IF v_action_type IS NULL THEN RETURN; END IF;

  v_base_score := COALESCE(v_relevance_score, 5.0);

  -- Portfolio detection (Bucket 2 = user P0)
  IF v_company_notion_id IS NOT NULL THEN
    v_is_portfolio := EXISTS(
      SELECT 1 FROM portfolio p WHERE p.company_name_id = v_company_notion_id
    );
  END IF;

  IF v_is_portfolio OR v_action_type IN ('Portfolio Check-in', 'Follow-on Eval') THEN
    v_portfolio_boost := 3.0;  -- Strong boost
    v_bucket := 'Portfolio (P0)';
    v_human_judgment_required := TRUE;
    v_reason := v_reason || 'portfolio_company ';
  END IF;

  -- Network detection (Bucket 3 = user P1)
  IF v_action_type = 'Meeting/Outreach' THEN
    v_network_boost := 2.0;  -- Moderate boost
    IF v_bucket IS NULL THEN v_bucket := 'Network (P1)'; END IF;
    v_human_judgment_required := TRUE;
    v_reason := v_reason || 'network_action ';
  END IF;

  -- Thesis/Research penalty (should be delegated)
  IF v_action_type IN ('Thesis Update', 'Content Follow-up') THEN
    v_thesis_penalty := -3.0;  -- Strong demotion
    IF v_bucket IS NULL THEN v_bucket := 'Thesis (Agent)'; END IF;
    v_reason := v_reason || 'thesis_maintenance ';
  END IF;

  IF v_action_type = 'Research' AND v_assigned_to = 'Agent' THEN
    v_thesis_penalty := -2.0;
    IF v_bucket IS NULL THEN v_bucket := 'Research (Agent)'; END IF;
    v_reason := v_reason || 'agent_research ';
  END IF;

  -- Human judgment detection
  -- These research tasks need Aakash even though they're "research"
  IF v_action_type = 'Research' AND v_assigned_to = 'Aakash' THEN
    v_human_judgment_required := TRUE;
    -- No penalty for human-required research
    IF v_bucket IS NULL THEN v_bucket := 'Research (Aakash)'; END IF;
    v_reason := v_reason || 'human_research ';
  END IF;

  IF v_action_type = 'Pipeline Action' THEN
    IF v_bucket IS NULL THEN v_bucket := 'Pipeline'; END IF;
    v_reason := v_reason || 'pipeline ';
  END IF;

  IF v_bucket IS NULL THEN v_bucket := 'Other'; END IF;

  v_final_score := GREATEST(0, LEAST(10,
    v_base_score + v_portfolio_boost + v_network_boost + v_thesis_penalty
  ));

  -- Determine surfacing
  IF v_human_judgment_required AND v_final_score >= 5.0 THEN
    v_surface := 'user_triage';
  ELSIF v_assigned_to = 'Agent' OR NOT v_human_judgment_required THEN
    v_surface := 'agent_queue';
  ELSE
    v_surface := 'background';
  END IF;

  RETURN QUERY SELECT v_final_score, v_bucket, v_surface, v_reason;
END;
$$;
```

### FIX 4: Rewrite `route_action_to_bucket` with User Priority Weighting

The current function treats all 4 buckets equally. Rewrite to apply a user-priority multiplier:

```sql
-- In the existing function, add after v_b1-v_b4 scores are computed:

-- USER PRIORITY REBALANCING
-- Boost Bucket 2 (Portfolio = user P0) and Bucket 3 (Network = user P1)
-- Demote Bucket 4 (Thesis = agent work)
v_b2_score := v_b2_score * 1.5;  -- 50% boost for portfolio
v_b3_score := v_b3_score * 1.3;  -- 30% boost for network
v_b4_score := v_b4_score * 0.6;  -- 40% penalty for thesis
```

### FIX 5: Separate User and Agent Queues

Add a `surfacing` column to actions_queue or a view:

```sql
CREATE VIEW user_triage_queue AS
SELECT
  a.*,
  ups.user_score,
  ups.user_bucket,
  ups.surfacing,
  ups.reasoning as routing_reason
FROM actions_queue a
CROSS JOIN LATERAL compute_user_priority_score(a.id) ups
WHERE a.status = 'Proposed'
  AND ups.surfacing = 'user_triage'
ORDER BY ups.user_score DESC;

CREATE VIEW agent_work_queue AS
SELECT
  a.*,
  ups.user_score,
  ups.user_bucket,
  ups.surfacing
FROM actions_queue a
CROSS JOIN LATERAL compute_user_priority_score(a.id) ups
WHERE a.status = 'Proposed'
  AND ups.surfacing = 'agent_queue'
ORDER BY ups.user_score DESC;
```

### FIX 6: Normalize Priority Labels

```sql
-- Fix inconsistent priority labels
UPDATE actions_queue SET priority = 'P1 - This Week'
WHERE priority = 'P1';

UPDATE actions_queue SET priority = 'P2 - This Month'
WHERE priority = 'P2';
```

### FIX 7: Normalize Thesis Connection Format

```sql
-- Standardize to pipe-delimited
UPDATE actions_queue
SET thesis_connection = REPLACE(thesis_connection, ' + ', '|')
WHERE thesis_connection LIKE '% + %';

-- Truncate paragraph-length ad-hoc thesis strings
-- (These are portfolio-generated observations, not thesis references)
UPDATE actions_queue
SET thesis_connection = NULL
WHERE LENGTH(thesis_connection) > 100
  AND thesis_connection NOT LIKE '%|%';
```

### FIX 8: Score Decay for Stale Actions

```sql
CREATE OR REPLACE FUNCTION apply_score_decay()
RETURNS void LANGUAGE sql AS $$
  UPDATE actions_queue
  SET relevance_score = GREATEST(1.0,
    relevance_score - (EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400 / 7) * 0.5
  )
  WHERE status = 'Proposed'
    AND relevance_score IS NOT NULL
    AND created_at < NOW() - INTERVAL '7 days';
$$;
```

---

## 7. Priority Order for Fixes

| Priority | Fix | Effort | Impact | Why First |
|----------|-----|--------|--------|-----------|
| **1** | FIX 1: Normalize score scale | XS | CRITICAL | Broken sort order — top 7 are wrong-scale items |
| **2** | FIX 6: Normalize priority labels | XS | MEDIUM | Data hygiene — 2 SQL statements |
| **3** | FIX 7: Normalize thesis_connection | XS | MEDIUM | Data hygiene — enables proper joins |
| **4** | FIX 3: Add user_priority_score function | M | CRITICAL | Reranks queue by actual user priorities |
| **5** | FIX 5: Separate user/agent queues | S | CRITICAL | Removes thesis tasks from user surface |
| **6** | FIX 2: Backfill unscored actions | S | HIGH | 80% of actions become sortable |
| **7** | FIX 4: Rewrite bucket router weights | S | HIGH | Fixes the 55% thesis skew |
| **8** | FIX 8: Score decay | S | MEDIUM | Prevents stale P0s from dominating |

---

## 8. Validation Queries

After implementing fixes, run these to verify:

```sql
-- V1: Verify no scores > 10
SELECT count(*) FROM actions_queue WHERE relevance_score > 10;
-- Expected: 0

-- V2: Verify score distribution is reasonable
SELECT
  min(relevance_score), max(relevance_score),
  avg(relevance_score), stddev(relevance_score)
FROM actions_queue WHERE relevance_score IS NOT NULL;
-- Expected: min ~2, max ~10, avg ~5-6, stddev ~1.5-2.5

-- V3: Verify user triage queue is portfolio/network heavy
SELECT user_bucket, count(*), round(avg(user_score)::numeric, 2)
FROM user_triage_queue
GROUP BY user_bucket ORDER BY avg(user_score) DESC;
-- Expected: Portfolio and Network dominate top slots

-- V4: Verify agent queue catches thesis work
SELECT user_bucket, count(*)
FROM agent_work_queue
GROUP BY user_bucket ORDER BY count(*) DESC;
-- Expected: Thesis/Research dominate

-- V5: Verify user triage queue size is curated
SELECT count(*) FROM user_triage_queue;
-- Expected: 15-25 actions (not 91)

-- V6: Check top 5 of user triage queue
SELECT id, left(action, 80), user_score, user_bucket, action_type
FROM user_triage_queue LIMIT 5;
-- Expected: Portfolio Check-ins and Meeting/Outreach dominate

-- V7: Verify priority labels are normalized
SELECT DISTINCT priority FROM actions_queue ORDER BY priority;
-- Expected: P0 - Act Now, P1 - This Week, P2 - This Month, P3 - Backlog

-- V8: Verify preference store is ready for feedback
SELECT count(*) FROM action_outcomes WHERE outcome != 'proposed';
-- Expected: starts at 0, grows as user triages via WebFront
```

---

## 9. Architectural Recommendation

The current architecture has scoring spread across 3 disconnected layers:

1. **Content Agent (LLM at generation time)** — computes 5-factor scores in the system prompt, writes to `scoring_factors` JSONB and `relevance_score`. But only 3.5% of actions have this data.
2. **SQL Functions (database)** — `route_action_to_bucket` and `score_action_thesis_relevance` compute bucket routing and thesis relevance. These run post-hoc on the materialized view.
3. **Python scorer (scripts/)** — standalone, never integrated.

**Recommended architecture:**

```
Content Agent generates action
  ↓
  writes to actions_queue with scoring_factors JSONB (5 factors)
  ↓
DB trigger computes:
  1. relevance_score (from scoring_factors weighted sum — CHECK 0-10)
  2. user_priority_score (portfolio/network boost, thesis penalty)
  3. surfacing (user_triage | agent_queue | background)
  4. primary_bucket (from route_action_to_bucket)
  ↓
Materialized view refreshes
  ↓
WebFront queries user_triage_queue view (sorted by user_priority_score)
Agent queries agent_work_queue view (sorted by relevance_score)
```

This ensures every action is scored, classified, and routed at write time with no manual intervention.

---

## Appendix: Raw Data Summary

| Table | Rows | Scored | Embedded | Key Gap |
|-------|------|--------|----------|---------|
| actions_queue | 115 | 23 (20%) | 115 (100%) | 80% unscored |
| action_outcomes | 4 | N/A | N/A | 0 human feedback |
| thesis_threads | 8 | N/A | 8 (100%) | — |
| content_digests | 22 | N/A | 22 (100%) | — |
| companies | 4,635 | N/A | processing | — |
| network | 3,728 | N/A | processing | — |
| portfolio | 142 | N/A | 142 (100%) | — |
| action_scores (mat view) | 91 | all routed | N/A | 55% Thesis bucket |
| entity_relationships (view) | 8,339 | N/A | N/A | — |
