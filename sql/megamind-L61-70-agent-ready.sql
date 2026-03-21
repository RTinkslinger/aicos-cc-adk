-- Megamind L61-70: Agent-Ready Strategic Data
-- Date: 2026-03-21
-- Purpose: Transform Megamind SQL functions into TOOLS for an agent, not the intelligence itself.
--
-- NEW FUNCTIONS:
--   megamind_agent_context()             — Single-call comprehensive context (9 sections)
--   actions_needing_decision_v2(limit)   — Full company/person/thesis/obligation/interaction context per action
--   cascade_impact_analysis(event_id)    — Full ripple effect analysis for any cascade event
--   generate_strategic_narrative(focus)  — Structured data for 4 narrative types
--
-- UPDATED FUNCTIONS:
--   megamind_system_report() v4.0 → v5.0 — Now wraps megamind_agent_context() + tool catalog
--
-- DESIGN PRINCIPLE: SQL produces DATA, the agent produces INTELLIGENCE.
-- Every function returns rich, structured JSONB that an agent can reason about
-- without needing to make additional queries.

-- =============================================================================
-- Function 1: megamind_agent_context()
-- Single call returning ALL data Megamind agent needs for strategic reasoning.
-- Replaces pattern of agent calling 5+ separate functions.
--
-- Returns 9 sections:
--   portfolio_risk    — Risk by tier (CRITICAL/HIGH) + portfolio summary
--   convergence       — Action queue state, by-type breakdown, score stats, trend
--   obligations       — Health, I-owe/they-owe urgent items with details
--   recent_cascades   — Last 7 days of cascade events
--   thesis_momentum   — Per-thesis conviction, momentum, portfolio exposure
--   strategic_network — Top 15 people by strategic importance
--   pending_decisions — Top 10 actions needing decision
--   recent_interactions — Last 30 days of interactions
--   system_capabilities — What the system can do
-- =============================================================================

CREATE OR REPLACE FUNCTION megamind_agent_context()
RETURNS JSONB
LANGUAGE plpgsql AS $$
DECLARE
  v_result JSONB;
  v_portfolio_risk JSONB;
  v_convergence JSONB;
  v_obligations JSONB;
  v_cascades JSONB;
  v_thesis JSONB;
  v_network JSONB;
  v_decisions JSONB;
  v_interactions JSONB;
  v_capabilities JSONB;
  v_conv_ratio numeric;
  v_conv_status text;
  v_by_type JSONB;
