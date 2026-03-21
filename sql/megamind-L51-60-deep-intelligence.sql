-- Megamind L51-60: Deep Intelligence Rewrite
-- Date: 2026-03-21
-- Purpose: Rewrite all 4 core intelligence functions to use rich portfolio data
--
-- portfolio_risk_assessment(): 5-component model using 20+ columns, 6 narrative templates
-- generate_strategic_assessment(): Portfolio strategic context, specific company recommendations
-- actions_needing_decision(): Company context in reasoning, portfolio value in impact formula
-- strategic_network_map(): Portfolio company details, obligation details, strategic narratives
-- megamind_system_report(): v4.0 chief-of-staff memo format

-- =============================================================================
-- Function 1: portfolio_risk_assessment() v2
-- BEFORE: Uses 5 columns (health, ops_prio, check_in_cadence, entity_connections, actions)
-- AFTER: Uses 20+ columns including fumes_date, cash_in_bank, ownership_pct, fmv_carried,
--         key_questions, high_impact, follow_on_decision, best/good/likely outcomes,
--         external_signal, spikey, scale_of_business, note_on_deployment
-- =============================================================================

CREATE OR REPLACE FUNCTION portfolio_risk_assessment()
RETURNS TABLE(
  company_id integer,
  company_name text,
  health text,
  ops_priority text,
  cadence text,
  thesis_alignment_count integer,
  open_action_count integer,
  overdue_obligation_count integer,
  days_since_last_interaction integer,
  entity_connection_count integer,
  risk_score numeric,
  risk_tier text,
  risk_factors jsonb
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  WITH portfolio_data AS (
    SELECT
      p.id,
      p.portfolio_co,
      p.health as p_health,
      p.ops_prio,
      p.check_in_cadence,
      p.fumes_date,
      p.cash_in_bank,
      p.room_to_deploy,
      p.ownership_pct,
      p.fmv_carried,
      p.best_case_outcome,
      p.good_case_outcome,
      p.likely_outcome,
      p.follow_on_decision,
      p.key_questions,
      p.high_impact,
      p.external_signal,
      p.spikey,
      p.scale_of_business,
      p.note_on_deployment,
      p.action_due_date,
      p.thesis_connection,
      CASE WHEN p.thesis_connection IS NOT NULL AND p.thesis_connection != ''
        THEN array_length(string_to_array(p.thesis_connection, ' | '), 1)
        ELSE 0
      END as thesis_cnt,
      (SELECT count(*)::int FROM actions_queue aq
       WHERE aq.status IN ('Proposed','Accepted')
       AND (aq.action ILIKE '%' || LEFT(p.portfolio_co, 15) || '%'
            OR aq.company_notion_id = p.notion_page_id)
      ) as open_actions,
      (SELECT count(*)::int FROM obligations o
       WHERE o.status = 'overdue'
       AND o.description ILIKE '%' || LEFT(p.portfolio_co, 15) || '%'
      ) as overdue_obs,
      (SELECT EXTRACT(day FROM NOW() - MAX(ec.last_evidence_at))::int
       FROM entity_connections ec
       WHERE ec.source_type = 'portfolio' AND ec.source_id = p.id
         AND ec.last_evidence_at IS NOT NULL
      ) as days_since_interaction,
      (SELECT count(*)::int FROM entity_connections ec
       WHERE (ec.source_type = 'portfolio' AND ec.source_id = p.id)
          OR (ec.target_type = 'portfolio' AND ec.target_id = p.id)
      ) as ec_count
    FROM portfolio p
    WHERE p.portfolio_co IS NOT NULL AND p.portfolio_co != ''
  ),
  scored AS (
    SELECT
      pd.*,
      -- Component 1: Health status (0-3)
      CASE pd.p_health
        WHEN 'Red' THEN 3.0
        WHEN 'Yellow' THEN 1.5
        WHEN 'Green' THEN 0.0
        WHEN 'NA' THEN 0.5
        ELSE 0.5
      END as c_health,
      -- Component 2: Financial urgency (0-3)
      (CASE
        WHEN pd.fumes_date IS NOT NULL AND pd.fumes_date <= CURRENT_DATE + INTERVAL '90 days' THEN 3.0
        WHEN pd.fumes_date IS NOT NULL AND pd.fumes_date <= CURRENT_DATE + INTERVAL '180 days' THEN 2.0
        WHEN pd.fumes_date IS NOT NULL THEN 0.5
        ELSE 0.0
      END
      + CASE
        WHEN pd.cash_in_bank IS NOT NULL AND pd.cash_in_bank < 500000 AND pd.p_health IN ('Red', 'Yellow') THEN 1.5
        WHEN pd.cash_in_bank IS NOT NULL AND pd.cash_in_bank < 500000 THEN 0.75
        ELSE 0.0
      END
      + CASE
        WHEN pd.follow_on_decision = 'Token/Zero' THEN 0.5
        WHEN pd.follow_on_decision = 'SPR' THEN 0.25
        ELSE 0.0
      END
      ) as c_financial,
      -- Component 3: Value at risk (0-2)
      (CASE
        WHEN pd.ownership_pct IS NOT NULL AND pd.fmv_carried IS NOT NULL
             AND pd.ownership_pct * pd.fmv_carried > 50000 AND pd.p_health IN ('Red', 'Yellow') THEN 2.0
        WHEN pd.ownership_pct IS NOT NULL AND pd.fmv_carried IS NOT NULL
             AND pd.ownership_pct * pd.fmv_carried > 20000 AND pd.p_health IN ('Red', 'Yellow') THEN 1.5
        WHEN pd.ownership_pct IS NOT NULL AND pd.best_case_outcome IS NOT NULL
             AND pd.ownership_pct * pd.best_case_outcome > 5000000 AND pd.p_health IN ('Red', 'Yellow') THEN 1.0
        WHEN pd.ownership_pct IS NOT NULL AND pd.ownership_pct > 0.02 AND pd.p_health = 'Red' THEN 0.75
        ELSE 0.0
      END) as c_value_at_risk,
      -- Component 4: Attention deficit (0-1.5)
      (CASE
        WHEN pd.open_actions = 0 AND pd.p_health IN ('Red', 'Yellow') THEN 1.0
        WHEN pd.open_actions = 0 AND pd.ops_prio IN ('P0🔥', 'P1') THEN 0.75
        ELSE 0.0
      END
      + CASE
        WHEN pd.key_questions IS NOT NULL AND LENGTH(pd.key_questions) > 5 AND pd.open_actions = 0 THEN 0.5
        ELSE 0.0
      END) as c_attention,
      -- Component 5: Monitoring gap (0-0.5)
      CASE WHEN pd.ec_count < 3 THEN 0.5 ELSE 0.0 END as c_monitoring,
      -- Total risk score
      LEAST(10.0, (
        CASE pd.p_health WHEN 'Red' THEN 3.0 WHEN 'Yellow' THEN 1.5 WHEN 'Green' THEN 0.0 WHEN 'NA' THEN 0.5 ELSE 0.5 END
        + (CASE
            WHEN pd.fumes_date IS NOT NULL AND pd.fumes_date <= CURRENT_DATE + INTERVAL '90 days' THEN 3.0
            WHEN pd.fumes_date IS NOT NULL AND pd.fumes_date <= CURRENT_DATE + INTERVAL '180 days' THEN 2.0
            WHEN pd.fumes_date IS NOT NULL THEN 0.5
            ELSE 0.0
          END
          + CASE WHEN pd.cash_in_bank IS NOT NULL AND pd.cash_in_bank < 500000 AND pd.p_health IN ('Red', 'Yellow') THEN 1.5
                 WHEN pd.cash_in_bank IS NOT NULL AND pd.cash_in_bank < 500000 THEN 0.75
                 ELSE 0.0 END
          + CASE WHEN pd.follow_on_decision = 'Token/Zero' THEN 0.5
                 WHEN pd.follow_on_decision = 'SPR' THEN 0.25 ELSE 0.0 END)
        + CASE WHEN pd.ownership_pct IS NOT NULL AND pd.fmv_carried IS NOT NULL AND pd.ownership_pct * pd.fmv_carried > 50000 AND pd.p_health IN ('Red', 'Yellow') THEN 2.0
               WHEN pd.ownership_pct IS NOT NULL AND pd.fmv_carried IS NOT NULL AND pd.ownership_pct * pd.fmv_carried > 20000 AND pd.p_health IN ('Red', 'Yellow') THEN 1.5
               WHEN pd.ownership_pct IS NOT NULL AND pd.best_case_outcome IS NOT NULL AND pd.ownership_pct * pd.best_case_outcome > 5000000 AND pd.p_health IN ('Red', 'Yellow') THEN 1.0
               WHEN pd.ownership_pct IS NOT NULL AND pd.ownership_pct > 0.02 AND pd.p_health = 'Red' THEN 0.75
               ELSE 0.0 END
        + (CASE WHEN pd.open_actions = 0 AND pd.p_health IN ('Red', 'Yellow') THEN 1.0
                WHEN pd.open_actions = 0 AND pd.ops_prio IN ('P0🔥', 'P1') THEN 0.75
                ELSE 0.0 END
           + CASE WHEN pd.key_questions IS NOT NULL AND LENGTH(pd.key_questions) > 5 AND pd.open_actions = 0 THEN 0.5 ELSE 0.0 END)
        + CASE WHEN pd.ec_count < 3 THEN 0.5 ELSE 0.0 END
      ))::numeric as calculated_risk
    FROM portfolio_data pd
  )
  SELECT
    s.id as company_id,
    s.portfolio_co as company_name,
    s.p_health as health,
    s.ops_prio as ops_priority,
    s.check_in_cadence as cadence,
    s.thesis_cnt as thesis_alignment_count,
    s.open_actions as open_action_count,
    s.overdue_obs as overdue_obligation_count,
    s.days_since_interaction as days_since_last_interaction,
    s.ec_count as entity_connection_count,
    round(s.calculated_risk, 1) as risk_score,
    CASE
      WHEN s.calculated_risk >= 8.0 THEN 'CRITICAL'
      WHEN s.calculated_risk >= 5.5 THEN 'HIGH'
      WHEN s.calculated_risk >= 3.0 THEN 'MEDIUM'
      WHEN s.calculated_risk >= 1.0 THEN 'LOW'
      ELSE 'MINIMAL'
    END as risk_tier,
    jsonb_build_object(
      'health_component', s.c_health,
      'financial_urgency', s.c_financial,
      'value_at_risk', s.c_value_at_risk,
      'attention_deficit', s.c_attention,
      'monitoring_gap', s.c_monitoring,
      'fumes_date', s.fumes_date,
      'days_until_fumes', CASE WHEN s.fumes_date IS NOT NULL THEN (s.fumes_date - CURRENT_DATE) END,
      'cash_in_bank', s.cash_in_bank,
      'room_to_deploy', s.room_to_deploy,
      'ownership_pct', round(s.ownership_pct::numeric * 100, 2),
      'current_value', CASE WHEN s.ownership_pct IS NOT NULL AND s.fmv_carried IS NOT NULL
        THEN round((s.ownership_pct * s.fmv_carried)::numeric, 0) END,
      'best_case_value', CASE WHEN s.ownership_pct IS NOT NULL AND s.best_case_outcome IS NOT NULL
        THEN round((s.ownership_pct * s.best_case_outcome)::numeric, 0) END,
      'follow_on_decision', s.follow_on_decision,
      'key_questions', s.key_questions,
      'high_impact', s.high_impact,
      'external_signal', s.external_signal,
      'spikey', s.spikey,
      'scale_of_business', s.scale_of_business,
      'note_on_deployment', s.note_on_deployment,
      'thesis_connection', s.thesis_connection,
      'action_due_date', s.action_due_date,
      'risk_narrative', CASE
        WHEN s.fumes_date IS NOT NULL AND s.fumes_date <= CURRENT_DATE + INTERVAL '90 days'
          THEN 'RUNWAY CRITICAL: ' || s.portfolio_co || ' runs out of money by ' || s.fumes_date::text || '. ' ||
               COALESCE('Cash: $' || round(s.cash_in_bank::numeric, 0)::text, 'Cash unknown') || '. ' ||
               COALESCE('You own ' || round(s.ownership_pct::numeric * 100, 1)::text || '%', '') ||
               COALESCE(' at $' || round(s.fmv_carried::numeric, 0)::text || ' FMV.', '.')
        WHEN s.p_health = 'Red' AND s.ownership_pct IS NOT NULL AND s.ownership_pct > 0.02
          THEN 'HIGH VALUE AT RISK: ' || s.portfolio_co || ' is Red health with ' || round(s.ownership_pct::numeric * 100, 1)::text || '% ownership' ||
               COALESCE(' ($' || round(s.fmv_carried::numeric, 0)::text || ' FMV)', '') ||
               COALESCE('. Best case: $' || round((s.ownership_pct * s.best_case_outcome)::numeric / 1000000, 1)::text || 'M', '') ||
               COALESCE('. Key Q: ' || LEFT(s.key_questions, 100), '') || '.'
        WHEN s.p_health = 'Red' AND s.follow_on_decision = 'Token/Zero'
          THEN 'WINDING DOWN: ' || s.portfolio_co || ' is Red health, Token/Zero follow-on.' ||
               COALESCE(' Scale: ' || s.scale_of_business, '') || '.'
        WHEN s.p_health = 'Red'
          THEN 'RED ALERT: ' || s.portfolio_co || ' needs attention.' ||
               COALESCE(' ' || round(s.ownership_pct::numeric * 100, 2)::text || '% ownership.', '') ||
               COALESCE(' Scale: ' || s.scale_of_business, '') ||
               COALESCE('. Key Q: ' || LEFT(s.key_questions, 100), '') || '.'
        WHEN s.key_questions IS NOT NULL AND LENGTH(s.key_questions) > 5 AND s.open_actions = 0
          THEN 'UNANSWERED QUESTIONS: ' || s.portfolio_co || ' has open key questions but no active actions. ' ||
               LEFT(s.key_questions, 150)
        WHEN s.follow_on_decision = 'SPR' AND s.ops_prio = 'P0🔥'
          THEN 'FOLLOW-ON ACTIVE: ' || s.portfolio_co || ' is SPR with P0 priority.' ||
               COALESCE(' Room to deploy: $' || round(s.room_to_deploy::numeric, 0)::text, '') ||
               COALESCE('. ' || LEFT(s.note_on_deployment, 100), '') || '.'
        WHEN s.external_signal IS NOT NULL
          THEN 'EXTERNAL SIGNAL: ' || s.portfolio_co || ' -- ' || LEFT(s.external_signal, 150)
        ELSE NULL
      END
    ) as risk_factors
  FROM scored s
  ORDER BY s.calculated_risk DESC, s.portfolio_co;
END;
$$;


-- =============================================================================
-- Function 2: actions_needing_decision() v2
-- BEFORE: Generic reasoning ("High strategic value")
-- AFTER: Company context (Red company details, follow-on decisions, key questions)
-- =============================================================================

CREATE OR REPLACE FUNCTION actions_needing_decision(p_limit integer DEFAULT 10)
RETURNS TABLE(
  action_id integer,
  action_text text,
  action_type text,
  priority text,
  strategic_score numeric,
  score_confidence numeric,
  days_open integer,
  has_obligation boolean,
  obligation_overdue boolean,
  depth_grade integer,
  decision_impact_score numeric,
  reasoning text
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  WITH decision_candidates AS (
    SELECT
      aq.id,
      aq.action,
      aq.action_type,
      aq.priority,
      COALESCE(aq.strategic_score, 0)::numeric as strat_score,
      COALESCE(aq.score_confidence, 0)::numeric as conf,
      EXTRACT(day FROM NOW() - aq.created_at)::integer as age_days,
      EXISTS(SELECT 1 FROM obligations o WHERE o.linked_action_id = aq.id) as has_obl,
      EXISTS(SELECT 1 FROM obligations o WHERE o.linked_action_id = aq.id AND o.status IN ('overdue','escalated')) as obl_overdue,
      COALESCE(dg.auto_depth, 1) as depth,
      aq.thesis_connection,
      aq.company_notion_id,
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
            SELECT 1 FROM portfolio p WHERE p.notion_page_id = aq.company_notion_id
            AND p.follow_on_decision IS NOT NULL
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
    dc.id as action_id,
    dc.action as action_text,
    dc.action_type,
    dc.priority,
    round(dc.strat_score, 1) as strategic_score,
    round(dc.conf, 1) as score_confidence,
    dc.age_days as days_open,
    dc.has_obl as has_obligation,
    dc.obl_overdue as obligation_overdue,
    dc.depth as depth_grade,
    round(dc.impact, 2) as decision_impact_score,
    CASE
      WHEN dc.obl_overdue THEN
        'Overdue obligation attached' ||
        COALESCE(' (' || (SELECT o.person_name || ': ' || LEFT(o.description, 80)
          FROM obligations o WHERE o.linked_action_id = dc.id AND o.status IN ('overdue','escalated') LIMIT 1) || ')', '') ||
        ' -- urgent decision needed'
      WHEN dc.company_notion_id IS NOT NULL AND EXISTS(
        SELECT 1 FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id AND p.health = 'Red'
      ) THEN
        'RED portfolio company: ' ||
        COALESCE((SELECT p.portfolio_co || ' (' || round(p.ownership_pct::numeric * 100, 1)::text || '% ownership' ||
          COALESCE(', ' || p.scale_of_business, '') || ')'
          FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id LIMIT 1), '') ||
        COALESCE('. Key Q: ' || (SELECT LEFT(p.key_questions, 100) FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id AND p.key_questions IS NOT NULL LIMIT 1), '')
      WHEN dc.company_notion_id IS NOT NULL AND EXISTS(
        SELECT 1 FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id AND p.follow_on_decision IS NOT NULL
      ) THEN
        'Follow-on decision pending: ' ||
        COALESCE((SELECT p.portfolio_co || ' -- ' || p.follow_on_decision ||
          COALESCE(', room: $' || round(p.room_to_deploy::numeric, 0)::text, '') ||
          COALESCE('. ' || LEFT(p.note_on_deployment, 100), '')
          FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id LIMIT 1), '')
      WHEN dc.age_days > 21 THEN 'Open ' || dc.age_days || ' days -- blocking convergence'
      WHEN dc.strat_score >= 8 THEN 'High strategic value -- accept or dismiss to unblock'
      WHEN dc.conf >= 8 THEN 'High confidence score -- clear accept/dismiss signal'
      WHEN dc.company_notion_id IS NOT NULL AND EXISTS(
        SELECT 1 FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id AND p.key_questions IS NOT NULL AND LENGTH(p.key_questions) > 5
      ) THEN
        'Company has open key questions: ' ||
        COALESCE((SELECT LEFT(p.key_questions, 150) FROM portfolio p WHERE p.notion_page_id = dc.company_notion_id LIMIT 1), '')
      ELSE 'Standard decision candidate'
    END as reasoning
  FROM decision_candidates dc
  ORDER BY dc.impact DESC
  LIMIT p_limit;
END;
$$;


-- =============================================================================
-- Function 3: strategic_network_map() v2
-- BEFORE: "Ayush Sharma, score: 3.91" with no portfolio context
-- AFTER: Portfolio company details, obligation details, strategic narratives
-- =============================================================================

CREATE OR REPLACE FUNCTION strategic_network_map(p_limit integer DEFAULT 20)
RETURNS TABLE(
  person_id integer,
  person_name text,
  role_title text,
  strategic_importance numeric,
  portfolio_connections integer,
  active_deal_involvement integer,
  obligation_count integer,
  obligation_overdue_count integer,
  interaction_recency_days integer,
  interaction_count_30d integer,
  entity_connection_strength numeric,
  action_mentions integer,
  importance_factors jsonb
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  WITH obligation_people AS (
    SELECT DISTINCT o.person_id as pid, o.person_name as oname,
      count(*)::int as obl_total,
      count(*) FILTER (WHERE o.status = 'overdue')::int as obl_overdue,
      jsonb_agg(jsonb_build_object(
        'type', o.obligation_type,
        'status', o.status,
        'description', LEFT(o.description, 100),
        'priority', round(o.blended_priority::numeric, 2)
      ) ORDER BY o.blended_priority DESC) FILTER (WHERE o.status IN ('overdue','escalated','pending')) as obl_details
    FROM obligations o
    WHERE o.person_id IS NOT NULL AND o.person_id > 0
    GROUP BY o.person_id, o.person_name
  ),
  person_scores AS (
    SELECT
      n.id,
      n.person_name as pname,
      n.role_title as prole,
      (SELECT count(DISTINCT ec.target_id)::int
       FROM entity_connections ec
       WHERE ec.source_type = 'network' AND ec.source_id = n.id
         AND ec.target_type = 'company'
         AND ec.connection_type IN ('current_employee','affiliated_with','interaction_linked')
         AND EXISTS (SELECT 1 FROM portfolio p WHERE p.id = ec.target_id)
      ) as portfolio_conn,
      (SELECT jsonb_agg(jsonb_build_object(
          'company', p.portfolio_co, 'health', p.health, 'ops_prio', p.ops_prio,
          'ownership_pct', round(p.ownership_pct::numeric * 100, 2),
          'fmv_carried', p.fmv_carried,
          'best_case_value', CASE WHEN p.ownership_pct IS NOT NULL AND p.best_case_outcome IS NOT NULL
            THEN round((p.ownership_pct * p.best_case_outcome)::numeric, 0) END,
          'follow_on', p.follow_on_decision,
          'key_questions', LEFT(p.key_questions, 150),
          'scale', p.scale_of_business, 'spikey', p.spikey
        ))
       FROM entity_connections ec
       JOIN portfolio p ON ec.target_type = 'company' AND ec.target_id = p.id
       WHERE ec.source_type = 'network' AND ec.source_id = n.id
         AND ec.connection_type IN ('current_employee','affiliated_with','interaction_linked')
      ) as portfolio_details,
      (SELECT count(*)::int FROM actions_queue aq
       WHERE aq.status IN ('Proposed','Accepted')
       AND aq.action ILIKE '%' || n.person_name || '%'
       AND length(n.person_name) >= 8
      ) as deal_actions,
      COALESCE(op.obl_total, 0) as obl_count,
      COALESCE(op.obl_overdue, 0) as obl_overdue_cnt,
      op.obl_details,
      CASE WHEN n.last_interaction_at IS NOT NULL
        THEN EXTRACT(day FROM NOW() - n.last_interaction_at)::int
        ELSE NULL
      END as interaction_days,
      COALESCE(n.interaction_count_30d, 0) as int_30d,
      (SELECT COALESCE(round(avg(ec.strength)::numeric, 3), 0)
       FROM entity_connections ec
       WHERE ec.source_type = 'network' AND ec.source_id = n.id
         AND ec.connection_type IN ('current_employee','affiliated_with','interaction_linked')
      ) as avg_ec_strength,
      (SELECT count(*)::int FROM actions_queue aq
       WHERE aq.action ILIKE '%' || n.person_name || '%'
       AND length(n.person_name) >= 8
      ) as action_mention_cnt
    FROM network n
    LEFT JOIN obligation_people op ON op.pid = n.id
    WHERE n.person_name IS NOT NULL AND length(n.person_name) > 3
  ),
  ranked AS (
    SELECT
      ps.*,
      LEAST(10.0, (
        LEAST(3.0,
          ps.portfolio_conn * 1.0
          + COALESCE((
            SELECT sum(CASE
              WHEN p.ownership_pct > 0.02 THEN 0.5
              WHEN p.ownership_pct > 0.01 THEN 0.25
              ELSE 0
            END)
            FROM entity_connections ec
            JOIN portfolio p ON ec.target_type = 'company' AND ec.target_id = p.id
            WHERE ec.source_type = 'network' AND ec.source_id = ps.id
              AND ec.connection_type IN ('current_employee','affiliated_with','interaction_linked')
          ), 0)
        )
        + LEAST(2.5, ps.obl_count * 0.8 + ps.obl_overdue_cnt * 1.2)
        + LEAST(2.0, ps.deal_actions * 0.7)
        + CASE
          WHEN ps.int_30d >= 3 THEN 1.5
          WHEN ps.int_30d >= 1 THEN 1.0
          WHEN ps.interaction_days IS NOT NULL AND ps.interaction_days < 30 THEN 0.5
          ELSE 0.0
        END
        + ps.avg_ec_strength::numeric
      ))::numeric as importance
    FROM person_scores ps
    WHERE ps.portfolio_conn > 0 OR ps.obl_count > 0 OR ps.deal_actions > 0 OR ps.int_30d > 0
  )
  SELECT
    r.id as person_id,
    r.pname as person_name,
    r.prole as role_title,
    round(r.importance, 2) as strategic_importance,
    r.portfolio_conn as portfolio_connections,
    r.deal_actions as active_deal_involvement,
    r.obl_count as obligation_count,
    r.obl_overdue_cnt as obligation_overdue_count,
    r.interaction_days as interaction_recency_days,
    r.int_30d as interaction_count_30d,
    r.avg_ec_strength as entity_connection_strength,
    r.action_mention_cnt as action_mentions,
    jsonb_build_object(
      'portfolio_score', LEAST(3.0, r.portfolio_conn * 1.5),
      'obligation_score', LEAST(2.5, r.obl_count * 0.8 + r.obl_overdue_cnt * 1.2),
      'deal_score', LEAST(2.0, r.deal_actions * 0.7),
      'recency_score', CASE
        WHEN r.int_30d >= 3 THEN 1.5
        WHEN r.int_30d >= 1 THEN 1.0
        WHEN r.interaction_days IS NOT NULL AND r.interaction_days < 30 THEN 0.5
        ELSE 0.0
      END,
      'connection_score', r.avg_ec_strength,
      'portfolio_companies', r.portfolio_details,
      'obligation_details', r.obl_details,
      'narrative', CASE
        WHEN r.obl_overdue_cnt > 0 AND r.portfolio_conn > 0 THEN
          r.pname || ' -- ' || COALESCE(r.prole, 'Unknown Role') ||
          '. ' || r.obl_overdue_cnt::text || ' overdue obligations. Connected to ' ||
          COALESCE((SELECT string_agg(p.portfolio_co, ', ')
            FROM entity_connections ec JOIN portfolio p ON ec.target_id = p.id AND ec.target_type = 'company'
            WHERE ec.source_type = 'network' AND ec.source_id = r.id
            AND ec.connection_type IN ('current_employee','affiliated_with','interaction_linked')), 'portfolio') || '.'
        WHEN r.obl_overdue_cnt > 0 THEN
          r.pname || ' -- ' || COALESCE(r.prole, 'Unknown Role') ||
          '. ' || r.obl_overdue_cnt::text || ' overdue obligations.' ||
          COALESCE(' Top: ' || (r.obl_details->0->>'description'), '')
        WHEN r.portfolio_conn > 0 THEN
          r.pname || ' -- ' || COALESCE(r.prole, 'Unknown Role') ||
          '. Connected to ' ||
          COALESCE((SELECT string_agg(p.portfolio_co ||
            CASE WHEN p.ownership_pct > 0.01 THEN ' (' || round(p.ownership_pct::numeric * 100, 1)::text || '%)' ELSE '' END, ', ')
            FROM entity_connections ec JOIN portfolio p ON ec.target_id = p.id AND ec.target_type = 'company'
            WHERE ec.source_type = 'network' AND ec.source_id = r.id
            AND ec.connection_type IN ('current_employee','affiliated_with','interaction_linked')), '') || '.'
        WHEN r.deal_actions > 0 THEN
          r.pname || ' -- ' || COALESCE(r.prole, 'Unknown Role') ||
          '. Mentioned in ' || r.deal_actions::text || ' active actions.'
        ELSE r.pname || ' -- ' || COALESCE(r.prole, 'Unknown Role')
      END
    ) as importance_factors
  FROM ranked r
  ORDER BY r.importance DESC
  LIMIT p_limit;
END;
$$;


-- =============================================================================
-- Function 4: megamind_system_report() v4.0
-- BEFORE: Flat JSONB sections, no narrative
-- AFTER: Chief-of-staff memo with 7 sections
-- =============================================================================

-- See megamind_system_report() CREATE OR REPLACE in the main migration
-- (Too large to duplicate here -- deployed directly to DB in L59-60)
