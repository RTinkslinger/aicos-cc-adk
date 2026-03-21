-- M10 CIR L66-75: Honest System Health, Connection Pool, Embedding Recovery, Feedback Store
-- Date: 2026-03-21
--
-- Changes:
-- 1. system_health_aggregate() rewritten for honest product quality (was B+ 7.2, now C 5.2)
-- 2. connection_pool_status() new function for pool monitoring
-- 3. terminate_idle_connections() new function for safe idle connection cleanup
-- 4. embedding_recovery_dashboard() new function for recovery tracking
-- 5. agent_feedback_store + user_feedback_store tables with RLS
-- 6. feedback_summary view

-- ============================================================================
-- 1. HONEST system_health_aggregate()
-- ============================================================================
CREATE OR REPLACE FUNCTION system_health_aggregate()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_start TIMESTAMPTZ := clock_timestamp();
  v_companies_total INT;
  v_companies_rich INT;
  v_companies_stub INT;
  v_companies_avg_len INT;
  v_network_total INT;
  v_network_rich INT;
  v_network_stub INT;
  v_network_avg_len INT;
  v_data_richness_score NUMERIC;
  v_co_embedded INT;
  v_net_embedded INT;
  v_port_embedded INT;
  v_port_total INT;
  v_embedding_score NUMERIC;
  v_total_connections INT;
  v_evidence_based INT;
  v_unnamed_connections INT;
  v_weak_connections INT;
  v_connection_score NUMERIC;
  v_irgi_pass INT;
  v_irgi_total INT;
  v_irgi_avg_ms NUMERIC;
  v_agent_score NUMERIC;
  v_score_stddev NUMERIC;
  v_max_bucket_pct NUMERIC;
  v_scoring_score NUMERIC;
  v_cir_queue_pending INT;
  v_cir_dead_letters INT;
  v_propagation_errors INT;
  v_propagation_score NUMERIC;
  v_embed_queue INT;
  v_backends INT;
  v_max_conn INT;
  v_pool_ratio NUMERIC;
  v_technical_score NUMERIC;
  v_overdue_obligations INT;
  v_product_score NUMERIC;
  v_product_grade TEXT;
  v_overall_score NUMERIC;
  v_overall_grade TEXT;
