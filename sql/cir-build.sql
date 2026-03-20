-- =============================================================================
-- CIR Build: Continuous Intelligence Refresh — Phase 1 (Foundation) + Phase 2 (Mechanical Propagation)
-- Supabase project: llfkxnsfczludgigknbs
-- Executed: 2026-03-20
-- =============================================================================

-- Prerequisites: pgmq 1.5.1, pg_cron 1.6.4, pg_net 0.20.0 (all pre-installed)

-- =============================================================================
-- PHASE 1: FOUNDATION (Tables + Queue)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Step 1: Create CIR Tables
-- -----------------------------------------------------------------------------

-- 1a. cir_propagation_rules: configures what triggers what
CREATE TABLE IF NOT EXISTS cir_propagation_rules (
  id serial PRIMARY KEY,
  source_table text NOT NULL,
  source_event text NOT NULL,        -- INSERT, UPDATE, DELETE
  target_action text NOT NULL,        -- function/handler to call
  significance text NOT NULL DEFAULT 'low', -- none/low/medium/high/critical
  enabled boolean NOT NULL DEFAULT true,
  config jsonb DEFAULT '{}'
);

-- 1b. entity_connections: tracks relationships between entities
CREATE TABLE IF NOT EXISTS entity_connections (
  id serial PRIMARY KEY,
  source_type text NOT NULL,          -- companies, network, portfolio, thesis_threads, actions_queue
  source_id integer NOT NULL,
  target_type text NOT NULL,
  target_id integer NOT NULL,
  connection_type text NOT NULL,      -- vector_similarity, explicit, thesis_link, interaction
  strength numeric NOT NULL DEFAULT 0.5,
  decay_factor numeric NOT NULL DEFAULT 0.98,
  evidence_count integer NOT NULL DEFAULT 1,
  last_evidence_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(source_type, source_id, target_type, target_id, connection_type)
);

-- 1c. preference_weight_adjustments: learned scoring modifiers
CREATE TABLE IF NOT EXISTS preference_weight_adjustments (
  id serial PRIMARY KEY,
  dimension text NOT NULL,            -- action_type, priority, source, thesis
  dimension_value text NOT NULL,
  weight_adjustment numeric NOT NULL DEFAULT 0,
  sample_count integer NOT NULL DEFAULT 0,
  last_updated_at timestamptz DEFAULT now(),
  UNIQUE(dimension, dimension_value)
);

-- 1d. cir_state: tracks propagation state
CREATE TABLE IF NOT EXISTS cir_state (
  key text PRIMARY KEY,
  value jsonb NOT NULL,
  updated_at timestamptz DEFAULT now()
);

