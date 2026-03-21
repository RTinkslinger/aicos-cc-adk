-- Megamind L80: Strategic Contradictions + Decision Ranking Fix + Briefing History
-- Date: 2026-03-21
-- Purpose: Three improvements to the strategic intelligence layer:
--
-- 1. STRATEGIC CONTRADICTIONS section in format_strategic_briefing()
--    - Red health + SPR/PR follow-on (doubling down on struggling companies)
--    - Red/P0-P1 companies with ZERO open actions (invisible problems)
--    - Expired fumes_date >180d (stale runway data)
--
-- 2. Decision ranking fix in actions_needing_decision_v2()
--    - CRITICAL BUG FIX: portfolio join used notion_page_id, should be company_name_id
--    - Red/Yellow + high ownership weight increased from 10% to 20%
--    - Green "Flag risk" actions penalized -1.5 impact score
--    - Red company with zero other actions gets +1.0 bonus
--    - Same join fix applied to generate_strategic_narrative() open_actions counts
--
-- 3. briefing_history table + daily cron
--    - CREATE TABLE briefing_history (id, briefing_date UNIQUE, briefing_text, assessment_jsonb)
--    - store_daily_briefing() function with UPSERT
--    - latest_briefing() function for WebFront consumption
--    - pg_cron job at 06:15 UTC daily
--
-- Impact: Before this fix, top 9/9 decision queue items were "Flag risk" on Green
--         companies. After: Yellow Stance Health ranks #1, obligations surface,
--         Green flag risks drop out of top 20.

-- ============================================================
-- All changes were applied via execute_sql (not migration tool).
-- This file documents what was deployed to Supabase project llfkxnsfczludgigknbs.
-- ============================================================

-- TABLE: briefing_history
CREATE TABLE IF NOT EXISTS briefing_history (
  id SERIAL PRIMARY KEY,
  briefing_date DATE NOT NULL,
  briefing_text TEXT NOT NULL,
  assessment_jsonb JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_briefing_history_date ON briefing_history (briefing_date);
CREATE INDEX IF NOT EXISTS idx_briefing_history_created ON briefing_history (created_at DESC);

-- FUNCTION: latest_briefing()
-- Returns the most recent daily briefing for WebFront
CREATE OR REPLACE FUNCTION latest_briefing()
RETURNS TABLE(briefing_date date, briefing_text text, assessment_jsonb jsonb, created_at timestamptz)
LANGUAGE sql STABLE
AS $$
  SELECT bh.briefing_date, bh.briefing_text, bh.assessment_jsonb, bh.created_at
  FROM briefing_history bh
  ORDER BY bh.briefing_date DESC
  LIMIT 1;
$$;

-- FUNCTION: store_daily_briefing()
-- Called by cron, generates and stores the daily briefing with structured assessment data
-- See full function body in Supabase (deployed via execute_sql)

-- CRON: daily-strategic-briefing
-- Schedule: '15 6 * * *' (06:15 UTC daily)
-- Command: SELECT store_daily_briefing()
-- Job ID: 20

-- KEY FIX: actions_needing_decision_v2() and generate_strategic_narrative()
-- Changed all portfolio joins from:
--   portfolio p WHERE p.notion_page_id = aq.company_notion_id
-- To:
--   portfolio p WHERE p.company_name_id = aq.company_notion_id
-- Because company_notion_id on actions_queue references the COMPANIES table notion_page_id,
-- and portfolio.company_name_id is the FK to companies, not portfolio.notion_page_id.