BEGIN
  SELECT COUNT(*),
    COUNT(CASE WHEN LENGTH(page_content) > 500 THEN 1 END),
    COUNT(CASE WHEN page_content IS NULL OR LENGTH(page_content) < 50 THEN 1 END),
    COALESCE(ROUND(AVG(LENGTH(page_content))), 0)
  INTO v_companies_total, v_companies_rich, v_companies_stub, v_companies_avg_len
  FROM companies;

  SELECT COUNT(*),
    COUNT(CASE WHEN LENGTH(page_content) > 500 THEN 1 END),
    COUNT(CASE WHEN page_content IS NULL OR LENGTH(page_content) < 50 THEN 1 END),
    COALESCE(ROUND(AVG(LENGTH(page_content))), 0)
  INTO v_network_total, v_network_rich, v_network_stub, v_network_avg_len
  FROM network;

  v_data_richness_score := LEAST(10, 10.0 * (v_companies_rich + v_network_rich) / GREATEST(v_companies_total + v_network_total, 1));
  v_data_richness_score := (v_data_richness_score + LEAST(10, 10.0 * ((v_companies_avg_len + v_network_avg_len) / 2.0) / 1000.0)) / 2.0;

  SELECT COUNT(embedding) INTO v_co_embedded FROM companies;
  SELECT COUNT(embedding) INTO v_net_embedded FROM network;
  SELECT COUNT(*), COUNT(embedding) INTO v_port_total, v_port_embedded FROM portfolio;

  v_embedding_score := 10.0 * (
    0.50 * v_co_embedded::numeric / GREATEST(v_companies_total, 1) +
    0.40 * v_net_embedded::numeric / GREATEST(v_network_total, 1) +
    0.10 * v_port_embedded::numeric / GREATEST(v_port_total, 1)
  );

  SELECT COUNT(*) INTO v_total_connections FROM entity_connections;
  SELECT COUNT(*) INTO v_evidence_based FROM entity_connections
  WHERE connection_type IN ('current_employee', 'past_employee', 'portfolio_investment',
                            'interaction_linked', 'co_attendance', 'discussed_in', 'co_occurrence');
  SELECT COUNT(*) INTO v_unnamed_connections FROM entity_connections
  WHERE source_id IN (SELECT id FROM companies WHERE name LIKE 'Unnamed%' OR name IS NULL OR name = '')
     OR target_id IN (SELECT id FROM companies WHERE name LIKE 'Unnamed%' OR name IS NULL OR name = '');
  SELECT COUNT(*) INTO v_weak_connections FROM entity_connections
  WHERE connection_type = 'sector_peer' AND strength <= 0.35;

  v_connection_score := LEAST(10, 10.0 * v_evidence_based::numeric / GREATEST(v_total_connections, 1) * 2.0);
  v_connection_score := GREATEST(0, v_connection_score - (v_unnamed_connections::numeric / GREATEST(v_total_connections, 1)) * 5);

  BEGIN
    SELECT COUNT(*), COUNT(CASE WHEN status = 'PASS' THEN 1 END), ROUND(AVG(latency_ms)::numeric, 1)
    INTO v_irgi_total, v_irgi_pass, v_irgi_avg_ms
    FROM irgi_benchmark();
    v_agent_score := 10.0 * v_irgi_pass::numeric / GREATEST(v_irgi_total, 1);
    IF v_irgi_avg_ms > 500 THEN v_agent_score := v_agent_score * 0.8; END IF;
  EXCEPTION WHEN OTHERS THEN
    v_irgi_total := 0; v_irgi_pass := 0; v_irgi_avg_ms := 0; v_agent_score := 0;
  END;

  BEGIN
    SELECT COALESCE(ROUND(stddev(user_priority_score)::numeric, 2), 0),
      COALESCE(ROUND(100.0 * MAX(bucket_count) / GREATEST(SUM(bucket_count), 1), 1), 0)
    INTO v_score_stddev, v_max_bucket_pct
    FROM (
      SELECT user_priority_score,
        COUNT(*) OVER (PARTITION BY FLOOR(user_priority_score)) as bucket_count
      FROM actions_queue
      WHERE status NOT IN ('completed', 'dismissed', 'Completed', 'Dismissed')
      AND user_priority_score IS NOT NULL
    ) sub;
    v_scoring_score := LEAST(10,
      CASE WHEN v_score_stddev >= 2.5 THEN 8 WHEN v_score_stddev >= 2.0 THEN 6
           WHEN v_score_stddev >= 1.5 THEN 4 ELSE 2 END +
      CASE WHEN v_max_bucket_pct <= 20 THEN 2 WHEN v_max_bucket_pct <= 30 THEN 1 ELSE 0 END);
  EXCEPTION WHEN OTHERS THEN
    v_score_stddev := 0; v_max_bucket_pct := 100; v_scoring_score := 0;
  END;

  BEGIN
    SELECT COALESCE((SELECT COUNT(*) FROM pgmq.q_cir_queue), 0) INTO v_cir_queue_pending;
    SELECT COALESCE((SELECT COUNT(*) FROM pgmq.q_cir_dead_letter), 0) INTO v_cir_dead_letters;
    SELECT COUNT(*) INTO v_propagation_errors
    FROM cir_propagation_log WHERE event_type LIKE 'error%' AND created_at > NOW() - INTERVAL '24 hours';
    v_propagation_score := 10;
    IF v_cir_queue_pending > 100 THEN v_propagation_score := v_propagation_score - 2; END IF;
    IF v_cir_dead_letters > 0 THEN v_propagation_score := v_propagation_score - 3; END IF;
    IF v_propagation_errors > 10 THEN v_propagation_score := v_propagation_score - 2; END IF;
    v_propagation_score := GREATEST(0, v_propagation_score);
  EXCEPTION WHEN OTHERS THEN
    v_cir_queue_pending := 0; v_cir_dead_letters := 0; v_propagation_errors := 0; v_propagation_score := 5;
  END;

  SELECT COUNT(*) INTO v_backends FROM pg_stat_activity WHERE datname = 'postgres';
  SELECT setting::int INTO v_max_conn FROM pg_settings WHERE name = 'max_connections';
  v_pool_ratio := v_backends::numeric / GREATEST(v_max_conn, 1);
  SELECT COALESCE((SELECT COUNT(*) FROM pgmq.q_embedding_jobs), 0) INTO v_embed_queue;
  v_technical_score := 10;
  IF v_pool_ratio > 0.9 THEN v_technical_score := v_technical_score - 4;
  ELSIF v_pool_ratio > 0.7 THEN v_technical_score := v_technical_score - 2;
  ELSIF v_pool_ratio > 0.5 THEN v_technical_score := v_technical_score - 1; END IF;
  IF v_embed_queue > 1000 THEN v_technical_score := v_technical_score - 2; END IF;
  IF v_embed_queue > 10000 THEN v_technical_score := v_technical_score - 2; END IF;
  v_technical_score := GREATEST(0, v_technical_score);

  BEGIN
    SELECT COUNT(*) INTO v_overdue_obligations FROM obligations WHERE status != 'fulfilled' AND due_date < CURRENT_DATE;
  EXCEPTION WHEN OTHERS THEN v_overdue_obligations := 0; END;

  v_product_score := ROUND(
    v_data_richness_score * 0.25 + v_embedding_score * 0.25 + v_connection_score * 0.15 +
    v_agent_score * 0.15 + v_scoring_score * 0.10 + v_propagation_score * 0.10, 1);
  v_product_grade := CASE
    WHEN v_product_score >= 9.0 THEN 'A+' WHEN v_product_score >= 8.0 THEN 'A'
    WHEN v_product_score >= 7.0 THEN 'B+' WHEN v_product_score >= 6.0 THEN 'B'
    WHEN v_product_score >= 5.0 THEN 'C' WHEN v_product_score >= 4.0 THEN 'D'
    WHEN v_product_score >= 3.0 THEN 'D-' ELSE 'F' END;
  v_overall_score := ROUND(v_product_score * 0.70 + v_technical_score * 0.30, 1);
  v_overall_grade := CASE
    WHEN v_overall_score >= 9.0 THEN 'A+' WHEN v_overall_score >= 8.0 THEN 'A'
    WHEN v_overall_score >= 7.0 THEN 'B+' WHEN v_overall_score >= 6.0 THEN 'B'
    WHEN v_overall_score >= 5.0 THEN 'C' WHEN v_overall_score >= 4.0 THEN 'D'
    WHEN v_overall_score >= 3.0 THEN 'D-' ELSE 'F' END;

  RETURN jsonb_build_object(
    'generated_at', now(), 'overall_grade', v_overall_grade, 'overall_score', v_overall_score,
    'product_grade', v_product_grade, 'product_score', v_product_score,
    'technical_grade', CASE WHEN v_technical_score >= 9 THEN 'A' WHEN v_technical_score >= 7 THEN 'B'
      WHEN v_technical_score >= 5 THEN 'C' ELSE 'D' END,
    'technical_score', v_technical_score,
    'duration_ms', EXTRACT(MILLISECOND FROM clock_timestamp() - v_start)::int,
    'user_reported_quality', '3-4/10 (2026-03-21)',
    'dimensions', jsonb_build_object(
      'data_richness', jsonb_build_object('score', ROUND(v_data_richness_score, 1), 'weight', '25%',
        'companies_rich_500plus', v_companies_rich, 'companies_stub_under50', v_companies_stub,
        'companies_avg_content_chars', v_companies_avg_len, 'network_rich_500plus', v_network_rich,
        'network_stub_under50', v_network_stub, 'network_avg_content_chars', v_network_avg_len,
        'verdict', CASE WHEN v_data_richness_score >= 5 THEN 'ADEQUATE' WHEN v_data_richness_score >= 3 THEN 'THIN' ELSE 'SKELETAL' END),
      'embedding_coverage', jsonb_build_object('score', ROUND(v_embedding_score, 1), 'weight', '25%',
        'companies_pct', ROUND(100.0 * v_co_embedded / GREATEST(v_companies_total, 1), 1),
        'network_pct', ROUND(100.0 * v_net_embedded / GREATEST(v_network_total, 1), 1),
        'portfolio_pct', ROUND(100.0 * v_port_embedded / GREATEST(v_port_total, 1), 1),
        'queue_depth', v_embed_queue,
        'verdict', CASE WHEN v_embedding_score >= 8 THEN 'HEALTHY' WHEN v_embedding_score >= 5 THEN 'RECOVERING'
          WHEN v_embedding_score >= 3 THEN 'DEGRADED' ELSE 'CRIPPLED' END),
      'connection_quality', jsonb_build_object('score', ROUND(v_connection_score, 1), 'weight', '15%',
        'total', v_total_connections, 'evidence_based', v_evidence_based,
        'evidence_pct', ROUND(100.0 * v_evidence_based / GREATEST(v_total_connections, 1), 1),
        'unnamed_noise', v_unnamed_connections, 'weak_sector_peers', v_weak_connections,
        'verdict', CASE WHEN v_connection_score >= 6 THEN 'SIGNAL-RICH' WHEN v_connection_score >= 4 THEN 'NOISY' ELSE 'NOISE-DOMINATED' END),
      'agent_readiness', jsonb_build_object('score', ROUND(v_agent_score, 1), 'weight', '15%',
        'irgi_passing', v_irgi_pass, 'irgi_total', v_irgi_total, 'avg_latency_ms', v_irgi_avg_ms,
        'verdict', CASE WHEN v_agent_score >= 8 THEN 'READY' WHEN v_agent_score >= 5 THEN 'PARTIAL' ELSE 'BROKEN' END),
      'score_accuracy', jsonb_build_object('score', ROUND(v_scoring_score, 1), 'weight', '10%',
        'stddev', v_score_stddev, 'max_bucket_pct', v_max_bucket_pct,
        'verdict', CASE WHEN v_scoring_score >= 7 THEN 'WELL-SPREAD' WHEN v_scoring_score >= 4 THEN 'COMPRESSED' ELSE 'BROKEN' END),
      'propagation', jsonb_build_object('score', ROUND(v_propagation_score, 1), 'weight', '10%',
        'cir_queue', v_cir_queue_pending, 'dead_letters', v_cir_dead_letters, 'errors_24h', v_propagation_errors,
        'verdict', CASE WHEN v_propagation_score >= 8 THEN 'FLOWING' WHEN v_propagation_score >= 5 THEN 'PARTIAL' ELSE 'BLOCKED' END)
    ),
    'technical', jsonb_build_object('score', v_technical_score, 'backends', v_backends,
      'max_connections', v_max_conn, 'pool_utilization_pct', ROUND(v_pool_ratio * 100, 1),
      'embedding_queue', v_embed_queue, 'overdue_obligations', v_overdue_obligations,
      'verdict', CASE WHEN v_technical_score >= 8 THEN 'HEALTHY' WHEN v_technical_score >= 5 THEN 'STRESSED' ELSE 'CRITICAL' END)
  );