-- 1e. cir_propagation_log: audit trail
CREATE TABLE IF NOT EXISTS cir_propagation_log (
  id serial PRIMARY KEY,
  source_table text NOT NULL,
  source_id integer,
  event_type text NOT NULL,
  significance text NOT NULL,
  actions_taken jsonb,
  created_at timestamptz DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_entity_connections_source ON entity_connections(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_entity_connections_target ON entity_connections(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_entity_connections_strength ON entity_connections(strength DESC);
CREATE INDEX IF NOT EXISTS idx_cir_log_recent ON cir_propagation_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pref_weights ON preference_weight_adjustments(dimension, dimension_value);

-- -----------------------------------------------------------------------------
-- Step 2: Seed Propagation Rules
-- -----------------------------------------------------------------------------

INSERT INTO cir_propagation_rules (source_table, source_event, target_action, significance) VALUES
('content_digests', 'INSERT', 'rescore_related_actions', 'medium'),
('thesis_threads', 'UPDATE', 'update_thesis_indicators', 'high'),
('actions_queue', 'INSERT', 'process_new_action', 'medium'),
('action_outcomes', 'INSERT', 'update_preference_weights', 'high'),
('interactions', 'INSERT', 'process_new_interaction', 'medium'),
('network', 'UPDATE', 'refresh_person_connections', 'low'),
('companies', 'UPDATE', 'refresh_company_connections', 'low');

-- -----------------------------------------------------------------------------
-- Step 3: Change Detection Trigger Function
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION cir_change_detected()
RETURNS trigger AS $$
DECLARE
  rule RECORD;
  record_id integer;
BEGIN
  -- Get the record ID from NEW (or OLD for DELETE)
  IF TG_OP = 'DELETE' THEN
    record_id := OLD.id;
  ELSE
    record_id := NEW.id;
  END IF;

  -- Look up propagation rules for this table + event
  FOR rule IN
    SELECT * FROM cir_propagation_rules
    WHERE source_table = TG_TABLE_NAME
    AND source_event = TG_OP
    AND enabled = true
  LOOP
    -- Log the change
    INSERT INTO cir_propagation_log (source_table, source_id, event_type, significance, actions_taken)
    VALUES (TG_TABLE_NAME, record_id, TG_OP, rule.significance,
      jsonb_build_object('target_action', rule.target_action, 'rule_id', rule.id));

    -- Enqueue for processing via pgmq
    BEGIN
      PERFORM pgmq.send('cir_queue', jsonb_build_object(
        'source_table', TG_TABLE_NAME,
        'source_id', record_id,
        'event', TG_OP,
        'target_action', rule.target_action,
        'significance', rule.significance,
        'rule_id', rule.id,
        'timestamp', now()
      ));
    EXCEPTION WHEN OTHERS THEN
      -- pgmq queue might not exist yet, just log
      NULL;
    END;
  END LOOP;

  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  ELSE
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- Step 4: Create pgmq Queue + Install Triggers
-- -----------------------------------------------------------------------------

SELECT pgmq.create('cir_queue');

-- Install triggers on key tables
DROP TRIGGER IF EXISTS cir_actions_queue ON actions_queue;
CREATE TRIGGER cir_actions_queue
  AFTER INSERT OR UPDATE ON actions_queue
  FOR EACH ROW EXECUTE FUNCTION cir_change_detected();

DROP TRIGGER IF EXISTS cir_thesis_threads ON thesis_threads;
CREATE TRIGGER cir_thesis_threads
  AFTER INSERT OR UPDATE ON thesis_threads
  FOR EACH ROW EXECUTE FUNCTION cir_change_detected();

DROP TRIGGER IF EXISTS cir_content_digests ON content_digests;
CREATE TRIGGER cir_content_digests
  AFTER INSERT ON content_digests
  FOR EACH ROW EXECUTE FUNCTION cir_change_detected();

DROP TRIGGER IF EXISTS cir_network ON network;
CREATE TRIGGER cir_network
  AFTER INSERT OR UPDATE ON network
  FOR EACH ROW EXECUTE FUNCTION cir_change_detected();

DROP TRIGGER IF EXISTS cir_action_outcomes ON action_outcomes;
CREATE TRIGGER cir_action_outcomes
  AFTER INSERT ON action_outcomes
  FOR EACH ROW EXECUTE FUNCTION cir_change_detected();

DROP TRIGGER IF EXISTS cir_interactions ON interactions;
CREATE TRIGGER cir_interactions
  AFTER INSERT ON interactions
  FOR EACH ROW EXECUTE FUNCTION cir_change_detected();

DROP TRIGGER IF EXISTS cir_companies ON companies;
CREATE TRIGGER cir_companies
  AFTER UPDATE ON companies
  FOR EACH ROW EXECUTE FUNCTION cir_change_detected();

-- =============================================================================
-- PHASE 2: PREFERENCE LEARNING + CRON JOBS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Step 5: Preference Weight Update Function
-- -----------------------------------------------------------------------------

-- Adapted from spec: uses priority + source instead of bucket
-- (actions_queue has no bucket column; bucket is computed in action_scores matview)
CREATE OR REPLACE FUNCTION update_preference_from_outcome(p_action_id integer, p_outcome text)
RETURNS void AS $$
DECLARE
  action_rec RECORD;
  weight_delta numeric;
BEGIN
  SELECT * INTO action_rec FROM actions_queue WHERE id = p_action_id;
  IF NOT FOUND THEN RETURN; END IF;

  -- Map outcome to weight delta
  weight_delta := CASE p_outcome
    WHEN 'gold' THEN 0.3
    WHEN 'helpful' THEN 0.1
    WHEN 'skip' THEN -0.2
    ELSE 0.0
  END;

  -- Update action_type preference
  IF action_rec.action_type IS NOT NULL THEN
    INSERT INTO preference_weight_adjustments (dimension, dimension_value, weight_adjustment, sample_count)
    VALUES ('action_type', action_rec.action_type, weight_delta, 1)
    ON CONFLICT (dimension, dimension_value) DO UPDATE SET
      weight_adjustment = (preference_weight_adjustments.weight_adjustment * preference_weight_adjustments.sample_count + weight_delta) / (preference_weight_adjustments.sample_count + 1),
      sample_count = preference_weight_adjustments.sample_count + 1,
      last_updated_at = now();
  END IF;

  -- Update priority preference
  IF action_rec.priority IS NOT NULL THEN
    INSERT INTO preference_weight_adjustments (dimension, dimension_value, weight_adjustment, sample_count)
    VALUES ('priority', action_rec.priority, weight_delta, 1)
    ON CONFLICT (dimension, dimension_value) DO UPDATE SET
      weight_adjustment = (preference_weight_adjustments.weight_adjustment * preference_weight_adjustments.sample_count + weight_delta) / (preference_weight_adjustments.sample_count + 1),
      sample_count = preference_weight_adjustments.sample_count + 1,
      last_updated_at = now();
  END IF;

  -- Update source preference
  IF action_rec.source IS NOT NULL THEN
    INSERT INTO preference_weight_adjustments (dimension, dimension_value, weight_adjustment, sample_count)
    VALUES ('source', action_rec.source, weight_delta, 1)
    ON CONFLICT (dimension, dimension_value) DO UPDATE SET
      weight_adjustment = (preference_weight_adjustments.weight_adjustment * preference_weight_adjustments.sample_count + weight_delta) / (preference_weight_adjustments.sample_count + 1),
      sample_count = preference_weight_adjustments.sample_count + 1,
      last_updated_at = now();
  END IF;

  -- Update thesis_connection preference
  IF action_rec.thesis_connection IS NOT NULL THEN
    INSERT INTO preference_weight_adjustments (dimension, dimension_value, weight_adjustment, sample_count)
    VALUES ('thesis', action_rec.thesis_connection, weight_delta, 1)
    ON CONFLICT (dimension, dimension_value) DO UPDATE SET
      weight_adjustment = (preference_weight_adjustments.weight_adjustment * preference_weight_adjustments.sample_count + weight_delta) / (preference_weight_adjustments.sample_count + 1),
      sample_count = preference_weight_adjustments.sample_count + 1,
      last_updated_at = now();
  END IF;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- Step 6: pg_cron Jobs
-- -----------------------------------------------------------------------------

-- 6a. Connection decay: daily at 3 AM IST (21:30 UTC)
SELECT cron.schedule('cir-connection-decay', '30 21 * * *', $$
  UPDATE entity_connections
  SET strength = strength * decay_factor,
      updated_at = now()
  WHERE strength > 0.1;
  DELETE FROM entity_connections WHERE strength <= 0.1;
$$);

-- 6b. Materialized view refresh: every 15 minutes
SELECT cron.schedule('cir-matview-refresh', '*/15 * * * *', $$
  REFRESH MATERIALIZED VIEW CONCURRENTLY action_scores;
$$);

-- 6c. Staleness check: hourly
SELECT cron.schedule('cir-staleness-check', '0 * * * *', $$
  INSERT INTO cir_propagation_log (source_table, source_id, event_type, significance, actions_taken)
  SELECT 'actions_queue', id, 'STALE_CHECK', 'low',
    jsonb_build_object('staleness_days', EXTRACT(DAY FROM now() - created_at))
  FROM actions_queue
  WHERE status = 'Proposed'
  AND created_at < now() - interval '14 days'
  AND id NOT IN (
    SELECT source_id FROM cir_propagation_log
    WHERE event_type = 'STALE_CHECK'
    AND created_at > now() - interval '1 day'
    AND source_id IS NOT NULL
  );
$$);

-- 6d. CIR queue processor: every minute
SELECT cron.schedule('cir-queue-processor', '* * * * *', $$
  WITH items AS (
    SELECT msg_id, message FROM pgmq.read('cir_queue', 60, 10)
  ),
  archived AS (
    SELECT pgmq.archive('cir_queue', msg_id) FROM items
  )
  INSERT INTO cir_propagation_log (source_table, source_id, event_type, significance, actions_taken)
  SELECT
    message->>'source_table',
    (message->>'source_id')::integer,
    'QUEUE_PROCESSED',
    COALESCE(message->>'significance', 'low'),
    jsonb_build_object(
      'target_action', message->>'target_action',
      'queued_at', message->>'timestamp',
      'processed_at', now()
    )
  FROM items;
$$);

-- -----------------------------------------------------------------------------
-- Seed Initial CIR State
-- -----------------------------------------------------------------------------

INSERT INTO cir_state (key, value) VALUES
('system_version', '"1.0.0"'::jsonb),
('installed_at', to_jsonb(now()::text)),
('phase', '"foundation"'::jsonb),
('config', jsonb_build_object(
  'queue_batch_size', 10,
  'decay_factor_default', 0.98,
  'staleness_threshold_days', 14,
  'matview_refresh_interval_min', 15
))
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();