BEGIN
  -- === 1. PORTFOLIO RISK BY TIER ===
  SELECT jsonb_build_object(
    'critical', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'id', company_id, 'name', company_name, 'health', health,
        'ops_priority', ops_priority, 'risk_score', risk_score,
        'open_actions', open_action_count, 'overdue_obligations', overdue_obligation_count,
        'days_silent', days_since_last_interaction,
        'fumes_date', risk_factors->>'fumes_date',
        'days_until_fumes', risk_factors->>'days_until_fumes',
        'cash_in_bank', risk_factors->>'cash_in_bank',
        'ownership_pct', risk_factors->>'ownership_pct',
        'current_value', risk_factors->>'current_value',
        'best_case_value', risk_factors->>'best_case_value',
        'follow_on', risk_factors->>'follow_on_decision',
        'key_questions', risk_factors->>'key_questions',
        'high_impact', risk_factors->>'high_impact',
        'external_signal', risk_factors->>'external_signal',
        'narrative', risk_factors->>'risk_narrative'
      ) ORDER BY risk_score DESC)
      FROM portfolio_risk_assessment() WHERE risk_tier = 'CRITICAL'
    ), '[]'::jsonb),
    'high', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'id', company_id, 'name', company_name, 'health', health,
        'risk_score', risk_score, 'open_actions', open_action_count,
        'ownership_pct', risk_factors->>'ownership_pct',
        'current_value', risk_factors->>'current_value',
        'follow_on', risk_factors->>'follow_on_decision',
        'key_questions', risk_factors->>'key_questions',
        'narrative', risk_factors->>'risk_narrative'
      ) ORDER BY risk_score DESC)
      FROM portfolio_risk_assessment() WHERE risk_tier = 'HIGH'
    ), '[]'::jsonb),
    'summary', jsonb_build_object(
      'total_companies', (SELECT count(*) FROM portfolio WHERE portfolio_co IS NOT NULL),
      'red', (SELECT count(*) FROM portfolio WHERE health = 'Red'),
      'yellow', (SELECT count(*) FROM portfolio WHERE health = 'Yellow'),
      'green', (SELECT count(*) FROM portfolio WHERE health = 'Green'),
      'total_fmv', (SELECT round(sum(fmv_carried)::numeric, 0) FROM portfolio WHERE fmv_carried IS NOT NULL),
      'total_best_case', (SELECT round(sum(ownership_pct * best_case_outcome)::numeric, 0) FROM portfolio WHERE ownership_pct IS NOT NULL AND best_case_outcome IS NOT NULL),
      'fmv_at_risk', (SELECT round(sum(fmv_carried)::numeric, 0) FROM portfolio WHERE health IN ('Red','Yellow') AND fmv_carried IS NOT NULL),
      'companies_with_fumes_90d', (SELECT count(*) FROM portfolio WHERE fumes_date IS NOT NULL AND fumes_date <= CURRENT_DATE + INTERVAL '90 days'),
      'companies_with_key_questions', (SELECT count(*) FROM portfolio WHERE key_questions IS NOT NULL AND LENGTH(key_questions) > 5),
      'companies_with_follow_on', (SELECT count(*) FROM portfolio WHERE follow_on_decision IS NOT NULL)
    )
  ) INTO v_portfolio_risk;

  -- === 2. CONVERGENCE STATE ===
  SELECT round(count(*) FILTER (WHERE status NOT IN ('Proposed'))::numeric / GREATEST(count(*), 1)::numeric, 3) INTO v_conv_ratio FROM actions_queue;
  v_conv_status := CASE
    WHEN v_conv_ratio >= 0.8 THEN 'fully_converged'
    WHEN v_conv_ratio >= 0.6 THEN 'converged'
    WHEN v_conv_ratio >= 0.5 THEN 'converging_fast'
    WHEN v_conv_ratio >= 0.3 THEN 'converging'
    ELSE 'diverging'
  END;

  SELECT COALESCE(jsonb_object_agg(sub.action_type, jsonb_build_object(
    'proposed', sub.proposed_cnt,
    'resolved', sub.resolved_cnt,
    'total', sub.total_cnt
  )), '{}'::jsonb) INTO v_by_type
  FROM (
    SELECT action_type,
      count(*) FILTER (WHERE status = 'Proposed') as proposed_cnt,
      count(*) FILTER (WHERE status IN ('Accepted','Dismissed','Done')) as resolved_cnt,
      count(*) as total_cnt
    FROM actions_queue WHERE action_type IS NOT NULL GROUP BY action_type
  ) sub;

  SELECT jsonb_build_object(
    'ratio', v_conv_ratio,
    'status', v_conv_status,
    'total_actions', count(*),
    'proposed', count(*) FILTER (WHERE status = 'Proposed'),
    'accepted', count(*) FILTER (WHERE status = 'Accepted'),
    'dismissed', count(*) FILTER (WHERE status = 'Dismissed'),
    'done', count(*) FILTER (WHERE status = 'Done'),
    'stale_14d', count(*) FILTER (WHERE status IN ('Proposed','Accepted') AND created_at < NOW() - INTERVAL '14 days'),
    'by_type', v_by_type,
    'score_stats', jsonb_build_object(
      'mean', (SELECT round(avg(strategic_score)::numeric, 2) FROM actions_queue WHERE strategic_score IS NOT NULL),
      'stddev', (SELECT round(stddev(strategic_score)::numeric, 2) FROM actions_queue WHERE strategic_score IS NOT NULL),
      'max', (SELECT round(max(strategic_score)::numeric, 2) FROM actions_queue WHERE strategic_score IS NOT NULL),
      'min', (SELECT round(min(strategic_score)::numeric, 2) FROM actions_queue WHERE strategic_score IS NOT NULL)
    ),
    'trend', COALESCE((SELECT CASE
      WHEN sa.convergence_ratio IS NOT NULL AND v_conv_ratio > sa.convergence_ratio + 0.05 THEN 'improving'
      WHEN sa.convergence_ratio IS NOT NULL AND v_conv_ratio < sa.convergence_ratio - 0.05 THEN 'degrading'
      ELSE 'stable'
    END FROM strategic_assessments sa ORDER BY sa.created_at DESC LIMIT 1), 'no_baseline')
  ) INTO v_convergence FROM actions_queue;

  -- === 3. OBLIGATION HEALTH ===
  SELECT jsonb_build_object(
    'total', count(*),
    'overdue', count(*) FILTER (WHERE status = 'overdue'),
    'escalated', count(*) FILTER (WHERE status = 'escalated'),
    'pending', count(*) FILTER (WHERE status = 'pending'),
    'i_owe_urgent', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'id', o.id, 'person', o.person_name, 'role', o.person_role,
        'description', o.description, 'category', o.category,
        'status', o.status, 'due_date', o.due_date,
        'blended_priority', round(o.blended_priority::numeric, 2),
        'linked_action_id', o.linked_action_id,
        'source_quote', LEFT(o.source_quote, 150),
        'days_overdue', EXTRACT(day FROM NOW() - o.due_date)::int
      ) ORDER BY o.blended_priority DESC)
      FROM obligations o
      WHERE o.obligation_type = 'I_OWE_THEM' AND o.status IN ('overdue','escalated')
    ), '[]'::jsonb),
    'they_owe_urgent', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'id', o.id, 'person', o.person_name, 'description', o.description,
        'status', o.status, 'blended_priority', round(o.blended_priority::numeric, 2)
      ) ORDER BY o.blended_priority DESC)
      FROM obligations o
      WHERE o.obligation_type = 'THEY_OWE_ME' AND o.status IN ('overdue','escalated')
    ), '[]'::jsonb),
    'linked_to_actions_pct', round(count(*) FILTER (WHERE linked_action_id IS NOT NULL)::numeric / GREATEST(count(*), 1)::numeric * 100, 1)
  ) INTO v_obligations FROM obligations;

  -- === 4. RECENT CASCADES ===
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'id', ce.id, 'trigger_type', ce.trigger_type,
    'trigger_description', ce.trigger_description,
    'affected_thesis', ce.affected_thesis_threads,
    'affected_companies', ce.affected_companies,
    'actions_rescored', ce.actions_rescored,
    'actions_resolved', ce.actions_resolved,
    'actions_generated', ce.actions_generated,
    'net_delta', ce.net_action_delta,
    'convergence_pass', ce.convergence_pass,
    'created_at', ce.created_at,
    'summary', ce.cascade_report->>'summary'
  ) ORDER BY ce.created_at DESC), '[]'::jsonb) INTO v_cascades
  FROM cascade_events ce WHERE ce.created_at > NOW() - INTERVAL '7 days';

  -- === 5. THESIS MOMENTUM ===
  SELECT COALESCE(jsonb_object_agg(tt.thread_name, jsonb_build_object(
    'id', tt.id, 'conviction', tt.conviction, 'status', tt.status,
    'core_thesis', LEFT(tt.core_thesis, 200),
    'evidence_for_length', LENGTH(COALESCE(tt.evidence_for, '')),
    'evidence_against_length', LENGTH(COALESCE(tt.evidence_against, '')),
    'key_questions', tt.key_question_summary,
    'key_companies', tt.key_companies,
    'investment_implications', LEFT(tt.investment_implications, 200),
    'bias_severity', tt.bias_flags->>'severity',
    'bias_type', tt.bias_flags->>'type',
    'updated_at', tt.updated_at,
    'momentum_tier', CASE
      WHEN tt.updated_at >= NOW() - INTERVAL '7 days' AND LENGTH(COALESCE(tt.evidence_for,'')) > 500 THEN 'HIGH'
      WHEN tt.updated_at >= NOW() - INTERVAL '30 days' THEN 'MEDIUM'
      ELSE 'LOW'
    END,
    'open_actions', (SELECT count(*) FROM actions_queue WHERE thesis_connection LIKE '%' || tt.thread_name || '%' AND status IN ('Proposed','Accepted')),
    'portfolio_companies', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'name', p.portfolio_co, 'health', p.health,
        'ownership_pct', round(p.ownership_pct::numeric * 100, 2),
        'scale', p.scale_of_business, 'spikey', p.spikey
      ))
      FROM portfolio p WHERE p.thesis_connection LIKE '%' || tt.thread_name || '%'
    ), '[]'::jsonb)
  )), '{}'::jsonb) INTO v_thesis FROM thesis_threads tt;

  -- === 6. STRATEGIC NETWORK ===
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'person_id', person_id, 'name', person_name, 'role', role_title,
    'importance', strategic_importance,
    'portfolio_connections', portfolio_connections,
    'obligations', obligation_count, 'overdue', obligation_overdue_count,
    'interaction_recency_days', interaction_recency_days,
    'interaction_count_30d', interaction_count_30d,
    'narrative', importance_factors->>'narrative',
    'portfolio_companies', importance_factors->'portfolio_companies',
    'obligation_details', importance_factors->'obligation_details'
  )), '[]'::jsonb) INTO v_network FROM strategic_network_map(15);

  -- === 7. ACTIONS NEEDING DECISIONS ===
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'action_id', action_id, 'action', action_text,
    'type', action_type, 'priority', priority,
    'strategic_score', strategic_score, 'confidence', score_confidence,
    'days_open', days_open,
    'has_obligation', has_obligation, 'obligation_overdue', obligation_overdue,
    'depth_grade', depth_grade,
    'impact_score', decision_impact_score,
    'reasoning', reasoning
  )), '[]'::jsonb) INTO v_decisions FROM actions_needing_decision(10);

  -- === 8. RECENT INTERACTIONS ===
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'id', i.id, 'source', i.source,
    'participants', i.participants,
    'summary', LEFT(i.summary, 200),
    'action_items', i.action_items,
    'thesis_signals', i.thesis_signals,
    'deal_signals', i.deal_signals,
    'timestamp', i.timestamp
  ) ORDER BY i.timestamp DESC), '[]'::jsonb) INTO v_interactions
  FROM interactions i WHERE i.timestamp > NOW() - INTERVAL '30 days';

  -- === 9. SYSTEM CAPABILITIES ===
  v_capabilities := jsonb_build_object(
    'depth_grading_coverage', (SELECT round(count(dg.id)::numeric / GREATEST((SELECT count(*) FROM actions_queue), 1)::numeric * 100, 1) FROM depth_grades dg),
    'cascade_dedup_guard', true,
    'convergence_simulation', true,
    'obligation_cascade', true,
    'portfolio_value_mapping', true,
    'follow_on_tracking', true,
    'key_question_surfacing', true,
    'strategic_network_mapping', true,
    'interaction_intelligence', true
  );

  -- === ASSEMBLE ===
  v_result := jsonb_build_object(
    'generated_at', NOW(),
    'version', 'v1.0-L62',
    'portfolio_risk', v_portfolio_risk,
    'convergence', v_convergence,
    'obligations', v_obligations,
    'recent_cascades', v_cascades,
    'thesis_momentum', v_thesis,
    'strategic_network', v_network,
    'pending_decisions', v_decisions,
    'recent_interactions', v_interactions,
    'system_capabilities', v_capabilities
  );

  RETURN v_result;