END;
$function$;

-- ============================================================================
-- 2. connection_pool_status()
-- ============================================================================
CREATE OR REPLACE FUNCTION connection_pool_status()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_max_conn INT;
  v_total_backends INT;
  v_idle_count INT;
  v_active_count INT;
  v_idle_in_tx INT;
  v_idle_over_5min INT;
  v_idle_over_30min INT;
  v_by_app JSONB;
  v_long_idle JSONB;
  v_recommendations JSONB := '[]'::jsonb;
  v_pool_ratio NUMERIC;
BEGIN
  SELECT setting::int INTO v_max_conn FROM pg_settings WHERE name = 'max_connections';
  SELECT COUNT(*), COUNT(*) FILTER (WHERE state = 'idle'), COUNT(*) FILTER (WHERE state = 'active'),
    COUNT(*) FILTER (WHERE state = 'idle in transaction'),
    COUNT(*) FILTER (WHERE state = 'idle' AND state_change < NOW() - INTERVAL '5 minutes'),
    COUNT(*) FILTER (WHERE state = 'idle' AND state_change < NOW() - INTERVAL '30 minutes')
  INTO v_total_backends, v_idle_count, v_active_count, v_idle_in_tx, v_idle_over_5min, v_idle_over_30min
  FROM pg_stat_activity WHERE datname = 'postgres';
  v_pool_ratio := v_total_backends::numeric / GREATEST(v_max_conn, 1);

  SELECT COALESCE(jsonb_agg(row_to_json(sub)::jsonb), '[]'::jsonb) INTO v_by_app
  FROM (SELECT COALESCE(NULLIF(application_name, ''), 'unnamed') as app, usename as user_name, state,
    COUNT(*) as connections, COUNT(*) FILTER (WHERE state_change < NOW() - INTERVAL '5 minutes') as idle_over_5min
    FROM pg_stat_activity WHERE datname = 'postgres' GROUP BY application_name, usename, state ORDER BY COUNT(*) DESC) sub;

  SELECT COALESCE(jsonb_agg(row_to_json(sub)::jsonb), '[]'::jsonb) INTO v_long_idle
  FROM (SELECT pid, COALESCE(NULLIF(application_name, ''), 'unnamed') as app, usename, state,
    ROUND(EXTRACT(EPOCH FROM (NOW() - state_change)))::int as idle_seconds, backend_start::text as connected_since
    FROM pg_stat_activity WHERE datname = 'postgres' AND state = 'idle' AND state_change < NOW() - INTERVAL '5 minutes'
    ORDER BY state_change ASC LIMIT 20) sub;

  IF v_pool_ratio > 0.9 THEN v_recommendations := v_recommendations || '"CRITICAL: Pool at >90%. Terminate idle connections."'::jsonb; END IF;
  IF v_idle_over_30min > 3 THEN v_recommendations := v_recommendations || ('"' || v_idle_over_30min || ' connections idle >30 min."')::jsonb; END IF;
  IF v_idle_in_tx > 0 THEN v_recommendations := v_recommendations || ('"' || v_idle_in_tx || ' idle-in-transaction connections."')::jsonb; END IF;

  RETURN jsonb_build_object('generated_at', NOW(),
    'summary', jsonb_build_object('max_connections', v_max_conn, 'total_backends', v_total_backends,
      'utilization_pct', ROUND(v_pool_ratio * 100, 1), 'idle', v_idle_count, 'active', v_active_count,
      'idle_in_transaction', v_idle_in_tx, 'idle_over_5min', v_idle_over_5min, 'idle_over_30min', v_idle_over_30min,
      'headroom', v_max_conn - v_total_backends,
      'status', CASE WHEN v_pool_ratio > 0.9 THEN 'CRITICAL' WHEN v_pool_ratio > 0.7 THEN 'WARNING'
        WHEN v_pool_ratio > 0.5 THEN 'ELEVATED' ELSE 'HEALTHY' END),
    'by_application', v_by_app, 'long_idle_connections', v_long_idle, 'recommendations', v_recommendations);
