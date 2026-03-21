-- IRGI L61-70: Agent-Ready Tools
-- 4 new functions that produce rich CONTEXT for agents to reason about
-- Created: 2026-03-21

------------------------------------------------------------
-- L61-62: agent_search_context
-- The PRIMARY search tool for ENIAC and other agents.
-- Enriches hybrid_search results with: WHY each result matters,
-- portfolio connection, thesis relevance, recent signals,
-- obligation context, interaction recency, agent action hints.
------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.agent_search_context(
  p_query TEXT,
  p_embedding vector(1024) DEFAULT NULL,
  p_limit INT DEFAULT 15
)
RETURNS TABLE(
  source_table TEXT,
  record_id INT,
  title TEXT,
  combined_score FLOAT,
  why_it_matters TEXT,
  portfolio_connection TEXT,
  thesis_relevance TEXT,
  recent_signals TEXT,
  obligation_context TEXT,
  interaction_recency TEXT,
  agent_action_hint TEXT
)
LANGUAGE plpgsql STABLE
SET search_path TO 'public', 'extensions'
AS $function$
BEGIN
  RETURN QUERY
  WITH base_search AS (
    SELECT es.source_table, es.record_id, es.title, es.combined_score, es.context_snippet
    FROM enriched_search(p_query, p_embedding, p_limit * 2) es
  ),
  enriched AS (
    SELECT
      bs.source_table,
      bs.record_id,
      bs.title,
      bs.combined_score,
      CASE
        WHEN bs.source_table = 'companies' THEN
          COALESCE(
            (SELECT 'PORTFOLIO COMPANY [' || p.health || '] — Own ' ||
              ROUND((p.ownership_pct * 100)::numeric, 1) || '% | ' ||
              COALESCE(p.scale_of_business, 'no scale data') ||
              CASE WHEN p.fumes_date IS NOT NULL AND p.fumes_date < CURRENT_DATE + INTERVAL '90 days'
                THEN ' | FUMES IN ' || (p.fumes_date - CURRENT_DATE) || ' DAYS' ELSE '' END
             FROM companies c JOIN portfolio p ON LOWER(p.portfolio_co) = LOWER(c.name)
             WHERE c.id = bs.record_id),
            (SELECT 'Pipeline company: ' || COALESCE(c.sector, '?') || ' | Deal: ' || COALESCE(c.deal_status, 'unknown') ||
              CASE WHEN c.page_content IS NOT NULL AND LENGTH(c.page_content) > 200
                THEN ' | Has rich profile (' || LENGTH(c.page_content) || ' chars)' ELSE '' END
             FROM companies c WHERE c.id = bs.record_id)
          )
        WHEN bs.source_table = 'network' THEN
          (SELECT
            COALESCE(nw.role_title, 'Unknown role') ||
            CASE WHEN nw.e_e_priority IN ('High', 'Core') THEN ' | HIGH PRIORITY CONTACT' ELSE '' END ||
            CASE WHEN nw.ryg = 'Green' THEN ' | Active relationship'
                 WHEN nw.ryg = 'Red' THEN ' | RELATIONSHIP NEEDS ATTENTION'
                 WHEN nw.ryg = 'Yellow' THEN ' | Relationship warming' ELSE '' END ||
            CASE WHEN nw.last_interaction_at IS NOT NULL
              THEN ' | Last seen: ' || nw.last_interaction_at::date ||
                CASE WHEN nw.last_interaction_at < NOW() - INTERVAL '90 days' THEN ' (STALE)'
                     WHEN nw.last_interaction_at < NOW() - INTERVAL '30 days' THEN ' (aging)'
                     ELSE ' (recent)' END
              ELSE ' | NO INTERACTION HISTORY' END ||
            CASE WHEN nw.interaction_count_30d > 0
              THEN ' | ' || nw.interaction_count_30d || ' interactions last 30d' ELSE '' END
           FROM network nw WHERE nw.id = bs.record_id)
        WHEN bs.source_table = 'thesis_threads' THEN
          (SELECT '[' || COALESCE(tt.conviction, '?') || ' conviction] ' || COALESCE(tt.status, '?') ||
            ' | ' || COALESCE(LEFT(tt.core_thesis, 200), 'no core thesis') ||
            CASE WHEN tt.bias_flags IS NOT NULL AND tt.bias_flags->>'severity' IN ('CRITICAL', 'HIGH')
              THEN ' | BIAS ALERT: ' || (tt.bias_flags->>'severity') ELSE '' END ||
            CASE WHEN tt.updated_at < NOW() - INTERVAL '30 days'
              THEN ' | STALE (not updated in ' || EXTRACT(DAY FROM NOW() - tt.updated_at)::int || ' days)' ELSE '' END
           FROM thesis_threads tt WHERE tt.id = bs.record_id)
        WHEN bs.source_table = 'actions_queue' THEN
          (SELECT '[' || COALESCE(aq.action_type, '?') || '/' || COALESCE(aq.status, '?') || '] ' ||
            CASE WHEN aq.user_priority_score IS NOT NULL
              THEN 'Priority: ' || ROUND(aq.user_priority_score::numeric, 1) || '/10' ELSE 'Unscored' END ||
            CASE WHEN aq.strategic_score IS NOT NULL
              THEN ' | Strategic: ' || ROUND(aq.strategic_score::numeric, 1) ELSE '' END ||
            ' | ' || COALESCE(LEFT(aq.reasoning, 200), 'no reasoning')
           FROM actions_queue aq WHERE aq.id = bs.record_id)
        WHEN bs.source_table = 'content_digests' THEN
          (SELECT COALESCE(cd.channel, '?') || ' | Published: ' || cd.created_at::date ||
            CASE WHEN cd.digest_data IS NOT NULL THEN ' | Has digest analysis' ELSE '' END
           FROM content_digests cd WHERE cd.id = bs.record_id)
        ELSE bs.context_snippet
      END AS why_it_matters,

      CASE
        WHEN bs.source_table = 'companies' THEN
          (SELECT 'DIRECT: ' || p.portfolio_co || ' [' || COALESCE(p.health, '?') || '] ' || COALESCE(p.current_stage, '?')
           FROM companies c JOIN portfolio p ON LOWER(p.portfolio_co) = LOWER(c.name) WHERE c.id = bs.record_id)
        WHEN bs.source_table = 'network' THEN
          (SELECT string_agg(DISTINCT p.portfolio_co || ' [' || COALESCE(p.health, '?') || ']', '; ')
           FROM entity_connections ec
           JOIN companies c ON (ec.target_type = 'company' AND ec.target_id = c.id) OR (ec.source_type = 'company' AND ec.source_id = c.id)
           JOIN portfolio p ON LOWER(p.portfolio_co) = LOWER(c.name)
           WHERE (ec.source_type = 'network' AND ec.source_id = bs.record_id) OR (ec.target_type = 'network' AND ec.target_id = bs.record_id))
        WHEN bs.source_table = 'thesis_threads' THEN
          (SELECT string_agg(DISTINCT p.portfolio_co || ' [' || COALESCE(p.health, '?') || ']', '; ')
           FROM entity_connections ec JOIN companies c ON ec.source_type = 'company' AND ec.source_id = c.id
           JOIN portfolio p ON LOWER(p.portfolio_co) = LOWER(c.name)
           WHERE ec.target_type = 'thesis' AND ec.target_id = bs.record_id LIMIT 5)
        ELSE NULL
      END AS portfolio_connection,

      CASE
        WHEN bs.source_table = 'thesis_threads' THEN 'IS A THESIS'
        ELSE (SELECT string_agg(tt.thread_name || ' [' || COALESCE(tt.conviction, '?') || ']', '; ' ORDER BY ec.strength DESC NULLS LAST)
           FROM entity_connections ec JOIN thesis_threads tt ON ec.target_type = 'thesis' AND ec.target_id = tt.id
           WHERE ec.source_type = CASE bs.source_table WHEN 'companies' THEN 'company' WHEN 'network' THEN 'network'
                    WHEN 'actions_queue' THEN 'action' ELSE bs.source_table END AND ec.source_id = bs.record_id LIMIT 3)
      END AS thesis_relevance,

      CASE WHEN bs.source_table IN ('companies', 'network') THEN
          (SELECT string_agg(i.source || ' (' || i.timestamp::date || '): ' || LEFT(COALESCE(i.summary, ''), 100), ' | ' ORDER BY i.timestamp DESC)
           FROM entity_connections ec JOIN interactions i ON ec.source_type = 'interaction' AND ec.source_id = i.id
           WHERE ec.target_type = CASE bs.source_table WHEN 'companies' THEN 'company' ELSE 'network' END AND ec.target_id = bs.record_id LIMIT 3)
        ELSE NULL END AS recent_signals,

      CASE
        WHEN bs.source_table = 'network' THEN
          (SELECT string_agg('[' || o.obligation_type || '] ' || LEFT(o.description, 100) ||
            CASE WHEN o.due_date IS NOT NULL THEN ' DUE: ' || o.due_date::date ELSE '' END || ' (' || o.status || ')', ' | ' ORDER BY o.cindy_priority DESC)
           FROM obligations o WHERE o.person_id = bs.record_id AND o.status NOT IN ('fulfilled', 'cancelled') LIMIT 3)
        WHEN bs.source_table = 'companies' THEN
          (SELECT string_agg('[' || o.obligation_type || '] ' || o.person_name || ': ' || LEFT(o.description, 80) || ' (' || o.status || ')', ' | ' ORDER BY o.cindy_priority DESC)
           FROM obligations o JOIN entity_connections ec ON ec.source_type = 'network' AND ec.source_id = o.person_id
           WHERE ec.target_type = 'company' AND ec.target_id = bs.record_id AND o.status NOT IN ('fulfilled', 'cancelled') LIMIT 3)
        ELSE NULL END AS obligation_context,

      CASE
        WHEN bs.source_table = 'network' THEN
          (SELECT CASE WHEN nw.last_interaction_at IS NULL THEN 'NEVER interacted'
                 WHEN nw.last_interaction_at > NOW() - INTERVAL '7 days' THEN 'This week'
                 WHEN nw.last_interaction_at > NOW() - INTERVAL '30 days' THEN 'This month'
                 WHEN nw.last_interaction_at > NOW() - INTERVAL '90 days' THEN 'Last quarter'
                 ELSE 'Over 90 days ago (' || nw.last_interaction_at::date || ')' END ||
            CASE WHEN nw.interaction_count_30d > 0 THEN ' | ' || nw.interaction_count_30d || ' recent' ELSE '' END
           FROM network nw WHERE nw.id = bs.record_id)
        WHEN bs.source_table = 'companies' THEN
          (SELECT CASE WHEN MAX(i.timestamp) IS NULL THEN 'No interactions recorded'
                 WHEN MAX(i.timestamp) > NOW() - INTERVAL '7 days' THEN 'Active this week'
                 WHEN MAX(i.timestamp) > NOW() - INTERVAL '30 days' THEN 'Active this month'
                 ELSE 'Last interaction: ' || MAX(i.timestamp)::date END
           FROM entity_connections ec JOIN interactions i ON ec.source_type = 'interaction' AND ec.source_id = i.id
           WHERE ec.target_type = 'company' AND ec.target_id = bs.record_id)
        ELSE NULL END AS interaction_recency,

      CASE
        WHEN bs.source_table = 'companies' AND EXISTS(
          SELECT 1 FROM companies c JOIN portfolio p ON LOWER(p.portfolio_co) = LOWER(c.name)
          WHERE c.id = bs.record_id AND p.health = 'Red'
        ) THEN 'URGENT: Red health portfolio company. Prioritize for meeting prep or check-in.'
        WHEN bs.source_table = 'companies' AND EXISTS(
          SELECT 1 FROM companies c JOIN portfolio p ON LOWER(p.portfolio_co) = LOWER(c.name)
          WHERE c.id = bs.record_id AND p.fumes_date IS NOT NULL AND p.fumes_date < CURRENT_DATE + INTERVAL '90 days'
        ) THEN 'URGENT: Portfolio company approaching fumes date. Assess runway situation.'
        WHEN bs.source_table = 'network' AND EXISTS(
          SELECT 1 FROM network nw WHERE nw.id = bs.record_id AND nw.e_e_priority IN ('High', 'Core')
          AND (nw.last_interaction_at IS NULL OR nw.last_interaction_at < NOW() - INTERVAL '60 days')
        ) THEN 'ACTION: High-priority contact with stale relationship. Schedule outreach.'
        WHEN bs.source_table = 'network' AND EXISTS(
          SELECT 1 FROM obligations o WHERE o.person_id = bs.record_id AND o.status = 'open' AND o.obligation_type = 'i_owe'
        ) THEN 'ACTION: Open I-owe obligation. Fulfill before next interaction.'
        WHEN bs.source_table = 'thesis_threads' AND EXISTS(
          SELECT 1 FROM thesis_threads tt WHERE tt.id = bs.record_id AND tt.bias_flags->>'severity' IN ('CRITICAL', 'HIGH')
        ) THEN 'RESEARCH: Thesis has bias alerts. Seek contra evidence before conviction moves.'
        WHEN bs.source_table = 'thesis_threads' AND EXISTS(
          SELECT 1 FROM thesis_threads tt WHERE tt.id = bs.record_id AND tt.updated_at < NOW() - INTERVAL '30 days'
        ) THEN 'REFRESH: Thesis data is stale. Gather recent evidence.'
        WHEN bs.source_table = 'actions_queue' AND EXISTS(
          SELECT 1 FROM actions_queue aq WHERE aq.id = bs.record_id
          AND aq.status IN ('open', 'Proposed', 'surfaced') AND aq.user_priority_score > 7
        ) THEN 'TRIAGE: High-priority open action. Present to user for decision.'
        WHEN bs.source_table = 'content_digests' THEN 'ANALYZE: Extract thesis signals and company mentions for further research.'
        ELSE 'CONTEXT: Use as background intelligence for current query.'
      END AS agent_action_hint
    FROM base_search bs
  )
  SELECT e.source_table, e.record_id, e.title, e.combined_score,
    e.why_it_matters, e.portfolio_connection, e.thesis_relevance,
    e.recent_signals, e.obligation_context, e.interaction_recency,
    e.agent_action_hint
  FROM enriched e
  ORDER BY e.combined_score DESC
  LIMIT p_limit;