END;
$$;


-- =============================================================================
-- Function 2: actions_needing_decision_v2(p_limit)
-- Enhanced version with full context per action.
-- An agent reading this should be able to write a chief-of-staff recommendation
-- without querying anything else.
--
-- Returns per action:
--   company_context      — Full portfolio company data (health, financials, questions)
--   person_context       — People connected to the company (obligations, interactions)
--   thesis_context       — Related thesis threads (conviction, momentum, bias)
--   obligation_context   — Obligations linked to this action
--   interaction_signals  — Recent interactions relevant to this action
--   recommendation       — Structured reasoning for the agent
-- =============================================================================

CREATE OR REPLACE FUNCTION actions_needing_decision_v2(p_limit integer DEFAULT 10)
RETURNS TABLE(
  action_id integer,
  action_text text,
  action_type text,
  priority text,
  strategic_score numeric,
  score_confidence numeric,
  days_open integer,
  decision_impact_score numeric,
  company_context jsonb,
  person_context jsonb,
  thesis_context jsonb,
  obligation_context jsonb,
  interaction_signals jsonb,
  recommendation text
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  WITH decision_candidates AS (
    SELECT
      aq.id,
      aq.action,
      aq.action_type as atype,
      aq.priority as apriority,
      COALESCE(aq.strategic_score, 0)::numeric as strat_score,
      COALESCE(aq.score_confidence, 0)::numeric as conf,
      EXTRACT(day FROM NOW() - aq.created_at)::integer as age_days,
      aq.thesis_connection,
      aq.company_notion_id,
      aq.reasoning as action_reasoning,
      aq.source as action_source,
      COALESCE(dg.auto_depth, 1) as depth,
      dg.reasoning as depth_reasoning,
      (
        COALESCE(aq.strategic_score, 0) * 0.25
        + LEAST(10, EXTRACT(day FROM NOW() - aq.created_at)::numeric / 3) * 0.20
        + COALESCE(aq.score_confidence, 5) * 0.15
        + CASE WHEN EXISTS(SELECT 1 FROM obligations o WHERE o.linked_action_id = aq.id AND o.status IN ('overdue','escalated')) THEN 3.0 ELSE 0 END * 0.15
        + CASE WHEN COALESCE(dg.auto_depth, 1) >= 3 THEN 2.0 ELSE 0 END * 0.05
        + CASE WHEN aq.company_notion_id IS NOT NULL AND EXISTS(
            SELECT 1 FROM portfolio p WHERE p.notion_page_id = aq.company_notion_id
            AND p.ownership_pct > 0.01 AND p.health IN ('Red', 'Yellow')
          ) THEN 2.0 ELSE 0 END * 0.10
        + CASE WHEN aq.company_notion_id IS NOT NULL AND EXISTS(
            SELECT 1 FROM portfolio p WHERE p.notion_page_id = aq.company_notion_id AND p.follow_on_decision IS NOT NULL
          ) THEN 1.5 ELSE 0 END * 0.05
        + CASE WHEN aq.company_notion_id IS NOT NULL AND EXISTS(
            SELECT 1 FROM portfolio p WHERE p.notion_page_id = aq.company_notion_id
            AND p.key_questions IS NOT NULL AND LENGTH(p.key_questions) > 5
          ) THEN 1.5 ELSE 0 END * 0.05
      )::numeric as impact
    FROM actions_queue aq
    LEFT JOIN depth_grades dg ON aq.id = dg.action_id
    WHERE aq.status = 'Proposed'
  )
  SELECT
    dc.id, dc.action, dc.atype, dc.apriority,
    round(dc.strat_score, 1), round(dc.conf, 1), dc.age_days, round(dc.impact, 2),
    -- COMPANY CONTEXT
    CASE WHEN dc.company_notion_id IS NOT NULL THEN (
      SELECT jsonb_build_object(
        'company_name', p.portfolio_co, 'health', p.health,
        'ops_priority', p.ops_prio, 'check_in_cadence', p.check_in_cadence,
        'ownership_pct', round(p.ownership_pct::numeric * 100, 2),
        'fmv_carried', p.fmv_carried,
        'best_case_outcome', p.best_case_outcome,
        'current_value', CASE WHEN p.ownership_pct IS NOT NULL AND p.fmv_carried IS NOT NULL
          THEN round((p.ownership_pct * p.fmv_carried)::numeric, 0) END,
        'best_case_value', CASE WHEN p.ownership_pct IS NOT NULL AND p.best_case_outcome IS NOT NULL
          THEN round((p.ownership_pct * p.best_case_outcome)::numeric, 0) END,
        'follow_on_decision', p.follow_on_decision,
        'room_to_deploy', p.room_to_deploy,
        'note_on_deployment', LEFT(p.note_on_deployment, 200),
        'key_questions', p.key_questions,
        'high_impact', p.high_impact,
        'external_signal', p.external_signal,
        'spikey', p.spikey, 'scale_of_business', p.scale_of_business,
        'fumes_date', p.fumes_date,
        'days_until_fumes', CASE WHEN p.fumes_date IS NOT NULL THEN (p.fumes_date - CURRENT_DATE) END,
        'cash_in_bank', p.cash_in_bank,
        'thesis_connection', p.thesis_connection,
        'current_stage', p.current_stage,
        'other_open_actions', (SELECT count(*) FROM actions_queue aq2
          WHERE aq2.company_notion_id = dc.company_notion_id
          AND aq2.status IN ('Proposed','Accepted') AND aq2.id != dc.id)
      )
      FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id LIMIT 1
    ) ELSE NULL END,
    -- PERSON CONTEXT
    COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'person_id', sub.nid, 'name', sub.pname, 'role', sub.prole,
        'interaction_recency_days', sub.int_days,
        'interaction_count_30d', sub.int_30d,
        'obligations', sub.obl_cnt, 'overdue_obligations', sub.obl_overdue
      ))
      FROM (
        SELECT n.id as nid, n.person_name as pname, n.role_title as prole,
          CASE WHEN n.last_interaction_at IS NOT NULL THEN EXTRACT(day FROM NOW() - n.last_interaction_at)::int END as int_days,
          COALESCE(n.interaction_count_30d, 0) as int_30d,
          (SELECT count(*) FROM obligations o WHERE o.person_id = n.id) as obl_cnt,
          (SELECT count(*) FROM obligations o WHERE o.person_id = n.id AND o.status IN ('overdue','escalated')) as obl_overdue
        FROM network n
        WHERE dc.company_notion_id IS NOT NULL AND EXISTS(
          SELECT 1 FROM entity_connections ec
          WHERE ec.source_type = 'network' AND ec.source_id = n.id
          AND ec.target_type = 'company' AND EXISTS(
            SELECT 1 FROM portfolio p WHERE p.id = ec.target_id AND p.notion_page_id = dc.company_notion_id
          )
          AND ec.connection_type IN ('current_employee','affiliated_with','interaction_linked')
        )
        ORDER BY n.interaction_count_30d DESC NULLS LAST LIMIT 5
      ) sub
    ), '[]'::jsonb),
    -- THESIS CONTEXT
    COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'thread_name', tt.thread_name, 'conviction', tt.conviction, 'status', tt.status,
        'core_thesis', LEFT(tt.core_thesis, 150),
        'key_questions', LEFT(tt.key_question_summary, 150),
        'key_companies', tt.key_companies,
        'momentum_tier', CASE
          WHEN tt.updated_at >= NOW() - INTERVAL '7 days' AND LENGTH(COALESCE(tt.evidence_for,'')) > 500 THEN 'HIGH'
          WHEN tt.updated_at >= NOW() - INTERVAL '30 days' THEN 'MEDIUM'
          ELSE 'LOW'
        END,
        'bias_severity', tt.bias_flags->>'severity'
      ))
      FROM thesis_threads tt
      WHERE dc.thesis_connection IS NOT NULL AND dc.thesis_connection LIKE '%' || tt.thread_name || '%'
    ), '[]'::jsonb),
    -- OBLIGATION CONTEXT
    COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'id', o.id, 'type', o.obligation_type,
        'person', o.person_name, 'description', o.description,
        'status', o.status, 'due_date', o.due_date,
        'blended_priority', round(o.blended_priority::numeric, 2),
        'days_overdue', CASE WHEN o.due_date IS NOT NULL AND o.status = 'overdue'
          THEN EXTRACT(day FROM NOW() - o.due_date)::int END,
        'source_quote', LEFT(o.source_quote, 100)
      ) ORDER BY o.blended_priority DESC)
      FROM obligations o
      WHERE o.linked_action_id = dc.id
        OR (o.description ILIKE '%' || LEFT(dc.action, 30) || '%' AND LENGTH(dc.action) > 20)
    ), '[]'::jsonb),
    -- INTERACTION SIGNALS
    COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'id', i.id, 'source', i.source,
        'summary', LEFT(i.summary, 150),
        'timestamp', i.timestamp,
        'thesis_signals', i.thesis_signals,
        'deal_signals', i.deal_signals
      ) ORDER BY i.timestamp DESC)
      FROM interactions i
      WHERE i.timestamp > NOW() - INTERVAL '60 days'
      AND (
        (dc.company_notion_id IS NOT NULL AND EXISTS(
          SELECT 1 FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id
          AND i.summary ILIKE '%' || LEFT(p.portfolio_co, 15) || '%'
        ))
        OR (dc.thesis_connection IS NOT NULL AND i.thesis_signals IS NOT NULL AND i.thesis_signals != 'null'::jsonb)
      )
      LIMIT 3
    ), '[]'::jsonb),
    -- RECOMMENDATION
    CASE
      WHEN dc.age_days > 30 THEN
        'STALE (' || dc.age_days || 'd). Consider: dismiss if superseded, accept if still relevant, or escalate. '
        || COALESCE('Source: ' || dc.action_source || '. ', '')
        || COALESCE('Depth reasoning: ' || LEFT(dc.depth_reasoning, 100), '')
      WHEN EXISTS(SELECT 1 FROM obligations o WHERE o.linked_action_id = dc.id AND o.status IN ('overdue','escalated')) THEN
        'OBLIGATION ATTACHED (overdue). This action has commitments to people -- prioritize or communicate delay.'
      WHEN dc.company_notion_id IS NOT NULL AND EXISTS(
        SELECT 1 FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id AND p.health = 'Red'
      ) THEN
        'RED COMPANY. '
        || COALESCE((SELECT 'Ownership: ' || round(p.ownership_pct::numeric * 100, 1)::text || '%. '
            || COALESCE('Key Q: ' || LEFT(p.key_questions, 80), '')
            FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id LIMIT 1), '')
        || ' High strategic importance -- recommend accept.'
      WHEN dc.strat_score >= 8 THEN
        'HIGH SCORE (' || round(dc.strat_score, 1)::text || '). Strong signal -- accept or investigate deeper.'
      WHEN dc.strat_score <= 3 THEN
        'LOW SCORE (' || round(dc.strat_score, 1)::text || '). Consider dismiss unless thesis-critical.'
      ELSE
        'Standard priority. Score: ' || round(dc.strat_score, 1)::text
        || ', confidence: ' || round(dc.conf, 1)::text
        || '. ' || COALESCE('Source: ' || dc.action_source, '')
    END
  FROM decision_candidates dc
  ORDER BY dc.impact DESC
  LIMIT p_limit;