END;
$function$;

-- ============================================================================
-- 3. terminate_idle_connections()
-- ============================================================================
CREATE OR REPLACE FUNCTION terminate_idle_connections(idle_minutes INT DEFAULT 5)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_terminated INT := 0;
  v_skipped INT := 0;
  rec RECORD;
BEGIN
  FOR rec IN
    SELECT pid, application_name, usename,
      ROUND(EXTRACT(EPOCH FROM (NOW() - state_change)))::int as idle_seconds
    FROM pg_stat_activity WHERE datname = 'postgres' AND state = 'idle'
    AND state_change < NOW() - (idle_minutes || ' minutes')::interval
    AND pid != pg_backend_pid() AND usename NOT IN ('supabase_admin')
    AND application_name NOT IN ('pg_cron scheduler', 'pg_net 0.20.0', 'postgres_exporter')
    ORDER BY state_change ASC
  LOOP
    BEGIN
      PERFORM pg_terminate_backend(rec.pid);
      v_terminated := v_terminated + 1;
    EXCEPTION WHEN OTHERS THEN
      v_skipped := v_skipped + 1;
    END;
  END LOOP;
  RETURN jsonb_build_object('action', 'terminate_idle_connections', 'threshold_minutes', idle_minutes,
    'terminated', v_terminated, 'skipped', v_skipped, 'timestamp', NOW());
