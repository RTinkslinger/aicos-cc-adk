-- v2.3 Cindy Conversation Log + Obligation Generator v2
-- Applied: 2026-03-22 (M8 Loop 5)
-- Purpose: FB-33 conversation memory + obligation pipeline restart

-- ============================================================================
-- 1. cindy_conversation_log table — FB-33 perpetual context
-- ============================================================================
-- Records every Cindy-user exchange per obligation/person.
-- This IS the RL loop: user responses become Cindy's training signal.

CREATE TABLE IF NOT EXISTS cindy_conversation_log (
  id SERIAL PRIMARY KEY,
  person_id INT REFERENCES network(id),
  person_name TEXT NOT NULL,
  obligation_id INT REFERENCES obligations(id),
  action_id INT,
  exchange_type TEXT NOT NULL DEFAULT 'decision',
  cindy_suggestion JSONB NOT NULL DEFAULT '{}',
  user_response JSONB NOT NULL DEFAULT '{}',
  context_snapshot JSONB DEFAULT '{}',
  surface TEXT NOT NULL DEFAULT 'webfront',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT valid_exchange_type CHECK (exchange_type IN (
    'decision', 'feedback', 'override', 'dismissal', 'escalation', 'followup'
  ))
);

CREATE INDEX IF NOT EXISTS idx_cindy_conv_person ON cindy_conversation_log(person_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cindy_conv_obligation ON cindy_conversation_log(obligation_id) WHERE obligation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_cindy_conv_type ON cindy_conversation_log(exchange_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cindy_conv_recent ON cindy_conversation_log(created_at DESC);

-- ============================================================================
-- 2. Extended user_feedback_store constraint for Cindy exchange types
-- ============================================================================

-- ALTER TABLE user_feedback_store DROP CONSTRAINT user_feedback_store_feedback_type_check;
-- ALTER TABLE user_feedback_store ADD CONSTRAINT user_feedback_store_feedback_type_check
--   CHECK (feedback_type = ANY(ARRAY[
--     'accept', 'dismiss', 'rate_quality', 'flag_wrong', 'flag_missing',
--     'comment', 'preference', 'UX', 'Intelligence', 'Data', 'Bug', 'General',
--     'task_response', 'cindy_decision', 'cindy_dismissal', 'cindy_override', 'cindy_feedback'
--   ]));

-- ============================================================================
-- 3. New functions:
--    - cindy_obligation_auto_generator_v2(mode, batch_size, obligations)
--    - cindy_conversation_log(mode, person_id, obligation_id, exchange, limit)
--    - cindy_task_auto_process upgraded with obligation_action + relationship_intelligence
-- ============================================================================
-- See Supabase for live function definitions (too large for SQL file).
-- Functions created via execute_sql during M8 L5.