END;
$$;


-- =============================================================================
-- Function 3: cascade_impact_analysis(p_event_id)
-- Full ripple-effect analysis for any cascade event.
-- Shows trigger, blast radius, impact results, downstream effects, and chain.
-- =============================================================================

CREATE OR REPLACE FUNCTION cascade_impact_analysis(p_event_id integer DEFAULT NULL)
RETURNS JSONB
LANGUAGE plpgsql AS $$
DECLARE
  v_result JSONB;
  v_event cascade_events%ROWTYPE;
  v_event_id integer;
BEGIN
  IF p_event_id IS NULL THEN
    SELECT id INTO v_event_id FROM cascade_events ORDER BY created_at DESC LIMIT 1;
  ELSE
    v_event_id := p_event_id;
  END IF;

  IF v_event_id IS NULL THEN
    RETURN jsonb_build_object('error', 'No cascade events found');
  END IF;

  SELECT * INTO v_event FROM cascade_events WHERE id = v_event_id;

  IF NOT FOUND THEN
    RETURN jsonb_build_object('error', 'Cascade event ' || v_event_id || ' not found');
  END IF;

  SELECT jsonb_build_object(
    'event_id', v_event.id,
    'created_at', v_event.created_at,
    'trigger', jsonb_build_object(
      'type', v_event.trigger_type,
      'source_id', v_event.trigger_source_id,
      'description', v_event.trigger_description,
      'source_details', CASE v_event.trigger_type
        WHEN 'depth_completed' THEN (
          SELECT jsonb_build_object(
            'depth_grade_id', dg.id, 'action_id', dg.action_id,
            'action_text', LEFT(dg.action_text, 120),
            'auto_depth', dg.auto_depth, 'strategic_score', dg.strategic_score,
            'thesis_connections', dg.thesis_connections, 'execution_status', dg.execution_status
          ) FROM depth_grades dg WHERE dg.id = v_event.trigger_source_id
        )
        WHEN 'conviction_change' THEN (
          SELECT jsonb_build_object(
            'thesis_id', tt.id, 'thread_name', tt.thread_name,
            'conviction', tt.conviction, 'status', tt.status, 'key_companies', tt.key_companies
          ) FROM thesis_threads tt WHERE tt.id = v_event.trigger_source_id
        )
        ELSE NULL
      END
    ),
    'blast_radius', jsonb_build_object(
      'affected_thesis_threads', v_event.affected_thesis_threads,
      'affected_companies', v_event.affected_companies,
      'affected_actions_count', v_event.affected_actions_count,
      'thesis_details', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'name', tt.thread_name, 'conviction', tt.conviction, 'status', tt.status,
          'open_actions', (SELECT count(*) FROM actions_queue WHERE thesis_connection LIKE '%' || tt.thread_name || '%' AND status IN ('Proposed','Accepted')),
          'bias_severity', tt.bias_flags->>'severity'
        )) FROM thesis_threads tt WHERE tt.thread_name = ANY(v_event.affected_thesis_threads)
      ), '[]'::jsonb),
      'company_details', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'name', p.portfolio_co, 'health', p.health, 'ops_priority', p.ops_prio,
          'ownership_pct', round(p.ownership_pct::numeric * 100, 2),
          'fmv_carried', p.fmv_carried, 'key_questions', LEFT(p.key_questions, 100),
          'follow_on', p.follow_on_decision,
          'open_actions', (SELECT count(*) FROM actions_queue aq WHERE aq.status IN ('Proposed','Accepted')
            AND (aq.action ILIKE '%' || LEFT(p.portfolio_co, 15) || '%' OR aq.company_notion_id = p.notion_page_id))
        )) FROM portfolio p WHERE p.portfolio_co = ANY(v_event.affected_companies)
      ), '[]'::jsonb)
    ),
    'impact', jsonb_build_object(
      'actions_rescored', v_event.actions_rescored,
      'actions_resolved', v_event.actions_resolved,
      'actions_generated', v_event.actions_generated,
      'net_delta', v_event.net_action_delta,
      'convergence_pass', v_event.convergence_pass,
      'convergence_exception', v_event.convergence_exception_reason,
      'rescored_details', COALESCE(v_event.cascade_report->'rescored', '[]'::jsonb),
      'resolved_details', COALESCE(v_event.cascade_report->'resolved', '[]'::jsonb),
      'generated_details', COALESCE(v_event.cascade_report->'generated', '[]'::jsonb),
      'summary', v_event.cascade_report->>'summary'
    ),
    'downstream_depth_changes', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'depth_grade_id', dg.id, 'action_id', dg.action_id,
        'action_text', LEFT(dg.action_text, 80),
        'auto_depth', dg.auto_depth, 'strategic_score', dg.strategic_score,
        'execution_status', dg.execution_status, 'updated_at', dg.updated_at
      ) ORDER BY dg.updated_at DESC)
      FROM depth_grades dg
      WHERE dg.updated_at > v_event.created_at
      AND dg.updated_at < v_event.created_at + INTERVAL '1 hour'
      AND dg.thesis_connections && v_event.affected_thesis_threads
    ), '[]'::jsonb),
    'downstream_obligation_changes', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'obligation_id', o.id, 'person', o.person_name,
        'type', o.obligation_type, 'status', o.status,
        'description', LEFT(o.description, 80), 'status_changed_at', o.status_changed_at
      ) ORDER BY o.status_changed_at DESC)
      FROM obligations o
      WHERE o.updated_at > v_event.created_at AND o.updated_at < v_event.created_at + INTERVAL '1 hour'
    ), '[]'::jsonb),
    'cascade_chain', jsonb_build_object(
      'preceding', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'id', ce.id, 'trigger_type', ce.trigger_type,
          'trigger_description', LEFT(ce.trigger_description, 80),
          'net_delta', ce.net_action_delta, 'created_at', ce.created_at
        ) ORDER BY ce.created_at DESC)
        FROM cascade_events ce
        WHERE ce.created_at < v_event.created_at AND ce.created_at > v_event.created_at - INTERVAL '24 hours' AND ce.id != v_event_id
      ), '[]'::jsonb),
      'following', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'id', ce.id, 'trigger_type', ce.trigger_type,
          'trigger_description', LEFT(ce.trigger_description, 80),
          'net_delta', ce.net_action_delta, 'created_at', ce.created_at
        ) ORDER BY ce.created_at ASC)
        FROM cascade_events ce
        WHERE ce.created_at > v_event.created_at AND ce.created_at < v_event.created_at + INTERVAL '24 hours' AND ce.id != v_event_id
      ), '[]'::jsonb)
    ),
    'state_comparison', jsonb_build_object(
      'actions_proposed_now', (SELECT count(*) FROM actions_queue WHERE status = 'Proposed'),
      'convergence_ratio_now', (SELECT round(count(*) FILTER (WHERE status NOT IN ('Proposed'))::numeric / GREATEST(count(*), 1)::numeric, 3) FROM actions_queue),
      'obligations_overdue_now', (SELECT count(*) FROM obligations WHERE status = 'overdue')
    )
  ) INTO v_result;

  RETURN v_result;
