-- =============================================================================
-- Scoring System Improvements — M5 Loop 2
-- Date: 2026-03-20
-- Context: Fixes the 8 issues identified in scoring-audit-m5-loop1.md
-- Supabase Project: llfkxnsfczludgigknbs (Mumbai)
-- =============================================================================

-- =============================================================================
-- FIX 1: Normalize Score Scale (CRITICAL)
-- Problem: 7 actions scored 64-76 on a 0-100 scale while 16 others are on 0-10
-- =============================================================================

-- Identify wrong-scale scores
SELECT id, action, relevance_score FROM actions_queue WHERE relevance_score > 10;

-- Fix: divide by 10
UPDATE actions_queue SET relevance_score = relevance_score / 10.0 WHERE relevance_score > 10;

-- Verify
SELECT min(relevance_score), max(relevance_score), avg(relevance_score)
FROM actions_queue WHERE relevance_score IS NOT NULL;


-- =============================================================================
-- FIX 2: Normalize Priority Labels
-- Problem: "P1" vs "P1 - This Week" and "P2" vs "P2 - This Month"
-- =============================================================================

-- Normalize to short form
UPDATE actions_queue SET priority = 'P0' WHERE priority LIKE 'P0%';
UPDATE actions_queue SET priority = 'P1' WHERE priority LIKE 'P1%';
UPDATE actions_queue SET priority = 'P2' WHERE priority LIKE 'P2%';
UPDATE actions_queue SET priority = 'P3' WHERE priority LIKE 'P3%';


-- =============================================================================
-- FIX 3: Create User Priority Score Function
-- Purpose: Reranks actions by Aakash's actual priorities
--   Portfolio work = highest (+3), Network = high (+2), Thesis = demoted (-3)
-- =============================================================================

CREATE OR REPLACE FUNCTION compute_user_priority_score(action_row actions_queue)
RETURNS numeric AS $$
DECLARE
  base_score numeric;
  priority_boost numeric;
  type_boost numeric;
  recency_factor numeric;
BEGIN
  base_score := COALESCE(action_row.relevance_score, 5.0);

  -- Priority boost
  priority_boost := CASE action_row.priority
    WHEN 'P0' THEN 2.0
    WHEN 'P1' THEN 1.0
    WHEN 'P2' THEN 0.0
    WHEN 'P3' THEN -1.0
    ELSE 0.0
  END;

  -- Type boost (USER PRIORITY HIERARCHY)
  type_boost := CASE
    WHEN action_row.action_type ILIKE '%portfolio%' OR action_row.action_type ILIKE '%check-in%' OR action_row.action_type ILIKE '%follow-on%' THEN 3.0
    WHEN action_row.action_type ILIKE '%network%' OR action_row.action_type ILIKE '%meet%' OR action_row.action_type ILIKE '%connect%' OR action_row.action_type ILIKE '%outreach%' THEN 2.0
    WHEN action_row.action_type ILIKE '%thesis%' OR action_row.action_type ILIKE '%research%' OR action_row.action_type ILIKE '%evidence%' THEN -3.0
    WHEN action_row.action_type ILIKE '%content%' OR action_row.action_type ILIKE '%digest%' THEN -2.0
    ELSE 0.0
  END;

  -- Also check the action text itself for portfolio/network signals
  IF type_boost = 0.0 THEN
    type_boost := CASE
      WHEN action_row.action ILIKE '%portfolio%' OR action_row.action ILIKE '%check-in%' OR action_row.action ILIKE '%board%' THEN 2.0
      WHEN action_row.action ILIKE '%meet%' OR action_row.action ILIKE '%connect%' OR action_row.action ILIKE '%intro%' OR action_row.action ILIKE '%network%' THEN 1.5
      WHEN action_row.action ILIKE '%thesis%' OR action_row.action ILIKE '%research%' OR action_row.action ILIKE '%review evidence%' THEN -2.0
      ELSE 0.0
    END;
  END IF;

  -- Recency factor (newer = slightly higher, decays over 30 days)
  recency_factor := GREATEST(0, 1.0 - EXTRACT(EPOCH FROM (now() - COALESCE(action_row.created_at, now()))) / (30 * 86400));

  RETURN GREATEST(0, LEAST(10, base_score + priority_boost + type_boost + recency_factor));
END;
$$ LANGUAGE plpgsql IMMUTABLE;


-- =============================================================================
-- FIX 4: Create User Triage Queue and Agent Work Queue Views
-- Purpose: Separates user-facing actions from agent-executable ones
-- =============================================================================

