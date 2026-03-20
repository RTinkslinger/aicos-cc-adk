-- Actions Intelligence Quality Fixes (M9 Audit Response)
-- Date: 2026-03-20
-- Purpose: Fix 5 systemic quality issues found by M9 audit (scored 5.5/10, target 7+)
-- Applied live to Supabase project llfkxnsfczludgigknbs

-- =============================================================================
-- FIX 1: Reclassify 27 mistyped Research actions
-- =============================================================================
-- 24 "Research" actions contain user-action verbs (Flag, Request, Schedule, etc.)
-- These were suppressed by the -1.5 type_boost penalty, ranking urgent P0 diligence
-- actions below routine P1 portfolio check-ins.

-- 1a: Schedule/Commission actions -> Meeting/Outreach (3 actions)
UPDATE actions_queue
SET action_type = 'Meeting/Outreach'
WHERE id IN (34, 56, 66)
AND action_type = 'Research';
-- id:34 "Schedule urgent team scaling call..."
-- id:56 "Commission independent lab testing..."
-- id:66 "Schedule product security review..."

-- 1b: Flag/Request/Investigate/Verify/Resolve/Portfolio-check-in -> Portfolio Check-in (24 actions)
UPDATE actions_queue
SET action_type = 'Portfolio Check-in'
WHERE id IN (4, 12, 13, 16, 18, 24, 25, 27, 31, 35, 36, 37, 38, 46, 47, 60, 62, 64, 67, 71, 72, 81, 99, 100)
AND action_type = 'Research';

-- NOTE: id:110 "Research which SaaS categories survive..." was excluded despite matching
-- '%resolve%' in the action text. The word "resolve" in that context means "understand/figure out"
-- (a Miles Clements vs Jerry Murdock contradiction), not "resolve an issue with a company."

-- =============================================================================
-- FIX 2: Dismiss confirmed duplicate (id:68)
-- =============================================================================
-- Audit flagged 3 HIGH-severity duplicate pairs: (2,68), (67,71), (36,62)
-- Investigation found:
--   (2, 68): TRUE DUPLICATE - both about Orange Slice trademark risk. Keep id:2 (P0, more detail)
--   (67, 71): NOT duplicate - different companies (Tracxn $1.89M vs $7.28M, different entities)
--   (36, 62): NOT duplicate - different companies (agritech/₹36.46L vs manufacturing/Häfele)

UPDATE actions_queue
SET status = 'Dismissed',
    outcome = 'Duplicate of action id:2 (same Orange Slice trademark risk). Dismissed during M9 intelligence quality fix.'
WHERE id = 68;

-- =============================================================================
-- FIX 3: Populate scoring_factors with multi-factor model
-- =============================================================================
-- 39 actions had empty {} scoring_factors, 76 had only legacy_thesis_note (string).
-- The multi-factor scoring model (bucket_impact, time_sensitivity, action_novelty,
-- effort_vs_impact, conviction_change_potential) was not implemented.

-- 3a: Populate empty scoring_factors (39 actions)
UPDATE actions_queue SET scoring_factors = jsonb_build_object(
  'bucket_impact', CASE action_type
    WHEN 'Portfolio Check-in' THEN 0.8
    WHEN 'Meeting/Outreach' THEN 0.7
    WHEN 'Pipeline Action' THEN 0.6
    WHEN 'Thesis Update' THEN 0.5
    WHEN 'Research' THEN 0.4
    WHEN 'Content Follow-up' THEN 0.3
    ELSE 0.5 END,
  'time_sensitivity', CASE priority
    WHEN 'P0' THEN 0.9
    WHEN 'P1' THEN 0.6
    WHEN 'P2' THEN 0.3
    ELSE 0.2 END,
  'action_novelty', 0.5,
  'effort_vs_impact', CASE action_type
    WHEN 'Meeting/Outreach' THEN 0.7
    WHEN 'Portfolio Check-in' THEN 0.6
    WHEN 'Pipeline Action' THEN 0.5
    WHEN 'Research' THEN 0.4
    WHEN 'Thesis Update' THEN 0.4
    ELSE 0.5 END,
  'conviction_change_potential', COALESCE(irgi_relevance_score, 0.5)
)
WHERE scoring_factors = '{}'::jsonb;

-- 3b: Add multi-factor fields alongside legacy_thesis_note (72 actions)
UPDATE actions_queue SET scoring_factors = scoring_factors || jsonb_build_object(
  'bucket_impact', CASE action_type
    WHEN 'Portfolio Check-in' THEN 0.8
    WHEN 'Meeting/Outreach' THEN 0.7
    WHEN 'Pipeline Action' THEN 0.6
    WHEN 'Thesis Update' THEN 0.5
    WHEN 'Research' THEN 0.4
    WHEN 'Content Follow-up' THEN 0.3
    ELSE 0.5 END,
  'time_sensitivity', CASE priority
    WHEN 'P0' THEN 0.9
    WHEN 'P1' THEN 0.6
    WHEN 'P2' THEN 0.3
    ELSE 0.2 END,
  'action_novelty', 0.5,
  'effort_vs_impact', CASE action_type
    WHEN 'Meeting/Outreach' THEN 0.7
    WHEN 'Portfolio Check-in' THEN 0.6
    WHEN 'Pipeline Action' THEN 0.5
    WHEN 'Research' THEN 0.4
    WHEN 'Thesis Update' THEN 0.4
    ELSE 0.5 END,
  'conviction_change_potential', COALESCE(irgi_relevance_score, 0.5)
)
WHERE scoring_factors IS NOT NULL
  AND scoring_factors != '{}'::jsonb
  AND NOT (scoring_factors ? 'bucket_impact');

-- 3c: Normalize 4 actions (101-104) that had old-format scoring_factors
UPDATE actions_queue SET scoring_factors = scoring_factors || jsonb_build_object(
  'conviction_change_potential', COALESCE(irgi_relevance_score, 0.5)
)
WHERE id IN (101, 102, 103, 104);

-- =============================================================================
-- FIX 4: Recompute scores after reclassification
-- =============================================================================
UPDATE actions_queue
SET user_priority_score = compute_user_priority_score(actions_queue.*);

-- =============================================================================
-- FIX 5: Refresh materialized view
-- =============================================================================
REFRESH MATERIALIZED VIEW CONCURRENTLY action_scores;

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

-- V1: No remaining misclassified Research
-- SELECT count(*) FROM actions_queue WHERE action_type = 'Research'
-- AND (action ILIKE '%schedule%' OR action ILIKE '%request%' OR action ILIKE '%flag%'
--   OR action ILIKE '%commission%' OR action ILIKE '%investigate%');
-- Expected: 0

-- V2: Duplicate dismissed
-- SELECT id, status FROM actions_queue WHERE id = 68;
-- Expected: Dismissed

-- V3: scoring_factors populated
-- SELECT count(*) FILTER (WHERE scoring_factors ? 'bucket_impact') as populated,
--   count(*) as total FROM actions_queue;
-- Expected: 115/115

-- V4: Score distribution
-- SELECT action_type, count(*), avg(user_priority_score)::numeric(5,2)
-- FROM actions_queue WHERE status != 'Dismissed'
-- GROUP BY action_type ORDER BY count(*) DESC;
