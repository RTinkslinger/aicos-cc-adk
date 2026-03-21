-- M7 Megamind v3.0-thesis-delta Migration
-- Date: 2026-03-21
-- Changes:
--   1. format_strategic_briefing() v3.0: 5 contradiction types, thesis intelligence, day-over-day delta
--   2. store_daily_briefing() v2: enriched assessment_jsonb with convergence, stale%, thesis_flags
--   3. auto_dismiss_stale_actions(): new function for automated stale action cleanup
--   4. pg_cron job: daily auto-dismiss at 06:00 UTC

-- ============================================================
-- 1. auto_dismiss_stale_actions()
-- ============================================================
CREATE OR REPLACE FUNCTION auto_dismiss_stale_actions()
RETURNS TABLE(action_id INT, action_text TEXT, reason TEXT, old_score NUMERIC)
LANGUAGE plpgsql
AS $function$
DECLARE
  r RECORD;
BEGIN
  -- Rule 1: Very low score (< 3) AND stale (> 14 days) AND no obligation
  FOR r IN
    SELECT aq.id, LEFT(aq.action, 100) as action_preview, aq.user_priority_score,
      EXTRACT(DAY FROM NOW() - aq.created_at)::int as age_days
    FROM actions_queue aq
    WHERE aq.status = 'Proposed'
      AND aq.user_priority_score < 3
      AND aq.created_at < NOW() - INTERVAL '14 days'
      AND NOT EXISTS (SELECT 1 FROM obligations o WHERE o.linked_action_id = aq.id AND o.status NOT IN ('fulfilled', 'dismissed'))
  LOOP
    UPDATE actions_queue SET
      status = 'Dismissed',
      triage_history = COALESCE(triage_history, '[]'::jsonb) || jsonb_build_object(
        'action', 'auto_dismiss', 'reason', 'stale_very_low_score',
        'score', r.user_priority_score, 'age_days', r.age_days,
        'dismissed_at', NOW()::text, 'dismissed_by', 'megamind_auto'),
      updated_at = NOW()
    WHERE id = r.id;
    action_id := r.id; action_text := r.action_preview;
    reason := 'stale_very_low_score (age: ' || r.age_days || 'd, score: ' || round(r.user_priority_score, 2) || ')';
    old_score := r.user_priority_score;
    RETURN NEXT;
  END LOOP;

  -- Rule 2: "Flag risk" or "Monitor for" actions with score < 5 and stale > 14 days
  FOR r IN
    SELECT aq.id, LEFT(aq.action, 100) as action_preview, aq.user_priority_score,
      EXTRACT(DAY FROM NOW() - aq.created_at)::int as age_days
    FROM actions_queue aq
    WHERE aq.status = 'Proposed'
      AND (aq.action ILIKE 'Flag%risk%' OR aq.action ILIKE 'Monitor for%')
      AND aq.user_priority_score < 5
      AND aq.created_at < NOW() - INTERVAL '14 days'
      AND NOT EXISTS (SELECT 1 FROM obligations o WHERE o.linked_action_id = aq.id AND o.status NOT IN ('fulfilled', 'dismissed'))
      AND aq.user_priority_score >= 3  -- don't double-count rule 1
  LOOP
    UPDATE actions_queue SET
      status = 'Dismissed',
      triage_history = COALESCE(triage_history, '[]'::jsonb) || jsonb_build_object(
        'action', 'auto_dismiss', 'reason', 'stale_flag_risk',
        'score', r.user_priority_score, 'age_days', r.age_days,
        'dismissed_at', NOW()::text, 'dismissed_by', 'megamind_auto'),
      updated_at = NOW()
    WHERE id = r.id;
    action_id := r.id; action_text := r.action_preview;
    reason := 'stale_flag_risk (age: ' || r.age_days || 'd, score: ' || round(r.user_priority_score, 2) || ')';
    old_score := r.user_priority_score;
    RETURN NEXT;
  END LOOP;

  RETURN;
END;
$function$;

-- ============================================================
-- 2. pg_cron: daily auto-dismiss at 06:00 UTC
-- ============================================================
-- SELECT cron.schedule('megamind_auto_dismiss', '0 6 * * *', 'SELECT * FROM auto_dismiss_stale_actions()');

-- ============================================================
-- 3. store_daily_briefing() v2
-- ============================================================
-- See function definition in audit report.
-- Key additions to assessment_jsonb:
--   convergence_ratio, stale_pct, overdue_obligations,
--   contradiction_count, thesis_flags[], version

-- ============================================================
-- 4. format_strategic_briefing() v3.0-thesis-delta
-- ============================================================
-- See function definition in audit report.
-- Key additions:
--   Section 4: Thesis Intelligence (flagged + clean thesis threads)
--   Contradiction type 4: Silent winners (Green >2% zero actions)
--   Contradiction type 5: SPR idle (SPR/PR non-Red zero actions)
--   Header: Day-over-day delta from briefing_history