CREATE OR REPLACE VIEW user_triage_queue AS
SELECT
  aq.*,
  compute_user_priority_score(aq) as user_score,
  CASE
    WHEN aq.action_type ILIKE '%research%' OR aq.action_type ILIKE '%evidence%' OR aq.action_type ILIKE '%content%' OR aq.action_type ILIKE '%thesis update%'
    THEN true
    WHEN aq.action ILIKE '%review evidence%' OR aq.action ILIKE '%research%' OR aq.action ILIKE '%analyze content%' OR aq.action ILIKE '%update thesis%'
    THEN true
    ELSE false
  END as is_agent_delegable
FROM actions_queue aq
WHERE aq.status = 'Proposed'
ORDER BY compute_user_priority_score(aq) DESC;

CREATE OR REPLACE VIEW agent_work_queue AS
SELECT aq.*
FROM actions_queue aq
WHERE aq.status = 'Proposed'
AND (
  aq.action_type ILIKE '%research%' OR aq.action_type ILIKE '%evidence%' OR aq.action_type ILIKE '%content%' OR aq.action_type ILIKE '%thesis update%'
  OR aq.action ILIKE '%review evidence%' OR aq.action ILIKE '%research%' OR aq.action ILIKE '%analyze content%' OR aq.action ILIKE '%update thesis%'
);


-- =============================================================================
-- FIX 5: Backfill Scores for Unscored Actions
-- Fills relevance_score using the user_priority_score function for NULL entries
-- =============================================================================

UPDATE actions_queue
SET relevance_score = compute_user_priority_score(actions_queue)::real
WHERE relevance_score IS NULL;


-- =============================================================================
-- FIX 6: Rewrite Bucket Router with User Priority Weighting
-- Changes: Bucket 2 (Portfolio) x1.5, Bucket 3 (Network) x1.3, Bucket 4 (Thesis) x0.6
-- NOTE: Must DROP first due to return type change, then recreate matview
-- =============================================================================

DROP FUNCTION IF EXISTS route_action_to_bucket(integer) CASCADE;

CREATE FUNCTION route_action_to_bucket(p_action_id INTEGER)
RETURNS TABLE(bucket TEXT, confidence FLOAT, reasoning TEXT)
LANGUAGE plpgsql STABLE
SET search_path = public, extensions
AS $$
DECLARE
    v_action TEXT;
    v_action_type TEXT;
    v_thesis_conn TEXT;
    v_source_content TEXT;
    v_reasoning TEXT;
    v_company_notion_id TEXT;
    v_combined_text TEXT;
    v_scoring_factors JSONB;

    v_b1_score FLOAT := 0.0;
    v_b2_score FLOAT := 0.0;
    v_b3_score FLOAT := 0.0;
    v_b4_score FLOAT := 0.0;

    v_has_portfolio_company BOOLEAN := FALSE;
    v_has_new_company_signal BOOLEAN := FALSE;
    v_has_network_signal BOOLEAN := FALSE;
    v_has_thesis_signal BOOLEAN := FALSE;