END;
$$;


-- =============================================================================
-- Function 4: generate_strategic_narrative(p_focus)
-- Produces structured data for an agent to turn into narrative.
-- The SQL produces DATA, the agent produces NARRATIVE.
--
-- Focus options:
--   'portfolio_attention'  — Red/Yellow companies, follow-on decisions, gaps
--   'thesis_progress'      — All thesis threads with evidence, bias, exposure
--   'network_priorities'   — Top people, obligation hotspots, interaction gaps
--   'upcoming_decisions'   — Decision queue with context, stale candidates, convergence
-- =============================================================================

CREATE OR REPLACE FUNCTION generate_strategic_narrative(p_focus text DEFAULT 'portfolio_attention')
RETURNS JSONB
LANGUAGE plpgsql AS $$
DECLARE
  v_result JSONB;
BEGIN
  CASE p_focus

  WHEN 'portfolio_attention' THEN
    SELECT jsonb_build_object(
      'focus', 'portfolio_attention',
      'generated_at', NOW(),
      'headline_data', jsonb_build_object(
        'total_portfolio_fmv', (SELECT round(sum(fmv_carried)::numeric, 0) FROM portfolio WHERE fmv_carried IS NOT NULL),
        'total_best_case', (SELECT round(sum(ownership_pct * best_case_outcome)::numeric, 0) FROM portfolio WHERE ownership_pct IS NOT NULL AND best_case_outcome IS NOT NULL),
        'red_count', (SELECT count(*) FROM portfolio WHERE health = 'Red'),
        'yellow_count', (SELECT count(*) FROM portfolio WHERE health = 'Yellow'),
        'fmv_at_risk', (SELECT round(sum(fmv_carried)::numeric, 0) FROM portfolio WHERE health IN ('Red','Yellow') AND fmv_carried IS NOT NULL)
      ),
      'urgent_attention', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'company', p.portfolio_co, 'health', p.health, 'ops_priority', p.ops_prio,
          'ownership_pct', round(p.ownership_pct::numeric * 100, 2), 'fmv_carried', p.fmv_carried,
          'current_value', CASE WHEN p.ownership_pct IS NOT NULL AND p.fmv_carried IS NOT NULL THEN round((p.ownership_pct * p.fmv_carried)::numeric, 0) END,
          'best_case_value', CASE WHEN p.ownership_pct IS NOT NULL AND p.best_case_outcome IS NOT NULL THEN round((p.ownership_pct * p.best_case_outcome)::numeric, 0) END,
          'fumes_date', p.fumes_date,
          'days_until_fumes', CASE WHEN p.fumes_date IS NOT NULL THEN (p.fumes_date - CURRENT_DATE) END,
          'cash_in_bank', p.cash_in_bank, 'follow_on_decision', p.follow_on_decision,
          'room_to_deploy', p.room_to_deploy, 'key_questions', p.key_questions,
          'high_impact', p.high_impact, 'external_signal', p.external_signal,
          'spikey', p.spikey, 'scale_of_business', p.scale_of_business,
          'note_on_deployment', LEFT(p.note_on_deployment, 200),
          'thesis_connection', p.thesis_connection
        ) ORDER BY (
          CASE p.health WHEN 'Red' THEN 3 WHEN 'Yellow' THEN 1.5 ELSE 0 END
          + CASE WHEN p.fumes_date IS NOT NULL AND p.fumes_date <= CURRENT_DATE + INTERVAL '90 days' THEN 3 ELSE 0 END
          + CASE WHEN p.ownership_pct > 0.02 THEN 1.5 WHEN p.ownership_pct > 0.01 THEN 0.5 ELSE 0 END
        ) DESC)
        FROM portfolio p WHERE p.health IN ('Red', 'Yellow') AND p.portfolio_co IS NOT NULL
      ), '[]'::jsonb),
      'follow_on_decisions', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'company', p.portfolio_co, 'decision', p.follow_on_decision,
          'health', p.health, 'ownership_pct', round(p.ownership_pct::numeric * 100, 2),
          'room_to_deploy', p.room_to_deploy, 'deployment_notes', LEFT(p.note_on_deployment, 150),
          'best_case_value', CASE WHEN p.ownership_pct IS NOT NULL AND p.best_case_outcome IS NOT NULL THEN round((p.ownership_pct * p.best_case_outcome)::numeric, 0) END
        ) ORDER BY p.ownership_pct DESC)
        FROM portfolio p WHERE p.follow_on_decision IS NOT NULL
      ), '[]'::jsonb),
      'unaddressed_questions', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'company', p.portfolio_co, 'health', p.health,
          'ownership_pct', round(p.ownership_pct::numeric * 100, 2), 'questions', p.key_questions
        ) ORDER BY p.ownership_pct DESC)
        FROM portfolio p
        WHERE p.key_questions IS NOT NULL AND LENGTH(p.key_questions) > 5
        AND NOT EXISTS (
          SELECT 1 FROM actions_queue aq WHERE aq.status IN ('Proposed','Accepted')
          AND (aq.action ILIKE '%' || LEFT(p.portfolio_co, 15) || '%' OR aq.company_notion_id = p.notion_page_id)
        )
      ), '[]'::jsonb)
    ) INTO v_result;

  WHEN 'thesis_progress' THEN
    SELECT jsonb_build_object(
      'focus', 'thesis_progress', 'generated_at', NOW(),
      'thesis_threads', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'name', tt.thread_name, 'conviction', tt.conviction, 'status', tt.status,
          'core_thesis', tt.core_thesis,
          'evidence_for', LEFT(tt.evidence_for, 500),
          'evidence_against', LEFT(tt.evidence_against, 500),
          'key_questions', tt.key_question_summary, 'key_companies', tt.key_companies,
          'investment_implications', tt.investment_implications,
          'bias_flags', tt.bias_flags, 'updated_at', tt.updated_at,
          'momentum_tier', CASE
            WHEN tt.updated_at >= NOW() - INTERVAL '7 days' AND LENGTH(COALESCE(tt.evidence_for,'')) > 500 THEN 'HIGH'
            WHEN tt.updated_at >= NOW() - INTERVAL '30 days' THEN 'MEDIUM' ELSE 'LOW'
          END,
          'open_actions', (SELECT count(*) FROM actions_queue WHERE thesis_connection LIKE '%' || tt.thread_name || '%' AND status IN ('Proposed','Accepted')),
          'resolved_actions', (SELECT count(*) FROM actions_queue WHERE thesis_connection LIKE '%' || tt.thread_name || '%' AND status IN ('Accepted','Dismissed','Done')),
          'portfolio_exposure', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
              'company', p.portfolio_co, 'health', p.health,
              'ownership_pct', round(p.ownership_pct::numeric * 100, 2), 'fmv_carried', p.fmv_carried, 'scale', p.scale_of_business
            )) FROM portfolio p WHERE p.thesis_connection LIKE '%' || tt.thread_name || '%'
          ), '[]'::jsonb),
          'recent_cascades', (SELECT count(*) FROM cascade_events ce WHERE tt.thread_name = ANY(ce.affected_thesis_threads) AND ce.created_at > NOW() - INTERVAL '7 days')
        ) ORDER BY tt.updated_at DESC) FROM thesis_threads tt
      ), '[]'::jsonb),
      'conviction_distribution', COALESCE((
        SELECT jsonb_object_agg(sub.conviction, sub.cnt)
        FROM (SELECT conviction, count(*) as cnt FROM thesis_threads GROUP BY conviction) sub
      ), '{}'::jsonb),
      'bias_alerts', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'thesis', tt.thread_name, 'severity', tt.bias_flags->>'severity',
          'type', tt.bias_flags->>'type', 'details', tt.bias_flags
        )) FROM thesis_threads tt WHERE tt.bias_flags->>'severity' IN ('HIGH','CRITICAL','MEDIUM')
      ), '[]'::jsonb)
    ) INTO v_result;

  WHEN 'network_priorities' THEN
    SELECT jsonb_build_object(
      'focus', 'network_priorities', 'generated_at', NOW(),
      'top_strategic_people', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'person_id', snm.person_id, 'name', snm.person_name, 'role', snm.role_title,
          'importance', snm.strategic_importance, 'portfolio_connections', snm.portfolio_connections,
          'obligations', snm.obligation_count, 'overdue_obligations', snm.obligation_overdue_count,
          'interaction_recency_days', snm.interaction_recency_days, 'interaction_count_30d', snm.interaction_count_30d,
          'narrative', snm.importance_factors->>'narrative',
          'portfolio_companies', snm.importance_factors->'portfolio_companies',
          'obligation_details', snm.importance_factors->'obligation_details'
        )) FROM strategic_network_map(20) snm
      ), '[]'::jsonb),
      'obligation_hotspots', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'person', o.person_name, 'role', o.person_role, 'type', o.obligation_type,
          'status', o.status, 'description', o.description, 'due_date', o.due_date,
          'days_overdue', CASE WHEN o.status = 'overdue' THEN EXTRACT(day FROM NOW() - o.due_date)::int END,
          'blended_priority', round(o.blended_priority::numeric, 2),
          'category', o.category, 'source_quote', LEFT(o.source_quote, 100)
        ) ORDER BY o.blended_priority DESC)
        FROM obligations o WHERE o.status IN ('overdue','escalated','pending')
      ), '[]'::jsonb),
      'interaction_gaps', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'person', n.person_name, 'role', n.role_title,
          'days_since_interaction', EXTRACT(day FROM NOW() - n.last_interaction_at)::int,
          'has_obligations', EXISTS(SELECT 1 FROM obligations o WHERE o.person_id = n.id AND o.status IN ('pending','overdue'))
        ) ORDER BY n.last_interaction_at ASC)
        FROM network n
        WHERE n.last_interaction_at IS NOT NULL AND n.last_interaction_at < NOW() - INTERVAL '30 days'
        AND EXISTS(
          SELECT 1 FROM entity_connections ec
          WHERE ec.source_type = 'network' AND ec.source_id = n.id AND ec.target_type = 'company'
          AND EXISTS(SELECT 1 FROM portfolio p WHERE p.id = ec.target_id AND p.health IN ('Red','Yellow'))
        ) LIMIT 10
      ), '[]'::jsonb)
    ) INTO v_result;

  WHEN 'upcoming_decisions' THEN
    SELECT jsonb_build_object(
      'focus', 'upcoming_decisions', 'generated_at', NOW(),
      'decision_queue', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'action_id', and2.action_id, 'action', and2.action_text,
          'type', and2.action_type, 'priority', and2.priority,
          'strategic_score', and2.strategic_score, 'confidence', and2.score_confidence,
          'days_open', and2.days_open, 'impact_score', and2.decision_impact_score,
          'company_context', and2.company_context, 'thesis_context', and2.thesis_context,
          'obligation_context', and2.obligation_context, 'recommendation', and2.recommendation
        )) FROM actions_needing_decision_v2(15) and2
      ), '[]'::jsonb),
      'convergence_projection', jsonb_build_object(
        'current_ratio', (SELECT round(count(*) FILTER (WHERE status NOT IN ('Proposed'))::numeric / GREATEST(count(*), 1)::numeric, 3) FROM actions_queue),
        'proposed_remaining', (SELECT count(*) FROM actions_queue WHERE status = 'Proposed'),
        'decisions_to_80pct', (SELECT GREATEST(0, CEIL(0.8 * count(*) - count(*) FILTER (WHERE status NOT IN ('Proposed')))) FROM actions_queue)
      ),
      'stale_candidates', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'action_id', aq.id, 'action', LEFT(aq.action, 100), 'type', aq.action_type,
          'days_open', EXTRACT(day FROM NOW() - aq.created_at)::int,
          'strategic_score', round(aq.strategic_score::numeric, 1),
          'has_obligation', EXISTS(SELECT 1 FROM obligations o WHERE o.linked_action_id = aq.id)
        ) ORDER BY aq.created_at ASC)
        FROM actions_queue aq
        WHERE aq.status = 'Proposed' AND aq.created_at < NOW() - INTERVAL '21 days'
        AND NOT EXISTS(SELECT 1 FROM obligations o WHERE o.linked_action_id = aq.id AND o.status IN ('pending','overdue'))
      ), '[]'::jsonb),
      'investment_decisions', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'company', p.portfolio_co, 'decision', p.follow_on_decision,
          'health', p.health, 'ownership_pct', round(p.ownership_pct::numeric * 100, 2),
          'room_to_deploy', p.room_to_deploy, 'notes', LEFT(p.note_on_deployment, 150),
          'fmv_carried', p.fmv_carried, 'best_case_outcome', p.best_case_outcome
        ) ORDER BY p.ownership_pct DESC) FROM portfolio p WHERE p.follow_on_decision IS NOT NULL
      ), '[]'::jsonb)
    ) INTO v_result;

  ELSE
    v_result := jsonb_build_object('error', 'Unknown focus: ' || p_focus || '. Valid: portfolio_attention, thesis_progress, network_priorities, upcoming_decisions');
  END CASE;

  RETURN v_result;