END;
$function$;

-- ============================================================================
-- 4. embedding_recovery_dashboard()
-- ============================================================================
CREATE OR REPLACE FUNCTION embedding_recovery_dashboard()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_co_total INT; v_co_embedded INT; v_co_missing INT;
  v_net_total INT; v_net_embedded INT; v_net_missing INT;
  v_port_total INT; v_port_embedded INT;
  v_queue_pending BIGINT; v_queue_oldest TIMESTAMPTZ; v_queue_newest TIMESTAMPTZ;
  v_queue_visible BIGINT; v_queue_locked BIGINT; v_queue_by_table JSONB;
  v_archived BIGINT; v_cron_active BOOLEAN; v_cron_last_run TIMESTAMPTZ; v_cron_last_status TEXT;
  v_recovery_pct NUMERIC; v_target_total INT; v_current_embedded INT;
  v_processing_rate NUMERIC; v_hours_to_drain NUMERIC; v_recommendations JSONB;
BEGIN
  SELECT COUNT(*), COUNT(embedding), COUNT(*) - COUNT(embedding) INTO v_co_total, v_co_embedded, v_co_missing FROM companies;
  SELECT COUNT(*), COUNT(embedding), COUNT(*) - COUNT(embedding) INTO v_net_total, v_net_embedded, v_net_missing FROM network;
  SELECT COUNT(*), COUNT(embedding) INTO v_port_total, v_port_embedded FROM portfolio;

  BEGIN
    SELECT COUNT(*), MIN(enqueued_at), MAX(enqueued_at), COUNT(*) FILTER (WHERE vt <= NOW()), COUNT(*) FILTER (WHERE vt > NOW())
    INTO v_queue_pending, v_queue_oldest, v_queue_newest, v_queue_visible, v_queue_locked FROM pgmq.q_embedding_jobs;
    SELECT COALESCE(jsonb_object_agg(tbl, cnt), '{}'::jsonb) INTO v_queue_by_table
    FROM (SELECT message->>'table' as tbl, COUNT(*) as cnt FROM pgmq.q_embedding_jobs GROUP BY message->>'table') sub;
  EXCEPTION WHEN OTHERS THEN
    v_queue_pending := 0; v_queue_visible := 0; v_queue_locked := 0; v_queue_by_table := '{}'::jsonb;
  END;

  BEGIN SELECT COUNT(*) INTO v_archived FROM pgmq.a_embedding_jobs; EXCEPTION WHEN OTHERS THEN v_archived := 0; END;

  BEGIN
    SELECT j.active, (SELECT MAX(start_time) FROM cron.job_run_details WHERE jobid = j.jobid),
      (SELECT status FROM cron.job_run_details WHERE jobid = j.jobid ORDER BY start_time DESC LIMIT 1)
    INTO v_cron_active, v_cron_last_run, v_cron_last_status FROM cron.job j WHERE j.jobid = 1;
  EXCEPTION WHEN OTHERS THEN v_cron_active := false; v_cron_last_status := 'unknown'; END;

  BEGIN
    SELECT COUNT(*)::numeric INTO v_processing_rate FROM pgmq.a_embedding_jobs WHERE archived_at > NOW() - INTERVAL '1 hour';
  EXCEPTION WHEN OTHERS THEN v_processing_rate := 0; END;

  v_hours_to_drain := CASE WHEN v_processing_rate > 0 THEN ROUND(v_queue_pending::numeric / v_processing_rate, 1) ELSE -1 END;
  v_target_total := v_co_total + v_net_total + v_port_total;
  v_current_embedded := v_co_embedded + v_net_embedded + v_port_embedded;
  v_recovery_pct := ROUND(100.0 * v_current_embedded / GREATEST(v_target_total, 1), 1);

  IF v_queue_pending > 10000 AND v_processing_rate = 0 THEN
    v_recommendations := jsonb_build_array('Queue stalled with >10K jobs. Edge Function not working.');
  ELSIF v_queue_pending > 1000 AND v_processing_rate < 10 THEN
    v_recommendations := jsonb_build_array('Queue draining too slowly.');
  ELSIF v_queue_pending = 0 AND v_recovery_pct < 90 THEN
    v_recommendations := jsonb_build_array('Queue drained but coverage still low.');
  ELSE
    v_recommendations := jsonb_build_array('Embedding system nominal.');
  END IF;

  RETURN jsonb_build_object('generated_at', NOW(),
    'recovery_progress', jsonb_build_object('overall_pct', v_recovery_pct, 'target', v_target_total,
      'current_embedded', v_current_embedded, 'remaining', v_target_total - v_current_embedded,
      'status', CASE WHEN v_recovery_pct >= 95 THEN 'RECOVERED' WHEN v_recovery_pct >= 75 THEN 'RECOVERING_WELL'
        WHEN v_recovery_pct >= 50 THEN 'RECOVERING' WHEN v_recovery_pct >= 25 THEN 'EARLY_RECOVERY' ELSE 'CRITICAL' END),
    'coverage', jsonb_build_object(
      'companies', jsonb_build_object('total', v_co_total, 'embedded', v_co_embedded, 'missing', v_co_missing,
        'pct', ROUND(100.0 * v_co_embedded / GREATEST(v_co_total, 1), 1)),
      'network', jsonb_build_object('total', v_net_total, 'embedded', v_net_embedded, 'missing', v_net_missing,
        'pct', ROUND(100.0 * v_net_embedded / GREATEST(v_net_total, 1), 1)),
      'portfolio', jsonb_build_object('total', v_port_total, 'embedded', v_port_embedded,
        'pct', ROUND(100.0 * v_port_embedded / GREATEST(v_port_total, 1), 1))),
    'queue', jsonb_build_object('pending', v_queue_pending, 'visible_now', v_queue_visible, 'locked', v_queue_locked,
      'by_table', v_queue_by_table, 'oldest_job', v_queue_oldest, 'newest_job', v_queue_newest, 'archived_total', v_archived),
    'processing', jsonb_build_object('rate_per_hour', v_processing_rate, 'hours_to_drain', v_hours_to_drain,
      'cron_active', v_cron_active, 'cron_last_run', v_cron_last_run, 'cron_last_status', v_cron_last_status,
      'drain_verdict', CASE WHEN v_queue_pending = 0 THEN 'DRAINED' WHEN v_processing_rate > 100 THEN 'DRAINING_FAST'
        WHEN v_processing_rate > 0 THEN 'DRAINING_SLOW' ELSE 'STALLED' END),
    'recommendations', v_recommendations);