BEGIN
    SELECT
        a.action, a.action_type, a.thesis_connection,
        a.source_content, a.reasoning, a.company_notion_id,
        a.scoring_factors
    INTO v_action, v_action_type, v_thesis_conn, v_source_content,
         v_reasoning, v_company_notion_id, v_scoring_factors
    FROM actions_queue a
    WHERE a.id = p_action_id;

    IF v_action IS NULL THEN
        RETURN;
    END IF;

    v_combined_text := LOWER(COALESCE(v_action, '') || ' ' ||
                       COALESCE(v_thesis_conn, '') || ' ' ||
                       COALESCE(v_source_content, '') || ' ' ||
                       COALESCE(v_reasoning, ''));

    IF v_company_notion_id IS NOT NULL AND v_company_notion_id != '' THEN
        v_has_portfolio_company := EXISTS(
            SELECT 1 FROM portfolio p
            WHERE p.company_name_id = v_company_notion_id
        );
    END IF;

    v_has_new_company_signal := (
        v_combined_text ~ '(new company|discover|pipeline|evaluate|due diligence|scout|deal flow|source|first meeting|intro to.*founder|cap table|investable)'
        OR v_action_type IN ('Pipeline Action')
        OR (v_company_notion_id IS NOT NULL AND NOT v_has_portfolio_company)
    );

    v_has_network_signal := (
        v_combined_text ~ '(collective|community|network|intro|connect|meet|outreach|relationship|devc|extended|core member|funnel|angel|mentor)'
        OR v_action_type IN ('Meeting/Outreach')
    );

    v_has_thesis_signal := (
        v_combined_text ~ '(thesis|conviction|evidence|research|framework|hypothesis|validate|key question|evolving)'
        OR v_action_type IN ('Thesis Update', 'Research', 'Content Follow-up')
        OR (v_thesis_conn IS NOT NULL AND v_thesis_conn != '')
    );

    -- Bucket 1: Discover New
    IF v_has_new_company_signal THEN v_b1_score := v_b1_score + 0.4; END IF;
    IF v_action_type = 'Pipeline Action' THEN v_b1_score := v_b1_score + 0.3; END IF;
    IF v_combined_text ~ '(new|discover|scout|pipeline|first)' THEN v_b1_score := v_b1_score + 0.15; END IF;
    IF NOT v_has_portfolio_company AND v_company_notion_id IS NOT NULL THEN v_b1_score := v_b1_score + 0.2; END IF;

    -- Bucket 2: Deepen Existing (BOOSTED — user P0)
    IF v_has_portfolio_company THEN v_b2_score := v_b2_score + 0.5; END IF;
    IF v_action_type IN ('Portfolio Check-in', 'Follow-on Eval') THEN v_b2_score := v_b2_score + 0.35; END IF;
    IF v_combined_text ~ '(portfolio|follow.on|ownership|check.in|ids|competitive intel|deepen|existing)' THEN v_b2_score := v_b2_score + 0.2; END IF;

    -- Bucket 3: DeVC Collective (BOOSTED — user P1)
    IF v_has_network_signal AND v_combined_text ~ '(collective|devc|community|funnel)' THEN v_b3_score := v_b3_score + 0.4; END IF;
    IF v_action_type = 'Meeting/Outreach' THEN v_b3_score := v_b3_score + 0.2; END IF;
    IF v_combined_text ~ '(intro|connect|meet|network|relationship|outreach)' THEN v_b3_score := v_b3_score + 0.15; END IF;

    -- Bucket 4: Thesis Evolution (DEMOTED — agent work)
    IF v_has_thesis_signal THEN v_b4_score := v_b4_score + 0.3; END IF;
    IF v_action_type IN ('Thesis Update', 'Research') THEN v_b4_score := v_b4_score + 0.3; END IF;
    IF v_combined_text ~ '(thesis|conviction|framework|hypothesis|evolving|evidence)' THEN v_b4_score := v_b4_score + 0.2; END IF;
    IF v_action_type = 'Content Follow-up' THEN v_b4_score := v_b4_score + 0.15; END IF;

    -- USER PRIORITY REBALANCING
    v_b2_score := v_b2_score * 1.5;  -- 50% boost for portfolio
    v_b3_score := v_b3_score * 1.3;  -- 30% boost for network
    v_b4_score := v_b4_score * 0.6;  -- 40% penalty for thesis

    v_b1_score := LEAST(v_b1_score, 1.0);
    v_b2_score := LEAST(v_b2_score, 1.0);
    v_b3_score := LEAST(v_b3_score, 1.0);
    v_b4_score := LEAST(v_b4_score, 1.0);

    RETURN QUERY
    SELECT bk.bk_name, bk.bk_conf, bk.bk_reason
    FROM (
        VALUES
            ('Discover New (Bucket 1)'::TEXT, v_b1_score,
             ('Signals: ' ||
                CASE WHEN v_has_new_company_signal THEN 'new_company ' ELSE '' END ||
                CASE WHEN v_action_type = 'Pipeline Action' THEN 'pipeline_action ' ELSE '' END ||
                CASE WHEN NOT v_has_portfolio_company AND v_company_notion_id IS NOT NULL THEN 'non_portfolio_company ' ELSE '' END
             )::TEXT),
            ('Deepen Existing (Bucket 2)'::TEXT, v_b2_score,
             ('Signals: ' ||
                CASE WHEN v_has_portfolio_company THEN 'portfolio_company ' ELSE '' END ||
                CASE WHEN v_action_type IN ('Portfolio Check-in', 'Follow-on Eval') THEN 'portfolio_action_type ' ELSE '' END ||
                '[1.5x user-priority boost]'
             )::TEXT),
            ('DeVC Collective (Bucket 3)'::TEXT, v_b3_score,
             ('Signals: ' ||
                CASE WHEN v_has_network_signal THEN 'network_keywords ' ELSE '' END ||
                CASE WHEN v_action_type = 'Meeting/Outreach' THEN 'meeting_outreach_type ' ELSE '' END ||
                '[1.3x user-priority boost]'
             )::TEXT),
            ('Thesis Evolution (Bucket 4)'::TEXT, v_b4_score,
             ('Signals: ' ||
                CASE WHEN v_has_thesis_signal THEN 'thesis_keywords ' ELSE '' END ||
                CASE WHEN v_action_type IN ('Thesis Update', 'Research', 'Content Follow-up') THEN 'thesis_action_type ' ELSE '' END ||
                '[0.6x user-priority penalty]'
             )::TEXT)
    ) AS bk(bk_name, bk_conf, bk_reason)
    WHERE bk.bk_conf > 0
    ORDER BY bk.bk_conf DESC;
