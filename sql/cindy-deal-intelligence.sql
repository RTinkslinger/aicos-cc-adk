-- M8 Cindy: Deal Intelligence Layer
-- Created: 2026-03-21
-- Purpose: Auto-generate deal follow-up obligations from WhatsApp deal signals,
--          fix the "poor reasoning" gap where active portfolio deals had no obligations.

-- 1. Deal Obligation Generator
-- Scans interactions with deal_signals, finds deals without active obligations,
-- and creates deal_followup obligations linked to the company's primary contact.
-- Idempotent: won't create duplicates within 7 days.

CREATE OR REPLACE FUNCTION cindy_deal_obligation_generator()
RETURNS jsonb
LANGUAGE plpgsql
AS $function$
DECLARE
  result JSONB;
BEGIN
  WITH deal_interactions AS (
    SELECT
      i.id AS interaction_id,
      i.source,
      i.timestamp,
      i.summary,
      (i.deal_signals->>'company') AS deal_company,
      (i.deal_signals->>'stage') AS deal_stage,
      i.linked_companies,
      c.name AS company_name,
      c.id AS company_id,
      c.priority AS company_priority,
      c.pipeline_status,
      p.portfolio_co,
      p.ops_prio,
      p.health,
      p.ownership_pct,
      p.entry_cheque
    FROM interactions i
    JOIN LATERAL unnest(i.linked_companies) AS lc(cid) ON TRUE
    JOIN companies c ON c.id = lc.cid
    LEFT JOIN portfolio p ON p.company_name_id = c.notion_page_id
    WHERE i.deal_signals IS NOT NULL
      AND i.deal_signals != '{}'::jsonb
      AND i.timestamp > NOW() - INTERVAL '14 days'
  ),
  deals_without_obligations AS (
    SELECT DISTINCT ON (di.company_id)
      di.*,
      (SELECT n.person_name FROM network n
       JOIN entity_connections ec ON ec.source_id = n.id
         AND ec.source_type = 'network'
         AND ec.target_type = 'company'
         AND ec.target_id = di.company_id
         AND ec.connection_type IN ('current_employee', 'founder')
       ORDER BY
         CASE WHEN n.role_title ILIKE '%CEO%' THEN 1
              WHEN n.role_title ILIKE '%founder%' THEN 2
              WHEN n.role_title ILIKE '%CTO%' THEN 3
              ELSE 4 END
       LIMIT 1) AS primary_person_name,
      (SELECT n.id FROM network n
       JOIN entity_connections ec ON ec.source_id = n.id
         AND ec.source_type = 'network'
         AND ec.target_type = 'company'
         AND ec.target_id = di.company_id
         AND ec.connection_type IN ('current_employee', 'founder')
       ORDER BY
         CASE WHEN n.role_title ILIKE '%CEO%' THEN 1
              WHEN n.role_title ILIKE '%founder%' THEN 2
              WHEN n.role_title ILIKE '%CTO%' THEN 3
              ELSE 4 END
       LIMIT 1) AS primary_person_id,
      (SELECT n.role_title FROM network n
       JOIN entity_connections ec ON ec.source_id = n.id
         AND ec.source_type = 'network'
         AND ec.target_type = 'company'
         AND ec.target_id = di.company_id
         AND ec.connection_type IN ('current_employee', 'founder')
       ORDER BY
         CASE WHEN n.role_title ILIKE '%CEO%' THEN 1
              WHEN n.role_title ILIKE '%founder%' THEN 2
              WHEN n.role_title ILIKE '%CTO%' THEN 3
              ELSE 4 END
       LIMIT 1) AS primary_person_role
    FROM deal_interactions di
    WHERE NOT EXISTS (
      SELECT 1 FROM obligations o
      WHERE o.status IN ('pending', 'reminded', 'escalated')
        AND o.context->>'company' = di.company_name
        AND o.detected_at > NOW() - INTERVAL '7 days'
    )
    ORDER BY di.company_id, di.timestamp DESC
  ),
  inserted AS (
    INSERT INTO obligations (
      person_id, person_name, person_role,
      obligation_type, description, category,
      source, source_interaction_id, source_quote,
      detection_method, detected_at,
      due_date, due_date_source,
      status, cindy_priority, cindy_priority_factors,
      context, suggested_action
    )
    SELECT
      dwo.primary_person_id,
      COALESCE(dwo.primary_person_name, dwo.company_name || ' team'),
      dwo.primary_person_role,
      'I_OWE_THEM',
      'Follow up on ' || dwo.company_name || ' deal progress — ' ||
        CASE
          WHEN dwo.deal_stage = 'active-deal' THEN 'active negotiation detected via ' || dwo.source
          WHEN dwo.deal_stage ILIKE '%due-diligence%' THEN 'due diligence in progress'
          ELSE 'deal activity detected'
        END,
      'deal_followup',
      dwo.source,
      dwo.interaction_id,
      LEFT(dwo.summary, 200),
      'deal_signal_auto',
      NOW(),
      (NOW() + INTERVAL '3 days')::date,
      'auto_generated',
      'pending',
      CASE
        WHEN dwo.pipeline_status = 'Portfolio' THEN 0.95
        WHEN dwo.company_priority ILIKE '%P0%' THEN 0.9
        WHEN dwo.company_priority ILIKE '%P1%' THEN 0.8
        ELSE 0.7
      END,
      jsonb_build_object(
        'reason', 'Auto-generated from deal signal',
        'portfolio', dwo.pipeline_status = 'Portfolio',
        'deal_stage', dwo.deal_stage,
        'priority', dwo.company_priority
      ),
      jsonb_build_object(
        'company', dwo.company_name,
        'company_id', dwo.company_id,
        'deal_stage', dwo.deal_stage,
        'portfolio', dwo.pipeline_status = 'Portfolio',
        'ownership_pct', dwo.ownership_pct,
        'entry_cheque', dwo.entry_cheque,
        'health', dwo.health,
        'auto_generated', true
      ),
      'Check deal status and ensure no blockers'
    FROM deals_without_obligations dwo
    WHERE dwo.primary_person_name IS NOT NULL
    RETURNING id
  )
  SELECT jsonb_build_object(
    'generated_at', NOW(),
    'obligations_created', (SELECT COUNT(*) FROM inserted),
    'message', CASE
      WHEN (SELECT COUNT(*) FROM inserted) > 0 THEN (SELECT COUNT(*) FROM inserted) || ' deal follow-up obligations created'
      ELSE 'All active deals already have obligations'
    END
  ) INTO result;

  RETURN result;
END;
$function$;

-- 2. Cron: Run daily at 6am UTC (11:30am IST)
-- SELECT cron.schedule('cindy-deal-obligation-generator', '0 6 * * *', 'SELECT cindy_deal_obligation_generator()');