END;
$function$;

-- ============================================================================
-- 5. Feedback Store tables
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_feedback_store (
  id SERIAL PRIMARY KEY,
  action_id INTEGER REFERENCES actions_queue(id) ON DELETE SET NULL,
  agent_name TEXT NOT NULL,
  feedback_type TEXT NOT NULL CHECK (feedback_type IN (
    'scoring_reasoning', 'routing_decision', 'enrichment_result', 'quality_assessment',
    'propagation_decision', 'strategic_assessment', 'error_recovery', 'other')),
  feedback_text TEXT NOT NULL,
  context JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_action ON agent_feedback_store(action_id);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_agent ON agent_feedback_store(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_created ON agent_feedback_store(created_at DESC);

CREATE TABLE IF NOT EXISTS user_feedback_store (
  id SERIAL PRIMARY KEY,
  page TEXT NOT NULL,
  item_id TEXT,
  item_type TEXT,
  feedback_type TEXT NOT NULL CHECK (feedback_type IN (
    'accept', 'dismiss', 'rate_quality', 'flag_wrong', 'flag_missing', 'comment', 'preference')),
  feedback_text TEXT,
  rating INTEGER CHECK (rating >= 1 AND rating <= 10),
  context JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_feedback_page ON user_feedback_store(page);
CREATE INDEX IF NOT EXISTS idx_user_feedback_item ON user_feedback_store(item_type, item_id);
CREATE INDEX IF NOT EXISTS idx_user_feedback_type ON user_feedback_store(feedback_type);
CREATE INDEX IF NOT EXISTS idx_user_feedback_created ON user_feedback_store(created_at DESC);

ALTER TABLE agent_feedback_store ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_feedback_store ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 6. feedback_summary view
-- ============================================================================
CREATE OR REPLACE VIEW feedback_summary AS
WITH agent_stats AS (
  SELECT agent_name, feedback_type, COUNT(*) as count, MAX(created_at) as latest
  FROM agent_feedback_store GROUP BY agent_name, feedback_type
),
user_stats AS (
  SELECT page, feedback_type, COUNT(*) as count, AVG(rating) as avg_rating, MAX(created_at) as latest
  FROM user_feedback_store GROUP BY page, feedback_type
),
user_accept_dismiss AS (
  SELECT item_type,
    COUNT(*) FILTER (WHERE feedback_type = 'accept') as accepts,
    COUNT(*) FILTER (WHERE feedback_type = 'dismiss') as dismisses,
    COUNT(*) FILTER (WHERE feedback_type = 'flag_wrong') as flags_wrong,
    COUNT(*) FILTER (WHERE feedback_type = 'flag_missing') as flags_missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE feedback_type = 'accept') /
      GREATEST(COUNT(*) FILTER (WHERE feedback_type IN ('accept', 'dismiss')), 1), 1) as acceptance_rate
  FROM user_feedback_store WHERE feedback_type IN ('accept', 'dismiss', 'flag_wrong', 'flag_missing')
  GROUP BY item_type
)
SELECT 'agent_feedback' as source,
  COALESCE((SELECT jsonb_agg(row_to_json(a)::jsonb) FROM agent_stats a), '[]'::jsonb) as agent_breakdown,
  COALESCE((SELECT jsonb_agg(row_to_json(u)::jsonb) FROM user_stats u), '[]'::jsonb) as user_breakdown,
  COALESCE((SELECT jsonb_agg(row_to_json(ad)::jsonb) FROM user_accept_dismiss ad), '[]'::jsonb) as acceptance_rates,
  (SELECT COUNT(*) FROM agent_feedback_store) as total_agent_feedback,
  (SELECT COUNT(*) FROM user_feedback_store) as total_user_feedback,
  NOW() as generated_at;