END;
$$;

-- Also fix score_action_thesis_relevance search_path for vector type resolution
ALTER FUNCTION score_action_thesis_relevance(integer) SET search_path = public, extensions;

-- Recreate action_scores materialized view
CREATE MATERIALIZED VIEW action_scores AS
SELECT
  a.id,
  a.action,
  a.action_type,
  a.status,
  a.priority,
  a.relevance_score,
  a.thesis_connection,
  a.created_at,
  (SELECT b.bucket FROM route_action_to_bucket(a.id) b LIMIT 1) AS primary_bucket,
  (SELECT b.confidence FROM route_action_to_bucket(a.id) b LIMIT 1) AS bucket_confidence,
  (SELECT b.reasoning FROM route_action_to_bucket(a.id) b LIMIT 1) AS bucket_reasoning,
  (SELECT COALESCE(json_agg(json_build_object(
    'thesis_id', t.thesis_id,
    'thesis_name', t.thesis_name,
    'relevance_score', t.relevance_score,
    'match_type', t.match_type
  )), '[]'::json)
   FROM (
     SELECT * FROM score_action_thesis_relevance(a.id)
     LIMIT 3
   ) t
  ) AS thesis_relevance
FROM actions_queue a
WHERE a.status = 'Proposed';

CREATE UNIQUE INDEX action_scores_id_idx ON action_scores (id);


-- =============================================================================
-- FIX 7: Add user_priority_score Column with Score Decay
-- Persists the computed priority score for sorting/indexing
-- =============================================================================

ALTER TABLE actions_queue ADD COLUMN IF NOT EXISTS user_priority_score numeric;

UPDATE actions_queue SET user_priority_score = compute_user_priority_score(actions_queue);


-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

-- V1: Score range should be 0-10 with no outliers
SELECT min(user_priority_score), max(user_priority_score), avg(user_priority_score), stddev(user_priority_score)
FROM actions_queue WHERE user_priority_score IS NOT NULL;

-- V2: User vs agent queue split
SELECT
  (SELECT count(*) FROM user_triage_queue WHERE NOT is_agent_delegable) as user_actions,
  (SELECT count(*) FROM agent_work_queue) as agent_actions;

-- V3: Top 10 user actions (should be portfolio/network heavy)
SELECT id, left(action, 80), action_type, priority, round(user_score::numeric, 2) as user_score
FROM user_triage_queue WHERE NOT is_agent_delegable
LIMIT 10;

-- V4: Top 10 agent actions (should be thesis/research heavy)
SELECT id, left(action, 80), action_type, priority
FROM agent_work_queue
LIMIT 10;

-- V5: Bucket distribution (should be portfolio-heavy, not thesis-heavy)
SELECT primary_bucket, count(*), round(avg(bucket_confidence)::numeric, 3)
FROM action_scores
GROUP BY primary_bucket
ORDER BY count(*) DESC;

-- V6: Priority labels clean
SELECT DISTINCT priority FROM actions_queue ORDER BY priority;

-- V7: Score coverage = 100%
SELECT count(*) as total,
  count(relevance_score) as has_relevance_score,
  count(user_priority_score) as has_user_priority_score,
  count(*) FILTER (WHERE relevance_score > 10) as scores_over_10
FROM actions_queue;


-- =============================================================================
-- M5 Loop 4 Fixes — 2026-03-20
-- Context: Fixes L4-1 (ceiling compression) and L4-2 (portfolio research misclassification)
-- from scoring-verify-m5-loop3.md
-- =============================================================================

-- =============================================================================
-- FIX L4-1: Ceiling Compression
-- Problem: 53% of actions (61/115) pinned at exactly 10.00
-- Root cause: Type boosts (+3, +2) + priority boosts (+2, +1) exceed 0-10 headroom
-- Solution: Reduced boost magnitudes + sigmoid-like soft cap at scale edges
-- =============================================================================