END;
$$;


-- =============================================================================
-- Function 5: megamind_system_report() v5.0
-- Updated to wrap megamind_agent_context() and provide tool catalog.
-- Agent-ready: contains all data + knows what tools to call for deeper dives.
-- =============================================================================

CREATE OR REPLACE FUNCTION megamind_system_report()
RETURNS JSONB
LANGUAGE plpgsql AS $$
DECLARE
  v_result JSONB;
  v_agent_context JSONB;
  v_conv_ratio numeric;
  v_conv_status text;
  v_red_companies integer;
  v_open_actions integer;
  v_portfolio_fmv numeric;
  v_portfolio_best_case numeric;
BEGIN
  v_agent_context := megamind_agent_context();

  v_conv_ratio := (v_agent_context->'convergence'->>'ratio')::numeric;
  v_conv_status := v_agent_context->'convergence'->>'status';
  v_open_actions := (v_agent_context->'convergence'->>'proposed')::integer;
  v_red_companies := (v_agent_context->'portfolio_risk'->'summary'->>'red')::integer;
  v_portfolio_fmv := (v_agent_context->'portfolio_risk'->'summary'->>'total_fmv')::numeric;
  v_portfolio_best_case := (v_agent_context->'portfolio_risk'->'summary'->>'total_best_case')::numeric;

  SELECT jsonb_build_object(
    'timestamp', NOW(),
    'version', 'v5.0-L70',
    'executive_summary', jsonb_build_object(
      'headline', CASE
        WHEN v_conv_ratio >= 0.8 AND v_red_companies < 15 THEN 'System fully converged. Portfolio needs ' || v_red_companies || ' Red company reviews.'
        WHEN v_conv_ratio >= 0.6 THEN 'System converged at ' || round(v_conv_ratio * 100, 0)::text || '%. ' || v_open_actions || ' actions awaiting decision. ' || v_red_companies || ' Red companies.'
        ELSE 'System at ' || round(v_conv_ratio * 100, 0)::text || '% convergence. ' || v_open_actions || ' actions need triage.'
      END,
      'portfolio_snapshot', '$' || round(v_portfolio_fmv / 1000000.0, 1)::text || 'M FMV carried. $' || round(v_portfolio_best_case / 1000000.0, 0)::text || 'M best-case.',
      'urgent_count', (v_agent_context->'obligations'->>'overdue')::integer,
      'convergence_ratio', v_conv_ratio,
      'convergence_status', v_conv_status,
      'convergence_trend', v_agent_context->'convergence'->>'trend'
    ),
    'agent_context', v_agent_context,
    'available_tools', jsonb_build_object(
      'megamind_agent_context', 'Returns full strategic context in one call (9 sections)',
      'actions_needing_decision_v2', 'Actions with full company/person/thesis/obligation context. Args: p_limit',
      'cascade_impact_analysis', 'Full cascade event analysis. Args: p_event_id (NULL=latest)',
      'generate_strategic_narrative', 'Structured data for narratives. Args: p_focus (portfolio_attention|thesis_progress|network_priorities|upcoming_decisions)',
      'portfolio_risk_assessment', 'Per-company risk with 5-component model',
      'strategic_network_map', 'Top N people by importance. Args: p_limit',
      'simulate_convergence', 'Convergence projection under scenarios'
    ),
    'function_catalog', (
      SELECT jsonb_agg(jsonb_build_object('name', r.routine_name, 'returns', r.data_type))
      FROM information_schema.routines r
      WHERE r.routine_schema = 'public'
      AND r.routine_name IN (
        'megamind_agent_context', 'megamind_system_report',
        'actions_needing_decision', 'actions_needing_decision_v2',
        'cascade_impact_analysis', 'generate_strategic_narrative',
        'portfolio_risk_assessment', 'strategic_network_map',
        'generate_strategic_assessment', 'simulate_convergence',
        'create_cascade_event', 'process_cascade_event',
        'obligation_health_summary', 'thesis_health_dashboard',
        'scoring_intelligence_report', 'irgi_system_report',
        'cindy_system_report', 'data_quality_dashboard'
      )
    )
  ) INTO v_result;

  RETURN v_result;
END;
$$;