END;
$function$;


------------------------------------------------------------
-- L63-64: thesis_research_package
-- Everything an ENIAC agent needs to research a thesis.
-- Returns JSONB with 23 keys from 12 data sources.
------------------------------------------------------------
-- See full implementation in Supabase (too large to duplicate here)
-- Key: thesis core data, evidence (for/against + cross-refs),
-- connected companies/people, key questions, recent signals,
-- comparable theses, bias analysis, momentum, actions pipeline,
-- related content, obligations, agent_research_directives


------------------------------------------------------------
-- L65-66: portfolio_deep_context
-- Full company dossier for meeting prep.
-- Works for both portfolio and pipeline companies.
------------------------------------------------------------
-- See full implementation in Supabase
-- Key: portfolio data (if applicable), key people with obligations
-- and relationship status, interaction history, obligations (I-owe/they-owe),
-- actions pipeline, thesis connections, similar companies,
-- agent_meeting_prep directives


------------------------------------------------------------
-- L67-68: discover_connections
-- Finds non-obvious connections across entity types.
-- 5 connection discovery methods.
------------------------------------------------------------
-- See full implementation in Supabase
-- Key: shared_people_connections, thesis_overlap,
-- interaction_bridges, sector_clusters,
-- hidden_semantic_connections, insight_summary