CREATE OR REPLACE FUNCTION compute_user_priority_score(action_row actions_queue)
RETURNS numeric AS $$
DECLARE
  base_score numeric;
  priority_boost numeric;
  type_boost numeric;
  recency_factor numeric;
  raw_score numeric;
BEGIN
  base_score := COALESCE(action_row.relevance_score, 5.0);

  -- REDUCED priority boost (was +2/+1/0/-1)
  priority_boost := CASE action_row.priority
    WHEN 'P0' THEN 1.0
    WHEN 'P1' THEN 0.5
    WHEN 'P2' THEN 0.0
    WHEN 'P3' THEN -0.5
    ELSE 0.0
  END;

  -- REDUCED type boost (was +3/+2/-3/-2)
  type_boost := CASE
    WHEN action_row.action_type ILIKE '%portfolio%' OR action_row.action_type ILIKE '%check-in%' OR action_row.action_type ILIKE '%follow-on%' THEN 1.5
    WHEN action_row.action_type ILIKE '%network%' OR action_row.action_type ILIKE '%meet%' OR action_row.action_type ILIKE '%connect%' OR action_row.action_type ILIKE '%outreach%' THEN 1.0
    WHEN action_row.action_type ILIKE '%thesis%' OR action_row.action_type ILIKE '%research%' OR action_row.action_type ILIKE '%evidence%' THEN -1.5
    WHEN action_row.action_type ILIKE '%content%' OR action_row.action_type ILIKE '%digest%' THEN -1.0
    ELSE 0.0
  END;

  -- Also check action text
  IF type_boost = 0.0 THEN
    type_boost := CASE
      WHEN action_row.action ILIKE '%portfolio%' OR action_row.action ILIKE '%check-in%' OR action_row.action ILIKE '%board%' THEN 1.0
      WHEN action_row.action ILIKE '%meet%' OR action_row.action ILIKE '%connect%' OR action_row.action ILIKE '%intro%' OR action_row.action ILIKE '%network%' THEN 0.8
      WHEN action_row.action ILIKE '%thesis%' OR action_row.action ILIKE '%research%' OR action_row.action ILIKE '%review evidence%' THEN -1.0
      ELSE 0.0
    END;
  END IF;

  -- Recency factor: halved magnitude (was 1.0 max, now 0.5 max), 30-day decay
  recency_factor := GREATEST(0, 0.5 * (1.0 - EXTRACT(EPOCH FROM (now() - COALESCE(action_row.created_at, now()))) / (30 * 86400)));

  raw_score := base_score + priority_boost + type_boost + recency_factor;

  -- Soft cap: sigmoid-like compression at edges instead of hard LEAST/GREATEST
  -- Preserves ordering even when scores cluster near boundaries
  RETURN CASE
    WHEN raw_score > 9.0 THEN 9.0 + (raw_score - 9.0) / (1.0 + (raw_score - 9.0))  -- compresses above 9
    WHEN raw_score < 1.0 THEN 1.0 - (1.0 - raw_score) / (1.0 + (1.0 - raw_score))  -- compresses below 1
    ELSE raw_score
  END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Recompute all scores
UPDATE actions_queue SET user_priority_score = compute_user_priority_score(actions_queue.*);


-- =============================================================================
-- FIX L4-2: Portfolio Research Misclassification
-- Problem: 24+ Research-typed portfolio diligence actions marked agent-delegable
-- Root cause: is_agent_delegable flag was based purely on action_type = 'Research'
-- Solution: Detect portfolio-diligence signals (keywords, assigned_to) and keep with user
-- =============================================================================

DROP VIEW IF EXISTS user_triage_queue;

