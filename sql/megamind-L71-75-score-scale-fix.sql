-- M7 Megamind L71-75: Score Scale Fix & Briefing v5.0
-- Applied: 2026-03-21
-- Fixes: 3 column blockers, 2 root cause functions, 1 CHECK constraint, briefing v5.0

-- =============================================================================
-- FIX 1: Normalize existing strategic_scores from 1-10 to 0-1
-- =============================================================================
UPDATE actions_queue
SET strategic_score = strategic_score / 10.0
WHERE strategic_score > 1.0;

-- =============================================================================
-- FIX 2: CHECK constraint to permanently prevent scale corruption
-- =============================================================================
ALTER TABLE actions_queue ADD CONSTRAINT strategic_score_0_1_scale
  CHECK (strategic_score IS NULL OR (strategic_score >= 0 AND strategic_score <= 1.0));

-- =============================================================================
-- FIX 3: recalibrate_strategic_scores() - output 0-1 (was 0-10)
-- Key change: v_final divided by 10.0 before return
-- =============================================================================
-- See function definition in Supabase (applied via execute_sql)

-- =============================================================================
-- FIX 4: auto_generate_obligation_followup_actions() - set both scores on creation
-- Key change: INSERT now includes relevance_score and strategic_score
-- =============================================================================
-- See function definition in Supabase (applied via execute_sql)

-- =============================================================================
-- FIX 5: format_strategic_briefing() v5.0
-- Key changes:
--   - Scores displayed as /10 in DECISIONS and OBLIGATIONS sections
--   - Convergence health indicator in header [HEALTHY/OK/WARN/CRITICAL ratio]
--   - OBLIGATION section uses strategic_score instead of user_priority_score
--   - Version bump to v5.0
-- =============================================================================
-- See function definition in Supabase (applied via execute_sql)

-- =============================================================================
-- FIX 6: megamind_system_report() v5.1-L75
-- Key changes:
--   - convergence_health field added
--   - score_scale documentation
--   - blockers_fixed field
--   - recalibrate/apply tools added to catalog
-- =============================================================================
-- See function definition in Supabase (applied via execute_sql)