CREATE VIEW user_triage_queue AS
SELECT
  aq.*,
  compute_user_priority_score(aq) as user_score,
  CASE
    -- Research assigned to 'Agent' is always delegable
    WHEN aq.action_type ILIKE '%research%' AND aq.assigned_to = 'Agent' THEN true

    -- Research with portfolio-diligence signals stays with user
    WHEN aq.action_type ILIKE '%research%' AND (
      -- Assigned to a human (non-empty, non-Agent)
      (aq.assigned_to IS NOT NULL AND aq.assigned_to != '' AND aq.assigned_to != 'Agent')
      -- Or has portfolio diligence keywords in action text
      OR aq.action ILIKE '%flag %' OR aq.action ILIKE '%request %'
      OR aq.action ILIKE '%commission %' OR aq.action ILIKE '%investigate %'
      OR aq.action ILIKE '%verify %' OR aq.action ILIKE '%resolve %'
      OR aq.action ILIKE '%schedule %' OR aq.action ILIKE '%unit economics%'
      OR aq.action ILIKE '%diligence%' OR aq.action ILIKE '%working capital%'
      OR aq.action ILIKE '%funding discrepan%' OR aq.action ILIKE '%SOC 2%'
      OR aq.action ILIKE '%team scaling%' OR aq.action ILIKE '%product quality%'
      OR aq.action ILIKE '%security review%'
    ) THEN false  -- Portfolio diligence stays with user

    -- Remaining Research (landscape mapping, thesis analysis) is delegable
    WHEN aq.action_type ILIKE '%research%' OR aq.action_type ILIKE '%evidence%' OR
         aq.action_type ILIKE '%content%' OR aq.action_type ILIKE '%thesis update%'
    THEN true
    WHEN aq.action ILIKE '%review evidence%' OR aq.action ILIKE '%analyze content%' OR
         aq.action ILIKE '%update thesis%'
    THEN true
    ELSE false
  END as is_agent_delegable
FROM actions_queue aq
WHERE aq.status = 'Proposed'
ORDER BY compute_user_priority_score(aq) DESC;


CREATE OR REPLACE VIEW agent_work_queue AS
SELECT aq.*
FROM actions_queue aq
WHERE aq.status = 'Proposed'
AND (
  -- Research assigned to Agent is delegable
  (aq.action_type ILIKE '%research%' AND aq.assigned_to = 'Agent')

  -- Research without portfolio-diligence signals is delegable
  OR (aq.action_type ILIKE '%research%'
      AND NOT (
        (aq.assigned_to IS NOT NULL AND aq.assigned_to != '' AND aq.assigned_to != 'Agent')
        OR aq.action ILIKE '%flag %' OR aq.action ILIKE '%request %'
        OR aq.action ILIKE '%commission %' OR aq.action ILIKE '%investigate %'
        OR aq.action ILIKE '%verify %' OR aq.action ILIKE '%resolve %'
        OR aq.action ILIKE '%schedule %' OR aq.action ILIKE '%unit economics%'
        OR aq.action ILIKE '%diligence%' OR aq.action ILIKE '%working capital%'
        OR aq.action ILIKE '%funding discrepan%' OR aq.action ILIKE '%SOC 2%'
        OR aq.action ILIKE '%team scaling%' OR aq.action ILIKE '%product quality%'
        OR aq.action ILIKE '%security review%'
      )
  )

  -- Non-research delegable types
  OR aq.action_type ILIKE '%evidence%'
  OR aq.action_type ILIKE '%content%'
  OR aq.action_type ILIKE '%thesis update%'
  OR aq.action ILIKE '%review evidence%'
  OR aq.action ILIKE '%analyze content%'
  OR aq.action ILIKE '%update thesis%'
);


-- Refresh materialized view with new scores
REFRESH MATERIALIZED VIEW CONCURRENTLY action_scores;


-- =============================================================================
-- LOOP 4 VALIDATION QUERIES
-- =============================================================================

-- V-L4-1: Score distribution (should have better spread, zero at ceiling)
SELECT
  width_bucket(user_priority_score, 0, 10, 10) as bucket,
  count(*),
  min(user_priority_score)::numeric(5,2), max(user_priority_score)::numeric(5,2)
FROM actions_queue
GROUP BY 1 ORDER BY 1;

-- V-L4-2: No more ceiling compression
SELECT count(*) FILTER (WHERE user_priority_score >= 9.9) as near_ceiling FROM actions_queue;

-- V-L4-3: Portfolio research correctly in user queue
SELECT id, LEFT(action, 80), action_type, is_agent_delegable
FROM user_triage_queue
WHERE action_type ILIKE '%research%' AND NOT is_agent_delegable
LIMIT 10;

-- V-L4-4: Queue counts
SELECT
  (SELECT count(*) FROM user_triage_queue WHERE NOT is_agent_delegable) as user_q,
  (SELECT count(*) FROM agent_work_queue) as agent_q;

-- V-L4-5: Top 10 should have VARYING scores, not all 10.00
SELECT id, LEFT(action, 60), user_priority_score::numeric(5,2), action_type, priority
FROM actions_queue ORDER BY user_priority_score DESC LIMIT 10;
